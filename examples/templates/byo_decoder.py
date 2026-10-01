"""Wrap an existing decoder with an explicit output meaning (core only).

Default: about 1 second; --quick: under 1 second. The physical correction
is mapped to logical observables by lz; output shape never implies meaning.
Exact/direct MC estimate absolute P_L. This static decoder stays fixed across
the run. Diagnostics cannot prove correctness; the paper is in preparation.
"""

import argparse
from itertools import product
import json
import math
import os
from pathlib import Path, PureWindowsPath
import tempfile

import numpy as np

from mcmc4qec import CSSCode, IndependentBitFlip, Problem, direct_mc, exact, spawn_seeds
from mcmc4qec.adapters import DecoderAdapter


# >>> EDIT HERE
hx = np.zeros((0, 3), dtype=np.uint8)
hz = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
lx = np.array([[1, 1, 1]], dtype=np.uint8)
lz = np.array([[1, 0, 0]], dtype=np.uint8)
output_kind = "correction"  # Or "observable" if decode already returns k logical bits.


class ExistingDecoder:
    """Replace with a configured object exposing decode(syndrome)."""

    corrections = {(0, 0): (0, 0, 0), (1, 0): (1, 0, 0),
                   (1, 1): (0, 1, 0), (0, 1): (0, 0, 1)}

    def decode(self, syndrome):
        return self.corrections[tuple(syndrome)]

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


def check_components(code, raw_decoder, adapter, problem, p, rng):
    """Check algebra, normalized noise, raw output, logical map and failure."""
    if np.any(code.hx @ code.hz.T % 2):
        raise ValueError("hx @ hz.T must vanish modulo 2")
    if np.any(code.hz @ code.lx.T % 2) or np.any(code.hx @ code.lz.T % 2):
        raise ValueError("logical operators must commute with stabilizers")
    # CSSCode additionally verifies GF(2) logical independence and completeness.
    if code.n <= 12:
        total = sum(math.exp(problem.log_prob(bits, p)) for bits in product((0, 1), repeat=code.n))
        if not math.isclose(total, 1.0, abs_tol=1e-10):
            raise ValueError(f"noise is not normalized: sum={total:.12g}")
    else:
        print("Noise normalization unchecked for n > 12; validate on a small instance.")
    m = code.hz.shape[0]
    syndromes = product((0, 1), repeat=m) if m <= 8 else (
        rng.integers(0, 2, size=m) for _ in range(32))
    for syndrome in syndromes:
        syndrome = np.asarray(syndrome, dtype=np.uint8)
        raw = np.asarray(raw_decoder.decode(syndrome))
        again = np.asarray(raw_decoder.decode(syndrome))
        width = code.n if output_kind == "correction" else len(code.lz)
        if raw.shape != (width,) or not np.all((raw == 0) | (raw == 1)):
            raise ValueError(f"decoder {output_kind} output must contain {width} binary bits")
        if not np.array_equal(raw, again):
            raise ValueError("decoder output is not deterministic")
        prediction = adapter.predict(syndrome)
        if prediction.shape != (len(code.lz),) or not np.all((prediction == 0) | (prediction == 1)):
            raise ValueError(f"mapped decoder prediction must contain {len(code.lz)} logical bits")
        if output_kind == "correction":
            if not np.array_equal(code.hz @ raw % 2, syndrome):
                raise ValueError("physical correction does not match its syndrome")
            if not np.array_equal(code.lz @ raw % 2, prediction):
                raise ValueError("logical_map does not map correction to prediction")
    states = product((0, 1), repeat=code.n) if code.n <= 12 else (
        rng.integers(0, 2, size=code.n) for _ in range(32))
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
    code = CSSCode(hx, hz, lx, lz)
    raw_decoder = ExistingDecoder()
    append_bits = int(os.environ.get("MCMC4QEC_TEMPLATE_APPEND_BITS", "0"))
    if append_bits:
        original = raw_decoder.decode
        raw_decoder.decode = lambda syndrome: tuple(original(syndrome)) + (0,) * append_bits
    adapter = DecoderAdapter(raw_decoder, output_kind=output_kind,
                             logical_map=code.lz if output_kind == "correction" else None,
                             identifier="byo-existing-decoder-v1")
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), adapter)
    p = 0.25
    seed, check_seed = spawn_seeds(args.seed, 2)
    check_components(code, raw_decoder, adapter, problem, p, np.random.default_rng(check_seed))
    reference = exact(problem, p) if code.n <= 12 else None
    mc = direct_mc(problem, p, trials=100 if args.quick else 1000, seed=seed)
    pl = reference.estimate if reference is not None else mc.estimate
    out.mkdir(parents=True, exist_ok=True)
    payload = {"n": code.n, "output_kind": output_kind, "checks_passed": code.n <= 12, "pl": pl}
    (out / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out / 'result.json'}")
    if reference is not None:
        print(f"Exact P_L={pl:.6g}; direct MC P_L={mc.estimate:.6g}, Wilson interval={mc.interval}")
    else:
        print(f"Direct MC P_L={pl:.6g}, Wilson interval={mc.interval}; exact enumeration unavailable.")
    print(f"Declared decoder output_kind={output_kind}; mapped predictions are logical observables.")
    if code.n > 12:
        print("checks_passed=false means partial preflight: normalization unchecked; syndrome/state checks may use 32 sampled inputs.")
    print("Diagnostics do not prove convergence, ergodicity, or correctness; complete four-check screening needs independent direct-MC conditional variance.")
    print("SUMMARY " + json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"CHECK FAILED: {type(exc).__name__}: {str(exc).splitlines()[0]}") from None
