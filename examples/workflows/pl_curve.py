"""Estimate toric d=3,5 P_L(p) with anchored BAR and direct-MC checks.

Requires mcmc4qec[matching,codes]; matplotlib via mcmc4qec[plot] is optional.
Typical runtime: --quick under 10 s, default under 120 s.
The unweighted MWPM decoder is fixed across each ladder. An MC anchor must
observe failures. The anchor point is reused in the check table; independent
direct-MC validation is at the two non-anchor rungs. Neighboring rungs need
sampled bidirectional overlap; a
coarse ladder can have poor overlap, but finite full-support p values alone
do not imply the strict zero-support condition that raises OverlapError.
The --demo-overlap endpoint example uses p=0 and p=1, whose supports are
disjoint, to demonstrate that exact condition. Conditional chains alone do
not estimate absolute P_L. BAR intervals assume mixing and adequate blocks.
The quick budget only checks the workflow; it does not provide research-grade
precision. Nonoverlapping BAR and independent direct-MC intervals require
investigation, with inadequate mixing and finite-sample noise among possible
causes. For the default d=3, p=0.22 problem, exact P_L=0.6026625647:
seed 2026's BAR interval misses it while the independent MC interval covers it.
Exploratory seeds 2026..2045 gave BAR coverage 13/20 and MC coverage 20/20.
Default block 8 was shorter than the median maximum weight IAT (35.69);
larger blocks widened intervals but did not fix seed 2026's estimate.
See docs/bar_sensitivity_ja.md for controlled block, sample, and ladder checks.
"""

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (CSSCode, CallableDecoder, CallableFailure,
                      IndependentBitFlip, KernelConfig, Problem, SamplingConfig,
                      OverlapError, direct_mc, estimate_logical_error, exact,
                      spawn_seeds)
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import mwpm_decoder


def output_dir(value):
    path = Path(value).expanduser().resolve()
    roots = [Path('C:/dev/RIMC'), Path('A:/dev/RIMC')]
    roots += [Path(os.environ[name]) for name in ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT')
              if os.environ.get(name)]
    for forbidden in roots:
        root = forbidden.resolve()
        if path == root or root in path.parents:
            raise ValueError('Refusing to write into the read-only RIMC repository')
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_rows(rows, out):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('matplotlib unavailable; PNG omitted; numeric data saved in CSV')
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    for distance in (3, 5):
        subset = sorted((r for r in rows if r['distance'] == distance), key=lambda r: r['p'])
        line, = ax.plot([r['p'] for r in subset], [r['bar'] for r in subset],
                        'o-', label=f'BAR d={distance}')
        with_interval = [r for r in subset if r['bar_low'] is not None and
                         r['bar_high'] is not None]
        if with_interval:
            ax.errorbar([r['p'] for r in with_interval], [r['bar'] for r in with_interval],
                        yerr=[[r['bar']-r['bar_low'] for r in with_interval],
                              [r['bar_high']-r['bar'] for r in with_interval]],
                        fmt='none', ecolor=line.get_color(), capsize=3)
        checks = [r for r in subset if r['mc'] is not None]
        ax.errorbar([r['p'] for r in checks], [r['mc'] for r in checks],
                    yerr=[[r['mc']-r['mc_low'] for r in checks],
                          [r['mc_high']-r['mc'] for r in checks]],
                    fmt='x', capsize=3, label=f'direct MC d={distance}')
    ax.set(xlabel='physical bit-flip p', ylabel='logical failure probability')
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / 'pl_curve.png', dpi=110)
    plt.close(fig)


def demonstrate_overlap(seed):
    # This one-bit didactic problem marks both states in its common failure
    # set, while endpoint noise distributions support opposite states.
    code = CSSCode(np.zeros((0, 1), dtype=int), np.zeros((0, 1), dtype=int),
                   [[1]], [[1]])
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(1),
                      CallableDecoder(lambda syndrome: [0], identifier='zero-one-bit'),
                      failure=CallableFailure(lambda state, predicted, truth: True,
                                              identifier='all-states-for-overlap-demo'))
    try:
        estimate_logical_error(
            problem, [0.0, 1.0], anchor=exact(problem, 0.0),
            config=SamplingConfig(samples=8, burn_in=2,
                                  kernels=KernelConfig(single=1, zanella=0,
                                                       cluster=0, stabilizer=0)),
            seed=seed, bootstrap_replicates=0,
        )
    except OverlapError as exc:
        print(f'OverlapError from estimate_logical_error on disjoint endpoint supports '
              f'p=0 and p=1: {exc}')
        return
    raise AssertionError('Expected OverlapError for disjoint supports')


def compare_intervals(bar_interval, mc_interval, distance, p):
    if bar_interval is None:
        return None, (f'WARNING: d={distance} p={p:.2f} BAR interval is unavailable; '
                      'overlap check cannot be made.')
    overlap = max(bar_interval[0], mc_interval[0]) <= min(bar_interval[1], mc_interval[1])
    if not overlap:
        return False, (f'WARNING: d={distance} p={p:.2f} BAR and independent direct-MC '
                       'intervals do not overlap; investigate mixing and finite-sample '
                       'effects. Cause not diagnosed here.')
    return True, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--out', default=str(Path(tempfile.gettempdir()) / 'mcmc4qec' / 'pl_curve'))
    parser.add_argument('--demo-overlap', action='store_true')
    args = parser.parse_args()
    out = output_dir(args.out)
    print(f'Output: {out}')
    print('The anchor point reuses its MC anchor; independent direct-MC checks are at the two non-anchor rungs.')
    if args.quick:
        print('WARNING: --quick checks the workflow only; it does not guarantee research precision.')
    ladder = [0.30, 0.26, 0.22]
    anchor_trials = 200 if args.quick else 1500
    check_trials = 180 if args.quick else 1200
    config = SamplingConfig(chains=4, samples=40 if args.quick else 600,
                            burn_in=12 if args.quick else 180)
    seeds = iter(spawn_seeds(args.seed, 9))
    rows = []
    estimates, intervals, checks = {}, {}, {}
    for distance in (3, 5):
        code = make_toric_code(distance)
        problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
        anchor = direct_mc(problem, ladder[0], trials=anchor_trials, seed=next(seeds))
        if not 0 < anchor.failures < anchor.trials:
            raise RuntimeError('MC anchor needs both observed failures and successes; increase trials')
        print(f'd={distance} anchor p={ladder[0]}: {anchor.failures}/{anchor.trials} failures')
        bar = estimate_logical_error(problem, ladder, anchor=anchor, config=config,
                                     seed=next(seeds), bootstrap_replicates=10 if args.quick else 30)
        key = f'toric_d{distance}'
        estimates[key], intervals[key], checks[key] = bar.estimates, bar.intervals, {}
        for index, p in enumerate(ladder):
            mc = anchor if index == 0 else direct_mc(problem, p, trials=check_trials,
                                                     seed=next(seeds))
            interval = bar.intervals[index]
            intervals_overlap, warning = compare_intervals(interval, mc.interval,
                                                            distance, p)
            rows.append(dict(distance=distance, p=p, bar=bar.estimates[index],
                             bar_low=interval[0] if interval else None,
                             bar_high=interval[1] if interval else None,
                             mc=mc.estimate if mc else None,
                             mc_low=mc.interval[0] if mc else None,
                             mc_high=mc.interval[1] if mc else None,
                             mc_role='anchor_reuse' if index == 0 else 'independent_direct_mc',
                             intervals_overlap=intervals_overlap))
            checks[key][str(p)] = {'estimate': mc.estimate, 'interval': mc.interval,
                                    'failures': mc.failures, 'trials': mc.trials,
                                    'mc_role': 'anchor_reuse' if index == 0 else 'independent_direct_mc',
                                    'intervals_overlap': intervals_overlap}
            print(f'd={distance} p={p:.2f} BAR={bar.estimates[index]:.5g} {interval}; '
                  f'direct MC={mc.estimate} {mc.interval}; '
                  f'intervals_overlap={intervals_overlap}')
            if warning:
                print(warning)
        print(f'd={distance} minimum observed BAR overlap: '
              f'{min(min(x["forward_mean"], x["reverse_mean"]) for x in bar.overlap):.3g}')
    with (out / 'pl_curve.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    plot_rows(rows, out)
    if args.demo_overlap:
        demonstrate_overlap(next(seeds))
    print('BAR intervals assume adequate mixing and block length; inspect overlap and diagnostics.')
    print('Recorded default d=3, p=0.22 study: exact P_L=0.6026625647; '
          'seed 2026 BAR missed truth, independent MC covered it. '
          'Over 20 seeds: BAR coverage 13/20, MC 20/20. '
          'Block 8 was shorter than median maximum weight IAT 35.69; '
          'larger blocks alone did not fix that seed. See docs/bar_sensitivity_ja.md.')
    print('SUMMARY ' + json.dumps(dict(codes=['toric_d3', 'toric_d5'], ladder=ladder,
                                       estimates=estimates, intervals=intervals, checks=checks),
                                  allow_nan=False))


if __name__ == '__main__':
    main()
