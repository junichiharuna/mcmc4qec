import itertools
from types import SimpleNamespace

import numpy as np
import pytest

from mcmc4qec.core import CSSCode, CallableDecoder, Problem
from mcmc4qec.noise import IndependentBitFlip
from mcmc4qec.sampling import SamplingConfig, sample_faulty
from mcmc4qec.initial_states import (
    minimum_weight_coset_representative, logical_representatives,
    minimum_weight_initial_state, maximum_weight_initial_state,
    random_logical_sector_initial_state, observable_sector_initial_state,
)


def example_code():
    return CSSCode(
        hx=[[0, 0, 1, 1, 1]],
        hz=[[1, 1, 0, 0, 0]],
        lx=[[1, 1, 1, 1, 1], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0]],
        lz=[[1, 0, 0, 0, 0], [0, 0, 1, 0, 1], [0, 0, 0, 1, 1]],
    )


def test_exact_minimum_for_each_coset_by_enumeration():
    c = example_code()
    reps = logical_representatives(c)
    for logical, rep in zip(c.lx, reps):
        coset = [logical ^ (np.asarray(mask, dtype=np.uint8) @ c.hx % 2)
                 for mask in itertools.product((0, 1), repeat=len(c.hx))]
        assert int(rep.sum()) == min(int(x.sum()) for x in coset)
        assert any(np.array_equal(rep, x) for x in coset)
        assert np.array_equal(c.lz @ logical % 2, c.lz @ rep % 2)
    assert int(reps[0].sum()) == 2 < int(c.lx[0].sum())
    assert int(minimum_weight_initial_state(c).sum()) == 1
    assert int(maximum_weight_initial_state(c).sum()) == 2


def test_random_sector_is_nonzero_and_reproducible():
    c = example_code()
    x = random_logical_sector_initial_state(c, seed=7)
    y = random_logical_sector_initial_state(c, seed=7)
    assert np.array_equal(x, y)
    assert np.any(c.lz @ x % 2)
    assert not np.any(c.hz @ x % 2)


def test_observable_sector_uses_crossing_matrix():
    c = example_code()
    requested = np.array([0, 1, 1], dtype=np.uint8)
    x = observable_sector_initial_state(c, requested)
    assert np.array_equal(c.lz @ x % 2, requested)
    assert not np.any(c.hz @ x % 2)


def test_independent_crossing_matrix_and_sample_faulty_input():
    c = example_code()
    model = c.bit_flip_model()
    problem = Problem(model, IndependentBitFlip(c.n), CallableDecoder(
        lambda syndrome: np.zeros(3, dtype=np.uint8), identifier="zero"))
    starts = np.stack((minimum_weight_initial_state(c), maximum_weight_initial_state(c)))
    result = sample_faulty(problem, .1, config=SamplingConfig(samples=8, burn_in=0, chains=2),
                           seed=4, initial_state=starts)
    assert result.metadata["config"]["initial_states"] == starts.tolist()

    # The crossing matrix need only be invertible, not the identity.
    unpaired = SimpleNamespace(
        lx=np.array([[1, 0], [0, 1]], dtype=np.uint8),
        lz=np.array([[1, 1], [0, 1]], dtype=np.uint8),
        hx=np.zeros((0, 2), dtype=np.uint8), hz=np.zeros((0, 2), dtype=np.uint8))
    x = observable_sector_initial_state(unpaired, [0, 1])
    assert np.array_equal(unpaired.lz @ x % 2, [0, 1])


def test_nonbinary_coset_and_invalid_sector_rejected():
    with pytest.raises(ValueError):
        minimum_weight_coset_representative([2, 0], [[1, 1]])
    with pytest.raises(ValueError):
        logical_representatives(example_code(), sector="both")


def test_exact_milp_branch_for_thirteen_stabilizers():
    rows = np.eye(13, 14, dtype=np.uint8)
    logical = np.ones(14, dtype=np.uint8)
    representative = minimum_weight_coset_representative(logical, rows)
    assert np.array_equal(representative, np.r_[np.zeros(13, dtype=np.uint8), 1])
