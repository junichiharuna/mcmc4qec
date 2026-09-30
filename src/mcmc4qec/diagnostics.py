"""Weight-trace diagnostics; these do not certify mixing or correctness."""
import math
import numpy as np


def _iat(x):
    n = len(x)
    centered = x - x.mean()
    transform = np.fft.rfft(centered, n=2*n)
    covariance = np.fft.irfft(transform * transform.conj(), n=2*n)[:n] / n
    acf = covariance / covariance[0]
    # Initial-positive paired autocorrelations, including rho(0)+rho(1).
    pairs = acf[:2*(n//2)].reshape(-1, 2).sum(axis=1)
    nonpositive = np.flatnonzero(pairs <= 0)
    if len(nonpositive):
        pairs = pairs[:nonpositive[0]]
    pairs = np.minimum.accumulate(pairs) if len(pairs) else pairs
    return max(1.0, float(-1 + 2*pairs.sum()))


def diagnose(result):
    if result.states is None or result.states.ndim != 3:
        raise ValueError("diagnose requires [chain, sample, bit] states")
    weights = np.count_nonzero(result.states, axis=-1).astype(float)
    chains, n = weights.shape
    warnings = ["Diagnostics do not prove convergence, ergodicity, or correctness."]
    report = dict(observable="nonidentity coordinate count", iat=None, ess=None, rhat=None,
                  chain_means=weights.mean(axis=1).tolist(), warnings=warnings,
                  acceptance=result.acceptance)
    if n < 8:
        warnings.append("too few samples for IAT/ESS (requires at least 8 per chain)")
    elif np.any(np.var(weights, axis=1) == 0):
        warnings.append("constant chain: IAT/ESS undefined")
    else:
        iats = [_iat(x) for x in weights]
        report["iat"] = float(np.mean(iats))
        report["ess"] = float(sum(n/tau for tau in iats))
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
            report["rhat"] = math.sqrt(((half-1)/half*within + between/half)/within)
    return report
