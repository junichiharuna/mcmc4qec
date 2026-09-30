"""Physical, mutually exclusive Pauli faults at Stim circuit locations."""
from dataclasses import dataclass
from importlib.metadata import version
import math

import numpy as np

from ..core import categorical, identified


_PAULI = ("I", "X", "Y", "Z")
_NOISE = frozenset(("X_ERROR", "Y_ERROR", "Z_ERROR", "DEPOLARIZE1", "DEPOLARIZE2"))
_IDEAL_MEASURE_RESET = frozenset(("M", "MX", "MY", "MR", "MRX", "MRY",
                                  "MPP", "MXX", "MYY", "MZZ", "R", "RX", "RY"))


@dataclass(frozen=True)
class FaultLocation:
    """One exclusive Pauli fault location in a flattened Stim circuit.

    Attributes:
        instruction_index: Index of the source noise instruction after flattening.
        target_group_index: Index of this independent target group within the
            instruction, distinguishing repeated groups on the same qubits.
        targets: One qubit, or an ordered qubit pair for DEPOLARIZE2.
        channel: Supported Stim noise instruction name.
        faults: Nonidentity Pauli strings, in categorical label order 1, 2, ... .
            Label 0 always means no fault at this physical location.
    """

    instruction_index: int
    targets: tuple[int, ...]
    channel: str
    faults: tuple[str, ...]
    target_group_index: int = 0


def stim_noise_locations(circuit):
    """Enumerate physical target groups of supported Stim Pauli channels.

    Args:
        circuit: A Stim circuit, possibly containing REPEAT blocks.

    Returns:
        A tuple of FaultLocation objects in flattened circuit order. Each
        DEPOLARIZE2 target pair is one exclusive 15-fault location; X/Y/Z_ERROR
        and DEPOLARIZE1 targets are single-qubit locations.

    Raises:
        TypeError: ``circuit`` is not a Stim circuit.
        ValueError: A noise instruction or target structure is unsupported.
    """
    import stim

    if not isinstance(circuit, stim.Circuit):
        raise TypeError("circuit must be stim.Circuit")
    locations = []
    for index, instruction in enumerate(circuit.flattened()):
        channel = instruction.name
        if channel not in _NOISE:
            if channel in _IDEAL_MEASURE_RESET and instruction.gate_args_copy():
                raise ValueError(f"unsupported noisy measurement or reset {channel}")
            if channel not in _IDEAL_MEASURE_RESET and stim.gate_data(channel).is_noisy_gate:
                raise ValueError(f"unsupported noise instruction {channel}")
            continue
        targets = instruction.targets_copy()
        size = 2 if channel == "DEPOLARIZE2" else 1
        if len(targets) % size:
            raise ValueError("noise target groups are incomplete")
        faults = (tuple(a+b for a in _PAULI for b in _PAULI if a+b != "II")
                  if size == 2 else (("X", "Y", "Z") if channel == "DEPOLARIZE1"
                                     else (channel[0],)))
        for offset in range(0, len(targets), size):
            group = targets[offset:offset+size]
            if any(not target.is_qubit_target for target in group):
                raise ValueError("noise targets must be qubits")
            locations.append(FaultLocation(index, tuple(target.value for target in group),
                                           channel, faults, offset // size))
    return tuple(locations)


class CircuitFaultModel:
    """Detector and observable effects of categorical physical Pauli faults.

    Args:
        circuit: Stim circuit with supported Pauli noise instructions marking
            physical locations. Their written probabilities are ignored.
        locations: Unique FaultLocation objects selected from the circuit.
        identifier: Stable caller-facing model identifier for provenance.

    The state has one categorical coordinate per location. ``syndrome`` and
    ``observables`` return detector and logical flips for the whole circuit
    experiment relative to the noiseless circuit. Single-fault Stim effects are
    XOR-composed, and ``simulate_state`` independently injects a full placement.
    The noiseless circuit must have deterministic detectors and observables.

    Raises:
        TypeError: The input is not a Stim circuit.
        ValueError: Locations are invalid or the noiseless circuit has random
            detector or observable outcomes.
    """

    def __init__(self, circuit, locations, *, identifier="circuit-physical-faults"):
        import stim

        if not isinstance(circuit, stim.Circuit):
            raise TypeError("circuit must be stim.Circuit")
        self._circuit = circuit.flattened()
        self.locations = tuple(locations)
        if not self.locations:
            raise ValueError("at least one physical fault location is required")
        available = set(stim_noise_locations(self._circuit))
        if len(set(self.locations)) != len(self.locations) or any(loc not in available for loc in self.locations):
            raise ValueError("locations must be unique supported source noise targets")
        self.n = len(self.locations)
        self.alphabets = tuple(len(loc.faults) + 1 for loc in self.locations)
        self.identifier = str(identifier)
        if not self.identifier:
            raise ValueError("identifier must be nonempty")
        self._base = self._injected_circuit(np.zeros(self.n, dtype=np.uint8))
        try:
            self._base.detector_error_model()
        except ValueError as exc:
            raise ValueError("noiseless circuit must have deterministic detectors and observables") from exc
        self._converter = self._base.compile_m2d_converter()
        measurements = self._base.compile_sampler().sample(shots=4)
        detectors, observables = self._converter.convert(
            measurements=measurements, separate_observables=True)
        if (not np.all(detectors == detectors[0]) or
                not np.all(observables == observables[0])):
            raise ValueError("noiseless circuit has intrinsically random detectors or observables")
        self._baseline_d = detectors[0].astype(np.uint8)
        self._baseline_o = observables[0].astype(np.uint8)
        H = np.empty((self._base.num_detectors, sum(a-1 for a in self.alphabets)), dtype=np.uint8)
        L = np.empty((self._base.num_observables, H.shape[1]), dtype=np.uint8)
        self._effects_d, self._effects_o = [], []
        column = 0
        for i, size in enumerate(self.alphabets):
            d = np.zeros((size, self._base.num_detectors), dtype=np.uint8)
            o = np.zeros((size, self._base.num_observables), dtype=np.uint8)
            for label in range(1, size):
                state = np.zeros(self.n, dtype=np.uint8)
                state[i] = label
                d[label], o[label] = self.simulate_state(state)
                H[:, column] = d[label]
                L[:, column] = o[label]
                column += 1
            self._effects_d.append(d)
            self._effects_o.append(o)
        self.H, self.L = H, L
        self.H.flags.writeable = False
        self.L.flags.writeable = False

    @classmethod
    def from_stim_circuit(cls, circuit, *, locations=None, location_rule=None,
                          identifier="circuit-physical-faults"):
        """Build from all supported channels or a caller-supplied location rule.

        Args:
            circuit: Stim circuit whose Pauli noise channels mark locations.
            locations: Optional explicit sequence of selected FaultLocation objects.
            location_rule: Optional callable receiving ``circuit`` and returning
                selected FaultLocation objects. Omitted locations have zero fault
                probability because their source noise commands are stripped.
            identifier: Stable model identifier for provenance.

        Returns:
            A CircuitFaultModel with precomputed detector and observable effects.

        Raises:
            TypeError: ``location_rule`` is not callable.
            ValueError: Both location selectors are supplied, or the circuit
                violates the supported deterministic Pauli-noise contract.
        """
        if locations is not None and location_rule is not None:
            raise ValueError("choose explicit locations or a location_rule")
        if location_rule is not None:
            if not callable(location_rule):
                raise TypeError("location_rule must be callable")
            locations = location_rule(circuit)
        return cls(circuit, stim_noise_locations(circuit) if locations is None else locations,
                   identifier=identifier)

    @property
    def circuit(self):
        """Return a copy of the source Stim circuit to protect cached effects."""
        return self._circuit.copy()

    def validate_state(self, state):
        return categorical(state, self.alphabets)

    def _injected_circuit(self, state):
        import stim

        selected = {}
        for loc, label in zip(self.locations, state):
            if label:
                selected.setdefault(loc.instruction_index, []).append((loc, int(label)))
        output = stim.Circuit()
        for index, instruction in enumerate(self._circuit):
            if instruction.name in _NOISE:
                for loc, label in selected.get(index, ()):
                    for pauli, target in zip(loc.faults[label-1], loc.targets):
                        if pauli != "I":
                            output.append(pauli, target)
            else:
                output.append(instruction)
        return output

    def simulate_state(self, state):
        """Directly run a deterministic fault placement through Stim."""
        state = self.validate_state(state)
        circuit = self._injected_circuit(state)
        measurements = circuit.compile_sampler().sample(shots=1)
        d, o = self._converter.convert(measurements=measurements, separate_observables=True)
        return (d[0].astype(np.uint8) ^ self._baseline_d,
                o[0].astype(np.uint8) ^ self._baseline_o)

    def syndrome(self, state):
        state = self.validate_state(state)
        value = np.zeros(self.H.shape[0], dtype=np.uint8)
        for label, effects in zip(state, self._effects_d):
            value ^= effects[label]
        return value

    def observables(self, state):
        state = self.validate_state(state)
        value = np.zeros(self.L.shape[0], dtype=np.uint8)
        for label, effects in zip(state, self._effects_o):
            value ^= effects[label]
        return value

    def metadata(self):
        return identified(dict(type="CircuitFaultModel", identifier=self.identifier,
            source_circuit=str(self._circuit), stim_version=version("stim"),
            locations=[dict(instruction_index=x.instruction_index,
                            target_group_index=x.target_group_index, targets=x.targets,
                            channel=x.channel, faults=x.faults) for x in self.locations],
            distribution="physical exclusive categorical locations",
            observable="detector and logical flips relative to noiseless circuit"))


class CircuitFaultNoise:
    """Normalized product distribution on exclusive physical fault locations.

    Args:
        model: CircuitFaultModel providing channel and fault label order.
        conditional_probabilities: Either a dictionary from each used Stim
            channel to its nonidentity fault probabilities, or a sequence with
            one such probability vector per physical location. Each vector
            must sum to one without implicit renormalization.

    A scalar ``p`` gives every location that failure rate. A dictionary ``p``
    can give one rate per channel, or ``{"location_rates": [...]}`` with one
    rate per physical location. All rates lie in [0, 1]. The latter form is
    accepted by exact/direct MC and by BAR ladder coordinates.

    ``log_prob`` and ``sample`` concern one complete circuit experiment, whose
    locations are independent but whose faults within a location are exclusive.
    The distribution does not treat individual DEM mechanisms as independent.

    Raises:
        ValueError: A channel is missing, unused, malformed, or unnormalized.
    """

    def __init__(self, model, conditional_probabilities):
        self.model = model
        self.n = model.n
        self.alphabets = model.alphabets
        channels = {loc.channel for loc in model.locations}
        if isinstance(conditional_probabilities, dict):
            if set(conditional_probabilities) != channels:
                raise ValueError("conditional probabilities must specify exactly the used channels")
            provided = [conditional_probabilities[loc.channel] for loc in model.locations]
            self.conditional_mode = "per_channel"
        else:
            if len(conditional_probabilities) != self.n:
                raise ValueError("one conditional probability vector per location is required")
            provided = conditional_probabilities
            self.conditional_mode = "per_location"
        conditional = []
        for loc, source in zip(model.locations, provided):
            values = np.asarray(source, dtype=float)
            size = len(loc.faults)
            if (values.shape != (size,) or not np.all(np.isfinite(values)) or
                    np.any(values < 0) or not math.isclose(float(values.sum()), 1,
                                                           rel_tol=0, abs_tol=1e-12)):
                raise ValueError("each conditional fault alphabet must be finite, nonnegative, and sum to one")
            values = values.copy()
            values.flags.writeable = False
            conditional.append(values)
        self.conditional_probabilities = tuple(conditional)

    def probabilities(self, p):
        if isinstance(p, dict):
            if set(p) == {"location_rates"}:
                rates = np.asarray(p["location_rates"])
                if rates.shape != (self.n,):
                    raise ValueError("p.location_rates must have one rate per location")
            elif set(p) == {loc.channel for loc in self.model.locations}:
                rates = [p[loc.channel] for loc in self.model.locations]
            else:
                raise ValueError("p must give one rate per channel or location_rates")
        else:
            rates = [p] * self.n
        output = []
        for rate, conditional in zip(rates, self.conditional_probabilities):
            if isinstance(rate, (bool, np.bool_)) or not isinstance(rate, (int, float, np.number)) or not np.isfinite(rate) or not 0 <= rate <= 1:
                raise ValueError("physical location rates must be finite in [0, 1]")
            output.append(np.r_[1-float(rate), float(rate)*conditional])
        return output

    def sample(self, p, rng):
        return np.asarray([rng.choice(len(q), p=q) for q in self.probabilities(p)], dtype=np.uint8)

    def log_prob(self, state, p):
        state = self.model.validate_state(state)
        values = [q[label] for q, label in zip(self.probabilities(p), state)]
        return -np.inf if any(x == 0 for x in values) else float(np.log(values).sum())

    def metadata(self):
        return identified(dict(type="CircuitFaultNoise", model_sha256=self.model.metadata()["sha256"],
            conditional_probabilities=[v.tolist() for v in self.conditional_probabilities],
            conditional_mode=self.conditional_mode,
            family="scalar p, per-channel p, or explicit location_rates", normalized=True,
            independence="between physical locations, exclusive categories within each location"))


def uniform_fault_noise(model):
    """Assign equal conditional probabilities to each physical Pauli fault.

    Args:
        model: CircuitFaultModel with supported physical locations.

    Returns:
        CircuitFaultNoise with per-location failure rate supplied later as p.
        Its probabilities refer to the complete circuit experiment, not a
        logical rate per syndrome-extraction round.
    """
    conditional = {loc.channel: [1 / len(loc.faults)] * len(loc.faults)
                   for loc in model.locations}
    return CircuitFaultNoise(model, conditional)
