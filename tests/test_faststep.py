"""Finite-state checks for the dedicated conditional MH step."""
import itertools
import math

import numpy as np
import pytest

from mcmc4qec import (BinaryLinearModel, CallableDecoder, CallableFailure,
    CSSCode, DepolarizingModel, DepolarizingNoise, IndependentBitFlip,
    PhenomenologicalModel, PhenomenologicalNoise, Problem, KernelConfig,
    SamplingConfig, sample_faulty)
from mcmc4qec.faststep import make_faststep
from mcmc4qec.kernels import OBF, Zanella, ClusterExchange, _neighbors
from mcmc4qec.kernels import StabilizerFlip
from mcmc4qec.decode_cache import CachedDecoder, FailureEvaluator


def case(kind):
    code = CSSCode([[0, 0]], [[1, 1]], [[1, 1]], [[1, 0]])
    if kind == "bit":
        model, noise, p = code.bit_flip_model(), IndependentBitFlip(2, scales=[1, 2]), .2
    elif kind == "pauli":
        model, noise, p = DepolarizingModel(code), DepolarizingNoise(2), .2
    else:
        model = PhenomenologicalModel(code, 1, initial_boundary="clean",
            final_boundary="noisy", representation="difference")
        noise, p = PhenomenologicalNoise(model), {"data": .2, "measurement": .3}
    shape = model.observables(np.zeros(model.n, dtype=np.uint8)).shape
    decoder = CallableDecoder(lambda s: np.zeros(shape, dtype=np.uint8), identifier="zero")
    return Problem(model, noise, decoder), p


@pytest.mark.parametrize("kind", ["bit", "pauli", "phenom"])
def test_z_distribution_and_mh_probability_for_every_neighbor(kind):
    problem, p = case(kind)
    stepper = make_faststep(problem, p)
    reference = Zanella(use_fastpath=False)
    assert stepper is not None
    for labels in itertools.product(*(range(a) for a in problem.alphabets)):
        state = np.array(labels, dtype=np.uint8)
        stepper.start(state)
        q = stepper._distribution(state)
        qr = reference._distribution(state, problem, p)
        assert np.allclose(q, qr, atol=1e-14)
        assert q.sum() == pytest.approx(1)
        for index, neighbor in enumerate(_neighbors(state, problem.alphabets)):
            forward = reference.probability(state, neighbor, problem, p)
            backward = reference.probability(neighbor, state, problem, p)
            delta = problem.log_prob(neighbor, p) - problem.log_prob(state, p)
            reverse = stepper._distribution(neighbor)
            changed = int(np.flatnonzero(state != neighbor)[0])
            reverse_index = int(stepper.offsets[changed]) + int(state[changed]) - int(state[changed] > neighbor[changed])
            fast_forward = float(q[index])
            fast_backward = float(reverse[reverse_index])
            assert fast_forward == pytest.approx(forward, abs=1e-14)
            assert fast_backward == pytest.approx(backward, abs=1e-14)
            fast_alpha = min(1, math.exp(delta) * fast_backward / fast_forward)
            ref_alpha = min(1, math.exp(delta) * backward / forward)
            assert fast_alpha == pytest.approx(ref_alpha)
        for seed in range(6):
            left, right = np.random.default_rng(seed), np.random.default_rng(seed)
            candidate, ratio = stepper.propose(state, Zanella(), left)
            proposal = Zanella(use_fastpath=False).propose(state, problem, p, right)
            assert np.array_equal(candidate, proposal.state)
            assert ratio == pytest.approx(proposal.log_reverse_forward, abs=1e-13)
            assert left.random() == right.random()


@pytest.mark.parametrize("kind,initial", [
    ("bit", [1, 0]), ("pauli", [1, 0]), ("phenom", [1, 0, 0])])
@pytest.mark.parametrize("weights", [(0, 1, 0), (.2, .5, .3)])
def test_same_seed_full_result(kind, initial, weights, monkeypatch):
    problem, p = case(kind)
    original_rng = np.random.default_rng
    class TracedRng:
        def __init__(self, generator, trace):
            self.generator, self.trace = generator, trace
        def random(self, *args, **kwargs):
            value = self.generator.random(*args, **kwargs)
            self.trace.append(("random", np.asarray(value).tolist()))
            return value
        def integers(self, *args, **kwargs):
            value = self.generator.integers(*args, **kwargs)
            self.trace.append(("integers", np.asarray(value).tolist()))
            return value
        def choice(self, *args, **kwargs):
            value = self.generator.choice(*args, **kwargs)
            self.trace.append(("choice", np.asarray(value).tolist()))
            return value
    def run(enabled):
        trace = []
        with monkeypatch.context() as patch:
            patch.setattr(np.random, "default_rng", lambda seed: TracedRng(original_rng(seed), trace))
            result = sample_faulty(problem, p, initial_state=initial, seed=912,
                config=SamplingConfig(samples=120, burn_in=12, kernels=KernelConfig(
                    single=weights[0], zanella=weights[1], cluster=weights[2],
                    cluster_k=1, lazy=.1, zanella_fastpath=enabled)))
        return result, trace
    (fast, fast_trace), (reference, reference_trace) = run(True), run(False)
    assert np.array_equal(fast.states, reference.states)
    assert fast.acceptance == reference.acceptance
    assert fast_trace == reference_trace
    assert fast.metadata["rng"] == reference.metadata["rng"]
    assert fast.metadata["model"] == reference.metadata["model"]
    assert fast.metadata["noise"] == reference.metadata["noise"]
    assert fast.metadata["config"]["expanded_move_probabilities"] == reference.metadata["config"]["expanded_move_probabilities"]


def test_exact_type_gate_and_custom_failure_fallback():
    problem, p = case("bit")
    assert make_faststep(problem, p) is not None
    assert make_faststep(problem, p, enabled=False) is None
    problem.failure = CallableFailure(lambda state, predicted, truth: bool(state[0]), identifier="custom")
    assert make_faststep(problem, p) is None
    def run(enabled):
        return sample_faulty(problem, p, initial_state=[1, 0], seed=75,
            config=SamplingConfig(samples=12, burn_in=2, kernels=KernelConfig(
                zanella=1, cluster=0, lazy=.05, zanella_fastpath=enabled)))
    fast, reference = run(True), run(False)
    assert np.array_equal(fast.states, reference.states)
    assert fast.acceptance == reference.acceptance
    problem.failure = None
    class SpecialNoise(IndependentBitFlip):
        pass
    problem.noise = SpecialNoise(2)
    assert make_faststep(problem, p) is None
    problem, p = case("bit")
    problem.model = BinaryLinearModel([[1, 1]], [[1, 0]])
    assert make_faststep(problem, p) is not None
    class SpecialModel(BinaryLinearModel):
        pass
    problem.model = SpecialModel([[1, 1]], [[1, 0]])
    assert make_faststep(problem, p) is None


def test_support_boundaries_and_rng_for_other_kernels():
    problem, _ = case("bit")
    for p, state in [(0, [0, 0]), (1, [1, 1])]:
        problem.noise = IndependentBitFlip(2)
        stepper = make_faststep(problem, p)
        state = np.array(state, dtype=np.uint8)
        assert stepper._distribution(state) is None
        for kernel in (OBF(), ClusterExchange(1)):
            left, right = np.random.default_rng(54), np.random.default_rng(54)
            candidate, ratio = stepper.propose(state, kernel, left)
            expected = kernel.propose(state, problem, p, right)
            assert np.array_equal(candidate, expected.state)
            assert ratio == expected.log_reverse_forward
            assert left.random() == right.random()


def reference_attempt(state, current_log, syndrome, kernel, problem, p, rng):
    evaluator = FailureEvaluator(problem)
    stats = dict(accepted=0, moved=0)
    proposal = kernel.propose(state, problem, p, rng)
    candidate = problem.state(proposal.state)
    lp = problem.log_prob(candidate, p)
    if math.isfinite(lp):
        faulty, candidate_syndrome = evaluator.evaluate(candidate, previous=state,
            previous_syndrome=syndrome)
    else:
        faulty = False
    if faulty:
        u = rng.random()
        if (math.log(u) if u else -np.inf) < min(0, lp-current_log+proposal.log_reverse_forward):
            stats["accepted"] = 1
            stats["moved"] = int(not np.array_equal(state, candidate))
            return candidate, lp, candidate_syndrome, stats
    return state, current_log, syndrome, stats


@pytest.mark.parametrize("kind", ["bit", "pauli", "phenom"])
def test_actual_attempt_matches_reference_on_every_faulty_state(kind):
    problem, p = case(kind)
    problem.decoder = CachedDecoder(problem.decoder)
    kernels = (OBF(), Zanella(use_fastpath=False), ClusterExchange(1), StabilizerFlip())
    for labels in itertools.product(*(range(a) for a in problem.alphabets)):
        state = np.array(labels, dtype=np.uint8)
        if not problem.is_faulty(state):
            continue
        for kernel in kernels:
            stepper = make_faststep(problem, p)
            if kernel.name == "stabilizer":
                if kind != "bit":
                    continue
                stepper.stabilizers = kernel._rows(problem)
            for seed in range(4):
                left, right = np.random.default_rng(seed), np.random.default_rng(seed)
                stepper.start(state)
                syndrome = problem.model.syndrome(state)
                current_log = problem.log_prob(state, p)
                stats = dict(accepted=0, moved=0)
                actual = stepper.attempt(state, current_log, syndrome, kernel,
                    left, stats)
                expected = reference_attempt(state, current_log, syndrome,
                    kernel, problem, p, right)
                assert np.array_equal(actual[0], expected[0])
                assert actual[1] == pytest.approx(expected[1], abs=1e-13)
                assert np.array_equal(actual[2], expected[2])
                assert stats == expected[3]
                assert left.bit_generator.state == right.bit_generator.state


def test_phenomenological_depolarizing_two_round_history_trajectory():
    code = CSSCode([[0, 0]], [[1, 1]], [[1, 1]], [[1, 0]])
    model = PhenomenologicalModel(code, 2, initial_boundary="clean",
        final_boundary="noisy", representation="history", data_noise="depolarizing")
    problem = Problem(model, PhenomenologicalNoise(model), CallableDecoder(
        lambda s: np.zeros(2, dtype=np.uint8), identifier="zero"))
    p = {"data": .2, "measurement": .3}
    initial = np.zeros(model.n, dtype=np.uint8)
    initial[0] = 1
    def run(enabled):
        return sample_faulty(problem, p, initial_state=initial, seed=735,
            config=SamplingConfig(samples=40, burn_in=5, kernels=KernelConfig(
                zanella=1, cluster=0, lazy=.05, zanella_fastpath=enabled)))
    fast, reference = run(True), run(False)
    assert np.array_equal(fast.states, reference.states)
    assert fast.acceptance == reference.acceptance
