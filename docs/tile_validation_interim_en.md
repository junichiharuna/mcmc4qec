# Tile code validation: interim guidance

This guidance describes the evidence available on 23 October 2026, after collection and arithmetic review of 11 of the 12 low-noise conditions.
The remaining condition is tile288 with depolarizing noise at `p=0.001`.
The comparison across all 12 conditions, independent timing study, and final recommendations are unfinished.
This is a working-tree update; it has not been added to the previously prepared release archives.

## What you can use

The package implements the open-boundary tile CSS factory, code-capacity noise models, logical-failure evaluation, direct Monte Carlo, and fixed-decoder BAR workflows.
See the [API](api_en.md), [tile example](../examples/tile_bposd.py), and [fixed-prior workflow](../examples/workflows/tile_capacity_fixed_prior.py).
Short examples demonstrate the interface and do not establish research precision.

For reproducing the low-noise study, tile72 bit-flip at `p=0.01` is the first candidate supported by the completed results.
Its 16 prespecified long configurations used 16 chains, burn-in 6,000, 60,000 saved samples, and the fine ladder.
Each retained 192 replicates, with no diagnostic flags or undefined diagnostics, and passed the study's empirical relative-RMSE gates of 10% and 20%.
These observations neither prove mixing over the entire failure-conditioned support nor certify nominal 95% coverage.
They do not validate the public one-chain defaults, shorter examples, or a speed advantage over direct MC.

## Where the evidence is insufficient

In the other ten completed low-noise conditions, every replicate in each of the 16 prespecified long configurations had a diagnostic flag.
Tile288 depolarizing at `p=0.003` also had flags and undefined diagnostics in all 192 replicates of every one of its 352 configurations, despite obtaining all point estimates and intervals.
All 352 configurations failed the study's empirical relative-RMSE gates of 10% and 20%.
They are retained for investigation and reproduction, not recommended as calibrated configurations.

The weight-stratified reference for that condition has no full point estimate.
Its partial estimate is about `2.071e-15`, while its saved 99.9% reference interval is approximately `[7.964e-20, 8.723e-7]`.
The interval incorporates stratum-wise Clopper–Pearson intervals, Bonferroni adjustment, and an omitted-mass bound.
Neither the partial estimate nor the interval midpoint is a substitute for the true logical error rate.
Agreement with such a broad reference interval does not establish accuracy or coverage.
The RMSE gates are finite-reference empirical assessments, not population-RMSE certificates.

## Conditions to preserve when reproducing results

- Fix the decoder prior and all settings across the entire BAR ladder and its reference calculation.
- Preserve the native decoder environment, thread settings, and recorded fixtures. A tested tile288 depolarizing state received different failure labels on Windows and Linux; matching package versions alone is insufficient.
- For depolarizing noise, preserve the joint Pauli noise model. Sector decoding does not make the physical sectors independent.
- Keep unconverged replicates, undefined diagnostics, and unavailable intervals in the reporting denominator.
- Changing the interval method does not repair biased point estimates or poor mixing.
- BP-LSD, BeliefFind, and Union-Find have implementation acceptance evidence, but their BAR accuracy, coverage, and speed rankings remain uncalibrated. The BP-OSD results do not transfer automatically to them.

## Evidence and reproduction

The [Japanese usage guide](wp/low_noise_interim_usage_2026-10-23_ja.md) links the earlier nine-condition comparison and the individual tile288 reports.
The [p=0.003 report](wp/low_c3t1_result_2026-10-23_ja.md) links saved CSVs, manifests, arithmetic review, and reproduction scripts.
Its arithmetic review checked 11,968 scalar values; this verifies aggregation, not MCMC convergence.
The [experimental release notes](experimental_release_notes_en.md) describe decoder restrictions and the data required for independent reanalysis.
The latest verified publication status is recorded separately in the [candidate status](wp/publication_candidate_status_2026-10-23_ja.md); older statements that publication already occurred are not evidence of current GitHub visibility.
The complete raw trace and weight-stratified datasets are not included in the prepared source snapshot, and their public download location remains unresolved.
