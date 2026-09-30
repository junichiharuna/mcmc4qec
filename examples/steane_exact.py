"""Steane exact reference, direct MC and exact-anchored BAR at every rung.

Requires core only. Measured default/--quick: about 2.4s/0.5s on Windows.
The minimum-weight decoder is fixed across the ladder; the exact first rung
anchors P_L. BAR intervals assume adequate mixing and block length; chain
frequencies alone do not estimate absolute P_L or prove correctness.
"""
import argparse
from itertools import product
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (CallableDecoder, IndependentBitFlip, Problem, SamplingConfig,
                       direct_mc, estimate_logical_error, exact, spawn_seeds)
from mcmc4qec.codes import make_steane_code


def output_dir(value):
    path = Path(value).expanduser().resolve()
    roots = [Path('C:/dev/RIMC'), Path('A:/dev/RIMC')]
    roots += [Path(os.environ[name]) for name in ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT') if os.environ.get(name)]
    for root in roots:
        if path == root.resolve() or root.resolve() in path.parents:
            raise ValueError('output directory cannot be inside the research repository')
    path.mkdir(parents=True, exist_ok=True)
    return path


def minimum_weight_decoder(code):
    table = {}
    # Product order supplies a deterministic tie-break between equal weights.
    for bits in product((0, 1), repeat=code.n):
        correction = np.asarray(bits, dtype=np.uint8)
        syndrome = tuple((code.hz @ correction % 2).tolist())
        weight = int(correction.sum())
        if syndrome not in table or weight < table[syndrome][0]:
            table[syndrome] = (weight, (code.lz @ correction % 2).tolist())
    assert len(table) == 2 ** len(code.hz)
    return CallableDecoder(lambda syndrome: table[tuple(syndrome)][1],
                           identifier='steane-enumerated-minimum-weight-v1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=20260930)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    code = make_steane_code()
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), minimum_weight_decoder(code))
    ladder = [0.4, 0.3, 0.2]
    references = [exact(problem, p) for p in ladder]
    seeds = spawn_seeds(args.seed, len(ladder) + 1)
    mc = [direct_mc(problem, p, trials=300 if args.quick else 3000, seed=seed)
          for p, seed in zip(ladder, seeds[:-1])]
    bar = estimate_logical_error(problem, ladder, anchor=references[0],
                                 config=SamplingConfig(samples=100 if args.quick else 600,
                                                       burn_in=20 if args.quick else 100),
                                 seed=seeds[-1], bootstrap_replicates=20 if args.quick else 60)
    inside_bar = []
    for p, ref, trial, estimate, interval in zip(ladder, references, mc, bar.estimates, bar.intervals):
        covered = interval is not None and interval[0] <= ref.estimate <= interval[1]
        inside_bar.append(covered)
        direct_covered = trial.interval[0] <= ref.estimate <= trial.interval[1]
        print(f'p={p}: exact={ref.estimate:.6g}; direct MC={trial.estimate:.6g} {trial.interval} '
              f'(contains exact={direct_covered}); BAR={estimate:.6g} {interval} '
              f'(contains exact={covered})')
    print(f'BAR intervals containing exact: {sum(inside_bar)}/{len(ladder)}')
    print('BAR intervals assume chain mixing and sufficient block length; diagnostics do not prove either.')
    summary = dict(code='Steane-7', ladder=ladder, exact=[r.estimate for r in references],
                   bar=bar.estimates, bar_intervals=bar.intervals)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == '__main__':
    main()
