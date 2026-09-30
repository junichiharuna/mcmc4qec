"""Screen conditional-chain weight traces from three logical initializations.

Requires mcmc4qec[matching,codes]. Typical runtime: --quick under 10 s, default
under 120 s. A fixed unweighted MWPM decoder defines failure. Independent
direct MC estimates the variance of weight conditioned on failure, not the
variance of its estimated mean; the four checks use that variance. Passing
ESS, split R-hat, or all four checks proves neither convergence nor correctness.
"""

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (IndependentBitFlip, Problem, SamplingConfig,
                      evaluate_convergence, maximum_weight_initial_state,
                      minimum_weight_initial_state,
                      random_logical_sector_initial_state, sample_faulty,
                      spawn_seeds)
from mcmc4qec.codes import make_asymmetric_toric_code
from mcmc4qec.decoders import mwpm_decoder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--out', default=str(Path(tempfile.gettempdir()) / 'mcmc4qec' / 'convergence_check'))
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
    code = make_asymmetric_toric_code(3, 5)
    p = 0.2
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
    seeds = iter(spawn_seeds(args.seed, 5))
    direct_seed = next(seeds)
    initial = {
        'minimum': minimum_weight_initial_state(code),
        'random_sector': random_logical_sector_initial_state(code, seed=next(seeds)),
        'maximum': maximum_weight_initial_state(code),
    }
    for label, state in initial.items():
        if not np.isfinite(problem.log_prob(state, p)) or not problem.is_faulty(state):
            raise RuntimeError(f'{label} start is outside noise support or not faulty')
        print(f'{label} initial weight={int(state.sum())}; observable sector='
              f'{(code.lz @ state % 2).tolist()}')
    # These are independent unconditional noise draws. Retain failed weights
    # and estimate their conditional sample variance, not the MC mean's variance.
    rng = np.random.default_rng(direct_seed)
    failed_weights = []
    trials = 600 if args.quick else 3000
    for _ in range(trials):
        state = problem.noise.sample(p, rng)
        if problem.is_faulty(state):
            failed_weights.append(int(np.count_nonzero(state)))
    if len(failed_weights) < 2:
        raise RuntimeError('Too few independent direct-MC failures for conditional variance')
    direct_variance = float(np.var(failed_weights, ddof=1))
    if direct_variance <= 0:
        raise RuntimeError('Degenerate direct-MC conditional variance; increase trials')
    print(f'Independent direct MC conditional weight variance={direct_variance:.4g} '
          f'from {len(failed_weights)}/{trials} failures')
    config = SamplingConfig(chains=2, samples=48 if args.quick else 160,
                            burn_in=16 if args.quick else 60)
    runs = {}
    for label, state in initial.items():
        runs[label] = sample_faulty(problem, p, config=config, seed=next(seeds),
                                    initial_state=np.stack([state, state]))
    reports = {label: evaluate_convergence(runs['minimum'],
                                           other_initialization=runs[label],
                                           direct_variance=direct_variance)
               for label in ('random_sector', 'maximum')}
    check_names = ('scaling', 'stationarity', 'multistart', 'dispersion')
    explanations = {
        'scaling': 'Tests persistent between-chain spread; shared relaxation can pass.',
        'stationarity': 'Tests late drift; a common wrong stationary region can pass.',
        'multistart': 'Tests different basins reached from different starts; a shared basin can pass.',
        'dispersion': 'Tests whether independent conditional variance and IAT explain chain spread; common bias can pass.',
    }
    for label, current in reports.items():
        print(f'Comparison: minimum versus {label}')
        for name in check_names:
            print(f'{name}: {current["checks"][name]["ok"]}. {explanations[name]}')
        print(f'Four-check verdict: {current["converged"]}')
        for warning in current['warnings']:
            print(f'Warning: {warning}')
    with (out / 'convergence_check.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['other_initialization', 'check', 'ok', 'description'])
        for label, current in reports.items():
            for name in check_names:
                writer.writerow([label, name, current['checks'][name]['ok'], explanations[name]])
    print('SUMMARY ' + json.dumps(dict(code='asymmetric_toric_3x5', p=p,
                                       checks={label: {name: current['checks'][name]['ok']
                                                       for name in check_names}
                                               for label, current in reports.items()},
                                       verdict={label: current['converged'] for label, current in reports.items()},
                                       warnings={label: current['warnings'] for label, current in reports.items()}),
                                  allow_nan=False))


if __name__ == '__main__':
    main()
