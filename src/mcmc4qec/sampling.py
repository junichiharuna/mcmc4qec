"""Exact enumeration, fixed-budget direct MC, and conditional MH sampling."""
from __future__ import annotations
from typing import Any, Protocol, TypeVar, cast
from dataclasses import asdict, dataclass, field
from dataclasses import replace
import itertools
import math
import time

import numpy as np
from numpy.typing import ArrayLike
from .core import Problem, positive_integer
from .kernels import OBF, Zanella, ClusterExchange, StabilizerFlip
from .results import Result, metadata
from .diagnostics import diagnose
from .decode_cache import CachedDecoder, FailureEvaluator


class InitializationError(RuntimeError):
    """No supported faulty initial state found within the finite search budget."""


class _Kernel(Protocol):
    name: str
    def propose(self, state: np.ndarray, problem: Problem[Any], p: Any,
                rng: np.random.Generator) -> Any: ...


_P = TypeVar("_P")


@dataclass(frozen=True)
class KernelConfig:
    """Per-step kernel mixture and optional laziness.

    The five move probabilities must sum to one; lazy is applied separately.
    single, zanella, cluster, stabilizer, and circuit_single are their weights.
    cluster_k counts occupied and empty coordinates exchanged by one H move.
    zanella_fastpath affects only exact built-in product noises. Invalid weights,
    cluster_k, or lazy probability raise ValueError. CircuitFaultModel permits
    mixtures of single, zanella, and circuit_single. Circuit cluster exchange
    additionally requires explicit circuit_groups of compatible physical
    location indices. Circuit stabilizer XOR remains unsupported.
    """
    single: float = 0.0
    zanella: float = 0.7
    cluster: float = 0.3
    stabilizer: float = 0.0
    cluster_k: int = 2
    lazy: float = 0.05
    zanella_fastpath: bool = True
    circuit_single: float = 0.0
    circuit_groups: tuple[tuple[int, ...], ...] | None = None

    def __post_init__(self) -> None:
        weights = [self.single, self.zanella, self.cluster, self.stabilizer, self.circuit_single]
        if any(not np.isfinite(w) or w < 0 for w in weights):
            raise ValueError("kernel probabilities must be finite and nonnegative")
        if not math.isclose(sum(weights), 1, rel_tol=0, abs_tol=1e-12):
            raise ValueError("kernel probabilities must sum to 1; no implicit normalization")
        positive_integer(self.cluster_k, "cluster_k")
        if not np.isfinite(self.lazy) or not 0 <= self.lazy < 1:
            raise ValueError("lazy must be in [0, 1)")
        if not isinstance(self.zanella_fastpath, bool):
            raise ValueError("zanella_fastpath must be boolean")


@dataclass(frozen=True)
class SamplingConfig:
    """Conditional MCMC budget, decoder cache, and kernel configuration.

    samples counts retained states per chain; burn_in and thin count every
    transition, including rejected and lazy steps. chains is the number of
    independent RNG streams. cache_cap limits entries according to
    cache_policy. max_initial_attempts bounds initialization draws per chain;
    kernels supplies the KernelConfig. The cache's
    research_clear policy checks for size > cap every ten steps, as in
    the research runner; it is a soft cap. lru and freeze are strict caps.
    Invalid counts, cache settings, or kernel configuration raise ValueError.
    """
    samples: int = 1000
    burn_in: int = 100
    thin: int = 1
    chains: int = 1
    max_initial_attempts: int = 10000
    kernels: KernelConfig = field(default_factory=KernelConfig)
    cache_cap: int | None = None
    cache_policy: str = "research_clear"

    def __post_init__(self) -> None:
        for name in ("samples", "thin", "chains", "max_initial_attempts"):
            positive_integer(getattr(self, name), name)
        positive_integer(self.burn_in, "burn_in", zero=True)
        if not isinstance(self.kernels, KernelConfig):
            raise ValueError("kernels must be KernelConfig")
        if self.cache_cap is not None:
            positive_integer(self.cache_cap, "cache_cap")
        if self.cache_policy not in ("research_clear", "lru", "freeze"):
            raise ValueError("cache_policy must be research_clear, lru, or freeze")


def spawn_seeds(seed: int | None, count: int) -> list[int]:
    """Return count deterministic child seeds for caller-managed workers.

    seed follows NumPy SeedSequence semantics. Raises ValueError unless count
    is a positive integer.
    """
    positive_integer(count, "count")
    return [int(s.generate_state(1, dtype=np.uint64)[0])
            for s in np.random.SeedSequence(seed).spawn(count)]


def exact(problem: Problem[_P], p: _P, *, max_states: int=1_048_576) -> Result:
    """Enumerate the full experiment state space and return an exact Result.

    problem binds the model, noise, decoder, and shared failure definition.
    p is the noise parameter; max_states bounds the enumerated cardinality.
    estimate is the logical failure probability per complete experiment, and
    conditional_weight is the expected nonidentity coordinate count given
    failure. Raises ValueError on excessive state space or nonnormalized noise.
    """
    start = time.perf_counter()
    positive_integer(max_states, "max_states")
    n = problem.model.n
    if math.prod(problem.alphabets) > max_states:
        raise ValueError("exact state count exceeds max_states")
    total, failure_logs, weights = [], [], []
    for bits in itertools.product(*(range(a) for a in problem.alphabets)):
        state = problem.state(bits)
        log_probability = problem.log_prob(state, p)
        total.append(log_probability)
        if math.isfinite(log_probability) and problem.is_faulty(state):
            failure_logs.append(log_probability)
            weights.append(int(np.count_nonzero(state)))
    log_total = float(np.logaddexp.reduce(total))
    if not math.isclose(math.exp(log_total), 1, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("noise probabilities are not normalized on the categorical state space")
    log_rate = min(0.0, float(np.logaddexp.reduce(failure_logs))) if failure_logs else None
    rate = math.exp(log_rate) if log_rate is not None else 0.0
    conditional = (float(np.dot(np.exp(np.asarray(failure_logs)-log_rate), weights))
                   if log_rate is not None else None)
    warnings = []
    if log_rate is None:
        warnings.append("empty supported failure set; conditional mean is undefined")
    elif rate == 0:
        warnings.append("probability underflow in estimate; use finite log_estimate for the positive failure mass")
    return Result("exact", metadata(problem, p, dict(max_states=max_states)),
        time.perf_counter()-start, estimate=rate, log_estimate=log_rate,
        conditional_weight=conditional, warnings=warnings)


def _wilson(failures: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    rate = failures/n
    denominator = 1 + z*z/n
    center = (rate + z*z/(2*n)) / denominator
    radius = z*math.sqrt(rate*(1-rate)/n + z*z/(4*n*n)) / denominator
    return (0.0 if failures == 0 else max(0.0, center-radius),
            1.0 if failures == n else min(1.0, center+radius))


def direct_mc(problem: Problem[_P], p: _P, *, trials: int, seed: int | None=None) -> Result:
    """Return a direct Monte Carlo Result for a fixed number of experiments.

    problem binds the model, noise, decoder, and shared failure definition.
    p is the noise parameter; trials is a positive fixed experiment count and
    seed controls its RNG. estimate and the Wilson interval describe logical
    failure probability per complete experiment. conditional_weight counts
    nonidentity coordinates in failed experiments. Raises ValueError for an
    invalid budget or noise sample outside support. The Wilson interval is
    not an optional-stopping interval.
    """
    start = time.perf_counter()
    positive_integer(trials, "trials")
    sequence = np.random.SeedSequence(seed)
    rng = np.random.default_rng(sequence)
    count, weight = 0, 0
    for _ in range(trials):
        state = problem.state(problem.noise.sample(p, rng))
        if not math.isfinite(problem.log_prob(state, p)):
            raise ValueError("noise.sample generated a state outside its support")
        if problem.is_faulty(state):
            count += 1
            weight += int(np.count_nonzero(state))
    warning = [] if count else ["zero failures observed; the true failure probability is not established as zero"]
    return Result("direct_mc", metadata(problem, p, dict(trials=trials,
        interval_method="Wilson score 95%, fixed trial count"), sequence),
        time.perf_counter()-start, estimate=count/trials, log_estimate=math.log(count/trials) if count else None,
        interval=_wilson(count, trials),
        trials=trials, failures=count, conditional_weight=weight/count if count else None,
        warnings=warning)


def sample_faulty(problem: Problem[_P], p: _P, *, config: SamplingConfig | None=None, seed: int | None=None, initial_state: ArrayLike | None=None) -> Result:
    """Sample normalized noise restricted to one fixed deterministic failure set.

    problem binds the model, noise, decoder, and shared failure definition.
    p is the noise parameter; config defines per-chain budgets and kernels.
    seed initializes independent chain streams. initial_state may be one
    supported faulty state or one such state per chain. Returns a Result whose
    states include every retained rejection and lazy self-loop. The samples
    describe a conditional distribution, not an experiment failure rate.
    Raises InitializationError if no faulty start is found within the budget,
    and ValueError on an invalid supplied start, support, or proposal ratio.

    Each chain uses a separate SeedSequence child. Burn-in and thinning are step
    counts; a rejection/lazy step still counts and can be retained as a repeat.
    Only the requested states are allocated. Decoder predictions are cached by
    complete syndrome; research_clear checks its soft cap every ten steps.
    """
    start = time.perf_counter()
    config = SamplingConfig() if config is None else config
    if not isinstance(config, SamplingConfig):
        raise ValueError("config must be SamplingConfig")
    kc = config.kernels
    from .circuit.model import CircuitFaultModel
    from .circuit.proposal import PhysicalFaultProposal
    from .circuit.cluster import PhysicalClusterExchange
    is_circuit = isinstance(problem.model, CircuitFaultModel)
    if is_circuit:
        if kc.stabilizer:
            raise ValueError("CircuitFaultModel does not support stabilizer kernels")
        if kc.cluster and kc.circuit_groups is None:
            raise ValueError("CircuitFaultModel cluster requires explicit circuit_groups")
    elif kc.circuit_single or kc.circuit_groups is not None:
        raise ValueError("circuit_single and circuit_groups require CircuitFaultModel")
    kernels: list[_Kernel] = [OBF(), Zanella(use_fastpath=kc.zanella_fastpath),
               ClusterExchange(kc.cluster_k), StabilizerFlip(), PhysicalFaultProposal()]
    if kc.circuit_groups is not None:
        physical_cluster = PhysicalClusterExchange(kc.circuit_groups, kc.cluster_k)
        physical_cluster._groups(problem)
        kernels[2] = physical_cluster
    cache = CachedDecoder(problem.decoder, cap=config.cache_cap,
                          policy=config.cache_policy)
    problem = replace(problem, decoder=cache)
    evaluator = FailureEvaluator(problem)
    from .faststep import make_faststep
    faststep = make_faststep(problem, p, enabled=kc.zanella_fastpath)
    probabilities = np.array([kc.single, kc.zanella, kc.cluster, kc.stabilizer, kc.circuit_single])
    cumulative_probabilities = np.cumsum(probabilities)
    if kc.stabilizer:
        cast(StabilizerFlip, kernels[3])._rows(problem)
        if faststep is not None:
            faststep.stabilizers = np.asarray(getattr(problem.model, "stabilizers"))
    sequence = np.random.SeedSequence(seed)
    children = sequence.spawn(config.chains)
    saved = np.empty((config.chains, config.samples, problem.model.n), dtype=np.uint8)
    acceptance: dict[str, dict[str, Any]] = {k.name: dict(proposed=0, accepted=0, moved=0) for k in kernels}
    acceptance["lazy"] = dict(proposed=0, accepted=0, moved=0)
    if initial_state is not None:
        initial = np.asarray(initial_state)
        if initial.shape == (problem.model.n,):
            initial = np.repeat(initial[None, :], config.chains, axis=0)
        if initial.shape != (config.chains, problem.model.n):
            raise ValueError("initial_state must have shape (n,) or (chains, n)")
    initial_attempts, effective_initial_states = [], []
    for chain, child in enumerate(children):
        rng = np.random.default_rng(child)
        if initial_state is not None:
            current = problem.state(initial[chain])
            if not math.isfinite(problem.log_prob(current, p)):
                raise ValueError("initial_state is outside noise support")
            faulty, current_syndrome = evaluator.evaluate(current)
            if not faulty:
                raise ValueError("initial_state must be faulty")
            attempts = 0
        else:
            for attempts in range(1, config.max_initial_attempts + 1):
                current = problem.state(problem.noise.sample(p, rng))
                if not math.isfinite(problem.log_prob(current, p)):
                    raise ValueError("noise.sample generated a state outside support")
                faulty, current_syndrome = evaluator.evaluate(current)
                if faulty:
                    break
            else:
                raise InitializationError("no faulty state found within max_initial_attempts; "
                                          "supply a supported faulty initial_state")
        initial_attempts.append(attempts)
        effective_initial_states.append(current.tolist())
        current_log = problem.log_prob(current, p)
        if faststep is not None:
            faststep.start(current)
        total_steps = config.burn_in + config.samples * config.thin
        index = 0
        for step in range(total_steps):
            if step and step % 10 == 0:
                cache.boundary()
            if rng.random() < kc.lazy:
                acceptance["lazy"]["proposed"] += 1
                acceptance["lazy"]["accepted"] += 1
            else:
                # CDF selection uses caller probabilities without renormalizing.
                chosen = int(cumulative_probabilities.searchsorted(rng.random(), side="right"))
                chosen = min(chosen, len(kernels)-1)
                kernel = kernels[chosen]
                stats = acceptance[kernel.name]
                stats["proposed"] += 1
                if faststep is not None:
                    current, current_log, current_syndrome = faststep.attempt(
                        current, current_log, cast(np.ndarray, current_syndrome), kernel, rng, stats)
                else:
                    proposal = kernel.propose(current, problem, p, rng)
                    candidate = problem.state(proposal.state)
                    lp = problem.log_prob(candidate, p)
                    log_ratio = proposal.log_reverse_forward
                    if np.isnan(log_ratio) or log_ratio == np.inf:
                        raise ValueError("invalid proposal ratio")
                    if math.isfinite(lp):
                        faulty, candidate_syndrome = evaluator.evaluate(
                            candidate, previous=current,
                            previous_syndrome=current_syndrome)
                    else:
                        faulty = False
                    if faulty:
                        u = rng.random()
                        if (math.log(u) if u else -np.inf) < min(0, lp-current_log+log_ratio):
                            stats["accepted"] += 1
                            stats["moved"] += int(not np.array_equal(current, candidate))
                            current, current_log = candidate, lp
                            current_syndrome = candidate_syndrome
            if step >= config.burn_in and (step-config.burn_in+1) % config.thin == 0:
                saved[chain, index] = current
                index += 1
    run_config = {**asdict(config), "n_replicas": 1,
                  "preset": "Z+H" if kc == KernelConfig() else "custom",
                  "initialization_attempts": initial_attempts,
                  "initial_states": effective_initial_states,
                  "initialization": "provided" if initial_state is not None else "noise_sample",
                  "acceptance_scope": "all steps, including burn-in",
                  "decode_cache": {"cap": config.cache_cap,
                                   "policy": config.cache_policy,
                                   "size_at_end": cache.size,
                                   "research_clear_boundary_steps": 10},
                  "expanded_move_probabilities": {**{k.name: float((1-kc.lazy)*w)
                      for k, w in zip(kernels, probabilities)}, "lazy": kc.lazy}}
    for stats in acceptance.values():
        stats["acceptance_rate"] = stats["accepted"] / stats["proposed"] if stats["proposed"] else None
        stats["move_rate"] = stats["moved"] / stats["proposed"] if stats["proposed"] else None
    result = Result("sample_faulty", metadata(problem, p, run_config, sequence, children),
                    time.perf_counter()-start, states=saved, acceptance=acceptance)
    result.diagnostics = diagnose(result)
    result.warnings = list(result.diagnostics["warnings"])
    return result
