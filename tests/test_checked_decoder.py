"""Physical-correction contract, independent of optional native decoders."""
import numpy as np
import pytest

from mcmc4qec._checked_decoder import CheckedCorrectionAdapter


class Backend:
    def __init__(self, correction):
        self.correction = correction
        self.calls = 0

    def decode(self, syndrome, **kwargs):
        self.calls += 1
        syndrome[:] = 0  # The wrapper must retain its own input for Hc=s.
        return self.correction


def adapter(backend):
    return CheckedCorrectionAdapter(backend, check_matrix=[[1, 1, 0], [1, 1, 0]],
                                    logical_map=[[1, 0, 1]], identifier="test", settings={})


def test_physical_correction_and_input_are_checked_before_logical_mapping():
    backend = Backend([1, 0, 1])
    decoder = adapter(backend)
    syndrome = np.array([1, 1], dtype=np.uint8)
    np.testing.assert_array_equal(decoder.predict(syndrome), [0])
    np.testing.assert_array_equal(syndrome, [1, 1])
    assert backend.calls == 1


@pytest.mark.parametrize("syndrome", [[1, 0], [1], [[1, 1]], [2, 2], [np.nan, 0]])
def test_invalid_or_unrealizable_syndrome_never_calls_backend(syndrome):
    backend = Backend([0, 0, 0])
    with pytest.raises(ValueError):
        adapter(backend).predict(syndrome)
    assert backend.calls == 0


@pytest.mark.parametrize("correction", [[0, 0, 0], [1, 0], [[1, 0, 0]], [2, 0, 0], [np.nan, 0, 0]])
def test_invalid_correction_is_never_a_logical_prediction(correction):
    with pytest.raises(ValueError):
        adapter(Backend(correction)).predict([1, 1])


def test_metadata_and_matrices_are_copied():
    h = np.array([[1, 1]], dtype=np.uint8)
    decoder = CheckedCorrectionAdapter(Backend([1, 0]), check_matrix=h,
                                       logical_map=[[1, 0]], identifier="test", settings={"p": .1})
    h[:] = 0
    np.testing.assert_array_equal(decoder.predict([1]), [1])
    meta = decoder.metadata()
    assert meta["syndrome_consistency_checked"] is True
    assert meta["invalid_correction_policy"] == "raise"
    meta["check_matrix"][0][0] = 0
    assert decoder.metadata()["check_matrix"] == [[1, 1]]


def test_backend_exception_propagates():
    class Broken:
        def decode(self, syndrome):
            raise RuntimeError("native failed")
    with pytest.raises(RuntimeError, match="native failed"):
        adapter(Broken()).predict([1, 1])


def test_all_binary_syndromes_with_dependent_checks():
    h = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.uint8)
    for value in range(8):
        syndrome = np.array([(value >> bit) & 1 for bit in range(3)], dtype=np.uint8)
        backend = Backend(syndrome[:2].copy())
        decoder = CheckedCorrectionAdapter(backend, check_matrix=h, logical_map=[[1, 0]],
                                           identifier="test", settings={})
        if syndrome[2] == (syndrome[0] ^ syndrome[1]):
            np.testing.assert_array_equal(decoder.predict(syndrome), syndrome[:1])
            assert backend.calls == 1
        else:
            with pytest.raises(ValueError, match="realizable"):
                decoder.predict(syndrome)
            assert backend.calls == 0
