import numpy as np
import pytest

stim = pytest.importorskip("stim")
pymatching = pytest.importorskip("pymatching")

from mcmc4qec.circuit import surface_logical_idle_circuit, surface_logical_idle_problem
from mcmc4qec.sampling import direct_mc


def test_rotated_surface_d3_midpoint_direct_mc_matches_native_stim():
    p = .01
    problem = surface_logical_idle_problem(distance=3, decoder_p=p, basis="Z")
    assert problem.model.H.shape[0] == 48
    assert problem.model.L.shape[0] == 1
    assert problem.model.n > 300
    midpoint_index = next(i for i, instruction in enumerate(problem.model.circuit)
                          if instruction.name == "MPP")
    before = next(i for i, loc in enumerate(problem.model.locations)
                  if loc.channel == "DEPOLARIZE1" and loc.targets == (1,)
                  and loc.instruction_index < midpoint_index)
    after = next(i for i, loc in enumerate(problem.model.locations)
                 if loc.channel == "DEPOLARIZE1" and loc.targets == (1,)
                 and loc.instruction_index > midpoint_index)
    state = np.zeros(problem.model.n, dtype=np.uint8)
    state[before] = 1
    assert problem.model.observables(state).tolist() == [1]
    state[before] = 0
    state[after] = 1
    assert problem.model.observables(state).tolist() == [0]
    circuit = surface_logical_idle_circuit(distance=3, p=p, basis="Z")
    assert circuit.num_observables == 1
    native_detectors, native_observables = circuit.compile_detector_sampler(
        seed=2026).sample(shots=5000, separate_observables=True)
    native_predictions = problem.decoder.decoder.decode_batch(native_detectors)
    native_failures = np.count_nonzero(native_predictions != native_observables)
    native_rate = native_failures / 5000
    result = direct_mc(problem, p, trials=700, seed=2027)
    assert result.failures > 20
    assert result.interval[0] <= native_rate <= result.interval[1]
    assert result.estimate == pytest.approx(native_rate, abs=.04)


def test_midpoint_is_not_final_memory_observable():
    midpoint = surface_logical_idle_circuit(distance=3, p=.01, basis="Z")
    final = stim.Circuit.generated(
        "surface_code:rotated_memory_z", distance=3, rounds=6,
        after_clifford_depolarization=.01,
        after_reset_flip_probability=.01,
        before_measure_flip_probability=.01,
        before_round_data_depolarization=.01)
    assert str(midpoint) != str(final)
    assert "MPP Z5*Z3*Z1" in str(midpoint)
    assert str(midpoint).count("OBSERVABLE_INCLUDE") == 1
    midpoint.detector_error_model(decompose_errors=True)
