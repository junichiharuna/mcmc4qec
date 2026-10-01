"""Compare X and Z code-capacity failures on a rectangular toric CSS code.

Requires codes,matching extras. Expected default/--quick runtime: under 2 min/
10 s. Relevant scientific cautions: X uses hz/lz and Z uses hx/lx; a
rectangular geometry alone does not establish unequal aggregate failure rates.
Direct MC estimates P_L; its finite intervals do not prove equality or a gap.
The 30-bit state space exceeds the public exact enumeration limit.
"""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import tempfile

from mcmc4qec import IndependentBitFlip, Problem, direct_mc, spawn_seeds
from mcmc4qec.codes import make_asymmetric_toric_code
from mcmc4qec.decoders import mwpm_decoder


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
    parser.add_argument('--seed', type=int, default=20261001)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)

    code = make_asymmetric_toric_code(3, 5)
    p = .13
    seeds = spawn_seeds(args.seed, 2)
    x = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
    z = Problem(code.phase_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code, errors='Z'))
    trials = 250 if args.quick else 3000
    x_mc = direct_mc(x, p, trials=trials, seed=seeds[0])
    z_mc = direct_mc(z, p, trials=trials, seed=seeds[1])
    rows = [('bit_flip', x_mc), ('phase_flip', z_mc)]
    csv_path = out / 'phase_flip_comparison.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['sector', 'p', 'trials', 'pl', 'lower', 'upper'])
        for label, result in rows:
            writer.writerow([label, p, trials, result.estimate, *result.interval])
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('Plot unavailable; numeric CSV retained.')
    else:
        fig, axis = plt.subplots(figsize=(5, 3))
        values = [result.estimate for _, result in rows]
        intervals = [[v - result.interval[0] for v, (_, result) in zip(values, rows)],
                     [result.interval[1] - v for v, (_, result) in zip(values, rows)]]
        axis.bar(['X errors', 'Z errors'], values, color=['tab:blue', 'tab:orange'])
        axis.errorbar(range(2), values, yerr=intervals, fmt='none', color='black', capsize=4)
        axis.set_ylabel('Logical failure probability')
        axis.set_ylim(0, min(1, max(result.interval[1] for _, result in rows) * 1.15))
        fig.tight_layout()
        fig.savefig(out / 'phase_flip_comparison.png', dpi=140)
        plt.close(fig)

    exact_available = math.prod(x.alphabets) <= 1_048_576
    summary = dict(code='asymmetric-toric-3x5', p=p,
                   pl_bit_flip=x_mc.estimate, pl_phase_flip=z_mc.estimate,
                   interval_bit_flip=x_mc.interval, interval_phase_flip=z_mc.interval,
                   exact_available=exact_available)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'X errors: P_L={x_mc.estimate:.6g}, 95% Wilson={x_mc.interval}')
    print(f'Z errors: P_L={z_mc.estimate:.6g}, 95% Wilson={z_mc.interval}')
    print('These independent finite-sample intervals do not establish an X/Z gap.')
    print(f'Output: {csv_path}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == '__main__':
    main()
