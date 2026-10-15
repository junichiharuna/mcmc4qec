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
    from .circuit.model import CircuitFaultModel, CircuitFaultNoise
    if pair == (CircuitFaultModel, CircuitFaultNoise):
        from .circuit.faststep import CircuitFastStepper
        return CircuitFastStepper(problem, cast(np.ndarray, _probability_rows(problem.noise, p)))
    allowed = ((BinaryLinearModel, IndependentBitFlip),
               (DepolarizingModel, DepolarizingNoise),
               (PhenomenologicalModel, PhenomenologicalNoise))
    if pair not in allowed:
        return None
    rows = _probability_rows(problem.noise, p)
    return FastStepper(problem, cast(np.ndarray, rows))


class FastStepper:
    """Keep a validated state and its linear outputs across accepted moves."""

    def __init__(self, problem: Problem[Any], rows: np.ndarray) -> None:
        self.problem = problem
        self.binary_model = type(problem.model) is BinaryLinearModel
        self.phenomenological = type(problem.model) is PhenomenologicalModel
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
        self._initialize_effects()
        self.observables: np.ndarray | None = None
        self.current_q: np.ndarray | None = None
        self.next_q: np.ndarray | None = None
        self.current_logs: np.ndarray | None = None
        self.next_logs: np.ndarray | None = None
        self.next_site: int | None = None

    def _initialize_effects(self) -> None:
        self.effects_s: list[np.ndarray] = []
        self.effects_o: list[np.ndarray] = []
        zero = np.zeros(self.n, dtype=np.uint8)
        for i, size in enumerate(self.alphabets):
            syndromes, observables = [], []
            for label in range(size):
                basis = zero.copy()
                basis[i] = label
                syndromes.append(np.asarray(self.problem.model.syndrome(basis), dtype=np.uint8))
                observables.append(np.asarray(self.problem.model.observables(basis), dtype=np.uint8))
            self.effects_s.append(np.asarray(syndromes, dtype=np.uint8))
            self.effects_o.append(np.asarray(observables, dtype=np.uint8))

    def start(self, state: np.ndarray) -> None:
        self.observables = np.asarray(self.problem.model.observables(state), dtype=np.uint8)
        self.current_q = self._current_distribution(state)

    def _distribution(self, state: np.ndarray) -> np.ndarray | None:
        selected = self.rows[self.positions, state]
        if np.any(selected == 0):
            return None
        if self.binary_logs is not None:
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
    def _normalize(logs: np.ndarray) -> np.ndarray | None:
        maximum = logs.max()
        if maximum == -np.inf:
            return None
        weights = np.exp(logs - maximum)
        normalized: np.ndarray = weights / weights.sum()
        return normalized

    def _current_distribution(self, state: np.ndarray) -> np.ndarray | None:
        selected = self.rows[self.positions, state]
        if np.any(selected == 0):
            self.current_logs = None
            return None
        if self.binary_logs is not None:
            self.current_logs = np.where(state, self.binary_logs[1], self.binary_logs[0])
        else:
            pieces = []
            for i, size in enumerate(self.alphabets):
                labels = np.arange(size)
                pieces.append(.5 * (self.log_rows[i, labels[labels != state[i]]]
                                      - self.log_rows[i, state[i]]))
            self.current_logs = np.concatenate(pieces)
        return self._normalize(self.current_logs)

    def _reverse_distribution(self, candidate: np.ndarray, site: int) -> np.ndarray | None:
        if self.rows[site, candidate[site]] == 0:
            self.next_logs = None
            return None
        logs = cast(np.ndarray, self.current_logs).copy()
        if self.binary_logs is not None:
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

    def _neighbor(self, state: np.ndarray, index: int | np.integer[Any]) -> np.ndarray:
        i = int(self.neighbor_sites[index])
        label = int(index - self.offsets[i])
        candidate = state.copy()
        candidate[i] = label + int(label >= state[i])
        return candidate

    def _draw_zanella(self, state: np.ndarray, rng: np.random.Generator
                      ) -> tuple[np.ndarray, int | None]:
        q = self.current_q
        if q is None:
            q = self._current_distribution(state)
            self.current_q = q
        if q is None:
            self.next_site = None
            return state.copy(), None
        index = int(rng.choice(len(q), p=q))
        self.next_site = int(self.neighbor_sites[index])
        return self._neighbor(state, index), index

    def _zanella_ratio(self, state: np.ndarray, candidate: np.ndarray,
                       index: int | None) -> float:
        if index is None:
            return 0.0
        i = int(self.neighbor_sites[index])
        reverse_index = int(self.offsets[i]) + int(state[i]) - int(state[i] > candidate[i])
        reverse = self._reverse_distribution(candidate, i)
        self.next_q = reverse
        qr = 0.0 if reverse is None else float(reverse[reverse_index])
        return -np.inf if qr == 0 else float(math.log(qr) - math.log(cast(np.ndarray, self.current_q)[index]))

    def propose(self, state: np.ndarray, kernel: Any,
                rng: np.random.Generator) -> tuple[np.ndarray, float]:
        """Draw exactly the reference proposal and return its Hastings log ratio."""
        index: int | np.integer[Any]
        name = kernel.name
        if name == "single":
            index = rng.integers(self.degree)
            self.next_site = int(self.neighbor_sites[index])
            return self._neighbor(state, index), 0.0
        if name == "zanella":
            candidate, selected_index = self._draw_zanella(state, rng)
            return candidate, self._zanella_ratio(state, candidate, selected_index)
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
        zanella = kernel.name == "zanella"
        if zanella:
            candidate, index = self._draw_zanella(state, rng)
            log_ratio = 0.0
        else:
            candidate, log_ratio = self.propose(state, kernel, rng)
        if math.isnan(log_ratio) or log_ratio == math.inf:
            raise ValueError("invalid proposal ratio")
        # Zero probabilities already have log density -inf. Preserve the full
        # coordinate-order sum, including the history model's two reductions.
        if self.phenomenological:
            boundary = cast(PhenomenologicalModel, self.problem.model).n_data
            logs = self.log_rows[self.positions, candidate]
            lp = float(logs[:boundary].sum() + logs[boundary:].sum())
        else:
            lp = float(self.log_rows[self.positions, candidate].sum())
        if not math.isfinite(lp):
            return state, current_log, current_syndrome
        if self.binary_model and self.next_site is not None:
            # A binary single-site proposal always toggles the bit. Label zero
            # has zero linear effect, so no temporary index array is needed.
            i = self.next_site
            moved = True
            syndrome = current_syndrome ^ self.effects_s[i][1]
            observables = cast(np.ndarray, self.observables) ^ self.effects_o[i][1]
        else:
            changes = ([self.next_site] if self.next_site is not None
                       else np.flatnonzero(state != candidate))
            moved = bool(len(changes))
            syndrome = current_syndrome.copy() if moved else current_syndrome
            observables = cast(np.ndarray, self.observables).copy() if moved else cast(np.ndarray, self.observables)
            for changed_site in changes:
                i = int(changed_site)
                if self.binary_model:
                    syndrome ^= self.effects_s[i][1]
                    observables ^= self.effects_o[i][1]
                else:
                    before, after = int(state[i]), int(candidate[i])
                    syndrome ^= self.effects_s[i][before] ^ self.effects_s[i][after]
                    observables ^= self.effects_o[i][before] ^ self.effects_o[i][after]
        predicted = self.problem.decoder.predict(syndrome)
        prediction: np.ndarray = (cast(np.ndarray, predicted)
                                  if type(self.problem.decoder) is CachedDecoder
                                  else binary(predicted, ndim=1, name="prediction"))
        if prediction.shape != observables.shape:
            raise ValueError("decoder prediction and observable dimensions differ")
        if (prediction != observables).any():
            if zanella:
                log_ratio = self._zanella_ratio(state, candidate, index)
            u = rng.random()
            if (math.log(u) if u else -np.inf) < min(0, lp-current_log+log_ratio):
                stats["accepted"] += 1
                stats["moved"] += int(moved)
                self.observables = observables
                if kernel.name == "zanella":
                    self.current_q, self.current_logs = self.next_q, self.next_logs
                elif moved:
                    self.current_q = self._current_distribution(candidate)
                return candidate, lp, syndrome
        return state, current_log, current_syndrome
