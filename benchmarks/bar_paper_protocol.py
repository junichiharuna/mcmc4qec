"""Fixed-cohort toric d=3 BAR coverage under library and paper-like protocols.

Run one configuration and a bounded seed slice per invocation. The script writes
per-seed CSV and a slice summary. Merge all slices only after checking that seeds
2026..2045 are present exactly once; no result may be selected by outcome.
This is a finite-budget experiment, not a reproduction of the paper's figures.
"""

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import tempfile
import time

import numpy as np

from mcmc4qec import IndependentBitFlip, KernelConfig, Problem, Result, SamplingConfig, direct_mc, exact, sample_faulty, spawn_seeds
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import mwpm_decoder
from mcmc4qec.estimation import _block_indices, bennett_log_ratio, estimate_logical_error
from mcmc4qec.initial_states import maximum_weight_initial_state, minimum_weight_initial_state
from mcmc4qec.diagnostics import _first_negative_iat as research_iat, paper_burn_in_cut as paper_burn_cut
from mcmc4qec.results import metadata


LADDERS = {"paper": [0.10, 0.07, 0.05, 0.03], "dev4": [0.30, 0.26, 0.22]}
PROTOCOLS = {"default_block": (4, "fixed", "block_bootstrap"),
             "default_cross": (4, "fixed", "cross_chain"),
             "paper50": (50, "iat5", "cross_chain"),
             "paper16": (16, "iat5", "cross_chain")}
COHORT = tuple(range(2026, 2046))
Z = 1.959963984540054
WARNINGS = ("Diagnostics do not prove convergence, ergodicity, or correctness. "
            "Finite-chain BAR bias is excluded from intervals. "
            "Toric d=3 min/max logical basis starts coincide, so the paper multistart check is unresolved. "
            "Adaptive cuts can leave unequal chain lengths; BAR cross-chain covariance/K is an asymptotic approximation.")


def output_dir(value):
    path = Path(value).expanduser().resolve()
    for name in ("RIMC_RESEARCH_ROOT", "RESEARCH_ROOT"):
        if os.environ.get(name):
            root = Path(os.environ[name]).resolve()
            if path == root or root in path.parents:
                raise ValueError("Refusing to write into the read-only research repository")
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def wilson(k, n):
    center = (k/n + Z*Z/(2*n)) / (1+Z*Z/n)
    half = Z*math.sqrt((k/n)*(1-k/n)/n + Z*Z/(4*n*n))/(1+Z*Z/n)
    return max(0.0, center-half), min(1.0, center+half)


def _problem_digest(code, problem):
    digest = hashlib.sha256()
    for name in ("hx", "hz", "lx", "lz"):
        matrix = np.asarray(getattr(code, name), dtype=np.uint8)
        digest.update(name.encode())
        digest.update(np.asarray(matrix.shape, dtype=np.int64).tobytes())
        digest.update(matrix.tobytes())
    digest.update(json.dumps(problem.metadata(), sort_keys=True).encode())
    return digest.hexdigest()


def make_truth_cache(path, code, problem):
    """Enumerate failure weights once for every bit-flip p in both ladders."""
    counts = [0]*(code.n+1)
    for bits in itertools.product((0, 1), repeat=code.n):
        state = np.fromiter(bits, dtype=np.uint8, count=code.n)
        if problem.is_faulty(state):
            counts[int(np.count_nonzero(state))] += 1
    if sum(counts) != 196_608:
        raise RuntimeError("toric d=3 failure count differs from the independently checked count")
    payload = dict(code="toric_d3", n=code.n, problem_sha256=_problem_digest(code, problem),
                   package_source_sha256=metadata(problem, .5, {})["package_source_sha256"],
                   failure_weight_counts=counts,
                   counts_sha256=hashlib.sha256(np.asarray(counts, dtype=np.int64).tobytes()).hexdigest())
    target = Path(path).expanduser().resolve()
    output_dir(target.parent)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_truth_cache(path, code, problem):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if (payload.get("code") != "toric_d3" or payload.get("n") != code.n or
            payload.get("problem_sha256") != _problem_digest(code, problem) or
            payload.get("package_source_sha256") != metadata(problem, .5, {})["package_source_sha256"] or
            len(payload.get("failure_weight_counts", [])) != code.n+1 or
            any(not isinstance(v, int) or v < 0 for v in payload["failure_weight_counts"]) or
            sum(payload["failure_weight_counts"]) != 196_608 or
            payload.get("counts_sha256") != hashlib.sha256(np.asarray(
                payload["failure_weight_counts"], dtype=np.int64).tobytes()).hexdigest()):
        raise ValueError("truth cache does not match this toric d=3 problem")
    return payload


def cached_exact(problem, p, payload):
    counts = payload["failure_weight_counts"]
    n = payload["n"]
    masses = [count*(p**w)*((1-p)**(n-w)) for w, count in enumerate(counts)]
    value = math.fsum(masses)
    conditional_weight = math.fsum(w*mass for w, mass in enumerate(masses))/value
    return Result("exact", metadata(problem, p, dict(max_states=1_048_576,
                  truth_cache_sha256=payload["problem_sha256"])), 0.0,
                  estimate=value, log_estimate=math.log(value),
                  conditional_weight=conditional_weight)


def _summary(rows, elapsed):
    n = len(rows)
    k = sum(row["covered"] == "True" for row in rows)
    low, high = wilson(k, n)
    valid = [row for row in rows if row["low"] != ""]
    return dict(region=rows[0]["region"], protocol=rows[0]["protocol"],
                anchor_kind=rows[0]["anchor_kind"], samples=rows[0]["samples"],
                total_steps=rows[0]["total_steps"],
                chains=rows[0]["chains"], problem_sha256=rows[0]["problem_sha256"],
                auxiliary_start=rows[0]["auxiliary_start"], seeds=n,
                seed_start=min(int(row["seed"]) for row in rows),
                seed_end=max(int(row["seed"]) for row in rows),
                exact=float(rows[0]["exact"]), covered=k,
                wilson_low=low, wilson_high=high, valid_intervals=len(valid),
                mean_width=float(np.mean([float(row["high"])-float(row["low"]) for row in valid])) if valid else "",
                mean_estimate=float(np.mean([float(row["estimate"]) for row in rows])),
                mean_bias=float(np.mean([float(row["estimate"])-float(row["exact"]) for row in rows])),
                four_rule_pass=sum(row["four_rule_pass"] == "True" for row in rows),
                four_rule_unresolved=sum(row["four_rule_pass"] in (None, "", "None") for row in rows),
                paper_vacuous_pass=sum(row["paper_vacuous_pass"] == "True" for row in rows),
                auxiliary_four_rule_pass=sum(row["auxiliary_four_rule_pass"] == "True" for row in rows),
                burn_capped=sum(row["burn_capped"] == "True" for row in rows),
                warnings=WARNINGS,
                elapsed_seconds=elapsed)


def aggregate(directory, out, truth_cache):
    """Require every predeclared seed once per configuration before summarizing."""
    if not truth_cache:
        raise ValueError("--aggregate requires --truth-cache for independent exact-truth validation")
    code = make_toric_code(3)
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
    cache = load_truth_cache(truth_cache, code, problem)
    problem_sha = _problem_digest(code, problem)
    groups = {}
    for path in sorted(Path(directory).glob("*_runs.csv")):
        if path.name == "cohort_runs.csv":
            continue
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                key = (row["region"], row["protocol"], row["anchor_kind"],
                       row["samples"], row["total_steps"], row["chains"], row["problem_sha256"],
                       row["bootstrap_replicates"], row["block"],
                       row["anchor_trials"], row["auxiliary_start"], row["lazy"],
                       row["truth_source"], row["truth_cache_source_sha256"])
                groups.setdefault(key, []).append(row)
    if not groups:
        raise ValueError("no per-seed CSV files found")
    all_rows, summaries = [], []
    for key, rows in sorted(groups.items()):
        seeds = [int(row["seed"]) for row in rows]
        if len(seeds) != len(COHORT) or sorted(seeds) != list(COHORT):
            raise ValueError(f"{key}: require each fixed cohort seed 2026..2045 exactly once")
        if len({row["exact"] for row in rows}) != 1:
            raise ValueError(f"{key}: exact truth differs across seed rows")
        expected = cached_exact(problem, LADDERS[key[0]][-1], cache).estimate
        if any(row["problem_sha256"] != problem_sha or
               row["truth_cache_source_sha256"] != cache["package_source_sha256"] or
               row["truth_source"] != "checked_weight_cache" or
               not math.isclose(float(row["exact"]), expected, rel_tol=0, abs_tol=1e-12)
               for row in rows):
            raise ValueError(f"{key}: exact truth or problem provenance differs from checked cache")
        ordered = sorted(rows, key=lambda row: int(row["seed"]))
        all_rows.extend(ordered)
        summaries.append(_summary(ordered, ""))
    target = output_dir(out)
    write_csv(target / "cohort_runs.csv", all_rows)
    write_csv(target / "cohort_summary.csv", summaries)
    print(f"Validated {len(groups)} configurations with 20/20 fixed seeds each: {target}")


def _bar_from_traces(problem, ladder, states, cuts, method, bootstrap_replicates, block, bootstrap_seed):
    k = states[0].shape[0]
    differences = []
    for i, trace in enumerate(states):
        if i == 0:
            targets = [ladder[1]]
        elif i == len(ladder)-1:
            targets = [ladder[-2]]
        else:
            targets = [ladder[i-1], ladder[i+1]]
        differences.append({target: [np.asarray([
            problem.log_prob(state, target)-problem.log_prob(state, ladder[i])
            for state in trace[j, cuts[i][j]:, :]]) for j in range(k)]
            for target in targets})
    edges = []
    for i in range(len(ladder)-1):
        forward = differences[i][ladder[i+1]]
        reverse = [-values for values in differences[i+1][ladder[i]]]
        edges.append((forward, reverse))
    ratios = [bennett_log_ratio(np.concatenate(a), np.concatenate(b)) for a, b in edges]
    if method == "cross_chain":
        chain_ratios = np.asarray([[bennett_log_ratio(a[j], b[j]) for a, b in edges]
                                   for j in range(k)])
        covariance = np.atleast_2d(np.cov(chain_ratios, rowvar=False, ddof=1)) / k
    else:
        rng = np.random.default_rng(bootstrap_seed)
        rectangular = [(np.stack(a), np.stack(b)) for a, b in edges]
        draws = []
        for _ in range(bootstrap_replicates):
            indices = [_block_indices((trace.shape[0], trace.shape[1]-cut[0]), block, rng)
                       for trace, cut in zip(states, cuts)]
            draws.append([bennett_log_ratio(np.take_along_axis(a, indices[i], axis=1),
                                            np.take_along_axis(b, indices[i+1], axis=1))
                          for i, (a, b) in enumerate(rectangular)])
        covariance = np.atleast_2d(np.cov(draws, rowvar=False, ddof=1))
    return ratios, float(covariance.sum())


def _anchored_estimate(anchor, ratios, mcmc_log_variance):
    log_var_anchor = (0.0 if anchor.kind == "exact" else
                      (1-anchor.estimate)/(anchor.trials*anchor.estimate))
    log_estimate = math.log(anchor.estimate) + sum(ratios)
    se = math.sqrt(max(0.0, log_var_anchor + mcmc_log_variance))
    estimate = math.exp(log_estimate)
    interval = (math.exp(min(0.0, log_estimate-Z*se)),
                math.exp(min(0.0, log_estimate+Z*se))) if log_estimate <= 0 else None
    return estimate, interval, se


def _se(means):
    return float(np.std(means, ddof=1) / math.sqrt(len(means)))


def _ratio(num, den):
    return num / den if den > 0 else (math.inf if num > 0 else None)


def _convergence(states, cuts, other_states=None, other_cuts=None):
    """Use unburned checkpoints for S/D and individually burned means for M/R."""
    reports = []
    for i, (trace, cut) in enumerate(zip(states, cuts)):
        weights = np.count_nonzero(trace, axis=-1).astype(float)
        k, n = weights.shape
        quarter, half = n//4, n//2
        ref_sd = float(np.std(weights[:, :quarter].mean(axis=1), ddof=1))
        final_sd = float(np.std(weights.mean(axis=1), ddof=1))
        scale_ratio = _ratio(final_sd, ref_sd*math.sqrt(quarter/n))
        scaling = None if scale_ratio is None else scale_ratio <= 1.5
        drift = abs(weights[:, half:].mean()-weights[:, quarter:half].mean())
        drift_ratio = _ratio(drift, _se(weights.mean(axis=1))*math.sqrt(
            n*(1/(half-quarter)+1/(n-half))))
        stationary = None if drift_ratio is None else drift_ratio <= 3
        burned = [weights[j, cut[j]:] for j in range(k)]
        means = np.asarray([row.mean() for row in burned])
        sd = float(np.std(means, ddof=1))
        within = float(np.mean([np.var(row, ddof=1) for row in burned]))
        tau = float(np.median([max(research_iat(row), 1.0) for row in burned]))
        n_used = float(np.median([len(row) for row in burned]))
        dispersion_ratio = _ratio(sd, math.sqrt(within*tau/n_used))
        dispersion = None if dispersion_ratio is None else dispersion_ratio <= 3
        flags = [scaling, stationary, dispersion]
        vacuous = False if False in flags else (None if None in flags else True)
        auxiliary = None
        if other_states is not None:
            other_weights = np.count_nonzero(other_states[i], axis=-1).astype(float)
            other_burned = [other_weights[j, other_cuts[i][j]:] for j in range(k)]
            other_means = np.asarray([row.mean() for row in other_burned])
            z = _ratio(abs(means.mean()-other_means.mean()),
                       math.hypot(_se(means), _se(other_means)))
            auxiliary = None if z is None else z <= 3
        auxiliary_flags = flags + [auxiliary]
        auxiliary_full = (False if False in auxiliary_flags else
                          None if None in auxiliary_flags else True)
        paper_full = False if False in flags else None
        reports.append((paper_full, vacuous, flags, auxiliary, auxiliary_full))
    paper_flags = [item[0] for item in reports]
    paper_full = False if False in paper_flags else None
    vacuous_flags = [item[1] for item in reports]
    paper_vacuous = False if False in vacuous_flags else (None if None in vacuous_flags else True)
    aux_flags = [item[4] for item in reports]
    aux_full = False if False in aux_flags else (None if None in aux_flags else True)
    return paper_full, paper_vacuous, aux_full, reports


def run(args):
    start = time.perf_counter()
    out = output_dir(args.out)
    chains, burn_mode, method = PROTOCOLS[args.protocol]
    ladder = LADDERS[args.region]
    code = make_toric_code(3)
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
    if args.make_truth_cache:
        payload = make_truth_cache(args.make_truth_cache, code, problem)
        print(dict(path=str(Path(args.make_truth_cache).resolve()),
                   problem_sha256=payload["problem_sha256"],
                   failures=sum(payload["failure_weight_counts"])))
        return
    cache = load_truth_cache(args.truth_cache, code, problem) if args.truth_cache else None
    short, long = minimum_weight_initial_state(code), maximum_weight_initial_state(code)
    distinct_start = not np.array_equal(short, long)
    alternate = np.bitwise_xor(code.lx[0], code.lx[1]).astype(np.uint8)
    if args.aux_multistart and (np.array_equal(alternate, short) or not problem.is_faulty(alternate)):
        raise RuntimeError("No distinct faulty auxiliary start")
    if cache is not None:
        truth = cached_exact(problem, ladder[-1], cache).estimate
    else:
        truth = exact(problem, ladder[-1]).estimate
    exact_anchor = (cached_exact(problem, ladder[0], cache) if cache is not None and args.anchor in ("exact", "both")
                    else exact(problem, ladder[0]) if args.anchor in ("exact", "both") else None)
    rows = []
    for seed in range(args.seed_start, args.seed_start+args.seeds):
        anchor_seed, bar_seed, _, _, auxiliary_seed = spawn_seeds(seed, 5)
        anchors = []
        if args.anchor in ("mc", "both"):
            mc_anchor = direct_mc(problem, ladder[0], trials=args.anchor_trials, seed=anchor_seed)
            if mc_anchor.estimate <= 0 or mc_anchor.estimate >= 1:
                raise RuntimeError(f"seed {seed}: MC anchor lacks failures or successes")
            anchors.append(("mc", mc_anchor))
        if exact_anchor is not None:
            anchors.append(("exact", exact_anchor))
        sequence = np.random.SeedSequence(bar_seed)
        children = sequence.spawn(len(ladder)+1)
        rung_seeds = [int(child.generate_state(1, dtype=np.uint64)[0])
                      for child in children[:-1]]
        # Save the whole trace, then apply either a fixed or iterated post-hoc cut.
        # Both uncertainty methods read these same states and pooled BAR ratios.
        total = args.samples + (180 if burn_mode == "fixed" else 0)
        kernels = KernelConfig(lazy=0.0) if burn_mode == "iat5" else KernelConfig()
        config = SamplingConfig(chains=chains, samples=total, burn_in=0, kernels=kernels)
        start_state = None if burn_mode == "fixed" else short
        states = [sample_faulty(problem, p, config=config, seed=s, initial_state=start_state).states
                  for p, s in zip(ladder, rung_seeds)]
        if burn_mode == "fixed":
            cuts, capped = [[180]*chains for _ in ladder], [[False]*chains for _ in ladder]
        else:
            cut_info = [[paper_burn_cut(row) for row in np.count_nonzero(trace, axis=-1)]
                        for trace in states]
            cuts = [[v[0] for v in rung] for rung in cut_info]
            capped = [[v[1] for v in rung] for rung in cut_info]
        other_states, other_cuts = None, None
        if args.aux_multistart:
            other_children = np.random.SeedSequence(auxiliary_seed).spawn(len(ladder))
            other_seeds = [int(child.generate_state(1, dtype=np.uint64)[0]) for child in other_children]
            other_states = [sample_faulty(problem, p, config=config, seed=s, initial_state=alternate).states
                            for p, s in zip(ladder, other_seeds)]
            other_cuts = ([[180]*chains for _ in ladder] if burn_mode == "fixed" else
                          [[paper_burn_cut(row)[0] for row in np.count_nonzero(trace, axis=-1)]
                           for trace in other_states])
        full, vacuous, auxiliary_full, rule_details = _convergence(states, cuts, other_states, other_cuts)
        ratios, mcmc_log_variance = _bar_from_traces(
            problem, ladder, states, cuts, method, args.bootstrap_replicates,
            args.block, children[-1])
        for anchor_kind, anchor in anchors:
            estimate, interval, se = _anchored_estimate(anchor, ratios, mcmc_log_variance)
            if args.verify_api:
                if burn_mode != "fixed":
                    raise ValueError("--verify-api applies only to fixed-burn protocols")
                api = estimate_logical_error(problem, ladder, anchor=anchor,
                    config=SamplingConfig(chains=chains, samples=args.samples, burn_in=180,
                                          kernels=kernels),
                    seed=bar_seed, uncertainty=method,
                    bootstrap_replicates=args.bootstrap_replicates,
                    bootstrap_block_length=args.block)
                if not (np.isclose(api.estimate, estimate, rtol=0, atol=1e-12) and
                        np.isclose(api.log_standard_errors[-1], se, rtol=0, atol=1e-12) and
                        np.allclose(api.adjacent_log_ratios, ratios, rtol=0, atol=1e-12) and
                        np.allclose(api.interval, interval, rtol=0, atol=1e-12)):
                    raise AssertionError(f"seed {seed}: benchmark and API differ")
            rows.append(dict(region=args.region, protocol=args.protocol, anchor_kind=anchor_kind,
                             seed=seed, samples=args.samples, total_steps=total,
                             chains=chains, ladder="/".join(map(str, ladder)),
                             problem_sha256=_problem_digest(code, problem),
                             truth_cache_source_sha256=cache["package_source_sha256"] if cache is not None else "",
                             truth_source="checked_weight_cache" if cache is not None else "fresh_exact",
                             bootstrap_replicates=args.bootstrap_replicates, block=args.block,
                             anchor_trials=args.anchor_trials, lazy=kernels.lazy,
                             cuts="/".join(",".join(map(str, rung)) for rung in cuts),
                             burn_capped=any(any(rung) for rung in capped),
                             estimate=estimate, low=interval[0] if interval else "",
                             high=interval[1] if interval else "", exact=truth,
                             covered=interval is not None and interval[0] <= truth <= interval[1],
                             log_se=se, ratios="/".join(map(str, ratios)),
                             four_rule_pass=full, paper_vacuous_pass=vacuous,
                             auxiliary_four_rule_pass=auxiliary_full,
                             scaling="/".join(str(r[2][0]) for r in rule_details),
                             drift="/".join(str(r[2][1]) for r in rule_details),
                             multistart=("/".join(str(r[3]) for r in rule_details) if args.aux_multistart
                                         else "unresolved_same_basis" if not distinct_start else "unmeasured"),
                             auxiliary_start=args.aux_multistart,
                             dispersion="/".join(str(r[2][2]) for r in rule_details),
                             warnings=WARNINGS))
    for anchor_kind in ("mc", "exact"):
        selected = [row for row in rows if row["anchor_kind"] == anchor_kind]
        if not selected:
            continue
        name = f"{args.region}_{args.protocol}_{anchor_kind}_{args.seed_start}_{args.seeds}"
        write_csv(out / f"{name}_runs.csv", selected)
        summary = _summary([{key: str(value) for key, value in row.items()} for row in selected],
                           time.perf_counter()-start)
        write_csv(out / f"{name}_summary.csv", [summary])
        print(summary)
    print(f"CSV: {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="One seed with an 80-step paper trace or 80 fixed-cut retained steps")
    parser.add_argument("--seed", type=int, help="Alias for --seed-start with one seed")
    parser.add_argument("--seed-start", type=int, default=2026)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--region", choices=LADDERS, default="dev4")
    parser.add_argument("--protocol", choices=PROTOCOLS, default="default_block")
    parser.add_argument("--anchor", choices=("mc", "exact", "both"), default="mc",
                        help="Both reuses the same rung and auxiliary trajectories for MC and exact anchors")
    parser.add_argument("--samples", type=int, default=600,
                        help="Retained steps for fixed-cut protocols; full trace steps before IAT cut for paper protocols")
    parser.add_argument("--anchor-trials", type=int, default=1500)
    parser.add_argument("--make-truth-cache", help="Enumerate the failure-weight histogram once and write a checked cache")
    parser.add_argument("--truth-cache", help="Checked failure-weight cache for exact truth and exact anchor")
    parser.add_argument("--bootstrap-replicates", type=int, default=30)
    parser.add_argument("--block", type=int, default=8)
    parser.add_argument("--aux-multistart", action="store_true",
                        help="Also sample a distinct faulty logical combination for all four convergence rules")
    parser.add_argument("--verify-api", action="store_true",
                        help="Recompute the fixed-cut case with the API and compare point estimate and interval")
    parser.add_argument("--aggregate", help="Directory of split *_runs.csv files; require full fixed cohort")
    parser.add_argument("--out", default=str(Path(tempfile.gettempdir()) / "mcmc4qec" / "bar_paper_protocol"))
    args = parser.parse_args()
    if args.aggregate:
        aggregate(args.aggregate, args.out, args.truth_cache)
        return
    if args.seed is not None:
        args.seed_start, args.seeds = args.seed, 1
    if args.quick:
        args.seeds, args.samples, args.bootstrap_replicates = 1, 80, 4
    if args.seeds < 1 or args.samples < 8 or args.bootstrap_replicates < 2 or args.block < 2:
        parser.error("seeds, samples, bootstrap-replicates, and block must be positive valid counts")
    if not args.quick and not set(range(args.seed_start, args.seed_start+args.seeds)) <= set(COHORT):
        parser.error("production seeds must be a contiguous slice of 2026..2045")
    run(args)


if __name__ == "__main__":
    main()
