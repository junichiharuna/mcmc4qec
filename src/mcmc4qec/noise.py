"""Normalized independent bit-flip distributions, including zero support."""
from __future__ import annotations
from typing import Any
import numpy as np
from numpy.typing import ArrayLike
from .core import binary, positive_integer, identified


class IndependentBitFlip:
    """Independent Bernoulli faults with coordinate probabilities p * scales.

    n is a positive integer; optional scales is a nonnegative finite length-n
    vector (default ones). sample(p, rng) returns a uint8 binary state;
    log_prob(state, p) returns its normalized natural log probability and -inf
    outside support. p and every scaled probability must lie in [0, 1].
    Invalid dimensions, states, or parameters raise ValueError. Probabilities
    refer to latent coordinates, not logical failure or a derived round rate.
    """
    def __init__(self, n: int, *, scales: ArrayLike | None=None) -> None:
        self.n = positive_integer(n, "n")
        self.alphabets = (2,) * self.n
        self.scales = np.ones(n) if scales is None else np.asarray(scales, dtype=float).copy()
        if self.scales.shape != (n,) or not np.all(np.isfinite(self.scales)) or np.any(self.scales < 0):
            raise ValueError("scales must be finite nonnegative length-n values")
        self.scales.flags.writeable = False

    def probabilities(self, p: float) -> np.ndarray:
        if np.ndim(p) != 0 or not np.isfinite(p) or not 0 <= p <= 1:
            raise ValueError("p must be a finite scalar in [0, 1]")
        probabilities = float(p) * self.scales
        if np.any(probabilities > 1):
            raise ValueError("p * scales must be in [0, 1]")
        return probabilities

    def sample(self, p: float, rng: np.random.Generator) -> np.ndarray:
        return (rng.random(self.n) < self.probabilities(p)).astype(np.uint8)

    def log_prob(self, state: np.ndarray, p: float) -> float:
        state = binary(state, shape=(self.n,), name="state")
        probs = self.probabilities(p)
        selected = np.where(state, probs, 1 - probs)
        if np.any(selected == 0):
            return -np.inf
        return float(np.log(selected).sum())

    def metadata(self) -> dict[str, Any]:
        return identified(dict(type="IndependentBitFlip", n=self.n, scales=self.scales,
                               normalized=True, parameterization="probabilities = p * scales"))
