import numpy as np
import pytest

stim = pytest.importorskip("stim")

from mcmc4qec.circuit import CircuitFaultModel, CircuitFaultNoise, stim_noise_locations
from mcmc4qec.core import BinaryLinearModel, CallableDecoder, Problem
from mcmc4qec.estimation import estimate_logical_error
from mcmc4qec.noise import IndependentBitFlip
from mcmc4qec.sampling import KernelConfig, SamplingConfig, direct_mc, exact, sample_faulty


def repetition_problem(rounds):
    circuit = stim.Circuit.generated(
        "repetition_code:memory", distance=3, rounds=rounds,
        before_round_data_depolarization=.01)
    locations = tuple(loc for loc in stim_noise_locations(circuit)
                      if loc.channel == "DEPOLARIZE1" and
                      loc.instruction_index == min(x.instruction_index for x in stim_noise_locations(circuit)))
    model = CircuitFaultModel.from_stim_circuit(circuit, locations=locations)
    noise = CircuitFaultNoise(model, {"DEPOLARIZE1": [1 / 3] * 3})
    decoder = CallableDecoder(lambda s: np.zeros(1, dtype=np.uint8), identifier="zero")
    return Problem(model, noise, decoder)


@pytest.mark.parametrize("rounds", [1, 2])
def test_repetition_d3_exact_and_existing_sampling_pipeline(rounds):
    problem = repetition_problem(rounds)
    anchor = exact(problem, .15)
    assert anchor.estimate == pytest.approx(.1)
    direct = direct_mc(problem, .1, trials=300, seed=73)
    assert direct.interval[0] <= 2 * .1 / 3 <= direct.interval[1]
    config = SamplingConfig(samples=120, burn_in=30,
                            kernels=KernelConfig(circuit_single=1, single=0,
                                                 zanella=0, cluster=0, lazy=.05))
    run = sample_faulty(problem, .1, config=config, seed=74)
    assert run.states.shape == (1, 120, problem.model.n)
    assert run.acceptance["physical_fault"]["proposed"] > 0
    assert all(problem.is_faulty(s) for s in run.states.reshape(-1, problem.model.n))
    estimate = estimate_logical_error(problem, [.15, .1], anchor=anchor,
                                      config=config, seed=75, bootstrap_replicates=0)
    assert estimate.estimate == pytest.approx(2 * .1 / 3, abs=.03)


def test_circuit_rejects_unsupported_kernel_mixes():
    problem = repetition_problem(1)
    unsupported = SamplingConfig(samples=4, burn_in=0,
        kernels=KernelConfig(circuit_single=.5, single=.5, zanella=0, cluster=0))
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
