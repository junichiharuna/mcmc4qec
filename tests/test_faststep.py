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
from mcmc4qec.adapters import DecoderAdapter


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

    class ForcedChoice:
        def __init__(self, index):
            self.index = index

        def choice(self, count, *, p):
            assert count == len(p)
            assert p.sum() == pytest.approx(1)
            return self.index

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
            forced_candidate, forced_ratio = stepper.propose(
                state, Zanella(), ForcedChoice(index))
            assert np.array_equal(forced_candidate, neighbor)
            assert forced_ratio == pytest.approx(math.log(backward) - math.log(forward),
                                                 abs=1e-13)
            forward_flux = math.exp(problem.log_prob(state, p)) * fast_forward * fast_alpha
            reverse_alpha = min(1, math.exp(-delta) * fast_forward / fast_backward)
            reverse_flux = math.exp(problem.log_prob(neighbor, p)) * fast_backward * reverse_alpha
            assert forward_flux == pytest.approx(reverse_flux, abs=1e-14)
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


def test_toric_d3_seeded_trajectory_and_rng_calls(monkeypatch):
    pytest.importorskip("pymatching")
    from mcmc4qec.codes import make_toric_code
    from mcmc4qec.decoders import mwpm_decoder

    code = make_toric_code(3)
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n),
                      mwpm_decoder(code))
    original_rng = np.random.default_rng

    class TracedRng:
        def __init__(self, generator, trace):
            self.generator, self.trace = generator, trace

        @staticmethod
        def value(arg):
            if isinstance(arg, np.ndarray):
                return (arg.shape, arg.dtype.str, arg.tobytes())
            return (type(arg).__name__, repr(arg))

        def record(self, method, value, args, kwargs):
            self.trace.append((method, self.value(value),
                               tuple(self.value(arg) for arg in args),
                               tuple((key, self.value(arg)) for key, arg in sorted(kwargs.items()))))

        def random(self, *args, **kwargs):
            value = self.generator.random(*args, **kwargs)
            self.record("random", value, args, kwargs)
            return value

        def integers(self, *args, **kwargs):
            value = self.generator.integers(*args, **kwargs)
            self.record("integers", value, args, kwargs)
            return value

        def choice(self, *args, **kwargs):
            value = self.generator.choice(*args, **kwargs)
            self.record("choice", value, args, kwargs)
            return value

    def run(enabled, samples=24):
        trace = []
        with monkeypatch.context() as patch:
            patch.setattr(np.random, "default_rng",
                          lambda seed: TracedRng(original_rng(seed), trace))
            result = sample_faulty(problem, .1, initial_state=code.lx[0], seed=3201,
                config=SamplingConfig(samples=samples, burn_in=0, kernels=KernelConfig(
                    zanella=.7, cluster=.3, cluster_k=2, lazy=.05,
                    zanella_fastpath=enabled)))
        return result, trace

    def assert_trace_equal(left, right):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            assert a[:3] == b[:3]
            assert len(a[3]) == len(b[3])
            for (name_a, value_a), (name_b, value_b) in zip(a[3], b[3]):
                assert name_a == name_b
                if name_a == "p":
                    assert value_a[:2] == value_b[:2]
                    pa = np.frombuffer(value_a[2], dtype=np.dtype(value_a[1]))
                    pb = np.frombuffer(value_b[2], dtype=np.dtype(value_b[1]))
                    assert np.allclose(pa, pb, rtol=0, atol=1e-14)
                else:
                    assert value_a == value_b

    fast, fast_trace = run(True)
    reference, reference_trace = run(False)
    assert np.array_equal(fast.states, reference.states)
    assert fast.acceptance == reference.acceptance
    assert_trace_equal(fast_trace, reference_trace)
    # Prefix runs expose each transition's kernel, lazy event and acceptance.
    previous_fast = previous_reference = None
    for length in range(1, 25):
        fast_prefix, fast_calls = run(True, length)
        reference_prefix, reference_calls = run(False, length)
        assert np.array_equal(fast_prefix.states, reference_prefix.states)
        assert_trace_equal(fast_calls, reference_calls)
        if previous_fast is not None:
            def delta(result, previous):
                return {name: tuple(result.acceptance[name][field] -
                                    previous.acceptance[name][field]
                                    for field in ("proposed", "accepted", "moved"))
                        for name in result.acceptance}
            assert delta(fast_prefix, previous_fast) == delta(reference_prefix, previous_reference)
        previous_fast, previous_reference = fast_prefix, reference_prefix


def test_faststep_cache_hit_still_checks_prediction_shape():
    problem, p = case("bit")
    decoder = CachedDecoder(problem.decoder)
    problem.decoder = decoder
    stepper = make_faststep(problem, p)
    state = np.array([1, 0], dtype=np.uint8)
    stepper.start(state)
    syndrome = problem.model.syndrome(state)
    decoder.predict(syndrome)
    key = next(iter(decoder.lookup))
    decoder.lookup[key] = np.zeros(2, dtype=np.uint8)
    with pytest.raises(ValueError, match="dimensions differ"):
        stepper.attempt(state, problem.log_prob(state, p), syndrome,
                        ClusterExchange(2), np.random.default_rng(19),
                        {"accepted": 0, "moved": 0})


def test_cached_decoder_copy_and_miss_validation():
    problem, _ = case("bit")
    cache = CachedDecoder(problem.decoder)
    syndrome = np.zeros(1, dtype=np.uint8)
    first = cache.predict(syndrome)
    first[:] = 1
    assert np.array_equal(cache.predict(syndrome), np.zeros(1, dtype=np.uint8))
    class RawDecoder:
        def __init__(self, output):
            self.output = output

        def predict(self, syndrome):
            return self.output

        def metadata(self):
            return {"identifier": "raw"}

    problem.decoder = RawDecoder([2])
    with pytest.raises(ValueError, match="binary"):
        CachedDecoder(problem.decoder).predict(syndrome)
    problem.decoder = RawDecoder([[0]])
    with pytest.raises(ValueError, match="dimension"):
        CachedDecoder(problem.decoder).predict(syndrome)

    class RawEngine:
        def decode(self, syndrome):
            return [2]

    adapter = DecoderAdapter(RawEngine(), output_kind="observable", identifier="bad")
    with pytest.raises(ValueError, match="binary"):
        CachedDecoder(adapter).predict(syndrome)


def test_at_most_one_distribution_normalization_per_step():
    problem, p = case("bit")
    state = np.array([1, 0], dtype=np.uint8)
    for kernel in (OBF(), Zanella(), ClusterExchange(1), StabilizerFlip()):
        stepper = make_faststep(problem, p)
        if kernel.name == "stabilizer":
            stepper.stabilizers = kernel._rows(problem)
        calls = []
        original = stepper._normalize

        def traced(logs):
            calls.append(1)
            return original(logs)

        stepper._normalize = traced
        stepper.start(state)
        assert len(calls) == 1
        current = state.copy()
        current_log = problem.log_prob(current, p)
        syndrome = problem.model.syndrome(current)
        for seed in range(12):
            before = len(calls)
            current, current_log, syndrome = stepper.attempt(
                current, current_log, syndrome, kernel,
                np.random.default_rng(seed), {"accepted": 0, "moved": 0})
            assert len(calls) - before <= 1


@pytest.mark.parametrize("distance", [3, 5, 7])
@pytest.mark.parametrize("p", [.01, .22])
def test_toric_larger_seeded_trajectories(distance, p):
    pytest.importorskip("pymatching")
    from mcmc4qec.codes import make_toric_code
    from mcmc4qec.decoders import mwpm_decoder

    code = make_toric_code(distance)
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n),
                      mwpm_decoder(code))
    results = [sample_faulty(problem, p, initial_state=code.lx[0], seed=731,
        config=SamplingConfig(samples=100, burn_in=5, chains=2,
            kernels=KernelConfig(zanella=.7, cluster=.3, cluster_k=2,
                                 lazy=.05, zanella_fastpath=enabled)))
        for enabled in (False, True)]
    assert np.array_equal(results[0].states, results[1].states)
    assert results[0].acceptance == results[1].acceptance


def test_supported_boundary_attempts_preserve_rng():
    problem, _ = case("bit")
    problem.noise = IndependentBitFlip(2, scales=[1, 0])
    state = np.array([1, 0], dtype=np.uint8)
    for p in (.2, 1):
        for kernel in (OBF(), Zanella(use_fastpath=False), ClusterExchange(1)):
            for seed in range(10):
                stepper = make_faststep(problem, p)
                stepper.start(state)
                left, right = np.random.default_rng(seed), np.random.default_rng(seed)
                lp = problem.log_prob(state, p)
                syndrome = problem.model.syndrome(state)
                stats = {"accepted": 0, "moved": 0}
                actual = stepper.attempt(state, lp, syndrome, kernel, left, stats)
                expected = reference_attempt(state, lp, syndrome, kernel, problem, p, right)
                assert np.array_equal(actual[0], expected[0])
                assert actual[1] == expected[1]
                assert np.array_equal(actual[2], expected[2])
                assert stats == expected[3]
                assert left.bit_generator.state == right.bit_generator.state
