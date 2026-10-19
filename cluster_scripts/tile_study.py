"""Separate, fixed-input tile code-capacity pilot and subsequent calibration."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import itertools
import json
import math
from pathlib import Path
import time
import traceback

import numpy as np
import mcmc4qec as qec
import calibration as c

MASTER = 2026101719
SETTINGS = dict(max_iter=100, bp_method="min_sum", ms_scaling_factor=1.0,
                schedule="parallel", osd_method="osd_cs", osd_order=10)
CASES = [(6, "bit"), (12, "bit"), (6, "depolarizing"), (12, "depolarizing")]
KERNELS = {"ZH": qec.KernelConfig(),
           "ZHS": qec.KernelConfig(zanella=.6, cluster=.3, stabilizer=.1)}


def seed(task, purpose):
    return int(np.random.SeedSequence([MASTER, 1, *task, purpose]).generate_state(1, dtype=np.uint64)[0])


def runtime():
    result = c.runtime()
    result["tile_driver_sha256"] = c.file_hash(__file__)
    return result


def make_plan():
    return dict(schema=1, master_seed=MASTER, stage="pilot", cases=CASES,
                probabilities=[.1, .05, .03, .01], replicates=6, mc_trials=512,
                steps=512, probe_samples=32, max_initial_attempts=20000,
                decoder=SETTINGS, kernels={name: asdict(k) for name, k in KERNELS.items()},
                runtime=runtime(), warning="Pilot is not a coverage experiment; diagnostics do not prove convergence or irreducibility.")


def build_problem(size, noise, target_p):
    code = qec.make_tile_code(size, size)
    if noise == "bit":
        problem = qec.Problem(code.bit_flip_model(), qec.IndependentBitFlip(code.n),
                              qec.bposd_decoder(code, target_p, **SETTINGS))
    elif noise == "depolarizing":
        problem = qec.Problem(qec.DepolarizingModel(code), qec.DepolarizingNoise(code.n),
                              qec.depolarizing_bposd_decoder(code, 2*target_p/3, **SETTINGS))
    else:
        raise ValueError("unknown noise")
    return code, problem


def compact(problem, states):
    states = np.asarray(states, dtype=np.uint8)
    syndromes = np.array([problem.model.syndrome(s) for s in states])
    observed = np.array([problem.model.observables(s) for s in states])
    unique, inverse = np.unique(syndromes, axis=0, return_inverse=True)
    predicted = np.array([problem.decoder.predict(s) for s in unique])[inverse]
    residual = observed ^ predicted
    return dict(weight=np.count_nonzero(states, axis=1).astype(np.uint16),
                syndrome_weight=syndromes.sum(axis=1).astype(np.uint16),
                sector=(residual.astype(np.uint32) @ (np.uint32(1) << np.arange(residual.shape[1], dtype=np.uint32))),
                logical=residual)


def initial_state(code, problem, p, noise, mode, index, rng, max_attempts):
    if mode == "logical":
        basis = code.lx if noise == "bit" else np.concatenate((code.lx, 3*code.lz))
        state, attempts = basis[index % len(basis)].copy(), 0
    elif mode == "rejection":
        for attempts in range(1, max_attempts+1):
            state = problem.noise.sample(p, rng)
            if problem.is_faulty(state):
                break
        else:
            raise qec.InitializationError("fixed rejection budget exhausted")
    else:
        raise ValueError("unknown initialization")
    if not problem.is_faulty(state) or not math.isfinite(problem.log_prob(state, p)):
        raise ValueError("initial state outside supported failure set")
    return state, attempts


def decoder_probe(size, noise, target_p, states, *, priors):
    code, problem = build_problem(size, noise, target_p)
    syndromes = np.array([problem.model.syndrome(s) for s in states])
    truth = np.array([problem.model.observables(s) for s in states])
    prediction = lambda decoder, seq: np.array([decoder.predict(s) for s in seq])
    baseline = prediction(problem.decoder, syndromes)
    repeat = prediction(problem.decoder, syndromes)
    reverse = prediction(problem.decoder, syndromes[::-1])[::-1]
    fresh = prediction(build_problem(size, noise, target_p)[1].decoder, syndromes)
    mismatch = lambda arr: int(np.any(arr != baseline, axis=1).sum())
    result = dict(samples=len(states), repeat_mismatches=mismatch(repeat),
                  reverse_mismatches=mismatch(reverse), fresh_mismatches=mismatch(fresh),
                  syndrome_violations=0, failure_definition_mismatches=0, prior_comparisons=[])
    corrections = []
    children = [(problem.decoder, code.hz, 0)] if noise == "bit" else [
        (problem.decoder.x_decoder, code.hz, 0), (problem.decoder.z_decoder, code.hx, len(code.hz))]
    for decoder, checks, offset in children:
        corrected = []
        for s in syndromes:
            input_syndrome = s[offset:offset+len(checks)]
            correction = decoder.decoder.decode(input_syndrome).copy()
            result["syndrome_violations"] += int(np.any(checks @ correction % 2 != input_syndrome))
            corrected.append(correction)
        corrections.append(np.array(corrected))
    if noise == "bit":
        logical_residual = ((np.asarray(states)^corrections[0]) @ code.lz.T) % 2
    else:
        x = np.isin(states, [1, 2]).astype(np.uint8)
        z = np.isin(states, [2, 3]).astype(np.uint8)
        logical_residual = np.concatenate(((x^corrections[0])@code.lz.T%2, (z^corrections[1])@code.lx.T%2), axis=1)
    baseline_failure = np.any(baseline != truth, axis=1)
    public_failure = np.array([problem.is_faulty(s) for s in states])
    result["failure_definition_mismatches"] = int(((np.any(logical_residual, axis=1) != public_failure) |
                                                    (baseline_failure != public_failure)).sum())
    for prior in priors:
        other = prediction(build_problem(size, noise, prior)[1].decoder, syndromes)
        failed = np.any(other != truth, axis=1)
        result["prior_comparisons"].append(dict(physical_target_prior=prior,
            sector_prior=prior if noise == "bit" else 2*prior/3,
            logical_disagreements=mismatch(other), failure_disagreements=int((failed != baseline_failure).sum()),
            failures=int(failed.sum()), baseline_failures=int(baseline_failure.sum())))
    return result


def pilot_task(args):
    root, plan, task = args
    identity = dict(manifest=c.digest(plan), task=list(task))
    path = Path(root)/"pilot"/c.task_id(task)
    cached = c.load_artifact(path, identity)
    if cached is not None:
        return dict(cached[1], resumed=True)
    start, cpu = time.perf_counter(), time.process_time()
    arrays, record = {}, dict(task=list(task), status="ok", chains=[])
    try:
        case, p_index, rep = task
        size, noise = plan["cases"][case]
        p = plan["probabilities"][p_index]
        code, problem = build_problem(size, noise, p)
        record.update(n=code.n, noise=noise, p=p, matrices=c.digest([a.tolist() for a in (code.hx, code.hz, code.lx, code.lz)]),
                      metadata=problem.metadata(), mc_seed=seed(task, 1))
        mc = qec.direct_mc(problem, p, trials=plan["mc_trials"], seed=seed(task, 1))
        record["direct_mc"] = dict(estimate=mc.estimate, interval=mc.interval, failures=mc.failures, trials=mc.trials,
                                    wall_seconds=mc.elapsed_seconds)
        rng = np.random.default_rng(seed(task, 2))
        probe_states = np.array([problem.noise.sample(p, rng) for _ in range(plan["probe_samples"])])
        arrays["probe_states"] = probe_states
        probe = decoder_probe(size, noise, p, probe_states, priors=[.0001, .001, .03, .1])
        record["decoder_probe"] = probe
        if any(probe[k] for k in ("repeat_mismatches", "reverse_mismatches", "fresh_mismatches", "syndrome_violations", "failure_definition_mismatches")):
            raise ValueError("decoder reproducibility or correction equation failed")
        for init_index, mode in enumerate(("rejection", "logical")):
            init_start = time.perf_counter()
            try:
                initial, attempts = initial_state(code, problem, p, noise, mode, rep,
                       np.random.default_rng(seed(task, 10+init_index)), plan["max_initial_attempts"])
                initial_error = None
            except qec.InitializationError as error:
                initial_error = repr(error)
            init_seconds = time.perf_counter()-init_start
            for kernel_index, (name, kernel_data) in enumerate(plan["kernels"].items()):
                key = f"{mode}_{name}"
                if initial_error is not None:
                    record["chains"].append(dict(init=mode, kernel=name, status="initialization_failed", error=initial_error,
                                                 initial_seconds=init_seconds, max_initial_attempts=plan["max_initial_attempts"]))
                    continue
                sample_seed = seed(task, 100+10*init_index+kernel_index)
                chain_start = time.perf_counter()
                result = qec.sample_faulty(problem, p, config=qec.SamplingConfig(samples=plan["steps"], burn_in=0,
                       kernels=qec.KernelConfig(**kernel_data), cache_cap=20000, cache_policy="lru"), seed=sample_seed, initial_state=initial)
                sample_seconds = time.perf_counter()-chain_start
                states = result.states[0]
                traces = compact(problem, states)
                if np.any(traces["sector"] == 0):
                    raise ValueError("saved state is not faulty")
                arrays[key+"_states"] = states
                arrays.update({key+"_"+k: v for k,v in traces.items()})
                record["chains"].append(dict(init=mode, kernel=name, status="ok", initial=initial.tolist(), initial_attempts=attempts,
                    initial_seconds=init_seconds, seed=sample_seed, sampling_seconds=sample_seconds,
                    acceptance=result.acceptance, diagnostics=result.diagnostics,
                    mean_weight=float(traces["weight"].mean()),
                    sector_transitions=int(np.count_nonzero(traces["sector"][1:] != traces["sector"][:-1])),
                    unique_sectors=int(len(np.unique(traces["sector"])))))
    except Exception as error:
        record.update(status="failed", error=repr(error), traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-start, cpu_seconds=time.process_time()-cpu, peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(path, identity, arrays, record)
    return record


def pilot_tasks(plan):
    return list(itertools.product(range(len(plan["cases"])), range(len(plan["probabilities"])), range(plan["replicates"])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "pilot"])
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=96)
    args = parser.parse_args()
    if args.command == "plan":
        if (args.root/"manifest.json").exists():
            raise ValueError("manifest already exists")
        c.atomic_json(args.root/"manifest.json", make_plan())
        return
    plan = json.loads((args.root/"manifest.json").read_text())
    if plan["runtime"] != runtime() or plan["master_seed"] != MASTER:
        raise ValueError("runtime or seed differs from manifest")
    started = time.perf_counter()
    records = c.parallel_map(pilot_task, [(str(args.root), plan, t) for t in pilot_tasks(plan)], args.workers)
    records.sort(key=lambda r:r["task"])
    summary = dict(manifest=c.digest(plan), elapsed_seconds=time.perf_counter()-started,
                   tasks=len(records), failed=sum(r["status"] != "ok" for r in records), records=records)
    c.atomic_json(args.root/"pilot_summary.json", summary)
    print(json.dumps({k:v for k,v in summary.items() if k != "records"}))
    if summary["failed"]:
        raise RuntimeError("pilot failed; investigate recorded errors before production")


if __name__ == "__main__":
    main()
