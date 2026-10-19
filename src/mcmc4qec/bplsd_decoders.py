"""Fixed-prior BP-LSD recipes with checked physical corrections."""
from __future__ import annotations

from numbers import Real
from typing import Any

import numpy as np

from ._checked_decoder import CheckedCorrectionAdapter
from .adapter_composition import SectorDecoder
from .adapters import DecoderAdapter
from .core import CSSCode, positive_integer


def _settings(checks: np.ndarray, p: float, kw: dict[str, Any]) -> dict[str, Any]:
    allowed = {"max_iter", "bp_method", "ms_scaling_factor", "lsd_method",
               "lsd_order", "bits_per_step", "always_run_lsd"}
    if set(kw) - allowed:
        raise ValueError(f"unsupported BP-LSD settings: {sorted(set(kw) - allowed)}")
    if (isinstance(p, (bool, np.bool_)) or not isinstance(p, Real) or
            not np.isfinite(p) or not 0 < p < 1):
        raise ValueError("p must be a finite decoder prior strictly between 0 and 1")
    settings = dict(max_iter=100, bp_method="minimum_sum", ms_scaling_factor=1.,
                    lsd_method="lsd_0", lsd_order=0, bits_per_step=1,
                    always_run_lsd=False)
    settings.update(kw)
    for name in ("max_iter", "lsd_order", "bits_per_step"):
        value = positive_integer(settings[name], name, zero=name == "lsd_order")
        if value > np.iinfo(np.int32).max:
            raise ValueError(f"{name} exceeds native signed integer range")
        settings[name] = value
    if settings["bits_per_step"] > checks.shape[1]:
        raise ValueError("bits_per_step exceeds the number of bits")
    if settings["lsd_method"] not in ("lsd_0", "lsd_cs", "lsd_e"):
        raise ValueError("lsd_method must be lsd_0, lsd_cs or lsd_e")
    if settings["lsd_order"] != 0:
        raise ValueError("only lsd_order=0 is supported: positive orders lack verified local-cluster bounds")
    aliases = {"min_sum": "minimum_sum", "minimum_sum": "minimum_sum",
               "product_sum": "product_sum"}
    method = settings["bp_method"]
    if not isinstance(method, str) or method not in aliases:
        raise ValueError("bp_method must be minimum_sum, min_sum or product_sum")
    settings["bp_method"] = aliases[method]
    factor = settings["ms_scaling_factor"]
    if (isinstance(factor, (bool, np.bool_)) or not isinstance(factor, Real) or
            not np.isfinite(factor) or factor < 0):
        raise ValueError("ms_scaling_factor must be finite and nonnegative")
    settings["ms_scaling_factor"] = float(factor)
    if not isinstance(settings["always_run_lsd"], bool):
        raise ValueError("always_run_lsd must be a bool")
    settings.update(error_rate=float(p), schedule="parallel", omp_thread_count=1,
                    random_schedule_seed=0, random_serial_schedule=False,
                    serial_schedule_order=None, input_vector_type="syndrome")
    return settings


def bplsd_decoder(code: CSSCode, p: float, *, errors: str = "X", **kw: Any) -> DecoderAdapter:
    """Construct fixed-prior BP-LSD for one CSS error sector.

    ``p`` is the binary sector prior, strictly between zero and one, independent
    of subsequent sampling probabilities. X errors use ``hz``/``lz`` and Z
    errors use ``hx``/``lx``. Defaults: 100 BP iterations, minimum-sum factor 1,
    parallel schedule, one thread, no random schedule, LSD-0/order 0, one bit
    per growth step, and LSD only when BP fails. Supported overrides are
    ``max_iter``, ``bp_method`` (minimum_sum/min_sum/product_sum),
    ``ms_scaling_factor`` (nonnegative; zero uses the backend adaptive rule),
    ``lsd_method`` (lsd_0/lsd_cs/lsd_e), ``lsd_order``, ``bits_per_step`` and
    ``always_run_lsd``. Only order zero is supported: positive native orders
    lack verified bounds for local cluster nullities. Zero syndrome returns
    the identity correction before calling native code, for every prior.
    This explicit rule avoids an uninitialized native zero-syndrome branch
    observed in ldpc 2.4.1 and is recorded in metadata.

    Returns logical predictions after validating the physical correction
    against the supplied syndrome. Invalid settings, unrealizable syndromes,
    and inconsistent corrections raise ValueError; backend exceptions
    propagate without fallback. Raises TypeError for a non-CSS code and
    ImportError without the optional ``bposd`` extra (ldpc). Keep this object,
    settings and native build fixed throughout a BAR ladder. Determinism
    across platforms or all possible inputs is not certified by the factory.
    """
    if not isinstance(code, CSSCode):
        raise TypeError("code must be a CSSCode")
    if not isinstance(errors, str) or errors not in ("X", "Z"):
        raise ValueError("errors must be 'X' or 'Z'")
    checks, mapping = (code.hz, code.lz) if errors == "X" else (code.hx, code.lx)
    settings = _settings(checks, p, kw)
    try:
        from ldpc import BpLsdDecoder
    except ImportError as exc:
        raise ImportError("install mcmc4qec[bposd] for BP-LSD decoding") from exc
    backend = BpLsdDecoder(checks, **settings)
    return CheckedCorrectionAdapter(backend, check_matrix=checks, logical_map=mapping,
                                    identifier=f"bplsd-css-{errors.lower()}", settings=settings,
                                    zero_syndrome_is_identity=True)


def depolarizing_bplsd_decoder(code: CSSCode, p: float, **kw: Any) -> SectorDecoder:
    """Return checked BP-LSD sector decoders in X/Z model order.

    ``p`` is the fixed binary sector prior, not a total Pauli probability.
    For a physical depolarizing probability q, pass p=2*q/3 to match its
    marginals. Sampling still uses the joint I/X/Y/Z noise distribution;
    independent-sector decoding is an explicit decoder approximation.
    Options, validation and exceptions follow ``bplsd_decoder``.
    """
    x = bplsd_decoder(code, p, errors="X", **kw)
    z = bplsd_decoder(code, p, errors="Z", **kw)
    return SectorDecoder(x, z, x_syndrome_size=len(code.hz),
                         identifier="depolarizing-bplsd-sectors")
