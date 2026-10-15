# Choose a workflow

[日本語](guide_ja.md) · [Tutorial](tutorial_en.md)

Start by deciding what quantity you need and what experiment your state represents.
A logical error probability for one round, a bounded measurement history, and a physical circuit are different quantities even when the code has the same distance.
The following routes connect that choice to runnable examples and the relevant API contracts.

## Estimate a probability or study failures

| Goal | Method | First example |
| --- | --- | --- |
| Check a small model against all possible states | `exact` | [Steane enumeration](../examples/steane_exact.py) |
| Estimate a probability where failures can be observed in a fixed trial budget | `direct_mc` | [Bit-flip comparison](../examples/bit_flip.py) |
| Study typical errors conditional on decoder failure | `sample_faulty` | [Conditional weight](../examples/workflows/conditional_weight.py) |
| Estimate rarer failure probabilities using a ladder of noise rates | `estimate_logical_error` | [BAR curve](../examples/workflows/pl_curve.py) |

Check a small instance by enumeration before scaling a custom model.
Use independent direct MC as a comparison where failures are frequent enough.
Conditional states alone do not determine the absolute probability of failure: BAR needs an anchor as well as probability ratios between adjacent rungs.
The [tutorial](tutorial_en.md#noise-ladder-and-reference-probability) explains how those pieces fit together.

## Choose the experiment and dependencies

Install extras from the repository root, for example `python -m pip install -e ".[codes,matching]"`.
The core installation contains NumPy and the small custom-model examples.

| Experiment | Model and noise | Runnable example | Extras |
| --- | --- | --- | --- |
| CSS X errors | `code.bit_flip_model()`, `IndependentBitFlip` | [Toric bit flips](../examples/toric_pymatching.py) | `codes,matching` |
| CSS Z errors | `code.phase_flip_model()`, `IndependentBitFlip` | [X/Z comparison](../examples/phase_flip_asymmetric.py) | `codes,matching` |
| Joint Pauli errors | `DepolarizingModel`, `DepolarizingNoise` | [Toric depolarising noise](../examples/toric_depolarizing.py) | `codes,matching` |
| Data and measurement faults | `PhenomenologicalModel`, `PhenomenologicalNoise` | [Repeated measurements](../examples/phenomenological_toric.py) | `codes,matching` |
| Latent detector error mechanisms | `from_stim_dem` or `from_stim_circuit` | [Stim DEM](../examples/stim_dem.py) | `stim` |
| Physical circuit locations | `CircuitFaultModel`, `CircuitFaultNoise` | [Circuit baseline](../examples/circuit_baseline.py) | `stim,matching` |
| BB code with fixed-prior decoding | Code factory, bit-flip model, BP-OSD | [BB72](../examples/bb72_bposd.py) | `codes` |

Joint Pauli noise preserves the correlation between X and Z components of a Y error, even when a decoder handles the two sectors separately.
A phenomenological result refers to the full configured experiment, not a per-round rate.
A Stim DEM state records latent mechanisms; a physical circuit state records exclusive fault categories at locations.
Choose the representation that matches your experiment before comparing rates.

## Check uncertainty and mixing

First inspect the result's warnings, anchor provenance, and sampling configuration.
Then compare chain behavior and sensitivity to run length, initial states, and block length.
Keep the failure definition and decoder fixed throughout a standard BAR ladder.

| Check | Where to look | What it tells you |
| --- | --- | --- |
| Absolute probability uncertainty | MC `interval`; BAR `intervals` and `log_standard_errors` | Sampling error for the probability estimator |
| Conditional mean uncertainty | `conditional_weight_standard_error` | MCSE of the mean nonidentity-coordinate count among failures |
| ACF, IAT, ESS, split R-hat | `diagnostics=True` or `DiagnosticsConfig` | Dependence and disagreement visible in the chosen observable |
| Block-length sensitivity | Detailed `trace_analysis` report | Whether observable-mean error estimates change with block size |
| Different starting populations | [Convergence workflow](../examples/workflows/convergence_check.py) | Disagreement between starts and unresolved checks |

The [diagnostics tutorial](tutorial_en.md#initialization-cache-and-diagnostics) explains the numerical outputs.
For formulas and the distinction between BAR and observable bootstrap calculations, see the [statistical conventions](api_en.md#default-statistical-errors-and-optional-detailed-diagnostics).
Good diagnostics do not establish convergence or nominal interval coverage; chains can share a bias that neither block bootstrap nor cross-chain variation reveals.

## Bring your own components

Replace one component at a time and validate it on a finite, enumerable instance.
The templates contain marked editing regions and checks before sampling.

| Component | Contract to check | Template |
| --- | --- | --- |
| CSS matrices | Binary dimensions, commutation, logical basis pairing | [CSS bit flips](../examples/templates/byo_css_bitflip.py) |
| Noise distribution | Normalized full-state `log_prob` and a sampler for the same distribution | [Custom noise](../examples/templates/byo_noise.py) |
| Decoder | Deterministic output with explicitly declared correction or observable meaning | [Custom decoder](../examples/templates/byo_decoder.py) |
| Stim circuit converted to a DEM | Mechanism support and observable mapping | [Stim DEM adapter](../examples/templates/byo_stim_dem.py) |

The [custom CSS tutorial](tutorial_en.md#your-css-matrices) develops small examples of these contracts.
For a decoder whose prior changes with the noise rate, read the [p-dependent workflow](../examples/workflows/p_dependent_decoder.py) before selecting the approximate BAR mode.
Its intervals do not include the bias caused by changing failure sets.

## Run a complete example

From the repository root, start with a short run:

```sh
python examples/steane_exact.py --quick --seed 7 --out output/steane
```

Example scripts accept `--quick`, `--seed`, and `--out` and finish with a `SUMMARY` JSON line.
The [example index](../examples/README.md) describes each output, optional dependencies, and recorded execution times.
Use `--quick` to learn the workflow; choose and validate the statistical budget for the problem you intend to study.
