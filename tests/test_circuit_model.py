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
    original_signature = model.metadata()["sha256"]
    model.circuit.append("X", 0)
    assert model.metadata()["sha256"] == original_signature
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


def test_unsupported_noisy_stim_gate_is_rejected():
    circuit = stim.Circuit("""
        R 0
        HERALDED_ERASE(0.1) 0
        M 0
    """)
    with pytest.raises(ValueError, match="unsupported noise"):
        CircuitFaultModel.from_stim_circuit(circuit)


@pytest.mark.parametrize("measurement", ["M(0.2) 0", "MPP(0.2) Z0"])
def test_noisy_measurement_is_rejected_before_effect_cache(measurement):
    circuit = stim.Circuit(f"""
        R 0
        X_ERROR(0) 0
        {measurement}
        DETECTOR rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)
    with pytest.raises(ValueError, match="noisy measurement"):
        CircuitFaultModel.from_stim_circuit(circuit)


def test_repeated_target_groups_remain_distinct_physical_locations():
    circuit = stim.Circuit("""
        R 0
        X_ERROR(0.1) 0 0
        M 0
        DETECTOR rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)
    model = CircuitFaultModel.from_stim_circuit(circuit)
    assert model.n == 2
    assert [loc.target_group_index for loc in model.locations] == [0, 1]
    assert model.syndrome([1, 1]).tolist() == [0]
    noise = CircuitFaultNoise(model, {"X_ERROR": [1]})
    problem = Problem(model, noise,
        CallableDecoder(lambda syndrome: np.zeros(1, dtype=np.uint8), identifier="zero"))
    assert exact(problem, .1).estimate == pytest.approx(2 * .1 * .9)


def test_explicit_location_rule_filters_physical_channels():
    circuit = small_circuit()
    model = CircuitFaultModel.from_stim_circuit(
        circuit, location_rule=lambda source: [loc for loc in stim_noise_locations(source)
                                               if loc.channel == "X_ERROR"])
    assert model.n == 1
    assert model.locations[0].targets == (0,)
    with pytest.raises(ValueError):
        CircuitFaultModel.from_stim_circuit(
            circuit, locations=model.locations, location_rule=stim_noise_locations)


def test_same_channel_locations_can_have_distinct_alphabets_and_rates():
    circuit = stim.Circuit("""
        R 0 1
        DEPOLARIZE1(0.1) 0 1
        M 0 1
        DETECTOR rec[-2]
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)
    model = CircuitFaultModel.from_stim_circuit(circuit)
    noise = CircuitFaultNoise(model, [[.2, .3, .5], [.5, .3, .2]])
    p = {"location_rates": [.1, .2]}
    assert np.exp(noise.log_prob([1, 3], p)) == pytest.approx(.1 * .2 * .2 * .2)
    assert sum(np.exp(noise.log_prob(s, p)) for s in itertools.product(range(4), repeat=2)) == pytest.approx(1)
    assert noise.metadata()["conditional_mode"] == "per_location"
    draws = np.asarray([noise.sample(p, np.random.default_rng(seed)) for seed in range(600)])
    assert np.mean(draws[:, 0] != 0) == pytest.approx(.1, abs=.035)
    assert np.mean(draws[:, 1] != 0) == pytest.approx(.2, abs=.05)
    with pytest.raises(ValueError):
        noise.probabilities({"location_rates": [.1]})
    with pytest.raises(ValueError):
        CircuitFaultNoise(model, [[.2, .3, .5000000005], [.5, .3, .2]])


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
