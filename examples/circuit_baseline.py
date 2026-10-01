"""Physical fault baseline with a midpoint rotated-surface logical idle.

Requires stim,matching extras. Measured default/--quick: about 3.9s/1.4s
on Windows with the dev3 circuit construction path.
The decoder prior is fixed at p=0.01, the evaluated physical fault rate.
This example selects the physical single-fault kernel for conditional MCMC.
OBF and Z are also supported; H/stabilizer remain unavailable.
Direct MC estimates whole-circuit P_L; conditional samples do not.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

from mcmc4qec.circuit import surface_logical_idle_problem
from mcmc4qec import KernelConfig, SamplingConfig, spawn_seeds
from mcmc4qec.sampling import direct_mc


def output_dir(value):
    path = Path(value).expanduser().resolve()
    roots = [Path('C:/dev/RIMC'), Path('A:/dev/RIMC')]
    roots += [Path(os.environ[name]) for name in ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT') if os.environ.get(name)]
    for root in roots:
        if path == root.resolve() or root.resolve() in path.parents:
            raise ValueError('output directory cannot be inside the research repository')
    path.mkdir(parents=True, exist_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    p = .01
    circuit_config = SamplingConfig(kernels=KernelConfig(circuit_single=1, single=0,
                              zanella=0, cluster=0, stabilizer=0))
    problem = surface_logical_idle_problem(distance=3, decoder_p=p, basis="Z")
    result = direct_mc(problem, p, trials=80 if args.quick else 500,
                       seed=spawn_seeds(args.seed, 1)[0])
    print(f"locations={problem.model.n}; detectors={problem.model.H.shape[0]}")
    print(f"midpoint logical-Z failure={result.estimate:.5f}; "
          f"Wilson 95% interval={result.interval}; trials={result.trials}")
    print(f'Conditional circuit kernel configuration: {circuit_config.kernels}')
    summary = dict(locations=problem.model.n, detectors=int(problem.model.H.shape[0]),
                   pl=result.estimate, pl_interval=result.interval)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == "__main__":
    main()
