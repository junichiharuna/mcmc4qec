# RIMC

An experimental Python library for rare-event Monte Carlo in quantum error
correction. It provides inspectable finite-state CSS models for bit-flip,
depolarising, and phenomenological noise; exact enumeration, direct Monte
Carlo, failure-conditioned MCMC, and splitting with Bennett acceptance ratios
(BAR). Optional adapters connect existing decoders and Stim detector error models.

**Development status:** local pre-alpha. `rimc` is a provisional package name.
This is not a published release. Physical circuit-fault configurations, a
research-runner compatibility wrapper, and public release preparation remain
subsequent work. The research repository and its runner defaults are separate.

## Install locally

Python 3.11 or newer and NumPy are required. From this directory:

```console
python -m pip install .
python examples/bit_flip.py
```

To build and exercise an installed wheel:

```console
python -m pip install build pytest
python -m build --wheel
```

Install the resulting wheel into a separate environment, then run the example
and `python -m pytest --override-ini pythonpath= tests/` from this directory.
The override prevents the test configuration from importing `src/` in place of
the installed package. Optional decoder dependencies are not needed by the
example or core API.

## Quickstart

The three-qubit repetition code has one logical observable. The callable below
returns a **predicted logical observable**, not a physical correction.

```python
import numpy as np
from rimc import (
    CSSCode, CallableDecoder, IndependentBitFlip, Problem,
    SamplingConfig, KernelConfig, exact, direct_mc, sample_faulty, diagnose,
)

code = CSSCode(
    hx=np.zeros((0, 3), dtype=int),
    hz=[[1, 1, 0], [0, 1, 1]],
    lx=[[1, 1, 1]],
    lz=[[1, 0, 0]],
)
decoder = CallableDecoder(
    lambda syndrome: [int(tuple(syndrome) == (1, 0))],
    identifier="repetition3-minimum-weight-v1",
)
problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)

p = 0.25
reference = exact(problem, p)
mc = direct_mc(problem, p, trials=10_000, seed=18)
samples = sample_faulty(
    problem, p,
    config=SamplingConfig(
        samples=2_000, burn_in=100, chains=2,
        kernels=KernelConfig(cluster_k=1),
    ),
    seed=31,
)

print("Exact P_L:", reference.estimate)  # 3*p**2 - 2*p**3 = 0.15625
print("Direct MC P_L and 95% Wilson interval:", mc.estimate, mc.interval)
print("MCMC E[weight | faulty]:", samples.states.sum(axis=-1).mean())
print("Exact E[weight | faulty]:", reference.conditional_weight)
print("Weight-series diagnostics:", diagnose(samples))
```

The example sets `cluster_k=1` because this code is too small for a two-pair
exchange within its failure states. The public default is Z+H with Z probability
0.7, cluster probability 0.3, and `cluster_k=2`. There is one chain by default,
with no parallel tempering. A separate lazy probability of 0.05 leaves the
state unchanged before selecting a kernel; the kernel probabilities themselves
must sum to one. Thus the default per-step probabilities are 0.665 for Z, 0.285
for H, and 0.05 for lazy. All expanded settings are recorded in the result.

`sample_faulty` samples the distribution conditioned on failure. Its state
frequency does **not** estimate the absolute logical-error probability. Use
`exact` for small state spaces, fixed-trial `direct_mc`, or an anchored BAR
ladder. Zero
observed failures yields a zero point estimate and a positive upper confidence
bound; it does not establish that the true failure probability is zero.

## Contracts and extension points

The implemented state space is a finite vector of category labels, with an
explicit alphabet size for each coordinate. `BinaryLinearModel`
accepts binary check and observable matrices. `CSSCode.bit_flip_model()` uses
`hz` for the syndrome and `lz` for logical observables of X errors. CSS matrix
compatibility is validated before sampling.

- A model defines state validation, coordinate alphabets, syndrome, and true logical observables.
- A noise model supplies normalized `log_prob(state, p)` and `sample(p, rng)`
  on the same state space, with zero probability represented by negative
  infinity. `IndependentBitFlip(n, scales=...)` permits nonidentical per-bit
  probabilities `p * scales`; all resulting probabilities must be in [0, 1].
- A decoder must be deterministic for a fixed syndrome and fixed settings.
  Its common output is a binary vector of predicted logical observables.
  Callable implementations receive explicit identifiers for provenance.
- The default failure predicate compares predicted and true observables.
  `CallableFailure(function, identifier=...)` receives
  `(state, predicted, truth)`. Exact enumeration, direct MC, and MCMC share this
  predicate. A custom predicate need not be invariant under stabilizer moves.
- OBF (single-category replacement for nonbinary states), Zanella, cluster
  exchange, and static stabilizer proposals use the general MH
  density and forward/reverse proposal ratios. Cluster exchange swaps occupied
  and empty positions **within one state**; Pauli proposals also relabel occupied
  positions. Mixed state spaces select equal-alphabet groups. H preserves the
  number of nonzero labels in each such group; density ratios still matter.
  It does not exchange replicas. Static stabilizer moves re-evaluate the failure
  predicate. Phenomenological models do not expose static stabilizer updates.

Custom components must preserve these contracts, provide their metadata, and
keep their settings fixed during a run. Custom Python callables are not
serialized or reconstructed from the result; retain the source and identifiers
needed to recreate the problem.

The exported `Model`, `Noise`, and `Decoder` protocols describe the Python
interface. Metadata must be JSON compatible with no nonfinite numbers.

| Component | Required interface |
| --- | --- |
| Model | `n`, `alphabets` (binary default), `validate_state(state)`, `syndrome(state)`, `observables(state)`, `metadata()` |
| Noise | `n`, matching `alphabets`, `sample(p, rng)`, `log_prob(state, p)`, `metadata()` |
| Decoder | `predict(syndrome)`, `metadata()` |
| Custom failure | `__call__(state, predicted, truth)` returning a Boolean, `metadata()` |

Every rejected and lazy step counts as a Markov-chain step. Thinning applies
independently of acceptance, retaining repeated states rather than filtering
them out. The saved state shape is `(chains, samples, bits)`. Initialization has
a finite search limit: for very rare events, pass a known supported faulty
`initial_state`. Exhausting that search is not proof that the failure set is
empty. Exact enumeration has a state-count limit and is intended only for
small problems.

The Zanella implementation scans the single-coordinate neighbourhood using the full
log density. It is a correctness reference, not a performance-equivalent
replacement for the optimized research runner. Kernel balance and lazy steps
alone do not guarantee that all failure states communicate.

## Optional decoder adapters

`rimc.adapters.DecoderAdapter` wraps an existing deterministic object with a
`decode` method. The output meaning is a required argument. For a BP-OSD object
that returns a physical correction, use:

```python
from rimc.adapters import DecoderAdapter

# bp_osd is an existing ldpc.BpOsdDecoder configured by the caller.
decoder = DecoderAdapter(
    bp_osd,
    output_kind="correction",
    logical_map=code.lz,
    identifier="my-fixed-bp-osd-v1",
    distribution="ldpc",
    settings={"decoder_prior": 0.25},
)
```

`settings` records provenance; it does not configure or update the wrapped
decoder. Keep its prior fixed during a run. `output_kind="observable"` accepts
logical predictions directly and must not be combined with `logical_map`.
Input syndrome dimensions are preserved by the wrapper; this alone does not
provide a phenomenological model or validate its time boundaries.

For PyMatching, install `python -m pip install ".[matching]"`.
`PyMatchingAdapter` additionally requires `built_with_correlations=True` or
`False` and forwards a matching `enable_correlations` setting at decode time.
For a static check matrix, `matching_from_check_matrix(H, logical_map=L,
identifier=...)` builds an uncorrelated correction adapter, rejecting columns
with more than two checks instead of silently dropping hyperedges. An existing
Matching object's graph or DEM completeness cannot be reconstructed by the
wrapper; callers remain responsible for how that object was constructed.
`matching_from_dem` checks that each decomposition component is graphlike
before constructing a matching object; see the DEM scope below.

## Depolarising and repeated measurements

`DepolarizingModel(code)` and `DepolarizingNoise(code.n)` use labels
`I=0, X=1, Y=2, Z=3`, with probabilities `(1-p, p/3, p/3, p/3)`. Y carries both
X and Z components. The syndrome order is `[hz @ X, hx @ Z]` and the observable
order is `[lz @ X, lx @ Z]`, all modulo two. A decoder must predict this full
observable vector. Separate sector decoding is a decoder choice, never a
replacement of the joint Pauli noise by independent X/Z draws.

`PhenomenologicalModel` requires explicit time boundaries and representation:

```python
from rimc import PhenomenologicalModel, PhenomenologicalNoise

model = PhenomenologicalModel(
    code, rounds=2,
    initial_boundary="clean",
    final_boundary="perfect",
    representation="difference",  # or "history"
    data_noise="bit_flip",          # or "depolarizing"
)
noise = PhenomenologicalNoise(model)
p = {"data": 0.05, "measurement": 0.02}
```

Each round adds data faults before measurement. The clean initial syndrome is
zero. A perfect final boundary removes last-round measurement faults; it adds
neither an extra data round nor an extra measurement row. A noisy final boundary
retains those faults. Both representations produce `(rounds, n_checks)` decoder
input. Observables refer to the final cumulative data error. The failure rate
is for this entire bounded experiment; it is not silently converted to a
per-round rate. Both probability keys are required even if no measurement-fault
coordinates remain. Supply a decoder that understands the chosen full history.

## Splitting and BAR

```python
from rimc import estimate_logical_error

# Here problem is the fixed bit-flip Problem from the quickstart.
ladder = [0.4, 0.25, 0.1]
estimate = estimate_logical_error(
    problem, ladder, anchor=exact(problem, ladder[0]),
    config=SamplingConfig(samples=2_000, burn_in=100, chains=2),
    seed=73, bootstrap_replicates=100,
)
print(estimate.estimates, estimate.intervals)
```

The anchor must be a positive `exact` or fixed-trial `direct_mc` result whose
parameter, model, noise, failure, and decoder metadata match the first rung.
An exact anchor below floating-point probability range remains usable through
its finite `log_estimate`; an observed zero-failure MC anchor does not.
Every rung uses a separate random stream. The default `mode="fixed_failure"`
holds the same decoder object and failure predicate across the ladder and uses
full cross log densities. Parameter dictionaries support data/measurement
ladders. Missing observed support overlap raises `OverlapError`.

The explicitly selected `mode="p_dependent_decoder_approx"` requires
`decoder_factory(prior)`, one `decoder_priors` entry per rung, and a nonempty
`approximation_reason`. Density-only BAR then ignores changes in failure sets.
It can be seriously biased, including estimates above one; such point estimates
are retained with warnings and no interval. This mode does not repair a changing
failure definition. Sampling coordinates, decoder priors, and the reason are saved.

Uncertainty uses a circular block bootstrap within each chain, sharing each
rung's resampled indices between adjacent ratios to retain their covariance.
The default block length is approximately the cube root of retained samples;
set `bootstrap_block_length` to inspect sensitivity. An independent MC anchor
adds a binomial delta approximation to log variance; an exact anchor adds none.
These intervals assume adequate mixing and block length. They omit approximation
bias and may miss long correlations. `bootstrap_replicates=0` explicitly omits
MCMC error bars. Failed-overlap bootstrap draws make the error bars unavailable.
For probabilities that underflow floating-point representation, use
`log_estimates`; rounded zero values do not establish a zero failure probability.

## Stim DEM scope

`from_stim_dem(dem)` returns `(model, noise)`, representing each complete `error`
instruction as one latent Bernoulli bit. Pieces separated by `^` remain correlated
parts of that same mechanism. A fixed DEM requires `p=None` in exact/MC/MCMC.
For a ladder, supply an explicit `probabilities(p)` or `dem_factory(p)` with a
`family_identifier`. A DEM factory must preserve mechanism signatures/order and
H/L matrices; a probabilities callback supplies one probability per fixed mechanism.

`from_stim_circuit(circuit, decompose_errors=False,
approximate_disjoint_errors=False)` records both conversion choices. It never
silently retries with a disjoint-error approximation. This path samples the DEM
distribution. It does not implement mutually exclusive physical `(gate, fault)`
configurations or establish equivalence to every original circuit noise model.
Physical circuit-fault MCMC and the referenced circuit-paper experiment remain
future work. Stim and PyMatching are optional imports used only by these adapters.

## Results and diagnostics

`Result.to_json()` and `Result.from_json(text)` preserve numerical results and
run metadata. Results record model/noise/decoder identities, model hashes,
configuration, random-seed information, source provenance, and elapsed time.
Some provenance may be unavailable in an unpacked source tree or wheel; absent
source information must not be interpreted as a verified commit.
The current local prototype records its unavailable source commit separately
from the fixed research reference commit; these are different provenance fields.

`diagnose(result)` examines the nonzero-coordinate count (binary Hamming weight)
using IAT, ESS, and
split R-hat where meaningful. Short or constant series return unavailable
diagnostics with explanations. A healthy diagnostic is not proof of convergence,
ergodicity, or an unbiased estimate. In particular, a trapped chain can have an
apparently healthy weight trace.

## Development and next stages

The Japanese [initial-library design and limitations](docs/initial_library_ja.md)
describes the current implementation boundary and remaining work.
The [stage-one document](docs/stage1_ja.md) preserves the earlier binary milestone.
See
[CONTRIBUTING.md](CONTRIBUTING.md) for tests and release preparation.

The license, final distribution name, release destination, and complete
citation metadata remain undecided. No license is selected by this prototype,
and no public repository or package publication is performed here.
