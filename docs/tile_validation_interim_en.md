# Tile code validation: interim guidance

## Update on 29 October 2026

The independent timing study has completed: all 48 method rows (12 selected conditions × MC/BAR × capacity and main runs) terminated with exit 0, and the final report (`report.json`, SHA-256 `79d1357d…`; `report_ja.md`, SHA-256 `3614ab8f…`) was accepted on 29 October 2026 at 02:21 JST.
The selected conditions are tile72 bit-flip and tile72 depolarizing at `p ∈ {0.01, 0.003, 0.001}` with target relative RMSE `ε ∈ {0.2, 0.1}`; each has 192 of 192 replicates completed for both MC and BAR.
The twelve tile288 rows were not selected because their weight-stratified reference intervals are too wide (`ineligible_reference_width`); this is a selection outcome, not a missing calibration.

The frozen report prints an MC/BAR cost ratio only where both methods passed the empirical precision gate (relative RMSE ≤ ε): tile72 bit-flip at `p=0.003` (ε=0.2: 2.0, ε=0.1: 3.0) and at `p=0.001`, ε=0.1 (29.7), all in favour of BAR.
Seven of the eleven gate exceedances in the other nine conditions lie within one standard error of the RMSE estimate (about 5%); only tile72 bit-flip BAR at `p=0.001`, ε=0.2 (+20%) and tile72 depolarizing BAR at `p=0.01`, ε=0.2 (+10%) clearly miss the gate.
A precision-normalized cost, mean task cost × (achieved relative RMSE / ε)², shows a crossover: at `p=0.01` direct MC is cheaper than BAR (MC/BAR 0.17–0.57), at `p=0.003` BAR is cheaper by 2–5×, and at `p=0.001` by 10–35×.
Any statement that BAR is faster therefore applies to tile72 at `p ≤ 0.003` only.

BAR intervals covered the reference interval in 151–176 of 192 replicates (MC: 178–186), so nominal 95% coverage is still not claimed, and the timing study collected no mixing diagnostics for BAR.
At tile72 depolarizing, `p=0.001`, ε=0.2, BAR shows a relative bias of −0.14 that accounts for about half of its mean squared error.
Costs are per-task means over 192 replicates and exclude capacity measurement, seed audit, selection, and reporting; the relative RMSE is measured against finite weight-stratified reference intervals, not against a known true value.

The per-condition tables, the normalization, and its caveats are in the Japanese notes [`wp/low_noise_cost_comparison_2026-10-29_ja.md`](wp/low_noise_cost_comparison_2026-10-29_ja.md) and the final-report draft [`wp/final_validation_report_draft_2026-10-24_ja.md`](wp/final_validation_report_draft_2026-10-24_ja.md); local copies of the report and the extracted summaries are under `wp/data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/` (not tracked by git).
The sections below are the 23 October 2026 guidance, kept as history; where they say the timing study is unfinished, this update supersedes them.

## Guidance as of 23 October 2026

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
