"""Explicit-output wrappers for existing decoder objects.

Optional decoders are imported only by their construction helpers. An existing
object's source graph/DEM cannot be reconstructed or certified by this wrapper:
callers must validate its mechanisms before constructing it. Caller-supplied
settings describe the decoder at construction; mutating it afterwards invalidates
that provenance (and can change the failure set).
"""
from __future__ import annotations
from typing import Any

from importlib.metadata import PackageNotFoundError, version
import json

import numpy as np
from numpy.typing import ArrayLike
from .core import Decoder


def _binary(value, name, dimensions):
    try:
        result = np.asarray(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a binary array") from exc
    if result.ndim not in dimensions or result.dtype.kind not in "buif":
        raise ValueError(f"{name} must be a binary array of dimension {dimensions}")
    if not np.all((result == 0) | (result == 1)):
        raise ValueError(f"{name} must contain only binary values")
    return result.astype(np.uint8, copy=True)


def _json_copy(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON dictionary")
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite JSON dictionary") from exc


class DecoderAdapter:
    """Wrap ``object.decode`` with an explicit logical-output contract.

    ``output_kind='observable'`` means decode returns logical predictions.
    ``output_kind='correction'`` requires ``logical_map`` with shape
    (number of observables, correction length), applied over GF(2). Meaning is
    never inferred from output length. Input must be binary with one or two
    dimensions; a two-dimensional history reaches decode without flattening.

    ``settings`` is caller-supplied provenance, not configuration applied to the
    existing object. ``distribution`` names the installed distribution whose
    version is recorded; it does not import that package.

    ``decoder`` exposes ``decode(syndrome, **decode_kwargs)`` and must be
    deterministic for fixed settings. ``identifier`` is a nonempty provenance
    label. ``predict`` returns a one-dimensional binary logical-observable
    vector; ``metadata`` returns a JSON-compatible dictionary. Invalid output
    kinds, maps, binary values, or correction widths raise ``ValueError``;
    a missing decode method raises ``TypeError``. Predictions have no physical
    rate unit; a surrounding Problem reports failure for its whole experiment.
    """

    def __init__(self, decoder: Any, *, output_kind: str, identifier: str, logical_map: ArrayLike | None=None,
                 settings: dict[str, Any] | None=None, distribution: str | None=None, decode_kwargs: dict[str, Any] | None=None) -> None:
        if not callable(getattr(decoder, "decode", None)):
            raise TypeError("decoder must expose a callable decode method")
        if output_kind not in ("observable", "correction"):
            raise ValueError("output_kind must be 'observable' or 'correction'")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("identifier must be a nonempty string")
        if output_kind == "correction" and logical_map is None:
            raise ValueError("correction output requires logical_map")
        if output_kind == "observable" and logical_map is not None:
            raise ValueError("logical_map is only valid for correction output")
        self.decoder = decoder
        self.output_kind = output_kind
        self.identifier = identifier
        self.logical_map = None if logical_map is None else _binary(logical_map, "logical_map", (2,))
        if self.logical_map is not None:
            self.logical_map.flags.writeable = False
        self._settings = _json_copy(settings if settings is not None else {}, "settings")
        self._decode_kwargs = _json_copy(decode_kwargs if decode_kwargs is not None else {}, "decode_kwargs")
        if self._decode_kwargs.get("return_weight", False):
            raise ValueError("decode must return a binary vector, not return_weight output")
        if distribution is not None and (not isinstance(distribution, str) or not distribution.strip()):
            raise ValueError("distribution must be a nonempty string or None")
        self.distribution = distribution
        self._version = None
        if distribution is not None:
            try:
                self._version = version(distribution)
            except PackageNotFoundError:
                pass

    def predict(self, syndrome: np.ndarray) -> np.ndarray:
        syndrome = _binary(syndrome, "syndrome", (1, 2))
        prediction = _binary(self.decoder.decode(syndrome, **self._decode_kwargs), "decoder output", (1,))
        if self.output_kind == "correction":
            if len(prediction) != self.logical_map.shape[1]:  # type: ignore[union-attr]
                raise ValueError("decoder correction length does not match logical_map")
            return (self.logical_map @ prediction % 2).astype(np.uint8)
        return prediction

    def metadata(self) -> dict[str, Any]:
        return _json_copy({
            "identifier": self.identifier,
            "adapter": type(self).__name__,
            "decoder_class": f"{type(self.decoder).__module__}.{type(self.decoder).__qualname__}",
            "output_kind": self.output_kind,
            "logical_map": None if self.logical_map is None else self.logical_map.tolist(),
            "settings": self._settings,
            "decode_kwargs": self._decode_kwargs,
            "distribution": self.distribution,
            "version": self._version,
            "source_graph_validated": False,
        }, "metadata")


class PyMatchingAdapter(DecoderAdapter):
    """Require an explicit construction-time correlation setting.

    ``built_with_correlations`` is the caller's declaration; the original
    construction cannot be inspected reliably on an existing Matching object.
    Decode uses the same setting and rejects conflicting kwargs.
    The remaining arguments and prediction/metadata returns follow
    ``DecoderAdapter``. A missing or conflicting correlation flag raises
    ``ValueError``. No graph-completeness guarantee is inferred.
    """

    def __init__(self, decoder: Any, *, built_with_correlations: bool, output_kind: str,
                 identifier: str, logical_map: ArrayLike | None=None, settings: dict[str, Any] | None=None, decode_kwargs: dict[str, Any] | None=None) -> None:
        if not isinstance(built_with_correlations, bool):
            raise ValueError("built_with_correlations must be a bool")
        kwargs = _json_copy(decode_kwargs if decode_kwargs is not None else {}, "decode_kwargs")
        if "enable_correlations" in kwargs:
            if not isinstance(kwargs["enable_correlations"], bool) or kwargs["enable_correlations"] != built_with_correlations:
                raise ValueError("build and decode correlation settings must agree")
        kwargs["enable_correlations"] = built_with_correlations
        self.built_with_correlations = built_with_correlations
        super().__init__(decoder, output_kind=output_kind, identifier=identifier,
                         logical_map=logical_map, settings=settings,
                         distribution="pymatching", decode_kwargs=kwargs)

    def metadata(self) -> dict[str, Any]:
        result = super().metadata()
        result["built_with_correlations"] = self.built_with_correlations
        return result


def matching_from_check_matrix(check_matrix: ArrayLike, *, logical_map: ArrayLike, identifier: str,
                               weights: ArrayLike | None=None, error_probabilities: ArrayLike | None=None) -> PyMatchingAdapter:
    """Construct a static, uncorrelated correction-output Matching adapter.

    All binary columns are validated before constructing the graph; columns of
    degree greater than two raise instead of silently losing hyperedges. Sparse
    inputs are accepted via ``toarray``. This small helper does not construct
    repeated-measurement graphs or DEMs; wrap those existing objects explicitly.
    Zero-degree columns have no syndrome signature and produce no graph edge.
    ``check_matrix`` has shape (checks, bits), and ``logical_map`` has shape
    (observables, bits). ``identifier`` records provenance; ``weights`` and
    ``error_probabilities`` are forwarded to PyMatching construction. Returns
    a ``PyMatchingAdapter`` predicting logical observables. Invalid shapes,
    nonbinary inputs, or degree-above-two columns raise ``ValueError``;
    unavailable PyMatching raises ``ImportError``. No probability per round is
    inferred from this static graph.
    """
    if hasattr(check_matrix, "toarray"):
        check_matrix = check_matrix.toarray()
    matrix = _binary(check_matrix, "check_matrix", (2,))
    if np.any(matrix.sum(axis=0) > 2):
        raise ValueError("PyMatching requires check-matrix column degree at most two")
    mapping = _binary(logical_map, "logical_map", (2,))
    if mapping.shape[1] != matrix.shape[1]:
        raise ValueError("logical_map width must match check_matrix")
    construction = {"check_matrix": matrix.tolist()}
    for name, value in (("weights", weights), ("error_probabilities", error_probabilities)):
        if value is not None:
            construction[name] = np.asarray(value).tolist()
    _json_copy(construction, "construction settings")
    try:
        import pymatching
    except ImportError as exc:
        raise ImportError("install mcmc4qec[matching] to construct a Matching decoder") from exc
    decoder = pymatching.Matching.from_check_matrix(matrix, weights=weights,
                                                    error_probabilities=error_probabilities)
    # Ensure trailing zero columns remain represented in physical corrections.
    decoder.ensure_num_fault_ids(matrix.shape[1])
    adapter = PyMatchingAdapter(decoder, output_kind="correction", identifier=identifier,
                                logical_map=mapping, built_with_correlations=False,
                                settings=construction)
    return adapter
