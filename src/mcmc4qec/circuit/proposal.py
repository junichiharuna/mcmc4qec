"""A reversible physical single-location addition, deletion, or replacement."""
import math

import numpy as np

from ..kernels import Proposal


class PhysicalFaultProposal:
    """Select a location and a nonzero fault uniformly, then toggle or replace.

    ``propose(state, problem, p, rng)`` returns a standard Proposal with the
    complete reverse/forward log probability ratio. ``probability`` returns
    the forward probability of one ordered state transition. These proposals
    are symmetric even when locations have different fault-alphabet sizes,
    because forward and reverse moves use the same location and alphabet.
    The sampler applies general MH to the complete physical log density and
    the shared failure predicate; a rejected step remains in the chain.

    Args:
        state: One categorical physical fault placement.
        problem: Problem with a CircuitFaultModel and CircuitFaultNoise.
        p: Physical rates accepted by CircuitFaultNoise, including an explicit
            location_rates dictionary; the proposal itself does not use p.
        rng: NumPy random Generator.

    Returns:
        A Proposal for addition, deletion, or replacement at one location.

    Raises:
        ValueError: A state has invalid dimensions or categorical labels.
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
