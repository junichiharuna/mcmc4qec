"""Compare E[weight | faulty] from Z+H chains and independent direct MC.

Requires mcmc4qec[matching,codes]; matplotlib via mcmc4qec[plot] is optional.
Typical runtime: --quick under 10 s, default under 120 s.
The unweighted MWPM decoder is fixed. Direct MC supplies conditional means
only when failures are observed. MCMC samples the normalized noise restricted
to failures, so occupancy or state frequencies from that chain cannot yield
the absolute logical failure probability P_L. Diagnostics are not a proof.
"""

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (IndependentBitFlip, Problem, SamplingConfig, direct_mc,
                      sample_faulty, spawn_seeds)
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import mwpm_decoder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--out', default=str(Path(tempfile.gettempdir()) / 'mcmc4qec' / 'conditional_weight'))
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
    code = make_toric_code(5)
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
    ps = [0.14, 0.20, 0.26]
    seeds = iter(spawn_seeds(args.seed, 2 * len(ps)))
    config = SamplingConfig(chains=4, samples=40 if args.quick else 600,
                            burn_in=12 if args.quick else 180)
    if args.quick:
        print('Quick mode checks execution only; these short chains do not establish precision.')
    rows = []
    for p in ps:
        direct = direct_mc(problem, p, trials=250 if args.quick else 2000,
                           seed=next(seeds))
        if direct.failures == 0:
            raise RuntimeError('No direct-MC failures; increase trials before comparing conditional means')
        chain = sample_faulty(problem, p, config=config, seed=next(seeds))
        ew_chain = float(np.count_nonzero(chain.states, axis=-1).mean())
        rows.append(dict(p=p, ew_direct=direct.conditional_weight,
                         ew_chain=ew_chain, direct_failures=direct.failures,
                         direct_trials=direct.trials))
        print(f'p={p:.2f} direct E[w|faulty]={direct.conditional_weight:.3f} '
              f'({direct.failures} failures); Z+H E[w|faulty]={ew_chain:.3f}')
    with (out / 'conditional_weight.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('matplotlib unavailable; PNG omitted; numeric data saved in CSV')
    else:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(ps, [row['ew_direct'] for row in rows], 'o-', label='direct MC')
        ax.plot(ps, [row['ew_chain'] for row in rows], 's-', label='Z+H conditional chain')
        ax.set(xlabel='physical bit-flip p', ylabel='E[weight | faulty]')
        ax.legend()
        fig.tight_layout()
        fig.savefig(out / 'conditional_weight.png', dpi=110)
        plt.close(fig)
    # Rejected and repeated MCMC states still belong to a chain whose target
    # distribution is conditioned on failure. Its frequency normalization is
    # one inside that restricted set, with no information about total failure
    # mass. Only independent direct MC here estimates absolute P_L.
    print('Conditional chain state frequencies are not P_L; only direct MC here estimates absolute P_L.')
    print('Good trace diagnostics would not prove convergence or correctness.')
    print('SUMMARY ' + json.dumps(dict(code='toric_d5', ps=ps,
                                       ew_direct=[row['ew_direct'] for row in rows],
                                       ew_chain=[row['ew_chain'] for row in rows]),
                                  allow_nan=False))


if __name__ == '__main__':
    main()
