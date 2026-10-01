"""Toric d=5 PyMatching direct MC and conditional MCMC example.

Requires matching,codes extras. Measured default/--quick: about 1.0s/0.7s on Windows.
Direct MC estimates P_L; Z+H estimates only E[weight | faulty]. Its
diagnostics do not prove mixing, ergodicity or correctness.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig, direct_mc, sample_faulty, spawn_seeds
from mcmc4qec.adapters import matching_from_check_matrix
from mcmc4qec.codes import make_toric_code


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
    parser.add_argument('--seed', type=int, default=11)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    code = make_toric_code(5)
    decoder = matching_from_check_matrix(
        code.hz, logical_map=code.lz, identifier="toric-d5-mwpm"
    )
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
    p = 0.1
    mc_seed, chain_seed = spawn_seeds(args.seed, 2)
    mc = direct_mc(problem, p, trials=100 if args.quick else 2_000, seed=mc_seed)
    chain = sample_faulty(problem, p, config=SamplingConfig(samples=50 if args.quick else 100,
                          burn_in=10 if args.quick else 20), seed=chain_seed)
    print(f"Toric d=5, p={p}: direct MC P_L={mc.estimate:.4f}, interval={mc.interval}")
    print(f"Direct MC E[weight | faulty]={mc.conditional_weight:.3f}")
    print(f"Conditional MCMC E[weight | faulty]={np.count_nonzero(chain.states, axis=-1).mean():.3f}")
    print("Kernels:", chain.metadata["config"]["expanded_move_probabilities"])
    summary = dict(code='toric-d5-bit-flip', p=p, pl=mc.estimate, pl_interval=mc.interval,
                   ew_direct=mc.conditional_weight,
                   ew_chain=float(np.count_nonzero(chain.states, axis=-1).mean()))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == "__main__":
    main()
