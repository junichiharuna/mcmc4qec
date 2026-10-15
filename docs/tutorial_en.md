# Tutorial: from a first estimate to your own model

[Documentation](index.md) · [README](../README.md) · [日本語版](tutorial_ja.md) · [API reference](api_en.md)

Start with the README's toric example, inspect its components and results, then adjust sampling and diagnostics before replacing components with your own.
The initial example needs the `codes` and `matching` extras.
Later examples using small custom models run with core dependencies alone.
Each Python block can be run independently.

Follow the [first estimate](#estimate-a-toric-codes-logical-error-probability), then [choose a method](#choose-a-method), [set the sampling budget](#set-the-sampling-budget), and [read diagnostics](#initialization-cache-and-diagnostics).
The [saving example](#save-and-reload-results) uses a tiny model and core dependencies only.
When adapting the library, start with [your CSS matrices](#your-css-matrices) and check small instances by enumeration before increasing the problem size.

## Estimate a toric code's logical error probability

From a local checkout, install the package with code factories and PyMatching:

```sh
python -m pip install -e ".[codes,matching]"
```

This example estimates logical error probabilities for a distance-3 toric code under independent bit flips with an MWPM decoder.
It follows physical bit-flip probabilities `0.2 → 0.15 → 0.1` and prints an estimate and uncertainty interval at each rate.

```python
import mcmc4qec as qec

code = qec.make_toric_code(3)
noise = qec.IndependentBitFlip(code.n)
decoder = qec.mwpm_decoder(code)
problem = qec.Problem(code.bit_flip_model(), noise, decoder)

# Physical bit-flip probabilities, from the anchor to the target.
ladder = [0.2, 0.15, 0.1]
result = qec.estimate_logical_error(problem, ladder)

for p, estimate, interval in zip(ladder, result.estimates, result.intervals):
    print(f"p={p}: P_L={estimate:.6g}, interval={interval}")
```

Each output row gives a physical bit-flip probability `p`, the estimated logical error probability `P_L`, and its uncertainty interval.
These settings provide an initial run.
For research use, review sample counts and diagnostics and adjust the settings accordingly.

## Understand the example

### Code, noise, and decoder

The `code` returned by `make_toric_code(3)` contains the matrices defining the code.
Its attributes in this example are:

| Attribute | Meaning | Value or shape in this example |
| --- | --- | --- |
| `code.n` | Number of physical qubits | `18` |
| `code.hx`, `code.hz` | X and Z check matrices | `(9, 18)` each |
| `code.lx`, `code.lz` | X and Z logical-operator matrices | `(2, 18)` each |

`code.bit_flip_model()` builds a model that maps bit-flip errors to syndromes and logical observables, using `hz` and `lz`, respectively.
`noise` supplies the error distribution, and `decoder` predicts logical observables from syndromes.
`Problem` combines the model, noise, and decoder, judging decoding success by whether the predicted logical observables match the actual ones.
To define your own matrices or decoder, follow the [CSS tutorial](#your-css-matrices).

### Noise ladder and reference probability

`ladder` lists the noise rates used for estimation.
The example first computes the logical error probability at `p=0.2` as a reference value (**anchor**).
BAR then estimates probability ratios between adjacent noise rates to obtain the estimates at `p=0.15` and `p=0.1`.

The anchor is computed by exact enumeration for small state spaces and by direct Monte Carlo otherwise.
Pass `anchor` to supply a reference result computed separately.
Use `config` to adjust sample counts and other sampling settings, and pass an integer such as `seed=73` for reproducibility with the same settings.
All three arguments are optional.
See the [API settings example](api_en.md#automatic-bar-anchor) for defaults and configuration.

## Choose a method

All four methods use the same `Problem` and failure definition, but they answer different questions.

| Method | What it does | When to start here |
| --- | --- | --- |
| `exact(problem, p)` | Sums the normalized probability of every failing state | Validate a small model, decoder, or custom noise before sampling |
| `direct_mc(problem, p, trials=..., seed=...)` | Draws independent experiments and estimates `failures / trials` | Failures occur often enough to observe within a fixed trial budget |
| `sample_faulty(problem, p, ...)` | Samples states conditioned on failure | Study typical failure patterns or a conditional observable |
| `estimate_logical_error(problem, ladder, ...)` | Combines an absolute anchor probability with adjacent BAR ratios | Estimate a sequence of failure probabilities using conditional sampling |

Exact enumeration grows with the product of all coordinate alphabet sizes: an `n`-bit model has `2**n` states.
It has no Monte Carlo sampling error, but still uses floating-point arithmetic.
Direct MC with no observed failures does not establish zero failure probability; inspect its interval and trial count.
Conditional MCMC deliberately keeps only failing states, so counting failures in its saved states cannot estimate the absolute failure probability.
BAR supplies that missing normalization through the anchor.

For a new problem, first check an enumerable instance, compare direct MC where failures are observable, and then use a ladder to explore lower probabilities.
The ladder needs at least two distinct adjacent coordinates; the tutorial uses decreasing rates so its first rate is convenient for the anchor.
The ordering alone does not ensure that neighboring conditional distributions overlap or that chains mix.

## BAR with default settings

No `config` or `anchor` is required. The default `SamplingConfig()` retains 1,000 samples after 100 burn-in steps per rung, with one chain, thinning 1, Z/H weights 0.7/0.3, `cluster_k=2`, and lazy probability 0.05. Pass a `SamplingConfig` to tune the run; these defaults do not establish research accuracy, and physical circuit models still require appropriate kernel settings.

The first rung's anchor is computed by exact enumeration if the product of coordinate alphabet sizes is at most 4,096, and otherwise by 10,000 fixed direct-MC trials. For example, `qec.estimate_logical_error(problem, ladder, anchor_max_states=0, anchor_trials=20000, seed=73)` forces a 20,000-trial MC anchor. Its independent RNG and uncertainty are recorded and propagated into the result. You can instead provide `anchor=qec.exact(problem, ladder[0])` for a small problem or a compatible independent `qec.direct_mc` result.

An MC anchor with zero failures or all trials failing raises `ValueError`; increase the trial budget, change the first noise rate, or supply a valid anchor. The automatic calculation does not extend its trial count until failures appear. Inspect warnings and `result.metadata["anchor"]`, and check mixing and sensitivity before interpreting intervals. See [automatic-anchor settings](api_en.md#automatic-bar-anchor) for validation and provenance details.

To change the sampling budget, pass, for example, `config=qec.SamplingConfig(samples=2000, burn_in=200, chains=4)` in the toric call above.
These numbers illustrate the settings rather than prescribing a sufficient run length.
Compare results across run lengths and initial states, and inspect the diagnostics below.

The first toric example has `2**18 = 262144` possible bit-flip states, so its automatic anchor uses direct MC with the default state limit of 4,096.
The anchor has statistical uncertainty even though the code's distance is only three.

## Set the sampling budget

`SamplingConfig` controls conditional sampling in both `sample_faulty` and every BAR rung.
The counts apply to each chain, not to the whole run.

| Field and default | Meaning |
| --- | --- |
| `samples=1000` | Number of retained states per chain after burn-in |
| `burn_in=100` | Transitions performed before retaining states; this is a chosen count, not an automatic convergence test |
| `thin=1` | Number of transitions between retained states |
| `chains=1` | Number of independent RNG streams; chains currently execute sequentially |
| `max_initial_attempts=10000` | Maximum noise draws per chain when searching for a failing initial state |
| `kernels=KernelConfig()` | Proposal mixture and lazy-step settings |
| `cache_cap=None` | No limit on the number of cached decoder predictions |
| `cache_policy="research_clear"` | Soft-cap policy; `"lru"` and `"freeze"` enforce strict caps when a cap is supplied |

For example, `samples=2000, burn_in=200, thin=2, chains=4` retains 8,000 states per rung and performs `4 * (200 + 2000 * 2) = 16800` transitions, excluding initialization.
Increasing `thin` with `samples` fixed increases computation; it does not guarantee independent saved states.
Every rejected proposal and lazy step counts as a transition, and repeated retained states are part of the sample.
Do not remove duplicates before analyzing a trace.
For conditional MCMC, `run.states.shape` is `(chains, samples, number_of_coordinates)`.

`KernelConfig` separates the move mixture from the lazy probability.
The weights `single`, `zanella`, `cluster`, `stabilizer`, and `circuit_single` must sum to one; they are not automatically normalized.
With the defaults, a step is lazy with probability 0.05, selects Z with probability `0.95 * 0.7`, and selects H with probability `0.95 * 0.3`.
For the binary model above, `cluster_k=2` exchanges two occupied and two empty coordinates in an H proposal.
If the selected move cannot change the state, that step remains in the chain.
Start with the defaults for supported static models and change one setting at a time while comparing diagnostics and estimates.

## Read estimates and uncertainty

Statistical uncertainty is returned with numerical estimates by default.
In the BAR example, `result.estimates` and `result.intervals` follow the order of `ladder`.

| Method | Estimate | Uncertainty |
| --- | --- | --- |
| Exact enumeration | `estimate` | No Monte Carlo sampling interval |
| Direct MC | `estimate` | 95% Wilson `interval` |
| BAR | `estimates` | `intervals` and `log_standard_errors` at each noise rate |
| Failure-conditioned MCMC | `conditional_weight` | `conditional_weight_standard_error`: autocorrelation-aware standard error of the mean weight |

BAR uses block bootstrap by default.
With at least two independent chains, `uncertainty="cross_chain"` instead estimates uncertainty from variation between chains.
Unavailable errors are `None`, not zero.

For BAR, `result.estimate` and `result.interval` select the final rung; the plural fields contain all rungs.
`log_estimates` and `log_standard_errors` use natural logarithms: a log standard error is not a standard error in probability units.
Use the reported `intervals` when presenting probability intervals, and inspect `log_estimates` if a very small probability underflows to zero.

The conditional weight is the number of nonidentity coordinates, averaged over failing states.
It counts flipped bits for a bit-flip model and occupied fault locations for a physical circuit model; it is not the logical failure probability or an importance weight.
Its MCSE describes uncertainty in that conditional mean.
Neither that MCSE nor BAR's reported intervals include arbitrary model misspecification or bias from inadequate mixing.

There are two separate bootstrap controls:

| Setting | Quantity whose uncertainty is analyzed |
| --- | --- |
| `estimate_logical_error(..., bootstrap_replicates=100, bootstrap_block_length=...)` | BAR logical-probability estimates; block length is measured in retained samples per chain |
| `DiagnosticsConfig(bootstrap_replicates=200, block_sizes=...)` | Conditional observable means; several block lengths can be compared |

BAR's default block length is the rounded cube root of `samples`.
Setting its `bootstrap_replicates=0` disables MCMC error bars in block-bootstrap mode.
Setting the diagnostic replicate count to zero skips only the diagnostic bootstrap, leaving ACF, IAT, and blocking analysis available.
Changing detailed diagnostic settings does not change BAR intervals.

Standard BAR uses the same decoder and failure definition throughout the ladder and requires a positive anchor and observed overlap between adjacent distributions.
Missing required observed overlap raises `OverlapError`.
The `p_dependent_decoder_approx` mode ignores changes in failure sets, and its uncertainty intervals omit that bias; see the [API reference](api_en.md) before using it.

## Initialization, cache, and diagnostics

To inspect diagnostics in a quick run, the following example uses a two-bit model with a simple failure condition.
`sample_faulty` samples conditioned on failure; its state frequencies alone do not estimate the absolute logical error probability.

Statistical errors accompany numerical results by default. A conditional MCMC run returns its weight mean and Monte Carlo standard error (MCSE), accounting for integrated autocorrelation time (IAT).
Diagnostics also include effective sample size (ESS) and classical split Gelman–Rubin R-hat.
Use `diagnostics=True` for additional autocorrelation function (ACF) arrays, blocking and bootstrap results, or provide `DiagnosticsConfig` to bound their cost:

```python
from mcmc4qec import (BinaryLinearModel, CallableDecoder, DiagnosticsConfig,
                      IndependentBitFlip, KernelConfig, Problem, SamplingConfig,
                      diagnostic_report, sample_faulty)

# Failure is x[0] == 1; x[1] remains a variable conditional observable.
problem = Problem(BinaryLinearModel([[1, 1]], [[1, 0]]), IndependentBitFlip(2),
                  CallableDecoder(lambda syndrome: [0], identifier="zero-v1"))
run = sample_faulty(problem, 0.3, seed=41,
    config=SamplingConfig(samples=128, burn_in=32, chains=4,
                          kernels=KernelConfig(cluster_k=1)),
    diagnostics=DiagnosticsConfig(max_lag=32, block_sizes=(1, 4, 16, 32),
                                  bootstrap_replicates=100, seed=7))
print("Conditional mean and MCSE:", run.conditional_weight,
      run.conditional_weight_standard_error)
report = run.diagnostics["trace_analysis"]
print("Classical split R-hat:", report["rhat"])
print("Chain IAT / ESS:", report["chain_iat"], report["chain_ess"])
print("ACF:", report["acf"])
print("Batch-mean SE scan:", report["blocking"])
print("Bootstrap mean intervals:", report["bootstrap"]["blocks"])

# Alternative observables can be analyzed afterwards without resampling.
last_bit = diagnostic_report(run, observable=lambda state: float(state[-1]),
    observable_name="last bit", config=DiagnosticsConfig(bootstrap_replicates=0))
print("Last-bit mean and MCSE:", last_bit["mean"], last_bit["iat_mcse"])
```

Omit `diagnostics` to skip extra analysis while still returning the default mean MCSE. In BAR, the same keyword adds per-rung reports to `result.diagnostics[i]["trace_analysis"]`. These are conditional observable errors; the logical-probability errors remain in `result.intervals` and `result.log_standard_errors`. The detailed analysis has its own RNG and does not affect sampled states or BAR uncertainty. `None` means unavailable, not zero error. Inspect block-length sensitivity, short/constant chains, and warnings before interpreting intervals. See the [API formulas and fields](api_en.md#default-statistical-errors-and-optional-detailed-diagnostics).

`minimum_weight_initial_state(code)` and `maximum_weight_initial_state(code)` choose among minimum representatives of the code's logical-basis cosets. `observable_sector_initial_state(code, bits)` requests a particular nonzero observable sector even when logical bases are independent, and `random_logical_sector_initial_state(code, seed=...)` chooses a nonzero sector. These are candidates: verify that the state lies in the noise support and fails under your actual decoder and predicate before passing it as `initial_state` to `sample_faulty`. Large stabilizer ranks use SciPy MILP and require proven optimality within `time_limit`.

For repeated decoding, `SamplingConfig(cache_cap=1000, cache_policy="lru")` applies a strict LRU cache; `"freeze"` stops adding entries at the cap, while `"research_clear"` checks the soft cap every ten steps. `KernelConfig(zanella_fastpath=True)` accelerates supported product noises without changing their target distribution. `diagnose` can summarize multiple chains, but an apparently healthy weight series is insufficient evidence of mixing. `evaluate_convergence` screens chain scaling, late stationarity, different starting populations, and IAT versus an independently estimated direct-MC **conditional observable variance**. Without that variance or a second initialization population, the corresponding checks remain unresolved.

Good ESS or R-hat values do not prove convergence, ergodicity, correctness, or nominal interval coverage.
Neither block bootstrap nor cross-chain uncertainty captures bias shared by poorly mixed chains.
The [BAR sensitivity study](bar_sensitivity_ja.md) records limitations found in short experiments.

### Read the diagnostic output

In the two-bit example, failure fixes `x[0]` to one while `x[1]` can vary, so the weight takes values one and two.
This makes the weight mean informative even though every saved state is a failure.
Read the report in this order:

1. Read `run.warnings` and the report's `warnings`; short or constant traces may make uncertainty unavailable.
2. Compare `chain_means`, `chain_iat`, and `chain_ess` across chains. A disagreement is a reason to investigate initialization and run length.
3. Inspect the ACF and IAT for persistence. Their units are retained samples: with `thin=5`, lag one spans five sampler transitions.
4. Compare the blocking SEs across block lengths. Longer blocks can represent longer correlations, but leave fewer batches; a single chosen length cannot certify accuracy.
5. Repeat with longer runs and different supported failing starts, comparing the observable and the BAR estimate relevant to your question.

R-hat here is classical raw split R-hat, not rank-normalized or folded R-hat.
The reported aggregate `ess` sums chain ESS estimates and is generally not the ESS of the pooled mean.
A constant trace does not establish zero uncertainty; the report can return `None` instead.

`DiagnosticsConfig.max_lag` is inclusive and must be smaller than `samples`; each `block_sizes` entry must be at most `samples`.
Its bootstrap replicate count must be zero or at least two.
Its default `seed=0` controls a separate analysis RNG, not the sampler RNG.
For an already saved run, `diagnostic_report` applies no additional burn-in or thinning and requires `observable_name` for a custom observable.
For numerical arrays you already have, `analyze_traces` accepts a vector or an equal-length `(chains, samples)` array of retained scalar observations.

## Save and reload results

Use `Result` for exact, direct-MC, and conditional-MCMC results, and `EstimationResult` for BAR results.
The following standalone example uses a four-state model, writes two JSON files in `output/tutorial/`, and reads them back.
The small sample budget demonstrates the interface, not research precision.

```python
from pathlib import Path
import mcmc4qec as qec

problem = qec.Problem(
    qec.BinaryLinearModel([[1, 1]], [[1, 0]]),
    qec.IndependentBitFlip(2),
    qec.CallableDecoder(lambda syndrome: [0], identifier="zero-v1"),
)
config = qec.SamplingConfig(
    samples=128, burn_in=32, chains=2,
    kernels=qec.KernelConfig(cluster_k=1),
)
run = qec.sample_faulty(problem, 0.3, config=config, seed=41)
bar = qec.estimate_logical_error(
    problem, [0.3, 0.2], config=config, seed=42,
    anchor=qec.exact(problem, 0.3), bootstrap_replicates=20,
)

directory = Path("output/tutorial")
directory.mkdir(parents=True, exist_ok=True)
run_path = directory / "conditional_run.json"
bar_path = directory / "bar_result.json"
run_path.write_text(run.to_json(), encoding="utf-8")
bar_path.write_text(bar.to_json(), encoding="utf-8")

restored_run = qec.Result.from_json(run_path.read_text(encoding="utf-8"))
restored_bar = qec.EstimationResult.from_json(bar_path.read_text(encoding="utf-8"))
print("Saved state shape:", restored_run.states.shape)
print("Final BAR estimate and interval:", restored_bar.estimate, restored_bar.interval)
print("Warnings:", restored_bar.warnings)
print("Sampling settings:", restored_run.metadata["config"])
```

`Result` preserves retained states when present, allowing later `diagnostic_report` calls.
`EstimationResult` preserves estimates and rung diagnostics but does not contain the underlying rung states.
JSON also records configuration, model and decoder metadata, RNG information, Python and NumPy versions, and a package-source fingerprint.
It does not reconstruct executable `Problem` objects or user callables, and it is not a checkpoint for resuming a chain.
Keep the code that builds the model and decoder, dependency versions, settings, and seeds alongside results when reproducing an experiment.
Saving the same filenames again replaces those files.

## Resolve common problems

| Symptom | What to check or change |
| --- | --- |
| Missing optional dependency | Install the extras required by that example; the custom two-bit examples need only core dependencies |
| `InitializationError` | No failing start was found within the search budget; supply a supported failing state or increase `max_initial_attempts` |
| Invalid supplied initial state | Check its shape, positive noise probability, and failure under the actual decoder and predicate |
| Zero-failure or all-failure MC anchor | Choose a suitable first rate, increase the fixed trial budget, or supply a compatible exact anchor |
| `OverlapError` | Check noise support and the common failure definition, inspect mixing, and try closer adjacent ladder rates |
| An interval or MCSE is `None` | Read warnings for short/constant chains, missing overlap in uncertainty calculations, or disabled uncertainty |
| Kernel probabilities do not sum to one | Specify the complete intended mixture, accounting for nonzero defaults; `lazy` is separate |

`sample_faulty(initial_state=...)` accepts a state shaped `(n,)` or one state per chain shaped `(chains, n)`.
BAR instead uses `initial_states=[...]`, with one entry per rung; an entry may be `None` to use noise-based initialization there.
These are initial states, not samples to include directly in the estimate.
Providing a failing start avoids the search but does not establish stationarity or adequate exploration of the failure set.

## Your CSS matrices

The following examples replace individual parts of `Problem` while keeping a finite state space and a deterministic failure definition.
They use small models so exact enumeration can check results before sampling.

Supply binary `hx`, `hz`, `lx`, and `lz` with the same number of columns. By default the logical rows must be complete paired bases: `hx @ hz.T = 0`, stabilizer/logical commutators vanish, and `lx @ lz.T` is the identity over GF(2). If you deliberately use independently ordered logical bases, pass `logical_basis="independent"`; their cross-pairing must be invertible, and the input rows are not rebased. `CSSCode` validates these conditions and raises `ValueError` on a mismatch. In the bit-flip model, `hz` measures X errors and `lz` maps them to logical observables.

```python
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, IndependentBitFlip, Problem, exact

code = CSSCode(hx=np.zeros((0, 3), dtype=int),
               hz=[[1, 1, 0], [0, 1, 1]],
               lx=[[1, 1, 1]], lz=[[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="my-repetition3-logical-decoder-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
print(exact(problem, 0.25).estimate)  # 0.15625
```

`CallableDecoder` returns predicted **logical observables**, not physical corrections. Keep the same decoder and failure predicate for standard BAR ladders.

## Static CSS phase flips

For binary Z-error support, `code.phase_flip_model()` measures syndrome with X checks (`hx`), reads logical observables with `lx`, and uses Z stabilizer rows (`hz`). The same `IndependentBitFlip(code.n)` represents the Bernoulli product distribution on Z-error support. For example, this three-qubit CSS code protects X errors but has no X checks to detect Z errors:

```python
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, IndependentBitFlip, Problem, exact

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
z_decoder = CallableDecoder(lambda syndrome: [0], identifier="zero-z-v1")
problem = Problem(code.phase_flip_model(), IndependentBitFlip(code.n), z_decoder)
print(exact(problem, 0.25).estimate)  # 0.4375
```

With optional PyMatching, `mwpm_decoder(code, errors="Z")` builds from `hx` and maps its physical correction through `lx`; `bposd_decoder(code, p, errors="Z", **kw)` does the same with a fixed BP-OSD prior. Both default to `errors="X"`, preserving the existing `hz`/`lz` decoder. A rectangular toric geometry alone does not establish unequal aggregate X/Z failure rates: compare them with exact enumeration when feasible or report Monte Carlo uncertainty. For bounded repeated measurements, `PhenomenologicalModel(..., data_noise="phase_flip")` uses binary Z data faults and noisy X checks. Its `PhenomenologicalNoise` still needs explicit `{"data": ..., "measurement": ...}` probabilities for the complete experiment.

## Your normalized noise

A custom noise object has `n`, matching `alphabets`, `sample(p, rng)`, `log_prob(state, p)`, and JSON-compatible `metadata()`. Its `log_prob` is the normalized log probability of the **full** state under parameter `p`. Return negative infinity for zero support. The sampler must draw from that same distribution. This example uses three different per-qubit rates while retaining a scalar ladder parameter:

```python
import math
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, Problem, exact

class UnequalBitFlip:
    n = 3
    alphabets = (2, 2, 2)
    scales = np.array([0.5, 1.0, 1.5])

    def sample(self, p, rng):
        rates = p * self.scales
        if np.any((rates < 0) | (rates > 1)):
            raise ValueError("rates must be in [0, 1]")
        return (rng.random(self.n) < rates).astype(np.uint8)

    def log_prob(self, state, p):
        rates = p * self.scales
        if np.any((rates < 0) | (rates > 1)):
            raise ValueError("rates must be in [0, 1]")
        state = np.asarray(state)
        if state.shape != (self.n,) or np.any((state != 0) & (state != 1)):
            raise ValueError("invalid state")
        probabilities = np.where(state, rates, 1 - rates)
        return float(np.log(probabilities).sum()) if np.all(probabilities > 0) else -math.inf

    def metadata(self):
        return {"identifier": "unequal-bit-flip-v1", "scales": self.scales.tolist()}

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="my-repetition3-logical-decoder-v1")
print(exact(Problem(code.bit_flip_model(), UnequalBitFlip(), decoder), 0.25).estimate)
```

For correlated noise, compute the true joint state probability. Replacing it with independent marginals changes both the target distribution and BAR ratios. Check normalization by enumeration on a small instance before sampling.

## Your physical-correction decoder

An existing object's `decode(syndrome)` may return a physical correction instead of logical observables. Declare `output_kind="correction"` and supply `logical_map` (`L`) explicitly. The adapter multiplies `L @ correction % 2`. The following deterministic table is a stand-in for an external decoder and can be replaced by a configured BP-OSD object:

```python
import numpy as np
from mcmc4qec import CSSCode, IndependentBitFlip, Problem, exact
from mcmc4qec.adapters import DecoderAdapter

class CorrectionDecoder:
    corrections = {(0, 0): (0, 0, 0), (1, 0): (1, 0, 0),
                   (1, 1): (0, 1, 0), (0, 1): (0, 0, 1)}

    def decode(self, syndrome):
        return self.corrections[tuple(syndrome)]

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
adapter = DecoderAdapter(CorrectionDecoder(), output_kind="correction",
                         logical_map=code.lz, identifier="my-correction-decoder-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), adapter)
print(exact(problem, 0.25).estimate)  # 0.15625
```

For a decoder returning logical predictions directly, use `output_kind="observable"` and omit `logical_map`. `settings` records configuration for provenance but does not configure the wrapped decoder. Pin its behavior during a run. A decoder for repeated measurements must accept the full selected syndrome history or difference representation. A custom failure predicate receives `(state, predicted, truth)` and must return a Boolean; the same predicate is used by exact enumeration, direct MC, and conditional MCMC. Do not assume it stays unchanged under stabilizer flips.

## Built-in codes and decoders

Install `python -m pip install -e ".[codes,matching]"` for the HGP-based factories and PyMatching. The same `Problem` contract applies to these codes:

```python
from mcmc4qec import IndependentBitFlip, Problem, direct_mc
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import mwpm_decoder

code = make_toric_code(3)
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
print(direct_mc(problem, 0.1, trials=100, seed=3).estimate)
```

Other factories include toric, surface, asymmetric toric, Hamming HGP, BB72/108/144, and concatenated Steane. Some preserve independently ordered logical rows through `logical_basis="independent"`; treat the rows as the supplied basis rather than assuming `lx[i]` flips only observable `i`. `bposd_decoder(code, p, **kw)` fixes its channel prior at construction. The depolarising sector constructors return both logical sectors in model order, while `DepolarizingNoise` continues to sample correlated X/Z components through joint I/X/Y/Z labels.

## Physical circuit faults

`stim_noise_locations(circuit)` lists supported single- and two-qubit Pauli noise target groups. A `CircuitFaultModel` assigns each selected location one exclusive category: no fault or one fault label. `CircuitFaultNoise` uses explicit location probabilities; `uniform_fault_noise(model)` is a convenience choice. The circuit's native noise probabilities are ignored by the physical likelihood and need not equal the supplied fault probabilities. `surface_logical_idle_problem(distance=3, decoder_p=0.01, basis="Z")` constructs a 2d-round rotated-surface midpoint-observable baseline with a PyMatching decoder. The DEM is used to construct that decoder; sampled states remain physical location choices. See `examples/circuit_baseline.py` for a runnable direct-MC example.

Conditional circuit MCMC supports physical single-fault moves with `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)` and Z+OBF with `KernelConfig(zanella=0.7, single=0.3, cluster=0, stabilizer=0)`, including mixtures of these moves. H requires explicit `circuit_groups`, and circuit stabilizer moves remain unavailable. The circuit builder supports specified Pauli noise instructions on deterministic Clifford detector circuits; it does not handle non-Pauli faults or correlations between locations. See [the kernel comparison](../examples/circuit_zanella.py) for conditional weights, acceptance rates, and IAT; these conditional samples do not estimate absolute `P_L`.

Each `circuit_groups` entry is a nonempty group of location indices from `model.locations`. Groups must be disjoint, and every location within a group must have the same channel and ordered fault alphabet; equal alphabet size alone is insufficient. If locations 1 and 2 meet that contract, `KernelConfig(single=.2, zanella=.4, circuit_single=.2, cluster=.2, cluster_k=1, circuit_groups=((1, 2),))` mixes all four moves. Omitted locations are unchanged by H. Groups are selected uniformly independently of the state; unavailable relocation branches remain self-loops, with no mixture renormalization. H preserves occupancy within each group and is generally reducible alone; mixing with other moves does not by itself prove connectivity of an arbitrary failure set. The proposal is also available as `PhysicalClusterExchange` from `mcmc4qec.circuit`.

With `zanella_fastpath=True`, exact built-in circuit model/noise pairs with the standard failure predicate reuse physical detector/observable effect tables and update only changed locations. Custom subclasses or failure predicates retain the general path. `python benchmarks/bench_circuit_step.py --steps 100 --compare-delta` compares the dedicated and general paths from a common faulty state and checks retained trajectories and acceptance counts.

DEM and physical circuit sampling use distinct noise models; neither example establishes reproduction of published circuit results.
See the [circuit validation record](circuit_baseline_ja.md) for tested cases and limitations.
