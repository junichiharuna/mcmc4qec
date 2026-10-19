from itertools import product
import json

import numpy as np
import pytest

from mcmc4qec.adapter_composition import HistoryDecoder, SectorDecoder
from mcmc4qec.adapters import DecoderAdapter, PyMatchingAdapter
from mcmc4qec.core import CSSCode, Problem
from mcmc4qec.models import PhenomenologicalModel
from mcmc4qec.noise_categorical import PhenomenologicalNoise
from mcmc4qec.sampling import exact


class Record:
    def __init__(self, result):
        self.result = result

    def predict(self, syndrome):
        self.received = syndrome.copy()
        return self.result

    def metadata(self):
        return {"type": "Record"}


def test_sector_explicit_boundary_and_output_order():
    x, z = Record([1, 0]), Record([0, 1])
    decoder = SectorDecoder(x, z, x_syndrome_size=2, identifier="separate")
    np.testing.assert_array_equal(decoder.predict([1, 0, 1]), [1, 0, 0, 1])
    np.testing.assert_array_equal(x.received, [1, 0])
    np.testing.assert_array_equal(z.received, [1])
    assert decoder.metadata()["approximation"]["noise_y_correlations_preserved"] is True
    assert json.loads(json.dumps(decoder.metadata())) == decoder.metadata()


@pytest.mark.parametrize("layout,expected", [("history", [[1, 0], [1, 1], [0, 1]]),
                                             ("check_major_history", [[1, 1, 0], [0, 1, 1]]),
                                             ("round_major_flat", [1, 0, 1, 1, 0, 1])])
def test_full_history_is_retained(layout, expected):
    inner = Record([0])
    decoder = HistoryDecoder(inner, layout=layout, identifier="history")
    decoder.predict([[1, 0], [1, 1], [0, 1]])
    np.testing.assert_array_equal(inner.received, expected)
    assert decoder.metadata()["input_transformation"]["output_layout"] == layout
    assert decoder.metadata()["input_transformation"]["retains_all_rounds"] is True


@pytest.mark.parametrize("syndrome", [[0], [[[1]]], [[2]], [[float("nan")]], [["1"]], [[1j]], np.empty((0, 1))])
def test_invalid_history_rejected(syndrome):
    decoder = HistoryDecoder(Record([0]), layout="history", identifier="test")
    with pytest.raises(ValueError):
        decoder.predict(syndrome)


def test_invalid_options_and_decoder_output():
    with pytest.raises(ValueError):
        HistoryDecoder(Record([0]), layout="last_round", identifier="test")
    for size in (-1, 1.5, True):
        with pytest.raises(ValueError):
            SectorDecoder(Record([0]), Record([0]), x_syndrome_size=size, identifier="test")
    with pytest.raises(ValueError):
        SectorDecoder(Record([0]), Record([0]), x_syndrome_size=2, identifier="test").predict([0])
    with pytest.raises(ValueError):
        HistoryDecoder(Record([[0]]), layout="history", identifier="test").predict([[0]])
    with pytest.raises(ValueError):
        SectorDecoder(Record([2]), Record([0]), x_syndrome_size=1, identifier="test").predict([0, 0])


def model():
    code = CSSCode(np.empty((0, 3)), [[1, 1, 0], [0, 1, 1]], [[1, 1, 1]], [[1, 0, 0]])
    return PhenomenologicalModel(code, 2, initial_boundary="clean", final_boundary="perfect", representation="difference")


def test_real_pymatching_repeated_history():
    pm = pytest.importorskip("pymatching")
    m = model()
    matching = pm.Matching.from_check_matrix(m.code.hz, repetitions=2, weights=[2, 2, 2], timelike_weights=3)
    inner = PyMatchingAdapter(matching, output_kind="correction", logical_map=m.code.lz,
                              built_with_correlations=False, identifier="rep3-2round")
    decoder = HistoryDecoder(inner, layout="check_major_history", identifier="transpose-all")
    # Every single data fault is corrected. A measurement fault changes two
    # adjacent detection events and should not cause a data correction.
    for index in range(m.n):
        state = np.eye(m.n, dtype=np.uint8)[index]
        np.testing.assert_array_equal(decoder.predict(m.syndrome(state)), m.observables(state))
    problem = Problem(m, PhenomenologicalNoise(m), decoder)
    result = exact(problem, {"data": 0.1, "measurement": 0.02})
    assert 0 < result.estimate < 1
    for state in product((0, 1), repeat=m.n):
        direct_prediction = m.code.lz @ matching.decode(m.syndrome(state).T) % 2
        assert problem.is_faulty(state) == bool(np.any(direct_prediction != m.observables(state)))


def test_real_bposd_spacetime_round_major_flat():
    ldpc = pytest.importorskip("ldpc")
    m = model()
    basis = np.eye(m.n, dtype=np.uint8)
    check = np.stack([m.syndrome(row).reshape(-1) for row in basis], axis=1)
    logical = np.stack([m.observables(row) for row in basis], axis=1)
    bposd = ldpc.BpOsdDecoder(check, error_rate=0.1, max_iter=20, osd_method="OSD_0", osd_order=0)
    inner = DecoderAdapter(bposd, output_kind="correction", logical_map=logical,
                           identifier="spacetime-bposd", distribution="ldpc")
    decoder = HistoryDecoder(inner, layout="round_major_flat", identifier="flatten-all")
    for state in basis:
        np.testing.assert_array_equal(decoder.predict(m.syndrome(state)), m.observables(state))
    problem = Problem(m, PhenomenologicalNoise(m), decoder)
    result = exact(problem, {"data": 0.1, "measurement": 0.02})
    assert 0 < result.estimate < 1
    for state in product((0, 1), repeat=m.n):
        direct_prediction = logical @ bposd.decode(m.syndrome(state).reshape(-1)) % 2
        assert problem.is_faulty(state) == bool(np.any(direct_prediction != m.observables(state)))
