"""Static Z-sector model, decoder, and bounded phase-fault acceptance tests."""
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import mcmc4qec

from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip, KernelConfig,
                       PhenomenologicalModel, PhenomenologicalNoise, Problem,
                       SamplingConfig, exact, sample_faulty)
from mcmc4qec.codes import (make_bb_code_72, make_hgp_hamming,
                            make_steane_code, make_toric_code,
                            make_asymmetric_toric_code)
from mcmc4qec.decoders import bposd_decoder, mwpm_decoder
from mcmc4qec.fastpath import _probability_rows
from mcmc4qec.initial_states import minimum_weight_initial_state
from mcmc4qec.kernels import Zanella


def repetition3():
    return CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
                   [[1, 1, 1]], [[1, 0, 0]])


def dual(code):
    return CSSCode(code.hz, code.hx, code.lz, code.lx,
                   logical_basis=code.logical_basis)


@pytest.mark.parametrize("factory", [repetition3, make_steane_code,
                                     make_hgp_hamming, make_bb_code_72])
def test_phase_model_is_dual_bit_model(factory):
    if factory in (make_hgp_hamming,):
        pytest.importorskip("ldpc")
        pytest.importorskip("bposd")
    code = factory()
    phase = code.phase_flip_model()
    reference = dual(code).bit_flip_model()
    assert phase.identifier == "css-phase-flip"
    assert np.array_equal(phase.H, code.hx)
    assert np.array_equal(phase.L, code.lx)
    assert np.array_equal(phase.stabilizers, code.hz)
    for name in ("H", "L", "stabilizers"):
        np.testing.assert_array_equal(getattr(phase, name), getattr(reference, name))
    for state in [np.zeros(code.n, dtype=np.uint8), np.ones(code.n, dtype=np.uint8),
                  np.arange(code.n, dtype=np.uint8) % 2]:
        np.testing.assert_array_equal(phase.syndrome(state), reference.syndrome(state))
        np.testing.assert_array_equal(phase.observables(state), reference.observables(state))


def test_binary_sector_all_states_and_exact_duality():
    code = repetition3()
    phase, reference = code.phase_flip_model(), dual(code).bit_flip_model()
    decoder = CallableDecoder(lambda syndrome: [0], identifier="zero")
    phase_problem = Problem(phase, IndependentBitFlip(code.n), decoder)
    dual_problem = Problem(reference, IndependentBitFlip(code.n), decoder)
    for bits in product((0, 1), repeat=code.n):
        for row in code.hz:
            shifted = np.asarray(bits, dtype=np.uint8) ^ row
            np.testing.assert_array_equal(phase.syndrome(shifted), phase.syndrome(bits))
            np.testing.assert_array_equal(phase.observables(shifted), phase.observables(bits))
        assert phase_problem.is_faulty(bits) == dual_problem.is_faulty(bits)
    got, expected = exact(phase_problem, .13), exact(dual_problem, .13)
    assert got.estimate == pytest.approx(expected.estimate)
    assert got.conditional_weight == pytest.approx(expected.conditional_weight)


def test_repetition_code_has_distinct_x_and_z_failure_rates():
    code = repetition3()
    assert code.bit_flip_model().syndrome([1, 0, 0]).tolist() == [1, 0]
    assert code.phase_flip_model().syndrome([1, 0, 0]).tolist() == []
    x_decoder = CallableDecoder(lambda syndrome: [int(tuple(syndrome) == (1, 0))],
                                identifier="minimum-weight-x")
    z_decoder = CallableDecoder(lambda syndrome: [0], identifier="zero-z")
    p = .13
    x = exact(Problem(code.bit_flip_model(), IndependentBitFlip(3), x_decoder), p)
    z = exact(Problem(code.phase_flip_model(), IndependentBitFlip(3), z_decoder), p)
    assert x.estimate == pytest.approx(3 * p**2 - 2 * p**3)
    assert z.estimate == pytest.approx(3 * p * (1-p)**2 + p**3)
    assert x.estimate != pytest.approx(z.estimate)


def test_asymmetric_toric_phase_exact_equals_dual_bit_exact():
    pytest.importorskip("pymatching")
    pytest.importorskip("bposd")
    code = make_asymmetric_toric_code(2, 3)
    dual_code = dual(code)
    assert not np.array_equal(code.hx, code.hz)
    phase = Problem(code.phase_flip_model(), IndependentBitFlip(code.n),
                    mwpm_decoder(code, errors="Z"))
    reference = Problem(dual_code.bit_flip_model(), IndependentBitFlip(code.n),
                        mwpm_decoder(dual_code))
    got, expected = exact(phase, .13), exact(reference, .13)
    assert got.estimate == pytest.approx(expected.estimate, abs=1e-12)
    assert got.conditional_weight == pytest.approx(expected.conditional_weight, abs=1e-12)


def test_z_decoder_selection_validation_and_existing_identifier():
    pymatching = pytest.importorskip("pymatching")
    pytest.importorskip("bposd")
    code = make_toric_code(2)
    x = mwpm_decoder(code)
    z = mwpm_decoder(code, errors="Z")
    assert x.metadata()["identifier"] == "mwpm-css-x"
    assert z.metadata()["identifier"] == "mwpm-css-z"
    reference = pymatching.Matching(code.hx)
    syndromes = {tuple(np.zeros(len(code.hx), dtype=np.uint8))}
    for column in code.hx.T:
        syndromes |= {tuple(np.asarray(s, dtype=np.uint8) ^ column) for s in syndromes}
    for bits in syndromes:
        syndrome = np.asarray(bits, dtype=np.uint8)
        np.testing.assert_array_equal(z.predict(syndrome), code.lx @ reference.decode(syndrome) % 2)
    for invalid in ("x", "Y", "", None):
        with pytest.raises(ValueError, match="errors"):
            mwpm_decoder(code, errors=invalid)
        with pytest.raises(ValueError, match="errors"):
            bposd_decoder(code, .1, errors=invalid)


def test_z_bposd_identifier_and_default_unchanged():
    pytest.importorskip("ldpc")
    code = make_steane_code()
    x = bposd_decoder(code, .1, osd_order=2)
    z = bposd_decoder(code, .1, errors="Z", osd_order=2)
    assert x.metadata()["identifier"] == "bposd-css-x"
    assert z.metadata()["identifier"] == "bposd-css-z"


def test_z_bposd_predictions_use_x_checks_on_nonselfdual_code():
    ldpc = pytest.importorskip("ldpc")
    code = dual(repetition3())
    reference = ldpc.BpOsdDecoder(code.hx, error_rate=.1, max_iter=100,
                                  bp_method="min_sum", osd_method="osd_cs",
                                  osd_order=1)
    decoder = bposd_decoder(code, .1, errors="Z", osd_order=1)
    for bits in product((0, 1), repeat=len(code.hx)):
        syndrome = np.asarray(bits, dtype=np.uint8)
        expected = code.lx @ reference.decode(syndrome) % 2
        np.testing.assert_array_equal(decoder.predict(syndrome), expected)


@pytest.mark.parametrize("representation", ["history", "difference"])
def test_phenomenological_phase_flip_binary_and_dual(representation):
    code = dual(repetition3())
    options = dict(initial_boundary="clean", final_boundary="noisy",
                   representation=representation, data_noise="phase_flip")
    phase = PhenomenologicalModel(code, 2, **options)
    reference = PhenomenologicalModel(dual(code), 2,
        **{**options, "data_noise": "bit_flip"})
    assert phase.n_checks == len(code.hx) == 2
    assert phase.alphabets == (2,) * phase.n
    assert phase.metadata()["data_noise"] == "phase_flip"
    assert phase.metadata()["n_checks"] == phase.n_checks
    for bits in product((0, 1), repeat=phase.n):
        np.testing.assert_array_equal(phase.syndrome(bits), reference.syndrome(bits))
        np.testing.assert_array_equal(phase.observables(bits), reference.observables(bits))
        p = {"data": .2, "measurement": .3}
        assert PhenomenologicalNoise(phase).log_prob(bits, p) == pytest.approx(
            PhenomenologicalNoise(reference).log_prob(bits, p))


def test_phenomenological_phase_flip_check_history_and_fastpath():
    code = dual(repetition3())
    model = PhenomenologicalModel(code, 1, initial_boundary="clean",
        final_boundary="noisy", representation="history", data_noise="phase_flip")
    noise = PhenomenologicalNoise(model)
    p = {"data": .2, "measurement": .3}
    assert model.n_checks == len(code.hx)
    assert model.alphabets == (2,) * model.n
    rows = _probability_rows(noise, p)
    np.testing.assert_allclose(rows[:model.n_data, :2], [[.8, .2]] * model.n_data)
    np.testing.assert_allclose(rows[model.n_data:, :2], [[.7, .3]] * model.n_measurement)
    np.testing.assert_array_equal(rows[:, 2:], 0)
    decoder = CallableDecoder(lambda syndrome: np.zeros(len(code.lx), dtype=np.uint8),
                              identifier="zero")
    problem = Problem(model, noise, decoder)
    total = 0.0
    for bits in product((0, 1), repeat=model.n):
        state = np.asarray(bits, dtype=np.uint8)
        total += np.exp(noise.log_prob(state, p))
        np.testing.assert_allclose(Zanella()._distribution(state, problem, p),
                                   Zanella(use_fastpath=False)._distribution(state, problem, p), atol=1e-14)
    assert total == pytest.approx(1)
    initial = np.zeros(model.n, dtype=np.uint8)
    initial[0] = 1
    assert problem.is_faulty(initial)
    def run(enabled):
        return sample_faulty(problem, p, initial_state=initial, seed=933,
            config=SamplingConfig(samples=100, burn_in=10,
                kernels=KernelConfig(zanella=1, cluster=0, lazy=0,
                                     zanella_fastpath=enabled)))
    fast, reference = run(True), run(False)
    np.testing.assert_array_equal(fast.states, reference.states)
    assert fast.acceptance == reference.acceptance


def test_z_coset_initializer_is_faulty_and_chain_targets_exact_weight():
    code = dual(repetition3())
    state = minimum_weight_initial_state(code, sector="z")
    decoder = CallableDecoder(lambda syndrome: [int(tuple(syndrome) == (1, 0))],
                              identifier="minimum-weight-z")
    problem = Problem(code.phase_flip_model(), IndependentBitFlip(3), decoder)
    assert problem.is_faulty(state)
    truth = exact(problem, .3)
    chain = sample_faulty(problem, .3, initial_state=state, seed=724,
        config=SamplingConfig(samples=3000, burn_in=200,
            kernels=KernelConfig(zanella=.7, cluster=.3, cluster_k=1, lazy=.05)))
    weights = np.count_nonzero(chain.states, axis=-1).ravel()
    ess = chain.diagnostics["ess"]
    assert ess is not None and ess > 100
    half_width = 1.959963984540054 * np.std(weights, ddof=1) / np.sqrt(ess)
    assert weights.mean() - half_width <= truth.conditional_weight <= weights.mean() + half_width


def test_invalid_phenomenological_data_noise():
    with pytest.raises(ValueError, match="data_noise"):
        PhenomenologicalModel(repetition3(), 1, initial_boundary="clean",
            final_boundary="perfect", representation="history", data_noise="Z")


def test_example_quick_cli(tmp_path):
    pytest.importorskip("pymatching")
    pytest.importorskip("bposd")
    script = Path(__file__).resolve().parents[1] / "examples" / "phase_flip_asymmetric.py"
    env = dict(os.environ, PYTHONPATH=str(Path(mcmc4qec.__file__).resolve().parent.parent))
    run = subprocess.run([sys.executable, str(script), "--quick", "--seed", "20261001",
                          "--out", str(tmp_path)], capture_output=True, text=True,
                         timeout=10, env=env)
    assert run.returncode == 0, run.stderr
    summary = json.loads(run.stdout.strip().splitlines()[-1].removeprefix("SUMMARY "))
    assert set(summary) == {"code", "p", "pl_bit_flip", "pl_phase_flip",
                            "interval_bit_flip", "interval_phase_flip", "exact_available"}
    assert (tmp_path / "phase_flip_comparison.csv").is_file()
