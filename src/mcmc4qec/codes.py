"""CSS factories preserving the reference research matrix ordering."""
from .core import CSSCode, positive_integer


def _distance(d):
    d = positive_integer(d, "d")
    if d < 2:
        raise ValueError("d must be at least 2")
    return d


def _from_hgp(q):
    return CSSCode(*(a.toarray() for a in (q.hx, q.hz, q.lx, q.lz)))


def make_toric_code(d: int) -> CSSCode:
    """Return the [[2*d*d, 2, d]] toric code in research HGP ordering.

    Requires optional ldpc and bposd packages. Raises ValueError unless d is
    an integer at least two. The result contains paired CSS logical matrices.
    """
    d = _distance(d)
    from ldpc.codes import ring_code
    from bposd.hgp import hgp
    return _from_hgp(hgp(ring_code(d)))


def make_surface_code(d: int) -> CSSCode:
    """Return the [[2*d*d-2*d+1, 1, d]] unrotated surface code.

    Requires optional ldpc and bposd packages. Raises ValueError unless d is
    an integer at least two. The result uses research HGP matrix ordering.
    """
    d = _distance(d)
    from ldpc.codes import rep_code
    from bposd.hgp import hgp
    return _from_hgp(hgp(rep_code(d), rep_code(d)))
