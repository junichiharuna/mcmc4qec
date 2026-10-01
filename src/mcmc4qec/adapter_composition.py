"""Explicit sector and full-history transformations for logical decoders."""
from __future__ import annotations
from typing import Any
import numpy as np

from .core import Decoder, binary, identified, json_value, positive_integer


def _binary(value, ndim, name):
    if np.asarray(value).dtype.kind not in "buif":
        raise ValueError(f"{name} must contain binary numeric values")
    return binary(value, ndim=ndim, name=name)


def _decoder(decoder):
    if not callable(getattr(decoder, "predict", None)) or not callable(getattr(decoder, "metadata", None)):
        raise TypeError("decoder must provide predict and metadata methods")
    metadata = json_value(decoder.metadata())
    if not isinstance(metadata, dict):
        raise ValueError("decoder.metadata must return a JSON dictionary")


def _identifier(identifier):
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("identifier must be a nonempty string")
    return identifier


class SectorDecoder:
    """Decode explicit X and Z syndrome sectors independently.

    Input is the one-dimensional concatenation of X-error and Z-error
    syndromes. Each child already returns logical predictions. Independence is
    a decoder approximation; this composition never changes the noise model or
    removes its sampled Y correlations.
    ``x_decoder`` and ``z_decoder`` each predict binary logical observables;
    ``x_syndrome_size`` splits the input and ``identifier`` labels provenance.
    ``predict`` returns their concatenated one-dimensional predictions, while
    ``metadata`` records both children and the sector approximation. Invalid
    decoders, identifiers, binary inputs, or split sizes raise ``TypeError`` or
    ``ValueError``. This decoder does not define a probability unit.
    """

    def __init__(self, x_decoder: Decoder, z_decoder: Decoder, *, x_syndrome_size: int, identifier: str) -> None:
        _decoder(x_decoder)
        _decoder(z_decoder)
        self.x_decoder = x_decoder
        self.z_decoder = z_decoder
        self.x_syndrome_size = positive_integer(x_syndrome_size, "x_syndrome_size", zero=True)
        self.identifier = _identifier(identifier)

    def predict(self, syndrome: np.ndarray) -> np.ndarray:
        syndrome = _binary(syndrome, 1, "syndrome")
        if len(syndrome) < self.x_syndrome_size:
            raise ValueError("syndrome is shorter than x_syndrome_size")
        x = _binary(self.x_decoder.predict(syndrome[:self.x_syndrome_size].copy()), 1, "X prediction")
        z = _binary(self.z_decoder.predict(syndrome[self.x_syndrome_size:].copy()), 1, "Z prediction")
        return np.concatenate((x, z))

    def metadata(self) -> dict[str, Any]:
        return identified(dict(type="SectorDecoder", identifier=self.identifier,
                               x_syndrome_size=self.x_syndrome_size,
                               sector_order=["X", "Z"],
                               x_decoder=self.x_decoder.metadata(),
                               z_decoder=self.z_decoder.metadata(),
                               approximation=dict(kind="independent-sector decoding",
                                                  reason="X and Z predictions are decoded separately",
                                                  noise_y_correlations_preserved=True)))


class HistoryDecoder:
    """Transform every entry of a round-major syndrome history explicitly.

    ``round_major_flat`` flattens in C order; ``check_major_history`` transposes
    to (checks, rounds), as used by repeated-measurement PyMatching;
    ``history`` retains (rounds, checks). This adapter does not convert history
    into difference syndromes: the model's representation must already match
    the decoder. No mode drops rounds or selects only the final syndrome.
    ``decoder`` consumes the selected ``layout`` and returns binary logical
    predictions; ``identifier`` labels provenance. ``predict`` accepts a
    (rounds, checks) binary array and returns a one-dimensional prediction.
    Invalid layouts, empty histories, or nonbinary data raise ``ValueError``;
    a decoder without ``predict``/``metadata`` raises ``TypeError``. It does
    not convert an experiment-wide failure probability to a per-round rate.
    """

    def __init__(self, decoder: Decoder, *, layout: str, identifier: str) -> None:
        _decoder(decoder)
        if layout not in ("round_major_flat", "check_major_history", "history"):
            raise ValueError("layout must be round_major_flat, check_major_history, or history")
        self.decoder = decoder
        self.layout = layout
        self.identifier = _identifier(identifier)

    def predict(self, syndrome: np.ndarray) -> np.ndarray:
        history = _binary(syndrome, 2, "syndrome history")
        if history.shape[0] == 0:
            raise ValueError("syndrome history must contain at least one round")
        if self.layout == "round_major_flat":
            transformed = history.reshape(-1)
        elif self.layout == "check_major_history":
            transformed = history.T.copy()
        else:
            transformed = history
        return _binary(self.decoder.predict(transformed), 1, "prediction")

    def metadata(self) -> dict[str, Any]:
        return identified(dict(type="HistoryDecoder", identifier=self.identifier,
                               decoder=self.decoder.metadata(),
                               input_transformation=dict(input_layout="round_major_history",
                                                         output_layout=self.layout,
                                                         retains_all_rounds=True,
                                                         changes_history_to_difference=False)))
