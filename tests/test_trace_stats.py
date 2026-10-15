"""Acceptance checks for scalar-trace uncertainty, independent of QEC kernels."""
import json
import math

import numpy as np
import pytest

from mcmc4qec.diagnostics import _iat
from mcmc4qec.trace_stats import analyze_traces


def test_acf_matches_direct_biased_covariance_and_no_mutation():
    values = np.array([[2., 4., 1., 3., 8., 7., 4., 5.]])
    original = values.copy()
    report = analyze_traces(values, max_lag=7, bootstrap_replicates=0)
    centered = values[0] - values.mean()
    expected = [np.dot(centered[:8-lag], centered[lag:]) /
                np.dot(centered, centered) for lag in range(8)]
    assert report["acf"]["chains"][0] == pytest.approx(expected)
    assert report["acf"]["lags"] == list(range(8))
    assert report["chain_iat"] == pytest.approx([_iat(values[0])])
    assert np.array_equal(values, original)
    assert report["bootstrap"]["blocks"] == []
    json.dumps(report, allow_nan=False)


def test_batch_means_and_discarded_tail_are_explicit():
    x = np.array([[0., 2., 3., 7., 11.], [10., 12., 13., 17., 41.]])
    report = analyze_traces(x, block_sizes=[2, 5], bootstrap_replicates=0)
    row = report["blocking"][0]
    # Chain batch means [1, 5], [11, 15], each sample variance 8.
    assert row == dict(block_size=2, batches_per_chain=2,
                       samples_used_per_chain=4, discarded_per_chain=1,
                       mean=8., mean_difference=pytest.approx(8.-x.mean()),
                       se=pytest.approx(math.sqrt(2.)))
    assert report["blocking"][1]["se"] is None


def test_iat_mean_uncertainty_uses_variance_weighting():
    rng = np.random.default_rng(120)
    x = rng.normal(size=(3, 200)) * np.array([1., 3., 7.])[:, None]
    report = analyze_traces(x, bootstrap_replicates=0)
    taus = np.array([_iat(row) for row in x])
    expected = np.sqrt(np.sum(np.var(x, axis=1, ddof=1)*taus/200))/3
    assert report["iat_mcse"] == pytest.approx(expected)
    assert report["ess"] == pytest.approx(np.sum(200/taus))
    assert report["iat"] == pytest.approx(np.mean(taus))
    assert report["cross_chain_se"] == pytest.approx(np.std(x.mean(axis=1), ddof=1)/np.sqrt(3))


def test_seeded_bootstrap_reproducibility_and_rng_isolation():
    x = np.arange(40.).reshape(2, 20)
    np.random.seed(73)
    before = np.random.get_state()
    left = analyze_traces(x, block_sizes=[1, 4, 20], seed=2, bootstrap_replicates=60)
    after = np.random.get_state()
    assert left == analyze_traces(x, block_sizes=[1, 4, 20], seed=2, bootstrap_replicates=60)
    assert before[0] == after[0]
    assert np.array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    rows = left["bootstrap"]["blocks"]
    assert rows[0]["se"] > 0
    assert rows[1]["interval"][0] < x.mean() < rows[1]["interval"][1]
    assert rows[2]["se"] is None and rows[2]["interval"] is None
    assert left["bootstrap"]["seed"] == 2


def test_entropy_seed_recorded_for_reproduction():
    x = np.arange(16.)
    report = analyze_traces(x, bootstrap_replicates=10)
    assert isinstance(report["bootstrap"]["seed"], int)
    assert analyze_traces(x, bootstrap_replicates=10,
                          seed=report["bootstrap"]["seed"]) == report


def test_circular_bootstrap_matches_explicit_chainwise_resampling():
    x = np.array([[2., 0., 8., 1., 9., 5., 3.],
                  [22., 20., 28., 21., 29., 25., 23.]])
    report = analyze_traces(x, block_sizes=[3], seed=86, bootstrap_replicates=50)
    rng = np.random.default_rng(86)
    expected = []
    for _ in range(50):
        chain_means = []
        for trace in x:
            starts = rng.integers(7, size=3)
            indices = ((starts[:, None] + np.arange(3)) % 7).ravel()[:7]
            chain_means.append(trace[indices].mean())
        expected.append(np.mean(chain_means))
    block = report["bootstrap"]["blocks"][0]
    assert block["se"] == pytest.approx(np.std(expected, ddof=1))
    assert block["interval"] == pytest.approx(np.quantile(expected, [.025, .975]))


def test_one_constant_chain_does_not_claim_pooled_mean_certainty():
    report = analyze_traces([np.ones(16), np.arange(16)], seed=3, bootstrap_replicates=10)
    assert report["iat_mcse"] is None
    assert report["cross_chain_se"] is None
    assert all(row["se"] is None for row in report["blocking"])
    assert all(row["se"] is None for row in report["bootstrap"]["blocks"])


@pytest.mark.parametrize("x", [np.ones((2, 16)), np.array([[0.]*16, [1.]*16]), [2.]])
def test_constants_are_undefined_not_zero_certainty(x):
    report = analyze_traces(x, bootstrap_replicates=10, seed=9)
    assert report["iat"] is None
    assert report["ess"] is None
    assert report["rhat"] is None
    assert report["cross_chain_se"] is None
    assert report["iat_mcse"] is None
    assert all(value is None for row in report["acf"]["chains"] for value in row)
    assert all(row["se"] is None for row in report["blocking"])
    assert all(row["interval"] is None for row in report["bootstrap"]["blocks"])
    json.dumps(report, allow_nan=False)


def test_short_trace_and_default_blocks():
    short = analyze_traces([1., 2., 3.], bootstrap_replicates=0)
    assert short["chain_iat"] == [None]
    assert short["rhat"] is None
    assert [row["block_size"] for row in short["blocking"]] == [1]
    long = analyze_traces(np.arange(35.), bootstrap_replicates=0)
    assert [row["block_size"] for row in long["blocking"]] == [1, 2, 4, 8]


def test_negative_correlation_keeps_ess_above_sample_count():
    rng = np.random.default_rng(52)
    x = np.zeros(4096)
    for i in range(1, len(x)):
        x[i] = -.6*x[i-1] + rng.normal()
    report = analyze_traces(x, bootstrap_replicates=0)
    assert 0 < report["chain_iat"][0] < 1
    assert report["chain_ess"][0] > len(x)
    alternating = analyze_traces([0., 1.]*8, bootstrap_replicates=0)
    assert alternating["iat"] is None


@pytest.mark.parametrize("x", [[], [[]], 3., [[[1., 2.]]], [[1., 2.], [3.]],
                                [np.nan], [np.inf], [1.+2.j], ["a"]])
def test_invalid_traces(x):
    with pytest.raises(ValueError):
        analyze_traces(x)


@pytest.mark.parametrize("kwargs", [
    {"max_lag": -1}, {"max_lag": 8}, {"max_lag": 1.5}, {"max_lag": True},
    {"block_sizes": []}, {"block_sizes": [0]}, {"block_sizes": [9]},
    {"block_sizes": [1, 1]}, {"block_sizes": [1.2]}, {"block_sizes": [True]},
    {"bootstrap_replicates": 1}, {"bootstrap_replicates": -1},
    {"bootstrap_replicates": 2.5}, {"bootstrap_replicates": True},
    {"seed": -1}, {"seed": True}, {"seed": 2.5}, {"observable": ""},
    {"observable": 3},
])
def test_invalid_options(kwargs):
    with pytest.raises(ValueError):
        analyze_traces(np.arange(8.), **kwargs)


def test_extreme_finite_values_produce_json_safe_report():
    report = analyze_traces([[1e308, -1e308]*8, [1e308, 0.]*8],
                            bootstrap_replicates=10, seed=2)
    json.dumps(report, allow_nan=False)
    assert math.isfinite(report["mean"])
