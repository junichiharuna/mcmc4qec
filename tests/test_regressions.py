"""Numerical and integration boundary regressions found in final review."""
import math
import json

import numpy as np
import pytest

from rimc import BinaryLinearModel, CallableDecoder, CallableFailure, CSSCode, IndependentBitFlip, Problem, Result, exact
from rimc.models import PhenomenologicalModel
from rimc.noise_categorical import PhenomenologicalNoise


def test_exact_distinguishes_underflow_from_empty_failure_support():
    problem = Problem(
        BinaryLinearModel(np.zeros((0, 2), dtype=int), [[1, 0]]),
        IndependentBitFlip(2),
        CallableDecoder(lambda syndrome: [0], identifier="zero"),
        failure=CallableFailure(lambda state, prediction, truth: bool(np.all(state)),
                                identifier="both-bits"),
    )
    tiny = exact(problem, 1e-200)
    assert tiny.estimate == 0  # 1e-400 cannot be represented as a float.
    assert tiny.conditional_weight == pytest.approx(2)
    assert tiny.log_estimate == pytest.approx(-400 * math.log(10))
    assert any("underflow" in warning for warning in tiny.warnings)
    assert not any("empty" in warning for warning in tiny.warnings)
    empty = exact(problem, 0)
    assert empty.conditional_weight is None
    assert any("empty" in warning for warning in empty.warnings)


def test_model_bound_noise_rejects_same_width_but_different_coordinate_meaning():
    repetition = CSSCode(np.zeros((0, 2), dtype=int), [[1, 1]], [[1, 1]], [[1, 0]])
    unencoded = CSSCode(np.zeros((0, 1), dtype=int), np.zeros((0, 1), dtype=int), [[1]], [[1]])
    # Both spaces contain three binary coordinates, but only the first contains
    # a measurement-error coordinate. Width/alphabet checks cannot distinguish.
    first = PhenomenologicalModel(repetition, 1, initial_boundary="clean",
                                 final_boundary="noisy", representation="history")
    different = PhenomenologicalModel(unencoded, 3, initial_boundary="clean",
                                     final_boundary="perfect", representation="history")
    assert first.n == different.n == 3
    decoder = CallableDecoder(lambda syndrome: [0], identifier="zero")
    with pytest.raises(ValueError, match="model"):
        Problem(different, PhenomenologicalNoise(first), decoder)
    equivalent = PhenomenologicalModel(repetition, 1, initial_boundary="clean",
                                      final_boundary="noisy", representation="history")
    # Metadata equivalence is enough; object identity must not be required.
    assert Problem(equivalent, PhenomenologicalNoise(first), decoder).model is equivalent


def test_dem_bound_noise_rejects_different_detector_maps_of_equal_width():
    stim = pytest.importorskip("stim")
    from rimc.stim_dem import from_stim_dem

    first, noise = from_stim_dem(stim.DetectorErrorModel("error(0.1) D0 L0"))
    different, _ = from_stim_dem(stim.DetectorErrorModel("error(0.1) D1 L0"))
    assert first.n == different.n == 1
    with pytest.raises(ValueError, match="model"):
        Problem(different, noise, CallableDecoder(lambda syndrome: [0], identifier="zero"))


def test_json_alphabet_validation_prevents_uint8_wraparound():
    payload = dict(schema_version=1, kind="sample_faulty", elapsed_seconds=0,
                   metadata={"state_space": {"alphabets": [257]}},
                   states=dict(values=[[[256]]], shape=[1, 1, 1], dtype="uint8"))
    with pytest.raises(ValueError):
        Result.from_json(json.dumps(payload))


def test_dev0_binary_json_without_state_space_metadata_still_loads():
    payload = dict(schema_version=1, kind="sample_faulty", elapsed_seconds=.1,
                   metadata={"library_version": "0.1.0.dev0"},
                   states=dict(values=[[[1, 0], [0, 1]]], shape=[1, 2, 2], dtype="uint8"))
    result = Result.from_json(json.dumps(payload))
    assert result.states.dtype == np.uint8
    assert np.array_equal(result.states, [[[1, 0], [0, 1]]])
    assert result.log_estimate is None
    assert result.metadata == payload["metadata"]
    payload["states"]["values"][0][0][0] = 2
    with pytest.raises(ValueError):
        Result.from_json(json.dumps(payload))
