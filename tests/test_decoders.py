"""Research decoder recipes compared on every realizable small-code syndrome."""
import numpy as np
import pytest

from mcmc4qec.codes import make_steane_code, make_toric_code
from mcmc4qec.decoders import (
    bposd_decoder, depolarizing_bposd_decoder, depolarizing_mwpm_decoder,
    mwpm_decoder,
)


def _syndromes(checks):
    """Deduplicate actual syndromes rather than assume independent check rows."""
    found = {tuple(np.zeros(checks.shape[0], dtype=np.uint8))}
    for column in checks.T:
        found |= {tuple(np.asarray(s, dtype=np.uint8) ^ column) for s in found}
    return [np.asarray(s, dtype=np.uint8) for s in sorted(found)]


@pytest.mark.parametrize("factory", [lambda: make_toric_code(2), lambda: make_toric_code(3)])
def test_mwpm_all_syndromes_match_research_recipe(factory):
    pymatching = pytest.importorskip("pymatching")
    pytest.importorskip("bposd")
    code = factory()
    reference = pymatching.Matching(code.hz)
    decoder = mwpm_decoder(code)
    for syndrome in _syndromes(code.hz):
        correction = reference.decode(syndrome)
        assert np.array_equal(decoder.predict(syndrome), code.lz @ correction % 2)
        assert np.array_equal(code.hz @ correction % 2, syndrome)


def test_bposd_all_syndromes_match_research_recipe():
    ldpc = pytest.importorskip("ldpc")
    pytest.importorskip("bposd")
    code = make_toric_code(3)
    p = 0.05
    reference = ldpc.BpOsdDecoder(code.hz, error_rate=p, max_iter=100,
                                   bp_method="min_sum", osd_method="osd_cs",
                                   osd_order=10)
    decoder = bposd_decoder(code, p)
    for syndrome in _syndromes(code.hz):
        correction = reference.decode(syndrome).astype(np.uint8)
        assert np.array_equal(decoder.predict(syndrome), code.lz @ correction % 2)
        assert np.array_equal(code.hz @ correction % 2, syndrome)


@pytest.mark.parametrize("factory", [lambda: make_toric_code(2), lambda: make_toric_code(3)])
def test_depolarizing_sector_mwpm_all_syndromes(factory):
    pymatching = pytest.importorskip("pymatching")
    pytest.importorskip("bposd")
    code = factory()
    x_reference = pymatching.Matching(code.hz)
    z_reference = pymatching.Matching(code.hx)
    decoder = depolarizing_mwpm_decoder(code)
    for x_syndrome in _syndromes(code.hz):
        for z_syndrome in _syndromes(code.hx):
            expected = np.concatenate((code.lz @ x_reference.decode(x_syndrome) % 2,
                                       code.lx @ z_reference.decode(z_syndrome) % 2))
            actual = decoder.predict(np.concatenate((x_syndrome, z_syndrome)))
            assert np.array_equal(actual, expected)


def test_depolarizing_sector_bposd_all_syndromes():
    ldpc = pytest.importorskip("ldpc")
    pytest.importorskip("bposd")
    code = make_toric_code(3)
    p = 0.05
    settings = dict(error_rate=p, max_iter=100, bp_method="min_sum",
                    osd_method="osd_cs", osd_order=10)
    x_reference = ldpc.BpOsdDecoder(code.hz, **settings)
    z_reference = ldpc.BpOsdDecoder(code.hx, **settings)
    decoder = depolarizing_bposd_decoder(code, p)
    for x_syndrome in _syndromes(code.hz):
        z_syndrome = np.zeros(len(code.hx), dtype=np.uint8)
        expected = np.concatenate((code.lz @ x_reference.decode(x_syndrome) % 2,
                                   code.lx @ z_reference.decode(z_syndrome) % 2))
        assert np.array_equal(decoder.predict(np.concatenate((x_syndrome, z_syndrome))), expected)
    for z_syndrome in _syndromes(code.hx):
        x_syndrome = np.zeros(len(code.hz), dtype=np.uint8)
        expected = np.concatenate((code.lz @ x_reference.decode(x_syndrome) % 2,
                                   code.lx @ z_reference.decode(z_syndrome) % 2))
        assert np.array_equal(decoder.predict(np.concatenate((x_syndrome, z_syndrome))), expected)


def test_mwpm_rejects_hyperedge_columns():
    from mcmc4qec.codes import make_hgp_hamming
    pytest.importorskip("pymatching")
    pytest.importorskip("bposd")
    with pytest.raises(ValueError, match="column degree"):
        mwpm_decoder(make_hgp_hamming())


def test_bposd_settings_are_explicit():
    pytest.importorskip("ldpc")
    code = make_steane_code()
    decoder = bposd_decoder(code, 0.05, osd_order=2)
    assert decoder.metadata()["settings"]["osd_order"] == 2
    with pytest.raises(ValueError, match="error_rate"):
        bposd_decoder(code, 0.05, error_rate=0.1)
    with pytest.raises(ValueError, match="nullity"):
        bposd_decoder(code, 0.05)


@pytest.mark.parametrize("order", [10, np.int64(10)])
def test_bposd_unsafe_order_rejected_before_native_constructor(order, monkeypatch):
    ldpc = pytest.importorskip("ldpc")
    code = make_steane_code()
    monkeypatch.setattr(ldpc, "BpOsdDecoder", lambda *args, **kwargs: pytest.fail("native constructor called"))
    with pytest.raises(ValueError, match="nullity"):
        bposd_decoder(code, 0.05, osd_order=order)


def test_bposd_numpy_integer_order_is_normalized_before_native_constructor(monkeypatch):
    ldpc = pytest.importorskip("ldpc")
    seen = {}

    class FakeDecoder:
        def decode(self, syndrome):
            return np.zeros(7, dtype=np.uint8)

    def constructor(*args, **kwargs):
        seen.update(kwargs)
        return FakeDecoder()

    monkeypatch.setattr(ldpc, "BpOsdDecoder", constructor)
    decoder = bposd_decoder(make_steane_code(), np.float64(0.05),
                            osd_order=np.int64(2))
    assert type(seen["osd_order"]) is int
    assert decoder.metadata()["settings"]["osd_order"] == 2


@pytest.mark.parametrize("order", [True, 2.0, -1])
def test_bposd_noninteger_order_rejected(order):
    with pytest.raises(ValueError, match="osd_order"):
        bposd_decoder(make_steane_code(), 0.05, osd_order=order)


@pytest.mark.parametrize("prior", [True, np.bool_(False), -0.1, 1.1, np.nan, np.inf, [0.1]])
def test_bposd_prior_validation(prior):
    with pytest.raises(ValueError, match="decoder prior"):
        bposd_decoder(make_steane_code(), prior, osd_order=2)
