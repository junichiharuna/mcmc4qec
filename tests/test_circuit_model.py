import itertools

import numpy as np
import pytest

stim = pytest.importorskip("stim")

from mcmc4qec.circuit import CircuitFaultModel, CircuitFaultNoise, stim_noise_locations
from mcmc4qec.core import CallableDecoder, Problem
from mcmc4qec.sampling import exact


def small_circuit():
    return stim.Circuit("""
        R 0 1
        X_ERROR(0.1) 0
        DEPOLARIZE1(0.1) 1
        M 0 1
        DETECTOR rec[-2]
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)


def test_exclusive_alphabet_and_normalized_density():
    model = CircuitFaultModel.from_stim_circuit(small_circuit())
    assert model.alphabets == (2, 4)
    noise = CircuitFaultNoise(model, {"X_ERROR": [1], "DEPOLARIZE1": [.2, .3, .5]})
    states = itertools.product(range(2), range(4))
    assert sum(np.exp(noise.log_prob(s, .2)) for s in states) == pytest.approx(1)
    assert np.exp(noise.log_prob([0, 2], .2)) == pytest.approx(.8 * .2 * .3)
    with pytest.raises(ValueError):
        CircuitFaultNoise(model, {"X_ERROR": [1], "DEPOLARIZE1": [.2, .3, .4]})
    with pytest.raises(ValueError):
        model.validate_state([0, 4])


def test_intrinsically_random_observable_is_rejected():
    circuit = stim.Circuit("""
        R 0
        X_ERROR(0.1) 0
        H 0
        M 0
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)
    with pytest.raises(ValueError, match="deterministic"):
        CircuitFaultModel.from_stim_circuit(circuit)


def test_single_fault_xor_matches_direct_stim_random_placements():
    circuit = stim.Circuit.generated(
        "repetition_code:memory", distance=3, rounds=2,
        after_clifford_depolarization=.01,
        after_reset_flip_probability=.01,
        before_measure_flip_probability=.01,
        before_round_data_depolarization=.01)
    model = CircuitFaultModel.from_stim_circuit(circuit)
    rng = np.random.default_rng(83)
    for _ in range(24):
        state = np.zeros(model.n, dtype=np.uint8)
        for i in rng.choice(model.n, size=min(5, model.n), replace=False):
            state[i] = rng.integers(1, model.alphabets[i])
        detectors, observable = model.simulate_state(state)
        assert np.array_equal(model.syndrome(state), detectors)
        assert np.array_equal(model.observables(state), observable)


def test_repetition_d3_exact_uses_physical_locations():
    circuit = stim.Circuit.generated(
        "repetition_code:memory", distance=3, rounds=1,
        before_round_data_depolarization=.01)
    locations = tuple(x for x in stim_noise_locations(circuit) if x.channel == "DEPOLARIZE1")
    model = CircuitFaultModel.from_stim_circuit(circuit, locations=locations)
    assert model.n == 3
    noise = CircuitFaultNoise(model, {"DEPOLARIZE1": [1 / 3] * 3})
    decoder = CallableDecoder(lambda syndrome: np.zeros(1, dtype=np.uint8), identifier="zero")
    problem = Problem(model, noise, decoder)
    result = exact(problem, .1)
    expected = sum(
        np.exp(noise.log_prob(s, .1)) * problem.is_faulty(s)
        for s in itertools.product(range(4), repeat=3))
    assert result.estimate == pytest.approx(expected)
    assert result.estimate == pytest.approx(2 * .1 / 3)
