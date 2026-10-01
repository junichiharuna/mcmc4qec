"""Weight-trace diagnostics; these do not certify mixing or correctness."""
from __future__ import annotations
from typing import Any, Callable, cast
import math

import numpy as np
from .results import Result


def _iat(x):
    """Return positive Geyer paired IAT, or None if the estimate is nonpositive.

    Negative serial correlation can give IAT below one and ESS above the
    recorded sample count. Clamping at one would lose that information.
    """
    n = len(x)
    centered = x - x.mean()
    transform = np.fft.rfft(centered, n=2 * n)
    covariance = np.fft.irfft(transform * transform.conj(), n=2 * n)[:n] / n
    acf = covariance / covariance[0]
    pairs = acf[:2 * (n // 2)].reshape(-1, 2).sum(axis=1)
    nonpositive = np.flatnonzero(pairs <= 0)
    if len(nonpositive):
        pairs = pairs[:nonpositive[0]]
    pairs = np.minimum.accumulate(pairs) if len(pairs) else pairs
    tau = float(-1 + 2 * pairs.sum())
    return tau if np.isfinite(tau) and tau > 0 else None


def weight_traces(results: Result | list[Result]) -> tuple[np.ndarray, list[Result]]:
    """Extract [chain, sample] nonidentity counts from one or more Results.

    Equal sample counts are required so pooled split R-hat has a single segment
    length. Chain labels from distinct Results are treated as independent only
    when the caller supplied independently seeded runs.
    """
    if hasattr(results, "states"):
        results = [cast(Result, results)]
    else:
        results = list(results)
    if not results:
        raise ValueError("at least one Result is required")
    traces = []
    sample_count = None
    for result in results:
        states = result.states
        if states is None or states.ndim != 3 or states.shape[0] < 1 or states.shape[1] < 1:
            raise ValueError("diagnose requires [chain, sample, coordinate] states")
        if sample_count is None:
            sample_count = states.shape[1]
        elif states.shape[1] != sample_count:
            raise ValueError("all Results need the same sample count")
        traces.append(np.count_nonzero(states, axis=-1).astype(float))
    return np.concatenate(traces), results


def _aggregate_acceptance(results):
    counts = {}
    for result in results:
        for kernel, stats in result.acceptance.items():
            entry = counts.setdefault(kernel, dict(proposed=0, accepted=0, moved=0))
            for field in ("proposed", "accepted", "moved"):
                entry[field] += int(stats.get(field, 0))
    for stats in counts.values():
        proposed = stats["proposed"]
        stats["acceptance_rate"] = stats["accepted"] / proposed if proposed else None
        stats["move_rate"] = stats["moved"] / proposed if proposed else None
    return counts


def diagnose(results: Result | list[Result]) -> dict[str, Any]:
    """Diagnose one or more independently seeded conditional-sampling Results.

    `results` is one Result or an iterable of Results, each with states shaped
    [chain, sample, coordinate]. All sample counts must match. The observable
    is a count of nonidentity coordinates per state. Returns a dict with
    `chain_means`, `cross_chain_se`, `chain_iat`, `chain_ess`, `rhat`,
    `acceptance` (per-kernel counts and rates), and `warnings`. Pooled `iat`
    and `ess` remain for backward compatibility. The cross-chain SE is the
    sample SD of independent chain means divided by sqrt(K). A short or
    constant chain has undefined IAT/ESS, encoded as None. Split R-hat
    requires two chains and eight samples per chain. Invalid or unequal
    state shapes raise ValueError. No statistic proves stationarity,
    ergodicity, unbiasedness, or correctness.
    """
    weights, sources = weight_traces(results)
    chains, n = weights.shape
    warnings = ["Diagnostics do not prove convergence, ergodicity, or correctness."]
    means = weights.mean(axis=1)
    report = dict(observable="nonidentity coordinate count", iat=None, ess=None,
                  chain_iat=[None] * chains, chain_ess=[None] * chains,
                  rhat=None, cross_chain_se=None, chain_means=means.tolist(),
                  warnings=warnings, acceptance=_aggregate_acceptance(sources))
    if chains < 2:
        warnings.append("cross-chain SE requires at least two independent chains")
    else:
        report["cross_chain_se"] = float(np.std(means, ddof=1) / math.sqrt(chains))
    if n < 8:
        warnings.append("too few samples for IAT/ESS (requires at least 8 per chain)")
    else:
        for j, trace in enumerate(weights):
            if np.var(trace) == 0:
                continue
            tau = _iat(trace)
            if tau is None:
                continue
            report["chain_iat"][j] = tau
            report["chain_ess"][j] = float(n / tau)
        if any(tau is None for tau in report["chain_iat"]):
            warnings.append("constant chain or nonpositive IAT estimate: IAT/ESS undefined")
        else:
            report["iat"] = float(np.mean(report["chain_iat"]))
            report["ess"] = float(sum(report["chain_ess"]))
    if chains < 2 or n < 8:
        warnings.append("split R-hat requires at least two chains and eight samples per chain")
    else:
        half = n // 2
        split = np.concatenate((weights[:, :half], weights[:, -half:]), axis=0)
        within = float(np.var(split, axis=1, ddof=1).mean())
        between = half * float(np.var(split.mean(axis=1), ddof=1))
        if within == 0:
            warnings.append("constant split chains: R-hat undefined")
        else:
            report["rhat"] = math.sqrt(((half - 1) / half * within + between / half) / within)
    return report
