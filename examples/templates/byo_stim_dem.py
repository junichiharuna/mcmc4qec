"""Bring a Stim circuit through its detector error model (stim, matching extras).

Default: about 1 second; --quick: under 1 second. Direct MC estimates P_L
for the whole fixed DEM experiment; the conditional chain does not. Each DEM
error instruction is one latent mechanism, including correlated ^ pieces.
This does not certify equivalence to arbitrary physical circuit fault sampling
or a per-round rate. Diagnostics do not prove mixing. The paper is in preparation.
"""

import argparse
from itertools import product
import json
import math
import os
from pathlib import Path, PureWindowsPath
import tempfile

import numpy as np
import stim

from mcmc4qec import (KernelConfig, Problem, SamplingConfig, direct_mc,
                       from_stim_dem, matching_from_dem, sample_faulty, spawn_seeds)


# >>> EDIT HERE
circuit = stim.Circuit("""
    R 0 1
    X_ERROR(0.1) 0
    X_ERROR(0.1) 1
    M 0 1
    DETECTOR rec[-2]
    OBSERVABLE_INCLUDE(0) rec[-2] rec[-1]
""")
decompose_errors = False
approximate_disjoint_errors = False
enable_correlations = False
# <<< END EDIT


def output_directory(raw):
    path = Path(raw).expanduser().resolve()
    windows = PureWindowsPath(str(raw))
    roots = [os.environ[key] for key in ("RIMC_RESEARCH_ROOT", "RESEARCH_ROOT")
              if os.environ.get(key)]
    for raw_root in roots:
        root = PureWindowsPath(raw_root)
        if windows == root or root in windows.parents:
            raise ValueError("--out resolves inside the read-only research repository")
        native = Path(raw_root).expanduser().resolve()
        if path == native or native in path.parents:
            raise ValueError("--out resolves inside the read-only research repository")
    return path


def check_components(model, problem, rng):
    """Validate latent DEM map, probability mass, decoder output, and failure."""
    if model.H.shape[1] != model.n or model.L.shape[1] != model.n:
        raise ValueError("DEM detector/logical maps must cover every mechanism")
    if model.L.shape[0] == 0:
        raise ValueError("the conditional chain requires a DEM logical observable")
    if model.n <= 12:
        total = sum(math.exp(problem.log_prob(bits, None)) for bits in product((0, 1), repeat=model.n))
        if not math.isclose(total, 1.0, abs_tol=1e-10):
            raise ValueError(f"DEM noise is not normalized: sum={total:.12g}")
    else:
        print("DEM normalization unchecked for more than 12 mechanisms; validate on a small instance.")
    m = model.H.shape[0]
    syndromes = product((0, 1), repeat=m) if m <= 8 else (
        rng.integers(0, 2, size=m) for _ in range(32))
    for syndrome in syndromes:
        first = np.asarray(problem.decoder.predict(syndrome))
        again = np.asarray(problem.decoder.predict(syndrome))
        if first.shape != (model.L.shape[0],) or not np.all((first == 0) | (first == 1)):
            raise ValueError(f"matching must predict {model.L.shape[0]} logical-observable bits")
        if not np.array_equal(first, again):
            raise ValueError("DEM decoder prediction is not deterministic")
    states = product((0, 1), repeat=model.n) if model.n <= 12 else (
        rng.integers(0, 2, size=model.n) for _ in range(32))
    for bits in states:
        if problem.is_faulty(bits) != problem.is_faulty(bits):
            raise ValueError("failure predicate is not deterministic")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "mcmc4qec" / Path(__file__).stem)
    args = parser.parse_args()
    out = output_directory(args.out)
    dem = circuit.detector_error_model(decompose_errors=decompose_errors,
                                       approximate_disjoint_errors=approximate_disjoint_errors)
    model, noise = from_stim_dem(dem, identifier="byo-circuit-dem-v1")
    decoder = matching_from_dem(dem, enable_correlations=enable_correlations,
                                identifier="byo-dem-matching-v1")
    problem = Problem(model, noise, decoder)
    seeds = spawn_seeds(args.seed, 3)
    check_components(model, problem, np.random.default_rng(seeds[2]))
    mc = direct_mc(problem, None, trials=100 if args.quick else 1000, seed=seeds[0])
    config = SamplingConfig(samples=30 if args.quick else 200, burn_in=10 if args.quick else 40,
                            kernels=KernelConfig(cluster_k=1))
    chain = sample_faulty(problem, None, config=config, seed=seeds[1])
    out.mkdir(parents=True, exist_ok=True)
    payload = {"detectors": dem.num_detectors, "mechanisms": model.n, "pl": mc.estimate}
    (out / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out / 'result.json'}")
    print(f"Whole-DEM direct MC P_L={mc.estimate:.6g}, Wilson interval={mc.interval}")
    print(f"Conditional latent-mechanism mean weight={np.count_nonzero(chain.states, axis=-1).mean():.6g}; it does not estimate P_L.")
    print("Matching predicts logical observables from the full detector syndrome; physical circuit equivalence is not inferred.")
    print("Diagnostics do not prove convergence, ergodicity, or correctness; complete four-check screening needs independent direct-MC conditional variance.")
    print("SUMMARY " + json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"CHECK FAILED: {type(exc).__name__}: {str(exc).splitlines()[0]}") from None
