"""Four post-hoc consistency screens for independent MCMC chain populations."""
import math

import numpy as np

from .diagnostics import _iat, weight_traces


def _traces(value):
    if isinstance(value, np.ndarray):
        traces = np.asarray(value, dtype=float)
    else:
        traces, _ = weight_traces(value)
    if (traces.ndim != 2 or min(traces.shape) < 1 or
            not np.all(np.isfinite(traces))):
        raise ValueError("traces must be a finite [chain, sample] array")
    return traces


def _population(traces):
    means = np.mean(traces, axis=1)
    k = len(means)
    sd = float(np.std(means, ddof=1)) if k >= 2 else None
    se = sd / math.sqrt(k) if sd is not None else None
    return float(np.mean(means)), sd, se


def _check(ok, **values):
    return {"ok": None if ok is None else bool(ok), **values}


def _dispersion(traces, observed_sd, variance, factor, source):
    k, n = traces.shape
    if (k < 2 or n < 8 or observed_sd is None or variance <= 0 or
            np.any(np.var(traces, axis=1) == 0)):
        return _check(None, ratio=None, variance_source=source)
    iats = [_iat(trace) for trace in traces]
    if any(tau is None for tau in iats):
        return _check(None, ratio=None, variance_source=source, chain_iat=iats)
    predicted = math.sqrt(variance * float(np.mean(iats)) / n)
    ratio = observed_sd / predicted
    return _check(ratio <= factor, ratio=ratio, observed_sd=observed_sd,
                  predicted_sd=predicted, variance_source=source, chain_iat=iats)


def evaluate_convergence(results, *, other_initialization=None, direct_variance=None,
                         scale_factor=1.5, sigma_cut=3.0, dispersion_factor=3.0):
    """Screen a chain population using the four checks in the paper's Setup.

    `results` and `other_initialization` accept Result objects, sequences of
    Results, or numeric [chain, sample] traces. The two populations must have
    deliberately different starts. `direct_variance` is an independent direct
    MC estimate of the conditional observable variance, not the variance of a
    direct-MC mean. If omitted, dispersion is unresolved. A separate
    `within_chain_dispersion` field reports the paper's internal-variance
    comparison for reference but cannot make the four-check verdict pass.

    Scaling detects persistent between-chain spread but may pass if all chains
    relax together. Stationarity detects late drift, not a frozen common bias.
    Multistart detects differing basins reached from two starts, but misses a
    basin shared by both. Dispersion detects an IAT too small to explain the
    chain scatter, but misses a common bias and depends on the variance source.
    A passing result is only a finite-budget consistency screen, never a proof.
    """
    for value, name, floor in ((scale_factor, "scale_factor", 1),
                               (sigma_cut, "sigma_cut", 0),
                               (dispersion_factor, "dispersion_factor", 1)):
        if not np.isfinite(value) or value <= floor:
            raise ValueError(f"{name} must be finite and greater than {floor}")
    a = _traces(results)
    k, n = a.shape
    mean, sd, se = _population(a)
    warnings = ["Passing all four checks is not a proof of convergence, ergodicity, unbiasedness, or correctness."]
    checks = {}

    # Compare N/4 with N; the earlier N/16 checkpoint is transient-prone.
    quarter = n // 4
    if k < 2 or quarter < 2:
        checks["scaling"] = _check(None, ratio=None)
        warnings.append("scaling requires two chains and at least eight samples")
    else:
        _, ref_sd, _ = _population(a[:, :quarter])
        expected = ref_sd * math.sqrt(quarter / n)
        ratio = sd / expected if expected > 0 else (math.inf if sd > 0 else None)
        checks["scaling"] = _check(None if ratio is None else ratio <= scale_factor,
                                    ratio=ratio, reference_samples=quarter,
                                    reference_sd=ref_sd, final_sd=sd)
        if ratio is None:
            warnings.append("zero scatter at both scaling checkpoints is uninformative")

    # Compare the preceding quarter with the final half, dropping first quarter.
    if k < 2 or quarter < 2 or se is None:
        checks["stationarity"] = _check(None, z=None)
        warnings.append("stationarity requires two chains and enough samples")
    else:
        half = n // 2
        earlier = float(a[:, quarter:half].mean())
        later = float(a[:, half:].mean())
        se_difference = se * math.sqrt(n * (1 / (half - quarter) + 1 / (n - half)))
        difference = abs(later - earlier)
        z = difference / se_difference if se_difference > 0 else (
            math.inf if difference > 0 else None)
        checks["stationarity"] = _check(None if z is None else z <= sigma_cut,
                                         z=z, preceding_quarter=earlier,
                                         final_half=later, se_difference=se_difference)
        if z is None:
            warnings.append("zero SE and zero late drift make stationarity uninformative")

    if other_initialization is None:
        checks["multistart"] = _check(None, z=None)
        warnings.append("different initial states were not supplied; multistart is untested")
    else:
        b = _traces(other_initialization)
        other_mean, _, other_se = _population(b)
        combined_se = (math.hypot(se, other_se) if se is not None and other_se is not None
                       else None)
        if combined_se is None:
            checks["multistart"] = _check(None, z=None)
            warnings.append("multistart needs two chains per population")
        else:
            difference = abs(mean - other_mean)
            z = difference / combined_se if combined_se > 0 else (
                math.inf if difference > 0 else None)
            checks["multistart"] = _check(None if z is None else z <= sigma_cut,
                                           z=z, other_mean=other_mean,
                                           combined_se=combined_se)
            if z is None:
                warnings.append("zero SE and equal multistart means are uninformative")

    within_variance = float(np.var(a, axis=1, ddof=1).mean()) if n >= 2 else 0.0
    within_chain_dispersion = _dispersion(a, sd, within_variance,
                                           dispersion_factor, "within_chain")
    if direct_variance is None:
        checks["dispersion"] = _check(None, ratio=None, variance_source="direct_mc")
        warnings.append("independent direct-MC conditional variance was not supplied; dispersion is untested")
    else:
        if not np.isfinite(direct_variance) or direct_variance <= 0:
            raise ValueError("direct_variance must be finite and positive")
        checks["dispersion"] = _dispersion(a, sd, float(direct_variance),
                                            dispersion_factor, "direct_mc")
        if checks["dispersion"]["ok"] is None:
            warnings.append("dispersion requires variable chains, positive IAT, and eight samples")
    flags = [entry["ok"] for entry in checks.values()]
    converged = False if False in flags else (None if None in flags else True)
    if converged is None:
        warnings.append("one or more checks could not be evaluated")
    return dict(converged=converged, mean=mean, cross_chain_se=se,
                checks=checks, within_chain_dispersion=within_chain_dispersion,
                warnings=warnings)
