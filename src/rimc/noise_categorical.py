"""Normalized categorical Pauli and data/measurement fault distributions."""
import numpy as np

from .core import categorical, identified, positive_integer
from .models import PhenomenologicalModel


def _probability(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (float, int, np.floating, np.integer)):
        raise ValueError(f"{name} must be a finite scalar probability")
    value = float(value)
    if not np.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


def _log_selected(state, probability, alphabet):
    selected = np.where(state == 0, 1 - probability, probability / (alphabet - 1))
    if np.any(selected == 0):
        return -np.inf
    return float(np.log(selected).sum())


def _sample(n, probability, alphabet, rng):
    if alphabet == 2:
        return (rng.random(n) < probability).astype(np.uint8)
    return rng.choice(alphabet, size=n, p=[1 - probability] + [probability / (alphabet - 1)] * (alphabet - 1)).astype(np.uint8)


class DepolarizingNoise:
    """Independent qubit categories with probabilities (1-p, p/3, p/3, p/3)."""

    def __init__(self, n):
        self.n = positive_integer(n, "n")
        self.alphabets = (4,) * self.n

    def sample(self, p, rng):
        return _sample(self.n, _probability(p, "p"), 4, rng)

    def log_prob(self, state, p):
        return _log_selected(categorical(state, self.alphabets), _probability(p, "p"), 4)

    def metadata(self):
        return identified(dict(type="DepolarizingNoise", n=self.n, alphabets=self.alphabets,
                               normalized=True, parameterization="P(I)=1-p; P(X)=P(Y)=P(Z)=p/3",
                               pauli_encoding=["I", "X", "Y", "Z"]))


class PhenomenologicalNoise:
    """Data and measurement probabilities must both be explicitly provided.

    ``p={'data': p_data, 'measurement': p_measurement}``. Even a perfect final
    boundary with no measurement coordinates requires both keys, keeping the
    experiment's parameter schema independent of its number of rounds.
    """

    def __init__(self, model: PhenomenologicalModel):
        if not isinstance(model, PhenomenologicalModel):
            raise TypeError("model must be a PhenomenologicalModel")
        self.model = model
        self.n = model.n
        self.alphabets = model.alphabets

    def _parameters(self, p):
        if not isinstance(p, dict) or set(p) != {"data", "measurement"}:
            raise ValueError("p must specify exactly 'data' and 'measurement'")
        return _probability(p["data"], "data"), _probability(p["measurement"], "measurement")

    def sample(self, p, rng):
        data_p, measurement_p = self._parameters(p)
        alphabet = 2 if self.model.data_noise == "bit_flip" else 4
        return np.concatenate((_sample(self.model.n_data, data_p, alphabet, rng),
                               _sample(self.model.n_measurement, measurement_p, 2, rng)))

    def log_prob(self, state, p):
        data_p, measurement_p = self._parameters(p)
        state = self.model.validate_state(state)
        alphabet = 2 if self.model.data_noise == "bit_flip" else 4
        return (_log_selected(state[:self.model.n_data], data_p, alphabet)
                + _log_selected(state[self.model.n_data:], measurement_p, 2))

    def metadata(self):
        return identified(dict(type="PhenomenologicalNoise", n=self.n, alphabets=self.alphabets,
                               model=self.model.metadata(), normalized=True,
                               parameters=["data", "measurement"],
                               measurement_distribution="independent Bernoulli",
                               data_distribution="independent Bernoulli" if self.model.data_noise == "bit_flip" else "independent I/X/Y/Z categories"))
