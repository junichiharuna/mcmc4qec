"""Optional numerical diagnostics for retained conditional MCMC samples."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

import numpy as np

from .core import positive_integer
from .diagnostics import weight_traces
from .results import Result
from .trace_stats import analyze_traces


@dataclass(frozen=True)
class DiagnosticsConfig:
    """Controls for optional observable-mean diagnostics, not BAR error bars.

    max_lag is inclusive and measured in retained samples; None uses the
    analyze_traces default. block_sizes selects batch/bootstrap block lengths;
    None scans powers of two with at least four batches where possible.
    bootstrap_replicates=0 skips only bootstrap; otherwise at least two draws
    are required. seed defaults to 0 and is independent of all sampling and
    BAR RNGs. None requests fresh entropy. Invalid values raise ValueError.
    """
    max_lag: int | None = None
    block_sizes: tuple[int, ...] | None = None
    bootstrap_replicates: int = 200
    seed: int | None = 0

    def __post_init__(self) -> None:
        if self.max_lag is not None:
            positive_integer(self.max_lag, "max_lag", zero=True)
        if self.block_sizes is not None:
            if not isinstance(self.block_sizes, tuple) or not self.block_sizes:
                raise ValueError("block_sizes must be a nonempty tuple of integers")
            for size in self.block_sizes:
                positive_integer(size, "block size")
            if len(set(self.block_sizes)) != len(self.block_sizes):
                raise ValueError("block_sizes must not contain duplicates")
        positive_integer(self.bootstrap_replicates, "bootstrap_replicates", zero=True)
        if self.bootstrap_replicates == 1:
            raise ValueError("bootstrap_replicates must be zero or at least two")
        if self.seed is not None:
            positive_integer(self.seed, "seed", zero=True)


def _resolve_diagnostics(value: bool | DiagnosticsConfig, samples: int) -> DiagnosticsConfig | None:
    if value is False:
        return None
    settings = DiagnosticsConfig() if value is True else value
    if not isinstance(settings, DiagnosticsConfig):
        raise ValueError("diagnostics must be a bool or DiagnosticsConfig")
    if settings.max_lag is not None and settings.max_lag >= samples:
        raise ValueError("max_lag must be smaller than retained samples per chain")
    if settings.block_sizes is not None and any(size > samples for size in settings.block_sizes):
        raise ValueError("block size exceeds retained samples per chain")
    return settings


def diagnostic_report(results: Result | Iterable[Result], *,
                      config: DiagnosticsConfig | None = None,
                      observable: Callable[[np.ndarray], float] | None = None,
                      observable_name: str | None = None) -> dict[str, Any]:
    """Analyze retained samples without changing results or their stored states.

    The default observable is nonidentity coordinate count. A custom scalar
    callback receives a copy of each state and requires observable_name.
    Multiple Results must have equal chain lengths and represent independent
    chains of the same target distribution; the caller must ensure this.
    No additional burn-in or thinning is applied. Returned ACF, blocking and
    bootstrap arrays are JSON-compatible and can be plotted by the caller.
    SEs/intervals describe the observable mean, not the failure probability.
    Constant/short traces produce None and explanatory warnings. Good
    diagnostics never certify convergence, ergodicity or interval coverage.
    """
    weights, sources = weight_traces(results)
    settings = DiagnosticsConfig() if config is None else config
    if not isinstance(settings, DiagnosticsConfig):
        raise ValueError("config must be DiagnosticsConfig")
    _resolve_diagnostics(settings, weights.shape[1])
    if observable is None:
        name = "nonidentity coordinate count" if observable_name is None else observable_name
        traces = weights
    else:
        if not callable(observable):
            raise ValueError("observable must be callable")
        if not isinstance(observable_name, str) or not observable_name.strip():
            raise ValueError("custom observables require a nonempty observable_name")
        name = observable_name
        rows = []
        for source in sources:
            assert source.states is not None  # validated by weight_traces
            for chain in source.states:
                rows.append([observable(state.copy()) for state in chain])
        traces = np.asarray(rows)
    report = analyze_traces(traces, observable=name, max_lag=settings.max_lag,
                            block_sizes=settings.block_sizes,
                            bootstrap_replicates=settings.bootstrap_replicates,
                            seed=settings.seed)
    spacings = [source.metadata.get("config", {}).get("thin") for source in sources]
    report["sample_spacing"] = spacings[0] if all(s == spacings[0] for s in spacings) else None
    report["lag_unit"] = "retained samples"
    report["iat_unit"] = "retained samples"
    report["warnings"] = list(dict.fromkeys([
        *report["warnings"], *(warning for source in sources for warning in source.warnings
                              if warning in source.diagnostics.get("warnings", []) or
                              warning not in source.diagnostics.get("trace_analysis", {}).get("warnings", []))]))
    return report
