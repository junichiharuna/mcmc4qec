"""Three hand-written DEM mechanisms, not a physical-circuit reproduction.

Requires the stim extra. Measured default/--quick: about 0.5s/0.2s on Windows.
The ^ fragments share one latent fault. Exact and direct MC give absolute P_L;
this DEM example makes no physical-circuit equivalence claim.
"""
import argparse
from itertools import product
import json
import os
from pathlib import Path
import tempfile

import numpy as np
import stim

from mcmc4qec import CallableDecoder, Problem, from_stim_dem, exact, direct_mc, spawn_seeds


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
    parser.add_argument('--seed', type=int, default=41)
    parser.add_argument('--out', type=Path, default=Path(tempfile.gettempdir()) / 'mcmc4qec' / Path(__file__).stem)
    args = parser.parse_args()
    out = output_dir(args.out)
    replay_seed, mc_seed = spawn_seeds(args.seed, 2)
    dem = stim.DetectorErrorModel("""
        error(0.10) D0 L0 ^ D1
        error(0.05) D0
        error(0.02) D1
    """)
    model, noise = from_stim_dem(dem, identifier="three-mechanism-demo")
    assert model.n == 3
    latent = np.array(list(product((0, 1), repeat=model.n)), dtype=bool)
    detectors, observables, replayed = dem.compile_sampler(seed=replay_seed % (2**63)).sample(
        shots=len(latent), return_errors=True, recorded_errors_to_replay=latent,
    )
    assert np.array_equal(replayed, latent)
    assert np.array_equal(detectors, latent @ model.H.T % 2)
    assert np.array_equal(observables, latent @ model.L.T % 2)
    decoder = CallableDecoder(
        lambda syndrome: [int(np.all(syndrome))],
        identifier="predict-correlated-mechanism-on-two-clicks-v1",
    )
    problem = Problem(model, noise, decoder)
    reference = exact(problem, None)
    mc = direct_mc(problem, None, trials=200 if args.quick else 2_000, seed=mc_seed)
    print("Three latent mechanisms retained; ^ does not introduce an independent fault.")
    print("Stim replay agrees with H/L for all eight latent configurations.")
    print(f"Fixed DEM (p=None): exact P_L={reference.estimate:.6f}, direct MC={mc.estimate:.6f}")
    print(f"Direct MC Wilson95 interval: {mc.interval}")
    print("This example samples independent DEM mechanisms; physical fault equivalence is not inferred.")
    summary = dict(mechanisms=model.n, exact=reference.estimate, pl=mc.estimate,
                   pl_interval=mc.interval)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Output: {out / "summary.json"}')
    print('SUMMARY ' + json.dumps(summary))


if __name__ == "__main__":
    main()
