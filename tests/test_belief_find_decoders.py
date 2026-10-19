"""BeliefFind correction contract on complete small syndrome spaces."""
import builtins
import itertools
import sys
import types

import numpy as np
import pytest

from mcmc4qec.belief_find_decoders import (
    belief_find_decoder, depolarizing_belief_find_decoder,
)
from mcmc4qec.codes import (
    make_steane_code, make_toric_code, make_surface_code,
    make_hgp_hamming, make_bb_code_72, make_tile_code,
)
from mcmc4qec.core import CSSCode


def syndromes(h):
    found = {tuple(np.zeros(len(h), dtype=np.uint8))}
    for col in h.T:
        found |= {tuple(np.asarray(s, dtype=np.uint8) ^ col) for s in found}
    return [np.asarray(s, dtype=np.uint8) for s in sorted(found)]


@pytest.mark.parametrize("factory", [make_steane_code, lambda: make_toric_code(2)])
@pytest.mark.parametrize("errors", ["X", "Z"])
def test_all_syndromes_native_mapping_and_order_independence(factory, errors):
    ldpc = pytest.importorskip("ldpc")
    if factory is not make_steane_code:
        pytest.importorskip("bposd")
    code = factory()
    h, logical = (code.hz, code.lz) if errors == "X" else (code.hx, code.lx)
    adapter = belief_find_decoder(code, .07, errors=errors, max_iter=1)
    settings = adapter.metadata()["settings"].copy()
    settings.pop("random_serial_schedule")
    native = ldpc.BeliefFindDecoder(h, **settings)
    native.random_serial_schedule = False
    inputs = syndromes(h)
    expected = []
    uf_used = False
    for s in inputs:
        correction = native.decode(s)
        uf_used |= not native.converge
        np.testing.assert_array_equal(h @ correction % 2, s)
        expected.append(logical @ correction % 2)
    if factory is make_steane_code:
        assert uf_used  # Cover the UF branch rather than only BP convergence.
    fresh = belief_find_decoder(code, .07, errors=errors, max_iter=1)
    for decoder, order in [(adapter, range(len(inputs))), (adapter, reversed(range(len(inputs)))),
                           (fresh, range(len(inputs)))]:
        for i in order:
            np.testing.assert_array_equal(decoder.predict(inputs[i]), expected[i])
    assert adapter.decoder.random_serial_schedule is False


@pytest.mark.parametrize("factory", [lambda: make_toric_code(2), lambda: make_surface_code(2)])
@pytest.mark.parametrize("errors", ["X", "Z"])
def test_peeling_graphlike_all_syndromes(factory, errors):
    pytest.importorskip("ldpc")
    pytest.importorskip("bposd")
    code = factory()
    h = code.hz if errors == "X" else code.hx
    adapter = belief_find_decoder(code, .1, errors=errors, uf_method="peeling", max_iter=1)
    for s in syndromes(h):
        result = adapter.predict(s)
        assert result.shape == (len(code.lx),)
        np.testing.assert_array_equal(h @ adapter.decoder.decode(s) % 2, s)


def test_depolarizing_sector_prior_order_and_metadata():
    pytest.importorskip("ldpc")
    code = make_steane_code()
    decoder = depolarizing_belief_find_decoder(code, .02, max_iter=1)
    x = belief_find_decoder(code, .02, errors="X", max_iter=1)
    z = belief_find_decoder(code, .02, errors="Z", max_iter=1)
    for sx, sz in itertools.product(syndromes(code.hz), syndromes(code.hx)):
        np.testing.assert_array_equal(decoder.predict(np.concatenate([sx, sz])),
                                      np.concatenate([x.predict(sx), z.predict(sz)]))
    meta = decoder.metadata()
    assert meta["x_decoder"]["settings"]["error_rate"] == .02
    assert meta["z_decoder"]["settings"]["error_rate"] == .02
    assert meta["approximation"]["noise_y_correlations_preserved"] is True


@pytest.mark.parametrize("p", [0, 1, -1, float("nan"), float("inf"), True, "0.1"])
def test_invalid_prior_before_native(monkeypatch, p):
    monkeypatch.setitem(sys.modules, "ldpc", types.SimpleNamespace())
    with pytest.raises(ValueError, match="p"):
        belief_find_decoder(make_steane_code(), p)


@pytest.mark.parametrize("kw", [
    {"error_rate": .1}, {"error_channel": [.1]*7}, {"unknown": 1},
    {"max_iter": True}, {"max_iter": 0}, {"max_iter": 2**40},
    {"bits_per_step": 0}, {"bits_per_step": 8}, {"bits_per_step": 1.2},
    {"bp_method": "bad"}, {"bp_method": []}, {"uf_method": "bad"},
    {"ms_scaling_factor": float("nan")}, {"ms_scaling_factor": -.1},
    {"ms_scaling_factor": True}, {"schedule": "serial"},
    {"omp_thread_count": 2}, {"omp_thread_count": True},
    {"random_schedule_seed": 1}, {"random_serial_schedule": True},
    {"serial_schedule_order": list(range(7))}, {"input_vector_type": "auto"},
])
def test_invalid_options_before_native(monkeypatch, kw):
    monkeypatch.setitem(sys.modules, "ldpc", types.SimpleNamespace())
    with pytest.raises(ValueError):
        belief_find_decoder(make_steane_code(), .1, **kw)


def test_hyperedge_peeling_and_zero_column_both_modes_rejected_before_native(monkeypatch):
    monkeypatch.setitem(sys.modules, "ldpc", types.SimpleNamespace())
    with pytest.raises(ValueError, match="degree"):
        belief_find_decoder(make_steane_code(), .1, uf_method="peeling")
    code = CSSCode(np.zeros((0, 4), dtype=np.uint8), [[1,1,0,0],[0,1,1,0]],
                   [[1,1,1,0],[0,0,0,1]], [[1,0,0,0],[0,0,0,1]])
    for method in ("inversion", "peeling"):
        with pytest.raises(ValueError, match="zero-degree"):
            belief_find_decoder(code, .1, uf_method=method)


def test_optional_missing_is_informative(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == "ldpc":
            raise ImportError("deliberately unavailable")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(ImportError, match=r"mcmc4qec\[bposd\]"):
        belief_find_decoder(make_steane_code(), .1)


def test_native_bad_correction_raises_instead_of_logical_success(monkeypatch):
    class Bad:
        def __init__(self, h, **kw):
            self.h = h
        def decode(self, syndrome):
            return np.zeros(self.h.shape[1], dtype=np.uint8)
    monkeypatch.setitem(sys.modules, "ldpc", types.SimpleNamespace(BeliefFindDecoder=Bad))
    code = make_steane_code()
    decoder = belief_find_decoder(code, .1)
    with pytest.raises(ValueError, match="Hc != s"):
        decoder.predict(code.hz[:, 0])
    with pytest.raises(ValueError, match="length"):
        decoder.predict([1])


def test_settings_defaults_and_alias_are_explicit():
    pytest.importorskip("ldpc")
    decoder = belief_find_decoder(make_steane_code(), .1, bp_method="minimum_sum")
    settings = decoder.metadata()["settings"]
    assert settings == dict(error_rate=.1, max_iter=100, bp_method="min_sum",
        ms_scaling_factor=1., schedule="parallel", omp_thread_count=1,
        random_schedule_seed=0, serial_schedule_order=None,
        random_serial_schedule=False, input_vector_type="syndrome",
        uf_method="inversion", bits_per_step=1)


@pytest.mark.parametrize("errors", ["Y", "x", None, [], 1])
def test_invalid_sector_before_native(monkeypatch, errors):
    monkeypatch.setitem(sys.modules, "ldpc", types.SimpleNamespace())
    with pytest.raises(ValueError, match="errors"):
        belief_find_decoder(make_steane_code(), .1, errors=errors)


def test_invalid_code_and_second_sector_rejected_before_native(monkeypatch):
    monkeypatch.setitem(sys.modules, "ldpc", types.SimpleNamespace())
    for factory in (belief_find_decoder, depolarizing_belief_find_decoder):
        with pytest.raises(TypeError, match="CSSCode"):
            factory(object(), .1)
    # X checks have zero columns, while Z checks do not: validate the second
    # sector before constructing the first native object.
    code = CSSCode(np.zeros((0, 3), dtype=np.uint8), [[1,1,0],[0,1,1]],
                   [[1,1,1]], [[1,0,0]])
    with pytest.raises(ValueError, match="zero-degree"):
        depolarizing_belief_find_decoder(code, .1)


@pytest.mark.parametrize("method", ["min_sum", "product_sum"])
def test_options_applied_to_native(method):
    pytest.importorskip("ldpc")
    decoder = belief_find_decoder(make_steane_code(), .3, max_iter=2,
        bp_method=method, ms_scaling_factor=.5, bits_per_step=7)
    assert decoder.decoder.max_iter == 2
    assert decoder.decoder.ms_scaling_factor == .5
    np.testing.assert_allclose(decoder.decoder.channel_probs, .3)
    for s in syndromes(make_steane_code().hz):
        decoder.predict(s)


@pytest.mark.parametrize("factory", [make_hgp_hamming, make_bb_code_72,
    lambda: make_tile_code(6, 6), lambda: make_tile_code(12, 12)])
@pytest.mark.parametrize("errors", ["X", "Z"])
def test_general_css_representative_syndromes(factory, errors):
    pytest.importorskip("ldpc")
    if factory is make_hgp_hamming:
        pytest.importorskip("bposd")
    code = factory()
    h = code.hz if errors == "X" else code.hx
    decoder = belief_find_decoder(code, .05, errors=errors, max_iter=1)
    rng = np.random.default_rng(20261018)
    for state in [np.zeros(code.n, dtype=np.uint8),
                  np.eye(1, code.n, dtype=np.uint8)[0],
                  (rng.random(code.n) < .05).astype(np.uint8)]:
        s = h @ state % 2
        prediction = decoder.predict(s)
        assert prediction.shape == (len(code.lx),)
        np.testing.assert_array_equal(h @ decoder.decoder.decode(s) % 2, s)
