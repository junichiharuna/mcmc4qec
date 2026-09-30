"""Research-compatible CSS decoder constructors with explicit logical output."""
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
        A decoder returning ``code.lz @ correction % 2``.

    Raises
    ------
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
    settings = {**_BPOSD_DEFAULTS, **kw, "error_rate": p}
    # ldpc 2.4.1 can corrupt the heap on Windows when OSD order exceeds the
    # binary nullity (e.g. Steane [[7,1,3]] with the research order 10).
    order = settings["osd_order"]
    if isinstance(order, int) and order > checks.shape[1] - gf2_rank(checks):
        raise ValueError("osd_order exceeds the check matrix nullity")
    try:
        from ldpc import BpOsdDecoder
    except ImportError as exc:
        raise ImportError("install mcmc4qec[bposd] for BP-OSD decoding") from exc
    decoder = BpOsdDecoder(checks, **settings)
    return DecoderAdapter(decoder, output_kind="correction", identifier=identifier,
                          logical_map=logical_map, settings=settings,
                          distribution="ldpc")


def bposd_decoder(code: CSSCode, p: float, **kw):
    """Decode X errors using the RIMC BP-OSD defaults at channel prior ``p``.

    ``kw`` explicitly overrides ``max_iter``, ``bp_method``, ``osd_method`` or
    ``osd_order`` and is passed to ``ldpc.BpOsdDecoder``. The default values
    are 100, ``min_sum``, ``osd_cs`` and 10. The returned adapter maps the
    physical correction through ``code.lz`` to a logical prediction. Invalid
    decoder options raise from ldpc; ``error_rate`` cannot override ``p``.
    """
    code = _code(code)
    return _bposd(code.hz, code.lz, p, "bposd-css-x", kw)


def depolarizing_mwpm_decoder(code: CSSCode):
    """Return independent X/Z PyMatching sector decoders in model order.

    The first prediction uses ``hz`` and ``lz``; the second uses ``hx`` and
    ``lx``. The noise model retains sampled Y correlations, while this decoder
    makes an explicit independent-sector approximation. Requires pymatching.
    """
    code = _code(code)
    x = _mwpm(code.hz, code.lz, "mwpm-css-x")
    z = _mwpm(code.hx, code.lx, "mwpm-css-z")
    return SectorDecoder(x, z, x_syndrome_size=len(code.hz),
                         identifier="depolarizing-mwpm-sectors")


def depolarizing_bposd_decoder(code: CSSCode, p: float, **kw):
    """Return independent X/Z BP-OSD sector decoders at prior ``p``.

    This is a decoder approximation only; it does not split the I/X/Y/Z noise
    distribution. Invalid options raise from ldpc; ``error_rate`` cannot
    override ``p``.
    """
    code = _code(code)
    x = _bposd(code.hz, code.lz, p, "bposd-css-x", kw)
    z = _bposd(code.hx, code.lx, p, "bposd-css-z", kw)
    return SectorDecoder(x, z, x_syndrome_size=len(code.hz),
                         identifier="depolarizing-bposd-sectors")
