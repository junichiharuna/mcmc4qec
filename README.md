# mcmc4qec

mcmc4qec is a Python library for estimating logical error probabilities in quantum error correction, including rare failures that are costly to observe with direct Monte Carlo.
It provides exact enumeration, direct Monte Carlo, and anchored Bennett acceptance ratio (BAR) splitting for CSS codes, with support for custom codes, noise models, and decoders.

The package is **pre-alpha** and under active validation; it has not been published as a public package.
[日本語版](README_ja.md) · [API reference](docs/api_en.md) · [Tutorial](docs/tutorial_en.md) · [All examples](examples/README.md)

## Quick start

From a local checkout, install the core package:

```sh
python -m pip install -e .
```

The following example estimates the logical error probability at three bit-flip rates for a three-qubit repetition code.
BAR splitting transfers an absolute probability from a reference point (the **anchor**) along a sequence of noise rates (the **ladder**).
The anchor at `p=0.4` is computed automatically; no optional dependencies are needed.

```python
import numpy as np
from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip,
                      Problem, estimate_logical_error)

code = CSSCode(hx=np.zeros((0, 3), dtype=int),
               hz=[[1, 1, 0], [0, 1, 1]],
               lx=[[1, 1, 1]], lz=[[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="repetition3-minimum-weight-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
ladder = [0.4, 0.25, 0.1]
result = estimate_logical_error(problem, ladder)
for p, estimate, interval in zip(ladder, result.estimates, result.intervals):
    print(f"p={p}: P_L={estimate:.6g}, interval={interval}")
```

Each output row gives a noise rate, its estimated logical error probability `P_L`, and an uncertainty interval.
Omitting `seed` starts a fresh random run; pass an integer such as `seed=73` to reproduce a run with the same settings.
Omitting `config` uses 1,000 retained samples after 100 burn-in steps per rung; these defaults do not guarantee research accuracy.
Omitting `anchor` uses exact enumeration for at most 4,096 states, otherwise 10,000 direct-MC trials; customize with `anchor_max_states` and `anchor_trials`, or pass an explicit `anchor` ([details](docs/api_en.md#automatic-bar-anchor)).
`CallableDecoder` returns a prediction of the logical observable; see the [CSS tutorial](docs/tutorial_en.md#your-css-matrices) for the matrix and decoder conventions.
For a guided comparison of exact enumeration, direct MC, and BAR, run `python examples/steane_exact.py --quick` or open the [quickstart notebook](notebooks/01_quickstart.ipynb).

## Choose an example

Choose the workflow for the quantity you want to compute.
In particular, `sample_faulty` samples **conditioned on failure**: its state frequencies alone do not estimate the absolute failure probability `P_L`.

| Goal | API | Example |
| --- | --- | --- |
| Enumerate a small problem or run direct MC | `exact`, `direct_mc` | [Steane comparison](examples/steane_exact.py) |
| Estimate `P_L` across noise rates with BAR | `estimate_logical_error` | [Toric BAR curve](examples/workflows/pl_curve.py), [BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| Study errors conditioned on failure | `sample_faulty` | [Conditional weight](examples/workflows/conditional_weight.py), [multiple-chain checks](examples/workflows/convergence_check.py) |
| Supply your own code, noise, or decoder | `Problem` and component interfaces | [CSS template](examples/templates/byo_css_bitflip.py), [noise template](examples/templates/byo_noise.py), [decoder template](examples/templates/byo_decoder.py) |
| Sample detector or physical circuit faults | DEM and circuit models | [Stim DEM](examples/stim_dem.py), [physical circuit baseline](examples/circuit_baseline.py) |

The [example index](examples/README.md) lists all scripts and notebooks, their dependencies, and how to interpret their output.

## Supported models and dependencies

Built-in code factories cover toric, surface, asymmetric toric, Hamming HGP, BB72/108/144, Steane, and concatenated Steane codes.
Noise models include bit-flip, phase-flip, joint I/X/Y/Z depolarising noise, phenomenological data and measurement faults, Stim detector error models (DEM), and physical Stim circuit faults.
Decoder constructors connect to PyMatching and BP-OSD; custom components follow the [API contracts](docs/api_en.md), including normalized noise and deterministic decoding.

Optional dependencies are installed as extras.
For example, `python -m pip install -e ".[codes,matching]"` enables the [toric MWPM example](examples/toric_pymatching.py).

| Extra | Use |
| --- | --- |
| `codes` | Toric, surface, asymmetric toric, Hamming HGP, and BB factories |
| `matching` | PyMatching decoders |
| `bposd` | BP-OSD decoders |
| `stim` | Stim DEM and circuit examples |
| `plot` | PNG plots in workflow scripts; CSV output is also available |
| `notebooks` | Notebook execution and plotting |

MCMC supports one-bit flip (OBF), Zanella (Z), cluster exchange (H), and, for static CSS models, stabilizer moves.
Defaults are Z/H weights 0.7/0.3, `cluster_k=2`, one chain, and lazy probability 0.05; rejected and lazy steps remain in the trace.
Physical circuit models require their own kernel configuration, including explicit location groups for H; see the [circuit tutorial](docs/tutorial_en.md#physical-circuit-faults) for supported combinations and restrictions.

## Estimates, errors, and diagnostics

Statistical uncertainty is returned with numerical estimates by default.

| Method | Estimate | Uncertainty |
| --- | --- | --- |
| Direct MC | `estimate` | 95% Wilson `interval` |
| BAR | `estimates` | `intervals` and `log_standard_errors` at each noise rate |
| Conditional MCMC | `conditional_weight` | `conditional_weight_standard_error`: IAT-based Monte Carlo standard error of the mean weight |

Conditional MCMC also returns integrated autocorrelation time (IAT), effective sample size (ESS), classical split Gelman–Rubin R-hat, cross-chain standard errors, and acceptance statistics in `result.diagnostics`.
Unavailable errors are `None`, not zero; short or constant traces can be uninformative.

### Optional detailed diagnostics

Pass `diagnostics=True` to `sample_faulty` or `estimate_logical_error` to add autocorrelation arrays, blocking estimates across block lengths, and bootstrap intervals for conditional observable means.
Use `DiagnosticsConfig` to set lags, block sizes, and bootstrap repetitions.
These reports are numerical results saved by `to_json()`; plotting packages are not required.
Analysis uses a separate random number generator and leaves sampling trajectories and BAR estimates and intervals unchanged.

For a complete example and the result fields, see the [diagnostics tutorial](docs/tutorial_en.md#initialization-cache-and-diagnostics), [diagnostics notebook](notebooks/03_conditional_sampling_and_diagnostics.ipynb), and [API formulas and settings](docs/api_en.md#default-statistical-errors-and-optional-detailed-diagnostics).
The API also covers analysis of saved results and custom observables with `diagnostic_report` and `analyze_traces`.

## Validation and limitations

BAR requires an anchor with positive failure probability, the same decoder and failure definition across the standard ladder, and observed support overlap between adjacent distributions.
Missing observed overlap raises `OverlapError`.
The `p_dependent_decoder_approx` mode ignores changes in failure sets, and its uncertainty intervals omit that bias.

BAR uses block bootstrap by default; `uncertainty="cross_chain"` uses variation across at least two independent chains while keeping pooled point estimates unchanged.
Neither method accounts for bias shared by poorly mixed chains.
Good ESS or R-hat values do not prove convergence, ergodicity, correctness, or nominal interval coverage.
The [BAR sensitivity study](docs/bar_sensitivity_ja.md) records coverage limitations of the short experiments.
DEM sampling and the physical circuit baseline also have distinct noise models; neither establishes reproduction of published circuit results.

For runtime measurements, see the [performance record](docs/performance_ja.md) and [benchmark script](benchmarks/bench_step.py).
The recorded toric d=5 and d=7 runs on 2026-10-15 met the target of at most twice the research runner's time under the measured settings.
Those same-seed timing repetitions do not establish performance on other workloads or sampling accuracy.

## License and citation

The code uses the [MIT License](LICENSE).
Citation metadata is in [CITATION.cff](CITATION.cff); the associated paper is in preparation, and affiliation, DOI, and release details remain pending.
See [CONTRIBUTING.md](CONTRIBUTING.md) for development and contribution guidance.
