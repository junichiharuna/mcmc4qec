import numpy as np
import pytest

from mcmc4qec.convergence import evaluate_convergence
from mcmc4qec.diagnostics import diagnose
from mcmc4qec.results import Result


def _ar1(seed, chains=16, n=2048, phi=0.4, offset=0):
    rng = np.random.default_rng(seed)
    innovations = rng.normal(size=(chains, n + 128))
    traces = np.empty_like(innovations)
    traces[:, 0] = innovations[:, 0]
    for j in range(1, traces.shape[1]):
        traces[:, j] = phi * traces[:, j - 1] + innovations[:, j]
    return traces[:, 128:] + offset


def _result(weights):
    weights = np.asarray(weights, dtype=int)
    states = np.arange(10) < weights[..., None]
    return Result("sample_faulty", {}, 0.0, states=states.astype(np.uint8),
                  acceptance={"single": {"proposed": 20, "accepted": 5, "moved": 5}})


def test_diagnose_multiple_results_and_kernel_counts():
    a = _result([[1, 2, 1, 2, 1, 2, 1, 2]])
    b = _result([[1, 2, 1, 2, 1, 2, 1, 2]])
    report = diagnose([a, b])
    assert report["cross_chain_se"] == pytest.approx(0)
    assert len(report["chain_iat"]) == 2
    assert len(report["chain_ess"]) == 2
    assert report["acceptance"]["single"]["proposed"] == 40
    assert report["acceptance"]["single"]["acceptance_rate"] == pytest.approx(.25)
    assert report["rhat"] is not None


def test_stationary_ar1_passes_four_checks():
    a = _ar1(12, chains=32)
    b = _ar1(13, chains=32)
    report = evaluate_convergence(a, other_initialization=b,
                                  direct_variance=1 / (1 - .4 ** 2))
    assert all(item["ok"] is True for item in report["checks"].values())
    assert report["converged"] is True
    assert "proof" in " ".join(report["warnings"]).lower()


def test_two_basins_are_rejected_by_multistart():
    a = _ar1(14, offset=2)
    b = _ar1(15, offset=7)
    report = evaluate_convergence(a, other_initialization=b,
                                  direct_variance=1 / (1 - .4 ** 2))
    assert report["checks"]["multistart"]["ok"] is False
    assert report["converged"] is False


def test_drift_and_dispersion_fail_independently():
    a = _ar1(16, n=1024)
    drift = a.copy()
    drift[:, 512:] += 4
    assert evaluate_convergence(drift, other_initialization=drift,
                                direct_variance=1.2)["checks"]["stationarity"]["ok"] is False
    tiny_reference = evaluate_convergence(a, other_initialization=a,
                                          direct_variance=.001)
    assert tiny_reference["checks"]["dispersion"]["ok"] is False


def test_persistent_chain_offsets_fail_scaling():
    a = _ar1(17, n=1024) + np.linspace(0, 5, 16)[:, None]
    report = evaluate_convergence(a, other_initialization=a)
    assert report["checks"]["scaling"]["ok"] is False


def test_missing_multistart_is_unresolved():
    report = evaluate_convergence(_ar1(19))
    assert report["checks"]["multistart"]["ok"] is None
    assert report["converged"] is None
    assert "initial" in " ".join(report["warnings"]).lower()
