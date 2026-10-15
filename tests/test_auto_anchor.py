"""Acceptance checks for bounded, independently seeded automatic BAR anchors."""
import math

import numpy as np
import pytest

from mcmc4qec import (
    BinaryLinearModel, CallableDecoder, CallableFailure, CSSCode,
    DepolarizingModel, DepolarizingNoise, IndependentBitFlip, Problem,
    SamplingConfig, direct_mc, exact, estimate_logical_error,
)
from mcmc4qec.estimation import EstimationResult


def problem():
    return Problem(BinaryLinearModel([[1, 1]], [[1, 0]]), IndependentBitFlip(2),
                   CallableDecoder(lambda s: [0], identifier="zero"))


def small_options():
    return dict(config=SamplingConfig(samples=24, burn_in=4), seed=31,
                bootstrap_replicates=4, bootstrap_block_length=3)


def assert_same_estimation(a, b):
    assert a.log_estimates == b.log_estimates
    assert a.log_standard_errors == b.log_standard_errors
    assert a.intervals == b.intervals
    assert a.adjacent_log_ratios == b.adjacent_log_ratios
    assert a.bootstrap_log_ratio_covariance == b.bootstrap_log_ratio_covariance
    assert a.metadata["rungs"] == b.metadata["rungs"]


def test_omitted_anchor_and_config_match_explicit_defaults():
    pr = problem()
    automatic = estimate_logical_error(pr, [.4, .2], seed=31, bootstrap_replicates=2)
    explicit = estimate_logical_error(pr, [.4, .2], anchor=exact(pr, .4),
        config=SamplingConfig(), seed=31, bootstrap_replicates=2)
    assert_same_estimation(automatic, explicit)
    assert automatic.metadata["config"]["sampling"] == explicit.metadata["config"]["sampling"]
    assert automatic.metadata["anchor"]["kind"] == "exact"
    assert automatic.metadata["anchor"]["source"] == "automatic"
    assert explicit.metadata["anchor"]["source"] == "provided"
    assert automatic.metadata["config"]["anchor_max_states"] == 4096
    assert automatic.metadata["config"]["anchor_trials"] == 10000


@pytest.mark.parametrize("uncertainty", ["block_bootstrap", "cross_chain"])
def test_mc_fixed_budget_independent_seed_variance_and_reproducibility(uncertainty):
    pr = problem()
    ladder = [.4, .3, .2]
    opts = small_options()
    opts["config"] = SamplingConfig(samples=24, burn_in=4, chains=2)
    opts["uncertainty"] = uncertainty
    sequence = np.random.SeedSequence(opts["seed"])
    children = sequence.spawn(len(ladder) + 2)
    anchor_seed = int(children[-1].generate_state(1, dtype=np.uint64)[0])
    anchor = direct_mc(pr, ladder[0], trials=200, seed=anchor_seed)
    automatic = estimate_logical_error(pr, ladder, anchor_max_states=0,
        anchor_trials=200, **opts)
    explicit = estimate_logical_error(pr, ladder, anchor=anchor, **opts)
    repeat = estimate_logical_error(pr, ladder, anchor_max_states=0,
        anchor_trials=200, **opts)
    assert_same_estimation(automatic, explicit)
    assert_same_estimation(automatic, repeat)
    info = automatic.metadata["anchor"]
    assert info["kind"] == "direct_mc"
    assert info["trials"] == 200
    assert info["failures"] == anchor.failures
    assert info["metadata"]["rng"]["entropy"] == anchor_seed
    assert anchor_seed not in [r["seed"] for r in automatic.metadata["rungs"]]
    variance = (1 - anchor.estimate) / (200 * anchor.estimate)
    assert info["log_variance"] == pytest.approx(variance)
    assert automatic.log_standard_errors[0] == pytest.approx(math.sqrt(variance))
    assert any("few observed failures" in w for w in automatic.warnings)
    restored = EstimationResult.from_json(automatic.to_json())
    assert restored.metadata == automatic.metadata
    assert restored.intervals == automatic.intervals


@pytest.mark.parametrize("limit,kind", [(15, "direct_mc"), (16, "exact")])
def test_threshold_counts_categorical_alphabet_product(limit, kind):
    code = CSSCode([[0, 0]], [[1, 1]], [[1, 1]], [[1, 0]])
    pr = Problem(DepolarizingModel(code), DepolarizingNoise(2),
                 CallableDecoder(lambda s: [0, 0], identifier="zero-pauli"))
    assert math.prod(pr.alphabets) == 16
    result = estimate_logical_error(pr, [.4, .2], anchor_max_states=limit,
                                   anchor_trials=200, **small_options())
    assert result.metadata["anchor"]["kind"] == kind


def test_large_numpy_integer_alphabets_do_not_overflow_into_enumeration(monkeypatch):
    import mcmc4qec.estimation as estimation

    model = BinaryLinearModel(np.ones((1, 64), dtype=int), [[1] + [0] * 63])
    model.alphabets = tuple(np.full(64, 2, dtype=np.int64))
    pr = Problem(model, IndependentBitFlip(64),
                 CallableDecoder(lambda s: [0], identifier="zero-64"))

    def unexpected(*args, **kwargs):
        raise AssertionError("2**64 states must not enter exact enumeration")

    monkeypatch.setattr(estimation, "exact", unexpected)
    result = estimate_logical_error(pr, [.4, .3], anchor_trials=100, **small_options())
    assert result.metadata["anchor"]["kind"] == "direct_mc"
    assert result.metadata["anchor"]["trials"] == 100


def test_approximate_mode_anchor_uses_first_constructed_decoder():
    pr = problem()

    def factory(prior):
        return CallableDecoder(lambda s: [1], identifier="one",
                               settings={"decoder_prior": prior})

    result = estimate_logical_error(pr, [.4, .2],
        mode="p_dependent_decoder_approx", decoder_factory=factory,
        decoder_priors=[.4, .2], approximation_reason="test approximation",
        **small_options())
    first = Problem(pr.model, pr.noise, factory(.4))
    assert result.estimates[0] == pytest.approx(exact(first, .4).estimate)
    assert result.estimates[0] == pytest.approx(.6)
    assert result.metadata["anchor"]["metadata"]["decoder"] == first.metadata()["decoder"]


class DictNoise:
    n = 2

    def metadata(self):
        return {"type": "auto-anchor-dict-noise", "n": 2}

    def sample(self, p, rng):
        return (rng.random(2) < [p["left"], p["right"]]).astype(np.uint8)

    def log_prob(self, state, p):
        probabilities = np.array([p["left"], p["right"]])
        return float(np.log(np.where(state, probabilities, 1 - probabilities)).sum())


def test_dictionary_coordinates():
    pr = problem()
    pr.noise = DictNoise()
    ladder = [{"left": .4, "right": .2}, {"left": .2, "right": .3}]
    result = estimate_logical_error(pr, ladder, **small_options())
    assert result.estimates[0] == pytest.approx(.4)
    assert result.metadata["anchor"]["metadata"]["sampling_p"] == ladder[0]


@pytest.mark.parametrize("name,value", [
    ("anchor_max_states", -1), ("anchor_max_states", True),
    ("anchor_max_states", 4.0), ("anchor_trials", 0),
    ("anchor_trials", -1), ("anchor_trials", False), ("anchor_trials", 10.0),
])
def test_invalid_automatic_budget_rejected(name, value):
    with pytest.raises(ValueError, match=name):
        estimate_logical_error(problem(), [.4, .2], **{name: value}, **small_options())


def test_explicit_anchor_ignores_automatic_budget():
    pr = problem()
    anchor = exact(pr, .4)
    actual = estimate_logical_error(pr, [.4, .2], anchor=anchor,
        anchor_max_states=-1, anchor_trials=False, **small_options())
    expected = estimate_logical_error(pr, [.4, .2], anchor=anchor, **small_options())
    assert_same_estimation(actual, expected)


@pytest.mark.parametrize("limit,always_failure", [(4, False), (0, False), (0, True)])
def test_uninformative_anchor_has_actionable_error(limit, always_failure):
    pr = problem()
    pr.failure = CallableFailure(lambda state, predicted, truth: always_failure,
                                  identifier=f"constant-{always_failure}")
    with pytest.raises(ValueError) as exc:
        estimate_logical_error(pr, [.4, .2], anchor_max_states=limit,
                               anchor_trials=10, **small_options())
    message = str(exc.value).lower()
    assert "anchor" in message
    assert "anchor_trials" in message or "trials" in message
    assert "first" in message or "ladder" in message


def test_exact_validation_error_is_not_hidden_by_mc_fallback():
    class UnnormalizedNoise(IndependentBitFlip):
        def log_prob(self, state, p):
            return super().log_prob(state, p) + math.log(2)

        def sample(self, p, rng):
            raise AssertionError("invalid exact density must not fall back to MC")

    pr = problem()
    pr.noise = UnnormalizedNoise(2)
    with pytest.raises(ValueError, match="normalized"):
        estimate_logical_error(pr, [.4, .2], **small_options())


def test_exact_all_failure_anchor_is_valid():
    pr = problem()
    pr.failure = CallableFailure(lambda state, predicted, truth: True,
                                 identifier="all-states")
    result = estimate_logical_error(pr, [.4, .2], **small_options())
    assert result.metadata["anchor"]["kind"] == "exact"
    assert result.estimates[0] == pytest.approx(1.0)
    assert result.log_standard_errors[0] == 0.0
    assert result.intervals[0] == pytest.approx((1.0, 1.0))


@pytest.mark.parametrize("extra", [
    {"initial_states": []}, {"bootstrap_replicates": 1},
    {"mode": "invalid"}, {"uncertainty": "invalid"}, {"config": "invalid"},
])
def test_known_invalid_inputs_rejected_before_anchor_computation(extra):
    pr = problem()

    def unexpected(*args, **kwargs):
        raise AssertionError("anchor computation occurred before input validation")

    pr.noise.log_prob = unexpected
    pr.noise.sample = unexpected
    opts = {**small_options(), **extra}
    with pytest.raises(ValueError):
        estimate_logical_error(pr, [.4, .2], **opts)


def test_auto_exact_underflow_preserves_finite_log_probability():
    pr = problem()
    pr.failure = CallableFailure(lambda state, predicted, truth: bool(np.all(state == 1)),
                                  identifier="both-faults")
    p = 1e-200
    result = estimate_logical_error(pr, [p, 2 * p],
        initial_states=[[1, 1], [1, 1]], **small_options())
    assert result.estimates[0] == 0
    assert result.log_estimates[0] == pytest.approx(2 * math.log(p))
    assert result.log_estimates[-1] == pytest.approx(2 * math.log(2 * p))
