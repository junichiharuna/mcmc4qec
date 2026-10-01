import numpy as np
import pytest

stim = pytest.importorskip("stim")

from mcmc4qec.circuit import CircuitFaultModel, CircuitFaultNoise, stim_noise_locations
from mcmc4qec.adapters import PyMatchingAdapter
from mcmc4qec.core import BinaryLinearModel, CallableDecoder, Problem
from mcmc4qec.estimation import estimate_logical_error
from mcmc4qec.noise import IndependentBitFlip
from mcmc4qec.sampling import KernelConfig, SamplingConfig, direct_mc, exact, sample_faulty


def repetition_problem(rounds):
    circuit = stim.Circuit.generated(
        "repetition_code:memory", distance=3, rounds=rounds,
        before_round_data_depolarization=.01)
    locations = tuple(loc for loc in stim_noise_locations(circuit)
                      if loc.channel == "DEPOLARIZE1")
    model = CircuitFaultModel.from_stim_circuit(circuit, locations=locations)
    noise = CircuitFaultNoise(model, {"DEPOLARIZE1": [1 / 3] * 3})
    decoder = CallableDecoder(lambda s: np.zeros(1, dtype=np.uint8), identifier="zero")
    return Problem(model, noise, decoder)


def zero_decoder_rate(rounds, p):
    flip = 2 * p / 3
    return (1 - (1 - 2 * flip)**rounds) / 2


@pytest.mark.parametrize("rounds", [1, 2])
def test_repetition_d3_exact_and_existing_sampling_pipeline(rounds):
    problem = repetition_problem(rounds)
    anchor = exact(problem, .15)
    assert problem.model.n == 3 * rounds
    assert anchor.estimate == pytest.approx(zero_decoder_rate(rounds, .15))
    direct = direct_mc(problem, .1, trials=300, seed=73)
    assert direct.interval[0] <= zero_decoder_rate(rounds, .1) <= direct.interval[1]
    config = SamplingConfig(samples=120, burn_in=30,
                            kernels=KernelConfig(circuit_single=1, single=0,
                                                 zanella=0, cluster=0, lazy=.05))
    run = sample_faulty(problem, .1, config=config, seed=74)
    assert run.states.shape == (1, 120, problem.model.n)
    assert run.acceptance["physical_fault"]["proposed"] > 0
    assert all(problem.is_faulty(s) for s in run.states.reshape(-1, problem.model.n))
    estimate = estimate_logical_error(problem, [.15, .1], anchor=anchor,
                                      config=config, seed=75, bootstrap_replicates=0)
    assert estimate.estimate == pytest.approx(zero_decoder_rate(rounds, .1), abs=.04)


def test_repetition_d3_two_rounds_all_locations_exact_with_pymatching():
    pymatching = pytest.importorskip("pymatching")
    p = .1
    circuit = stim.Circuit.generated(
        "repetition_code:memory", distance=3, rounds=2,
        before_round_data_depolarization=p)
    model = CircuitFaultModel.from_stim_circuit(circuit)
    assert model.n == 6
    assert np.prod(model.alphabets) == 4096
    noise = CircuitFaultNoise(model, {"DEPOLARIZE1": [1 / 3] * 3})
    dem = circuit.detector_error_model(decompose_errors=True)
    matching = pymatching.Matching.from_detector_error_model(dem)
    decoder = PyMatchingAdapter(matching, built_with_correlations=False,
        output_kind="observable", identifier="repetition-d3-two-rounds-mwpm",
        settings={"decoder_prior": p, "source": "Stim DEM"})
    problem = Problem(model, noise, decoder)
    enumerated = exact(problem, p)
    assert enumerated.estimate == pytest.approx(.02515682853, abs=1e-10)
    detectors, observables = circuit.compile_detector_sampler(seed=6001).sample(
        shots=20_000, separate_observables=True)
    native_failures = np.count_nonzero(matching.decode_batch(detectors) != observables)
    assert native_failures > 0
    assert native_failures / 20_000 == pytest.approx(enumerated.estimate, abs=.006)


def test_circuit_rejects_unsupported_kernel_mixes():
    problem = repetition_problem(1)
    unsupported = SamplingConfig(samples=4, burn_in=0,
        kernels=KernelConfig(circuit_single=.5, single=0, zanella=0, cluster=.5))
    with pytest.raises(ValueError):
        sample_faulty(problem, .1, config=unsupported, initial_state=[0, 0, 1])
    with pytest.raises(ValueError):
        sample_faulty(problem, .1, config=SamplingConfig(samples=4, burn_in=0),
                      initial_state=[0, 0, 1])


def test_physical_kernel_rejected_for_non_circuit_model():
    model = BinaryLinearModel([[1]], [[1]])
    decoder = CallableDecoder(lambda syndrome: np.array([0], dtype=np.uint8), identifier="zero")
    problem = Problem(model, IndependentBitFlip(1), decoder)
    config = SamplingConfig(samples=4, burn_in=0,
        kernels=KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0))
    with pytest.raises(ValueError):
        sample_faulty(problem, .1, config=config, initial_state=[1])
