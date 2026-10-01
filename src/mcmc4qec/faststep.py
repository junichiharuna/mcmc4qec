"""Validated product-noise MH steps for built-in linear models.

This module is internal. Its type gate deliberately excludes user subclasses and
custom failure predicates, whose behavior cannot be inferred from their shape.
"""
from __future__ import annotations
from typing import Any, cast
import math

import numpy as np

from .core import BinaryLinearModel, Problem, binary
from .models import DepolarizingModel, PhenomenologicalModel
from .noise import IndependentBitFlip
from .noise_categorical import DepolarizingNoise, PhenomenologicalNoise
from .fastpath import _probability_rows


def make_faststep(problem: Problem[Any], p: Any,
                  enabled: bool=True) -> FastStepper | None:
    """Return a dedicated stepper only for exact built-in model/noise pairs."""
    if not enabled or problem.failure is not None:
        return None
    pair = (type(problem.model), type(problem.noise))
    allowed = ((BinaryLinearModel, IndependentBitFlip),
               (DepolarizingModel, DepolarizingNoise),
               (PhenomenologicalModel, PhenomenologicalNoise))
    if pair not in allowed:
        return None
    rows = _probability_rows(problem.noise, p)
    return FastStepper(problem, rows)


class FastStepper:
    """Keep a validated state and its linear outputs across accepted moves."""

    def __init__(self, problem: Problem[Any], rows: np.ndarray) -> None:
        self.problem = problem
        self.rows = rows
        self.binary_logs: tuple[np.ndarray, np.ndarray] | None
        with np.errstate(divide="ignore"):
            self.log_rows = np.log(rows)
            if rows.shape[1] == 2:
                self.binary_logs = (.5 * (self.log_rows[:, 1] - self.log_rows[:, 0]),
                                    .5 * (self.log_rows[:, 0] - self.log_rows[:, 1]))
            else:
                self.binary_logs = None
        self.alphabets = problem.alphabets
        self.n = problem.model.n
        self.degree = sum(size - 1 for size in self.alphabets)
        self.offsets = np.cumsum([0] + [size - 1 for size in self.alphabets[:-1]])
        self.positions = np.arange(self.n)
        self.groups = [(size, np.flatnonzero(np.asarray(self.alphabets) == size))
                       for size in sorted(set(self.alphabets))]
        self.stabilizers: np.ndarray | None = None
        self.effects_s = []
        self.effects_o = []
        zero = np.zeros(self.n, dtype=np.uint8)
        for i, size in enumerate(self.alphabets):
            syndromes, observables = [], []
            for label in range(size):
                basis = zero.copy()
                basis[i] = label
                syndromes.append(np.asarray(problem.model.syndrome(basis), dtype=np.uint8))
                observables.append(np.asarray(problem.model.observables(basis), dtype=np.uint8))
            self.effects_s.append(syndromes)
            self.effects_o.append(observables)
        self.observables: np.ndarray | None = None
        self.current_q = None
        self.next_q = None

    def start(self, state: np.ndarray) -> None:
        self.observables = np.asarray(self.problem.model.observables(state), dtype=np.uint8)
        self.current_q = None

    def _distribution(self, state):
        selected = self.rows[self.positions, state]
        if np.any(selected == 0):
            return None
        if self.rows.shape[1] == 2:
            logs = np.where(state, self.binary_logs[1], self.binary_logs[0])
        else:
            pieces = []
            with np.errstate(divide="ignore"):
                for i, size in enumerate(self.alphabets):
                    labels = np.arange(size)
                    pieces.append(.5 * (np.log(self.rows[i, labels[labels != state[i]]])
                                          - np.log(selected[i])))
            logs = np.concatenate(pieces)
        maximum = logs.max()
        if maximum == -np.inf:
            return None
        weights = np.exp(logs - maximum)
        return weights / weights.sum()

    def _neighbor(self, state, index):
        for i, size in enumerate(self.alphabets):
            if index < size - 1:
                candidate = state.copy()
                candidate[i] = index + int(index >= state[i])
                return candidate
            index -= size - 1
        raise IndexError("neighbor index out of range")

    def propose(self, state: np.ndarray, kernel: Any,
                rng: np.random.Generator) -> tuple[np.ndarray, float]:
        """Draw exactly the reference proposal and return its Hastings log ratio."""
        name = kernel.name
        if name == "single":
            return self._neighbor(state, rng.integers(self.degree)), 0.0
        if name == "zanella":
            q = self.current_q
            if q is None:
                q = self._distribution(state)
                self.current_q = q
            if q is None:
                return state.copy(), 0.0
            index = rng.choice(len(q), p=q)
            candidate = self._neighbor(state, index)
            differences = np.flatnonzero(state != candidate)
            i = int(differences[0])
            reverse_index = int(self.offsets[i]) + int(state[i]) - int(state[i] > candidate[i])
            reverse = self._distribution(candidate)
            self.next_q = reverse
            qr = 0.0 if reverse is None else float(reverse[reverse_index])
            return candidate, -np.inf if qr == 0 else float(math.log(qr) - math.log(q[index]))
        if name == "cluster":
            size, positions = self.groups[rng.integers(len(self.groups))]
            occupied = positions[state[positions] != 0]
            empty = positions[state[positions] == 0]
            candidate = state.copy()
            relocate = size == 2 or rng.random() < .5
            if len(occupied) < kernel.k:
                return candidate, 0.0
            if relocate:
                if len(empty) < kernel.k:
                    return candidate, 0.0
                removed = rng.choice(occupied, kernel.k, replace=False)
                added = rng.choice(empty, kernel.k, replace=False)
                candidate[removed] = 0
                candidate[added] = rng.integers(1, size, size=kernel.k)
            else:
                selected = rng.choice(occupied, kernel.k, replace=False)
                candidate[selected] = rng.integers(1, size, size=kernel.k)
            return candidate, 0.0
        if name == "stabilizer":
            rows = self.stabilizers
            return state ^ cast(np.ndarray, rows)[rng.integers(len(cast(np.ndarray, rows)))], 0.0
        raise ValueError("unsupported fast step kernel")

    def attempt(self, state: np.ndarray, current_log: float,
                current_syndrome: np.ndarray, kernel: Any,
                rng: np.random.Generator,
                stats: dict[str, Any]) -> tuple[np.ndarray, float, np.ndarray]:
        """Apply one conditional MH step, updating stats and cached observables."""
        candidate, log_ratio = self.propose(state, kernel, rng)
        if np.isnan(log_ratio) or log_ratio == np.inf:
            raise ValueError("invalid proposal ratio")
        selected = self.rows[self.positions, candidate]
        if np.any(selected == 0):
            lp = -np.inf
        elif type(self.problem.model) is PhenomenologicalModel:
            boundary = self.problem.model.n_data
            logs = self.log_rows[self.positions, candidate]
            lp = float(logs[:boundary].sum() + logs[boundary:].sum())
        else:
            lp = float(self.log_rows[self.positions, candidate].sum())
        if not math.isfinite(lp):
            return state, current_log, current_syndrome
        changes = np.flatnonzero(state != candidate)
        syndrome = current_syndrome.copy()
        observables = cast(np.ndarray, self.observables).copy()
        for i in changes:
            before, after = int(state[i]), int(candidate[i])
            syndrome ^= self.effects_s[i][before] ^ self.effects_s[i][after]
            observables ^= self.effects_o[i][before] ^ self.effects_o[i][after]
        prediction = binary(self.problem.decoder.predict(syndrome), ndim=1,
                            name="prediction")
        if prediction.shape != observables.shape:
            raise ValueError("decoder prediction and observable dimensions differ")
        if np.any(prediction != observables):
            u = rng.random()
            if (math.log(u) if u else -np.inf) < min(0, lp-current_log+log_ratio):
                stats["accepted"] += 1
                stats["moved"] += int(bool(len(changes)))
                self.observables = observables
                self.current_q = self.next_q if kernel.name == "zanella" else None
                return candidate, lp, syndrome
        return state, current_log, current_syndrome
