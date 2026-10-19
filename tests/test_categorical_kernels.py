"""Enumerated and empirical checks on Pauli and mixed-alphabet proposals."""
import itertools
import math

import numpy as np
import pytest

from mcmc4qec import CallableDecoder, CallableFailure, Problem
from mcmc4qec.kernels import OBF, Zanella, ClusterExchange, StabilizerFlip


class CategoryModel:
    def __init__(self, alphabets):
        self.alphabets = tuple(alphabets)
        self.n = len(alphabets)

    def validate_state(self, state):
        state = np.asarray(state)
        if (state.shape != (self.n,) or not np.all(np.isfinite(state))
                or np.any(state != np.floor(state)) or np.any(state < 0)
                or np.any(state >= self.alphabets)):
            raise ValueError("invalid categorical state")
        return state.astype(np.uint8, copy=True)

    def syndrome(self, state):
        return np.zeros(0, dtype=np.uint8)

    def observables(self, state):
        return np.array([state[0] != 0], dtype=np.uint8)

    def metadata(self):
        return {"identifier": "categorical-kernel-test", "alphabets": self.alphabets}


class TableNoise:
    def __init__(self, alphabets):
        self.n = len(alphabets)
        self.states = np.asarray(list(itertools.product(*(range(a) for a in alphabets))), dtype=np.uint8)
        energy = .2 * (self.states @ np.arange(1, self.n+1))
        energy += .8 * (self.states[:, 0] == self.states[:, 1])
        self.probabilities = np.exp(energy)
        self.probabilities /= self.probabilities.sum()
        self.index = {tuple(state): i for i, state in enumerate(self.states)}

    def sample(self, p, rng):
        return self.states[rng.choice(len(self.states), p=self.probabilities)].copy()

    def log_prob(self, state, p):
        return float(np.log(self.probabilities[self.index[tuple(state)]]))

    def metadata(self):
        return {"identifier": "correlated-category-table"}


def categorical_problem(alphabets):
    return Problem(CategoryModel(alphabets), TableNoise(alphabets),
                   CallableDecoder(lambda syndrome: [0], identifier="zero"),
                   failure=CallableFailure(lambda s, pred, truth: True, identifier="all"))


@pytest.mark.parametrize("alphabets,kernel", [
    ((4, 4), OBF()), ((4, 4), Zanella()),
    ((4, 4), ClusterExchange(1)), ((4, 4, 4), ClusterExchange(2)),
    ((4, 4, 2), OBF()), ((4, 4, 2), Zanella()),
    ((4, 4, 2, 2), ClusterExchange(1)),
])
def test_complete_proposal_matrix_and_mh_detailed_balance(alphabets, kernel):
    problem = categorical_problem(alphabets)
    states = problem.noise.states
    q = np.array([[kernel.probability(x, y, problem, .2) for y in states] for x in states])
    assert np.all(q >= 0)
    assert np.allclose(q.sum(axis=1), 1)
    pi = problem.noise.probabilities
    if isinstance(kernel, Zanella):
        # Independently enumerate square-root target weighting on neighbors.
        adjacency = np.count_nonzero(states[:, None, :] != states[None, :, :], axis=2) == 1
        expected = adjacency * np.sqrt(pi)[None, :]
        expected /= expected.sum(axis=1)[:, None]
        assert np.allclose(q, expected)
    else:
        assert np.allclose(q, q.T)
    accepted_flux = np.minimum(pi[:, None] * q, pi[None, :] * q.T)
    np.fill_diagonal(accepted_flux, 0)
    transition = accepted_flux / pi[:, None]
    np.fill_diagonal(transition, 1-transition.sum(axis=1))
    assert np.allclose(pi @ transition, pi)
    assert np.allclose(pi[:, None] * transition, (pi[:, None] * transition).T)


@pytest.mark.parametrize("alphabets,state,kernel", [
    ((4, 4), [1, 2], OBF()),
    ((4, 4), [1, 2], Zanella()),
    ((4, 4, 2), [1, 0, 1], OBF()),
    ((4, 4, 2), [1, 0, 1], Zanella()),
    ((4, 4, 4), [1, 2, 0], ClusterExchange(2)),
    ((4, 4, 4), [1, 2, 3], ClusterExchange(2)),
    ((4, 4, 2, 2), [1, 0, 1, 0], ClusterExchange(1)),
])
def test_draws_match_probabilities_including_duplicate_relabel_paths(alphabets, state, kernel):
    problem = categorical_problem(alphabets)
    states = problem.noise.states
    expected = np.array([kernel.probability(state, y, problem, .2) for y in states])
    rng = np.random.default_rng(915)
    counts = np.zeros(len(states), dtype=int)
    for _ in range(1200):
        proposal = kernel.propose(state, problem, .2, rng)
        index = problem.noise.index[tuple(proposal.state)]
        counts[index] += 1
        qr = kernel.probability(proposal.state, state, problem, .2)
        assert proposal.log_reverse_forward == pytest.approx(math.log(qr / expected[index]))
    assert np.max(np.abs(counts / counts.sum() - expected)) < .075


def test_cluster_relabel_probability_sums_duplicate_paths_and_unavailable_moves():
    problem = categorical_problem((4, 4, 4))
    kernel = ClusterExchange(2)
    # No two empty positions: half the mass is a relocation self-loop.
    assert kernel.probability([1, 2, 0], [1, 2, 0], problem, .2) == pytest.approx(.5 + .5/9)
    # Two of three selected subsets contain the one changed coordinate.
    assert kernel.probability([1, 2, 3], [2, 2, 3], problem, .2) == pytest.approx(.5 * 2/27)
    assert kernel.probability([0, 0, 0], [0, 0, 0], problem, .2) == 1


def test_cluster_k1_reaches_fixed_group_occupancy_component():
    problem = categorical_problem((4, 4, 2, 2))
    states = problem.noise.states
    component = [tuple(s) for s in states if np.count_nonzero(s[:2]) == 1
                 and np.count_nonzero(s[2:]) == 1]
    kernel = ClusterExchange(1)
    seen, pending = {component[0]}, [component[0]]
    while pending:
        x = pending.pop()
        for y in component:
            if y not in seen and kernel.probability(x, y, problem, .2) > 0:
                seen.add(y)
                pending.append(y)
    assert seen == set(component)


def test_pauli_stabilizer_xor_probabilities_include_repeated_rows():
    problem = categorical_problem((4, 4))
    problem.model.stabilizers = np.array([[1, 0], [1, 0], [0, 3]], dtype=np.uint8)
    kernel = StabilizerFlip()
    assert kernel.probability([3, 1], [2, 1], problem, .2) == pytest.approx(2/3)
    assert kernel.probability([3, 1], [3, 2], problem, .2) == pytest.approx(1/3)
    for x in problem.noise.states:
        assert sum(kernel.probability(x, y, problem, .2) for y in problem.noise.states) == pytest.approx(1)
    rng = np.random.default_rng(55)
    samples = [tuple(kernel.propose([3, 1], problem, .2, rng).state) for _ in range(900)]
    assert samples.count((2, 1)) / len(samples) == pytest.approx(2/3, abs=.06)
    missing = categorical_problem((4, 4))
    with pytest.raises(ValueError, match="static model stabilizers"):
        kernel.propose([1, 0], missing, .2, rng)
