"""Bounded deterministic decoder cache and safe syndrome delta evaluation."""
from __future__ import annotations
from typing import Any
from collections import OrderedDict

import numpy as np
from numpy.typing import ArrayLike

from .core import BinaryLinearModel, Decoder, Problem, binary, positive_integer
from .models import DepolarizingModel


class CachedDecoder:
    """Cache syndrome-to-logical prediction without changing decoder metadata.

    research_clear reproduces the research runner's periodic clear: boundary()
    clears when size exceeds cap. lru evicts the oldest entry at cap. freeze
    retains the first cap entries and decodes later misses without insertion.
    """

    def __init__(self, decoder: Decoder, *, cap: int | None=None, policy: str="research_clear") -> None:
        if cap is not None:
            cap = positive_integer(cap, "cache_cap")
        if policy not in ("research_clear", "lru", "freeze"):
            raise ValueError("cache_policy must be research_clear, lru, or freeze")
        self.decoder = decoder
        self.cap = cap
        self.policy = policy
        self.lookup: OrderedDict[tuple[tuple[int, ...], str, bytes], np.ndarray] = OrderedDict()

    @property
    def size(self) -> int:
        return len(self.lookup)

    def boundary(self) -> None:
        if self.policy == "research_clear" and self.cap is not None and self.size > self.cap:
            self.lookup.clear()

    def predict(self, syndrome: ArrayLike) -> np.ndarray:
        syndrome = np.asarray(syndrome)
        key = (syndrome.shape, syndrome.dtype.str, syndrome.tobytes())
        if key in self.lookup:
            if self.policy == "lru":
                self.lookup.move_to_end(key)
            return self.lookup[key].copy()
        prediction = binary(self.decoder.predict(syndrome.copy()), ndim=1,
                            name="prediction")
        if self.cap is None or self.policy == "research_clear" or self.size < self.cap:
            self.lookup[key] = prediction.copy()
        elif self.policy == "lru":
            self.lookup.popitem(last=False)
            self.lookup[key] = prediction.copy()
        return prediction.copy()

    def metadata(self) -> dict[str, Any]:
        return self.decoder.metadata()


class FailureEvaluator:
    """Evaluate the same failure predicate with exact single-site syndrome deltas."""

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    def syndrome(self, state: np.ndarray, *, previous: np.ndarray | None=None, previous_syndrome: ArrayLike | None=None) -> ArrayLike:
        model = self.problem.model
        if previous is not None and previous_syndrome is not None:
            differences = np.flatnonzero(np.asarray(state) != np.asarray(previous))
            if len(differences) == 0:
                return np.asarray(previous_syndrome, dtype=np.uint8).copy()
            if len(differences) == 1:
                i = int(differences[0])
                if type(model) is BinaryLinearModel:
                    return np.asarray(previous_syndrome, dtype=np.uint8) ^ model.H[:, i]
                if type(model) is DepolarizingModel:
                    before, after = int(previous[i]), int(state[i])
                    x = (0, 1, 1, 0)
                    z = (0, 0, 1, 1)
                    delta = np.concatenate((model.code.hz[:, i] * (x[before] ^ x[after]),
                                            model.code.hx[:, i] * (z[before] ^ z[after])))
                    return np.asarray(previous_syndrome, dtype=np.uint8) ^ delta
        return model.syndrome(state)

    def evaluate(self, state: np.ndarray, *, previous: np.ndarray | None=None, previous_syndrome: ArrayLike | None=None) -> tuple[bool, ArrayLike]:
        problem = self.problem
        state = problem.state(state)
        syndrome = self.syndrome(state, previous=previous,
                                 previous_syndrome=previous_syndrome)
        predicted = binary(problem.decoder.predict(syndrome), ndim=1, name="prediction")
        truth = binary(problem.model.observables(state.copy()), ndim=1, name="observables")
        if predicted.shape != truth.shape:
            raise ValueError("decoder prediction and observable dimensions differ")
        faulty: bool | np.bool_
        if problem.failure is None:
            faulty = bool(np.any(predicted != truth))
        else:
            faulty = problem.failure(state.copy(), predicted.copy(), truth.copy())
            if not isinstance(faulty, (bool, np.bool_)):
                raise ValueError("failure predicate must return a boolean")
        return bool(faulty), syndrome

    def is_faulty(self, state: np.ndarray, *, previous: np.ndarray | None=None, previous_syndrome: ArrayLike | None=None) -> bool:
        return self.evaluate(state, previous=previous,
                             previous_syndrome=previous_syndrome)[0]
