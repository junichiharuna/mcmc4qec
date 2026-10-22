# mcmc4qec

mcmc4qec is a Python library for estimating logical error probabilities in quantum error correction.
It combines failure-conditioned MCMC with Bennett acceptance ratio (BAR) splitting to estimate rare failures that are costly to observe with direct Monte Carlo.
It also provides exact enumeration for small problems and direct Monte Carlo, with support for custom codes, noise models, and decoders.

The package is **pre-alpha** and under active validation.
It is published on GitHub as an experimental release (0.1.0.dev5, 2026-10-22) and is not on PyPI.

[日本語版](README_ja.md) · [Documentation](docs/index.md) · [Tutorial](docs/tutorial_en.md) · [API reference](docs/api_en.md) · [All examples](examples/README.md)

## Install and run

From a local checkout, install the package with code factories and PyMatching:

```sh
python -m pip install -e ".[codes,matching]"
```

Estimate logical error probabilities for a distance-3 toric code under independent bit flips with an MWPM decoder.
The `ladder` follows noise rates `0.2 → 0.15 → 0.1`, printing an estimate and uncertainty interval at each rate.

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

The reference probability at the first noise rate is computed automatically, and statistical uncertainty is returned by default.
You can supply `config`, `anchor`, and `seed` as needed.
Continue with the [tutorial for this example](docs/tutorial_en.md) to inspect the code, understand the ladder, adjust settings, and interpret results.

## Supported models and dependencies

| Area | Support |
| --- | --- |
| Codes | Toric, surface, asymmetric toric, Hamming HGP, BB72/108/144, Steane, concatenated Steane, open-boundary tile |
| Noise | Bit-flip, phase-flip, depolarising, phenomenological data and measurement faults, Stim DEM, physical circuit faults |
| Decoders | PyMatching, BP-OSD, BP-LSD (order 0), BeliefFind, Union-Find, custom decoders |
| Methods | Exact enumeration (`exact`), direct MC (`direct_mc`), BAR (`estimate_logical_error`), failure-conditioned MCMC (`sample_faulty`) |

Optional dependency groups include `codes` for code factories, `matching` and `bposd` for decoders, and `stim` for Stim support.
The `bposd` extra also installs `ldpc` for BP-LSD, BeliefFind, and Union-Find; see the [decoder examples and restrictions](docs/wp/basic_decoders_usage_2026-10-18_ja.md) (Japanese).
Use `plot` for plotting and `notebooks` for notebook execution.
For an example with only core dependencies, install with `python -m pip install -e .` and run `python examples/steane_exact.py --quick`.

## Where to go next

| Goal | Guide |
| --- | --- |
| Understand the first example and adjust settings and diagnostics | [Tutorial](docs/tutorial_en.md) |
| Supply your own code, noise, or decoder | [Replacing components](docs/tutorial_en.md#your-css-matrices) |
| Try other codes, noise models, or notebooks | [Example and dependency index](examples/README.md) |
| Look up arguments, result fields, or formulas | [API reference](docs/api_en.md) |

## Usage notes

The example's default settings do not guarantee research accuracy.
Standard BAR requires a positive anchor, a common decoder and failure definition across noise rates, and observed sample overlap between adjacent distributions.
Samples from `sample_faulty` alone do not estimate the absolute logical error probability.

Statistical error estimates and healthy MCMC diagnostics do not guarantee convergence or nominal interval coverage.
Tile72/288 code-capacity studies have completed four main bit-flip/depolarizing conditions; low-noise calibration and independent timing remain in progress.
Some tested settings have poor mixing diagnostics or undercoverage, so this experimental implementation does not establish a generally reliable 95% interval or a speed advantage over direct MC.
Keep the decoder settings, target prior, and native environment fixed throughout a BAR ladder and its reference calculation: saved BP-OSD inputs have produced different logical failure decisions on Windows and Linux.
See the [tile validation report](docs/wp/tile_validation_report_2026-10-18_ja.md), [current study status](docs/wp/tile_validation_status_2026-10-17_ja.md), and [additional decoder validation](docs/wp/basic_decoders_validation_2026-10-18_ja.md) (Japanese).
The additional decoder tests cover their interfaces and selected small problems; their logical error rates, BAR coverage, and comparative speed have not been calibrated.
For validation conditions and limitations, see the [BAR sensitivity study](docs/bar_sensitivity_ja.md), [performance record](docs/performance_ja.md), and [circuit validation record](docs/circuit_baseline_ja.md).

## License and citation

The code uses the [MIT License](LICENSE); citation metadata is in [CITATION.cff](CITATION.cff).
The associated paper is in preparation, and affiliation and DOI remain pending.
See [CONTRIBUTING.md](CONTRIBUTING.md) for development and contribution guidance.
