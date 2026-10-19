"""Explicit independent logical bases preserve the full failure observable."""
import itertools

import numpy as np
import pytest

from mcmc4qec import (CSSCode, DepolarizingModel, CallableDecoder,
                     DecoderAdapter, IndependentBitFlip, Problem)


def matrices():
    checks = np.array([[1, 1, 0, 0]], dtype=np.uint8)
    lx = np.array([[0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.uint8)
    lz = np.array([[0, 0, 1, 0], [0, 0, 1, 1]], dtype=np.uint8)
    return checks, checks, lx, lz


def test_independent_logicals_require_explicit_opt_in():
    with pytest.raises(ValueError):
        CSSCode(*matrices())
    code = CSSCode(*matrices(), logical_basis="independent")
    assert code.logical_basis == "independent"
    for actual, supplied in zip((code.hx, code.hz, code.lx, code.lz), matrices()):
        np.testing.assert_array_equal(actual, supplied)
        assert not actual.flags.writeable


@pytest.mark.parametrize("basis", ["paired", "independent"])
def test_dependent_logicals_rejected(basis):
    hx, hz, lx, lz = matrices()
    lz[1] = lz[0]
    with pytest.raises(ValueError):
        CSSCode(hx, hz, lx, lz, logical_basis=basis)


def test_unknown_basis_rejected():
    with pytest.raises(ValueError):
        CSSCode(*matrices(), logical_basis="infer")


@pytest.mark.parametrize("pauli", [False, True])
def test_full_failure_observable_and_stabilizers(pauli):
    hx, hz, lx, lz = matrices()
    independent = CSSCode(hx, hz, lx, lz, logical_basis="independent")
    paired = CSSCode(hx, hz, lx, lx)
    assert paired.logical_basis == "paired"
    model = DepolarizingModel(independent) if pauli else independent.bit_flip_model()
    reference = DepolarizingModel(paired) if pauli else paired.bit_flip_model()
    # For any residual error, zero/nonzero full logical mismatch is invariant.
    for state in itertools.product(range(4 if pauli else 2), repeat=4):
        state = np.array(state, dtype=np.uint8)
        assert bool(model.observables(state).any()) == bool(reference.observables(state).any())
        for stabilizer in model.stabilizers:
            np.testing.assert_array_equal(model.syndrome(state ^ stabilizer), model.syndrome(state))
            np.testing.assert_array_equal(model.observables(state ^ stabilizer), model.observables(state))


def test_nonzero_correction_predictions_follow_logical_coordinates():
    hx, hz, lx, lz = matrices()
    paired = CSSCode(hx, hz, lx, lx)
    independent = CSSCode(hx, hz, lx, lz, logical_basis="independent")

    class Correction:
        def decode(self, syndrome):
            return np.array([syndrome[0], 0, 1, 0], dtype=np.uint8)

    def problem(code, decoder):
        return Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)

    def mapped(code):
        return problem(code, DecoderAdapter(Correction(), output_kind="correction",
                       identifier="nonzero-correction", logical_map=code.lz))

    old, new = mapped(paired), mapped(independent)
    for state in itertools.product(range(2), repeat=4):
        assert old.is_faulty(state) == new.is_faulty(state)
    # Copying old logical predictions without transforming them is incorrect.
    stale = problem(independent, CallableDecoder(lambda s: [1, 0], identifier="stale"))
    assert old.is_faulty([0, 0, 1, 0]) is False
    assert new.is_faulty([0, 0, 1, 0]) is False
    assert stale.is_faulty([0, 0, 1, 0]) is True
