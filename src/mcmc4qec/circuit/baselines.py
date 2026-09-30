"""Small repetition and midpoint logical-idle circuit baselines."""
import numpy as np

from ..adapters import PyMatchingAdapter
from ..core import Problem
from .model import CircuitFaultModel, uniform_fault_noise


def _measurement_count(instruction):
    if instruction.name in ("M", "MX", "MY", "MR", "MRX", "MRY", "R", "RX", "RY"):
        return len(instruction.targets_copy()) if instruction.name.startswith("M") else 0
    return 0


def _logical_qubits(circuit, basis):
    final_measure = "MX" if basis == "X" else "M"
    instructions = list(circuit)
    final = next((instruction for instruction in reversed(instructions)
                  if instruction.name == final_measure), None)
    logical = next((instruction for instruction in reversed(instructions)
                    if instruction.name == "OBSERVABLE_INCLUDE"), None)
    if final is None or logical is None:
        raise ValueError("generated memory circuit has no final data readout or logical observable")
    targets = final.targets_copy()
    qubits = []
    for target in logical.targets_copy():
        if not target.is_measurement_record_target or not -len(targets) <= target.value < 0:
            raise ValueError("final logical observable must refer only to final data measurements")
        qubits.append(targets[target.value].value)
    return tuple(qubits)


def surface_logical_idle_circuit(*, distance=3, p=.01, basis="Z"):
    """Make 2d noisy rounds with an ideal midpoint logical observable.

    Args:
        distance: Odd rotated-surface distance, at least three.
        p: Failure probability at each marked physical noise location in the
            full 2d-round experiment. It is not a logical rate per round.
        basis: Prepared and observed logical Pauli, ``"X"`` or ``"Z"``.

    Returns:
        Stim circuit with 2d noisy extraction rounds and one ideal midpoint
        MPP observable. It represents the logical value after the first d
        rounds. The later d noisy rounds provide decoder detector information;
        the final data measurement supplies detector boundary information.

    The original final-time logical observable is removed. Record references
    crossing the added MPP measurement are shifted to preserve their meaning.
    The ideal MPP adds no physical fault location.

    Raises:
        ValueError: Distance, basis, rate, or generated record layout is invalid.
    """
    import stim

    if not isinstance(distance, int) or distance < 3 or distance % 2 != 1:
        raise ValueError("distance must be an odd integer at least three")
    if basis not in ("X", "Z"):
        raise ValueError("basis must be X or Z")
    if not isinstance(p, (int, float)) or not 0 < p < 1:
        raise ValueError("p must be strictly between zero and one")
    original = stim.Circuit.generated(
        f"surface_code:rotated_memory_{basis.lower()}", distance=distance,
        rounds=2*distance, after_clifford_depolarization=p,
        after_reset_flip_probability=p, before_measure_flip_probability=p,
        before_round_data_depolarization=p).flattened()
    logical_qubits = _logical_qubits(original, basis)
    instructions = list(original)
    round_end = [i for i, instruction in enumerate(instructions) if instruction.name == "MR"]
    if len(round_end) != 2*distance:
        raise ValueError("unexpected noisy extraction round structure")
    midpoint_tick = next((i for i in range(round_end[distance-1]+1, len(instructions))
                          if instructions[i].name == "TICK"), None)
    if midpoint_tick is None:
        raise ValueError("no midpoint round boundary found")
    midpoint_measure_count = sum(_measurement_count(x) for x in instructions[:midpoint_tick+1])
    output = stim.Circuit()
    original_measure_count = 0
    for index, instruction in enumerate(instructions):
        if instruction.name == "OBSERVABLE_INCLUDE":
            continue
        targets = instruction.targets_copy()
        if index > midpoint_tick:
            shifted = []
            for target in targets:
                if (target.is_measurement_record_target and
                        original_measure_count + target.value < midpoint_measure_count):
                    shifted.append(stim.target_rec(target.value-1))
                else:
                    shifted.append(target)
            targets = shifted
        output.append(instruction.name, targets, instruction.gate_args_copy())
        original_measure_count += _measurement_count(instruction)
        if index == midpoint_tick:
            pauli_target = stim.target_x if basis == "X" else stim.target_z
            product = []
            for qubit in logical_qubits:
                if product:
                    product.append(stim.target_combiner())
                product.append(pauli_target(qubit))
            output.append("MPP", product)
            output.append("OBSERVABLE_INCLUDE", [stim.target_rec(-1)], 0)
    if output.num_observables != 1:
        raise ValueError("midpoint circuit must have one logical observable")
    return output


def surface_logical_idle_problem(*, distance=3, decoder_p=.01, basis="Z"):
    """Build a physical-location Problem and a DEM-derived PyMatching decoder.

    Args:
        distance: Odd rotated-surface distance, at least three.
        decoder_p: Physical per-location failure rate used for the fixed
            decoder's DEM prior, not an estimated logical rate per round.
        basis: Midpoint logical Pauli, ``"X"`` or ``"Z"``.

    Returns:
        Problem with a CircuitFaultModel, uniform conditional Pauli noise,
        and PyMatching observable prediction. ``Problem.is_faulty`` means a
        midpoint logical failure in the full 2d-round experiment. The DEM is
        used only to construct the decoder: sampling and likelihoods remain on
        exclusive physical gate-fault locations. Use the same fixed decoder
        when comparing rates or running a fixed-failure BAR ladder.

    Raises:
        ImportError: Stim or PyMatching is not installed.
        ValueError: Circuit parameters or DEM decomposition are unsupported.
    """
    import pymatching

    circuit = surface_logical_idle_circuit(distance=distance, p=decoder_p, basis=basis)
    model = CircuitFaultModel.from_stim_circuit(
        circuit, identifier=f"rotated-surface-{basis.lower()}-d{distance}-midpoint-idle")
    noise = uniform_fault_noise(model)
    dem = circuit.detector_error_model(decompose_errors=True)
    matching = pymatching.Matching.from_detector_error_model(dem)
    decoder = PyMatchingAdapter(matching, built_with_correlations=False,
        output_kind="observable", identifier=f"pymatching-midpoint-{basis.lower()}-d{distance}",
        settings=dict(decoder_prior=decoder_p, source="Stim midpoint DEM", distance=distance,
                      rounds=2*distance, correction_rounds=distance,
                      buffer_rounds=distance, logical_basis=basis,
                      dem_decompose_errors=True))
    return Problem(model, noise, decoder)
