"""Physical, mutually exclusive Pauli faults at Stim circuit locations."""
from dataclasses import dataclass
from importlib.metadata import version
import math

import numpy as np

from ..core import categorical, identified


_PAULI = ("I", "X", "Y", "Z")
_NOISE = frozenset(("X_ERROR", "Y_ERROR", "Z_ERROR", "DEPOLARIZE1", "DEPOLARIZE2"))


@dataclass(frozen=True)
class FaultLocation:
    """One target group of a physical noise instruction in a flattened circuit."""

    instruction_index: int
    targets: tuple[int, ...]
    channel: str
    faults: tuple[str, ...]


def stim_noise_locations(circuit):
    """Enumerate supported single and two-qubit Pauli channels by target group."""
    import stim

    if not isinstance(circuit, stim.Circuit):
        raise TypeError("circuit must be stim.Circuit")
    locations = []
    for index, instruction in enumerate(circuit.flattened()):
        channel = instruction.name
        if channel not in _NOISE:
            if channel.endswith("_ERROR") or channel.startswith("DEPOLARIZE") or channel in (
                    "PAULI_CHANNEL_1", "PAULI_CHANNEL_2", "CORRELATED_ERROR", "ELSE_CORRELATED_ERROR"):
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
                                           channel, faults))
    return tuple(locations)


class CircuitFaultModel:
    """Detector and observable effects of categorical physical Pauli faults.

    The source circuit supplies physical noise positions, while its native noise
    probabilities are ignored. Only deterministic Clifford detector circuits are
    supported. A direct Stim insertion path is retained for independent checks.
    """

    def __init__(self, circuit, locations, *, identifier="circuit-physical-faults"):
        import stim

        if not isinstance(circuit, stim.Circuit):
            raise TypeError("circuit must be stim.Circuit")
        self.circuit = circuit.flattened()
        self.locations = tuple(locations)
        if not self.locations:
            raise ValueError("at least one physical fault location is required")
        available = set(stim_noise_locations(self.circuit))
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
    def from_stim_circuit(cls, circuit, *, locations=None, identifier="circuit-physical-faults"):
        return cls(circuit, stim_noise_locations(circuit) if locations is None else locations,
                   identifier=identifier)

    def validate_state(self, state):
        return categorical(state, self.alphabets)

    def _injected_circuit(self, state):
        import stim

        selected = {}
        for loc, label in zip(self.locations, state):
            if label:
                selected.setdefault(loc.instruction_index, []).append((loc, int(label)))
        output = stim.Circuit()
        for index, instruction in enumerate(self.circuit):
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
            source_circuit=str(self.circuit), stim_version=version("stim"),
            locations=[dict(instruction_index=x.instruction_index, targets=x.targets,
                            channel=x.channel, faults=x.faults) for x in self.locations],
            distribution="physical exclusive categorical locations",
            observable="detector and logical flips relative to noiseless circuit"))


class CircuitFaultNoise:
    """Independent physical locations with explicit conditional fault alphabets."""

    def __init__(self, model, conditional_probabilities):
        self.model = model
        self.n = model.n
        self.alphabets = model.alphabets
        conditional = {}
        for channel in {loc.channel for loc in model.locations}:
            if channel not in conditional_probabilities:
                raise ValueError(f"missing conditional probabilities for {channel}")
            values = np.asarray(conditional_probabilities[channel], dtype=float)
            size = len(next(loc for loc in model.locations if loc.channel == channel).faults)
            if (values.shape != (size,) or not np.all(np.isfinite(values)) or
                    np.any(values < 0) or not math.isclose(float(values.sum()), 1, abs_tol=1e-12)):
                raise ValueError("each conditional fault alphabet must be finite, nonnegative, and sum to one")
            conditional[channel] = values.copy()
        if set(conditional_probabilities) != set(conditional):
            raise ValueError("conditional probabilities include unused channels")
        self.conditional_probabilities = conditional

    def probabilities(self, p):
        if isinstance(p, dict):
            if set(p) != set(self.conditional_probabilities):
                raise ValueError("p must give one rate per channel")
            rates = p
        else:
            rates = dict.fromkeys(self.conditional_probabilities, p)
        output = []
        for loc in self.model.locations:
            rate = rates[loc.channel]
            if isinstance(rate, (bool, np.bool_)) or not isinstance(rate, (int, float, np.number)) or not np.isfinite(rate) or not 0 <= rate <= 1:
                raise ValueError("physical location rates must be finite in [0, 1]")
            output.append(np.r_[1-float(rate), float(rate)*self.conditional_probabilities[loc.channel]])
        return output

    def sample(self, p, rng):
        return np.asarray([rng.choice(len(q), p=q) for q in self.probabilities(p)], dtype=np.uint8)

    def log_prob(self, state, p):
        state = self.model.validate_state(state)
        values = [q[label] for q, label in zip(self.probabilities(p), state)]
        return -np.inf if any(x == 0 for x in values) else float(np.log(values).sum())

    def metadata(self):
        return identified(dict(type="CircuitFaultNoise", model_sha256=self.model.metadata()["sha256"],
            conditional_probabilities={k: v.tolist() for k, v in self.conditional_probabilities.items()},
            family="p per location or explicit p per channel", normalized=True,
            independence="between physical locations, exclusive categories within each location"))


def uniform_fault_noise(model):
    """Use equal conditional probabilities for every Pauli fault label."""
    conditional = {loc.channel: [1 / len(loc.faults)] * len(loc.faults)
                   for loc in model.locations}
    return CircuitFaultNoise(model, conditional)
