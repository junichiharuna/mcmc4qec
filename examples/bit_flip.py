"""Small bit-flip example; run against an installed mcmc4qec package.

Requires core only. Measured default/--quick: about 2.5s/0.3s on Windows.
Exact and direct MC estimate P_L; the conditional chain only estimates
E[weight | faulty]. Diagnostics do not prove mixing or correctness.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (
    CSSCode,
    CallableDecoder,
    IndependentBitFlip,
    KernelConfig,
    Problem,
    Result,
    SamplingConfig,
    diagnose,
    direct_mc,
    exact,
    sample_faulty,
    spawn_seeds,
)


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
    parser.add_argument('--seed', type=int, default=18)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    code = CSSCode(
        hx=np.zeros((0, 3), dtype=int),
        hz=[[1, 1, 0], [0, 1, 1]],
        lx=[[1, 1, 1]],
        lz=[[1, 0, 0]],
    )
    # The minimum-weight correction acts on qubit 0 only for syndrome 10.
    # lz = [1, 0, 0] maps that correction to its logical observable.
    decoder = CallableDecoder(
        lambda syndrome: [int(tuple(syndrome) == (1, 0))],
        identifier="repetition3-minimum-weight-v1",
    )
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
    p = 0.25
    reference = exact(problem, p)
    mc_seed, chain_seed = spawn_seeds(args.seed, 2)
    mc = direct_mc(problem, p, trials=200 if args.quick else 10_000, seed=mc_seed)
    samples = sample_faulty(
        problem,
        p,
        config=SamplingConfig(
            samples=100 if args.quick else 2_000,
            burn_in=20 if args.quick else 100,
            chains=2,
            # Two occupied/empty pairs cannot be exchanged in this tiny code.
            kernels=KernelConfig(cluster_k=1),
        ),
        seed=chain_seed,
    )
    restored = Result.from_json(samples.to_json())
    assert np.array_equal(restored.states, samples.states)
    assert np.isclose(reference.estimate, 3 * p**2 - 2 * p**3)
    print(f"Exact P_L: {reference.estimate:.6f}")
    print(f"Direct MC P_L: {mc.estimate:.6f}; 95% Wilson interval: {mc.interval}")
    print(f"Exact E[weight | faulty]: {reference.conditional_weight:.6f}")
    print(f"MCMC E[weight | faulty]: {samples.states.sum(axis=-1).mean():.6f}")
    print("Diagnostics (do not establish convergence):", diagnose(samples))
    print("Result JSON round trip: preserved retained states")
    summary = dict(exact=reference.estimate, pl=mc.estimate, pl_interval=mc.interval,
                   ew_exact=reference.conditional_weight,
                   ew_chain=float(samples.states.sum(axis=-1).mean()))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == "__main__":
    main()
