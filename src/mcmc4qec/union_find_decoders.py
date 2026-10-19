"""Version-scoped, checked standalone Union-Find CSS decoder factories."""
from __future__ import annotations

from importlib.metadata import version
from typing import Any

import numpy as np

from ._checked_decoder import CheckedCorrectionAdapter
from .adapter_composition import SectorDecoder
from .core import CSSCode, positive_integer


def _backend() -> tuple[Any, str]:
    try:
        from ldpc import UnionFindDecoder
    except ImportError as exc:
        raise ImportError("install mcmc4qec[bposd] for Union-Find decoding") from exc
    installed = version("ldpc")
    if installed != "2.4.1":
        raise RuntimeError(
            "standalone Union-Find binding is verified only for ldpc 2.4.1; "
            f"installed version is {installed!r}")
    return UnionFindDecoder, installed


def _options(code: CSSCode, method: str, bits_per_step: int) -> None:
    if not isinstance(code, CSSCode):
        raise TypeError("code must be a CSSCode")
    if not isinstance(method, str) or method not in ("peeling", "inversion"):
        raise ValueError("method must be 'peeling' or 'inversion'")
    if positive_integer(bits_per_step, "bits_per_step") != 1:
        raise ValueError("bits_per_step must be 1: unweighted ldpc ignores growth limits")


def _checks(checks: np.ndarray, method: str) -> None:
    degrees = checks.sum(axis=0)
    if np.any(degrees == 0):
        raise ValueError("ldpc Union-Find does not support zero-degree check-matrix columns")
    if method == "peeling" and np.any(degrees > 2):
        raise ValueError("peeling requires check-matrix column degree 1 or 2")


def union_find_decoder(code: CSSCode, *, errors: str = "X", method: str = "peeling",
                       bits_per_step: int = 1) -> CheckedCorrectionAdapter:
    """Return unweighted Union-Find logical predictions for one CSS sector.

    ``errors='X'`` decodes ``hz`` and maps corrections through ``lz``; Z uses
    ``hx`` and ``lx``. Peeling accepts column degrees 1 (boundary) or 2;
    inversion accepts any positive degree. Zero-degree columns are rejected
    before entering the backend. Invalid or unrealizable syndromes and invalid
    corrections raise ValueError rather than being treated as logical success.

    This factory supports ldpc 2.4.1 only, with an explicit string-to-bool
    constructor workaround recorded in metadata. Other versions raise
    RuntimeError; missing ldpc raises ImportError. No BP, channel prior, LLR,
    or fallback is used. ``bits_per_step`` must be the integer 1: the backend's
    unweighted path grows all adjacent bits regardless of that parameter.
    Finite reproducibility checks do not guarantee identical OS/build behavior.
    """
    _options(code, method, bits_per_step)
    if not isinstance(errors, str) or errors not in ("X", "Z"):
        raise ValueError("errors must be 'X' or 'Z'")
    checks, logical_map = (code.hz, code.lz) if errors == "X" else (code.hx, code.lx)
    _checks(checks, method)
    backend, installed = _backend()
    native_method = "" if method == "peeling" else "inversion"
    decoder = backend(checks, uf_method=native_method)
    settings = dict(method=method, bits_per_step=1, llrs=None, channel_prior=None,
                    growth="all-adjacent-unweighted", native_uf_method=native_method,
                    compatibility="ldpc-2.4.1-str-to-bool", backend_version=installed)
    return CheckedCorrectionAdapter(
        decoder, check_matrix=checks, logical_map=logical_map,
        identifier=f"union-find-css-{errors.lower()}", settings=settings,
        decode_kwargs={"bits_per_step": 1})


def depolarizing_union_find_decoder(code: CSSCode, *, method: str = "peeling",
                                    bits_per_step: int = 1) -> SectorDecoder:
    """Return separate unweighted Union-Find X/Z logical predictions in order.

    This is an independent-sector decoder approximation; physical sampled Y
    correlations are preserved by the noise model. Neither sector uses a
    channel prior. Options, version restrictions, and exceptions follow
    ``union_find_decoder``. Both sectors are checked before native construction.
    """
    _options(code, method, bits_per_step)
    _checks(code.hz, method)
    _checks(code.hx, method)
    x = union_find_decoder(code, errors="X", method=method, bits_per_step=bits_per_step)
    z = union_find_decoder(code, errors="Z", method=method, bits_per_step=bits_per_step)
    return SectorDecoder(x, z, x_syndrome_size=len(code.hz),
                         identifier="depolarizing-union-find-sectors")
