"""Compare physical single-fault and Z+OBF conditional circuit sampling.

Requires stim,matching extras. Measured default/--quick: about 13.6s/3.6s
on Windows Python 3.11. The decoder prior is
fixed at p. Conditional chains do not estimate whole-circuit P_L, and IAT
does not prove convergence, ergodicity, or correctness.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import KernelConfig, SamplingConfig, spawn_seeds
from mcmc4qec.circuit import surface_logical_idle_problem
from mcmc4qec.sampling import direct_mc, sample_faulty


def output_dir(value):
    path = Path(value).expanduser().resolve()
    roots = [Path('C:/dev/RIMC'), Path('A:/dev/RIMC')]
    roots += [Path(os.environ[name]) for name in ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT')
              if os.environ.get(name)]
    for root in roots:
        if path == root.resolve() or root.resolve() in path.parents:
            raise ValueError('output directory cannot be inside the research repository')
    path.mkdir(parents=True, exist_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=20261001)
    parser.add_argument('--out', type=Path,
                        default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    p = .02
    problem = surface_logical_idle_problem(distance=3, decoder_p=p, basis='Z')
    seeds = spawn_seeds(args.seed, 3)
    settings = {
        'circuit_single': KernelConfig(circuit_single=1, single=0, zanella=0,
                                       cluster=0, stabilizer=0),
        'Z+OBF': KernelConfig(circuit_single=0, single=.3, zanella=.7,
                              cluster=0, stabilizer=0),
    }
    samples = 30 if args.quick else 250
    burn_in = 10 if args.quick else 80
    results = {}
    for (name, kernels), seed in zip(settings.items(), seeds[:2]):
        run = sample_faulty(problem, p, seed=seed,
            config=SamplingConfig(samples=samples, burn_in=burn_in, kernels=kernels))
        proposed = sum(item['proposed'] for key, item in run.acceptance.items() if key != 'lazy')
        accepted = sum(item['accepted'] for key, item in run.acceptance.items() if key != 'lazy')
        results[name] = dict(conditional_weight=float(np.count_nonzero(run.states, axis=-1).mean()),
                             acceptance=accepted / proposed if proposed else None,
                             iat=run.diagnostics['iat'])
    mc = direct_mc(problem, p, trials=80 if args.quick else 450, seed=seeds[2])
    summary = dict(distance=3, p=p, kernels=list(settings),
                   conditional_weight={key: value['conditional_weight'] for key, value in results.items()},
                   acceptance={key: value['acceptance'] for key, value in results.items()},
                   iat={key: value['iat'] for key, value in results.items()},
                   direct_mc_conditional_weight=mc.conditional_weight)
    with (out / 'conditional_weight.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['kernel', 'conditional_weight', 'acceptance', 'iat'])
        for name, result in results.items():
            writer.writerow([name, result['conditional_weight'], result['acceptance'], result['iat']])
        writer.writerow(['direct_mc', mc.conditional_weight, '', ''])
    print(f'Conditional weight and diagnostics: {out / "conditional_weight.csv"}')
    print('Conditional state frequencies are not whole-circuit P_L; diagnostics do not prove convergence.')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == '__main__':
    main()
