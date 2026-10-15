# mcmc4qec

mcmc4qec is a Python library for estimating logical error probabilities in quantum error correction.
When logical failures are rare, observing enough of them with direct Monte Carlo can be expensive.
mcmc4qec starts from a reference probability at a noise rate where failures are easier to observe, then estimates logical error probabilities at progressively lower noise rates.
It combines failure-conditioned MCMC with Bennett acceptance ratio (BAR) splitting.

The library also provides exact enumeration for small problems and direct Monte Carlo, with built-in CSS codes and support for custom codes, noise models, and decoders.
The package is **pre-alpha** and under active validation; it has not been published as a public package.

[日本語版](README_ja.md) · [API reference](docs/api_en.md) · [Tutorial](docs/tutorial_en.md) · [All examples](examples/README.md)

## Install and run

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

## How the example works

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
To define your own matrices or decoder, follow the [CSS tutorial](docs/tutorial_en.md#your-css-matrices).

### Noise ladder and reference probability

`ladder` lists the noise rates used for estimation.
The example first computes the logical error probability at `p=0.2` as a reference value (**anchor**).
BAR then estimates probability ratios between adjacent noise rates to obtain the estimates at `p=0.15` and `p=0.1`.

The anchor is computed by exact enumeration for small state spaces and by direct Monte Carlo otherwise.
Pass `anchor` to supply a reference result computed separately.
Use `config` to adjust sample counts and other sampling settings, and pass an integer such as `seed=73` for reproducibility with the same settings.
All three arguments are optional.
See the [API settings example](docs/api_en.md#automatic-bar-anchor) for defaults and configuration.

## Results and statistical uncertainty

Statistical uncertainty is returned with numerical estimates by default.
In the BAR example, `result.estimates` and `result.intervals` follow the order of `ladder`.

| Method | Estimate | Uncertainty |
| --- | --- | --- |
| Direct MC | `estimate` | 95% Wilson `interval` |
| BAR | `estimates` | `intervals` and `log_standard_errors` at each noise rate |
| Failure-conditioned MCMC | `conditional_weight` | `conditional_weight_standard_error`: autocorrelation-aware standard error of the mean weight |

BAR uses block bootstrap by default.
With at least two independent chains, `uncertainty="cross_chain"` instead estimates uncertainty from variation between chains.
Unavailable errors are `None`, not zero.

### MCMC diagnostics

Failure-conditioned MCMC also returns integrated autocorrelation time (IAT), effective sample size (ESS), classical split Gelman–Rubin R-hat, cross-chain standard errors, and acceptance statistics in `result.diagnostics`.
Short or constant traces can be uninformative.

Pass `diagnostics=True` to `sample_faulty` or `estimate_logical_error` to add autocorrelation arrays, blocking estimates across block lengths, and bootstrap intervals for conditional observable means.
These diagnostics describe observable means and are distinct from the BAR uncertainty intervals for logical error probabilities.
Reports are numerical results that can be saved with `to_json()`.
Enabling detailed diagnostics leaves sampling trajectories and BAR estimates and intervals unchanged.

See the [diagnostics tutorial](docs/tutorial_en.md#initialization-cache-and-diagnostics) to retrieve results, and the [API reference](docs/api_en.md#default-statistical-errors-and-optional-detailed-diagnostics) for `DiagnosticsConfig` settings and analysis of saved data.

## Supported models and dependencies

Built-in code factories cover toric, surface, asymmetric toric, Hamming HGP, BB72/108/144, Steane, and concatenated Steane codes.
Noise models include bit-flip, phase-flip, depolarising noise, phenomenological data and measurement faults, Stim detector error models (DEM), and physical circuit faults.
Decoder constructors connect to PyMatching and BP-OSD.

### Choose an example

| Goal | API | Example |
| --- | --- | --- |
| Enumerate a small problem or run direct MC | `exact`, `direct_mc` | [Steane comparison](examples/steane_exact.py) |
| Estimate logical error probabilities across noise rates | `estimate_logical_error` | [Toric BAR curve](examples/workflows/pl_curve.py), [BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| Study errors conditioned on failure | `sample_faulty` | [Conditional weight](examples/workflows/conditional_weight.py), [multiple-chain checks](examples/workflows/convergence_check.py) |
| Supply your own code, noise, or decoder | `Problem` and component interfaces | [CSS](examples/templates/byo_css_bitflip.py), [noise](examples/templates/byo_noise.py), and [decoder](examples/templates/byo_decoder.py) templates |
| Sample detector or physical circuit faults | DEM and circuit models | [Stim DEM](examples/stim_dem.py), [physical circuit baseline](examples/circuit_baseline.py) |

`sample_faulty` samples conditioned on failure.
Its state frequencies alone do not estimate the logical error probability `P_L`.
The [example index](examples/README.md) lists all scripts and notebooks and explains their output.

### Optional dependencies

Install optional dependency groups (extras) for the features you need.
The installation command above selects `codes` and `matching`.

| Extra | Use |
| --- | --- |
| `codes` | Toric, surface, asymmetric toric, Hamming HGP, and BB factories |
| `matching` | PyMatching decoders |
| `bposd` | BP-OSD decoders |
| `stim` | Stim DEM and circuit examples |
| `plot` | PNG plots in workflow scripts; CSV output is also available |
| `notebooks` | Notebook execution and plotting |

For an example with only core dependencies, install with `python -m pip install -e .` and run `python examples/steane_exact.py --quick`.
The [API reference](docs/api_en.md) covers custom component contracts and MCMC update methods; the [circuit tutorial](docs/tutorial_en.md#physical-circuit-faults) explains settings specific to circuit models.

## Applicability and validation

Standard BAR estimation requires a reference with positive failure probability and the same decoder and failure definition at every noise rate.
Adequate sample overlap between adjacent distributions is also important.
Missing required observed overlap raises `OverlapError`.
See the [API reference](docs/api_en.md) for the approximate mode that allows a decoder to vary with noise rate.

Statistical uncertainty estimates cannot fully capture bias from poorly mixed MCMC chains.
Good ESS or R-hat values do not prove convergence, ergodicity, correctness, or nominal interval coverage.
The [BAR sensitivity study](docs/bar_sensitivity_ja.md) records interval limitations found in short experiments, and the [performance record](docs/performance_ja.md) documents runtimes and measurement conditions.
DEM and physical circuit sampling use distinct noise models.
See the [circuit validation record](docs/circuit_baseline_ja.md) for the physical circuit model's supported scope and validation results.

## License and citation

The code uses the [MIT License](LICENSE); citation metadata is in [CITATION.cff](CITATION.cff).
The associated paper is in preparation, and affiliation, DOI, and release details remain pending.
See [CONTRIBUTING.md](CONTRIBUTING.md) for development and contribution guidance.
