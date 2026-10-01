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
from .decode_cache import CachedDecoder


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
        self.neighbor_sites = np.repeat(np.arange(self.n),
                                        np.asarray(self.alphabets) - 1)
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
        self.current_logs = None
        self.next_logs = None
        self.next_site: int | None = None

    def start(self, state: np.ndarray) -> None:
        self.observables = np.asarray(self.problem.model.observables(state), dtype=np.uint8)
        self.current_q = self._current_distribution(state)

    def _distribution(self, state):
        selected = self.rows[self.positions, state]
        if np.any(selected == 0):
            return None
        if self.rows.shape[1] == 2:
            logs = np.where(state, self.binary_logs[1], self.binary_logs[0])
        else:
            pieces = []
            for i, size in enumerate(self.alphabets):
                labels = np.arange(size)
                pieces.append(.5 * (self.log_rows[i, labels[labels != state[i]]]
                                      - self.log_rows[i, state[i]]))
            logs = np.concatenate(pieces)
        return self._normalize(logs)

    @staticmethod
    def _normalize(logs):
        maximum = logs.max()
        if maximum == -np.inf:
            return None
        weights = np.exp(logs - maximum)
        return weights / weights.sum()

    def _current_distribution(self, state):
        selected = self.rows[self.positions, state]
        if np.any(selected == 0):
            self.current_logs = None
            return None
        if self.rows.shape[1] == 2:
            self.current_logs = np.where(state, self.binary_logs[1], self.binary_logs[0])
        else:
            pieces = []
            for i, size in enumerate(self.alphabets):
                labels = np.arange(size)
                pieces.append(.5 * (self.log_rows[i, labels[labels != state[i]]]
                                      - self.log_rows[i, state[i]]))
            self.current_logs = np.concatenate(pieces)
        return self._normalize(self.current_logs)

    def _reverse_distribution(self, candidate, site):
        if self.rows[site, candidate[site]] == 0:
            self.next_logs = None
            return None
        logs = self.current_logs.copy()
        if self.rows.shape[1] == 2:
            logs[site] = self.binary_logs[1 if candidate[site] else 0][site]
        else:
            size = self.alphabets[site]
            labels = np.arange(size)
            start = self.offsets[site]
            logs[start:start + size - 1] = .5 * (
                self.log_rows[site, labels[labels != candidate[site]]]
                - self.log_rows[site, candidate[site]])
        self.next_logs = logs
        return self._normalize(logs)

    def _neighbor(self, state, index):
        i = int(self.neighbor_sites[index])
        label = int(index - self.offsets[i])
        candidate = state.copy()
        candidate[i] = label + int(label >= state[i])
        return candidate

    def propose(self, state: np.ndarray, kernel: Any,
                rng: np.random.Generator) -> tuple[np.ndarray, float]:
        """Draw exactly the reference proposal and return its Hastings log ratio."""
        name = kernel.name
        if name == "single":
            index = rng.integers(self.degree)
            self.next_site = int(self.neighbor_sites[index])
            return self._neighbor(state, index), 0.0
        if name == "zanella":
            q = self.current_q
            if q is None:
                q = self._current_distribution(state)
                self.current_q = q
            if q is None:
                self.next_site = None
                return state.copy(), 0.0
            index = rng.choice(len(q), p=q)
            candidate = self._neighbor(state, index)
            i = int(self.neighbor_sites[index])
            self.next_site = i
            reverse_index = int(self.offsets[i]) + int(state[i]) - int(state[i] > candidate[i])
            reverse = self._reverse_distribution(candidate, i)
            self.next_q = reverse
            qr = 0.0 if reverse is None else float(reverse[reverse_index])
            return candidate, -np.inf if qr == 0 else float(math.log(qr) - math.log(q[index]))
        if name == "cluster":
            self.next_site = None
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
            self.next_site = None
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
        changes = (np.array([self.next_site]) if self.next_site is not None
                   else np.flatnonzero(state != candidate))
        syndrome = current_syndrome.copy() if len(changes) else current_syndrome
        observables = cast(np.ndarray, self.observables).copy() if len(changes) else cast(np.ndarray, self.observables)
        for i in changes:
            before, after = int(state[i]), int(candidate[i])
            syndrome ^= self.effects_s[i][before] ^ self.effects_s[i][after]
            observables ^= self.effects_o[i][before] ^ self.effects_o[i][after]
        predicted = self.problem.decoder.predict(syndrome)
        prediction: np.ndarray = (cast(np.ndarray, predicted)
                                  if type(self.problem.decoder) is CachedDecoder
                                  else binary(predicted, ndim=1, name="prediction"))
        if prediction.shape != observables.shape:
            raise ValueError("decoder prediction and observable dimensions differ")
        if np.any(prediction != observables):
            u = rng.random()
            if (math.log(u) if u else -np.inf) < min(0, lp-current_log+log_ratio):
                stats["accepted"] += 1
                stats["moved"] += int(bool(len(changes)))
                self.observables = observables
                if kernel.name == "zanella":
                    self.current_q, self.current_logs = self.next_q, self.next_logs
                elif len(changes):
                    self.current_q = self._current_distribution(candidate)
                return candidate, lp, syndrome
        return state, current_log, current_syndrome
