"""Bennett ratios on a common failure set and an explicitly approximate mode.

No weight-only density formula or independent-sample MCMC error bar is used.
"""
from __future__ import annotations
from typing import Any, Callable, cast
from dataclasses import asdict, dataclass, field
import json
import math
import time

import numpy as np

from .core import Decoder, Problem, json_value, positive_integer
from .results import Result, metadata
from .sampling import SamplingConfig, sample_faulty


class OverlapError(ValueError):
    """Raised when adjacent samples lack observed bidirectional BAR overlap."""


def _sigmoid(x):
    return np.exp(-np.logaddexp(0.0, -np.asarray(x)))


def bennett_log_ratio(log_b_minus_a_at_a: Any, log_b_minus_a_at_b: Any) -> float:
    """Estimate log(Z_b/Z_a) from cross log densities sampled at a and b.

    Arrays contain log(rho_b/rho_a), with rho the normalized original noise
    density restricted to one common failure set. Their lengths may differ.
    At a samples only -inf is allowed; at b samples only +inf is allowed.
    No finite-sample uncertainty or common-failure guarantee is inferred here.
    Both inputs are nonempty arrays and may have different lengths. Returns a
    dimensionless natural-log partition-mass ratio. NaNs or samples lacking
    positive density in their own ensemble raise ``ValueError``; absent
    observed bidirectional overlap raises ``OverlapError``. Converting this
    ratio to a physical logical failure probability requires an anchor.
    """
    a = np.asarray(log_b_minus_a_at_a, dtype=float).ravel()
    b = np.asarray(log_b_minus_a_at_b, dtype=float).ravel()
    if not len(a) or not len(b) or np.any(np.isnan(a)) or np.any(np.isnan(b)):
        raise ValueError("nonempty log density differences without NaN are required")
    if np.any(np.isposinf(a)) or np.any(np.isneginf(b)):
        raise ValueError("each sample must have positive density in its own ensemble")
    fa, fb = a[np.isfinite(a)], b[np.isfinite(b)]
    if not len(fa) or not len(fb):
        raise OverlapError("no bidirectional observed support overlap for BAR")
    offset = math.log(len(b) / len(a))

    def score(r):
        return float(_sigmoid(a-r+offset).sum() - _sigmoid(-b+r-offset).sum())

    low = min(float(fa.min()), float(fb.min())) + offset - 50
    high = max(float(fa.max()), float(fb.max())) + offset + 50
    for _ in range(200):
        middle = low + (high-low)/2
        value = score(middle)
        if value > 0:
            low = middle
        else:
            high = middle
        if high-low <= 1e-12 * max(1.0, abs(middle)):
            break
    return float(low + (high-low)/2)


@dataclass
class EstimationResult:
    """Absolute failure probabilities and diagnostic data for one BAR ladder.

    ``estimates`` and ``intervals`` are experiment-wide probabilities by rung;
    ``log_estimates`` and ``adjacent_log_ratios`` use natural logs.
    ``log_standard_errors`` are dimensionless, and ``elapsed_seconds`` is wall
    time. ``estimate`` and ``interval`` select the final rung. ``to_json``
    returns schema-versioned text; ``from_json`` reconstructs it and raises
    ``ValueError`` for incompatible schemas or invalid JSON-compatible values.
    Intervals assume adequate chain mixing and block length; approximate BAR
    bias is excluded.
    """
    estimates: list[float]
    log_estimates: list[float]
    adjacent_log_ratios: list[float]
    log_standard_errors: list[float | None]
    intervals: list[tuple[float, float] | None]
    metadata: dict[str, Any]
    elapsed_seconds: float
    warnings: list[str] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    overlap: list[dict[str, Any]] = field(default_factory=list)
    bootstrap_log_ratio_covariance: list[list[float]] | None = None
    kind: str = "splitting_bar"

    @property
    def estimate(self) -> float:
        return self.estimates[-1]

    @property
    def interval(self) -> tuple[float, float] | None:
        return self.intervals[-1]

    def to_json(self, *, indent: int=2) -> str:
        return json.dumps(json_value({**asdict(self), "schema_version": 1}),
                          indent=indent, allow_nan=False)

    @classmethod
    def from_json(cls, payload: str) -> EstimationResult:
        data = json.loads(payload)
        if data.pop("schema_version", None) != 1 or data.get("kind") != "splitting_bar":
            raise ValueError("unsupported estimation result schema")
        json_value(data)
        data["intervals"] = [None if x is None else tuple(x) for x in data["intervals"]]
        return cls(**data)


def _coordinate(p):
    p = json_value(p)
    if isinstance(p, bool) or not isinstance(p, (int, float, dict)):
        raise ValueError("each ladder coordinate must be a scalar or explicit parameter dict")
    if isinstance(p, dict) and not p:
        raise ValueError("parameter dict must not be empty")
    return p


def _anchor_variance(anchor, problem, p):
    if not isinstance(anchor, Result) or anchor.kind not in ("exact", "direct_mc"):
        raise ValueError("anchor must be an exact or fixed-trial direct_mc Result")
    _anchor_log(anchor)
    if anchor.metadata.get("sampling_p") != p:
        raise ValueError("anchor sampling_p must equal the first ladder coordinate")
    for key, value in problem.metadata().items():
        if anchor.metadata.get(key) != value:
            raise ValueError(f"anchor {key} metadata differs from the first rung")
    if anchor.kind == "exact":
        return 0.0
    n = positive_integer(anchor.trials, "anchor.trials")
    k = positive_integer(anchor.failures, "anchor.failures")
    if k > n or not math.isclose(k/n, anchor.estimate, rel_tol=1e-12):
        raise ValueError("anchor count and point estimate are inconsistent")
    if k == n:
        raise ValueError("all-failure MC anchor has no reliable delta-method uncertainty; use exact or more trials")
    return (1-anchor.estimate)/(n*anchor.estimate)


def _anchor_log(anchor):
    # An exact positive mass may be below the floating-point rate range.
    log_estimate = getattr(anchor, "log_estimate", None)
    if anchor.kind == "exact" and log_estimate is not None:
        if not np.isfinite(log_estimate) or log_estimate > 0:
            raise ValueError("exact anchor log_estimate must be finite and at most zero")
        return float(log_estimate)
    if anchor.estimate is None or not np.isfinite(anchor.estimate) or not 0 < anchor.estimate <= 1:
        raise ValueError("anchor estimate must be positive and at most one; zero is uninformative")
    return math.log(anchor.estimate)


def _block_indices(shape, length, rng):
    chains, samples = shape
    # Each chain is resampled independently. Blocks may wrap within that chain.
    starts = rng.integers(samples, size=(chains, math.ceil(samples/length)))
    indices = (starts[:, :, None] + np.arange(length)) % samples
    return indices.reshape(chains, -1)[:, :samples]


def estimate_logical_error(problem: Problem, ladder: list[float | dict[str, Any]], *, anchor: Result, config: SamplingConfig | None=None, seed: int | None=None,
                           initial_states: list[np.ndarray | None] | None=None, mode: str="fixed_failure", decoder_factory: Callable[[Any], Decoder] | None=None,
                           decoder_priors: list[Any] | None=None, approximation_reason: str | None=None,
                           bootstrap_replicates: int=100, bootstrap_block_length: int | None=None) -> EstimationResult:
    """Sample a ladder, estimate adjacent BAR ratios, and multiply an anchor.

    The first ladder coordinate is the anchor. Each subsequent coordinate is
    an explicit scalar or parameter dict understood by the supplied noise.
    ``initial_states`` has one entry per rung (each accepted by sample_faulty).
    Fixed mode holds the exact same decoder object and failure predicate.
    Approximate mode calls ``decoder_factory(decoder_prior)`` at each rung;
    density-only BAR then ignores changes in failure sets, intentionally.

    Error bars combine a circular-block bootstrap with the *independent*
    anchor's log variance. Mixing and sufficiently long blocks are assumptions,
    not consequences of diagnostics. Approximate-mode bias is not in the bars.
    Setting bootstrap_replicates=0 disables MCMC error bars explicitly.
    ``problem`` supplies the fixed model/noise/failure contract; ``ladder`` is
    an ordered list of at least two probability coordinates. ``anchor`` is a
    matching positive ``exact`` or fixed-trial ``direct_mc`` Result at rung 0.
    ``config`` and ``seed`` control conditional sampling; ``initial_states``
    can supply one initial state per rung. ``mode`` selects fixed failure or
    explicit decoder-dependent approximation with ``decoder_factory``,
    ``decoder_priors``, and ``approximation_reason``. Bootstrap controls are
    bootstrap_replicates (nonnegative count) and bootstrap_block_length
    (retained samples per chain per block; None uses the rounded cube root of
    config.samples, with a minimum of one).
    Returns ``EstimationResult`` with absolute failure probabilities for each
    whole modeled experiment, natural-log ratios, intervals where available,
    and warnings. Invalid inputs or anchor mismatch raise ``ValueError``;
    failed initialization raises ``InitializationError`` and missing adjacent
    observed overlap raises ``OverlapError``.
    """
    start = time.perf_counter()
    ladder = [_coordinate(p) for p in ladder]
    if len(ladder) < 2:
        raise ValueError("ladder requires at least two coordinates")
    if any(a == b for a, b in zip(ladder, ladder[1:])):
        raise ValueError("adjacent ladder coordinates must differ")
    config = SamplingConfig() if config is None else config
    if not isinstance(config, SamplingConfig):
        raise ValueError("config must be SamplingConfig")
    positive_integer(bootstrap_replicates, "bootstrap_replicates", zero=True)
    if bootstrap_replicates == 1:
        raise ValueError("bootstrap_replicates must be zero or at least two")
    length = max(1, int(round(config.samples ** (1/3)))) if bootstrap_block_length is None else positive_integer(
        bootstrap_block_length, "bootstrap_block_length")
    if length > config.samples:
        raise ValueError("bootstrap block length exceeds retained samples per chain")
    if bootstrap_replicates and (config.samples < 8 or length < 2):
        raise ValueError("block uncertainty requires at least eight samples and block length >= 2")
    if mode == "fixed_failure":
        if decoder_factory is not None or decoder_priors is not None or approximation_reason is not None:
            raise ValueError("decoder factory, priors, and reason require explicit approximate mode")
        problems = [problem] * len(ladder)
        priors = [problem.decoder.metadata().get("settings", {}).get("decoder_prior")] * len(ladder)
    elif mode == "p_dependent_decoder_approx":
        if not callable(decoder_factory) or not isinstance(approximation_reason, str) or not approximation_reason.strip():
            raise ValueError("approximate mode requires decoder_factory and approximation_reason")
        if decoder_priors is None or len(decoder_priors) != len(ladder):
            raise ValueError("one explicit decoder_prior per rung is required")
        priors = json_value(list(decoder_priors))
        if any(prior is None for prior in priors):
            raise ValueError("decoder_priors must contain explicit non-null coordinates")
        problems = [Problem(problem.model, problem.noise, decoder_factory(prior), failure=problem.failure)
                    for prior in priors]
    else:
        raise ValueError("unknown BAR mode")
    variance_anchor = _anchor_variance(anchor, problems[0], ladder[0])
    if initial_states is None:
        initial_states = [None] * len(ladder)
    elif len(initial_states) != len(ladder):
        raise ValueError("one initial_states entry per rung is required")
    sequence = np.random.SeedSequence(seed)
    children = sequence.spawn(len(ladder) + 1)
    rung_seeds = [int(child.generate_state(1, dtype=np.uint64)[0]) for child in children[:-1]]
    runs = [sample_faulty(pr, p, config=config, seed=s, initial_state=initial)
            for pr, p, s, initial in zip(problems, ladder, rung_seeds, initial_states)]
    edges, ratios, overlap = [], [], []
    for i in range(len(ladder)-1):
        differences = []
        for run in (runs[i], runs[i+1]):
            values = [problem.log_prob(state, ladder[i+1]) - problem.log_prob(state, ladder[i])
                      for state in cast(np.ndarray, run.states).reshape(-1, problem.model.n)]
            differences.append(np.asarray(values).reshape(cast(np.ndarray, run.states).shape[:2]))
        a, b = differences
        ratio = bennett_log_ratio(a, b)
        edges.append((a, b))
        ratios.append(ratio)
        offset = math.log(b.size/a.size)
        overlap.append(dict(forward_mean=float(_sigmoid(a-ratio+offset).mean()),
                            reverse_mean=float(_sigmoid(-b+ratio-offset).mean()),
                            finite_cross_fraction_a=float(np.isfinite(a).mean()),
                            finite_cross_fraction_b=float(np.isfinite(b).mean())))
    warnings = ["BAR error bars assume each chain mixed within the intended failure distribution; diagnostics do not prove this.",
                "Anchor and rung sampling are assumed independent; metadata cannot establish this independence.",
                "Circular block bootstrap uses a finite chosen block length; longer correlations and systematic bias may be missed."]
    if mode != "fixed_failure":
        warnings.append("p-dependent decoder approximate BAR ignores changing failure sets; its bias is not included in uncertainty.")
    if anchor.kind == "direct_mc":
        warnings.append("Anchor log variance uses a binomial delta approximation, unreliable with few observed failures.")
    if any(min(x["forward_mean"], x["reverse_mean"]) < .01 for x in overlap):
        warnings.append("Very low observed adjacent overlap; ratios and their uncertainty may be unreliable.")
    covariance: Any = None
    ses = [math.sqrt(variance_anchor)] + [None] * (len(ladder)-1)
    bootstrap_successes = 0
    if bootstrap_replicates:
        rng = np.random.default_rng(children[-1])
        draws = []
        for _ in range(bootstrap_replicates):
            indices = [_block_indices(cast(np.ndarray, run.states).shape[:2], length, rng) for run in runs]
            try:
                draws.append([bennett_log_ratio(np.take_along_axis(a, indices[i], axis=1),
                                                np.take_along_axis(b, indices[i+1], axis=1))
                              for i, (a, b) in enumerate(edges)])
            except OverlapError:
                continue
        bootstrap_successes = len(draws)
        if bootstrap_successes == bootstrap_replicates:
            covariance = np.atleast_2d(np.cov(np.asarray(draws), rowvar=False, ddof=1))
            for i in range(1, len(ladder)):
                ses[i] = math.sqrt(max(0, variance_anchor + float(covariance[:i, :i].sum())))
            covariance = covariance.tolist()
        else:
            warnings.append("Some bootstrap draws lacked overlap; all MCMC error bars omitted rather than conditioning on successful draws.")
    else:
        warnings.append("MCMC uncertainty was disabled; ladder error bars are unavailable.")
    logs = (_anchor_log(anchor) + np.r_[0, np.cumsum(ratios)]).tolist()
    if any(value > math.log(np.finfo(float).max) for value in logs):
        raise ValueError("BAR estimate overflow: check overlap, mixing, and anchor consistency")
    estimates = [math.exp(x) for x in logs]
    intervals = [None if se is None or x > 0 or math.exp(x) == 0 else (math.exp(min(0.0, x-1.959963984540054*se)),
                                          math.exp(min(0.0, x+1.959963984540054*se)))
                 for x, se in zip(logs, ses)]
    if any(x > 1 for x in estimates):
        warnings.append("An estimated probability exceeds one; point estimates were not clipped and its interval is omitted. Inspect sampling and anchor consistency.")
    if any(x == 0 for x in estimates):
        warnings.append("A probability underflowed floating-point representation and its interval is omitted; use log_estimates, not a claim of zero probability.")
    run_metadata = metadata(problem, ladder[-1], dict(sampling=asdict(config), mode=mode,
        bootstrap_replicates=bootstrap_replicates, bootstrap_block_length=length,
        bootstrap_successes=bootstrap_successes), sequence, children)
    run_metadata.update(json_value(dict(ladder=ladder, mode=mode,
        approximation_reason=approximation_reason, anchor=dict(kind=anchor.kind, estimate=anchor.estimate,
            log_estimate=_anchor_log(anchor),
            interval=anchor.interval, trials=anchor.trials, failures=anchor.failures,
            log_variance=variance_anchor, metadata=anchor.metadata),
        rungs=[dict(sampling_p=p, decoder_prior=prior, seed=s, metadata=run.metadata)
               for p, prior, s, run in zip(ladder, priors, rung_seeds, runs)],
        uncertainty_method="shared-rung circular block bootstrap plus independent anchor log-delta variance")))
    return EstimationResult(estimates, logs, ratios, ses, intervals, run_metadata,
        time.perf_counter()-start, warnings, [run.diagnostics for run in runs], overlap, covariance)
