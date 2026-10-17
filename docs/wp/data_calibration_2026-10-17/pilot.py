"""Bounded local API/timing pilot, never a coverage experiment.

Run with PYTHONPATH=src and Python 3.11. Each of three cases has one fixed
seed, four chains, 600 retained states and 600 burn-in steps. Public exact
enumeration supplies both anchor and target truth. No cluster is contacted.
Existing outputs are not overwritten. Timings cannot set cluster walltimes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import mcmc4qec as qec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", choices=("toric_d3", "surface_d3", "steane"),
                        default=["toric_d3", "surface_d3", "steane"])
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parent / "pilot_results.json")
    args = parser.parse_args()
    if len(args.cases) != len(set(args.cases)):
        parser.error("duplicate cases")
    out = args.out
    if out.exists():
        raise FileExistsError(f"Preserve the previous pilot: {out}")
    cases = [
        ("toric_d3", lambda: qec.make_toric_code(3), qec.mwpm_decoder),
        ("surface_d3", lambda: qec.make_surface_code(3), qec.mwpm_decoder),
        ("steane", qec.make_steane_code,
         lambda code: qec.bposd_decoder(code, .03, osd_order=2)),
    ]
    ladder = [.10, .07, .05, .03]
    config = qec.SamplingConfig(samples=600, burn_in=600, chains=4,
                               cache_cap=200000, cache_policy="lru")
    records = []
    for number, (name, factory, decoder_factory) in enumerate(cases):
        if name not in args.cases:
            continue
        start = time.perf_counter()
        code = factory()
        problem = qec.Problem(code.bit_flip_model(), qec.IndependentBitFlip(code.n),
                              decoder_factory(code))
        truth_start = time.perf_counter()
        anchor = qec.exact(problem, ladder[0])
        truth = qec.exact(problem, ladder[-1])
        exact_seconds = time.perf_counter() - truth_start
        print(json.dumps(dict(code=name, phase="exact_complete",
                              exact_seconds=exact_seconds)), flush=True)
        bar_start = time.perf_counter()
        result = qec.estimate_logical_error(
            problem, ladder, anchor=anchor, config=config, seed=91000 + number,
            bootstrap_replicates=100, bootstrap_block_length=32,
        )
        bar_seconds = time.perf_counter() - bar_start
        # Round-trip the entire record before writing any successful artifact.
        qec.EstimationResult.from_json(result.to_json())
        records.append(dict(code=name, seed=91000 + number, n=code.n,
                            exact_seconds=exact_seconds, bar_wall_seconds=bar_seconds,
                            total_seconds=time.perf_counter() - start,
                            target_truth=json.loads(truth.to_json()),
                            anchor=json.loads(anchor.to_json()),
                            result=json.loads(result.to_json())))
        print(json.dumps(dict(code=name, exact_seconds=exact_seconds,
                              bar_seconds=bar_seconds, estimate=result.estimate,
                              truth=truth.estimate), allow_nan=False), flush=True)
    payload = dict(purpose="API and local timing pilot; no coverage inference",
                   python=sys.version, executable=sys.executable, platform=platform.platform(),
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   records=records)
    with out.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
