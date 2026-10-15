# mcmc4qec
Estimate logical error probabilities for CSS quantum codes with exact enumeration, direct Monte Carlo, and anchored Bennett acceptance ratio (BAR) splitting.
Sample errors conditioned on failure with configurable one-bit flip (OBF), Zanella (Z), cluster exchange (H), and stabilizer kernels.

Bring your own code, normalized noise distribution, deterministic decoder, and failure predicate, following the [API contracts](docs/api_en.md) for supported inputs and custom components.
The public APIs include type annotations and a `py.typed` marker for IDEs and type checkers.

This pre-alpha package is under active validation. [日本語版](README_ja.md).

## Install and first run

Install a local checkout with `python -m pip install -e .` to run the core examples without optional dependencies. For the following toric example, use `python -m pip install -e ".[codes,matching]"` because `make_toric_code` currently requires the `codes` extra.

| Extra | Use |
| --- | --- |
| `codes` | Toric, surface, asymmetric toric, Hamming HGP, and BB code factories |
| `matching` | PyMatching decoders |
| `bposd` | BP-OSD decoder dependency |
| `stim` | Stim DEM and circuit examples |
| `plot` | Optional PNG plots in workflow scripts; CSV remains available without it |
| `notebooks` | Jupyter notebook execution and plotting |

To install several extras at once, use `python -m pip install -e ".[codes,matching,bposd,stim,plot,notebooks]"`, and consult the [full example index](examples/README.md) for each file's dependencies.

PyMatching 2.4 itself requires matplotlib, even though workflow scripts can produce CSV output when the pyplot drawing layer is unavailable.

```python
import numpy as np
from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig, direct_mc, sample_faulty
from mcmc4qec.adapters import matching_from_check_matrix
from mcmc4qec.codes import make_toric_code

code = make_toric_code(5)
decoder = matching_from_check_matrix(code.hz, logical_map=code.lz,
                                     identifier="toric-d5-mwpm")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
p = 0.1
mc = direct_mc(problem, p, trials=2_000, seed=11)
chain = sample_faulty(problem, p, config=SamplingConfig(samples=100, burn_in=20), seed=12)
print("Direct MC P_L and 95% Wilson interval:", mc.estimate, mc.interval)
print("Direct MC E[weight | faulty]:", mc.conditional_weight)
print("Z+H E[weight | faulty] and MCSE:", chain.conditional_weight,
      chain.conditional_weight_standard_error)
```

The conditional chain is a sequence of sampled states that measures properties **within** the failure set, whose state frequencies do not estimate the absolute logical failure probability `P_L`. The defaults are Z weight 0.7, H weight 0.3, `cluster_k=2`, one chain, and a separate lazy probability of 0.05. The trace retains rejected and lazy steps, and you can run the full example with `python examples/toric_pymatching.py`.

A BAR ladder estimates `P_L(p)` at a sequence of noise probabilities, with each probability called a rung. An anchor supplies the absolute logical failure probability at one rung. This example uses a small enumerable code to anchor the first rung exactly.

```python
import numpy as np
from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip, KernelConfig,
                      Problem, SamplingConfig, estimate_logical_error, exact)

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="repetition3-minimum-weight-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
ladder = [0.4, 0.25, 0.1]
result = estimate_logical_error(problem, ladder, anchor=exact(problem, ladder[0]),
                                config=SamplingConfig(samples=200, burn_in=30,
                                    kernels=KernelConfig(cluster_k=1)), seed=73)
print(result.estimates, result.intervals)
```

The complete runnable ladder, including its three-bit `Problem`, is in [examples/bar_ladder.py](examples/bar_ladder.py), and a standard ladder requires the same decoder and failure definition at every rung. A Monte Carlo (MC) anchor must observe positive failure mass, and the estimator raises `OverlapError` when observed support overlap is missing.

## Statistical errors and MCMC diagnostics

Numerical results include statistical uncertainty by default, with the estimate and uncertainty fields for each method shown in the table below.

| Method | Estimate and uncertainty |
| --- | --- |
| Direct MC | `estimate` and the 95% Wilson `interval` for logical failure probability |
| BAR | `estimates`, `intervals`, and `log_standard_errors` at each rung |
| Conditional MCMC | `conditional_weight` and `conditional_weight_standard_error`, the IAT-based Monte Carlo standard error (MCSE) of the mean weight |

Conditional MCMC also returns the integrated autocorrelation time (IAT) and effective sample size (ESS) of each chain in `result.diagnostics`. Other diagnostics include classical split Gelman–Rubin R-hat, standard errors across chains, and acceptance statistics. Detailed autocorrelation function (ACF) arrays, scans over block lengths, and bootstrap intervals are **optional**, enabled with `diagnostics=True` and configured with `DiagnosticsConfig`.

```python
from mcmc4qec import (BinaryLinearModel, CallableDecoder, DiagnosticsConfig,
                      IndependentBitFlip, KernelConfig, Problem, SamplingConfig,
                      sample_faulty)

# Core-only example: failure is x[0] == 1; x[1] still fluctuates.
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
print("Blocking SE scan:", report["blocking"])
print("Bootstrap mean intervals:", report["bootstrap"]["blocks"])
```

Omit `diagnostics` to skip detailed analysis while retaining the default mean MCSE, or set `DiagnosticsConfig(bootstrap_replicates=0)` to skip only the additional bootstrap. `report["acf"]` contains ACF values and lags for each chain, with lag and block lengths measured in retained samples. Reports contain numbers and arrays compatible with JSON, and `run.to_json()` preserves them without requiring plotting packages. `estimate_logical_error` accepts the same option and returns one report per rung in `result.diagnostics[i]["trace_analysis"]`.

Analysis uses a separate random number generator (RNG), so sampling trajectories and BAR estimates and intervals remain unchanged. The added bootstrap intervals describe a **conditional observable mean**, not the absolute logical failure probability. Unavailable errors are represented by `None` rather than zero, and short or constant chains may be uninformative. Classical split R-hat differs from rank-normalized and folded R-hat, and good diagnostics or narrow intervals do not prove convergence or nominal coverage.

Use `diagnostic_report` for existing Results and custom observables, or `analyze_traces` for numerical traces, as described in the [API formulas and settings](docs/api_en.md#default-statistical-errors-and-optional-detailed-diagnostics) and [post-processing example](docs/tutorial_en.md#initialization-cache-and-diagnostics).

## Performance

The dedicated step path applies to exact built-in linear or physical circuit models paired with product noise and the standard logical failure predicate, while custom subclasses or failure predicates use the general path.

Two local runs on Windows 11 Pro, Python 3.11.9, and an AMD Ryzen 5 3600 measured the following rates at p=0.01, with 10,000 steps, Z/H weights 0.7/0.3, `cluster_k=2`, one chain, and `lazy=0` (2026-10-15).

| Code | Library steps/s | Research runner steps/s | Library/research time |
| --- | ---: | ---: | ---: |
| Toric d=5 | 12,026–12,281 | 23,000–23,028 | 1.87–1.91× |
| Toric d=7 | 10,381–10,477 | 20,147–20,162 | 1.92–1.94× |
| BB72 | 6,113–6,157 | 7,914–8,186 | 1.29–1.33× |

The measured toric workloads meet the target of at most twice the research runner's time in both repetitions. Library timings include result construction and diagnostics, and both timings exclude decoder construction. The two runs share seed 731 and measure timing variation, not independent sampling accuracy. See the [measurement record](docs/performance_ja.md) for the comparison before and after optimization, decoder settings, and limitations.

Run `python benchmarks/bench_step.py --steps 10000 --repeats 2 --seed 731`, with `RIMC_RESEARCH_ROOT` (or `MCMC4QEC_RESEARCH`) set to a read-only research checkout for comparison. The script needs the `codes` and `matching` extras and measures only the library if neither variable is set. It supports `--quick` and `--out` and writes CSV to a temporary directory by default. Rates vary with hardware and load and do not establish mixing or estimation accuracy.

## Choose a starting point

| Goal | Start here |
| --- | --- |
| Estimate absolute `P_L` | [Steane exact/MC/BAR comparison](examples/steane_exact.py), [toric BAR curve](examples/workflows/pl_curve.py), or [BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| Explore a failure-conditioned distribution | [Conditional weight comparison](examples/workflows/conditional_weight.py), [multiple-chain checks](examples/workflows/convergence_check.py), or [diagnostics notebook](notebooks/03_conditional_sampling_and_diagnostics.ipynb) |
| Bring your own code, noise, or decoder | [CSS template](examples/templates/byo_css_bitflip.py), [noise template](examples/templates/byo_noise.py), [decoder template](examples/templates/byo_decoder.py), or [component notebook](notebooks/04_bring_your_own.ipynb) |
| Work with detector or physical circuit faults | [Stim DEM template](examples/templates/byo_stim_dem.py), [DEM example](examples/stim_dem.py), or [physical circuit baseline](examples/circuit_baseline.py) |

For a guided first run, open [the quickstart notebook](notebooks/01_quickstart.ipynb), or consult the [example index](examples/README.md) for each script and notebook, its required extras, and how to read its output. The [API reference](docs/api_en.md) and [tutorial on custom components](docs/tutorial_en.md) explain the component contracts.

| Noise and state | OBF / Z / H | Stabilizer flip | Decoder connection |
| --- | --- | --- | --- |
| Static CSS bit-flip | Supported | Optional | PyMatching or deterministic user decoder; BP-OSD through `DecoderAdapter` |
| Static CSS phase-flip | Supported | Optional | PyMatching or BP-OSD with `errors="Z"`, using `hx`/`lx` |
| Static CSS depolarising | Supported with joint I/X/Y/Z labels | Optional | Full logical prediction; sector composition is a decoder choice |
| Phenomenological data and measurement faults | Supported | Unavailable | Decoder must consume the selected syndrome history or difference representation |
| Stim detector error model | Supported on latent mechanism bits | Unavailable | Matching from a graphlike DEM, or a user decoder |
| Physical Stim circuit locations | OBF, Z, physical single-fault moves, and H with explicit location groups | Unavailable | Midpoint surface logical-idle baseline with PyMatching |

`exact` enumerates small categorical state spaces, and `direct_mc` uses a fixed trial count. `sample_faulty` draws from normalized noise conditioned on failure, while `estimate_logical_error` estimates the logical error probability using BAR ratios between adjacent rungs and an anchor.

Code factories include toric and surface codes, asymmetric toric, Hamming HGP, BB72, BB108, BB144, Steane, and concatenated Steane. The current toric, surface, asymmetric toric, Hamming HGP, and BB factories need `".[codes]"`. Decoder constructors cover MWPM and BP-OSD for bit-flip and phase-flip (`errors="Z"`), plus explicit sector decoding for depolarising noise. `SamplingConfig(cache_cap=..., cache_policy=...)` limits the size of the deterministic decode cache, and `KernelConfig(zanella_fastpath=True)` uses the verified path for product noise when available.

Diagnostics include summaries across multiple chains, exact CSS coset initialization helpers, and `evaluate_convergence`, which screens results against four checks. A complete verdict requires an independent estimate of the conditional variance from direct MC, and these checks cannot prove mixing or correctness.

The physical circuit baseline samples mutually exclusive fault labels at supported Stim noise locations. Choose physical single-fault moves with `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)`, or Z+OBF with `KernelConfig(zanella=0.7, single=0.3, cluster=0, stabilizer=0)`. H additionally requires explicit `circuit_groups`, which are disjoint groups of location indices with matching channels and ordered fault alphabets. H preserves each group's occupancy and is generally reducible on its own. Circuit stabilizer moves remain unavailable, and the default Z+H setting requires groups before use.

Built-in circuit models with the standard failure predicate use cached effect differences, while custom predicates retain general evaluation. The surface logical-idle example evaluates a midpoint observable after the first d of 2d noisy rounds and uses its DEM to construct the decoder. Sampling operates on physical locations, as described in the [physical baseline](examples/circuit_baseline.py), [kernel comparison](examples/circuit_zanella.py), and [group contract](docs/tutorial_en.md#physical-circuit-faults).

Diagnostics such as ESS and split R-hat do not prove convergence, ergodicity, or correctness, as a chain can remain trapped even when its weight trace looks healthy. The `p_dependent_decoder_approx` BAR mode explicitly ignores changes in failure sets, and its interval omits the resulting bias. Estimates are also limited by model support, initialization, observed overlap, finite samples, and block length. DEM sampling does not establish equivalence to every physical circuit noise model, and the circuit baseline does not establish reproduction of published figures.

BAR uses block bootstrap by default, with `uncertainty="cross_chain"` available to estimate variation between independent chains. This option requires at least two chains and leaves pooled point estimates unchanged. Neither method includes a bias shared by short or poorly mixed chains. The paper's experiments on observable means do not establish BAR interval coverage, and passing diagnostics does not guarantee 95% coverage. See the [BAR sensitivity study](docs/bar_sensitivity_ja.md) and [API assumptions](docs/api_en.md) before interpreting the short examples as precision estimates.

The associated paper is in preparation, and the software citation names junichi haruna as instructed by the project owner. Affiliation, DOI, release date, and public release details remain pending, as described in [CITATION.cff](CITATION.cff) and [CONTRIBUTING.md](CONTRIBUTING.md). The code is released under the [MIT License](LICENSE), and this repository has not been published as a public package.
