"""Scalar-trace diagnostics and finite-budget uncertainty of observable means."""
from __future__ import annotations

from collections.abc import Iterable
import math
from typing import Any, cast

import numpy as np
from numpy.typing import ArrayLike

from .diagnostics import _iat


def _integer(value: object, name: str, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    result = int(value)
    if result < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return result


def _finite(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def _acf(trace: np.ndarray, max_lag: int) -> list[float | None]:
    if np.ptp(trace) == 0:
        return [None] * (max_lag + 1)
    centered = trace - trace.mean()
    transform = np.fft.rfft(centered, n=2 * len(trace))
    covariance = np.fft.irfft(transform * transform.conj(), n=2 * len(trace))
    if covariance[0] <= 0:
        return [None] * (max_lag + 1)
    return [_finite(float(value)) for value in covariance[:max_lag+1] / covariance[0]]


def _bootstrap_means(
    traces: np.ndarray, block: int, replicates: int, rng: np.random.Generator,
) -> np.ndarray:
    """Resample independently within chains using circular window sums."""
    chains, n = traces.shape
    full_blocks, remainder = divmod(n, block)
    # Prefix sums avoid materializing all n resampled observations per draw.
    prefix = np.concatenate((np.zeros((chains, 1)),
                             np.cumsum(np.concatenate((traces, traces), axis=1), axis=1)),
                            axis=1)
    starts = np.arange(n)
    full_sums = prefix[:, starts + block] - prefix[:, starts]
    tail_sums = prefix[:, starts + remainder] - prefix[:, starts]
    means = np.empty(replicates)
    for draw in range(replicates):
        total = 0.0
        for chain in range(chains):
            indices = rng.integers(n, size=full_blocks + int(remainder > 0))
            total += float(full_sums[chain, indices[:full_blocks]].sum())
            if remainder:
                total += float(tail_sums[chain, indices[-1]])
        means[draw] = total / (chains * n)
    return means


def analyze_traces(
    traces: ArrayLike, *, observable: str = "observable", max_lag: int | None = None,
    block_sizes: Iterable[int] | None = None, bootstrap_replicates: int = 200,
    seed: int | None = None,
) -> dict[str, Any]:
    """Analyze finite scalar traces shaped [chain, sample], or a single vector.

    All chains must have equal, nonzero length. Pass stationary retained draws,
    including rejected steps; this function does not remove burn-in or thin.
    Classical raw split R-hat is not rank-normalized or folded. IAT uses the
    legacy Geyer initial monotone paired estimate, requiring eight observations.
    ``iat`` averages chain IATs and ``ess`` sums chain ESSs for compatibility;
    the latter is generally not a pooled-mean ESS (chain variances and
    autocorrelation times both matter).

    ``iat_mcse`` and blocking SE describe the equally weighted observable mean.
    Blocking discards a per-chain tail and reports its own mean and sample count.
    Circular moving-block bootstrap independently resamples each chain to its
    original length, using a separate RNG. ``seed=None`` records generated
    entropy in the report so the bootstrap can be reproduced. Zero replicates
    disable bootstrap; one replicate is invalid. Default block sizes are one
    and powers of two retaining at least four non-overlapping batches.

    Missing or degenerate estimates are None, never NaN or infinity. A constant
    chain makes mean uncertainty estimates undefined rather than certifying
    zero error. Returned dictionaries contain JSON-safe built-in types only.
    These are finite-budget diagnostics, not convergence or coverage guarantees,
    and do not estimate BAR or logical-failure-probability uncertainty.
    """
    if not isinstance(observable, str) or not observable.strip():
        raise ValueError("observable must be a nonempty string")
    try:
        raw = np.asarray(traces)
        if np.iscomplexobj(raw):
            raise ValueError("traces must be real")
        values = np.asarray(raw, dtype=float)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("traces must be a finite rectangular real array") from error
    if values.ndim == 1:
        values = values[None, :]
    if values.ndim != 2 or min(values.shape) < 1 or not np.isfinite(values).all():
        raise ValueError("traces must be a nonempty finite [chain, sample] array")
    chains, n = values.shape
    lag = min(100, n-1) if max_lag is None else _integer(max_lag, "max_lag")
    if lag >= n:
        raise ValueError("max_lag must be smaller than samples_per_chain")
    replicates = _integer(bootstrap_replicates, "bootstrap_replicates")
    if replicates == 1:
        raise ValueError("bootstrap_replicates must be zero or at least two")
    actual_seed = (cast(int, np.random.SeedSequence().entropy) if seed is None
                   else _integer(seed, "seed"))
    if block_sizes is None:
        blocks = [1]
        while 2 * blocks[-1] <= n // 4:
            blocks.append(2 * blocks[-1])
    else:
        try:
            blocks = [_integer(block, "block_size", 1) for block in block_sizes]
        except TypeError as error:
            raise ValueError("block_sizes must be an iterable of integers") from error
        if not blocks or max(blocks) > n or len(set(blocks)) != len(blocks):
            raise ValueError("block_sizes must contain distinct integers between one and n")
        blocks.sort()

    # Normalize once to avoid overflow in moments for large finite observables.
    scale = float(np.max(np.abs(values))) or 1.0
    x = values / scale
    means = x.mean(axis=1)
    point = float(means.mean())
    constant = np.ptp(x, axis=1) == 0
    any_constant = bool(np.any(constant))
    warnings = [
        "Finite-budget diagnostics do not prove convergence, ergodicity, or correctness.",
        "Mean uncertainty assumes stationary traces and independent chains; burn-in is not removed.",
        "Blocking and bootstrap depend on block length; inspect sensitivity, not a coverage guarantee.",
        "Uncertainty concerns this observable mean, not BAR or logical-failure-probability uncertainty.",
        "R-hat is classical raw split R-hat, not rank-normalized or folded.",
        "ess sums chain ESS estimates; it is generally not the pooled-mean ESS.",
    ]
    chain_iat: list[float | None] = [None] * chains
    chain_ess: list[float | None] = [None] * chains
    if n >= 8:
        for j, trace in enumerate(x):
            if not constant[j]:
                tau = _iat(trace)
                chain_iat[j] = tau
                if tau is not None:
                    chain_ess[j] = _finite(n / tau)
    if any(value is None for value in chain_iat):
        warnings.append("IAT/ESS undefined for short (<8), constant, or nonpositive-IAT chains.")
    if any_constant:
        warnings.append("Constant chain: ACF and mean uncertainty are undefined, not evidence of zero error.")

    report: dict[str, Any] = dict(
        observable=observable, mean=_finite(point * scale), chains=chains,
        samples_per_chain=n, chain_means=[_finite(float(v) * scale) for v in means],
        chain_iat=chain_iat, chain_ess=chain_ess, iat=None, ess=None,
        iat_method="geyer_initial_monotone_pairs",
        ess_method="sum_of_chain_ess_not_pooled_mean_ess", iat_mcse=None,
        cross_chain_se=None, rhat=None, rhat_method="classical_split",
        rhat_samples_used_per_chain=2 * (n // 2), rhat_discarded_per_chain=n % 2,
        acf=dict(lags=list(range(lag+1)), chains=[_acf(row, lag) for row in x],
                 method="biased_fft"), blocking=[],
        bootstrap=dict(method="circular_moving_block", replicates=replicates,
                       seed=actual_seed, confidence_level=0.95, blocks=[]), warnings=warnings,
    )
    if all(tau is not None for tau in chain_iat):
        taus = np.asarray(chain_iat, dtype=float)
        report["iat"] = _finite(float(taus.mean()))
        if all(ess is not None for ess in chain_ess):
            report["ess"] = _finite(sum(ess for ess in chain_ess if ess is not None))
        variance = float(np.sum(np.var(x, axis=1, ddof=1) * taus / n))
        report["iat_mcse"] = _finite(math.sqrt(variance) / chains * scale)
    if chains >= 2 and not any_constant:
        report["cross_chain_se"] = _finite(float(np.std(means, ddof=1)) / math.sqrt(chains) * scale)
    elif chains < 2:
        warnings.append("cross-chain SE requires at least two independent chains")
    if chains >= 2 and n >= 8:
        half = n // 2
        split = np.concatenate((x[:, :half], x[:, -half:]), axis=0)
        split_variances = np.var(split, axis=1, ddof=1)
        split_variances[np.ptp(split, axis=1) == 0] = 0
        within = float(split_variances.mean())
        between = half * float(np.var(split.mean(axis=1), ddof=1))
        if within > 0:
            report["rhat"] = _finite(math.sqrt(((half-1) * within + between) / half / within))
    if report["rhat"] is None:
        warnings.append("split R-hat undefined: needs two chains, eight samples, and positive within variance")
    if n % 2:
        warnings.append("Classical split R-hat discards the middle observation of odd-length chains.")

    rng = np.random.default_rng(actual_seed)
    for block in blocks:
        batches = n // block
        used = batches * block
        batch_means = x[:, :used].reshape(chains, batches, block).mean(axis=2)
        batch_point = float(batch_means.mean())
        se = None
        if batches >= 2 and not any_constant:
            variances = np.var(batch_means, axis=1, ddof=1)
            if np.all(variances > 0) and np.all(np.ptp(batch_means, axis=1) > 0):
                se = _finite(math.sqrt(float(variances.sum()) / batches) / chains * scale)
        report["blocking"].append(dict(
            block_size=block, batches_per_chain=batches, samples_used_per_chain=used,
            discarded_per_chain=n-used, mean=_finite(batch_point * scale),
            mean_difference=_finite((batch_point-point) * scale), se=se,
        ))
        if replicates:
            bootstrap_se = None
            interval = None
            if not any_constant and n >= 2 and block < n:
                draws = _bootstrap_means(x, block, replicates, rng)
                spread = float(np.std(draws, ddof=1))
                if spread > 0:
                    bootstrap_se = _finite(spread * scale)
                    bounds = [_finite(float(v) * scale) for v in np.quantile(draws, [.025, .975])]
                    if all(v is not None for v in bounds):
                        interval = bounds
            report["bootstrap"]["blocks"].append(dict(
                block_size=block, se=bootstrap_se, interval=interval,
            ))
    if any(row["se"] is None for row in report["blocking"]):
        warnings.append("Some blocking SEs are undefined: insufficient batches or degenerate batch variation.")
    if any(row["batches_per_chain"] < 4 for row in report["blocking"]):
        warnings.append("Some block lengths leave fewer than four batches per chain; uncertainty is especially unstable.")
    if any(row["se"] is None for row in report["bootstrap"]["blocks"]):
        warnings.append("Some bootstrap uncertainties are undefined: constant/short trace, full-length block, or degenerate draws.")
    return report
