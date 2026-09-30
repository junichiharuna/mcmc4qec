"""Bring your own CSS matrices and logical-observable decoder (core only).

Default: about 1 second; --quick: under 1 second. Exact/direct MC/BAR estimate
absolute P_L; the failure-conditioned chain does not. The decoder and failure
definition stay fixed across the exact-anchored BAR ladder. Diagnostics do not
prove convergence, ergodicity, or correctness. This is not a reproduction of
research results; the associated paper is in preparation. A ladder with poor
adjacent support overlap can raise OverlapError; choose closer rungs.
"""

import argparse
from itertools import product
import json
import math
import os
from pathlib import Path, PureWindowsPath
import tempfile

import numpy as np

from mcmc4qec import (CSSCode, CallableDecoder, CallableFailure,
                       IndependentBitFlip, KernelConfig, Problem, SamplingConfig,
                       direct_mc, estimate_logical_error, exact, sample_faulty,
                       spawn_seeds)


# >>> EDIT HERE
hx = np.zeros((0, 3), dtype=np.uint8)
hz = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
lx = np.array([[1, 1, 1]], dtype=np.uint8)
lz = np.array([[1, 0, 0]], dtype=np.uint8)
logical_basis = "paired"  # Use "independent" only for an invertible cross-pairing.


def predict_observables(syndrome):
    """Return k logical-observable bits, not a physical correction."""
    return [int(tuple(syndrome) == (1, 0))]


def failure_predicate(state, predicted, truth):
    """Use this one deterministic failure definition in every estimator."""
    return bool(np.any(predicted != truth))


ladder = (0.35, 0.25)
# <<< END EDIT


def output_directory(raw):
    path = Path(raw).expanduser().resolve()
    windows = PureWindowsPath(str(raw))
    roots = ["C:/dev/RIMC", "A:/dev/RIMC"]
    roots += [os.environ[key] for key in ("RIMC_RESEARCH_ROOT", "RESEARCH_ROOT")
              if os.environ.get(key)]
    for raw_root in roots:
        root = PureWindowsPath(raw_root)
        if windows == root or root in windows.parents:
            raise ValueError("--out resolves inside the read-only research repository")
        native = Path(raw_root).expanduser().resolve()
        if path == native or native in path.parents:
            raise ValueError("--out resolves inside the read-only research repository")
    return path


def check_components(code, problem, p, rng):
    """Check algebra, density, declared decoder meaning, and deterministic failure."""
    if len(code.lz) == 0:
        raise ValueError("the conditional chain and BAR require a nonzero logical sector")
    if np.any(code.hx @ code.hz.T % 2):
        raise ValueError("hx @ hz.T must vanish modulo 2")
    if np.any(code.hz @ code.lx.T % 2) or np.any(code.hx @ code.lz.T % 2):
        raise ValueError("logical operators must commute with stabilizers")
    cross = code.lx @ code.lz.T % 2
    if cross.shape != (len(code.lx), len(code.lx)) or not np.any(cross):
        raise ValueError("logical X/Z rows are not independent")
    # CSSCode also checks GF(2) rank, completeness, and paired/independent basis.
    if code.n <= 12:
        total = sum(math.exp(problem.log_prob(bits, p)) for bits in product((0, 1), repeat=code.n))
        if not math.isclose(total, 1.0, abs_tol=1e-10):
            raise ValueError(f"noise is not normalized: sum={total:.12g}")
        normalization = "enumerated"
    else:
        normalization = "unchecked (n > 12)"
        print("Noise normalization unchecked for n > 12; validate on a small instance.")
    m = code.hz.shape[0]
    syndromes = product((0, 1), repeat=m) if m <= 8 else (
        rng.integers(0, 2, size=m) for _ in range(32))
    for syndrome in syndromes:
        first = np.asarray(problem.decoder.predict(syndrome))
        second = np.asarray(problem.decoder.predict(syndrome))
        if first.shape != (len(code.lz),) or not np.all((first == 0) | (first == 1)):
            raise ValueError(f"decoder must predict {len(code.lz)} logical-observable bits")
        if not np.array_equal(first, second):
            raise ValueError("decoder prediction is not deterministic")
    states = product((0, 1), repeat=code.n) if code.n <= 12 else (
        rng.integers(0, 2, size=code.n) for _ in range(32))
    for bits in states:
        state = np.asarray(bits, dtype=np.uint8)
        syndrome = problem.model.syndrome(state)
        predicted = problem.decoder.predict(syndrome)
        truth = problem.model.observables(state)
        a = problem.failure(state.copy(), predicted.copy(), truth.copy())
        b = problem.failure(state.copy(), predicted.copy(), truth.copy())
        if not isinstance(a, (bool, np.bool_)) or a != b:
            raise ValueError("failure predicate must return a deterministic Boolean")
    return normalization


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "mcmc4qec" / Path(__file__).stem)
    args = parser.parse_args()
    out = output_directory(args.out)
    matrices = json.loads(os.environ.get("MCMC4QEC_TEMPLATE_MATRICES", "{}"))
    parts = {name: np.asarray(matrices.get(name, globals()[name]), dtype=np.uint8)
             for name in ("hx", "hz", "lx", "lz")}
    code = CSSCode(**parts, logical_basis=logical_basis)
    decoder = CallableDecoder(predict_observables, identifier="byo-css-observable-v1")
    # A custom predicate may change under stabilizer flips. Check invariance
    # yourself before enabling that kernel; this template never enables it.
    failure = CallableFailure(failure_predicate, identifier="byo-css-failure-v1")
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder, failure)
    seeds = spawn_seeds(args.seed, 5)
    check_rng = np.random.default_rng(seeds[4])
    for p in ladder:
        check_components(code, problem, p, check_rng)
    config = SamplingConfig(samples=50 if args.quick else 250, burn_in=10 if args.quick else 40,
                            kernels=KernelConfig(cluster_k=1))
    if code.n <= 12:
        anchor = exact(problem, ladder[0])
        anchor_note = "exact"
    else:
        anchor = direct_mc(problem, ladder[0], trials=10_000 if args.quick else 50_000,
                           seed=seeds[3])
        if not anchor.failures:
            raise ValueError("MC anchor observed zero failures; increase its fixed trial count")
        anchor_note = f"MC ({anchor.failures} observed failures)"
    mc = direct_mc(problem, ladder[-1], trials=100 if args.quick else 1000, seed=seeds[0])
    chain = sample_faulty(problem, ladder[-1], config=config, seed=seeds[1])
    bar = estimate_logical_error(problem, ladder, anchor=anchor, config=config,
                                 seed=seeds[2], bootstrap_replicates=0)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"n": code.n, "k": len(code.lz), "checks_passed": code.n <= 12, "pl": bar.estimates[-1]}
    (out / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out / 'result.json'}")
    print(f"{anchor_note} anchor P_L={anchor.estimate:.6g}; direct MC P_L={mc.estimate:.6g}; BAR P_L={bar.estimates[-1]:.6g}")
    print(f"Conditional chain mean weight={np.count_nonzero(chain.states, axis=-1).mean():.6g}; it does not estimate absolute P_L.")
    print(f"Normalization {('enumerated at every rung' if code.n <= 12 else 'unchecked for n > 12')}. Decoder output means logical observables.")
    if code.n > 12:
        print("checks_passed=false means normalization was not checked; no preflight check failed.")
    print("Diagnostics do not prove convergence, ergodicity, or correctness; a full four-check verdict also needs independent direct-MC conditional variance.")
    print("SUMMARY " + json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"CHECK FAILED: {type(exc).__name__}: {str(exc).splitlines()[0]}") from None
