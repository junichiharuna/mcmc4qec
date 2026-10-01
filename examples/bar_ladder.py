"""Exact-anchored BAR ladder on a small, exactly enumerable CSS problem.

Requires core only. Measured default/--quick: about 0.5s/0.3s on Windows.
The decoder is fixed at every rung; exact gives the absolute anchor.
BAR intervals assume mixing and adequate blocks, which diagnostics cannot prove.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip, KernelConfig,
                      Problem, SamplingConfig, estimate_logical_error, exact)


def output_dir(value):
    path = Path(value).expanduser().resolve()
    roots = [Path(os.environ[name]) for name in ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT') if os.environ.get(name)]
    for root in roots:
        if path == root.resolve() or root.resolve() in path.parents:
            raise ValueError('output directory cannot be inside the research repository')
    path.mkdir(parents=True, exist_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=73)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
                   [[1, 1, 1]], [[1, 0, 0]])
    decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                              identifier="repetition3-minimum-weight-v1")
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
    ladder = [0.4, 0.25, 0.1]
    result = estimate_logical_error(
        problem, ladder, anchor=exact(problem, ladder[0]),
        config=SamplingConfig(samples=100 if args.quick else 200, burn_in=15 if args.quick else 30,
                              kernels=KernelConfig(cluster_k=1)),
        seed=args.seed, bootstrap_replicates=10 if args.quick else 30,
    )
    for p, estimate, interval in zip(ladder, result.estimates, result.intervals):
        print(f"p={p}: BAR P_L={estimate:.5f}, interval={interval}")
    exact_final = exact(problem, ladder[-1]).estimate
    print("Exact final P_L:", exact_final)
    summary = dict(ladder=ladder, bar=result.estimates, intervals=result.intervals, exact=exact_final)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == "__main__":
    main()
