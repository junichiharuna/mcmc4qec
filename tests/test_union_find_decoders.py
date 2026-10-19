"""Finite acceptance for version-scoped, syndrome-checked Union-Find."""
import builtins
import importlib.metadata

import numpy as np
import pytest

from mcmc4qec.codes import make_steane_code, make_surface_code, make_toric_code
from mcmc4qec.core import CSSCode
from mcmc4qec import union_find_decoders as uf


def _backend():
    backend = pytest.importorskip("ldpc")
    pytest.importorskip("bposd")
    if importlib.metadata.version("ldpc") != "2.4.1":
        pytest.skip("native acceptance is scoped to ldpc 2.4.1")
    return backend


def _syndromes(checks):
    found = {tuple(np.zeros(checks.shape[0], dtype=np.uint8))}
    for column in checks.T:
        found |= {tuple(np.array(s, dtype=np.uint8) ^ column) for s in found}
    return [np.array(s, dtype=np.uint8) for s in sorted(found)]


@pytest.mark.parametrize("make_code", [lambda: make_toric_code(2), lambda: make_surface_code(2)])
@pytest.mark.parametrize("method", ["peeling", "inversion"])
@pytest.mark.parametrize("errors", ["X", "Z"])
def test_all_small_graphlike_syndromes_repeat_reverse_fresh(make_code, method, errors):
    backend = _backend()
    code = make_code()
    h, logical = (code.hz, code.lz) if errors == "X" else (code.hx, code.lx)
    raw = backend.UnionFindDecoder(h, uf_method="" if method == "peeling" else "inversion")
    wrapped = uf.union_find_decoder(code, errors=errors, method=method)
    syndromes = _syndromes(h)
    expected = []
    physical = []
    for syndrome in syndromes:
        correction = np.asarray(raw.decode(syndrome, bits_per_step=1), dtype=np.uint8)
        np.testing.assert_array_equal(h @ correction % 2, syndrome)
        expected.append(logical @ correction % 2)
        physical.append(correction.copy())
        np.testing.assert_array_equal(wrapped.predict(syndrome), expected[-1])
    for decoder, order in [(wrapped, range(len(syndromes))),
                           (wrapped, reversed(range(len(syndromes)))),
                           (uf.union_find_decoder(code, errors=errors, method=method), range(len(syndromes)))]:
        for i in order:
            np.testing.assert_array_equal(decoder.predict(syndromes[i]), expected[i])
            np.testing.assert_array_equal(decoder.decoder.decode(syndromes[i], bits_per_step=1), physical[i])


def test_boundary_degree_one_accepts_odd_syndrome():
    _backend()
    code = make_surface_code(2)
    assert np.any(code.hz.sum(axis=0) == 1)
    decoder = uf.union_find_decoder(code)
    for syndrome in _syndromes(code.hz):
        decoder.predict(syndrome)
    assert any(s.sum() % 2 for s in _syndromes(code.hz))


@pytest.mark.parametrize("errors", ["X", "Z"])
def test_inversion_general_css_all_syndromes(errors):
    _backend()
    code = make_steane_code()
    decoder = uf.union_find_decoder(code, errors=errors, method="inversion")
    checks = code.hz if errors == "X" else code.hx
    for syndrome in _syndromes(checks):
        prediction = decoder.predict(syndrome)
        np.testing.assert_array_equal(decoder.predict(syndrome), prediction)


@pytest.mark.parametrize("method", ["peeling", "inversion"])
def test_depolarizing_all_sector_pairs_and_metadata(method):
    _backend()
    code = make_surface_code(2)
    decoder = uf.depolarizing_union_find_decoder(code, method=method)
    x = uf.union_find_decoder(code, method=method)
    z = uf.union_find_decoder(code, errors="Z", method=method)
    for sx in _syndromes(code.hz):
        for sz in _syndromes(code.hx):
            np.testing.assert_array_equal(decoder.predict(np.r_[sx, sz]), np.r_[x.predict(sx), z.predict(sz)])
    assert decoder.metadata()["approximation"]["noise_y_correlations_preserved"] is True
    meta = x.metadata()
    assert meta["settings"]["method"] == method
    assert meta["settings"]["native_uf_method"] == ("" if method == "peeling" else "inversion")
    assert meta["settings"]["compatibility"] == "ldpc-2.4.1-str-to-bool"
    assert meta["settings"]["growth"] == "all-adjacent-unweighted"
    assert meta["decode_kwargs"] == {"bits_per_step": 1}
    assert meta["syndrome_consistency_checked"] is True
    assert meta["version"] == "2.4.1"


@pytest.mark.parametrize("method", ["bad", "", True, [], None])
def test_invalid_method(method):
    with pytest.raises(ValueError, match="method"):
        uf.union_find_decoder(make_steane_code(), method=method)


@pytest.mark.parametrize("bits", [0, 2, -1, True, np.bool_(True), 1.0, 2**32, None])
def test_unsupported_growth_parameter(bits):
    with pytest.raises(ValueError, match="bits_per_step"):
        uf.union_find_decoder(make_steane_code(), bits_per_step=bits)


def test_code_and_sector_validation():
    with pytest.raises(TypeError, match="CSSCode"):
        uf.union_find_decoder(None)
    with pytest.raises(TypeError, match="CSSCode"):
        uf.depolarizing_union_find_decoder(None)
    with pytest.raises(ValueError, match="errors"):
        uf.union_find_decoder(make_steane_code(), errors="Y", method="inversion")


def test_hyperedges_rejected_before_backend(monkeypatch):
    monkeypatch.setattr(uf, "_backend", lambda: pytest.fail("backend reached"))
    with pytest.raises(ValueError, match="column degree"):
        uf.union_find_decoder(make_steane_code())


@pytest.mark.parametrize("method", ["peeling", "inversion"])
def test_zero_degree_rejected_before_backend(monkeypatch, method):
    code = CSSCode(np.zeros((0, 1), dtype=np.uint8), np.zeros((0, 1), dtype=np.uint8), [[1]], [[1]])
    monkeypatch.setattr(uf, "_backend", lambda: pytest.fail("backend reached"))
    with pytest.raises(ValueError, match="zero-degree"):
        uf.union_find_decoder(code, method=method)


@pytest.mark.parametrize("version", ["2.4.0", "2.4.2", "3.0.0", "2.4.1+modified"])
def test_unknown_version_fails_before_native(monkeypatch, version):
    backend = _backend()
    monkeypatch.setattr(uf, "version", lambda name: version)
    monkeypatch.setattr(backend, "UnionFindDecoder", lambda *a, **k: pytest.fail("native reached"))
    with pytest.raises(RuntimeError, match="verified only.*2.4.1"):
        uf.union_find_decoder(make_toric_code(2))


def test_optional_dependency_missing(monkeypatch):
    original = builtins.__import__

    def no_ldpc(name, *args, **kwargs):
        if name == "ldpc":
            raise ImportError("test missing ldpc")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_ldpc)
    with pytest.raises(ImportError, match="mcmc4qec"):
        uf.union_find_decoder(make_steane_code(), method="inversion")


@pytest.mark.parametrize("syndrome", [[1, 0, 0, 0], [0], [[0, 0, 0, 0]], [0, 0, 0, 2]])
def test_invalid_or_unrealizable_syndrome(syndrome):
    _backend()
    decoder = uf.union_find_decoder(make_toric_code(2))
    with pytest.raises(ValueError):
        decoder.predict(syndrome)


def test_native_exception_not_retried(monkeypatch):
    backend = _backend()
    calls = []

    def fail(*args, **kwargs):
        calls.append(kwargs)
        raise TypeError("native failure")

    monkeypatch.setattr(backend, "UnionFindDecoder", fail)
    with pytest.raises(TypeError, match="native failure"):
        uf.union_find_decoder(make_toric_code(2))
    assert calls == [{"uf_method": ""}]
