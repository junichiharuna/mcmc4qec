"""Measure surface d=3 physical-location conditional MCMC step rates.

Requires stim and matching. Each configuration runs a fixed short chain;
the rates and acceptance are timing observations, not mixing guarantees.
"""
import argparse
import time

from mcmc4qec import KernelConfig, SamplingConfig, spawn_seeds
from mcmc4qec.circuit import surface_logical_idle_problem
from mcmc4qec.sampling import sample_faulty


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=150)
    parser.add_argument('--seed', type=int, default=20261001)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error('--steps must be positive')
    p = .02
    problem = surface_logical_idle_problem(distance=3, decoder_p=p)
    settings = {
        'circuit_single': KernelConfig(single=0, zanella=0, cluster=0,
                                       stabilizer=0, circuit_single=1, lazy=0),
        'zanella': KernelConfig(single=0, zanella=1, cluster=0,
                                stabilizer=0, circuit_single=0, lazy=0),
        'Z+OBF': KernelConfig(single=.3, zanella=.7, cluster=0,
                              stabilizer=0, circuit_single=0, lazy=0),
    }
    for (name, kernels), seed in zip(settings.items(), spawn_seeds(args.seed, 3)):
        start = time.perf_counter()
        result = sample_faulty(problem, p, seed=seed,
            config=SamplingConfig(samples=args.steps, burn_in=0, kernels=kernels))
        elapsed = time.perf_counter() - start
        proposed = sum(entry['proposed'] for key, entry in result.acceptance.items() if key != 'lazy')
        accepted = sum(entry['accepted'] for key, entry in result.acceptance.items() if key != 'lazy')
        print(f'{name}: steps={args.steps} seconds={elapsed:.3f} '
              f'step/s={args.steps / elapsed:.2f} acceptance={accepted / proposed:.4f}')


if __name__ == '__main__':
    main()
