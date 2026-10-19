"""Fixed-prior BeliefFind factories with checked physical corrections."""
from __future__ import annotations

from numbers import Integral, Real
from typing import Any

import numpy as np

from ._checked_decoder import CheckedCorrectionAdapter
from .adapter_composition import SectorDecoder
from .core import CSSCode


_DEFAULTS: dict[str, Any] = dict(
    max_iter=100, bp_method="min_sum", ms_scaling_factor=1.,
    schedule="parallel", omp_thread_count=1, random_schedule_seed=0,
    serial_schedule_order=None, random_serial_schedule=False,
    input_vector_type="syndrome", uf_method="inversion", bits_per_step=1,
)


def _code(code: CSSCode) -> CSSCode:
    if not isinstance(code, CSSCode):
        raise TypeError("code must be a CSSCode")
    return code


def _check_graph(checks: np.ndarray, method: str) -> None:
    degrees = checks.sum(axis=0)
    # The native UF constructor throws for these, even in inversion mode.
    if np.any(degrees == 0):
        raise ValueError("BeliefFind does not support zero-degree check-matrix columns")
    if method == "peeling" and np.any(degrees > 2):
        raise ValueError("BeliefFind peeling requires column degree at most two")


def _settings(p: float, n: int, kw: dict[str, Any]) -> dict[str, Any]:
    if isinstance(p, (bool, np.bool_)) or not isinstance(p, Real) or not np.isfinite(p) or not 0 < p < 1:
        raise ValueError("p must be a finite fixed sector prior in (0, 1)")
    unknown = set(kw) - set(_DEFAULTS)
    if unknown:
        raise ValueError(f"unsupported BeliefFind options: {', '.join(sorted(unknown))}")
    settings = {**_DEFAULTS, **kw, "error_rate": float(p)}
    for key, upper in (("max_iter", 2**31 - 1), ("bits_per_step", n)):
        value = settings[key]
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or not 1 <= value <= upper:
            raise ValueError(f"{key} must be an integer in [1, {upper}]")
        settings[key] = int(value)
    method = settings["bp_method"]
    if not isinstance(method, str) or method not in ("min_sum", "minimum_sum", "product_sum"):
        raise ValueError("bp_method must be min_sum, minimum_sum, or product_sum")
    settings["bp_method"] = "min_sum" if method == "minimum_sum" else method
    uf = settings["uf_method"]
    if not isinstance(uf, str) or uf not in ("inversion", "peeling"):
        raise ValueError("uf_method must be inversion or peeling")
    factor = settings["ms_scaling_factor"]
    if isinstance(factor, (bool, np.bool_)) or not isinstance(factor, Real) or not np.isfinite(factor) or factor < 0:
        raise ValueError("ms_scaling_factor must be finite and nonnegative")
    settings["ms_scaling_factor"] = float(factor)
    for key in ("schedule", "input_vector_type"):
        if not isinstance(settings[key], str) or settings[key] != _DEFAULTS[key]:
            raise ValueError(f"{key} must be {_DEFAULTS[key]!r}")
    for key in ("omp_thread_count", "random_schedule_seed"):
        value = settings[key]
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value != _DEFAULTS[key]:
            raise ValueError(f"{key} must be {_DEFAULTS[key]}")
        settings[key] = int(value)
    if settings["serial_schedule_order"] is not None:
        raise ValueError("serial_schedule_order must be None for parallel scheduling")
    if settings["random_serial_schedule"] is not False:
        raise ValueError("random_serial_schedule must be False")
    return settings


def _construct(checks: np.ndarray, logical_map: np.ndarray, settings: dict[str, Any],
               identifier: str) -> CheckedCorrectionAdapter:
    _check_graph(checks, settings["uf_method"])
    try:
        from ldpc import BeliefFindDecoder
    except ImportError as exc:
        raise ImportError("install mcmc4qec[bposd] for BeliefFind decoding") from exc
    constructor_settings = {key: value for key, value in settings.items()
                            if key != "random_serial_schedule"}
    decoder = BeliefFindDecoder(checks, **constructor_settings)
    # BeliefFind 2.4.1 omits this keyword from its Cython constructor.
    decoder.random_serial_schedule = False
    if decoder.random_serial_schedule:
        raise ValueError("BeliefFind backend did not disable random serial scheduling")
    return CheckedCorrectionAdapter(decoder, check_matrix=checks,
                                    logical_map=logical_map, identifier=identifier,
                                    settings=settings)


def belief_find_decoder(code: CSSCode, p: float, *, errors: str = "X",
                        **kw: Any) -> CheckedCorrectionAdapter:
    """Return checked logical predictions from fixed-prior BP plus Union-Find.

    ``p`` is a sector prior in (0, 1), fixed independently of sampling noise.
    X uses ``hz/lz`` and Z uses ``hx/lx``. Defaults are 100 min-sum BP
    iterations, scaling 1, inversion UF, and one bit per cluster growth step.
    ``kw`` can override max_iter, bp_method (min_sum/minimum_sum/product_sum),
    ms_scaling_factor (finite nonnegative), uf_method (inversion/peeling),
    and bits_per_step (1 through code.n). Parallel BP, one thread, and
    disabled random scheduling are fixed; explicit matching values are allowed.

    Both UF modes reject zero-degree columns; peeling also rejects degree
    above two. Invalid settings, unrealizable syndromes, or physical
    corrections not satisfying Hc=s raise ValueError. Missing ldpc raises
    ImportError; a non-CSS code raises TypeError. Native exceptions propagate.
    No additional fallback is used. Reproducibility across backend builds or
    platforms is not guaranteed; retain one validated environment and settings
    throughout a BAR ladder.
    """
    code = _code(code)
    if not isinstance(errors, str) or errors not in ("X", "Z"):
        raise ValueError("errors must be 'X' or 'Z'")
    settings = _settings(p, code.n, kw)
    h, logical = (code.hz, code.lz) if errors == "X" else (code.hx, code.lx)
    return _construct(h, logical, settings, f"belief-find-css-{errors.lower()}")


def depolarizing_belief_find_decoder(code: CSSCode, p: float,
                                     **kw: Any) -> SectorDecoder:
    """Compose checked X/Z BeliefFind decoders at the same fixed sector prior.

    ``p`` is the sector prior, as in depolarizing_bposd_decoder: for physical
    depolarizing probability p_star explicitly pass ``p=2*p_star/3``. Options
    and validation follow belief_find_decoder. Predictions are X logical bits
    followed by Z logical bits. Independent-sector decoding is an explicit
    approximation recorded in metadata; physical Y correlations are retained
    by the noise model. This function never changes the sampling noise.
    """
    code = _code(code)
    settings = _settings(p, code.n, kw)
    # Validate both sectors before entering either native constructor.
    for h in (code.hz, code.hx):
        _check_graph(h, settings["uf_method"])
    x = _construct(code.hz, code.lz, settings, "belief-find-css-x")
    z = _construct(code.hx, code.lx, settings, "belief-find-css-z")
    return SectorDecoder(x, z, x_syndrome_size=len(code.hz),
                         identifier="depolarizing-belief-find-sectors")
