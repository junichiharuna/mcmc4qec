"""Exact logical-coset representatives for conditional MCMC initialization."""
import itertools

import numpy as np

from .core import binary, gf2_rank


def _rows(stabilizers, n):
    if np.asarray(stabilizers).size == 0:
        return np.zeros((0, n), dtype=np.uint8)
    return binary(stabilizers, ndim=2, shape=(len(stabilizers), n), name="stabilizers")


def _independent_rows(rows):
    basis = np.zeros((0, rows.shape[1]), dtype=np.uint8)
    rank = 0
    for row in rows:
        candidate = np.vstack((basis, row))
        next_rank = gf2_rank(candidate)
        if next_rank > rank:
            basis, rank = candidate, next_rank
    return basis


def minimum_weight_coset_representative(logical, stabilizers, *, time_limit=30.0):
    """Return an exact minimum-Hamming-weight member of logical + span(stabilizers).

    `logical` is a binary `(n,)` vector and `stabilizers` is a binary `(r,n)`
    matrix. `time_limit` is the MILP solver limit in seconds for rank above 12.
    The result is a binary `(n,)` vector; its weight counts physical bits.
    Enumeration handles small row ranks; larger ranks use SciPy MILP and require
    an optimal solver status. A solver timeout or unavailable SciPy raises rather
    than returning an unverified approximation. This finite binary algorithm is
    intended for static CSS bit-flip sectors, not categorical circuit faults.
    Invalid binary data or time limits raise ValueError, missing SciPy raises
    ImportError, and an unproven optimum raises RuntimeError.
    """
    logical = binary(logical, ndim=1, name="logical")
    rows = _independent_rows(_rows(stabilizers, len(logical)))
    rank = len(rows)
    if not np.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and positive")
    if rank <= 12:
        best = logical.copy()
        best_weight = int(best.sum())
        for mask in itertools.product((0, 1), repeat=rank):
            candidate = logical ^ (np.asarray(mask, dtype=np.uint8) @ rows % 2)
            weight = int(candidate.sum())
            if weight < best_weight:
                best, best_weight = candidate, weight
        return best

    from scipy.optimize import Bounds, LinearConstraint, milp

    n = len(logical)
    # x - S.T @ z + 2t = logical. Integer t enforces GF(2) parity.
    a = np.hstack((np.eye(n), -rows.T.astype(float), 2 * np.eye(n)))
    objective = np.concatenate((np.ones(n), np.zeros(rank + n)))
    lower = np.zeros(2 * n + rank)
    upper = np.concatenate((np.ones(n + rank), np.full(n, (rank + 1) // 2)))
    answer = milp(objective, integrality=np.ones(len(objective)),
                  bounds=Bounds(lower, upper),
                  constraints=LinearConstraint(a, logical, logical),
                  options={"time_limit": float(time_limit), "mip_rel_gap": 0.0})
    if answer.status != 0 or answer.x is None:
        raise RuntimeError("minimum-weight coset optimization did not prove optimality")
    representative = np.rint(answer.x[:n]).astype(np.uint8)
    coefficients = np.rint(answer.x[n:n + rank]).astype(np.uint8)
    if not np.array_equal(representative, logical ^ (coefficients @ rows % 2)):
        raise RuntimeError("minimum-weight coset optimization returned an invalid state")
    # The objective is integer. A dual bound less than half a unit below the
    # feasible weight excludes every smaller integer objective despite solver
    # floating-point tolerances; a mere status=optimal is not enough.
    lower_bound = answer.get("mip_dual_bound")
    if (lower_bound is None or not np.isfinite(lower_bound) or
            int(representative.sum()) - lower_bound >= 0.5):
        raise RuntimeError("minimum-weight coset optimization lacks an integer optimum certificate")
    return representative


def _basis(code, sector):
    if sector == "x":
        return code.lx, code.hx, code.lz, code.hz
    if sector == "z":
        return code.lz, code.hz, code.lx, code.hx
    raise ValueError("sector must be 'x' or 'z'")


def logical_representatives(code, *, sector="x", time_limit=30.0):
    """Minimize each logical basis row inside its own stabilizer coset.

    The row index denotes a basis element, not an observable bit. In an
    independent (non-paired) CSS basis these differ; use
    `observable_sector_initial_state` to request an observable bit pattern.
    `code` is a CSSCode, `sector` is "x" or "z", and `time_limit` is seconds
    per large-rank MILP. Returns a binary `(k,n)` matrix. An invalid sector or
    zero-logical code raises ValueError; solver errors propagate as ImportError
    or RuntimeError. No noise probability is used and faultiness is not tested.
    """
    logicals, stabilizers, _, _ = _basis(code, sector)
    if len(logicals) == 0:
        raise ValueError("code has no nontrivial logical sectors")
    return np.stack([minimum_weight_coset_representative(row, stabilizers,
                     time_limit=time_limit) for row in logicals])


def minimum_weight_initial_state(code, *, sector="x", time_limit=30.0):
    """Return the lightest minimized logical basis representative.

    Output is a binary `(n,)` array accepted by `sample_faulty(initial_state=)`
    for the corresponding bit-flip sector when its decoder marks it faulty.
    `code` is a CSSCode, `sector` is "x" or "z", and `time_limit` is seconds
    per large-rank MILP. Invalid sectors and zero-logical codes raise ValueError;
    ImportError or RuntimeError can arise from exact optimization. Noise
    support and the caller's failure predicate are not evaluated here.
    """
    rows = logical_representatives(code, sector=sector, time_limit=time_limit)
    return rows[int(np.argmin(rows.sum(axis=1)))].copy()


def maximum_weight_initial_state(code, *, sector="x", time_limit=30.0):
    """Return the heaviest of the per-coset minimum-weight basis elements.

    This is the paper's long initialization, not the maximum weight anywhere
    in the full fault space. The result is a binary `(n,)` array.
    `code` is a CSSCode, `sector` is "x" or "z", and `time_limit` is seconds
    per large-rank MILP. Invalid sectors and zero-logical codes raise ValueError;
    ImportError or RuntimeError can arise from exact optimization. The result
    is not guaranteed faulty for an arbitrary decoder or predicate.
    """
    rows = logical_representatives(code, sector=sector, time_limit=time_limit)
    return rows[int(np.argmax(rows.sum(axis=1)))].copy()


def _solve_gf2(matrix, target):
    n = len(target)
    aug = np.hstack((matrix.astype(np.uint8).copy(), target[:, None])).astype(np.uint8)
    for col in range(n):
        pivots = np.flatnonzero(aug[col:, col])
        if not len(pivots):
            raise ValueError("logical crossing matrix is singular")
        pivot = col + int(pivots[0])
        aug[[col, pivot]] = aug[[pivot, col]]
        for row in range(n):
            if row != col and aug[row, col]:
                aug[row] ^= aug[col]
    return aug[:, -1]


def observable_sector_initial_state(code, observable, *, sector="x", time_limit=30.0):
    """Find the minimum-weight representative of a requested observable sector.

    code is a CSSCode supplying the stabilizer and logical matrices.
    The GF(2) crossing matrix maps logical-basis coefficients to observable
    bits, so non-paired independent CSS bases are supported. Zero is rejected
    because a zero logical sector is generally not a faulty initialization.
    `observable` is a nonzero binary `(k,)` vector, `sector` is "x" or "z",
    and `time_limit` is seconds per large-rank MILP. Returns a binary `(n,)`
    representative. Invalid inputs or a singular crossing matrix raise
    ValueError; exact solver failures raise ImportError or RuntimeError.
    Noise support and a custom failure predicate still require validation.
    """
    logicals, stabilizers, observables, checks = _basis(code, sector)
    target = binary(observable, ndim=1, shape=(len(logicals),), name="observable")
    if not np.any(target):
        raise ValueError("observable sector must be nonzero")
    crossing = logicals @ observables.T % 2
    coefficients = _solve_gf2(crossing.T, target)
    logical = coefficients @ logicals % 2
    representative = minimum_weight_coset_representative(logical, stabilizers,
                                                           time_limit=time_limit)
    if np.any(checks @ representative % 2) or not np.array_equal(
            observables @ representative % 2, target):
        raise RuntimeError("representative does not preserve requested sector")
    return representative


def random_logical_sector_initial_state(code, *, sector="x", seed=None,
                                        rng=None, time_limit=30.0):
    """Draw a uniform nonzero observable sector and minimize its CSS coset.

    Supply either `seed` or `rng`. The returned binary `(n,)` state can be used
    as `sample_faulty(initial_state=)` after the caller verifies failure and
    noise support for its own decoder, predicate, and probability.
    `code` is a CSSCode, `sector` is "x" or "z", and `time_limit` is seconds
    per large-rank MILP. `seed` initializes NumPy's generator; `rng` accepts
    an existing generator. Both at once, invalid sectors, or a zero-logical
    code raise ValueError. Exact solver failures raise ImportError or
    RuntimeError. No physical error probability is chosen by this function.
    """
    if rng is not None and seed is not None:
        raise ValueError("supply either seed or rng")
    logicals, _, _, _ = _basis(code, sector)
    if len(logicals) == 0:
        raise ValueError("code has no nontrivial logical sectors")
    rng = np.random.default_rng(seed) if rng is None else rng
    target = np.zeros(len(logicals), dtype=np.uint8)
    while not np.any(target):
        target = rng.integers(0, 2, size=len(logicals), dtype=np.uint8)
    return observable_sector_initial_state(code, target, sector=sector,
                                            time_limit=time_limit)
