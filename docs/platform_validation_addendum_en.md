# Additional BP-OSD platform validation

This supplement records measurements made after the experimental source snapshot was frozen.
It does not change the tested package or its defaults.

The same 1,048,576 physical error states were decoded on DGX Spark (Linux aarch64) and Labo PC (Windows x86-64).
The fixed design covered 16 conditions, each with 65,536 trials: tile72/288 with bit-flip/depolarizing noise, at the main validation probability and at p=0.01, 0.003, and 0.001.
All 256 chunks completed on each host, with no missing chunks or checkpoint failure-definition mismatches.
The full physical-state arrays were checked for equality before paired analysis.

| Condition | Different failure labels / 65,536 | Disagreement rate |
| --- | ---: | ---: |
| tile72, bit-flip, p=0.03 | 1,066 | 1.6266% |
| tile288, bit-flip, p=0.05 | 961 | 1.4664% |
| tile72, depolarizing, p=0.03 | 1,002 | 1.5289% |
| tile288, depolarizing, p=0.05 | 9 | 0.0137% |

Different failure labels do not imply a logical error-rate difference of the same size: either host can fail on states that the other host corrects.
The paired logical error-rate difference intervals included zero in all 16 conditions.
This does not establish equal error rates or equal failure sets.
The intervals use 96 Bonferroni-adjusted Clopper–Pearson intervals for a family confidence level of 95%, conditional on iid trials and a fixed decoder within each environment.
Limited repeated checks do not prove those determinism assumptions.
Several low-noise conditions had zero failures and do not provide precise error-rate references.

Python and dependency versions and package source hashes matched; OS, CPU architecture, and native binaries differed.
This comparison does not isolate the cause of the discrepancy.
Keep the decoder settings, target prior, and native environment fixed across a BAR ladder and its reference calculation.
Do not pool these personal-host results into the existing cluster cohorts without validating the corresponding failure definition.
The experiment used CPU workers and does not establish GPU performance, cluster speed comparisons, MCMC mixing, or BAR coverage.

The [Japanese report](wp/paired_platform_mc_result_2026-10-19_ja.md), [fixed specification](wp/paired_platform_mc_spec_2026-10-19_ja.md), and [all-condition results](wp/data_paired_platform_mc_2026-10-19/comparison_v1.json) contain the full evidence.
The accompanying validation supplement includes the physical states, logical sectors, labels, environment records, fixed driver, and analysis scripts for this experiment.
It does not contain all raw data from the broader tile study.
