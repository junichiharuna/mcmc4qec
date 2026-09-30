"""Finite-state equivalence checks for the product-noise fast path."""
import itertools
import math

import numpy as np
import pytest

from mcmc4qec import (BinaryLinearModel, CallableDecoder, CallableFailure,
                       CSSCode, DepolarizingModel, DepolarizingNoise,
                       IndependentBitFlip, PhenomenologicalModel,
                       PhenomenologicalNoise, Problem, KernelConfig,
                       SamplingConfig, sample_faulty)
from mcmc4qec.kernels import Zanella, _neighbors, _alphabets
from mcmc4qec.decode_cache import CachedDecoder, FailureEvaluator


def _problem(noise_kind):
    code = CSSCode([[0, 0]], [[1, 1]], [[1, 1]], [[1, 0]])
    if noise_kind == "bit":
        model = code.bit_flip_model()
        noise = IndependentBitFlip(2, scales=[1, 2])
        p = .2
    elif noise_kind == "pauli":
        model = DepolarizingModel(code)
        noise = DepolarizingNoise(2)
        p = .2
    else:
        model = PhenomenologicalModel(code, 1, initial_boundary="clean",
            final_boundary="noisy", representation="difference")
        noise = PhenomenologicalNoise(model)
        p = {"data": .2, "measurement": .3}
    decoder = CallableDecoder(lambda syndrome: np.zeros(model.observables(
        np.zeros(model.n, dtype=np.uint8)).shape, dtype=np.uint8), identifier="zero")
    return Problem(model, noise, decoder,
                   CallableFailure(lambda state, predicted, truth: True,
                                   identifier="all")), p


@pytest.mark.parametrize("kind", ["bit", "pauli", "phenom"])
def test_all_states_all_neighbors_match_reference(kind):
    problem, p = _problem(kind)
    fast, reference = Zanella(), Zanella(use_fastpath=False)
    states = itertools.product(*(range(a) for a in problem.alphabets))
    for state in states:
        state = np.array(state, dtype=np.uint8)
        assert np.allclose(fast._distribution(state, problem, p),
                           reference._distribution(state, problem, p), atol=1e-14)
        for neighbor in _neighbors(state, _alphabets(problem)):
            qf = fast.probability(state, neighbor, problem, p)
            qr = reference.probability(state, neighbor, problem, p)
            assert qf == pytest.approx(qr, abs=1e-14)
            rf = fast.probability(neighbor, state, problem, p)
            rr = reference.probability(neighbor, state, problem, p)
            lf = problem.log_prob(neighbor, p) - problem.log_prob(state, p)
            assert min(1, math.exp(lf) * rf / qf) == pytest.approx(
                min(1, math.exp(lf) * rr / qr), abs=1e-12)


def test_identical_seed_trajectory_and_acceptance():
    problem, p = _problem("bit")
    def run(enabled):
        return sample_faulty(problem, p, initial_state=[1, 0], seed=811,
            config=SamplingConfig(samples=200, burn_in=20, kernels=KernelConfig(
                zanella_fastpath=enabled, lazy=0, cluster=0, zanella=1)))
    fast, reference = run(True), run(False)
    assert np.array_equal(fast.states, reference.states)
    assert fast.acceptance == reference.acceptance


def test_correlated_and_overridden_noise_never_take_fast_path():
    problem, p = _problem("bit")
    class Correlated(IndependentBitFlip):
        def log_prob(self, state, p):
            state = np.asarray(state)
            return super().log_prob(state, p) + (.01 if state[0] == state[1] else -.01)
    problem.noise = Correlated(2)
    assert Zanella()._distribution([1, 0], problem, p) == pytest.approx(
        Zanella(use_fastpath=False)._distribution([1, 0], problem, p))


def test_zero_support_matches_reference():
    problem, _ = _problem("bit")
    problem.noise = IndependentBitFlip(2)
    for p, state in [(0, [0, 0]), (1, [1, 1])]:
        fast = Zanella()._distribution(state, problem, p)
        reference = Zanella(use_fastpath=False)._distribution(state, problem, p)
        assert (fast is None and reference is None) or np.allclose(fast, reference)


def test_cache_cap_policies_and_safe_copies():
    calls = []
    decoder = CallableDecoder(lambda s: calls.append(tuple(s)) or np.array([s[0]], dtype=np.uint8), identifier="count")
    cache = CachedDecoder(decoder, cap=2, policy="research_clear")
    for s in ([0], [1], [0]):
        cache.predict(s)
    assert len(calls) == 2
    cache.boundary()
    cache.predict([1])
    assert len(calls) == 2
    cache.predict([0, 1])
    cache.boundary()
    assert cache.size == 0
    assert len(calls) == 3
    for policy in ("lru", "freeze"):
        cache = CachedDecoder(decoder, cap=1, policy=policy)
        first = cache.predict([0])
        first[0] = 1
        assert cache.predict([0])[0] == 0
        cache.predict([1])
        assert cache.size == 1


def test_incremental_failure_matches_full_evaluation():
    for kind in ("bit", "pauli", "phenom"):
        problem, _ = _problem(kind)
        evaluator = FailureEvaluator(problem)
        for labels in itertools.product(*(range(a) for a in problem.alphabets)):
            state = np.array(labels, dtype=np.uint8)
            syndrome = problem.model.syndrome(state)
            for neighbor in _neighbors(state, problem.alphabets):
                assert np.array_equal(evaluator.syndrome(neighbor, previous=state,
                    previous_syndrome=syndrome), problem.model.syndrome(neighbor))
                assert evaluator.is_faulty(neighbor, previous=state,
                    previous_syndrome=syndrome) == problem.is_faulty(neighbor)
