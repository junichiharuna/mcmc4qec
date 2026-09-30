from itertools import product
import json

import numpy as np
import pytest

from mcmc4qec.core import CSSCode
from mcmc4qec.models import DepolarizingModel, PhenomenologicalModel
from mcmc4qec.noise_categorical import DepolarizingNoise, PhenomenologicalNoise


def repetition2():
    return CSSCode(np.empty((0, 2), dtype=int), [[1, 1]], [[1, 1]], [[1, 0]])


def phen(*, data_noise="bit_flip", boundary="perfect", representation="history", rounds=2):
    return PhenomenologicalModel(repetition2(), rounds, data_noise=data_noise,
                                initial_boundary="clean", final_boundary=boundary,
                                representation=representation)


def states(model):
    return product(*(range(q) for q in model.alphabets))


@pytest.mark.parametrize("p", [0, 0.1, 1])
def test_depolarizing_normalized_and_y_correlation(p):
    noise = DepolarizingNoise(2)
    masses = {s: np.exp(noise.log_prob(s, p)) for s in states(noise)}
    assert sum(masses.values()) == pytest.approx(1)
    assert sum(v for s, v in masses.items() if s[0] == 2) == pytest.approx(p / 3)
    if p == 0.1:
        assert p / 3 != pytest.approx((2 * p / 3) ** 2)


def test_pauli_both_sectors_and_stabilizer_invariance():
    model = DepolarizingModel(repetition2())
    np.testing.assert_array_equal(model.syndrome([2, 0]), [1])
    np.testing.assert_array_equal(model.observables([2, 0]), [1, 1])
    for state in states(model):
        for stabilizer in model.stabilizers:
            np.testing.assert_array_equal(model.syndrome(np.asarray(state) ^ stabilizer), model.syndrome(state))
            np.testing.assert_array_equal(model.observables(np.asarray(state) ^ stabilizer), model.observables(state))


def test_y_flips_both_x_and_z_check_sectors():
    code = CSSCode([[1, 1]], [[1, 1]], np.empty((0, 2)), np.empty((0, 2)))
    model = DepolarizingModel(code)
    np.testing.assert_array_equal(model.syndrome([2, 0]), [1, 1])
    np.testing.assert_array_equal(model.syndrome([1, 0]), [1, 0])
    np.testing.assert_array_equal(model.syndrome([3, 0]), [0, 1])


def test_two_round_unencoded_analytic_fault_probability():
    code = CSSCode(np.empty((0, 1)), np.empty((0, 1)), [[1]], [[1]])
    p = 0.2
    for data_noise, expected in [("bit_flip", 2 * p * (1 - p)),
                                 ("depolarizing", 1 - ((1 - p) ** 2 + p ** 2 / 3))]:
        model = PhenomenologicalModel(code, 2, data_noise=data_noise,
                                      initial_boundary="clean", final_boundary="perfect", representation="difference")
        noise = PhenomenologicalNoise(model)
        faulty_mass = sum(np.exp(noise.log_prob(state, {"data": p, "measurement": 0.1}))
                          for state in states(model) if np.any(model.observables(state)))
        assert faulty_mass == pytest.approx(expected)
        assert model.syndrome(np.zeros(model.n, dtype=int)).shape == (2, 0)


@pytest.mark.parametrize("data_noise", ["bit_flip", "depolarizing"])
@pytest.mark.parametrize("boundary", ["perfect", "noisy"])
@pytest.mark.parametrize("p", [{"data": 0, "measurement": 0}, {"data": 0.2, "measurement": 0.3}, {"data": 1, "measurement": 1}])
def test_phenomenological_normalized_small_exact(data_noise, boundary, p):
    model = phen(data_noise=data_noise, boundary=boundary, rounds=1)
    noise = PhenomenologicalNoise(model)
    assert sum(np.exp(noise.log_prob(state, p)) for state in states(model)) == pytest.approx(1)


def test_history_difference_and_final_boundary():
    model = phen()
    # X on qubit 0 at round 1, none at round 2, round-1 measurement fault.
    state = [1, 0, 0, 0, 1]
    np.testing.assert_array_equal(model.syndrome(state), [[0], [1]])
    np.testing.assert_array_equal(phen(representation="difference").syndrome(state), [[0], [1]])
    state[-1] = 0
    np.testing.assert_array_equal(model.syndrome(state), [[1], [1]])
    np.testing.assert_array_equal(phen(representation="difference").syndrome(state), [[1], [0]])
    noisy = phen(boundary="noisy")
    np.testing.assert_array_equal(noisy.syndrome([1, 0, 0, 0, 0, 1]), [[1], [0]])
    assert noisy.n == model.n + 1
    assert not hasattr(model, "stabilizers")


@pytest.mark.parametrize("data_noise", ["bit_flip", "depolarizing"])
def test_zero_measurement_limit_and_cumulative_observables(data_noise):
    model = phen(data_noise=data_noise, boundary="noisy")
    noise = PhenomenologicalNoise(model)
    p = {"data": 0.15, "measurement": 0}
    total = 0
    for state in states(model):
        mass = np.exp(noise.log_prob(state, p))
        if any(state[model.n_data:]):
            assert mass == 0
            continue
        data = np.asarray(state[:model.n_data]).reshape(model.rounds, model.code.n)
        cumulative = np.bitwise_xor.accumulate(data, axis=0)
        np.testing.assert_array_equal(model.syndrome(state), [model.data_model.syndrome(row) for row in cumulative])
        np.testing.assert_array_equal(model.observables(state), model.data_model.observables(cumulative[-1]))
        total += mass
    assert total == pytest.approx(1)


def test_pauli_accumulates_by_product_not_integer_addition():
    model = phen(data_noise="depolarizing")
    # X then Y = Z, so final X component cancels while Z remains.
    np.testing.assert_array_equal(model.observables([1, 0, 2, 0, 0]), [0, 1])
    np.testing.assert_array_equal(model.syndrome([1, 0, 2, 0, 0]), [[1], [0]])


@pytest.mark.parametrize("p", [0.1, {}, {"data": 0.1}, {"data": 0.1, "measurement": 0.2, "extra": 1}, {"data": -0.1, "measurement": 0.1}, {"data": 0.1, "measurement": float("nan")}])
def test_phenomenological_probability_schema(p):
    model = phen()
    noise = PhenomenologicalNoise(model)
    with pytest.raises(ValueError):
        noise.log_prob(np.zeros(model.n), p)


@pytest.mark.parametrize("state", [[4, 0], [-1, 0], [1.5, 0], [[1, 0]], [1], [float("nan"), 0]])
def test_depolarizing_invalid_state(state):
    with pytest.raises(ValueError):
        DepolarizingModel(repetition2()).validate_state(state)


def test_measurement_coordinates_remain_binary():
    model = phen(data_noise="depolarizing")
    with pytest.raises(ValueError):
        model.validate_state([0, 0, 0, 0, 2])


def test_required_boundaries_and_invalid_options():
    with pytest.raises(TypeError):
        PhenomenologicalModel(repetition2(), 1)
    defaults = dict(initial_boundary="clean", final_boundary="perfect", representation="history")
    for name, value in [("initial_boundary", "noisy"), ("final_boundary", "unknown"), ("representation", "flat"), ("data_noise", "independent-xz")]:
        with pytest.raises(ValueError):
            PhenomenologicalModel(repetition2(), 1, **{**defaults, name: value})
    with pytest.raises(ValueError):
        PhenomenologicalModel(repetition2(), 0, **defaults)


def test_seed_reproducibility_and_metadata():
    for model, noise, p in [(DepolarizingModel(repetition2()), DepolarizingNoise(2), 0.5),
                            (phen(data_noise="depolarizing"), PhenomenologicalNoise(phen(data_noise="depolarizing")), {"data": 0.3, "measurement": 0.4})]:
        rng1, rng2 = np.random.default_rng(41), np.random.default_rng(41)
        for _ in range(10):
            np.testing.assert_array_equal(noise.sample(p, rng1), noise.sample(p, rng2))
        for metadata in (model.metadata(), noise.metadata()):
            assert json.loads(json.dumps(metadata)) == metadata
            assert len(metadata["sha256"]) == 64
