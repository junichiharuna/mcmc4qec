# Runnable examples and notebooks

Run scripts from the repository root with `python examples/<name>.py --quick --seed 7 --out <directory>` (adjust the relative path for `workflows/` or `templates/`). Every example script accepts `--quick`, `--seed`, and `--out`. Its default output directory is the system temporary directory under `mcmc4qec/<script-stem>`; it does not write to the research repository. Each script ends with a `SUMMARY` JSON line. The tables below describe the meaning of that line. `--quick` uses the same computation path with smaller settings.

Times below are measured seconds on Windows with Python 3.11; they vary with machine load. Per-file measurements are recorded in the [WP memos](../docs/wp/); the full default regeneration was timed separately after integration. `plot` supplies workflow PNG support. If the pyplot drawing layer cannot import, the scripts keep the same numeric CSV output. PyMatching 2.4 itself requires matplotlib, so a matching workflow cannot be promised to run without the entire matplotlib package. `codes` is required for the current toric factory as well as HGP and BB factories. See [installation](../README.md#install-and-first-run).

## Estimation and real codes

| File | Purpose | Extras | Default time | Quick time | Read the output | Scientific notes |
| --- | --- | --- | --- | --- | --- | --- |
| [bit_flip.py](bit_flip.py) | Small bit-flip exact/MC/conditional comparison | none | 2.549 s | 0.292 s | `exact` and `pl` are absolute `P_L`; `ew_exact` and `ew_chain` are conditional weights | 1, 5 |
| [three_noise.py](three_noise.py) | Small depolarising and phenomenological cases | none | 4.340 s | 1.158 s | `cases` compares exact/MC/BAR within each full experiment | 1, 5 |
| [bar_ladder.py](bar_ladder.py) | Exact-anchored BAR on a three-bit code | none | 0.503 s | 0.348 s | `bar` and `intervals` estimate absolute `P_L` at `ladder`; `exact` checks it | 1, 3, 4, 5 |
| [toric_pymatching.py](toric_pymatching.py) | Toric bit-flip direct MC and conditional chain | `codes, matching` | 1.008 s | 0.680 s | `pl`/`pl_interval` come from direct MC; `ew_direct`/`ew_chain` are conditional means | 1, 5 |
| [phase_flip_asymmetric.py](phase_flip_asymmetric.py) | Rectangular toric 3x5 X/Z direct-MC comparison | `codes, matching` | 5.01 s | 1.76 s | Compare `pl_bit_flip`/`pl_phase_flip` with their Wilson intervals; `exact_available=false` | 1, 5; finite samples do not establish an X/Z gap |
| [stim_dem.py](stim_dem.py) | Hand-written latent Stim DEM mechanisms | `stim` | 0.476 s | 0.225 s | `exact` and `pl` compare absolute DEM-model failure; `mechanisms` counts latent bits | 1, 6; DEM is not physical-circuit equivalence |
| [circuit_baseline.py](circuit_baseline.py) | Midpoint surface logical-idle physical fault baseline | `stim, matching` | 3.908 s | 1.441 s | `locations`/`detectors` describe the experiment; `pl`/`pl_interval` are direct-MC results | 1, 2, 6, 7; selects the physical single-fault kernel |
| [circuit_zanella.py](circuit_zanella.py) | Surface d=3 physical single-fault versus Z+OBF conditional sampling | `stim, matching` (`plot` for PNG) | 13.79 s | 3.89 s | PNG/CSV compare conditional weight, acceptance, and IAT; these are not absolute `P_L` | 1, 2, 5, 6; short chains can disagree with independent MC |
| [bb72_bposd.py](bb72_bposd.py) | BB72 bit-flip with fixed-prior BP-OSD | `codes` | 1.951 s | 0.712 s | `pl`/`pl_interval` are direct MC; `ew_direct`/`ew_chain` compare conditional weights | 1, 2, 5 |
| [toric_depolarizing.py](toric_depolarizing.py) | Toric depolarising joint I/X/Y/Z faults | `codes, matching` | 1.521 s | 0.708 s | `pl`/`pl_interval` are direct MC; conditional weights include Pauli composition | 1, 5 |
| [phenomenological_toric.py](phenomenological_toric.py) | Toric data/measurement faults over `rounds` | `codes, matching` | 0.952 s | 0.644 s | `pl`/`pl_interval` concern the full bounded experiment, not a per-round rate | 1, 5 |
| [steane_exact.py](steane_exact.py) | Steane exact, direct MC, and exact-anchored BAR | none | 2.354 s | 0.516 s | `exact` and `bar` compare per-`ladder` absolute probabilities; `bar_intervals` are sampling intervals | 1, 3, 4, 5 |

## Research workflows

| File | Purpose | Extras | Default time | Quick time | Read the output | Scientific notes |
| --- | --- | --- | --- | --- | --- | --- |
| [workflows/pl_curve.py](workflows/pl_curve.py) | Toric d=3/5 BAR `P_L(p)` curve, direct-MC checks, CSV/PNG | `codes, matching` (`plot` for PNG) | 19.370 s | 3.610 s | `estimates`/`intervals` are anchored BAR values at `ladder`; `checks` are direct MC | 1, 3, 4, 5; MC anchor needs observed failures, `--demo-overlap` illustrates disjoint endpoint support |
| [workflows/conditional_weight.py](workflows/conditional_weight.py) | Direct-MC versus Z+H conditional weight | `codes, matching` (`plot` for PNG) | 16.790 s | 3.926 s | `ew_direct`/`ew_chain` are `E[w\|faulty]` at `ps`, not `P_L` | 1, 5 |
| [workflows/convergence_check.py](workflows/convergence_check.py) | Multiple initial populations and four convergence checks | `codes, matching` | 1.450 s | 1.010 s | `checks`, `verdict`, and `warnings` screen results; a complete screen needs independent direct-MC conditional variance | 1, 5; a good verdict proves neither convergence, ergodicity, nor correctness |
| [workflows/p_dependent_decoder.py](workflows/p_dependent_decoder.py) | Fixed BP-OSD ladder versus explicit approximate mode | `codes` | 1.720 s | 0.780 s | `fixed` uses one decoder; `approx` changes it with p and omits that bias from intervals | 1, 2, 3, 4, 5 |

For a standard BAR ladder, keep one decoder and failure predicate across every rung. A BP-OSD decoder built at `p`, a depolarising BP-OSD decoder, and the circuit baseline's `decoder_p` depend on their construction probability. Changing that probability across rungs requires the explicit `p_dependent_decoder_approx` mode, whose interval excludes the resulting failure-set bias. BAR also requires an exact anchor or an MC anchor with at least one observed failure. If adjacent sampled ensembles have no observed support overlap, refine the ladder rather than interpreting an `OverlapError` as a probability.

## Bring your own components

The templates contain `# >>> EDIT HERE` and `# <<< END EDIT` regions, followed by checks before sampling.

| File | Purpose | Extras | Default time | Quick time | Read the output | Scientific notes |
| --- | --- | --- | --- | --- | --- | --- |
| [templates/byo_css_bitflip.py](templates/byo_css_bitflip.py) | Supply CSS matrices and deterministic logical decoder | none | 0.599 s | 0.269 s | `checks_passed` reports input validation; `pl` is an absolute estimate | 1, 3, 5; check stabilizer invariance before enabling stabilizer flips for custom failure predicates |
| [templates/byo_noise.py](templates/byo_noise.py) | Supply normalized `log_prob` and matching sampler | none | 0.313 s | 0.190 s | `normalization` records small-state enumeration; `pl` is absolute | 1; retain the true joint distribution for correlated noise |
| [templates/byo_decoder.py](templates/byo_decoder.py) | Wrap a correction or logical-output decoder explicitly | none | 0.310 s | 0.184 s | `output_kind` declares meaning; `checks_passed` precedes `pl` | 1; decoder output meaning cannot be inferred from shape |
| [templates/byo_stim_dem.py](templates/byo_stim_dem.py) | Convert a Stim circuit to a DEM and matching decoder | `stim, matching` | 0.780 s | 0.596 s | `detectors`/`mechanisms` describe latent DEM; `pl` is its direct-MC failure estimate | 1, 6; DEM behavior does not establish physical-circuit equivalence |

## Notebooks

Set `MCMC4QEC_QUICK=1` for smaller notebook runs. Notebook cells are self-contained and do not import `examples/`. These notebooks need the `notebooks` extra; the first three also use `codes` and `matching`.

| File | Purpose | Extras | Default time | Quick time | Read the output | Scientific notes |
| --- | --- | --- | --- | --- | --- | --- |
| [01_quickstart.ipynb](../notebooks/01_quickstart.ipynb) | Toric d=5 direct MC and Z+H | `notebooks, codes, matching` | 5.890 s | 4.930 s | Compare absolute direct-MC `P_L` with conditional chain observables | 1, 5 |
| [02_pl_curve_with_bar.ipynb](../notebooks/02_pl_curve_with_bar.ipynb) | BAR anchor, overlap, and `P_L(p)` curve | `notebooks, codes, matching` | 37.680 s | 6.530 s | Curve is anchor plus BAR ratios; inspect overlap and uncertainty | 1, 3, 4, 5 |
| [03_conditional_sampling_and_diagnostics.ipynb](../notebooks/03_conditional_sampling_and_diagnostics.ipynb) | Conditional chain, trace, and multiple-chain diagnostics | `notebooks, codes, matching` | 7.560 s | 4.120 s | Trace and diagnostics describe a failure-conditioned run | 1, 5; diagnostics are not proofs |
| [04_bring_your_own.ipynb](../notebooks/04_bring_your_own.ipynb) | Core-only custom code, noise, and decoder | `notebooks` | 4.890 s | 2.580 s | Check component contracts before interpreting probability outputs | 1, 5 |
| [regenerate.py](../notebooks/regenerate.py) | Regenerate committed notebook outputs | `notebooks, codes, matching` | 34.989 s | 20.180 s | Re-executes the four notebooks; no `SUMMARY` contract | 1–5 as applicable to the notebooks |

ESS, split R-hat, and the four `evaluate_convergence` checks do not prove mixing, ergodicity, or correctness. The associated paper is in preparation; these examples do not claim to reproduce its figures.

These are short demonstrations. Some recorded BAR intervals fail to overlap independent direct-MC intervals even in default mode; the scripts and notebooks print warnings. Neither interval agreement nor diagnostic checks prove sufficient mixing or research precision. The Steane example prints exact coverage at every rung rather than selecting a seed to force coverage.
