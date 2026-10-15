"""Explicit physical-location groups for occupancy-preserving exchanges."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from ..core import Problem
from ..kernels import ClusterExchange
from .model import CircuitFaultModel


class PhysicalClusterExchange(ClusterExchange):
    """Exchange faults only within explicit compatible physical location groups.

    Args:
        groups: Nonempty disjoint groups of model location indices. Locations
            in a group must have the same channel and ordered fault alphabet.
            Groups may omit locations and may separate space/time regions.
        k: Number of occupied locations relocated or relabeled per move.

    Groups are chosen uniformly, independently of the current placement.
    Binary groups relocate k faults; other groups select relocation or
    relabeling with probability one half each. Unavailable branches self-loop.
    All labels remain exclusive at their physical location. The proposal is
    symmetric, but heterogeneous rates and zero support still require full MH
    density and failure checks. H alone preserves each group's occupancy and
    is generally reducible; mix with single-location proposals as appropriate.

    Raises:
        ValueError: Groups overlap, are empty, use invalid indices, or contain
            incompatible channels or alphabets, or the model is not a circuit.
    """

    def __init__(self, groups: Sequence[Sequence[int]], k: int = 2) -> None:
        super().__init__(k)
        self.location_groups = tuple(tuple(group) for group in groups)
        if not self.location_groups or any(not group for group in self.location_groups):
            raise ValueError("physical cluster groups must be nonempty")
        indices = [index for group in self.location_groups for index in group]
        if any(isinstance(index, (bool, np.bool_)) or
               not isinstance(index, (int, np.integer)) or index < 0 for index in indices):
            raise ValueError("physical cluster indices must be nonnegative integers")
        if len(set(indices)) != len(indices):
            raise ValueError("physical cluster groups must be disjoint without duplicates")

    def _groups(self, problem: Problem[Any]) -> list[tuple[int, np.ndarray]]:
        model = problem.model
        if not isinstance(model, CircuitFaultModel):
            raise ValueError("physical cluster groups require CircuitFaultModel")
        output = []
        for group in self.location_groups:
            if any(index >= model.n for index in group):
                raise ValueError("physical cluster location index is out of range")
            first = model.locations[group[0]]
            if any((model.locations[index].channel, model.locations[index].faults) !=
                   (first.channel, first.faults) for index in group):
                raise ValueError("physical cluster groups need matching channels and fault alphabets")
            output.append((model.alphabets[group[0]], np.asarray(group, dtype=int)))
        return output
