"""Local density ratios for exact built-in product noise types."""
import numpy as np

from .noise import IndependentBitFlip
from .noise_categorical import DepolarizingNoise, PhenomenologicalNoise, _probability


def _probability_rows(noise, p):
    """Return categorical probabilities or None for unrecognized noise."""
    # A local import avoids the circuit proposal -> kernels import cycle.
    from .circuit.model import CircuitFaultNoise
    if type(noise) is IndependentBitFlip:
        rates = noise.probabilities(p)
        return np.column_stack((1 - rates, rates))
    if type(noise) is DepolarizingNoise:
        rate = _probability(p, "p")
        return np.tile((1 - rate, rate / 3, rate / 3, rate / 3), (noise.n, 1))
    if type(noise) is PhenomenologicalNoise:
        data, measurement = noise._parameters(p)
        size = 4 if noise.model.data_noise == "depolarizing" else 2
        data_row = [1 - data] + [data / (size - 1)] * (size - 1)
        rows = np.zeros((noise.n, 4), dtype=float)
        rows[:noise.model.n_data, :size] = data_row
        rows[noise.model.n_data:, :2] = [1 - measurement, measurement]
        return rows
    if type(noise) is CircuitFaultNoise:
        # probabilities(p) holds one complete-experiment categorical row per
        # physical location; it is not a vector of logical failure rates.
        probabilities = noise.probabilities(p)
        rows = np.zeros((noise.n, max(noise.alphabets)), dtype=float)
        for index, row in enumerate(probabilities):
            rows[index, :len(row)] = row
        return rows
    return None


def product_neighbor_distribution(state, problem, p):
    """Return Zanella probabilities in flat-neighbor order, or None.

    None means the built-in product path is unavailable or the current state is
    outside support. The caller then uses the complete reference density.
    """
    rows = _probability_rows(problem.noise, p)
    if rows is None:
        return None
    state = np.asarray(state, dtype=np.uint8)
    selected = rows[np.arange(len(state)), state]
    if np.any(selected == 0):
        return None
    if rows.shape[1] == 2:
        changed = rows[np.arange(len(state)), 1 - state]
        with np.errstate(divide="ignore"):
            logs = .5 * (np.log(changed) - np.log(selected))
    else:
        pieces = []
        with np.errstate(divide="ignore"):
            for index, size in enumerate(problem.alphabets):
                labels = np.arange(size)
                pieces.append(.5 * (np.log(rows[index, labels[labels != state[index]]])
                                      - np.log(selected[index])))
        logs = np.concatenate(pieces)
    maximum = logs.max()
    if maximum == -np.inf:
        return None
    weights = np.exp(logs - maximum)
    return weights / weights.sum()
