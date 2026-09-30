"""Research-compatible CSS decoder constructors with explicit logical output."""
from numbers import Integral, Real

import numpy as np

from .adapter_composition import SectorDecoder
from .adapters import DecoderAdapter, matching_from_check_matrix
from .core import CSSCode, gf2_rank


def _code(code):
    if not isinstance(code, CSSCode):
        raise TypeError("code must be a CSSCode")
    return code


def _mwpm(checks, logical_map, identifier):
    return matching_from_check_matrix(checks, logical_map=logical_map,
                                      identifier=identifier)


def mwpm_decoder(code: CSSCode):
    """Decode X errors with unweighted PyMatching and return logical predictions.

    Parameters
    ----------
    code : CSSCode
        Static CSS code whose Z checks measure X-error syndrome.

    Returns
    -------
    PyMatchingAdapter
        A decoder returning ``code.lz @ correction % 2`` as logical bits,
        not an error probability or per-round rate.

    Raises
    ------
    TypeError
        If ``code`` is not a CSSCode.
    ValueError
        If any check-matrix column has degree greater than two.
    ImportError
        If optional ``pymatching`` is unavailable.
    """
    code = _code(code)
    return _mwpm(code.hz, code.lz, "mwpm-css-x")


_BPOSD_DEFAULTS = dict(max_iter=100, bp_method="min_sum",
                       osd_method="osd_cs", osd_order=10)


def _bposd(checks, logical_map, p, identifier, kw):
    if "error_rate" in kw:
        raise ValueError("error_rate is supplied by p")
    if isinstance(p, (bool, np.bool_)) or not isinstance(p, Real) or not np.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("p must be a finite decoder prior in [0, 1]")
    settings = {**_BPOSD_DEFAULTS, **kw, "error_rate": float(p)}
    # ldpc 2.4.1 can corrupt the heap on Windows when OSD order exceeds the
    # binary nullity (e.g. Steane [[7,1,3]] with the research order 10).
    order = settings["osd_order"]
    if isinstance(order, (bool, np.bool_)) or not isinstance(order, Integral) or order < 0:
        raise ValueError("osd_order must be a nonnegative integer")
    order = int(order)
    if order > checks.shape[1] - gf2_rank(checks):
        raise ValueError("osd_order exceeds the check matrix nullity")
    settings["osd_order"] = order
    try:
        from ldpc import BpOsdDecoder
    except ImportError as exc:
        raise ImportError("install mcmc4qec[bposd] for BP-OSD decoding") from exc
    decoder = BpOsdDecoder(checks, **settings)
    return DecoderAdapter(decoder, output_kind="correction", identifier=identifier,
                          logical_map=logical_map, settings=settings,
                          distribution="ldpc")


def bposd_decoder(code: CSSCode, p: float, **kw):
    """Decode X errors with the RIMC BP-OSD defaults and return logical bits.

    ``code`` is a static CSSCode. ``p`` is the fixed decoder channel prior in
    [0, 1], which need not equal a later sampling noise probability. ``kw``
    overrides ldpc options; the defaults are max_iter=100, bp_method="min_sum",
    osd_method="osd_cs", and osd_order=10. Returns a DecoderAdapter mapping
    the physical correction through ``code.lz``. Raises TypeError for a
    non-CSS code, ValueError for invalid p, error_rate override, or OSD order
    exceeding check-matrix nullity, ImportError if ldpc is unavailable, and
    ldpc's own exception for its other invalid options. The prediction is a
    logical bit vector; no probability or per-round rate is returned.
    """
    code = _code(code)
    return _bposd(code.hz, code.lz, p, "bposd-css-x", kw)


def depolarizing_mwpm_decoder(code: CSSCode):
    """Return independent X/Z PyMatching sector decoders in model order.

    The first prediction uses ``hz`` and ``lz``; the second uses ``hx`` and
    ``lx``. The noise model retains sampled Y correlations, while this decoder
    makes an explicit independent-sector approximation. ``code`` must be a
    static CSSCode. Returns a SectorDecoder predicting X logical bits followed
    by Z logical bits. Raises TypeError for a non-CSS code, ValueError for
    a column of degree greater than two, or ImportError without pymatching.
    The prediction is a bit vector, not a probability or per-round rate.
    """
    code = _code(code)
    x = _mwpm(code.hz, code.lz, "mwpm-css-x")
    z = _mwpm(code.hx, code.lx, "mwpm-css-z")
    return SectorDecoder(x, z, x_syndrome_size=len(code.hz),
                         identifier="depolarizing-mwpm-sectors")


def depolarizing_bposd_decoder(code: CSSCode, p: float, **kw):
    """Return independent X/Z BP-OSD sector decoders at prior ``p``.

    This is a decoder approximation only; it does not split the I/X/Y/Z noise
    distribution. ``code`` is a static CSSCode and ``p`` is the fixed decoder
    prior in [0, 1], independent of a later sampling noise probability. ``kw``
    overrides the same ldpc options as ``bposd_decoder``. Returns a
    SectorDecoder predicting X logical bits followed by Z logical bits.
    Raises TypeError for a non-CSS code, ValueError for invalid prior or OSD
    order, ImportError without ldpc, or ldpc's exception for other invalid
    options. The prediction is a bit vector, not a per-round rate.
    """
    code = _code(code)
    x = _bposd(code.hz, code.lz, p, "bposd-css-x", kw)
    z = _bposd(code.hx, code.lx, p, "bposd-css-z", kw)
    return SectorDecoder(x, z, x_syndrome_size=len(code.hz),
                         identifier="depolarizing-bposd-sectors")
