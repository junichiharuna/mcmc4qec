import json

import numpy as np
import pytest

from rimc.adapters import DecoderAdapter, PyMatchingAdapter, matching_from_check_matrix


class RecordingDecoder:
    def __init__(self, output):
        self.output = output

    def decode(self, syndrome, **kwargs):
        self.syndrome = syndrome.copy()
        self.kwargs = kwargs
        return self.output


def test_correction_requires_explicit_mapping_and_preserves_history():
    decoder = RecordingDecoder([1, 0, 1])
    adapter = DecoderAdapter(decoder, output_kind="correction", logical_map=[[1, 1, 0]], identifier="test")
    history = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    np.testing.assert_array_equal(adapter.predict(history), [1])
    np.testing.assert_array_equal(decoder.syndrome, history)
    with pytest.raises(ValueError, match="logical_map"):
        DecoderAdapter(decoder, output_kind="correction", identifier="test")


def test_observable_is_not_remapped_by_length():
    adapter = DecoderAdapter(RecordingDecoder([1, 0, 1]), output_kind="observable", identifier="test")
    np.testing.assert_array_equal(adapter.predict([0]), [1, 0, 1])
    with pytest.raises(ValueError, match="logical_map"):
        DecoderAdapter(RecordingDecoder([1]), output_kind="observable", logical_map=[[1]], identifier="test")


@pytest.mark.parametrize("output", [[2], [0.1], [float("nan")], [[1]], "1", ["1"], [1j]])
def test_invalid_decoder_output_rejected(output):
    adapter = DecoderAdapter(RecordingDecoder(output), output_kind="observable", identifier="test")
    with pytest.raises(ValueError):
        adapter.predict([0])


def test_correction_length_and_binary_input_validation():
    adapter = DecoderAdapter(RecordingDecoder([1, 0]), output_kind="correction", logical_map=[[1]], identifier="test")
    with pytest.raises(ValueError, match="length"):
        adapter.predict([0])
    for syndrome in ([2], [float("nan")], [[[1]]], 1):
        with pytest.raises(ValueError):
            adapter.predict(syndrome)


def test_metadata_is_json_and_defensively_copied():
    settings = {"prior": 0.1, "nested": [1]}
    adapter = DecoderAdapter(RecordingDecoder([0]), output_kind="observable", identifier="fixed", settings=settings)
    settings["nested"].append(2)
    metadata = adapter.metadata()
    assert json.loads(json.dumps(metadata)) == metadata
    assert metadata["settings"]["nested"] == [1]
    metadata["settings"]["nested"].append(3)
    assert adapter.metadata()["settings"]["nested"] == [1]
    with pytest.raises(ValueError, match="JSON"):
        DecoderAdapter(RecordingDecoder([0]), output_kind="observable", identifier="fixed", settings={"prior": float("nan")})


@pytest.mark.parametrize("build,decode", [(True, False), (False, True)])
def test_correlation_settings_must_agree(build, decode):
    with pytest.raises(ValueError, match="correlation"):
        PyMatchingAdapter(RecordingDecoder([0]), output_kind="observable", identifier="test", built_with_correlations=build, decode_kwargs={"enable_correlations": decode})


def test_correlation_setting_is_forwarded_and_recorded():
    decoder = RecordingDecoder([0])
    adapter = PyMatchingAdapter(decoder, output_kind="observable", identifier="test", built_with_correlations=True)
    adapter.predict([0])
    assert decoder.kwargs == {"enable_correlations": True}
    assert adapter.metadata()["built_with_correlations"] is True


def test_hyperedge_rejected_before_import_or_construction():
    with pytest.raises(ValueError, match="degree"):
        matching_from_check_matrix([[1], [1], [1]], logical_map=[[1]], identifier="test")


def test_real_pymatching_repetition_code():
    pytest.importorskip("pymatching")
    adapter = matching_from_check_matrix([[1, 1, 0], [0, 1, 1]], logical_map=[[1, 1, 1]], identifier="rep3", weights=[1, 1, 1])
    np.testing.assert_array_equal(adapter.predict([1, 0]), [1])
    assert adapter.metadata()["version"] is not None


def test_matching_preserves_trailing_unobservable_fault_dimensions():
    pytest.importorskip("pymatching")
    adapter = matching_from_check_matrix([[1, 1, 0]], logical_map=[[0, 0, 1]], identifier="zero-column")
    np.testing.assert_array_equal(adapter.predict([0]), [0])


@pytest.mark.parametrize("mapping", [[1], [[2]], [[float("nan")]], [["1"]]])
def test_invalid_logical_map_rejected(mapping):
    with pytest.raises(ValueError, match="logical_map"):
        DecoderAdapter(RecordingDecoder([0]), output_kind="correction", logical_map=mapping, identifier="bad")


def test_decode_error_is_propagated():
    class Broken:
        def decode(self, syndrome):
            raise RuntimeError("failed to decode")
    adapter = DecoderAdapter(Broken(), output_kind="observable", identifier="broken")
    with pytest.raises(RuntimeError, match="failed to decode"):
        adapter.predict([0])


def test_real_bposd_object_without_special_wrapper():
    ldpc = pytest.importorskip("ldpc")
    pcm = np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    decoder = ldpc.BpOsdDecoder(pcm, error_rate=0.1, max_iter=10, osd_method="OSD_0", osd_order=0)
    adapter = DecoderAdapter(decoder, output_kind="correction", logical_map=[[1, 1, 1]], identifier="rep3-bposd", distribution="ldpc", settings={"error_rate": 0.1, "max_iter": 10, "osd_method": "OSD_0", "osd_order": 0})
    np.testing.assert_array_equal(adapter.predict([1, 0]), [1])
    assert adapter.metadata()["version"] is not None
