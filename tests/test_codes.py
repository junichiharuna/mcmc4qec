"""Small-code acceptance checks for research-compatible factories."""
import itertools

import numpy as np
import pytest

from mcmc4qec.codes import make_surface_code, make_toric_code
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
