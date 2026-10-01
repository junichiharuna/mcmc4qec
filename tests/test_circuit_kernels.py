"""Finite physical-location proposal and sampler acceptance checks."""
import itertools
import math

import numpy as np
import pytest

stim = pytest.importorskip("stim")

from mcmc4qec.circuit import CircuitFaultModel, CircuitFaultNoise, PhysicalFaultProposal
from mcmc4qec.core import CallableDecoder, CallableFailure, Problem
from mcmc4qec.fastpath import _probability_rows
from mcmc4qec.faststep import make_faststep
from mcmc4qec.kernels import OBF, Zanella, _neighbors, _neighbor_at
from mcmc4qec.sampling import KernelConfig, SamplingConfig, sample_faulty
from test_circuit_pipeline import repetition_problem


def _states(problem):
    return [np.asarray(s, dtype=np.uint8) for s in
            itertools.product(*(range(a) for a in problem.alphabets))]


def _flow(problem, p, states, kernel):
    for a in states:
        assert sum(kernel.probability(a, b, problem, p) for b in states) == pytest.approx(1)
        if not problem.is_faulty(a):
            continue
        pi_a = math.exp(problem.log_prob(a, p))
        for b in _neighbors(a, problem.alphabets):
            qab = kernel.probability(a, b, problem, p)
            qba = kernel.probability(b, a, problem, p)
            if not problem.is_faulty(b):
                continue
            pi_b = math.exp(problem.log_prob(b, p))
            alpha_ab = min(1, pi_b * qba / (pi_a * qab))
            alpha_ba = min(1, pi_a * qab / (pi_b * qba))
            lhs = pi_a * qab * alpha_ab
            rhs = pi_b * qba * alpha_ba
            assert lhs == pytest.approx(rhs, abs=1e-14)


def test_repetition_64_state_normalization_and_detailed_balance():
    problem = repetition_problem(1)
    states = _states(problem)
    assert len(states) == 64
    obf, zanella = OBF(), Zanella(use_fastpath=False)
    for kernel in (obf, zanella):
        _flow(problem, .13, states, kernel)


def test_actual_component_mixture_transition_matrix_with_failure_and_lazy():
    problem = repetition_problem(1)
    p, lazy = .13, .05
    states = _states(problem)
    faulty = [i for i, state in enumerate(states) if problem.is_faulty(state)]
    assert len(faulty) == 32
    kernels = ((.25, OBF()), (.50, Zanella(use_fastpath=False)),
               (.25, PhysicalFaultProposal()))
    masses = np.exp([problem.log_prob(state, p) for state in states])
    index_of = {tuple(state): i for i, state in enumerate(states)}
    transition = np.zeros((64, 64))
    for i in faulty:
        a = states[i]
        rejected = 0.0
        proposed = np.zeros(len(kernels))
        for b in _neighbors(a, problem.alphabets):
            j = index_of[tuple(b)]
            for component, (weight, kernel) in enumerate(kernels):
                qab = kernel.probability(a, b, problem, p)
                if qab:
                    proposed[component] += qab
                    qba = kernel.probability(b, a, problem, p)
                    assert qba > 0
                    alpha = (min(1, masses[j] * qba / (masses[i] * qab))
                             if j in faulty else 0)
                    transition[i, j] += (1 - lazy) * weight * qab * alpha
                    rejected += weight * qab * (1 - alpha)
        assert proposed == pytest.approx(np.ones(len(kernels)), abs=1e-14)
        # Compute the diagonal from rejected proposals and lazy explicitly.
        transition[i, i] = lazy + (1 - lazy) * rejected
        assert transition[i, i] >= lazy
        assert transition[i].sum() == pytest.approx(1, abs=1e-14)
    for i in faulty:
        for j in faulty:
            assert masses[i] * transition[i, j] == pytest.approx(
                masses[j] * transition[j, i], abs=1e-14)
    # This finite failure graph is connected and aperiodic; no general claim follows.
    reached = {faulty[0]}
    frontier = [faulty[0]]
    while frontier:
        current = frontier.pop()
        for other in faulty:
            if transition[current, other] > 0 and other not in reached:
                reached.add(other)
                frontier.append(other)
    assert reached == set(faulty)


class FixedChoices:
    def __init__(self, *, integers=(), choices=()):
        self.integer_values = iter(integers)
        self.choice_values = iter(choices)

    def integers(self, low, high=None):
        value = next(self.integer_values)
        assert (0 <= value < low) if high is None else (low <= value < high)
        return value

    def choice(self, size, *, p):
        index = next(self.choice_values)
        assert len(p) == size and p[index] > 0
        return index


class ScriptedChoices(FixedChoices):
    def __init__(self):
        super().__init__(integers=[6, 2, 2, 1, 3], choices=[7])
        self.random_values = iter([.1, .9, .05, .9, .5, 0,
                                   .9, .9, .9, .9, 0])

    def random(self):
        return next(self.random_values)


def test_sampler_uses_selected_kernel_failure_gate_lazy_and_rejection(monkeypatch):
    problem = repetition_problem(1)
    assert make_faststep(problem, .13) is None
    assert problem.is_faulty([0, 0, 1])
    assert problem.is_faulty([0, 0, 2])
    assert problem.is_faulty([0, 3, 2])
    assert not problem.is_faulty([0, 0, 0])
    rng = ScriptedChoices()
    monkeypatch.setattr(np.random, 'default_rng', lambda seed: rng)
    result = sample_faulty(problem, .13, seed=10, initial_state=[0, 0, 1],
        config=SamplingConfig(samples=5, burn_in=0, kernels=KernelConfig(
            single=.3, zanella=.4, circuit_single=.3, cluster=0,
            stabilizer=0, lazy=.2, zanella_fastpath=False)))
    assert result.states[0].tolist() == [
        [0, 0, 1], [0, 0, 1], [0, 0, 2], [0, 0, 2], [0, 3, 2]]
    assert result.acceptance['lazy']['proposed'] == 1
    assert result.acceptance['single']['proposed'] == 1
    assert result.acceptance['single']['accepted'] == 0
    assert result.acceptance['zanella']['proposed'] == 1
    assert result.acceptance['zanella']['moved'] == 1
    assert result.acceptance['physical_fault']['proposed'] == 2
    assert result.acceptance['physical_fault']['moved'] == 1
    with pytest.raises(StopIteration):
        rng.random()


def test_every_proposal_branch_matches_probability_and_ratio():
    problem = repetition_problem(1)
    p = .13
    degree = sum(size - 1 for size in problem.alphabets)
    for state in _states(problem):
        for kernel in (OBF(), Zanella(use_fastpath=False), Zanella()):
            for index in range(degree):
                rng = (FixedChoices(integers=[index]) if isinstance(kernel, OBF)
                       else FixedChoices(choices=[index]))
                proposed = kernel.propose(state, problem, p, rng)
                expected = _neighbor_at(state, problem.alphabets, index)
                assert np.array_equal(proposed.state, expected)
                forward = kernel.probability(state, expected, problem, p)
                reverse = kernel.probability(expected, state, problem, p)
                assert forward > 0 and reverse > 0
                assert proposed.log_reverse_forward == pytest.approx(
                    math.log(reverse / forward), abs=1e-13)
        physical = PhysicalFaultProposal()
        for location, size in enumerate(problem.alphabets):
            for label in range(1, size):
                proposed = physical.propose(state, problem, p,
                    FixedChoices(integers=[location, label]))
                expected = state.copy()
                expected[location] = 0 if state[location] == label else label
                assert np.array_equal(proposed.state, expected)
                forward = physical.probability(state, expected, problem, p)
                reverse = physical.probability(expected, state, problem, p)
                assert proposed.log_reverse_forward == pytest.approx(
                    math.log(reverse / forward), abs=1e-13)


def test_fast_reference_distribution_and_same_seed_trajectory():
    problem = repetition_problem(1)
    p = .13
    fast, reference = Zanella(), Zanella(use_fastpath=False)
    for state in _states(problem):
        assert fast._distribution(state, problem, p) == pytest.approx(
            reference._distribution(state, problem, p), abs=1e-14)
    def run(enabled):
        return sample_faulty(problem, p, seed=901, initial_state=[0, 0, 1],
            config=SamplingConfig(samples=70, burn_in=10, kernels=KernelConfig(
                single=.25, zanella=.5, circuit_single=.25, cluster=0,
                lazy=.05, zanella_fastpath=enabled)))
    a, b = run(True), run(False)
    assert np.array_equal(a.states, b.states)
    assert a.acceptance == b.acceptance


def test_obf_physical_agree_only_for_equal_alphabets():
    equal = repetition_problem(1)
    mixed_model = CircuitFaultModel.from_stim_circuit(stim.Circuit("""
        R 0 1
        X_ERROR(0.1) 0
        DEPOLARIZE1(0.1) 1
        M 0 1
        DETECTOR rec[-2]
        OBSERVABLE_INCLUDE(0) rec[-1]
    """))
    mixed = Problem(mixed_model, CircuitFaultNoise(mixed_model,
        {"X_ERROR": [1], "DEPOLARIZE1": [.2, .3, .5]}),
        CallableDecoder(lambda s: np.zeros(1, dtype=np.uint8), identifier="zero"))
    obf, physical = OBF(), PhysicalFaultProposal()
    for problem in (equal, mixed):
        differences = [abs(obf.probability(a, b, problem, .2) -
                           physical.probability(a, b, problem, .2))
                       for a in _states(problem) for b in _states(problem)]
        assert (max(differences) < 1e-14) == (problem is equal)


def test_heterogeneous_rows_and_zero_padding():
    circuit = stim.Circuit("""
        R 0 1 2
        X_ERROR(0.1) 0
        DEPOLARIZE1(0.1) 1 2
        M 0 1 2
        DETECTOR rec[-3]
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)
    model = CircuitFaultModel.from_stim_circuit(circuit)
    noise = CircuitFaultNoise(model, [[1], [.2, .3, .5], [.5, .3, .2]])
    problem = Problem(model, noise, CallableDecoder(
        lambda s: np.zeros(1, dtype=np.uint8), identifier="zero"))
    p = {"location_rates": [.1, .2, .3]}
    rows = _probability_rows(noise, p)
    assert rows.shape == (3, 4)
    assert rows == pytest.approx(np.array([[.9, .1, 0, 0], [.8, .04, .06, .1],
                                           [.7, .15, .09, .06]]))
    fast, reference = Zanella(), Zanella(use_fastpath=False)
    for state in _states(problem):
        assert fast._distribution(state, problem, p) == pytest.approx(
            reference._distribution(state, problem, p), abs=1e-14)
        assert len(fast._distribution(state, problem, p)) == sum(a-1 for a in model.alphabets)
    edge_noise = CircuitFaultNoise(model, [[1], [0, 1, 0], [1, 0, 0]])
    edge = Problem(model, edge_noise, problem.decoder)
    edge_p = {"location_rates": [0, 1, .3]}
    supported = [state for state in _states(edge) if np.isfinite(edge.log_prob(state, edge_p))]
    assert [state.tolist() for state in supported] == [[0, 2, 0], [0, 2, 1]]
    for state in supported:
        distribution = fast._distribution(state, edge, edge_p)
        assert distribution == pytest.approx(
            reference._distribution(state, edge, edge_p), abs=1e-14)
        assert distribution.sum() == pytest.approx(1)
        for index, neighbor in enumerate(_neighbors(state, edge.alphabets)):
            if not np.isfinite(edge.log_prob(neighbor, edge_p)):
                assert distribution[index] == 0


def test_reject_cluster_and_stabilizer_without_failure_invariance_assumption():
    problem = repetition_problem(1)
    problem.failure = CallableFailure(lambda s, predicted, truth: bool(s[0]), identifier="custom")
    for kernels in (KernelConfig(cluster=1, zanella=0),
                    KernelConfig(stabilizer=1, zanella=0, cluster=0)):
        with pytest.raises(ValueError):
            sample_faulty(problem, .2, config=SamplingConfig(samples=1,
                kernels=kernels), initial_state=[1, 0, 0])


def test_surface_d3_conditional_weight_intervals():
    pytest.importorskip("pymatching")
    from mcmc4qec.circuit import surface_logical_idle_problem

    p = .03
    problem = surface_logical_idle_problem(distance=3, decoder_p=p)
    rng = np.random.default_rng(410)
    failed_weights = []
    for _ in range(300):
        state = problem.noise.sample(p, rng)
        if problem.is_faulty(state):
            failed_weights.append(np.count_nonzero(state))
    assert len(failed_weights) > 20
    mc = np.asarray(failed_weights)
    mc_mean = float(mc.mean())
    mc_half = 1.96 * float(mc.std(ddof=1)) / math.sqrt(len(mc))
    run = sample_faulty(problem, p, seed=411,
        config=SamplingConfig(samples=300, burn_in=100, kernels=KernelConfig(
            single=.3, zanella=.7, cluster=0, stabilizer=0, lazy=.05)))
    trace = np.count_nonzero(run.states, axis=-1).ravel()
    chain_mean = float(trace.mean())
    ess = run.diagnostics['ess']
    chain_half = (1.96 * float(trace.std(ddof=1)) / math.sqrt(ess)
                  if ess is not None else float('inf'))
    overlap = (mc_mean - mc_half <= chain_mean + chain_half and
               chain_mean - chain_half <= mc_mean + mc_half)
    print(f'surface d3 E[w|faulty]: MC={mc_mean:.3f}+/-{mc_half:.3f}, '
          f'Z+OBF={chain_mean:.3f}+/-{chain_half:.3f}, MC failures={len(mc)}, '
          f'ESS={ess}, intervals_overlap={overlap}')
    assert np.isfinite([mc_mean, mc_half, chain_mean, chain_half]).all()
    assert all(problem.is_faulty(state) for state in run.states.reshape(-1, problem.model.n))
