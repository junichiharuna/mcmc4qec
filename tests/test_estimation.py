import itertools
import math

import numpy as np
import pytest

from rimc import (BinaryLinearModel, CallableDecoder, CallableFailure,
                  IndependentBitFlip, KernelConfig, Problem, Result,
                  SamplingConfig, exact, direct_mc)
from rimc.estimation import (EstimationResult, OverlapError, bennett_log_ratio,
                             estimate_logical_error)


def problem():
    return Problem(BinaryLinearModel([[1, 1]], [[1, 0]]), IndependentBitFlip(2),
                   CallableDecoder(lambda s: [0], identifier="zero"))


def test_bennett_exact_empirical_distributions_and_unequal_counts():
    # rho_a=(.2,.3,.5), rho_b=(.1,.6,.3), F={0,1}; Z_b/Z_a=.7/.5.
    delta = np.log(np.array([.1, .6]) / [.2, .3])
    a = np.repeat(delta, [4, 6])
    b = np.repeat(delta, [3, 18])
    assert bennett_log_ratio(a, b) == pytest.approx(math.log(1.4), abs=1e-11)
    assert bennett_log_ratio(-b, -a) == pytest.approx(-math.log(1.4), abs=1e-11)


def test_support_zeros_and_no_observed_overlap():
    # The shared atom has equal unnormalized density, Z_a=1 and Z_b=2.
    assert bennett_log_ratio([0], [0, np.inf]) == pytest.approx(math.log(2), abs=1e-10)
    with pytest.raises(OverlapError):
        bennett_log_ratio([-np.inf], [np.inf])
    with pytest.raises(OverlapError):
        bennett_log_ratio([0], [np.inf])
    for a, b in [([], [0]), ([np.nan], [0]), ([np.inf], [0]), ([0], [-np.inf])]:
        with pytest.raises(ValueError):
            bennett_log_ratio(a, b)


def test_real_ladder_sampling_bootstrap_and_json():
    pr = problem()
    config = SamplingConfig(samples=400, burn_in=50, chains=2,
                            kernels=KernelConfig(cluster_k=1))
    result = estimate_logical_error(pr, [.4, .25, .1], anchor=exact(pr, .4),
        config=config, seed=25, bootstrap_replicates=20, bootstrap_block_length=5)
    assert result.estimates[0] == pytest.approx(.4)
    assert result.estimate == pytest.approx(.1, abs=.025)
    assert all(x is not None and x >= 0 for x in result.log_standard_errors)
    assert np.asarray(result.bootstrap_log_ratio_covariance).shape == (2, 2)
    assert result.metadata["mode"] == "fixed_failure"
    assert len(set(rung["seed"] for rung in result.metadata["rungs"])) == 3
    assert result.metadata["config"]["bootstrap_block_length"] == 5
    restored = EstimationResult.from_json(result.to_json())
    assert restored.metadata == result.metadata
    assert restored.estimates == result.estimates
    assert restored.intervals == result.intervals
    repeat = estimate_logical_error(pr, [.4, .25, .1], anchor=exact(pr, .4),
        config=config, seed=25, bootstrap_replicates=20, bootstrap_block_length=5)
    assert repeat.log_estimates == result.log_estimates
    assert repeat.bootstrap_log_ratio_covariance == result.bootstrap_log_ratio_covariance


def test_anchor_metadata_and_validation():
    pr = problem()
    anchor = exact(pr, .4)
    for change in ("model", "noise", "decoder", "failure", "sampling_p"):
        altered = Result.from_json(anchor.to_json())
        altered.metadata[change] = "different"
        with pytest.raises(ValueError, match="anchor"):
            estimate_logical_error(pr, [.4, .1], anchor=altered)
    with pytest.raises(ValueError, match="positive"):
        estimate_logical_error(pr, [0, .1], anchor=exact(pr, 0))
    for args in [dict(ladder=[.4]), dict(ladder=[.4, .4]),
                 dict(ladder=[.4, .1], decoder_factory=lambda p: pr.decoder),
                 dict(ladder=[.4, .1], bootstrap_replicates=1),
                 dict(ladder=[.4, .1], initial_states=[]),
                 dict(ladder=[.4, .1], mode="unknown")]:
        with pytest.raises(ValueError):
            estimate_logical_error(pr, anchor=anchor, **args)


def test_approximate_mode_requires_explicit_inputs_and_records_them():
    pr = problem()

    def factory(prior):
        return CallableDecoder(lambda s: [int(prior < .2)], identifier="prior-decoder",
                               settings={"decoder_prior": prior})

    first = Problem(pr.model, pr.noise, factory(.4))
    anchor = exact(first, .4)
    base = dict(anchor=anchor, mode="p_dependent_decoder_approx", decoder_factory=factory,
                decoder_priors=[.4, .1], approximation_reason="research approximation")
    for key in ("decoder_factory", "decoder_priors", "approximation_reason"):
        args = dict(base)
        del args[key]
        with pytest.raises(ValueError):
            estimate_logical_error(pr, [.4, .1], **args)
    result = estimate_logical_error(pr, [.4, .1], **base, seed=2,
        config=SamplingConfig(samples=30, burn_in=10), bootstrap_replicates=0)
    assert result.metadata["approximation_reason"] == "research approximation"
    assert [r["decoder_prior"] for r in result.metadata["rungs"]] == [.4, .1]
    assert result.interval is None
    assert any("changing failure" in warning for warning in result.warnings)
    assert any("disabled" in warning for warning in result.warnings)


class DictNoise:
    n = 2

    def metadata(self):
        return {"type": "test-two-probability-noise", "n": 2}

    def sample(self, p, rng):
        return (rng.random(2) < [p["left"], p["right"]]).astype(np.uint8)

    def log_prob(self, state, p):
        selected = np.where(state, [p["left"], p["right"]],
                            1-np.array([p["left"], p["right"]]))
        return float(np.log(selected).sum())


def test_general_density_parameter_dict_and_no_weight_shortcut():
    pr = problem()
    pr.noise = DictNoise()
    a, b = {"left": .4, "right": .2}, {"left": .1, "right": .6}
    result = estimate_logical_error(pr, [a, b], anchor=exact(pr, a), seed=12,
        config=SamplingConfig(samples=800, burn_in=40, kernels=KernelConfig(cluster_k=1)),
        bootstrap_replicates=0)
    assert result.estimate == pytest.approx(.1, abs=.025)
    assert result.metadata["ladder"] == [a, b]


def test_no_overlap_between_endpoint_rungs():
    pr = problem()
    pr.failure = CallableFailure(lambda state, predicted, truth: True, identifier="all-states")
    with pytest.raises(OverlapError):
        estimate_logical_error(pr, [0, 1], anchor=exact(pr, 0), seed=1,
            config=SamplingConfig(samples=8, burn_in=0), bootstrap_replicates=0)


def test_mc_anchor_delta_variance():
    pr = problem()
    anchor = direct_mc(pr, .4, trials=1000, seed=91)
    result = estimate_logical_error(pr, [.4, .2], anchor=anchor, seed=7,
        config=SamplingConfig(samples=8, burn_in=0), bootstrap_replicates=0)
    expected = math.sqrt((1-anchor.estimate)/(1000*anchor.estimate))
    assert result.log_standard_errors[0] == pytest.approx(expected)
    assert any("delta approximation" in warning for warning in result.warnings)


def test_changing_failure_set_bias_is_explicit_and_exceeds_one_is_not_an_interval():
    model = BinaryLinearModel([[0]], [[1]])
    noise = IndependentBitFlip(1)

    def factory(prior):
        return CallableDecoder(lambda syndrome: [int(prior < .6)],
            identifier="threshold-prior", settings={"decoder_prior": prior})

    # At p=.9 failure is {1}; at p=.5 failure is {0}. Each conditional chain
    # is a singleton, so this is a deterministic illustration of approximation
    # bias, not a statistical assertion about Monte Carlo fluctuations.
    first = Problem(model, noise, factory(.9))
    second = Problem(model, noise, factory(.5))
    assert first.is_faulty([1]) and not second.is_faulty([1])
    assert second.is_faulty([0]) and not first.is_faulty([0])
    result = estimate_logical_error(first, [.9, .5], anchor=exact(first, .9),
        config=SamplingConfig(samples=8, burn_in=0), seed=12,
        mode="p_dependent_decoder_approx", decoder_factory=factory,
        decoder_priors=[.9, .5], approximation_reason="deliberately disjoint failure sets",
        bootstrap_replicates=2, bootstrap_block_length=2)
    # Density-only BAR gives .9 sqrt[(.5/.9)*(.5/.1)] = 1.5, vs truth .5.
    assert result.estimate == pytest.approx(1.5, abs=1e-10)
    assert exact(second, .5).estimate == pytest.approx(.5)
    assert result.interval is None
    assert any("exceeds one" in warning for warning in result.warnings)
    assert any("changing failure" in warning for warning in result.warnings)


def test_exact_anchor_underflow_retains_log_probability():
    pr = problem()
    pr.failure = CallableFailure(lambda state, predicted, truth: bool(np.all(state == 1)),
                                  identifier="both-faults")
    p = 1e-200
    anchor = exact(pr, p)
    assert anchor.estimate == 0
    assert anchor.log_estimate == pytest.approx(2*math.log(p))
    result = estimate_logical_error(pr, [p, 2*p], anchor=anchor,
        config=SamplingConfig(samples=8, burn_in=0), seed=3,
        initial_states=[[1, 1], [1, 1]], bootstrap_replicates=0)
    assert result.adjacent_log_ratios[0] == pytest.approx(2*math.log(2))
    assert result.log_estimates[-1] == pytest.approx(2*math.log(2*p))
    assert result.metadata["anchor"]["log_estimate"] == anchor.log_estimate
    assert result.intervals[0] is None
    assert any("underflow" in warning for warning in result.warnings)


def test_old_positive_anchor_without_log_field_value_still_works():
    pr = problem()
    anchor = exact(pr, .4)
    anchor.log_estimate = None
    result = estimate_logical_error(pr, [.4, .2], anchor=anchor,
        config=SamplingConfig(samples=8, burn_in=0), seed=14, bootstrap_replicates=0)
    assert result.log_estimates[0] == pytest.approx(math.log(.4))
