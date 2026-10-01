"""Reversible finite-category proposals using the complete noise density."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass
from math import comb, log
import numpy as np
from .core import Problem, positive_integer
from .fastpath import product_neighbor_distribution


@dataclass(frozen=True)
class Proposal:
    state: np.ndarray
    log_reverse_forward: float = 0.0


def _alphabets(problem):
    sizes = tuple(getattr(problem.model, "alphabets", (2,) * problem.model.n))
    if len(sizes) != problem.model.n:
        raise ValueError("model.alphabets must have one entry per coordinate")
    for size in sizes:
        if positive_integer(size, "alphabet size") < 2:
            raise ValueError("alphabet sizes must be at least two")
    return sizes


def _neighbors(state, alphabets):
    for i, size in enumerate(alphabets):
        for label in range(size):
            if label != state[i]:
                candidate = state.copy()
                candidate[i] = label
                yield candidate


def _neighbor_at(state, alphabets, index):
    """Map a flat neighbor index to one replacement without storing neighbors."""
    for i, size in enumerate(alphabets):
        if index < size - 1:
            candidate = state.copy()
            candidate[i] = index + int(index >= state[i])
            return candidate
        index -= size - 1
    raise IndexError("neighbor index out of range")


class OBF:
    """Uniform single-coordinate category replacement; binary OBF is unchanged."""
    name = "single"

    def propose(self, state: np.ndarray, problem: Problem, p: float | dict[str, Any] | None, rng: np.random.Generator) -> Proposal:
        state = problem.state(state)
        alphabets = _alphabets(problem)
        index = rng.integers(sum(size-1 for size in alphabets))
        return Proposal(_neighbor_at(state, alphabets, index))

    def probability(self, state: np.ndarray, candidate: np.ndarray, problem: Problem, p: float | dict[str, Any] | None) -> float:
        state, candidate = problem.state(state), problem.state(candidate)
        degree = sum(size - 1 for size in _alphabets(problem))
        return 1 / degree if np.count_nonzero(state != candidate) == 1 else 0.0


class Zanella:
    """Square-root locally balanced proposal on all single-category neighbours.

    Zero-support isolated states self-loop. Failure is tested by the MH gate.
    The returned Hastings ratio includes both proposal normalization constants.
    """
    name = "zanella"

    def __init__(self, *, use_fastpath: bool=True) -> None:
        self.use_fastpath = bool(use_fastpath)

    def _distribution(self, state, problem, p):
        if self.use_fastpath:
            local = product_neighbor_distribution(state, problem, p)
            if local is not None:
                return local
        # Only scalar weights are retained; each candidate is released before
        # the next one is evaluated. State-vector storage is O(n), not O(n^2).
        alphabets = _alphabets(problem)
        logs = np.fromiter((.5 * problem.log_prob(neighbor, p)
                            for neighbor in _neighbors(state, alphabets)),
                           dtype=float, count=sum(size-1 for size in alphabets))
        maximum = logs.max()
        if maximum == -np.inf:
            return None
        weights = np.exp(logs - maximum)
        return weights / weights.sum()

    def propose(self, state: np.ndarray, problem: Problem, p: float | dict[str, Any] | None, rng: np.random.Generator) -> Proposal:
        state = problem.state(state)
        q = self._distribution(state, problem, p)
        if q is None:
            return Proposal(state.copy())
        i = rng.choice(len(q), p=q)
        candidate = _neighbor_at(state, _alphabets(problem), i)
        qr = self.probability(candidate, state, problem, p)
        return Proposal(candidate, -np.inf if qr == 0 else float(log(qr) - log(q[i])))

    def probability(self, state: np.ndarray, candidate: np.ndarray, problem: Problem, p: float | dict[str, Any] | None) -> float:
        state, candidate = problem.state(state), problem.state(candidate)
        q = self._distribution(state, problem, p)
        if q is None:
            return float(np.array_equal(state, candidate))
        differences = np.flatnonzero(state != candidate)
        if len(differences) != 1:
            return 0.0
        i = int(differences[0])
        index = sum(size-1 for size in _alphabets(problem)[:i])
        index += int(candidate[i]) - int(candidate[i] > state[i])
        return float(q[index])


class ClusterExchange:
    """Symmetric support-preserving exchange within equal-alphabet groups.

    Alphabet groups are selected uniformly, independently of the state. Binary
    groups exchange k occupied/empty positions. Larger alphabets choose between
    relocation and relabeling with probabilities 1/2 each. Relocation samples
    new nonzero labels uniformly; relabeling includes the current label. An
    unavailable branch self-loops. Occupancy means label != 0, not label sum.

    For Paulis, labels I=0, X=1, Y=2, Z=3 preserve physical error weight. Mixed
    Pauli/binary spaces preserve occupancy separately in each alphabet group.
    Density ratios are still required for nonuniform/correlated noise.
    """
    name = "cluster"

    def __init__(self, k: int=2) -> None:
        self.k = positive_integer(k, "cluster_k")

    def _groups(self, problem):
        alphabets = np.array(_alphabets(problem))
        return [(int(size), np.flatnonzero(alphabets == size)) for size in np.unique(alphabets)]

    def propose(self, state: np.ndarray, problem: Problem, p: float | dict[str, Any] | None, rng: np.random.Generator) -> Proposal:
        state = problem.state(state)
        groups = self._groups(problem)
        size, positions = groups[rng.integers(len(groups))]
        occupied = positions[state[positions] != 0]
        empty = positions[state[positions] == 0]
        candidate = state.copy()
        relocate = size == 2 or rng.random() < .5
        if len(occupied) < self.k:
            return Proposal(candidate)
        if relocate:
            if len(empty) < self.k:
                return Proposal(candidate)
            removed = rng.choice(occupied, self.k, replace=False)
            added = rng.choice(empty, self.k, replace=False)
            candidate[removed] = 0
            candidate[added] = rng.integers(1, size, size=self.k)
        else:
            selected = rng.choice(occupied, self.k, replace=False)
            candidate[selected] = rng.integers(1, size, size=self.k)
        return Proposal(candidate)

    def _group_probability(self, state, candidate, size):
        occupied, empty = state != 0, state == 0
        w, z = int(occupied.sum()), int(empty.sum())
        identical = np.array_equal(state, candidate)
        relocation = 0.0
        if min(w, z) < self.k:
            relocation = float(identical)
        else:
            removed = occupied & (candidate == 0)
            added = empty & (candidate != 0)
            unchanged = ~(removed | added)
            if (int(removed.sum()) == self.k and int(added.sum()) == self.k
                    and np.array_equal(state[unchanged], candidate[unchanged])):
                relocation = 1 / (comb(w, self.k) * comb(z, self.k) * (size-1)**self.k)
        if size == 2:
            return relocation
        relabeling = 0.0
        if w < self.k:
            relabeling = float(identical)
        elif np.array_equal(occupied, candidate != 0):
            differences = int(np.count_nonzero(state != candidate))
            if differences <= self.k:
                # Unchanged selected sites generate duplicate proposal paths.
                relabeling = comb(w-differences, self.k-differences) / (
                    comb(w, self.k) * (size-1)**self.k)
        return .5 * (relocation + relabeling)

    def probability(self, state: np.ndarray, candidate: np.ndarray, problem: Problem, p: float | dict[str, Any] | None) -> float:
        state, candidate = problem.state(state), problem.state(candidate)
        groups = self._groups(problem)
        probability = 0.0
        for size, positions in groups:
            outside = np.ones(len(state), dtype=bool)
            outside[positions] = False
            if np.array_equal(state[outside], candidate[outside]):
                probability += self._group_probability(state[positions], candidate[positions], size)
        return probability / len(groups)


class StabilizerFlip:
    """Uniform static stabilizer XOR for bits or I/X/Y/Z Pauli labels.

    With I=0, X=1, Y=2, Z=3, XOR is Pauli multiplication modulo phase.
    Every proposal still passes the general MH and custom failure gates.
    """
    name = "stabilizer"

    def _rows(self, problem):
        if any(size not in (2, 4) for size in _alphabets(problem)):
            raise ValueError("stabilizer XOR requires binary or Pauli alphabets")
        rows = getattr(problem.model, "stabilizers", None)
        if rows is None or len(rows) == 0:
            raise ValueError("stabilizer kernel requires static model stabilizers")
        return np.array([problem.state(row) for row in rows])

    def propose(self, state: np.ndarray, problem: Problem, p: float | dict[str, Any] | None, rng: np.random.Generator) -> Proposal:
        state = problem.state(state)
        rows = self._rows(problem)
        return Proposal(state ^ rows[rng.integers(len(rows))])

    def probability(self, state: np.ndarray, candidate: np.ndarray, problem: Problem, p: float | dict[str, Any] | None) -> float:
        state, candidate = problem.state(state), problem.state(candidate)
        rows = self._rows(problem)
        return float(np.mean(np.all(rows == (state ^ candidate), axis=1)))
