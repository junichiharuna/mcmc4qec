"""Independent numerical checks for observable-mean trace analysis."""

import math
import json

import numpy as np
import pytest

from mcmc4qec.trace_stats import analyze_traces
from mcmc4qec.diagnostics import diagnose
from mcmc4qec.reporting import DiagnosticsConfig, diagnostic_report
from mcmc4qec.results import Result


def _weight_result(weights, thin=1):
    weights = np.asarray(weights)
    states = (np.arange(4) < weights[..., None]).astype(np.uint8)
    return Result("sample_faulty", {"config": {"thin": thin}}, 0.0, states=states)


def test_default_mcse_preserves_valid_chain_when_other_chain_constant():
    variable = [0, 1, 1, 2, 0, 1, 2, 2, 0, 1, 1, 2, 0, 1, 2, 1]
    result = _weight_result([[1] * 16, variable])
    report = diagnose(result)
    assert report["chain_standard_errors"][0] is None
    assert report["chain_standard_errors"][1] > 0
    assert report["mean_standard_error"] is None
    expected_chain_variance = np.var(variable, ddof=1) * report["chain_iat"][1] / 16
    assert report["chain_standard_errors"][1] ** 2 == pytest.approx(expected_chain_variance)
    assert diagnostic_report(result, config=DiagnosticsConfig(bootstrap_replicates=0))["iat_mcse"] is None


def test_short_nonconstant_chains_have_unavailable_default_mcse():
    report = diagnose(_weight_result([[0, 1, 2, 1, 0, 2, 1], [1, 2, 0, 1, 2, 1, 0]]))
    assert report["chain_standard_errors"] == [None, None]
    assert report["mean_standard_error"] is None


def test_pre_mcse_json_remains_readable():
    original = _weight_result([[0, 1, 2, 0]])
    payload = json.loads(original.to_json())
    del payload["conditional_weight_standard_error"]
    restored = Result.from_json(json.dumps(payload))
    np.testing.assert_array_equal(restored.states, original.states)
    assert restored.conditional_weight_standard_error is None


@pytest.mark.parametrize("value", [[1.0, 2.0], np.complex128(1 + 2j), np.inf])
def test_custom_observable_must_return_finite_real_scalar(value):
    result = _weight_result([[0, 1, 2, 1]])
    with pytest.raises(ValueError):
        diagnostic_report(result, observable=lambda state: value, observable_name="invalid",
                          config=DiagnosticsConfig(bootstrap_replicates=0))


def test_heterogeneous_retention_spacing_is_not_a_single_physical_lag():
    first = _weight_result([[0, 1, 2, 1]], thin=1)
    second = _weight_result([[1, 2, 1, 0]], thin=3)
    report = diagnostic_report([first, second], config=DiagnosticsConfig(bootstrap_replicates=0))
    assert report["sample_spacing"] is None
    assert report["lag_unit"] == "retained samples"


def test_decimal_constant_chain_has_no_acf_despite_centering_roundoff():
    report = analyze_traces([[0.1] * 3, [1.0] * 3], bootstrap_replicates=0)
    assert report["acf"]["chains"] == [[None] * 3, [None] * 3]


def test_classical_split_rhat_ignores_only_odd_middle_sample():
    traces = np.array([
        [0, 1, 4, 2, 1000, 3, 1, 0, 2],
        [2, 0, 3, 1, -1000, 0, 4, 2, 1],
    ], dtype=float)
    report = analyze_traces(traces, bootstrap_replicates=0)
    segments = [row[part] for row in traces for part in (slice(0, 4), slice(5, 9))]
    within = sum(np.var(segment, ddof=1) for segment in segments) / 4
    between = 4 * np.var([np.mean(segment) for segment in segments], ddof=1)
    expected = math.sqrt((0.75 * within + between / 4) / within)
    assert report["rhat"] == pytest.approx(expected)
    assert report["rhat_method"] == "classical_split"
    assert report["rhat_samples_used_per_chain"] == 8
    assert report["rhat_discarded_per_chain"] == 1
    changed = traces.copy()
    changed[:, 4] += 500
    changed_report = analyze_traces(changed, bootstrap_replicates=0)
    assert changed_report["rhat"] == pytest.approx(expected)
    assert changed_report["mean"] != report["mean"]


def test_batch_mcse_keeps_independent_chain_strata_and_truncates_tail():
    first = np.arange(19, dtype=float)
    traces = np.stack([first, 5 * first + 1000])
    report = analyze_traces(traces, block_sizes=[4], bootstrap_replicates=0)
    row = report["blocking"][0]
    # Four complete batches per chain; the three tail samples are not used.
    batch_means = [[np.mean(chain[start:start + 4]) for start in (0, 4, 8, 12)]
                   for chain in traces]
    expected_variance = sum(np.var(means, ddof=1) / 4 for means in batch_means) / 4
    assert row["se"] == pytest.approx(math.sqrt(expected_variance))
    assert row["samples_used_per_chain"] == 16
    assert row["discarded_per_chain"] == 3
    assert row["mean"] == pytest.approx(np.mean(traces[:, :16]))
    assert row["mean_difference"] == pytest.approx(row["mean"] - report["mean"])


def test_circular_bootstrap_matches_exact_conditional_variance_with_partial_block():
    # For fixed data the variance can be enumerated over all circular starts,
    # without replaying the implementation's random-number stream.
    t = np.arange(31, dtype=float)
    traces = np.stack([np.sin(t / 3), 3 * np.cos(t / 4) + 100])
    size = 6
    full, remainder = divmod(traces.shape[1], size)
    conditional_variance = 0.0
    for chain in traces:
        block_sums = np.array([np.roll(chain, -start)[:size].sum() for start in range(31)])
        tail_sums = np.array([np.roll(chain, -start)[:remainder].sum() for start in range(31)])
        conditional_variance += (full * np.var(block_sums) + np.var(tail_sums)) / 31**2
    conditional_variance /= len(traces)**2
    report = analyze_traces(traces, block_sizes=[size], bootstrap_replicates=6000, seed=219)
    observed_se = report["bootstrap"]["blocks"][0]["se"]
    assert observed_se == pytest.approx(math.sqrt(conditional_variance), rel=0.06)


def test_stationary_ar1_mcse_tracks_known_asymptotic_variance():
    phi = 0.8
    chains, samples = 4, 8192
    rng = np.random.default_rng(921)
    traces = np.empty((chains, samples))
    traces[:, 0] = rng.normal(scale=1 / math.sqrt(1 - phi**2), size=chains)
    innovations = rng.normal(size=(chains, samples - 1))
    for index in range(1, samples):
        traces[:, index] = phi * traces[:, index - 1] + innovations[:, index - 1]
    report = analyze_traces(traces, block_sizes=[32], max_lag=5, bootstrap_replicates=0)
    exact_tau = (1 + phi) / (1 - phi)
    exact_mcse = math.sqrt(exact_tau / ((1 - phi**2) * chains * samples))
    assert np.mean(report["chain_iat"]) == pytest.approx(exact_tau, rel=0.25)
    assert report["iat_mcse"] == pytest.approx(exact_mcse, rel=0.15)
    assert np.mean([chain[1] for chain in report["acf"]["chains"]]) == pytest.approx(phi, abs=0.025)


def test_diagnostics_affine_equivariance_including_bootstrap_interval():
    traces = np.random.default_rng(981).normal(size=(3, 64))
    kwargs = dict(block_sizes=[1, 4, 8], bootstrap_replicates=100, seed=123)
    original = analyze_traces(traces, **kwargs)
    transformed = analyze_traces(-3 * traces + 2, **kwargs)
    assert transformed["mean"] == pytest.approx(-3 * original["mean"] + 2)
    for key in ("chain_iat", "chain_ess", "rhat"):
        assert transformed[key] == pytest.approx(original[key])
    for key in ("cross_chain_se", "iat_mcse"):
        assert transformed[key] == pytest.approx(3 * original[key])
    for old, new in zip(original["bootstrap"]["blocks"], transformed["bootstrap"]["blocks"]):
        assert new["se"] == pytest.approx(3 * old["se"])
        assert new["interval"] == pytest.approx([2 - 3 * old["interval"][1], 2 - 3 * old["interval"][0]])
