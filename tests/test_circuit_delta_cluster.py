"""Finite acceptance contract for circuit deltas and explicit physical groups."""
import itertools
import math

import numpy as np
import pytest

stim = pytest.importorskip("stim")

from mcmc4qec.circuit import CircuitFaultModel, CircuitFaultNoise, PhysicalClusterExchange
from mcmc4qec.core import CallableDecoder, CallableFailure, Problem
from mcmc4qec.faststep import make_faststep
from mcmc4qec.kernels import OBF
from mcmc4qec.sampling import KernelConfig, SamplingConfig, sample_faulty


def fixture_problem():
    model = CircuitFaultModel.from_stim_circuit(stim.Circuit("""
        R 0 1 2
        X_ERROR(.1) 0
        DEPOLARIZE1(.1) 1 2
        M 0 1 2
        DETECTOR rec[-3]
        OBSERVABLE_INCLUDE(0) rec[-2] rec[-1]
    """))
    noise = CircuitFaultNoise(model, [[1], [.2, .3, .5], [.5, 0, .5]])
    return Problem(model, noise, CallableDecoder(
        lambda s: np.zeros(1, dtype=np.uint8), identifier="zero"))


def states(problem):
    return [np.array(s, dtype=np.uint8) for s in
            itertools.product(*(range(a) for a in problem.alphabets))]


def test_explicit_group_normalization_ratio_support_and_balance():
    problem = fixture_problem()
    p = {"location_rates": [.1, .3, .7]}
    kernel = PhysicalClusterExchange(((0,), (1, 2)), k=1)
    all_states = states(problem)
    q = np.array([[kernel.probability(a, b, problem, p) for b in all_states]
                  for a in all_states])
    assert q.sum(axis=1) == pytest.approx(np.ones(len(q)))
    assert q == pytest.approx(q.T)
    pi = np.array([math.exp(problem.log_prob(s, p)) * problem.is_faulty(s)
                   for s in all_states])
    transition = np.zeros_like(q)
    for i, a in enumerate(all_states):
        if pi[i] == 0:
            continue
        for j in range(len(q)):
            transition[i, j] = min(q[i, j], pi[j] * q[j, i] / pi[i])
        transition[i, i] += 1 - transition[i].sum()
        # H preserves occupancy in each group; it cannot alone be irreducible.
        for j in np.flatnonzero(transition[i]):
            assert np.count_nonzero(a[1:]) == np.count_nonzero(all_states[j][1:])
        assert not np.any(transition[i, pi == 0])
    flow = pi[:, None] * transition
    assert flow == pytest.approx(flow.T, abs=1e-14)
    rng = np.random.default_rng(412)
    for a in all_states:
        for _ in range(12):
            proposal = kernel.propose(a, problem, p, rng)
            forward = kernel.probability(a, proposal.state, problem, p)
            reverse = kernel.probability(proposal.state, a, problem, p)
            assert forward > 0
            assert proposal.log_reverse_forward == pytest.approx(math.log(reverse / forward))


def test_h_obf_mixture_connectivity_and_laziness_separate_from_balance():
    problem = fixture_problem()
    p = {"location_rates": [.1, .3, .7]}
    supported = [s for s in states(problem) if
                 np.isfinite(problem.log_prob(s, p)) and problem.is_faulty(s)]
    pi = np.array([math.exp(problem.log_prob(s, p)) for s in supported])
    transition = np.zeros((len(pi), len(pi)))
    for weight, kernel in ((.6, OBF()), (.4, PhysicalClusterExchange(((1, 2),), k=1))):
        for i, a in enumerate(supported):
            for j, b in enumerate(supported):
                q = kernel.probability(a, b, problem, p)
                reverse = kernel.probability(b, a, problem, p)
                transition[i, j] += .95 * weight * min(q, pi[j] * reverse / pi[i])
    for i in range(len(pi)):
        transition[i, i] += 1 - transition[i].sum()
    assert transition.sum(axis=1) == pytest.approx(np.ones(len(pi)))
    assert np.diag(transition).min() >= .05 - 1e-14
    assert pi[:, None] * transition == pytest.approx((pi[:, None] * transition).T)
    reached = {0}
    while True:
        expanded = reached | {int(j) for i in reached for j in np.flatnonzero(transition[i])}
        if expanded == reached:
            break
        reached = expanded
    assert len(reached) == len(pi)  # Only this finite example, not a general guarantee.


@pytest.mark.parametrize("groups", [(), ((),), ((0, 0),), ((1,), (1,)), ((-1,),), ((3,),), ((0, 1),)])
def test_reject_invalid_or_incompatible_groups(groups):
    problem = fixture_problem()
    with pytest.raises(ValueError):
        PhysicalClusterExchange(groups, k=1).probability([0, 0, 0], [0, 0, 0], problem, .2)


def test_equal_alphabets_do_not_imply_compatible_physical_channels():
    model = CircuitFaultModel.from_stim_circuit(stim.Circuit("""
        R 0 1
        X_ERROR(.1) 0
        Y_ERROR(.1) 1
        M 0 1
        OBSERVABLE_INCLUDE(0) rec[-1]
    """))
    problem = Problem(model, CircuitFaultNoise(model, [[1], [1]]),
                      CallableDecoder(lambda s: np.zeros(1, dtype=np.uint8), identifier="zero"))
    with pytest.raises(ValueError, match="matching channels"):
        PhysicalClusterExchange(((0, 1),), 1).probability([0, 0], [0, 0], problem, .2)


def test_delta_gate_excludes_model_and_noise_subclasses():
    problem = fixture_problem()
    class DerivedModel(CircuitFaultModel):
        pass
    class DerivedNoise(CircuitFaultNoise):
        pass
    original_type = problem.model.__class__
    problem.model.__class__ = DerivedModel
    assert make_faststep(problem, .2) is None
    problem.model.__class__ = original_type
    problem.noise.__class__ = DerivedNoise
    assert make_faststep(problem, .2) is None


@pytest.mark.parametrize("rates", [[.1, .3, .7], [0, 1, .7]])
def test_delta_seed_trajectory_and_custom_failure_fallback(rates, monkeypatch):
    problem = fixture_problem()
    p = {"location_rates": rates}
    initial = np.array([0, 1, 0], dtype=np.uint8)
    generators = []
    original_rng = np.random.default_rng
    def tracked_rng(seed):
        rng = original_rng(seed)
        generators.append(rng)
        return rng
    monkeypatch.setattr(np.random, "default_rng", tracked_rng)
    def run(enabled):
        return sample_faulty(problem, p, seed=581, initial_state=initial,
            config=SamplingConfig(samples=100, burn_in=20, chains=2,
                kernels=KernelConfig(single=.2, zanella=.4, circuit_single=.2,
                    cluster=.2, cluster_k=1, circuit_groups=((0,), (1, 2)),
                    zanella_fastpath=enabled)))
    a, b = run(True), run(False)
    assert [rng.bit_generator.state for rng in generators[:2]] == [
        rng.bit_generator.state for rng in generators[2:]]
    assert np.array_equal(a.states, b.states)
    assert a.acceptance == b.acceptance
    assert all(problem.is_faulty(s) for s in a.states.reshape(-1, 3))
    stepper = make_faststep(problem, p)
    assert stepper is not None
    for old in states(problem):
        for new in states(problem):
            s, o = problem.model.syndrome(old), problem.model.observables(old)
            for i in np.flatnonzero(old != new):
                s ^= stepper.effects_s[i][old[i]] ^ stepper.effects_s[i][new[i]]
                o ^= stepper.effects_o[i][old[i]] ^ stepper.effects_o[i][new[i]]
            assert np.array_equal(s, problem.model.syndrome(new))
            assert np.array_equal(o, problem.model.observables(new))
    problem.failure = CallableFailure(lambda s, pred, truth: bool(s[1]), identifier="custom")
    assert make_faststep(problem, p) is None
    custom = run(True)
    assert all(problem.is_faulty(s) for s in custom.states.reshape(-1, 3))


def test_groups_are_required_and_only_for_circuit():
    problem = fixture_problem()
    with pytest.raises(ValueError, match="groups"):
        sample_faulty(problem, .2, initial_state=[0, 1, 0],
                      config=SamplingConfig(samples=1))
