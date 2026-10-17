"""Fixed-cohort calibration on PBS; independent homogeneous bit flips only.

This research driver deliberately does not extend the public BAR API. Histogram
sufficiency holds only for its fixed decoder and independent bit-flip family.
All transitions, including rejections, remain in the saved compact traces.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from functools import lru_cache
import hashlib
from importlib.metadata import version
import itertools
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
import sys
import time
import traceback

import numpy as np
import mcmc4qec as qec

CODES = ("toric3", "surface3", "steane")
LADDERS = ((.10, .07, .05, .03), (.03, .01, .003, .001, .0003, .0001))
MASTER = 20261017
SCHEMA = 1
WARNING = "Diagnostics do not prove mixing, ergodicity, convergence or nominal coverage."


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_bytes(canonical(obj) + b"\n")
    os.replace(temporary, path)


def runtime():
    root = Path(qec.__file__).parent
    h = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        h.update(path.relative_to(root).as_posix().encode() + b"\0")
        h.update(path.read_bytes())
    return dict(package_sha256=h.hexdigest(), driver_sha256=file_hash(__file__),
                python=platform.python_version(),
                packages={name: version(name) for name in ("numpy", "pymatching", "ldpc", "bposd")})


def make_plan(*, smoke=False):
    replicates = 2 if smoke else 192
    windows = [60, 600] if smoke else [600, 6000, 60000]
    burns = [60, 600] if smoke else [600, 6000]
    rows = sum(len([b for b in (8, 32, 128, 1024) if b <= n and (b != 1024 or n >= 6000)]) + 1
               for n in windows for _ in burns)
    return dict(schema=SCHEMA, master_seed=MASTER, purpose="smoke" if smoke else "calibration",
                codes=list(CODES), ladders=[list(p) for p in LADDERS],
                replicates=replicates, chains=4, init=["stationary", "dispersed"],
                steps=10000 if smoke else 66000, windows=windows, burns=burns,
                bootstrap_replicates=20 if smoke else 1000, blocks=[8, 32, 128, 1024],
                cache_cap=200000, cache_policy="lru", kernels=asdict(qec.KernelConfig()),
                expected_tasks=3 * 10 * 2 * replicates * 4,
                expected_analysis_rows=3 * 2 * 2 * replicates * rows,
                runtime=runtime(), warning=WARNING)


def read_plan(root):
    plan = json.loads((Path(root) / "manifest.json").read_text())
    if plan["runtime"] != runtime():
        raise ValueError("runtime differs from pinned manifest")
    if plan["schema"] != SCHEMA or plan["master_seed"] != MASTER:
        raise ValueError("unsupported manifest seed schema")
    return plan


def tasks(plan):
    for code, ladder, init, rep in itertools.product(range(3), range(2), range(2), range(plan["replicates"])):
        for rung, chain in itertools.product(range(len(plan["ladders"][ladder])), range(plan["chains"])):
            yield (code, ladder, init, rep, rung, chain)


def groups(plan):
    return itertools.product(range(3), range(2), range(2), range(plan["replicates"]))


def task_id(task):
    return "-".join(map(str, task))


def seed(task, purpose):
    return int(np.random.SeedSequence([MASTER, SCHEMA, *task, purpose]).generate_state(1, dtype=np.uint64)[0])


@lru_cache(maxsize=5)
def problem_for(code_id):
    if code_id == 0:
        code = qec.make_toric_code(3)
    elif code_id == 1:
        code = qec.make_surface_code(3)
    elif code_id == 2:
        code = qec.make_steane_code()
    elif code_id in (3, 4):
        code = qec.make_tile_code(6 if code_id == 3 else 12, 6 if code_id == 3 else 12)
    else:
        raise ValueError("unknown code")
    decoder = (qec.mwpm_decoder(code) if code_id < 2 else
               qec.bposd_decoder(code, .03, max_iter=100, bp_method="min_sum", osd_method="osd_cs", osd_order=2))
    return code, qec.Problem(code.bit_flip_model(), qec.IndependentBitFlip(code.n), decoder)


def code_identity(code_id):
    code, problem = problem_for(code_id)
    return dict(matrices=digest([x.tolist() for x in (code.hx, code.hz, code.lx, code.lz)]),
                problem=problem.metadata())


def unpack(indices, n):
    return ((np.asarray(indices, dtype=np.uint32)[:, None] >> np.arange(n, dtype=np.uint32)) & 1).astype(np.uint8)


def enumerate_bank(code_id, start=0, stop=None):
    code, problem = problem_for(code_id)
    if code.n > 18:
        raise ValueError("exact enumeration limited to 18 qubits")
    indices = np.arange(start, 2**code.n if stop is None else stop, dtype=np.uint32)
    states = unpack(indices, code.n)
    syndrome = states @ code.hz.T % 2
    unique, inverse = np.unique(syndrome, axis=0, return_inverse=True)
    predicted = np.asarray([problem.decoder.predict(s) for s in unique], dtype=np.uint8)
    residual = (states @ code.lz.T % 2) ^ predicted[inverse]
    sector = residual.astype(np.uint32) @ (np.uint32(1) << np.arange(len(code.lz), dtype=np.uint32))
    faulty = sector != 0
    return dict(index=indices[faulty], weight=states.sum(axis=1)[faulty].astype(np.uint16),
                syndrome_weight=syndrome.sum(axis=1)[faulty].astype(np.uint16), sector=sector[faulty])


def failure_mass(bank, n, p):
    count = np.bincount(bank["weight"], minlength=n+1)
    w = np.arange(n+1)
    return float(np.dot(count, p**w * (1-p)**(n-w)))


def dispersed_indices(bank, chains):
    chosen, sectors = [], set()
    for chain in range(chains):
        order = np.lexsort((bank["index"], (1 if chain % 2 == 0 else -1) * bank["weight"].astype(int)))
        candidates = [int(i) for i in order if int(bank["index"][i]) not in chosen]
        fresh = [i for i in candidates if int(bank["sector"][i]) not in sectors]
        i = (fresh or candidates)[0]
        chosen.append(int(bank["index"][i]))
        sectors.add(int(bank["sector"][i]))
    return chosen


def initial_index(bank, n, p, init, chain, rng):
    if init == 1:
        return dispersed_indices(bank, 4)[chain]
    counts = np.bincount(bank["weight"], minlength=n+1)
    weights = np.arange(n+1)
    log_mass = np.full(n+1, -np.inf)
    good = counts > 0
    log_mass[good] = np.log(counts[good]) + weights[good]*math.log(p) + (n-weights[good])*math.log1p(-p)
    masses = np.exp(log_mass - np.max(log_mass))
    w = rng.choice(n+1, p=masses/masses.sum())
    return int(rng.choice(bank["index"][bank["weight"] == w]))


def save_artifact(path, identity, arrays, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Invalidate an old marker first; never certify partially replaced files.
    path.with_suffix(".done.json").unlink(missing_ok=True)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    os.replace(temporary, path.with_suffix(".npz"))
    atomic_json(path.with_suffix(".json"), record)
    atomic_json(path.with_suffix(".done.json"), dict(identity=identity,
                sha256={ext: file_hash(path.with_suffix(ext)) for ext in (".npz", ".json")}))


def load_artifact(path, identity):
    path = Path(path)
    marker = path.with_suffix(".done.json")
    if not marker.exists():
        return None
    stored = json.loads(marker.read_text())
    if stored["identity"] != json.loads(canonical(identity)):
        raise ValueError(f"artifact identity mismatch: {path}")
    for ext, expected in stored["sha256"].items():
        if file_hash(path.with_suffix(ext)) != expected:
            raise ValueError(f"artifact checksum mismatch: {path}{ext}")
    with np.load(path.with_suffix(".npz"), allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    return arrays, json.loads(path.with_suffix(".json").read_text())


@lru_cache(maxsize=3)
def load_bank(root, manifest_hash, code_id):
    bank = load_artifact(Path(root)/"truth"/str(code_id), dict(manifest=manifest_hash, code=code_id, code_identity=code_identity(code_id)))
    if bank is None:
        raise ValueError("missing truth bank")
    return bank[0]


def peak_rss_mb():
    if sys.platform == "win32":
        return None
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def truth_chunk(args):
    root, plan, code_id, chunk = args
    identity = dict(manifest=digest(plan), code=code_id, chunk=chunk, code_identity=code_identity(code_id))
    path = Path(root)/"truth_parts"/f"{code_id}-{chunk}"
    if load_artifact(path, identity) is not None:
        return
    n = problem_for(code_id)[0].n
    start, stop = (2**n * c // 32 for c in (chunk, chunk+1))
    bank = enumerate_bank(code_id, start, stop)
    save_artifact(path, identity, bank, dict(status="ok", start=start, stop=stop))


def parallel_map(function, jobs, workers):
    if workers == 1:
        return [function(job) for job in jobs]
    with mp.get_context("spawn").Pool(workers) as pool:
        return list(pool.imap_unordered(function, jobs, chunksize=1))


def run_truth(root, plan, workers):
    parallel_map(truth_chunk, [(str(root), plan, c, chunk) for c in range(3) for chunk in range(32)], workers)
    for c in range(3):
        parts = [load_artifact(Path(root)/"truth_parts"/f"{c}-{chunk}", dict(manifest=digest(plan), code=c, chunk=chunk, code_identity=code_identity(c)))[0] for chunk in range(32)]
        bank = {key: np.concatenate([p[key] for p in parts]) for key in parts[0]}
        if np.any(np.diff(bank["index"].astype(np.int64)) <= 0):
            raise ValueError("unordered or duplicate truth states")
        n = problem_for(c)[0].n
        save_artifact(Path(root)/"truth"/str(c), dict(manifest=digest(plan), code=c, code_identity=code_identity(c)), bank,
                      dict(status="ok", n=n, faulty_states=len(bank["index"]), probabilities={str(p): failure_mass(bank, n, p) for p in set(sum(plan["ladders"], []))}))


def sample_task(args):
    root, plan, task = args
    identity = dict(manifest=digest(plan), task=list(task))
    path = Path(root)/"traces"/task_id(task)
    cached = load_artifact(path, identity)
    if cached is not None:
        return dict(task=list(task), resumed=True, **cached[1])
    started, cpu = time.perf_counter(), time.process_time()
    try:
        code_id, ladder, init, rep, rung, chain = task
        code, problem = problem_for(code_id)
        bank = load_bank(str(root), digest(plan), code_id)
        p = plan["ladders"][ladder][rung]
        initial = initial_index(bank, code.n, p, init, chain, np.random.default_rng(seed(task, 0)))
        result = qec.sample_faulty(problem, p, config=qec.SamplingConfig(samples=plan["steps"], burn_in=0, chains=1,
                    cache_cap=plan["cache_cap"], cache_policy=plan["cache_policy"], kernels=qec.KernelConfig(**plan["kernels"])),
                    seed=seed(task, 1), initial_state=unpack([initial], code.n)[0])
        indices = result.states[0].astype(np.uint32) @ (np.uint32(1) << np.arange(code.n, dtype=np.uint32))
        positions = np.searchsorted(bank["index"], indices)
        if np.any(positions >= len(bank["index"])) or not np.array_equal(bank["index"][positions], indices):
            raise ValueError("saved state violates the checked exact failure bank")
        arrays = {key: bank[key][positions] for key in ("weight", "syndrome_weight", "sector")}
        record = dict(status="ok", initial_index=initial, sample_seed=seed(task, 1), init_seed=seed(task, 0),
                      acceptance_whole_trace=result.acceptance, diagnostics_whole_trace=result.diagnostics,
                      warnings=result.warnings, metadata=result.metadata)
    except Exception as error:
        arrays = {}
        record = dict(status="failed", error=repr(error), traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started, cpu_seconds=time.process_time()-cpu, peak_rss_mb=peak_rss_mb())
    save_artifact(path, identity, arrays, record)
    return dict(task=list(task), resumed=False, **record)


def log_density_difference(n, p, q):
    w = np.arange(n+1)
    return w * math.log(q/p) + (n-w) * math.log((1-q)/(1-p))


def histogram_bar(a, b, delta):
    """Vectorized weighted Bennett roots; last axis is the weight histogram."""
    a, b = np.broadcast_arrays(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    if np.any(a < 0) or np.any(b < 0) or np.any(a.sum(-1) == 0) or np.any(b.sum(-1) == 0):
        raise ValueError("nonempty nonnegative histograms required")
    offset = np.log(b.sum(-1)/a.sum(-1))
    active = (a > 0) | (b > 0)
    low = np.min(np.where(active, delta, np.inf), axis=-1)+offset-50
    high = np.max(np.where(active, delta, -np.inf), axis=-1)+offset+50
    for _ in range(60):
        middle = (low+high)/2
        x = delta-middle[..., None]+offset[..., None]
        score = (a*np.exp(-np.logaddexp(0, -x)) - b*np.exp(-np.logaddexp(0, x))).sum(-1)
        low = np.where(score > 0, middle, low)
        high = np.where(score > 0, high, middle)
    return (low+high)/2


def bootstrap_histograms(weights, n, length, replicates, rng):
    """Exact circular blocks, including partial last block, without state expansion.

    RNG draws are identical to repeated public _block_indices calls. Prefix
    counts make cost independent of the block length's state expansion.
    """
    chains, samples = weights.shape
    blocks = math.ceil(samples/length)
    hist = np.zeros((replicates, n+1), dtype=np.int64)
    doubled = np.concatenate((weights, weights), axis=1)
    prefix = np.pad(np.cumsum(doubled[:, :, None] == np.arange(n+1), axis=1, dtype=np.int32), ((0, 0), (1, 0), (0, 0)))
    sizes = np.full(blocks, length)
    sizes[-1] = samples-(blocks-1)*length
    # Bound temporary gathered histograms to about 80 MB at the largest window.
    batch = max(1, min(16, 10_000_000 // (chains*blocks*(n+1))))
    for start in range(0, replicates, batch):
        count = min(batch, replicates-start)
        starts = rng.integers(samples, size=(count, chains, blocks))
        ids = np.arange(chains)[None, :, None]
        values = prefix[ids, starts+sizes]-prefix[ids, starts]
        hist[start:start+count] = values.sum(axis=(1, 2))
    return hist


def estimate_window(weights, n, ladder, anchor, *, block, replicates, rng):
    hist = np.array([[np.bincount(chain, minlength=n+1) for chain in w] for w in weights])
    deltas = [log_density_difference(n, p, q) for p, q in zip(ladder, ladder[1:])]
    pooled = hist.sum(axis=1)
    point_edges = np.array([histogram_bar(a, b, d) for a, b, d in zip(pooled, pooled[1:], deltas)])
    if block is None:
        draws = np.array([histogram_bar(a, b, d) for a, b, d in zip(hist, hist[1:], deltas)]).T
        covariance = np.atleast_2d(np.cov(draws, rowvar=False, ddof=1))/hist.shape[1]
    else:
        # One independent bootstrap stream per rung; each draw is reused on BOTH edges.
        resampled = [bootstrap_histograms(w, n, block, replicates, rng) for w in weights]
        draws = np.array([histogram_bar(a, b, d) for a, b, d in zip(resampled, resampled[1:], deltas)]).T
        covariance = np.atleast_2d(np.cov(draws, rowvar=False, ddof=1))
    logp = math.log(anchor)+float(point_edges.sum())
    se = math.sqrt(max(0., float(covariance.sum())))
    interval = None
    estimate = math.exp(logp) if logp <= 0 else None
    if estimate is not None and estimate > 0:
        lo, hi = logp-1.959963984540054*se, logp+1.959963984540054*se
        lower = math.exp(lo)
        if lower > 0:
            interval = [lower, math.exp(min(0., hi))]
    return dict(estimate=estimate, log_estimate=logp, log_se=se, interval=interval,
                adjacent_log_ratios=point_edges.tolist(), covariance=covariance.tolist())


def diagnostic_record(values, observable):
    # Numeric ACF is bounded, IAT still uses the full FFT sequence.
    return qec.analyze_traces(values, observable=observable, max_lag=min(64, values.shape[-1]-1),
                              block_sizes=[b for b in (8, 32, 128) if b <= values.shape[-1]],
                              bootstrap_replicates=0, seed=0)


def analyze_group(args):
    root, plan, group = args
    identity = dict(manifest=digest(plan), group=list(group))
    path = Path(root)/"analysis"/task_id(group)
    cached = load_artifact(path, identity)
    if cached is not None:
        return cached[1]
    started = time.perf_counter()
    code_id, ladder_id, init, rep = group
    ladder = plan["ladders"][ladder_id]
    n = problem_for(code_id)[0].n
    bank = load_bank(str(root), digest(plan), code_id)
    target = failure_mass(bank, n, ladder[-1])
    anchor = failure_mass(bank, n, ladder[0])
    loaded, failed = [], []
    for rung in range(len(ladder)):
        rung_data = []
        for chain in range(plan["chains"]):
            task = (*group, rung, chain)
            result = load_artifact(Path(root)/"traces"/task_id(task), dict(manifest=digest(plan), task=list(task)))
            if result is None:
                raise ValueError(f"missing expected task {task}")
            if result[1]["status"] != "ok":
                failed.append(dict(task=list(task), error=result[1].get("error")))
            rung_data.append(result[0])
        loaded.append(rung_data)
    rows, diagnostics = [], []
    for burn, samples in itertools.product(plan["burns"], plan["windows"]):
        blocks = [b for b in plan["blocks"] if b <= samples and (b != 1024 or samples >= 6000)] + [None]
        if not failed:
            compact = [{key: np.stack([v[key][burn:burn+samples] for v in rung]) for key in ("weight", "syndrome_weight", "sector")} for rung in loaded]
            if any(x["weight"].shape != (plan["chains"], samples) for x in compact):
                raise ValueError("short trace cannot supply preregistered window")
            for rung, obs in enumerate(compact):
                diag = dict(burn=burn, samples=samples, rung=rung, observables={})
                for key in ("weight", "syndrome_weight"):
                    diag["observables"][key] = diagnostic_record(obs[key], key)
                for bit in range(len(problem_for(code_id)[0].lz)):
                    key = f"logical_bit_{bit}"
                    diag["observables"][key] = diagnostic_record((obs["sector"] >> bit) & 1, key)
                # Bennett contribution observables on each side of each adjacent edge.
                weights = obs["weight"]
                for edge in (rung-1, rung):
                    if 0 <= edge < len(ladder)-1:
                        delta = log_density_difference(n, ladder[edge], ladder[edge+1])
                        other = compact[edge+1 if edge == rung else edge]["weight"]
                        a, b = (weights, other) if edge == rung else (other, weights)
                        ratio = histogram_bar(np.bincount(a.ravel(), minlength=n+1), np.bincount(b.ravel(), minlength=n+1), delta)
                        x = delta[weights]-ratio
                        contribution = np.exp(-np.logaddexp(0., -x if edge == rung else x))
                        key = f"bennett_edge_{edge}"
                        diag["observables"][key] = diagnostic_record(contribution, key)
                diagnostics.append(diag)
        for block in blocks:
            row = dict(group=list(group), code=CODES[code_id], ladder=ladder_id, init=plan["init"][init], replicate=rep,
                       burn=burn, samples=samples, method="cross_chain" if block is None else "block", block=block, truth=target,
                       estimate=None, interval=None, covered=False, available=False)
            if failed:
                row["failure"] = "sampling_failed"
            else:
                try:
                    estimate = estimate_window([obs["weight"] for obs in compact], n, ladder, anchor, block=block,
                                replicates=plan["bootstrap_replicates"], rng=np.random.default_rng(seed((*group, burn, samples, block or 0), 2)))
                    row.update(estimate)
                    row["available"] = estimate["interval"] is not None
                    row["covered"] = bool(row["available"] and estimate["interval"][0] <= target <= estimate["interval"][1])
                except (ValueError, FloatingPointError) as error:
                    row["failure"] = repr(error)
            rows.append(row)
    record = dict(status="ok", group=list(group), rows=rows, diagnostics=diagnostics, failed_tasks=failed,
                  wall_seconds=time.perf_counter()-started, peak_rss_mb=peak_rss_mb(), warning=WARNING)
    save_artifact(path, identity, {}, record)
    return {k: v for k, v in record.items() if k != "diagnostics"}


def aggregate(root, plan):
    import csv
    rows = []
    for group in groups(plan):
        result = load_artifact(Path(root)/"analysis"/task_id(group), dict(manifest=digest(plan), group=list(group)))
        if result is None:
            raise ValueError(f"missing analysis group {group}")
        rows.extend(result[1]["rows"])
    if len(rows) != plan["expected_analysis_rows"]:
        raise ValueError("unexpected cohort row count")
    columns = ["code", "ladder", "init", "replicate", "burn", "samples", "method", "block", "truth", "estimate", "log_estimate", "log_se", "interval", "covered", "available", "failure"]
    with (Path(root)/"coverage_rows.csv.tmp").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(Path(root)/"coverage_rows.csv.tmp", Path(root)/"coverage_rows.csv")
    grouped = {}
    for row in rows:
        key = tuple(row[k] for k in ("code", "ladder", "init", "burn", "samples", "method", "block"))
        grouped.setdefault(key, []).append(row)
    summary = []
    for key, cohort in grouped.items():
        total = plan["replicates"]
        if len(cohort) != total or len({r["replicate"] for r in cohort}) != total:
            raise ValueError("incomplete or duplicate cohort")
        available = sum(r["available"] for r in cohort)
        covered = sum(r["covered"] for r in cohort)
        phat, z = covered/total, 1.959963984540054
        center = (phat+z*z/(2*total))/(1+z*z/total)
        half = z*math.sqrt(phat*(1-phat)/total+z*z/(4*total*total))/(1+z*z/total)
        estimates = [r["estimate"] for r in cohort if r["estimate"] is not None]
        error = np.asarray(estimates)-cohort[0]["truth"]
        summary.append(dict(condition=list(key), denominator=total, available=available, covered=covered,
                            coverage=phat, conditional_coverage=covered/available if available else None,
                            wilson=[center-half, center+half], bias=float(error.mean()) if len(error) else None,
                            rmse=float(np.sqrt(np.mean(error**2))) if len(error) else None,
                            empirical_sd=float(np.std(estimates, ddof=1)) if len(estimates)>1 else None,
                            mean_log_se=float(np.mean([r["log_se"] for r in cohort if r["available"]])) if available else None,
                            mean_width=float(np.mean([r["interval"][1]-r["interval"][0] for r in cohort if r["available"]])) if available else None))
    pairs = []
    for key, cohort in grouped.items():
        if key[-2] != "block":
            continue
        other = grouped[(*key[:-2], "cross_chain", None)]
        a = {r["replicate"]: r for r in other}
        differences = [int(r["covered"])-int(a[r["replicate"]]["covered"]) for r in cohort]
        pairs.append(dict(condition=list(key), versus="cross_chain", paired_coverage_difference=float(np.mean(differences)),
                          paired_se=float(np.std(differences, ddof=1)/math.sqrt(len(differences))) if len(differences)>1 else None))
    atomic_json(Path(root)/"summary.json", dict(manifest=digest(plan), summary=summary, paired=pairs, warning=WARNING))


def run_sampling(root, plan, workers, shard=None):
    jobs = [t for t in tasks(plan) if shard is None or t[3] % 4 == shard]
    timing_path = Path(root).parent/"smoke"/"timing.json"
    timing = json.loads(timing_path.read_text()).get("cell_seconds", {}) if timing_path.exists() else {}
    jobs.sort(key=lambda t: timing.get(task_id((t[0], t[1], t[2], t[4])), 1.), reverse=True)
    records = parallel_map(sample_task, [(str(root), plan, t) for t in jobs], workers)
    atomic_json(Path(root)/f"sampling_{shard if shard is not None else 'all'}.json", dict(
                tasks=len(records), failed=sum(r["status"] != "ok" for r in records),
                resumed=sum(r["resumed"] for r in records), wall_seconds=sum(r["wall_seconds"] for r in records)))
    return records


def tile_smoke_task(number):
    start, cpu = time.perf_counter(), time.process_time()
    code_id = 3 + number % 2
    code, problem = problem_for(code_id)
    result = qec.sample_faulty(problem, .03, config=qec.SamplingConfig(
        samples=200 if code_id == 4 else 1000, burn_in=0, cache_cap=200000, cache_policy="lru"),
        initial_state=code.lx[0], seed=seed((code_id, number), 5))
    if not all(problem.is_faulty(s) for s in result.states[0]):
        raise ValueError("tile smoke emitted a nonfaulty state")
    qec.Result.from_json(result.to_json())
    return dict(code="tile72" if code_id == 3 else "tile288", n=code.n, k=len(code.lx),
                samples=result.states.shape[1], wall_seconds=time.perf_counter()-start,
                cpu_seconds=time.process_time()-cpu, peak_rss_mb=peak_rss_mb())


def analysis_timing_task(args):
    root, plan, number = args
    group = list(groups(plan))[number % (12*plan["replicates"])]
    code_id, ladder_id, _, _ = group
    n = problem_for(code_id)[0].n
    ladder = plan["ladders"][ladder_id]
    weights = []
    for rung in range(len(ladder)):
        traces = []
        for chain in range(4):
            task = (*group, rung, chain)
            result = load_artifact(Path(root)/"traces"/task_id(task), dict(manifest=digest(plan), task=list(task)))
            traces.append(np.resize(result[0]["weight"], 60000))
        weights.append(np.stack(traces))
    start = time.perf_counter()
    # Tiling is for capacity measurement ONLY; these numbers never enter coverage.
    estimate_window(weights, n, ladder, .1, block=8, replicates=1000, rng=np.random.default_rng(number))
    for obs in weights:
        diagnostic_record(obs, "timing_only_repeated_weight")
    return dict(wall_seconds=time.perf_counter()-start, peak_rss_mb=peak_rss_mb())


def run_smoke(root, plan, workers):
    if plan["purpose"] != "smoke":
        raise ValueError("smoke requires its own manifest")
    started = time.perf_counter()
    run_truth(root, plan, workers)
    records = run_sampling(root, plan, workers)
    if any(r["status"] != "ok" for r in records):
        raise RuntimeError("sampling smoke failed; inspect trace JSON")
    # Full replay checks markers and array checksums using a different pool size.
    replay = run_sampling(root, plan, 2)
    if not all(r["resumed"] for r in replay):
        raise RuntimeError("resume smoke recomputed a completed task")
    # Fresh execution equivalence across one and two workers (eight short tasks).
    short = dict(plan, steps=128)
    selected = list(tasks(short))[:8]
    for workers_test in (1, 2):
        destination = Path(root)/f"worker_check_{workers_test}"
        for code in range(3):
            bank = load_bank(str(root), digest(plan), code)
            save_artifact(destination/"truth"/str(code), dict(manifest=digest(short), code=code, code_identity=code_identity(code)), bank, dict(status="ok"))
        parallel_map(sample_task, [(str(destination), short, t) for t in selected], workers_test)
    for task in selected:
        pair = [load_artifact(Path(root)/f"worker_check_{w}"/"traces"/task_id(task), dict(manifest=digest(short), task=list(task))) for w in (1, 2)]
        if any(p[1]["status"] != "ok" for p in pair) or any(not np.array_equal(pair[0][0][key], pair[1][0][key]) for key in pair[0][0]):
            raise RuntimeError("worker-count trajectory mismatch")
    parallel_map(analyze_group, [(str(root), plan, g) for g in groups(plan)], workers)
    aggregate(root, plan)
    tiles = parallel_map(tile_smoke_task, list(range(96)), workers)
    capacity = parallel_map(analysis_timing_task, [(str(root), plan, i) for i in range(96)], workers)
    cell = {}
    for r in records:
        t = r["task"]
        key = task_id((t[0], t[1], t[2], t[4]))
        cell.setdefault(key, []).append(r["wall_seconds"])
    cell = {key: float(np.median(values)) for key, values in cell.items()}
    production = make_plan()
    shards = []
    for shard in range(4):
        costs = [cell[task_id((t[0], t[1], t[2], t[4]))] * production["steps"]/plan["steps"] for t in tasks(production) if t[3] % 4 == shard]
        shards.append(sum(costs)/workers+max(costs))
    # Conservative 28 longest-window analyses per group, plus diagnostic headroom.
    analysis_seconds = max(x["wall_seconds"] for x in capacity)*28*2304/workers
    atomic_json(Path(root)/"timing.json", dict(status="ok", manifest=digest(plan), cell_seconds=cell,
                predicted_sample_shard_seconds=shards, predicted_analysis_seconds=analysis_seconds,
                sample_peak_worker_rss_mb=max(r["peak_rss_mb"] or 0 for r in records),
                analysis_peak_worker_rss_mb=max(r["peak_rss_mb"] or 0 for r in capacity),
                capacity=capacity, tile=tiles, workers=workers, total_smoke_seconds=time.perf_counter()-started,
                note="Predictions, not measured production times. Capacity traces are repeated ONLY for timing."))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "truth", "sample", "analyze", "smoke"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=96)
    parser.add_argument("--shard", type=int, choices=range(4))
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 96:
        parser.error("workers must be in [1,96]")
    args.root.mkdir(parents=True, exist_ok=True)
    if args.command == "plan":
        plan = make_plan(smoke=args.smoke)
        path = args.root/"manifest.json"
        if path.exists() and json.loads(path.read_text()) != plan:
            raise ValueError("refusing to overwrite a different manifest")
        atomic_json(path, plan)
        print(json.dumps(dict(manifest=digest(plan), tasks=plan["expected_tasks"], rows=plan["expected_analysis_rows"])))
        return
    plan = read_plan(args.root)
    start = time.perf_counter()
    if args.command == "truth":
        run_truth(args.root, plan, args.workers)
    elif args.command == "sample":
        run_sampling(args.root, plan, args.workers, args.shard)
    elif args.command == "analyze":
        parallel_map(analyze_group, [(str(args.root), plan, g) for g in groups(plan)], args.workers)
        aggregate(args.root, plan)
    else:
        run_smoke(args.root, plan, args.workers)
    print(json.dumps(dict(command=args.command, wall_seconds=time.perf_counter()-start)), flush=True)


if __name__ == "__main__":
    main()
