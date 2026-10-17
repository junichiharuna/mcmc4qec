"""Finite CSS and decoder acceptance for open-boundary tile codes."""
import itertools

import numpy as np
import pytest

from mcmc4qec import make_tile_code, bposd_decoder, mwpm_decoder
from mcmc4qec.codes import _tile_checks
from mcmc4qec.core import CSSCode, gf2_rank


@pytest.mark.parametrize("l,m,n,k", [(4, 4, 32, 8), (6, 6, 72, 8), (12, 12, 288, 8)])
def test_tile_parameters_and_paired_logicals(l, m, n, k):
    c = make_tile_code(l, m)
    assert isinstance(c, CSSCode)
    assert c.n == n
    assert c.n - gf2_rank(c.hx) - gf2_rank(c.hz) == k
    assert not np.any(c.hx @ c.hz.T % 2)
    assert not np.any(c.hz @ c.lx.T % 2)
    assert not np.any(c.hx @ c.lz.T % 2)
    assert np.array_equal(c.lx @ c.lz.T % 2, np.eye(k))
    assert c.hx.sum(axis=1).max() == c.hz.sum(axis=1).max() == 6
    assert np.all(c.hx.sum(axis=0)) and np.all(c.hz.sum(axis=0))


@pytest.mark.parametrize("args", [(True, 3), (3, False), (2, 3), (3, 0), (3.5, 4)])
def test_tile_invalid_dimensions(args):
    with pytest.raises(ValueError):
        make_tile_code(*args)


def test_unknown_tile_is_not_silently_substituted():
    with pytest.raises(ValueError, match="preset"):
        make_tile_code(6, 6, preset="unknown")


def test_minimal_tile_pruning_and_full_finite_logical_quotient():
    c = make_tile_code(3, 3)
    assert c.n == 13 and len(c.lx) == 3
    states = np.asarray(list(itertools.product((0, 1), repeat=c.n)), dtype=np.uint8)
    for check, stabilizer, logical in [(c.hz, c.hx, c.lz), (c.hx, c.hz, c.lx)]:
        zero_syndrome = states[~np.any(states @ check.T % 2, axis=1)]
        labels = zero_syndrome @ logical.T % 2
        _, counts = np.unique(labels, axis=0, return_counts=True)
        assert len(counts) == 8
        assert np.all(counts == 2**gf2_rank(stabilizer))
        assert zero_syndrome[np.any(labels, axis=1)].sum(axis=1).min() == 2


@pytest.mark.parametrize("d", [2, 3, 4])
def test_surface_limit_layout_has_known_distance(d):
    hx, hz = _tile_checks(d, d, 2, ((0, 0), (1, 0)), ((0, 0), (0, 1)))
    n = hx.shape[1]
    assert n == d*d + (d-1)*(d-1)
    assert n - gf2_rank(hx) - gf2_rank(hz) == 1
    assert not np.any(hx @ hz.T % 2)
    # Distance via independent row-space membership, rather than factory logicals.
    for check, stabilizer in [(hx, hz), (hz, hx)]:
        rank = gf2_rank(stabilizer)
        found = False
        for w in range(1, d+1):
            for support in itertools.combinations(range(n), w):
                e = np.zeros(n, dtype=np.uint8)
                e[list(support)] = 1
                if not np.any(check @ e % 2) and gf2_rank(np.vstack((stabilizer, e))) > rank:
                    assert w == d
                    found = True
                    break
            if found:
                break
        assert found


def test_tile_boundary_rows_follow_independent_polynomial_evaluation():
    c = make_tile_code(6, 7)
    # A bulk X check, direct polynomial evaluation on the two edge layers.
    row = np.zeros(84, dtype=np.uint8)
    for x, y in [(2, 1), (3, 1), (1, 3)]:
        row[y*6+x] = 1
    for x, y in [(1, 1), (3, 2), (3, 3)]:
        row[42+y*6+x] = 1
    assert any(np.array_equal(row, r) for r in c.hx)
    assert np.any(c.hx.sum(axis=1) < 6)
    assert np.any(c.hz.sum(axis=1) < 6)


@pytest.mark.parametrize("sector", ["X", "Z"])
def test_tile_bposd_corrects_single_qubit_errors(sector):
    pytest.importorskip("ldpc")
    c = make_tile_code(6, 6)
    dec = bposd_decoder(c, .03, errors=sector, osd_order=2)
    h, logical = (c.hz, c.lz) if sector == "X" else (c.hx, c.lx)
    for e in np.eye(c.n, dtype=np.uint8):
        assert np.array_equal(dec.predict(h @ e % 2), logical @ e % 2)
    with pytest.raises(ValueError, match="degree"):
        mwpm_decoder(c, errors=sector)
