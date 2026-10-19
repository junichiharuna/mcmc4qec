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


def _two_basin_chain(seed, *, start, chains=32, n=2048, jump_probability=1e-6):
    rng = np.random.default_rng(seed)
    hidden = np.full(chains, start, dtype=np.uint8)
    traces = np.empty((chains, n), dtype=float)
    for step in range(n):
        hidden ^= rng.random(chains) < jump_probability
        traces[:, step] = 2 + 5 * hidden + rng.binomial(1, .5, size=chains)
    return traces


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
    a = _two_basin_chain(14, start=0)
    b = _two_basin_chain(15, start=1)
    # Equal stationary basin masses: Bernoulli emission variance .25 plus
    # between-basin variance (7 - 2)^2 / 4 = 6.25.
    report = evaluate_convergence(a, other_initialization=b,
                                  direct_variance=6.5)
    assert all(report["checks"][name]["ok"] is True for name in
               ("scaling", "stationarity", "dispersion"))
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
    report = evaluate_convergence(_ar1(19), direct_variance=1 / (1 - .4 ** 2))
    assert report["checks"]["multistart"]["ok"] is None
    assert report["converged"] is None
    assert "initial" in " ".join(report["warnings"]).lower()


def test_direct_variance_is_required_for_four_check_pass():
    a = _ar1(12, chains=32)
    b = _ar1(13, chains=32)
    report = evaluate_convergence(a, other_initialization=b)
    assert report["checks"]["dispersion"]["ok"] is None
    assert report["converged"] is None
    assert report["within_chain_dispersion"]["ok"] is True


def test_zero_se_and_zero_reference_scatter_do_not_hide_disagreement():
    a = np.zeros((4, 16))
    b = np.ones((4, 16))
    report = evaluate_convergence(a, other_initialization=b, direct_variance=1)
    assert report["checks"]["multistart"]["ok"] is False
    assert report["checks"]["multistart"]["z"] == float("inf")
    drift = np.tile(np.r_[np.zeros(8), np.ones(8)], (4, 1))
    report = evaluate_convergence(drift, other_initialization=drift, direct_variance=1)
    assert report["checks"]["stationarity"]["ok"] is False
    assert report["checks"]["stationarity"]["z"] == float("inf")
    scaling = a.copy()
    scaling[0, 4:] = 1
    report = evaluate_convergence(scaling, other_initialization=scaling,
                                  direct_variance=1)
    assert report["checks"]["scaling"]["ok"] is False
    assert report["checks"]["scaling"]["ratio"] == float("inf")
    same = evaluate_convergence(a, other_initialization=a, direct_variance=1)
    assert same["checks"]["multistart"]["ok"] is None
    assert same["checks"]["scaling"]["ok"] is None


def test_negative_ar1_has_iat_below_one_and_ess_above_sample_count():
    a = _ar1(22, chains=16, n=2048, phi=-.6)
    report = evaluate_convergence(a, other_initialization=_ar1(23, chains=16, n=2048, phi=-.6),
                                  direct_variance=1 / (1 - .6 ** 2))
    tau = np.mean(report["checks"]["dispersion"]["chain_iat"])
    assert .1 < tau < .6
    result = Result("sample_faulty", {}, 0.0, states=(a > 0).astype(np.uint8)[..., None])
    diagnostics = diagnose(result)
    assert np.mean(diagnostics["chain_iat"]) < 1
    assert np.mean(diagnostics["chain_ess"]) > a.shape[1]
