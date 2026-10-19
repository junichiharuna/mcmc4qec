"""Small-code acceptance checks for research-compatible factories."""
import itertools

import numpy as np
import pytest

from mcmc4qec.codes import (
    make_asymmetric_toric_code, make_bb_code_72, make_bb_code_108,
    make_bb_code_144, make_concatenated_steane_code, make_hgp_hamming,
    make_steane_code, make_surface_code, make_toric_code,
)
from mcmc4qec.core import gf2_rank


@pytest.mark.parametrize("factory,d,n,k", [
    (make_toric_code, 2, 8, 2), (make_toric_code, 3, 18, 2),
    (make_surface_code, 2, 5, 1), (make_surface_code, 3, 13, 1),
])
def test_small_code_parameters(factory, d, n, k):
    pytest.importorskip("bposd")
    code = factory(d)
    assert code.n == n
    assert n - gf2_rank(code.hx) - gf2_rank(code.hz) == k
    assert not np.any(code.hx @ code.hz.T % 2)
    assert np.array_equal(code.lx @ code.lz.T % 2, np.eye(k))
    for checks, logicals in [(code.hz, code.lz), (code.hx, code.lx)]:
        found = False
        for weight in range(1, d + 1):
            for indices in itertools.combinations(range(n), weight):
                state = np.zeros(n, dtype=np.uint8)
                state[list(indices)] = 1
                if not np.any(checks @ state % 2) and np.any(logicals @ state % 2):
                    assert weight == d
                    found = True
            if found:
                break
        assert found


@pytest.mark.parametrize("d", [True, 1, 0, -1, 2.5])
@pytest.mark.parametrize("factory", [make_surface_code, make_toric_code])
def test_invalid_distance(factory, d):
    with pytest.raises(ValueError):
        factory(d)


@pytest.mark.parametrize("factory,n,k,independent", [
    (lambda: make_asymmetric_toric_code(3, 5), 30, 2, False),
    (make_hgp_hamming, 58, 16, True),
    (make_bb_code_72, 72, 12, True),
    (make_bb_code_108, 108, 8, True),
    (make_bb_code_144, 144, 12, True),
    (make_steane_code, 7, 1, False),
    (lambda: make_concatenated_steane_code(2), 49, 1, False),
])
def test_research_code_parameters_and_logical_completeness(factory, n, k, independent):
    if n in (30, 58):
        pytest.importorskip("bposd")
        pytest.importorskip("ldpc")
    code = factory()
    assert code.n == n
    assert n - gf2_rank(code.hx) - gf2_rank(code.hz) == k
    assert code.lx.shape == code.lz.shape == (k, n)
    assert not np.any(code.hx @ code.hz.T % 2)
    assert not np.any(code.hz @ code.lx.T % 2)
    assert not np.any(code.hx @ code.lz.T % 2)
    gram = code.lx @ code.lz.T % 2
    assert gf2_rank(gram.astype(np.uint8)) == k
    assert (not np.array_equal(gram, np.eye(k, dtype=int))) == independent


@pytest.mark.parametrize("factory,args", [
    (make_asymmetric_toric_code, (1, 3)),
    (make_asymmetric_toric_code, (3, 1)),
    (make_concatenated_steane_code, (0,)),
    (make_concatenated_steane_code, (True,)),
])
def test_invalid_factory_arguments(factory, args):
    with pytest.raises(ValueError):
        factory(*args)


@pytest.mark.parametrize("factory,d", [
    (make_steane_code, 3),
    (lambda: make_asymmetric_toric_code(3, 5), 3),
])
def test_small_code_x_distance_by_exhaustive_low_weights(factory, d):
    if d == 3 and factory is not make_steane_code:
        pytest.importorskip("bposd")
        pytest.importorskip("ldpc")
    code = factory()
    for weight in range(1, d):
        for indices in itertools.combinations(range(code.n), weight):
            error = np.zeros(code.n, dtype=np.uint8)
            error[list(indices)] = 1
            assert np.any(code.hz @ error % 2) or not np.any(code.lz @ error % 2)
    assert any(int(row.sum()) == d and np.any(code.lz @ row % 2)
               for row in code.lx)


@pytest.mark.parametrize("factory,upper_bound", [
    (make_hgp_hamming, 3),
    (make_bb_code_72, 6),
    (make_bb_code_108, 12),
    (make_bb_code_144, 12),
    (lambda: make_concatenated_steane_code(2), 9),
])
def test_large_code_x_distance_witness_only(factory, upper_bound):
    if factory is make_hgp_hamming:
        pytest.importorskip("bposd")
        pytest.importorskip("ldpc")
    code = factory()
    assert any(int(row.sum()) == upper_bound and not np.any(code.hz @ row % 2)
               and np.any(code.lz @ row % 2) for row in code.lx)
