"""Measure toric d=3 BAR coverage and one-factor sensitivities against exact.

Requires mcmc4qec[codes,matching]. Each invocation is bounded by --seeds and
is intended to finish within ten minutes (20 baseline seeds takes much less
on the development machine). This is a benchmark, never called by pytest.
Intervals assume mixing and adequate blocks; diagnostics do not prove either.
"""

import argparse
import csv
import math
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace

import numpy as np

from mcmc4qec import (IndependentBitFlip, Problem, SamplingConfig, direct_mc,
                      estimate_logical_error, exact, sample_faulty, spawn_seeds)
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import mwpm_decoder
from mcmc4qec.initial_states import (maximum_weight_initial_state,
                                     minimum_weight_initial_state,
                                     random_logical_sector_initial_state)


SCENARIOS = (
    "baseline", "samples_short", "samples_long", "samples_short_auto",
    "samples_long_auto", "burn_zero", "burn_long",
    "block_tenth_iat", "block_one_iat", "block_four_iat",
    "ladder_fine", "ladder_coarse",
    "initial_min", "initial_random", "initial_max", "anchor_exact", "low_p",
)


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def output_dir(value):
    path = Path(value).expanduser().resolve()
    roots = [Path("C:/dev/RIMC"), Path("A:/dev/RIMC")]
    roots += [Path(os.environ[name]) for name in ("RIMC_RESEARCH_ROOT", "RESEARCH_ROOT")
              if os.environ.get(name)]
    for forbidden in roots:
        root = forbidden.resolve()
        if path == root or root in path.parents:
            raise ValueError("Refusing to write into the read-only RIMC repository")
    path.mkdir(parents=True, exist_ok=True)
    return path


def pilot_iat(problem, p):
    pilot = sample_faulty(problem, p, config=SamplingConfig(chains=4,
                          samples=600, burn_in=180), seed=1984)
    values = [value for value in pilot.diagnostics["chain_iat"] if value is not None]
    return max(values) if values else None


def initial_states(code, problem, scenario, seed, rungs):
    if not scenario.startswith("initial_"):
        return None
    if scenario == "initial_min":
        state = minimum_weight_initial_state(code)
    elif scenario == "initial_max":
        state = maximum_weight_initial_state(code)
    else:
        state = random_logical_sector_initial_state(code, seed=seed)
    if not problem.is_faulty(state):
        raise ValueError(f"{scenario} does not initialize a failure state")
    return [state] * rungs


def run(args):
    start = time.perf_counter()
    out = output_dir(args.out)
    code = make_toric_code(3)
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n),
                      mwpm_decoder(code))
    ladder = [0.30, 0.26, 0.22]
    if args.scenario == "ladder_fine":
        ladder = [0.30, 0.28, 0.26, 0.24, 0.22]
    elif args.scenario == "ladder_coarse":
        ladder = [0.30, 0.22]
    elif args.scenario == "low_p":
        ladder = [0.18, 0.14, 0.10]
    config_kwargs = dict(chains=4, samples=600, burn_in=180)
    if args.scenario in ("samples_short", "samples_short_auto"):
        config_kwargs["samples"] = 200
    elif args.scenario in ("samples_long", "samples_long_auto"):
        config_kwargs["samples"] = 1200
    elif args.scenario == "burn_zero":
        config_kwargs["burn_in"] = 0
    elif args.scenario == "burn_long":
        config_kwargs["burn_in"] = 600
    config = SamplingConfig(**config_kwargs)
    # Hold the baseline's eight-step block fixed in the controlled sample-count
    # comparisons. The *_auto scenarios retain the library's cube-root rule.
    block = 8 if args.scenario in ("samples_short", "samples_long") else None
    pilot_tau = None
    if args.scenario.startswith("block_"):
        pilot_tau = pilot_iat(problem, ladder[-1])
        if pilot_tau is None:
            raise RuntimeError("pilot IAT unavailable")
        multiplier = {"block_tenth_iat": 0.1, "block_one_iat": 1.0,
                      "block_four_iat": 4.0}[args.scenario]
        block = min(config.samples, max(2, math.ceil(multiplier * pilot_tau)))
    if args.truth_file:
        if not args.trust_truth_file:
            raise ValueError("--truth-file requires --trust-truth-file; verify same toric d=3 problem")
        with Path(args.truth_file).open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 1 or float(rows[0]["target_p"]) != ladder[-1]:
            raise ValueError("truth file must contain one row for target p")
        truth = SimpleNamespace(estimate=float(rows[0]["exact_estimate"]),
                                conditional_weight=float(rows[0]["exact_conditional_weight"]))
    else:
        truth = exact(problem, ladder[-1])
    exact_anchor = exact(problem, ladder[0]) if args.scenario == "anchor_exact" else None
    records = []
    for number in range(args.seeds):
        seed = args.seed_start + number
        anchor_seed, bar_seed, _, check_seed = spawn_seeds(seed, 4)
        anchor = exact_anchor or direct_mc(problem, ladder[0], trials=1500,
                                           seed=anchor_seed)
        if anchor.kind == "direct_mc" and not 0 < anchor.failures < anchor.trials:
            raise RuntimeError("MC anchor needs observed failures and successes")
        bar = estimate_logical_error(
            problem, ladder, anchor=anchor, config=config, seed=bar_seed,
            initial_states=initial_states(code, problem, args.scenario, seed,
                                          len(ladder)),
            bootstrap_replicates=args.bootstrap_replicates,
            bootstrap_block_length=block)
        mc = direct_mc(problem, ladder[-1], trials=1200, seed=check_seed)
        taus = [value for report in bar.diagnostics for value in report["chain_iat"]
                if value is not None]
        interval = bar.interval
        overlap = interval is not None and max(interval[0], mc.interval[0]) <= min(
            interval[1], mc.interval[1])
        records.append(dict(
            scenario=args.scenario, seed=seed, target_p=ladder[-1],
            ladder="/".join(map(str, ladder)), samples=config.samples,
            burn_in=config.burn_in, chains=config.chains,
            block_length=bar.metadata["config"]["bootstrap_block_length"],
            block_over_max_iat=(bar.metadata["config"]["bootstrap_block_length"] /
                                max(taus)) if taus else "",
            max_chain_iat=max(taus) if taus else "",
            pilot_iat=pilot_tau if pilot_tau is not None else "",
            anchor_kind=anchor.kind, anchor_estimate=anchor.estimate,
            bar_estimate=bar.estimate,
            bar_low=interval[0] if interval else "",
            bar_high=interval[1] if interval else "",
            bar_width=interval[1]-interval[0] if interval else "",
            bar_covers_exact=(interval[0] <= truth.estimate <= interval[1])
                             if interval else "",
            mc_estimate=mc.estimate, mc_low=mc.interval[0],
            mc_high=mc.interval[1],
            mc_conditional_weight=mc.conditional_weight,
            mc_covers_exact=mc.interval[0] <= truth.estimate <= mc.interval[1],
            intervals_overlap=overlap if interval else "",
            min_bar_overlap=min(min(edge["forward_mean"], edge["reverse_mean"])
                                for edge in bar.overlap),
            min_cross_fraction=min(min(edge["finite_cross_fraction_a"],
                                       edge["finite_cross_fraction_b"])
                                   for edge in bar.overlap),
            target_chain_weight=np.mean(bar.diagnostics[-1]["chain_means"]),
            target_chain_weight_range=(max(bar.diagnostics[-1]["chain_means"])-
                                       min(bar.diagnostics[-1]["chain_means"])),
            exact_estimate=truth.estimate,
            exact_conditional_weight=truth.conditional_weight,
            truth_source=str(Path(args.truth_file).resolve()) if args.truth_file else "exact",
            bootstrap_successes=bar.metadata["config"]["bootstrap_successes"],
        ))
    widths = [float(row["bar_width"]) for row in records if row["bar_width"] != ""]
    summary = dict(scenario=args.scenario, seeds=args.seeds,
                   seed_start=args.seed_start, target_p=ladder[-1],
                   exact_estimate=truth.estimate,
                   exact_conditional_weight=truth.conditional_weight,
                   truth_source=str(Path(args.truth_file).resolve()) if args.truth_file else "exact",
                   bar_covered=sum(row["bar_covers_exact"] is True for row in records),
                   bar_intervals=len(widths),
                   mc_covered=sum(row["mc_covers_exact"] for row in records),
                   interval_nonintersection=sum(row["intervals_overlap"] is False
                                                for row in records),
                   mean_bar_width=float(np.mean(widths)) if widths else "",
                   mean_min_overlap=float(np.mean([row["min_bar_overlap"]
                                                  for row in records])),
                   median_max_iat=float(np.median([row["max_chain_iat"]
                                                   for row in records
                                                   if row["max_chain_iat"] != ""])),
                   elapsed_seconds=time.perf_counter()-start)
    write_csv(out / f"{args.scenario}_runs.csv", records)
    write_csv(out / f"{args.scenario}_summary.csv", [summary])
    print(summary)
    print(f"CSV: {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="baseline")
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=2026)
    parser.add_argument("--bootstrap-replicates", type=int, default=30)
    parser.add_argument("--truth-file", help="Reuse exact value from an earlier summary CSV")
    parser.add_argument("--trust-truth-file", action="store_true",
                        help="Assert the truth CSV came from this same toric d=3/MWPM problem")
    parser.add_argument("--out", default=str(Path(tempfile.gettempdir()) /
                        "mcmc4qec" / "bar_sensitivity"))
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    run(args)


if __name__ == "__main__":
    main()
