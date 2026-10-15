"""Opt-in diagnostics must leave the sampling and BAR estimators unchanged."""
import json

import numpy as np
import pytest

from mcmc4qec import (
    BinaryLinearModel, CallableDecoder, DiagnosticsConfig, IndependentBitFlip,
    KernelConfig, Problem, Result, SamplingConfig, diagnostic_report,
    estimate_logical_error, exact, sample_faulty,
)


def problem():
    return Problem(BinaryLinearModel([[1, 1]], [[1, 0]]), IndependentBitFlip(2),
                   CallableDecoder(lambda s: [0], identifier="zero"))


def config():
    return SamplingConfig(samples=64, burn_in=12, chains=2, thin=2,
                          kernels=KernelConfig(cluster_k=1))


def test_default_does_not_compute_extra_diagnostics(monkeypatch):
    import mcmc4qec.sampling as sampling

    def forbidden(*args, **kwargs):
        raise AssertionError("optional diagnostics were called")

    monkeypatch.setattr(sampling, "diagnostic_report", forbidden)
    run = sample_faulty(problem(), .3, config=config(), seed=41)
    assert "trace_analysis" not in run.diagnostics
    assert "diagnostics" not in run.metadata["config"]
    assert run.conditional_weight_standard_error is not None
    traces = np.count_nonzero(run.states, axis=-1)
    expected = np.sqrt(np.sum(np.var(traces, axis=1, ddof=1) *
                              np.asarray(run.diagnostics["chain_iat"]) / traces.shape[1])) / len(traces)
    assert run.conditional_weight == pytest.approx(traces.mean())
    assert run.conditional_weight_standard_error == pytest.approx(expected)
    assert run.diagnostics["mean_standard_error"] == run.conditional_weight_standard_error


def test_opt_in_keeps_states_rng_and_acceptance_and_roundtrips():
    pr = problem()
    base = sample_faulty(pr, .3, config=config(), seed=41)
    settings = DiagnosticsConfig(max_lag=12, block_sizes=(1, 4, 8),
                                 bootstrap_replicates=24, seed=9)
    run = sample_faulty(pr, .3, config=config(), seed=41, diagnostics=settings)
    np.testing.assert_array_equal(run.states, base.states)
    assert run.acceptance == base.acceptance
    assert run.metadata["rng"] == base.metadata["rng"]
    for key, value in base.diagnostics.items():
        assert run.diagnostics[key] == value
    stats = run.diagnostics["trace_analysis"]
    assert stats["acf"]["lags"] == list(range(13))
    assert stats["sample_spacing"] == 2
    assert stats["mean"] == pytest.approx(np.count_nonzero(run.states, axis=-1).mean())
    assert stats["bootstrap"]["replicates"] == 24
    assert stats["iat_mcse"] == pytest.approx(run.conditional_weight_standard_error)
    assert Result.from_json(run.to_json()).diagnostics == run.diagnostics
    assert diagnostic_report(run, config=settings) == stats


def test_short_and_constant_default_uncertainty_is_unavailable():
    for samples in (2, 16):
        pr = Problem(BinaryLinearModel([[1]], [[1]]), IndependentBitFlip(1),
                     CallableDecoder(lambda s: [0], identifier="zero"))
        run = sample_faulty(pr, .3, initial_state=[1], seed=1,
                            config=SamplingConfig(samples=samples, burn_in=0))
        assert run.conditional_weight == 1
        assert run.conditional_weight_standard_error is None
        assert run.diagnostics["mean_standard_error"] is None
        assert run.diagnostics["chain_standard_errors"] == [None]
        assert Result.from_json(run.to_json()).conditional_weight_standard_error is None


def test_old_json_without_new_optional_field_is_accepted():
    run = sample_faulty(problem(), .3, config=config(), seed=41)
    payload = json.loads(run.to_json())
    payload.pop("conditional_weight_standard_error")
    restored = Result.from_json(json.dumps(payload))
    assert restored.conditional_weight_standard_error is None
    np.testing.assert_array_equal(restored.states, run.states)


def test_true_and_bootstrap_disabled():
    run = sample_faulty(problem(), .3, config=config(), seed=41, diagnostics=True)
    assert run.diagnostics["trace_analysis"]["bootstrap"]["replicates"] == 200
    report = diagnostic_report(run, config=DiagnosticsConfig(bootstrap_replicates=0))
    assert report["bootstrap"]["blocks"] == []
    assert report["blocking"]


@pytest.mark.parametrize("uncertainty", ["block_bootstrap", "cross_chain"])
def test_bar_diagnostics_preserve_estimate_and_probability_uncertainty(uncertainty):
    pr = problem()
    kwargs = dict(anchor=exact(pr, .4), config=config(), seed=31,
                  bootstrap_replicates=12, bootstrap_block_length=4,
                  uncertainty=uncertainty)
    base = estimate_logical_error(pr, [.4, .25, .1], **kwargs)
    run = estimate_logical_error(pr, [.4, .25, .1], diagnostics=DiagnosticsConfig(
        block_sizes=(1, 4, 8), bootstrap_replicates=8), **kwargs)
    assert run.estimates == base.estimates
    assert run.intervals == base.intervals
    assert run.log_standard_errors == base.log_standard_errors
    assert run.bootstrap_log_ratio_covariance == base.bootstrap_log_ratio_covariance
    assert run.metadata["rng"] == base.metadata["rng"]
    assert run.metadata.get("cross_chain_log_ratio_covariance") == base.metadata.get("cross_chain_log_ratio_covariance")
    assert all("trace_analysis" in d for d in run.diagnostics)
    assert all("trace_analysis" not in d for d in base.diagnostics)
    assert type(run).from_json(run.to_json()).diagnostics == run.diagnostics


def test_custom_observable_and_result_group_do_not_mutate_states():
    a = sample_faulty(problem(), .3, config=config(), seed=41)
    b = sample_faulty(problem(), .3, config=config(), seed=42)
    original = a.states.copy()

    def observable(state):
        value = float(state[-1])
        state[:] = 0  # A callback cannot mutate stored sampling states.
        return value

    stats = diagnostic_report([a, b], observable=observable, observable_name="last bit",
                              config=DiagnosticsConfig(bootstrap_replicates=0))
    assert stats["chains"] == 4
    assert stats["mean"] == pytest.approx(np.concatenate([a.states, b.states])[:, :, -1].mean())
    np.testing.assert_array_equal(a.states, original)
    json.dumps(stats, allow_nan=False)
    with pytest.raises(ValueError, match="observable_name"):
        diagnostic_report(a, observable=observable)


@pytest.mark.parametrize("kwargs", [dict(max_lag=-1), dict(max_lag=True),
    dict(block_sizes=()), dict(block_sizes=(0,)), dict(block_sizes=(True,)),
    dict(bootstrap_replicates=1), dict(bootstrap_replicates=True), dict(seed=-1)])
def test_config_rejects_invalid_arguments(kwargs):
    with pytest.raises(ValueError):
        DiagnosticsConfig(**kwargs)


@pytest.mark.parametrize("settings", [1, None, "yes", DiagnosticsConfig(max_lag=64),
                                      DiagnosticsConfig(block_sizes=(65,))])
def test_invalid_options_fail_before_sampling(settings, monkeypatch):
    import mcmc4qec.sampling as sampling

    def forbidden(*args, **kwargs):
        raise AssertionError("sampling began before option validation")

    monkeypatch.setattr(sampling, "CachedDecoder", forbidden)
    with pytest.raises(ValueError):
        sample_faulty(problem(), .3, config=config(), diagnostics=settings)
