"""BB72 bit-flip: direct P_L and conditional weights with a fixed BP-OSD prior.

Requires the codes extra. Measured default/--quick: about 2.0s/0.7s on Windows.
The decoder is built once at prior 0.08, equal to the evaluated p here.
Conditional chain frequencies are not absolute P_L; diagnostics prove no mixing.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig, direct_mc, sample_faulty, spawn_seeds
from mcmc4qec.codes import make_bb_code_72
from mcmc4qec.decoders import bposd_decoder


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
    code = make_bb_code_72()
    p = prior = 0.08
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), bposd_decoder(code, prior))
    mc_seed, chain_seed = spawn_seeds(args.seed, 2)
    mc = direct_mc(problem, p, trials=100 if args.quick else 2000, seed=mc_seed)
    chain = sample_faulty(problem, p, config=SamplingConfig(samples=100 if args.quick else 800,
                          burn_in=20 if args.quick else 100), seed=chain_seed)
    ew_chain = float(np.count_nonzero(chain.states, axis=-1).mean())
    print(f'BB72: evaluated p={p}; BP-OSD fixed prior={prior}; equal={p == prior}')
    print(f'Direct MC P_L={mc.estimate:.6g}, Wilson 95%={mc.interval}, failures={mc.failures}/{mc.trials}')
    print(f'E[weight | faulty]: direct MC={mc.conditional_weight}, Z+H={ew_chain:.6g}')
    print('Conditional samples estimate conditional observables, not absolute P_L. Diagnostics do not prove mixing.')
    summary = dict(code='BB72', p=p, pl=mc.estimate, pl_interval=mc.interval,
                   ew_direct=mc.conditional_weight, ew_chain=ew_chain)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == '__main__':
    main()
