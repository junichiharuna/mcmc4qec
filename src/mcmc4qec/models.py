"""Pauli and explicitly bounded repeated-measurement CSS state spaces."""
from __future__ import annotations
from typing import Any
import numpy as np

from .core import CSSCode, categorical, identified, positive_integer

_X_COMPONENT = np.array([0, 1, 1, 0], dtype=np.uint8)
_Z_COMPONENT = np.array([0, 0, 1, 1], dtype=np.uint8)


def _code_metadata(code):
    return dict(hx=code.hx, hz=code.hz, lx=code.lx, lz=code.lz)


class DepolarizingModel:
    """Map one I/X/Y/Z label per qubit to full CSS syndromes and observables.

    ``code`` is a validated CSSCode. ``syndrome`` returns ``[hz @ X, hx @ Z]``;
    ``observables`` returns ``[lz @ X, lx @ Z]``, all over GF(2). Y contributes
    to both components. ``validate_state`` returns a copied categorical vector
    and ``metadata`` a JSON-compatible description. A non-CSS code raises
    ``TypeError``; invalid state labels raise ``ValueError``. This model has no
    rate unit; a Problem's probability is for the full modeled experiment.
    """

    def __init__(self, code: CSSCode) -> None:
        if not isinstance(code, CSSCode):
            raise TypeError("code must be a CSSCode")
        self.code = code
        self.n = code.n
        self.alphabets = (4,) * self.n
        self.stabilizers = np.concatenate((code.hx, code.hz * 3), axis=0)
        self.stabilizers.flags.writeable = False

    def validate_state(self, state: np.ndarray) -> np.ndarray:
        return categorical(state, self.alphabets)

    def syndrome(self, state: np.ndarray) -> np.ndarray:
        state = self.validate_state(state)
        return np.concatenate((self.code.hz @ _X_COMPONENT[state] % 2,
                               self.code.hx @ _Z_COMPONENT[state] % 2))

    def observables(self, state: np.ndarray) -> np.ndarray:
        state = self.validate_state(state)
        return np.concatenate((self.code.lz @ _X_COMPONENT[state] % 2,
                               self.code.lx @ _Z_COMPONENT[state] % 2))

    def metadata(self) -> dict[str, Any]:
        return identified(dict(type="DepolarizingModel", code=_code_metadata(self.code),
                               n=self.n, alphabets=self.alphabets,
                               pauli_encoding=["I", "X", "Y", "Z"],
                               sector_order=["X", "Z"], stabilizers=self.stabilizers))


class PhenomenologicalModel:
    """Round-major data faults followed by round-major measurement faults.

    Each round applies new data faults before measurement. The clean initial
    syndrome is zero. ``final_boundary='perfect'`` removes measurement faults
    from the last round; it does not add another data round or noiseless round.
    ``'noisy'`` keeps last-round measurement faults. History and difference
    outputs both have shape ``(rounds, n_checks)``. Difference uses the clean
    initial zero syndrome. Observables refer to final cumulative data errors.
    ``code`` is a CSSCode and ``rounds`` is positive. ``initial_boundary``
    must be ``'clean'``; ``representation`` is ``'history'`` or ``'difference'``;
    ``data_noise`` is ``'bit_flip'``, ``'phase_flip'``, or ``'depolarizing'``.
    Binary phase flips use X checks and Z logical observables. ``validate_state``
    returns the flattened categorical state, ``syndrome`` the selected binary
    history, ``observables`` final logical bits, and ``metadata`` a JSON record.
    Invalid options or states raise ``ValueError``; a non-CSS code raises
    ``TypeError``. A logical failure probability spans all specified rounds.
    """

    def __init__(self, code: CSSCode, rounds: int, *, initial_boundary: Any,
                 final_boundary: Any, representation: str, data_noise: str="bit_flip") -> None:
        if not isinstance(code, CSSCode):
            raise TypeError("code must be a CSSCode")
        if initial_boundary != "clean":
            raise ValueError("initial_boundary must be explicitly 'clean'")
        if final_boundary not in ("perfect", "noisy"):
            raise ValueError("final_boundary must be 'perfect' or 'noisy'")
        if representation not in ("history", "difference"):
            raise ValueError("representation must be 'history' or 'difference'")
        if data_noise not in ("bit_flip", "phase_flip", "depolarizing"):
            raise ValueError("data_noise must be 'bit_flip', 'phase_flip', or 'depolarizing'")
        self.code = code
        self.rounds = positive_integer(rounds, "rounds")
        self.initial_boundary = initial_boundary
        self.final_boundary = final_boundary
        self.representation = representation
        self.data_noise = data_noise
        if data_noise == "bit_flip":
            self.data_model = code.bit_flip_model()
            self.n_checks = len(code.hz)
        elif data_noise == "phase_flip":
            self.data_model = code.phase_flip_model()
            self.n_checks = len(code.hx)
        else:
            self.data_model = DepolarizingModel(code)
            self.n_checks = len(code.hz) + len(code.hx)
        self.measurement_rounds = self.rounds - (final_boundary == "perfect")
        self.n_data = self.rounds * code.n
        self.n_measurement = self.measurement_rounds * self.n_checks
        self.n = self.n_data + self.n_measurement
        self.alphabets = (4 if data_noise == "depolarizing" else 2,) * self.n_data + (2,) * self.n_measurement

    def validate_state(self, state: np.ndarray) -> np.ndarray:
        return categorical(state, self.alphabets)

    def _cumulative_data(self, state):
        data = state[:self.n_data].reshape(self.rounds, self.code.n)
        return np.bitwise_xor.accumulate(data, axis=0)

    def syndrome(self, state: np.ndarray) -> np.ndarray:
        state = self.validate_state(state)
        cumulative = self._cumulative_data(state)
        history = np.array([self.data_model.syndrome(row) for row in cumulative], dtype=np.uint8)
        history[:self.measurement_rounds] ^= state[self.n_data:].reshape(self.measurement_rounds, self.n_checks)
        if self.representation == "difference":
            previous = np.concatenate((np.zeros((1, self.n_checks), dtype=np.uint8), history[:-1]), axis=0)
            return history ^ previous
        return history

    def observables(self, state: np.ndarray) -> np.ndarray:
        state = self.validate_state(state)
        return self.data_model.observables(self._cumulative_data(state)[-1])

    def metadata(self) -> dict[str, Any]:
        return identified(dict(type="PhenomenologicalModel", code=_code_metadata(self.code),
                               n=self.n, alphabets=self.alphabets, rounds=self.rounds,
                               data_noise=self.data_noise, initial_boundary=self.initial_boundary,
                               final_boundary=self.final_boundary, representation=self.representation,
                               n_data=self.n_data, n_measurement=self.n_measurement,
                               n_checks=self.n_checks, measurement_rounds=self.measurement_rounds,
                               state_layout="round-major data; round-major measurement",
                               syndrome_shape=[self.rounds, self.n_checks],
                               data_before_measurement=True,
                               pauli_encoding=["I", "X", "Y", "Z"] if self.data_noise == "depolarizing" else None))
