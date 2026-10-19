import itertools
import math

import numpy as np
import pytest

from mcmc4qec import (
    BinaryLinearModel, CSSCode, CallableDecoder, IndependentBitFlip,
    KernelConfig, SamplingConfig, Problem, exact, direct_mc, sample_faulty,
    diagnose, Result, InitializationError,
)
from mcmc4qec.kernels import OBF, Zanella, ClusterExchange, StabilizerFlip


def repetition_problem(noise=None, failure=None):
    code = CSSCode(hx=np.zeros((0, 3), dtype=int),
                   hz=[[1, 1, 0], [0, 1, 1]],
                   lx=[[1, 1, 1]], lz=[[1, 0, 0]])
    # Minimum-weight correction: syndromes 10 / 11 / 01 -> qubits 0 / 1 / 2.
    decoder = CallableDecoder(lambda s: np.array([int(tuple(s) == (1, 0))]),
                              identifier="repetition3-mw-v1")
    return Problem(code.bit_flip_model(), noise or IndependentBitFlip(3), decoder,
                   failure=failure)


def states(n):
    return [np.array(x, dtype=np.uint8) for x in itertools.product((0, 1), repeat=n)]


def test_exact_reference_and_support_endpoints():
    problem = repetition_problem()
    for p in (0, .01, .2, .5, 1):
        result = exact(problem, p)
        assert result.estimate == pytest.approx(3*p*p - 2*p**3)
        assert sum(math.exp(problem.noise.log_prob(s, p)) for s in states(3)) == pytest.approx(1)


@pytest.mark.parametrize("kernel", [OBF(), Zanella(), ClusterExchange(1),
                                           ClusterExchange(2)])
def test_transition_detailed_balance_with_nonidentical_probabilities(kernel):
    problem = repetition_problem(IndependentBitFlip(3, scales=[1, 2, .5]))
    p = .2
    all_states = states(3)
    pi = np.array([math.exp(problem.noise.log_prob(s, p)) if problem.is_faulty(s) else 0
                   for s in all_states])
    transition = np.zeros((8, 8))
    for i, state in enumerate(all_states):
        if pi[i] == 0:
            transition[i, i] = 1
            continue
        for j, candidate in enumerate(all_states):
            if i == j:
                continue
            q = kernel.probability(state, candidate, problem, p)
            qr = kernel.probability(candidate, state, problem, p)
            if q and qr and pi[j]:
                transition[i, j] = min(q, pi[j] * qr / pi[i])
        transition[i, i] = 1 - transition[i].sum()
    flux = pi[:, None] * transition
    assert np.allclose(flux, flux.T, atol=1e-14)
    assert np.allclose(pi @ transition, pi)
    for state in all_states:
        assert sum(kernel.probability(state, s, problem, p) for s in all_states) == pytest.approx(1)


def test_stabilizer_rechecks_custom_failure():
    from mcmc4qec import CallableFailure
    code = CSSCode(hx=[[1, 1, 0]], hz=[[1, 1, 0]], lx=[[0, 0, 1]], lz=[[0, 0, 1]])
    model = code.bit_flip_model()
    problem = Problem(model, IndependentBitFlip(3),
                      CallableDecoder(lambda s: [0], identifier="zero"),
                      failure=CallableFailure(lambda state, predicted, truth: state[0] == 1,
                                              identifier="first-bit"))
    assert np.array_equal(model.syndrome([1, 0, 0]), model.syndrome([0, 1, 0]))
    result = sample_faulty(problem, .5, config=SamplingConfig(
        samples=20, burn_in=0, kernels=KernelConfig(single=0, zanella=0, cluster=0,
                                                 stabilizer=1, lazy=0)),
        initial_state=[1, 0, 0], seed=7)
    assert np.all(result.states == [1, 0, 0])
    assert result.acceptance["stabilizer"]["accepted"] == 0


def test_mcmc_exact_conditional_and_reproducibility():
    problem = repetition_problem()
    cfg = SamplingConfig(samples=4000, burn_in=100, chains=2,
                         kernels=KernelConfig(cluster_k=1))
    a = sample_faulty(problem, .25, config=cfg, seed=31)
    b = sample_faulty(problem, .25, config=cfg, seed=31)
    assert np.array_equal(a.states, b.states)
    assert not np.array_equal(a.states[0], a.states[1])
    assert all(problem.is_faulty(s) for s in a.states.reshape(-1, 3))
    assert a.states.sum(axis=-1).mean() == pytest.approx(exact(problem, .25).conditional_weight, abs=.05)
    assert np.any(np.all(a.states[:, 1:] == a.states[:, :-1], axis=-1))
    assert a.metadata["config"]["kernels"]["zanella"] == .7
    assert a.metadata["config"]["kernels"]["cluster"] == .3
    assert a.metadata["rng"]["child_spawn_keys"] == [[0], [1]]
    restored = Result.from_json(a.to_json())
    assert np.array_equal(restored.states, a.states)
    assert restored.metadata == a.metadata


def test_direct_mc_same_failure_and_zero_failures_interval():
    problem = repetition_problem()
    result = direct_mc(problem, .25, trials=10000, seed=18)
    assert abs(result.estimate - exact(problem, .25).estimate) < .02
    zero = direct_mc(problem, 0, trials=100, seed=1)
    assert zero.failures == 0 and zero.estimate == 0
    assert zero.interval[0] == 0 < zero.interval[1]
    assert "zero failures" in " ".join(zero.warnings)
    assert Result.from_json(zero.to_json()).interval == zero.interval


def test_initialization_empty_support_and_invalid_inputs():
    problem = repetition_problem()
    cfg = SamplingConfig(samples=2, burn_in=0, max_initial_attempts=5)
    with pytest.raises(InitializationError):
        sample_faulty(problem, 0, config=cfg, seed=1)
    with pytest.raises(ValueError, match="support"):
        sample_faulty(problem, 0, config=cfg, initial_state=[1, 1, 0], seed=1)
    with pytest.raises(ValueError, match="faulty"):
        sample_faulty(problem, .2, config=cfg, initial_state=[0, 0, 0], seed=1)
    for p in (-1, 1.1, math.nan):
        with pytest.raises(ValueError):
            exact(problem, p)
    with pytest.raises(ValueError):
        KernelConfig(single=.1)
    with pytest.raises(ValueError):
        KernelConfig(zanella=math.nan)
    with pytest.raises(ValueError):
        SamplingConfig(samples=0)
    with pytest.raises(ValueError):
        IndependentBitFlip(3).log_prob([1, 0, 2], .1)
    with pytest.raises(ValueError):
        CSSCode(hx=[[1, 0]], hz=[[1, 1]], lx=[[1, 0]], lz=[[1, 0]])
    with pytest.raises(ValueError):
        BinaryLinearModel([[1, .5]], [[1, 0]])
    with pytest.raises(ValueError):
        exact(problem, .1, max_states=4)


def test_endpoint_zanella_and_diagnostic_nonclaims():
    problem = repetition_problem()
    result = sample_faulty(problem, 1, seed=2, config=SamplingConfig(samples=8, burn_in=0))
    assert np.all(result.states == 1)
    d = diagnose(result)
    assert d["ess"] is None and d["iat"] is None
    assert "constant" in " ".join(d["warnings"])
    assert d["rhat"] is None


def test_metadata_identifies_model_noise_decoder_and_source():
    r = exact(repetition_problem(), .1)
    assert r.metadata["model"]["sha256"]
    assert r.metadata["noise"]["type"] == "IndependentBitFlip"
    assert r.metadata["decoder"]["identifier"] == "repetition3-mw-v1"
    assert "source_commit" in r.metadata
    assert r.elapsed_seconds >= 0


def test_independent_seed_spawn():
    from mcmc4qec import spawn_seeds
    assert spawn_seeds(17, 3) == spawn_seeds(17, 3)
    assert len(set(spawn_seeds(17, 3))) == 3
