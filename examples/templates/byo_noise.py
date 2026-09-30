"""Bring a normalized noise sampler and full-state log density (core only).

Default: about 1 second; --quick: under 1 second. Exact and direct MC give
absolute P_L. Correlated noise needs its true joint density, never a product
of marginals. The decoder is fixed; no BAR ladder is used here. Diagnostics
cannot prove convergence or correctness; the paper is in preparation.
"""

import argparse
from itertools import product
import json
import math
import os
from pathlib import Path, PureWindowsPath
import tempfile

import numpy as np

from mcmc4qec import CSSCode, CallableDecoder, Problem, direct_mc, exact, spawn_seeds


# >>> EDIT HERE
hx = np.zeros((0, 3), dtype=np.uint8)
hz = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
lx = np.array([[1, 1, 1]], dtype=np.uint8)
lz = np.array([[1, 0, 0]], dtype=np.uint8)
p = 0.2


class MyNoise:
    """Independent unequal rates; replace both methods for a joint noise law."""

    n = 3
    alphabets = (2, 2, 2)
    scales = np.array([0.5, 1.0, 1.5])

    def sample(self, p, rng):
        rates = p * self.scales
        return (rng.random(self.n) < rates).astype(np.uint8)

    def log_prob(self, state, p):
        state = np.asarray(state)
        if state.shape != (self.n,) or np.any((state != 0) & (state != 1)):
            raise ValueError("noise state must contain n binary entries")
        rates = p * self.scales
        if np.any((rates < 0) | (rates > 1)):
            raise ValueError("noise rates must be in [0, 1]")
        selected = np.where(state, rates, 1 - rates)
        return float(np.log(selected).sum()) if np.all(selected > 0) else -math.inf

    def metadata(self):
        return {"identifier": "byo-unequal-noise-v1", "scales": self.scales.tolist()}


def predict_observables(syndrome):
    """Return one logical-observable bit, not a physical correction."""
    return [int(tuple(syndrome) == (1, 0))]

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
    """Validate CSS algebra, noise normalization, decoder and failure contract."""
    if np.any(code.hx @ code.hz.T % 2):
        raise ValueError("hx @ hz.T must vanish modulo 2")
    if np.any(code.hz @ code.lx.T % 2) or np.any(code.hx @ code.lz.T % 2):
        raise ValueError("logical operators must commute with stabilizers")
    # CSSCode validates GF(2) logical rank, completeness, and pairings.
    if code.n <= 12:
        total = sum(math.exp(problem.log_prob(bits, p)) for bits in product((0, 1), repeat=code.n))
        if not math.isclose(total, 1.0, abs_tol=1e-10):
            raise ValueError(f"noise is not normalized: sum={total:.12g}")
        normalization = total
    else:
        print("Noise normalization unchecked for n > 12; validate on a small instance.")
        normalization = None
    m = code.hz.shape[0]
    syndromes = product((0, 1), repeat=m) if m <= 8 else (
        rng.integers(0, 2, size=m) for _ in range(32))
    for syndrome in syndromes:
        predicted = np.asarray(problem.decoder.predict(syndrome))
        repeated = np.asarray(problem.decoder.predict(syndrome))
        if predicted.shape != (len(code.lz),) or not np.all((predicted == 0) | (predicted == 1)):
            raise ValueError(f"decoder must predict {len(code.lz)} logical-observable bits")
        if not np.array_equal(predicted, repeated):
            raise ValueError("decoder prediction is not deterministic")
    states = product((0, 1), repeat=code.n) if code.n <= 12 else (
        rng.integers(0, 2, size=code.n) for _ in range(32))
    for bits in states:
        state = np.asarray(bits, dtype=np.uint8)
        if problem.is_faulty(state) != problem.is_faulty(state):
            raise ValueError("failure predicate is not deterministic")
    return normalization


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "mcmc4qec" / Path(__file__).stem)
    args = parser.parse_args()
    out = output_directory(args.out)
    code = CSSCode(hx, hz, lx, lz)
    noise = MyNoise()
    # Test injection lives in the test process; the editable default stays valid.
    offset = float(os.environ.get("MCMC4QEC_TEMPLATE_LOG_OFFSET", "0"))
    if offset:
        original = noise.log_prob
        noise.log_prob = lambda state, p: original(state, p) + offset
    problem = Problem(code.bit_flip_model(), noise,
                      CallableDecoder(predict_observables, identifier="byo-noise-decoder-v1"))
    seed, check_seed = spawn_seeds(args.seed, 2)
    normalization = check_components(code, problem, p, np.random.default_rng(check_seed))
    reference = exact(problem, p) if code.n <= 12 else None
    mc = direct_mc(problem, p, trials=100 if args.quick else 1000, seed=seed)
    pl = reference.estimate if reference is not None else mc.estimate
    out.mkdir(parents=True, exist_ok=True)
    payload = {"n": code.n, "normalization": normalization, "pl": pl}
    (out / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out / 'result.json'}")
    if reference is not None:
        print(f"Exact P_L={pl:.6g}; direct MC P_L={mc.estimate:.6g}, Wilson interval={mc.interval}")
    else:
        print(f"Direct MC P_L={pl:.6g}, Wilson interval={mc.interval}; exact enumeration unavailable.")
    print("Decoder output means logical observables; failure is their mismatch with truth.")
    print("Diagnostics do not prove convergence or correctness; complete four-check screening needs independent direct-MC conditional variance.")
    print("SUMMARY " + json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"CHECK FAILED: {type(exc).__name__}: {str(exc).splitlines()[0]}") from None
