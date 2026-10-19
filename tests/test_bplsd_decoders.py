"""BP-LSD physical correction, fixed prior and small-code acceptance."""
import builtins
import itertools
import json

import numpy as np
import pytest

from mcmc4qec import codes
from mcmc4qec.bplsd_decoders import bplsd_decoder, depolarizing_bplsd_decoder


@pytest.mark.parametrize("errors", ["X", "Z"])
@pytest.mark.parametrize("method,order", [("lsd_0", 0), ("lsd_cs", 0), ("lsd_e", 0)])
def test_steane_all_errors_native_recipe_and_reproducibility(errors, method, order):
    ldpc = pytest.importorskip("ldpc")
    code = codes.make_steane_code()
    h, logical = (code.hz, code.lz) if errors == "X" else (code.hx, code.lx)
    options = dict(lsd_method=method, lsd_order=order, always_run_lsd=True)
    decoder = bplsd_decoder(code, .08, errors=errors, **options)
    reference = ldpc.BpLsdDecoder(h, **decoder.metadata()["settings"])
    syndromes = np.unique(np.array(list(itertools.product([0, 1], repeat=7)), dtype=np.uint8) @ h.T % 2, axis=0)
    expected = []
    for syndrome in syndromes:
        correction = reference.decode(syndrome) if np.any(syndrome) else np.zeros(code.n, dtype=np.uint8)
        np.testing.assert_array_equal(h @ correction % 2, syndrome)
        expected.append(logical @ correction % 2)
    for obj, inputs, outputs in ((decoder, syndromes, expected),
                                (decoder, syndromes[::-1], expected[::-1]),
                                (bplsd_decoder(code, .08, errors=errors, **options), syndromes, expected)):
        for syndrome, prediction in zip(inputs, outputs):
            np.testing.assert_array_equal(obj.predict(syndrome), prediction)


def test_depolarizing_matches_separate_sectors_and_fixed_prior():
    pytest.importorskip("ldpc")
    code = codes.make_steane_code()
    decoder = depolarizing_bplsd_decoder(code, .02)
    x, z = bplsd_decoder(code, .02), bplsd_decoder(code, .02, errors="Z")
    syndromes = [np.array(s, dtype=np.uint8) for s in itertools.product([0, 1], repeat=3)]
    before = json.dumps(decoder.metadata(), sort_keys=True)
    for sx, sz in itertools.product(syndromes, repeat=2):
        np.testing.assert_array_equal(decoder.predict(np.concatenate((sx, sz))),
                                      np.concatenate((x.predict(sx), z.predict(sz))))
    assert json.dumps(decoder.metadata(), sort_keys=True) == before
    assert x.metadata()["settings"]["error_rate"] == .02
    assert bplsd_decoder(code, .03).metadata() != x.metadata()


@pytest.mark.parametrize("factory", [lambda: codes.make_toric_code(2),
    lambda: codes.make_surface_code(3), codes.make_hgp_hamming, codes.make_bb_code_72,
    lambda: codes.make_tile_code(6, 6), lambda: codes.make_tile_code(12, 12)])
def test_other_codes_fixed_errors(factory):
    pytest.importorskip("ldpc")
    pytest.importorskip("bposd")
    code = factory()
    rng = np.random.default_rng(2026101811)
    states = np.vstack((np.zeros(code.n, dtype=np.uint8), np.eye(code.n, dtype=np.uint8)[[0, -1]],
                        (rng.random((3, code.n)) < .1).astype(np.uint8)))
    for errors, h in (("X", code.hz), ("Z", code.hx)):
        decoder = bplsd_decoder(code, .03, errors=errors)
        base = [decoder.predict(h @ state % 2) for state in states]
        fresh = bplsd_decoder(code, .03, errors=errors)
        for state, expected in zip(states[::-1], base[::-1]):
            np.testing.assert_array_equal(decoder.predict(h @ state % 2), expected)
            np.testing.assert_array_equal(fresh.predict(h @ state % 2), expected)


@pytest.mark.parametrize("options", [dict(error_rate=.1), dict(error_channel=[.1]*7),
    dict(schedule="serial"), dict(random_schedule_seed=3), dict(typo=1),
    dict(max_iter=True), dict(max_iter=0), dict(max_iter=2**40), dict(bits_per_step=0),
    dict(bits_per_step=8), dict(lsd_order=-1), dict(lsd_order=1), dict(lsd_order=2.0),
    dict(lsd_method="lsd_cs", lsd_order=5), dict(lsd_method="lsd_cs", lsd_order=1),
    dict(lsd_method="lsd_e", lsd_order=1), dict(lsd_method="off"),
    dict(ms_scaling_factor=np.nan), dict(ms_scaling_factor=-1), dict(ms_scaling_factor=True),
    dict(bp_method="bad"), dict(always_run_lsd=1)])
def test_bad_settings_rejected_before_native(options, monkeypatch):
    ldpc = pytest.importorskip("ldpc")
    monkeypatch.setattr(ldpc, "BpLsdDecoder", lambda *a, **kw: pytest.fail("native called"))
    with pytest.raises(ValueError):
        bplsd_decoder(codes.make_steane_code(), .1, **options)


@pytest.mark.parametrize("p", [0, 1, -.1, 1.1, True, np.nan, np.inf, [.1]])
def test_bad_prior(p):
    with pytest.raises(ValueError, match="prior"):
        bplsd_decoder(codes.make_steane_code(), p)


def test_metadata_defaults_and_numpy_scalars():
    pytest.importorskip("ldpc")
    decoder = bplsd_decoder(codes.make_steane_code(), np.float64(.1), max_iter=np.int64(10))
    settings = decoder.metadata()["settings"]
    assert settings == dict(error_rate=.1, max_iter=10, bp_method="minimum_sum",
        ms_scaling_factor=1., schedule="parallel", omp_thread_count=1,
        random_schedule_seed=0, random_serial_schedule=False, serial_schedule_order=None,
        input_vector_type="syndrome", lsd_method="lsd_0", lsd_order=0,
        bits_per_step=1, always_run_lsd=False)
    settings["error_rate"] = .2
    assert decoder.metadata()["settings"]["error_rate"] == .1


def test_missing_optional_dependency(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == "ldpc":
            raise ImportError("test missing dependency")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(ImportError, match="mcmc4qec\\[bposd\\]"):
        bplsd_decoder(codes.make_steane_code(), .1)


def test_invalid_code_and_sector():
    with pytest.raises(TypeError):
        bplsd_decoder(None, .1)
    with pytest.raises(ValueError, match="errors"):
        bplsd_decoder(codes.make_steane_code(), .1, errors="Y")


def test_zero_columns_and_redundant_zero_checks():
    pytest.importorskip("ldpc")
    from mcmc4qec import CSSCode
    code = CSSCode(np.zeros((0, 2), dtype=np.uint8), [[1, 0], [0, 0]],
                   [[0, 1]], [[0, 1]])
    decoder = bplsd_decoder(code, .1)
    np.testing.assert_array_equal(decoder.predict([1, 0]), [0])
    np.testing.assert_array_equal(decoder.predict([0, 0]), [0])
    with pytest.raises(ValueError, match="realizable"):
        decoder.predict([0, 1])


@pytest.mark.parametrize("p", [.1, .9])
def test_zero_syndrome_identity_rule_does_not_call_native(monkeypatch, p):
    ldpc = pytest.importorskip("ldpc")
    class Native:
        def decode(self, syndrome):
            pytest.fail("zero syndrome must not reach uninitialized native branch")
    monkeypatch.setattr(ldpc, "BpLsdDecoder", lambda *a, **kw: Native())
    decoder = bplsd_decoder(codes.make_steane_code(), p)
    np.testing.assert_array_equal(decoder.predict([0, 0, 0]), [0])
    assert decoder.metadata()["zero_syndrome_policy"] == "identity-before-native"


@pytest.mark.parametrize("errors", ["X", "Z"])
def test_full_state_failure_definition_and_sampling_integration(errors):
    ldpc = pytest.importorskip("ldpc")
    from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig, exact, sample_faulty
    code = codes.make_steane_code()
    decoder = bplsd_decoder(code, .08, errors=errors)
    model = code.bit_flip_model() if errors == "X" else code.phase_flip_model()
    problem = Problem(model, IndependentBitFlip(code.n), decoder)
    native = ldpc.BpLsdDecoder(model.H, **decoder.metadata()["settings"])
    probabilities = {p: 0. for p in (.08, .2)}
    for bits in itertools.product([0, 1], repeat=code.n):
        state = np.asarray(bits, dtype=np.uint8)
        syndrome = model.H @ state % 2
        correction = (native.decode(syndrome).astype(np.uint8) if np.any(syndrome)
                      else np.zeros(code.n, dtype=np.uint8))
        assert not np.any(model.H @ (state ^ correction) % 2)
        failure = bool(np.any(model.L @ (state ^ correction) % 2))
        assert problem.is_faulty(state) == failure
        for p in probabilities:
            probabilities[p] += failure * p**int(state.sum()) * (1-p)**(code.n-int(state.sum()))
    before = decoder.metadata()
    for p, expected in probabilities.items():
        assert exact(problem, p).estimate == pytest.approx(expected, abs=1e-14)
    initial = code.lx[0] if errors == "X" else code.lz[0]
    result = sample_faulty(problem, .2, config=SamplingConfig(samples=20, burn_in=5),
                           seed=2026101812, initial_state=initial)
    assert result.conditional_weight is not None
    assert decoder.metadata() == before
