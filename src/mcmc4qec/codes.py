"""CSS factories preserving the reference research matrix ordering."""
import numpy as np

from .core import CSSCode, positive_integer


def _distance(d):
    d = positive_integer(d, "d")
    if d < 2:
        raise ValueError("d must be at least 2")
    return d


def _from_hgp(q, *, logical_basis="paired"):
    return _css_code(*(a.toarray() for a in (q.hx, q.hz, q.lx, q.lz)),
                     logical_basis=logical_basis)


def _css_code(hx, hz, lx, lz, *, logical_basis="paired"):
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
    """Return rectangular toric [[2*d1*d2, 2, min(d1,d2)]] in RIMC order.

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
    """Return the [[58,16,3]] Hamming hypergraph-product code in RIMC order.

    Returns a CSSCode whose X/Z logical bases have an invertible, nonidentity
    intersection matrix and whose ``logical_basis`` is ``independent``.
    Raises ImportError unless optional ldpc and bposd are installed. This is
    a static code and defines no probability or round unit.
    """
    from ldpc.codes import hamming_code
    from bposd.hgp import hgp
    h = hamming_code(3)
    return _from_hgp(hgp(h, h), logical_basis="independent")


def _gf2_row_reduce(matrix):
    """Return RREF and pivot columns over GF(2), retaining RIMC row order."""
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


def _gf2_nullspace(matrix):
    """Return the RIMC-ordered basis for the GF(2) nullspace."""
    n = matrix.shape[1]
    rref, pivots = _gf2_row_reduce(matrix)
    free_cols = [col for col in range(n) if col not in set(pivots)]
    vectors = np.zeros((len(free_cols), n), dtype=np.uint8)
    for row, free in enumerate(free_cols):
        vectors[row, free] = 1
        for rank, pivot in enumerate(pivots):
            vectors[row, pivot] = rref[rank, free]
    return vectors


def _css_logicals(hx, hz):
    """Construct the same independent quotient bases as RIMC."""
    n = hx.shape[1]
    k = n - len(_gf2_row_reduce(hx)[1]) - len(_gf2_row_reduce(hz)[1])

    def logicals_for(stabilizer, other):
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


def make_bb_code(l: int, m: int, a_terms, b_terms) -> CSSCode:
    """Return a bivariate bicycle code with RIMC shift and logical ordering.

    ``l`` and ``m`` are positive integer block dimensions. ``a_terms`` and
    ``b_terms`` are nonempty sequences of integer exponent pairs over Z_l x
    Z_m; duplicate terms cancel over GF(2). Returns a CSSCode with the RIMC
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

    def shift(di, dj):
        matrix = np.zeros((block, block), dtype=np.uint8)
        for i in range(l):
            for j in range(m):
                matrix[((i + di) % l) * m + ((j + dj) % m), i * m + j] = 1
        return matrix

    def polynomial(terms):
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
    """Return the static research BB [[72,12,6]] CSSCode.

    Takes no arguments. Uses the RIMC polynomial terms and retains its X/Z
    logical row order. Raises ValueError if the CSS matrices are invalid.
    The factory defines no probability or round unit.
    """
    return make_bb_code(6, 6, _BB_A, _BB_B)


def make_bb_code_108() -> CSSCode:
    """Return the static research BB [[108,8,10]] CSSCode.

    Takes no arguments. Uses the RIMC polynomial terms and retains its X/Z
    logical row order. Raises ValueError if the CSS matrices are invalid.
    The factory defines no probability or round unit.
    """
    return make_bb_code(9, 6, _BB_A, _BB_B)


def make_bb_code_144() -> CSSCode:
    """Return the static research BB [[144,12,12]] CSSCode.

    Takes no arguments. Uses the RIMC polynomial terms and retains its X/Z
    logical row order. Raises ValueError if the CSS matrices are invalid.
    The factory defines no probability or round unit.
    """
    return make_bb_code(12, 6, _BB_A, _BB_B)


def make_steane_code() -> CSSCode:
    """Return the static self-dual [[7,1,3]] Steane CSSCode.

    Takes no arguments. Retains the RIMC check-column and logical-row order.
    Raises ValueError if the CSS matrices are invalid. The factory defines no
    probability or round unit.
    """
    h = np.array([[1, 0, 1, 0, 1, 0, 1],
                  [0, 1, 1, 0, 0, 1, 1],
                  [0, 0, 0, 1, 1, 1, 1]], dtype=np.uint8)
    lx, lz = _css_logicals(h, h)
    return CSSCode(h, h, lx, lz)


def _lift_rows(checks, inner_logical, n_inner):
    n_outer = checks.shape[1]
    rows = []
    for check in checks:
        row = np.zeros(n_outer * n_inner, dtype=np.uint8)
        for block in range(n_outer):
            if check[block]:
                row[block*n_inner:(block+1)*n_inner] = inner_logical
        rows.append(row)
    return np.array(rows, dtype=np.uint8).reshape(checks.shape[0], n_outer*n_inner)


def _block_diag_copies(check, blocks):
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
    """Return level-``levels`` self-concatenated Steane in RIMC block order.

    ``levels`` must be a positive integer. Returns a static CSSCode with RIMC
    block order; level two has parameters [[49,1,9]]. Raises ValueError for
    invalid levels or matrices. No probability or round unit is implied.
    """
    levels = positive_integer(levels, "levels")
    code = make_steane_code()
    for _ in range(levels - 1):
        code = concatenate_css(make_steane_code(), code)
    return code
