"""Compare fixed-decoder standard BAR and p-dependent-decoder approximate BAR.

Requires mcmc4qec[codes] (including ldpc/BP-OSD). Typical runtime: --quick
under 10 s, default under 120 s. The standard ladder builds BP-OSD once at
the anchor prior and reuses that same decoder at every rung. The explicit
p_dependent_decoder_approx mode rebuilds BP-OSD at each rung; its uncertainty
interval excludes bias from changing failure sets. Neither estimate is claimed
universally preferable. Both use a positive, independent direct-MC anchor.
"""

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

from mcmc4qec import (IndependentBitFlip, Problem, SamplingConfig, direct_mc,
                      estimate_logical_error, spawn_seeds)
from mcmc4qec.codes import make_bb_code_72
from mcmc4qec.decoders import bposd_decoder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--out', default=str(Path(tempfile.gettempdir()) / 'mcmc4qec' / 'p_dependent_decoder'))
    args = parser.parse_args()
    out = Path(args.out).expanduser().resolve()
    roots = [Path('C:/dev/RIMC'), Path('A:/dev/RIMC')]
    roots += [Path(os.environ[name]) for name in ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT')
              if os.environ.get(name)]
    for forbidden in roots:
        root = forbidden.resolve()
        if out == root or root in out.parents:
            raise ValueError('Refusing to write into the read-only RIMC repository')
    out.mkdir(parents=True, exist_ok=True)
    print(f'Output: {out}')
    code = make_bb_code_72()
    ladder = [0.08, 0.06] if args.quick else [0.08, 0.06, 0.04]
    fixed_prior = ladder[0]
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n),
                      bposd_decoder(code, fixed_prior))
    seeds = iter(spawn_seeds(args.seed, 3))
    anchor = direct_mc(problem, ladder[0], trials=120 if args.quick else 900,
                       seed=next(seeds))
    if not 0 < anchor.failures < anchor.trials:
        raise RuntimeError('MC anchor needs observed failures and successes; increase trials')
    print(f'Anchor at p={ladder[0]} with decoder prior={fixed_prior}: '
          f'{anchor.failures}/{anchor.trials} failures')
    config = SamplingConfig(samples=24 if args.quick else 120,
                            burn_in=8 if args.quick else 35)
    fixed = estimate_logical_error(problem, ladder, anchor=anchor, config=config,
                                   seed=next(seeds), bootstrap_replicates=8 if args.quick else 25)
    approx = estimate_logical_error(
        problem, ladder, anchor=anchor, config=config, seed=next(seeds),
        mode='p_dependent_decoder_approx', decoder_factory=lambda p: bposd_decoder(code, p),
        decoder_priors=ladder,
        approximation_reason='Each rung uses its own BP-OSD prior; density-only BAR omits the changed failure set.',
        bootstrap_replicates=8 if args.quick else 25,
    )
    rows = []
    for index, p in enumerate(ladder):
        rows.append(dict(p=p, fixed=fixed.estimates[index], fixed_low=fixed.intervals[index][0]
                         if fixed.intervals[index] else None,
                         fixed_high=fixed.intervals[index][1] if fixed.intervals[index] else None,
                         approx=approx.estimates[index], approx_low=approx.intervals[index][0]
                         if approx.intervals[index] else None,
                         approx_high=approx.intervals[index][1] if approx.intervals[index] else None))
        print(f'p={p:.2f} fixed-prior BAR={fixed.estimates[index]:.5g} {fixed.intervals[index]}; '
              f'p-dependent approximate BAR={approx.estimates[index]:.5g} {approx.intervals[index]}')
    with (out / 'p_dependent_decoder.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('Approximate intervals exclude bias from changing p-dependent decoder failure sets.')
    print('Both interval families assume adequate conditional-chain mixing and block length.')
    print('SUMMARY ' + json.dumps(dict(code='BB72', ladder=ladder,
                                       fixed={'estimates': fixed.estimates, 'intervals': fixed.intervals},
                                       approx={'estimates': approx.estimates, 'intervals': approx.intervals}),
                                  allow_nan=False))


if __name__ == '__main__':
    main()
