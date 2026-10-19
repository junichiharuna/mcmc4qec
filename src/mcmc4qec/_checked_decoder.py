"""Checked physical corrections for the new native decoder factories."""
from __future__ import annotations

from typing import Any, cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .adapters import DecoderAdapter, _binary
from .codes import _gf2_nullspace


class CheckedCorrectionAdapter(DecoderAdapter):
    """Reject invalid syndromes and corrections before returning logical bits.

    This internal adapter is deliberately opt-in: existing factories retain
    their output contract. Backend errors propagate; no recovery is substituted.
    """

    def __init__(self, decoder: Any, *, check_matrix: ArrayLike,
                 logical_map: ArrayLike, identifier: str, settings: dict[str, Any],
                 decode_kwargs: dict[str, Any] | None = None,
                 zero_syndrome_is_identity: bool = False) -> None:
        super().__init__(decoder, output_kind="correction", logical_map=logical_map,
                         identifier=identifier, settings=settings, distribution="ldpc",
                         decode_kwargs=decode_kwargs)
        self._checks = _binary(check_matrix, "check_matrix", (2,))
        mapping = cast(NDArray[np.uint8], self.logical_map)
        if self._checks.shape[1] != mapping.shape[1]:
            raise ValueError("check_matrix width must match logical_map")
        self._constraints = _gf2_nullspace(self._checks.T)
        self._checks.flags.writeable = False
        self._constraints.flags.writeable = False
        self._zero_syndrome_is_identity = zero_syndrome_is_identity

    def predict(self, syndrome: ArrayLike) -> np.ndarray:
        value = _binary(syndrome, "syndrome", (1,))
        if value.shape != (self._checks.shape[0],):
            raise ValueError("syndrome length must match check_matrix")
        if np.any(self._constraints @ value % 2):
            raise ValueError("syndrome is not realizable for check_matrix")
        if self._zero_syndrome_is_identity and not np.any(value):
            mapping = cast(NDArray[np.uint8], self.logical_map)
            return np.zeros(mapping.shape[0], dtype=np.uint8)
        correction = _binary(self.decoder.decode(value.copy(), **self._decode_kwargs),
                             "decoder correction", (1,))
        if correction.shape != (self._checks.shape[1],):
            raise ValueError("decoder correction length must match check_matrix")
        if not np.array_equal(self._checks @ correction % 2, value):
            raise ValueError("decoder correction does not reproduce syndrome (Hc != s)")
        mapping = cast(NDArray[np.uint8], self.logical_map)
        return (mapping @ correction % 2).astype(np.uint8)

    def metadata(self) -> dict[str, Any]:
        result = super().metadata()
        result.update(check_matrix=self._checks.tolist(),
                      syndrome_consistency_checked=True,
                      syndrome_realizability_checked=True,
                      invalid_correction_policy="raise")
        if self._zero_syndrome_is_identity:
            result["zero_syndrome_policy"] = "identity-before-native"
        return result
