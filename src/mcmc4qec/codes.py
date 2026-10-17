"""CSS factories preserving the reference research matrix ordering."""
from __future__ import annotations
from typing import Any
from collections.abc import Sequence
from numpy.typing import ArrayLike
import numpy as np

from .core import CSSCode, positive_integer


def _distance(d: int) -> int:
    d = positive_integer(d, "d")
    if d < 2:
        raise ValueError("d must be at least 2")
    return d


def _from_hgp(q: Any, *, logical_basis: str="paired") -> CSSCode:
    return _css_code(*(a.toarray() for a in (q.hx, q.hz, q.lx, q.lz)),
                     logical_basis=logical_basis)


def _css_code(hx: ArrayLike, hz: ArrayLike, lx: ArrayLike, lz: ArrayLike, *, logical_basis: str="paired") -> CSSCode:
    if logical_basis == "paired":
        return CSSCode(hx, hz, lx, lz)
    return CSSCode(hx, hz, lx, lz, logical_basis=logical_basis)


def make_toric_code(d: int) -> CSSCode:
    """Return the [[2*d*d, 2, d]] toric code in research HGP ordering.

    ``d`` is an integer at least two. Returns a CSSCode with paired X/Z
    logical matrices in research row order. Raises ValueError for invalid d
    and ImportError unless optional ldpc and bposd are installed. No noise
    probability or time-round unit is implied by this static code.
    """
    d = _distance(d)
    from ldpc.codes import ring_code
    from bposd.hgp import hgp
    return _from_hgp(hgp(ring_code(d)))


def make_surface_code(d: int) -> CSSCode:
    """Return the [[2*d*d-2*d+1, 1, d]] unrotated surface code.

    ``d`` is an integer at least two. Returns a CSSCode with paired X/Z
    logical matrices in research HGP order. Raises ValueError for invalid d
    and ImportError unless optional ldpc and bposd are installed. This is a
    static code and defines no probability or round unit.
    """
    d = _distance(d)
    from ldpc.codes import rep_code
    from bposd.hgp import hgp
    return _from_hgp(hgp(rep_code(d), rep_code(d)))


def make_asymmetric_toric_code(d1: int, d2: int) -> CSSCode:
    """Return rectangular toric [[2*d1*d2, 2, min(d1,d2)]] in reference-implementation order.

    ``d1`` and ``d2`` are integer side lengths at least two. Returns a CSSCode
    with paired X/Z logical matrices in research HGP order. Raises ValueError
    for invalid side lengths and ImportError without optional ldpc and bposd.
    This is a static code and defines no probability or round unit.
    """
    d1, d2 = _distance(d1), _distance(d2)
    from ldpc.codes import ring_code
    from bposd.hgp import hgp
    return _from_hgp(hgp(ring_code(d1), ring_code(d2)))


def make_hgp_hamming() -> CSSCode:
    """Return the research-labeled [[58,16,3]] Hamming HGP code in reference-implementation order.

    Returns a CSSCode whose X/Z logical bases have an invertible, nonidentity
    intersection matrix and whose ``logical_basis`` is ``independent``.
    Raises ImportError unless optional ldpc and bposd are installed. The
    distance label is inherited from the reference implementation; this factory does not prove its
    lower bound. This static code defines no probability or round unit.
    """
    from ldpc.codes import hamming_code
    from bposd.hgp import hgp
    h = hamming_code(3)
    return _from_hgp(hgp(h, h), logical_basis="independent")


def _gf2_row_reduce(matrix: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Return RREF and pivot columns over GF(2), retaining reference-implementation row order."""
    a = np.asarray(matrix, dtype=np.uint8).copy()
    rows, cols = a.shape
    pivots = []
    row = 0
    for col in range(cols):
        found = next((r for r in range(row, rows) if a[r, col]), -1)
        if found == -1:
            continue
        a[[row, found]] = a[[found, row]]
        for r in range(rows):
            if r != row and a[r, col]:
                a[r] ^= a[row]
        pivots.append(col)
        row += 1
        if row == rows:
            break
    return a, pivots


def _gf2_nullspace(matrix: np.ndarray) -> np.ndarray:
    """Return the reference-ordered basis for the GF(2) nullspace."""
    n = matrix.shape[1]
    rref, pivots = _gf2_row_reduce(matrix)
    free_cols = [col for col in range(n) if col not in set(pivots)]
    vectors = np.zeros((len(free_cols), n), dtype=np.uint8)
    for row, free in enumerate(free_cols):
        vectors[row, free] = 1
        for rank, pivot in enumerate(pivots):
            vectors[row, pivot] = rref[rank, free]
    return vectors


def _css_logicals(hx: np.ndarray, hz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Construct the same independent quotient bases as the reference implementation."""
    n = hx.shape[1]
    k = n - len(_gf2_row_reduce(hx)[1]) - len(_gf2_row_reduce(hz)[1])

    def logicals_for(stabilizer: np.ndarray, other: np.ndarray) -> np.ndarray:
        kernel = _gf2_nullspace(stabilizer)
        if k == 0:
            return np.zeros((0, n), dtype=np.uint8)
        other_rref, other_pivots = _gf2_row_reduce(other)
        for rank, pivot in enumerate(other_pivots):
            for row in range(len(kernel)):
                if kernel[row, pivot]:
                    kernel[row] ^= other_rref[rank]
        reduced, _ = _gf2_row_reduce(kernel)
        return reduced[reduced.any(axis=1)]

    return logicals_for(hz, hx), logicals_for(hx, hz)


def make_bb_code(l: int, m: int, a_terms: tuple[tuple[int, int], ...] | list[tuple[int, int]], b_terms: tuple[tuple[int, int], ...] | list[tuple[int, int]]) -> CSSCode:
    """Return a bivariate bicycle code with reference-implementation shift and logical ordering.

    ``l`` and ``m`` are positive integer block dimensions. ``a_terms`` and
    ``b_terms`` are nonempty sequences of integer exponent pairs over Z_l x
    Z_m; duplicate terms cancel over GF(2). Returns a CSSCode with the reference-implementation
    row order and an explicit independent logical basis when needed. Raises
    ValueError for invalid dimensions, terms, or inconsistent CSS matrices.
    This is a static code and defines no probability or round unit.
    """
    l = positive_integer(l, "l")
    m = positive_integer(m, "m")
    for name, terms in (("a_terms", a_terms), ("b_terms", b_terms)):
        if not isinstance(terms, (list, tuple)) or not terms:
            raise ValueError(f"{name} must be a nonempty sequence of exponent pairs")
        for pair in terms:
            if (not isinstance(pair, (list, tuple)) or len(pair) != 2 or
                    any(isinstance(x, bool) or not isinstance(x, (int, np.integer)) for x in pair)):
                raise ValueError(f"{name} must contain integer exponent pairs")
    block = l * m

    def shift(di: int, dj: int) -> np.ndarray:
        matrix = np.zeros((block, block), dtype=np.uint8)
        for i in range(l):
            for j in range(m):
                matrix[((i + di) % l) * m + ((j + dj) % m), i * m + j] = 1
        return matrix

    def polynomial(terms: Sequence[tuple[int, int]]) -> np.ndarray:
        result = np.zeros((block, block), dtype=np.uint8)
        for di, dj in terms:
            result ^= shift(di, dj)
        return result

    a, b = polynomial(a_terms), polynomial(b_terms)
    hx = np.hstack((a, b))
    hz = np.hstack((b.T, a.T))
    lx, lz = _css_logicals(hx, hz)
    gram = lx @ lz.T % 2
    basis = "paired" if np.array_equal(gram, np.eye(len(lx), dtype=int)) else "independent"
    return _css_code(hx, hz, lx, lz, logical_basis=basis)


_BB_A = ((3, 0), (0, 1), (0, 2))
_BB_B = ((0, 3), (1, 0), (2, 0))


def make_bb_code_72() -> CSSCode:
    """Return the static research-labeled BB [[72,12,6]] CSSCode.

    Takes no arguments. Uses the reference polynomial terms and retains its X/Z
    logical row order. Raises ValueError if the CSS matrices are invalid.
    The distance lower bound is not checked here. The factory defines no
    probability or round unit.
    """
    return make_bb_code(6, 6, _BB_A, _BB_B)


def make_bb_code_108() -> CSSCode:
    """Return the static research-labeled BB [[108,8,10]] CSSCode.

    Takes no arguments. Uses the reference polynomial terms and retains its X/Z
    logical row order. Raises ValueError if the CSS matrices are invalid.
    The distance lower bound is not checked here. The factory defines no
    probability or round unit.
    """
    return make_bb_code(9, 6, _BB_A, _BB_B)


def make_bb_code_144() -> CSSCode:
    """Return the static research-labeled BB [[144,12,12]] CSSCode.

    Takes no arguments. Uses the reference polynomial terms and retains its X/Z
    logical row order. Raises ValueError if the CSS matrices are invalid.
    The distance lower bound is not checked here. The factory defines no
    probability or round unit.
    """
    return make_bb_code(12, 6, _BB_A, _BB_B)


def make_steane_code() -> CSSCode:
    """Return the static self-dual [[7,1,3]] Steane CSSCode.

    Takes no arguments. Retains the reference-implementation check-column and logical-row order.
    Raises ValueError if the CSS matrices are invalid. The factory defines no
    probability or round unit.
    """
    h = np.array([[1, 0, 1, 0, 1, 0, 1],
                  [0, 1, 1, 0, 0, 1, 1],
                  [0, 0, 0, 1, 1, 1, 1]], dtype=np.uint8)
    lx, lz = _css_logicals(h, h)
    return CSSCode(h, h, lx, lz)


def _tile_checks(l: int, m: int, box: int,
                 horizontal: tuple[tuple[int, int], ...],
                 vertical: tuple[tuple[int, int], ...]) -> tuple[np.ndarray, np.ndarray]:
    """Translate reflected CSS tiles onto the unrotated open layout."""
    reach = box - 1
    qubits = [(direction, x, y) for direction in (0, 1)
              for y in range(m) for x in range(l)]
    indices = {edge: i for i, edge in enumerate(qubits)}
    z_horizontal = tuple((reach-x, reach-y) for x, y in vertical)
    z_vertical = tuple((reach-x, reach-y) for x, y in horizontal)

    def checks(xs: range, ys: range, h: tuple[tuple[int, int], ...],
               v: tuple[tuple[int, int], ...]) -> np.ndarray:
        rows = np.zeros((len(xs)*len(ys), len(qubits)), dtype=np.uint8)
        for row, (x, y) in enumerate((x, y) for y in ys for x in xs):
            for direction, terms in enumerate((h, v)):
                for dx, dy in terms:
                    col = indices.get((direction, x+dx, y+dy))
                    if col is not None:
                        rows[row, col] ^= 1
        return rows

    hx = checks(range(l-reach), range(-reach, m), horizontal, vertical)
    hz = checks(range(-reach, l), range(m-reach), z_horizontal, z_vertical)
    if np.any(hx @ hz.T % 2):
        raise ValueError("tile boundary checks do not commute")
    keep = hx.any(axis=0) & hz.any(axis=0)
    hx, hz = hx[:, keep], hz[:, keep]
    hx, hz = hx[hx.any(axis=1)], hz[hz.any(axis=1)]
    if np.any(hx @ hz.T % 2):
        raise ValueError("tile pruning broke CSS commutation")
    return hx, hz


def make_tile_code(l: int, m: int, *, preset: str="w6_288_8_12") -> CSSCode:
    """Build an open-boundary weight-six tile CSS code without optional packages.

    ``l`` and ``m`` are integer edge-grid dimensions at least three, not code
    distances. The only supported ``preset`` is ``w6_288_8_12``: horizontal
    X support x+x**2+y**2 and vertical support 1+x**2*y+x**2*y**2. Z tiles
    exchange the layers and reflect both coordinates about two. X anchors
    span x=0..l-3, y=-2..m-1; Z anchors span x=-2..l-1, y=0..m-3.
    Supports are clipped to the open grid, with qubits unsupported by either
    check type removed. Columns are horizontal then vertical, y-major/x-minor.
    Rows are y-major/x-minor anchors with empty checks removed.

    Returns a CSSCode with a deterministic paired logical basis. The 12x12
    instance has n=288, k=8 and literature distance 12; this function checks
    CSS algebra but does not independently certify that distance. The 6x6
    instance has n=72, k=8. This is a static code, not a measurement circuit.
    BP-OSD supports its hypergraph checks; generic MWPM does not.
    Raises ValueError for invalid dimensions, presets or CSS matrices.

    Construction: Steffan et al., arXiv:2504.09171, open rectangular layout;
    the polynomial convention is given in arXiv:2607.05897, Section II.1.
    """
    l, m = positive_integer(l, "l"), positive_integer(m, "m")
    if min(l, m) < 3:
        raise ValueError("tile l and m must be at least three")
    if not isinstance(preset, str) or preset != "w6_288_8_12":
        raise ValueError("unknown tile preset; use w6_288_8_12")
    hx, hz = _tile_checks(l, m, 3, ((1, 0), (2, 0), (0, 2)),
                         ((0, 0), (2, 1), (2, 2)))
    lx, lz = _css_logicals(hx, hz)
    k = len(lx)
    gram = lx @ lz.T % 2
    augmented, pivots = _gf2_row_reduce(np.hstack((gram, np.eye(k, dtype=np.uint8))))
    if pivots[:k] != list(range(k)):
        raise ValueError("incomplete tile logical pairing")
    lz = (augmented[:, k:].T @ lz % 2).astype(np.uint8)
    return CSSCode(hx, hz, lx, lz)


def _lift_rows(checks: np.ndarray, inner_logical: np.ndarray, n_inner: int) -> np.ndarray:
    n_outer = checks.shape[1]
    rows = []
    for check in checks:
        row = np.zeros(n_outer * n_inner, dtype=np.uint8)
        for block in range(n_outer):
            if check[block]:
                row[block*n_inner:(block+1)*n_inner] = inner_logical
        rows.append(row)
    return np.array(rows, dtype=np.uint8).reshape(checks.shape[0], n_outer*n_inner)


def _block_diag_copies(check: np.ndarray, blocks: int) -> np.ndarray:
    rows, n_inner = check.shape
    result = np.zeros((blocks*rows, blocks*n_inner), dtype=np.uint8)
    for block in range(blocks):
        result[block*rows:(block+1)*rows, block*n_inner:(block+1)*n_inner] = check
    return result


def concatenate_css(outer: CSSCode, inner: CSSCode) -> CSSCode:
    """Concatenate an outer CSS code with a single-logical-qubit inner code.

    ``outer`` and ``inner`` are static CSSCode instances; ``inner`` must
    encode one logical qubit. Returns a CSSCode with inner checks ordered
    block by block before lifted outer checks. Raises TypeError for a non-CSS
    input and ValueError unless the inner code encodes one qubit or the
    concatenated matrices are invalid. No probability or round unit is added.
    """
    if not isinstance(outer, CSSCode) or not isinstance(inner, CSSCode):
        raise TypeError("outer and inner must be CSSCode instances")
    if len(inner.lx) != 1:
        raise ValueError("inner code must encode exactly one qubit")
    n_in, n_out = inner.n, outer.n
    hx = np.vstack((_block_diag_copies(inner.hx, n_out),
                    _lift_rows(outer.hx, inner.lx[0], n_in)))
    hz = np.vstack((_block_diag_copies(inner.hz, n_out),
                    _lift_rows(outer.hz, inner.lz[0], n_in)))
    lx = _lift_rows(outer.lx, inner.lx[0], n_in)
    lz = _lift_rows(outer.lz, inner.lz[0], n_in)
    gram = lx @ lz.T % 2
    basis = "paired" if np.array_equal(gram, np.eye(len(lx), dtype=int)) else "independent"
    return _css_code(hx, hz, lx, lz, logical_basis=basis)


def make_concatenated_steane_code(levels: int) -> CSSCode:
    """Return level-``levels`` self-concatenated Steane in reference-implementation block order.

    ``levels`` must be a positive integer. Returns a static CSSCode with reference-implementation
    block order; level two has research-labeled parameters [[49,1,9]]. The
    distance lower bound is not checked here. Raises ValueError for invalid
    levels or matrices. No probability or round unit is implied.
    """
    levels = positive_integer(levels, "levels")
    code = make_steane_code()
    for _ in range(levels - 1):
        code = concatenate_css(make_steane_code(), code)
    return code
