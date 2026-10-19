"""Small independent numerical checks of the public proposal/MH contracts."""

import itertools
import math

import numpy as np
import pytest

from mcmc4qec import (
    BinaryLinearModel, CallableDecoder, CallableFailure, IndependentBitFlip,
    KernelConfig, Problem, SamplingConfig, direct_mc, exact, sample_faulty,
)
from mcmc4qec.kernels import OBF, Zanella, ClusterExchange, StabilizerFlip


ALL_STATES = np.asarray(list(itertools.product((0, 1), repeat=4)), dtype=np.uint8)


class CorrelatedNoise:
    """Normalized four-bit table, deliberately not a function of weight alone."""

    n = 4

    def probabilities(self, p):
        if not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError("p must be in [0, 1]")
        # The nonzero field keeps every table entry supported at the endpoints.
        field = 2 * p - 1
        interaction = 1.3 * (ALL_STATES[:, 0] == ALL_STATES[:, 1])
        interaction += .7 * (ALL_STATES[:, 1] != ALL_STATES[:, 2])
        interaction += .4 * ALL_STATES[:, 3]
        mass = np.exp(field * ALL_STATES.sum(axis=1) + interaction)
        return mass / mass.sum()

    def sample(self, p, rng):
        return ALL_STATES[rng.choice(len(ALL_STATES), p=self.probabilities(p))].copy()

    def log_prob(self, state, p):
        index = int(np.dot(np.asarray(state), [8, 4, 2, 1]))
        return float(np.log(self.probabilities(p)[index]))

    def metadata(self):
        return {"type": "CorrelatedNoise", "identifier": "four-bit-table-v1", "n": self.n}


def table_problem(failure=None):
    model = BinaryLinearModel([[1, 0, 1, 0]], [[1, 0, 0, 0]],
                              stabilizers=[[0, 1, 0, 1]], identifier="four-bit-test")
    decoder = CallableDecoder(lambda syndrome: [0], identifier="constant-zero")
    return Problem(model, CorrelatedNoise(), decoder, failure=failure)


@pytest.mark.parametrize("kernel", [OBF(), Zanella(), ClusterExchange(1),
                                     ClusterExchange(2), StabilizerFlip()])
def test_actual_proposal_frequencies_and_reported_hastings_ratio(kernel):
    problem = table_problem()
    state = np.array([1, 1, 0, 0], dtype=np.uint8)
    p = .2
    expected = np.array([kernel.probability(state, candidate, problem, p)
                         for candidate in ALL_STATES])
    assert expected.sum() == pytest.approx(1)
    rng = np.random.default_rng(602)
    counts = np.zeros(16, dtype=int)
    for _ in range(1200):
        proposal = kernel.propose(state, problem, p, rng)
        candidate = proposal.state
        index = int(np.dot(candidate, [8, 4, 2, 1]))
        counts[index] += 1
        forward = expected[index]
        reverse = kernel.probability(candidate, state, problem, p)
        assert forward > 0 and reverse > 0
        assert proposal.log_reverse_forward == pytest.approx(math.log(reverse / forward))
        assert np.array_equal(state, [1, 1, 0, 0]), "propose must not mutate its input"
    # More than five binomial standard deviations at the worst-case q=.5.
    assert np.max(np.abs(counts / counts.sum() - expected)) < .075


def test_same_custom_failure_for_exact_direct_mc_and_correlated_mcmc():
    failure = CallableFailure(lambda state, predicted, truth: state[1] == 1,
                              identifier="second-bit-only")
    problem = table_problem(failure)
    p = .3
    probabilities = problem.noise.probabilities(p)
    keep = ALL_STATES[:, 1] == 1
    failure_probability = float(probabilities[keep].sum())
    conditional = probabilities * keep / failure_probability
    exact_result = exact(problem, p)
    assert exact_result.estimate == pytest.approx(failure_probability)
    assert exact_result.conditional_weight == pytest.approx(
        float(np.dot(conditional, ALL_STATES.sum(axis=1))))
    mc = direct_mc(problem, p, trials=6000, seed=491)
    assert mc.estimate == pytest.approx(failure_probability, abs=.03)
    config = SamplingConfig(samples=5000, burn_in=100, kernels=KernelConfig(
        single=.25, zanella=.5, cluster=.25, cluster_k=1, lazy=.1))
    sampled = sample_faulty(problem, p, config=config, initial_state=[0, 1, 0, 0], seed=812)
    flat = sampled.states.reshape(-1, 4)
    assert np.all(flat[:, 1] == 1)
    indices = flat @ np.array([8, 4, 2, 1])
    empirical = np.bincount(indices, minlength=16) / len(indices)
    # Check the entire table, so a weight-only MH shortcut cannot pass.
    assert np.max(np.abs(empirical - conditional)) < .05


def test_rejected_single_flips_remain_in_recorded_trace():
    model = BinaryLinearModel(np.zeros((0, 4), dtype=int), [[1, 0, 0, 0]])
    problem = Problem(model, IndependentBitFlip(4),
                      CallableDecoder(lambda syndrome: [0], identifier="zero"),
                      failure=CallableFailure(lambda state, predicted, truth: state.sum() == 2,
                                              identifier="exact-weight-two"))
    config = SamplingConfig(samples=17, burn_in=4, thin=3, chains=2, kernels=KernelConfig(
        single=1, zanella=0, cluster=0, lazy=0))
    result = sample_faulty(problem, .1, config=config, initial_state=[1, 0, 1, 0], seed=11)
    assert result.states.shape == (2, 17, 4)
    assert np.all(result.states == [1, 0, 1, 0])
    assert result.acceptance["single"]["accepted"] == 0


def test_cluster_uses_density_ratio_for_equal_weight_correlated_states():
    problem = table_problem(CallableFailure(
        lambda state, predicted, truth: state.sum() == 2, identifier="weight-two"))
    probabilities = problem.noise.probabilities(.3)
    probabilities[ALL_STATES.sum(axis=1) != 2] = 0
    expected = probabilities / probabilities.sum()
    config = SamplingConfig(samples=4000, burn_in=100, kernels=KernelConfig(
        single=0, zanella=0, cluster=1, cluster_k=1, lazy=.1))
    result = sample_faulty(problem, .3, config=config, initial_state=[1, 1, 0, 0], seed=735)
    flat = result.states.reshape(-1, 4)
    assert np.all(flat.sum(axis=1) == 2)
    indices = flat @ np.array([8, 4, 2, 1])
    observed = np.bincount(indices, minlength=16) / len(indices)
    assert np.max(np.abs(observed - expected)) < .04


@pytest.mark.parametrize("state", [[1, 0], [1, 0, 0, 2], [1, 0, 0, float("nan")]])
def test_initial_state_rejects_wrong_size_and_nonbinary_values(state):
    with pytest.raises(ValueError):
        sample_faulty(table_problem(), .3, initial_state=state,
                      config=SamplingConfig(samples=2, burn_in=0), seed=5)
