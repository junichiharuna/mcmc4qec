"""Exact enumeration, fixed-budget direct MC, and conditional MH sampling."""
from dataclasses import asdict, dataclass, field
import itertools
import math
import time

import numpy as np
from .core import positive_integer
from .kernels import OBF, Zanella, ClusterExchange, StabilizerFlip
from .results import Result, metadata
from .diagnostics import diagnose


class InitializationError(RuntimeError):
    """No supported faulty initial state found within the finite search budget."""


@dataclass(frozen=True)
class KernelConfig:
    single: float = 0.0
    zanella: float = 0.7
    cluster: float = 0.3
    stabilizer: float = 0.0
    cluster_k: int = 2
    lazy: float = 0.05

    def __post_init__(self):
        weights = [self.single, self.zanella, self.cluster, self.stabilizer]
        if any(not np.isfinite(w) or w < 0 for w in weights):
            raise ValueError("kernel probabilities must be finite and nonnegative")
        if not math.isclose(sum(weights), 1, rel_tol=0, abs_tol=1e-12):
            raise ValueError("kernel probabilities must sum to 1; no implicit normalization")
        positive_integer(self.cluster_k, "cluster_k")
        if not np.isfinite(self.lazy) or not 0 <= self.lazy < 1:
            raise ValueError("lazy must be in [0, 1)")


@dataclass(frozen=True)
class SamplingConfig:
    samples: int = 1000
    burn_in: int = 100
    thin: int = 1
    chains: int = 1
    max_initial_attempts: int = 10000
    kernels: KernelConfig = field(default_factory=KernelConfig)

    def __post_init__(self):
        for name in ("samples", "thin", "chains", "max_initial_attempts"):
            positive_integer(getattr(self, name), name)
        positive_integer(self.burn_in, "burn_in", zero=True)
        if not isinstance(self.kernels, KernelConfig):
            raise ValueError("kernels must be KernelConfig")


def spawn_seeds(seed, count):
    """Deterministic independent child seeds for caller-managed workers."""
    positive_integer(count, "count")
    return [int(s.generate_state(1, dtype=np.uint64)[0])
            for s in np.random.SeedSequence(seed).spawn(count)]


def exact(problem, p, *, max_states=1_048_576):
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


def _wilson(failures, n):
    z = 1.959963984540054
    rate = failures/n
    denominator = 1 + z*z/n
    center = (rate + z*z/(2*n)) / denominator
    radius = z*math.sqrt(rate*(1-rate)/n + z*z/(4*n*n)) / denominator
    return (0.0 if failures == 0 else max(0.0, center-radius),
            1.0 if failures == n else min(1.0, center+radius))


def direct_mc(problem, p, *, trials, seed=None):
    """Fixed trial budget: Wilson interval is not an optional-stopping interval."""
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


def sample_faulty(problem, p, *, config=None, seed=None, initial_state=None):
    """Sample normalized noise restricted to one fixed deterministic failure set.

    Each chain uses a separate SeedSequence child. Burn-in and thinning are step
    counts; a rejection/lazy step still counts and can be retained as a repeat.
    Only the requested states are allocated; decoder results are never cached.
    """
    start = time.perf_counter()
    config = SamplingConfig() if config is None else config
    if not isinstance(config, SamplingConfig):
        raise ValueError("config must be SamplingConfig")
    kc = config.kernels
    kernels = [OBF(), Zanella(), ClusterExchange(kc.cluster_k), StabilizerFlip()]
    probabilities = np.array([kc.single, kc.zanella, kc.cluster, kc.stabilizer])
    if kc.stabilizer:
        kernels[-1]._rows(problem)
    sequence = np.random.SeedSequence(seed)
    children = sequence.spawn(config.chains)
    saved = np.empty((config.chains, config.samples, problem.model.n), dtype=np.uint8)
    acceptance = {k.name: dict(proposed=0, accepted=0, moved=0) for k in kernels}
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
            if not problem.is_faulty(current):
                raise ValueError("initial_state must be faulty")
            attempts = 0
        else:
            for attempts in range(1, config.max_initial_attempts + 1):
                current = problem.state(problem.noise.sample(p, rng))
                if not math.isfinite(problem.log_prob(current, p)):
                    raise ValueError("noise.sample generated a state outside support")
                if problem.is_faulty(current):
                    break
            else:
                raise InitializationError("no faulty state found within max_initial_attempts; "
                                          "supply a supported faulty initial_state")
        initial_attempts.append(attempts)
        effective_initial_states.append(current.tolist())
        current_log = problem.log_prob(current, p)
        total_steps = config.burn_in + config.samples * config.thin
        index = 0
        for step in range(total_steps):
            if rng.random() < kc.lazy:
                acceptance["lazy"]["proposed"] += 1
                acceptance["lazy"]["accepted"] += 1
            else:
                # CDF selection uses caller probabilities without renormalizing.
                chosen = int(np.searchsorted(np.cumsum(probabilities), rng.random(), side="right"))
                chosen = min(chosen, len(kernels)-1)
                kernel = kernels[chosen]
                stats = acceptance[kernel.name]
                stats["proposed"] += 1
                proposal = kernel.propose(current, problem, p, rng)
                candidate = problem.state(proposal.state)
                lp = problem.log_prob(candidate, p)
                log_ratio = proposal.log_reverse_forward
                if np.isnan(log_ratio) or log_ratio == np.inf:
                    raise ValueError("invalid proposal ratio")
                if math.isfinite(lp) and problem.is_faulty(candidate):
                    u = rng.random()
                    if (math.log(u) if u else -np.inf) < min(0, lp-current_log+log_ratio):
                        stats["accepted"] += 1
                        stats["moved"] += int(not np.array_equal(current, candidate))
                        current, current_log = candidate, lp
            if step >= config.burn_in and (step-config.burn_in+1) % config.thin == 0:
                saved[chain, index] = current
                index += 1
    run_config = {**asdict(config), "n_replicas": 1,
                  "preset": "Z+H" if kc == KernelConfig() else "custom",
                  "initialization_attempts": initial_attempts,
                  "initial_states": effective_initial_states,
                  "initialization": "provided" if initial_state is not None else "noise_sample",
                  "acceptance_scope": "all steps, including burn-in",
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
