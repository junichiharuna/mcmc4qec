"""Whole-experiment checks across static Pauli and space-time distributions."""
import itertools
import numpy as np
import pytest

from mcmc4qec import (
    CSSCode, CallableDecoder, DepolarizingModel, DepolarizingNoise,
    PhenomenologicalModel, PhenomenologicalNoise, Problem, Result,
    SamplingConfig, KernelConfig, exact, direct_mc, sample_faulty,
    bennett_log_ratio,
)


def experiment(kind):
    code = CSSCode(np.zeros((0, 2), dtype=int), [[1, 1]], [[1, 1]], [[1, 0]])
    if kind == "static":
        model = DepolarizingModel(code)
        return Problem(model, DepolarizingNoise(code.n),
                       CallableDecoder(lambda s: [int(s[0]), 0], identifier="pauli-test")), .3, .15
    model = PhenomenologicalModel(code, 2, initial_boundary="clean", final_boundary="noisy",
                                 representation="difference", data_noise=kind)
    # Deliberately simple fixed history rule, shared by all estimators.
    decoder = CallableDecoder(lambda s: [int(np.bitwise_xor.reduce(s[:, 0]))] + (
        [0] if kind == "depolarizing" else []), identifier="whole-history-v1")
    return (Problem(model, PhenomenologicalNoise(model), decoder),
            dict(data=.3, measurement=.2), dict(data=.15, measurement=.1))


@pytest.mark.parametrize("kind", ["static", "bit_flip", "depolarizing"])
def test_three_noise_end_to_end_shared_failure_and_categorical_json(kind):
    problem, p, _ = experiment(kind)
    truth = exact(problem, p)
    mc = direct_mc(problem, p, trials=2000, seed=419)
    assert mc.estimate == pytest.approx(truth.estimate, abs=.055)
    sample = sample_faulty(problem, p, seed=23, config=SamplingConfig(
        samples=1800, burn_in=100, kernels=KernelConfig(cluster_k=1)))
    assert np.count_nonzero(sample.states, axis=-1).mean() == pytest.approx(truth.conditional_weight, abs=.13)
    assert all(problem.is_faulty(s) for s in sample.states[0])
    assert np.array_equal(Result.from_json(sample.to_json()).states, sample.states)


@pytest.mark.parametrize("kind", ["static", "bit_flip", "depolarizing"])
def test_bar_full_density_against_exact_normalizers_for_each_noise(kind):
    problem, a, b = experiment(kind)
    all_states = [np.array(s, dtype=np.uint8) for s in itertools.product(*(range(x) for x in problem.alphabets))]
    faulty = [s for s in all_states if problem.is_faulty(s)]
    logs_a = np.array([problem.log_prob(s, a) for s in faulty])
    logs_b = np.array([problem.log_prob(s, b) for s in faulty])
    za, zb = np.exp(logs_a).sum(), np.exp(logs_b).sum()
    # Deterministic quadrature encoded as counts, not a stochastic convergence assertion.
    counts_a = np.maximum(1, np.round(np.exp(logs_a)/za * 200000).astype(int))
    counts_b = np.maximum(1, np.round(np.exp(logs_b)/zb * 200000).astype(int))
    ratio = bennett_log_ratio(np.repeat(logs_b-logs_a, counts_a), np.repeat(logs_b-logs_a, counts_b))
    assert ratio == pytest.approx(np.log(zb/za), abs=.006)
