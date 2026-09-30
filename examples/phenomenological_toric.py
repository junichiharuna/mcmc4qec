"""Toric d=3 data/measurement faults decoded by spacetime matching.

Requires matching,codes extras. Measured default/--quick: about 1.0s/0.6s on Windows.
The model supplies round-major syndrome differences from a clean initial
boundary through a perfect final measurement. Every round reaches matching.
P_L describes the complete T-round experiment, not a per-round rate.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from mcmc4qec import (PhenomenologicalModel, PhenomenologicalNoise, Problem,
                       direct_mc, spawn_seeds)
from mcmc4qec.adapter_composition import HistoryDecoder
from mcmc4qec.adapters import matching_from_check_matrix
from mcmc4qec.codes import make_toric_code


def output_dir(value):
    path = Path(value).expanduser().resolve()
    roots = [Path('C:/dev/RIMC'), Path('A:/dev/RIMC')]
    roots += [Path(os.environ[name]) for name in ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT') if os.environ.get(name)]
    for root in roots:
        if path == root.resolve() or root.resolve() in path.parents:
            raise ValueError('output directory cannot be inside the research repository')
    path.mkdir(parents=True, exist_ok=True)
    return path


def spacetime_decoder(model):
    # The j-th column is the complete difference history of a single fault.
    # Data faults touch the check events of their round; measurement faults
    # touch the events before and after the measured round.
    columns = np.eye(model.n, dtype=np.uint8)
    checks = np.column_stack([model.syndrome(column).reshape(-1) for column in columns])
    logical = np.column_stack([model.observables(column) for column in columns])
    assert np.all(checks.sum(axis=0) <= 2)
    matching = matching_from_check_matrix(checks, logical_map=logical,
                                          identifier='toric-d3-spacetime-differences')
    return HistoryDecoder(matching, layout='round_major_flat',
                          identifier='all-round-differences-to-spacetime-matching')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--seed', type=int, default=20260930)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    code = make_toric_code(3)
    rounds = 3 if args.quick else 4
    model = PhenomenologicalModel(code, rounds, initial_boundary='clean',
                                 final_boundary='perfect', representation='difference')
    p = {'data': 0.08, 'measurement': 0.04}
    problem = Problem(model, PhenomenologicalNoise(model), spacetime_decoder(model))
    mc = direct_mc(problem, p, trials=100 if args.quick else 1200,
                   seed=spawn_seeds(args.seed, 1)[0])
    print(f'Toric d=3, T={rounds}, data p={p["data"]}, measurement p={p["measurement"]}')
    print('HistoryDecoder flattens every round-major syndrome difference into spacetime checks.')
    print(f'Whole-experiment P_L={mc.estimate:.6g}; Wilson 95%={mc.interval}; failures={mc.failures}/{mc.trials}')
    summary = dict(code='toric-d3-phenomenological', rounds=rounds, p=p,
                   pl=mc.estimate, pl_interval=mc.interval)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == '__main__':
    main()
