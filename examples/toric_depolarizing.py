"""Toric depolarising example with joint Pauli noise and sector MWPM decoding.

Requires matching,codes extras. Measured default/--quick: about 1.5s/0.7s on Windows.
The decoder does not depend on p. Conditional chains do not estimate P_L,
and their diagnostics do not prove mixing or correctness.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (DepolarizingModel, DepolarizingNoise, Problem,
                       SamplingConfig, direct_mc, sample_faulty, spawn_seeds)
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import depolarizing_mwpm_decoder


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
    parser.add_argument('--seed', type=int, default=20260930)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    d = 3 if args.quick else 5
    code = make_toric_code(d)
    p = 0.16
    # Sector composition is a decoder choice; the noise still samples joint I/X/Y/Z labels.
    problem = Problem(DepolarizingModel(code), DepolarizingNoise(code.n), depolarizing_mwpm_decoder(code))
    mc_seed, chain_seed = spawn_seeds(args.seed, 2)
    mc = direct_mc(problem, p, trials=100 if args.quick else 1800, seed=mc_seed)
    chain = sample_faulty(problem, p, config=SamplingConfig(samples=100 if args.quick else 600,
                          burn_in=20 if args.quick else 100), seed=chain_seed)
    ew_chain = float(np.count_nonzero(chain.states, axis=-1).mean())
    counts = {name: float((chain.states == label).sum(axis=-1).mean())
              for label, name in ((1, 'X'), (2, 'Y'), (3, 'Z'))}
    print(f'Toric d={d}, depolarising p={p}, joint I/X/Y/Z noise; independent X/Z sector MWPM decoder')
    print(f'Direct MC P_L={mc.estimate:.6g}, Wilson 95%={mc.interval}, failures={mc.failures}/{mc.trials}')
    print(f'E[non-I weight | faulty]: direct MC={mc.conditional_weight}, Z+H={ew_chain:.6g}')
    print(f'Z+H conditional mean X/Y/Z counts: {counts}')
    print('Conditional chain frequencies are not absolute P_L; diagnostics do not prove mixing.')
    summary = dict(code=f'toric-d{d}-depolarizing', p=p, pl=mc.estimate,
                   pl_interval=mc.interval, ew_direct=mc.conditional_weight, ew_chain=ew_chain)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == '__main__':
    main()
