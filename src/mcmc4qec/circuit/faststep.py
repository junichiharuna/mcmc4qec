"""Internal delta-effect steps for exact built-in physical fault models."""
from __future__ import annotations

from typing import Any, cast

import numpy as np

from ..faststep import FastStepper
from .model import CircuitFaultModel


class CircuitFastStepper(FastStepper):
    """Reuse precomputed physical effects and the common validated MH gate."""

    def _initialize_effects(self) -> None:
        model = cast(CircuitFaultModel, self.problem.model)
        self.effects_s = model._effects_d
        self.effects_o = model._effects_o

    def propose(self, state: np.ndarray, kernel: Any,
                rng: np.random.Generator) -> tuple[np.ndarray, float]:
        if kernel.name == "physical_fault":
            index = int(rng.integers(self.n))
            label = int(rng.integers(1, self.alphabets[index]))
            candidate = state.copy()
            candidate[index] = 0 if state[index] == label else label
            self.next_site = index
            return candidate, 0.0
        if kernel.name == "cluster":
            self.next_site = None
            proposal = kernel.propose(state, self.problem, None, rng)
            return proposal.state, float(proposal.log_reverse_forward)
        return super().propose(state, kernel, rng)
