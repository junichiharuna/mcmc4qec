"""A reversible physical single-location addition, deletion, or replacement."""
import math

import numpy as np

from ..kernels import Proposal


class PhysicalFaultProposal:
    """Select a location and a nonzero fault uniformly, then toggle or replace.

    The proposal is symmetric for any categorical alphabets. General MH still
    evaluates the complete physical noise density and the failure predicate.
    """

    name = "physical_fault"

    def propose(self, state, problem, p, rng):
        state = problem.state(state)
        index = int(rng.integers(problem.model.n))
        label = int(rng.integers(1, problem.alphabets[index]))
        candidate = state.copy()
        candidate[index] = 0 if state[index] == label else label
        q_forward = self.probability(state, candidate, problem, p)
        q_reverse = self.probability(candidate, state, problem, p)
        return Proposal(candidate, math.log(q_reverse / q_forward))

    def probability(self, state, candidate, problem, p):
        state, candidate = problem.state(state), problem.state(candidate)
        different = np.flatnonzero(state != candidate)
        if len(different) != 1:
            return 0.0
        index = int(different[0])
        return 1 / (problem.model.n * (problem.alphabets[index] - 1))
