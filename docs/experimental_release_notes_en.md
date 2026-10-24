# Experimental release notes

These notes describe experimental version 0.1.0.dev5 of mcmc4qec, dated 2026-10-24.
A PyPI release will follow separately.
Completed validation checks and their limits are recorded in the readiness record linked below.

mcmc4qec provides direct Monte Carlo, failure-conditioned MCMC, and BAR splitting for logical error-rate estimation.
This release adds tile code construction and BP-LSD, BeliefFind, and standalone Union-Find adapters alongside the existing BP-OSD and matching interfaces.
See the [API](api_en.md), [tutorial](tutorial_en.md), and [runnable examples](../examples/README.md).

## Getting started from a checkout

Use Python 3.11 or later in a virtual environment.
From the repository root:

```sh
python -m pip install '.[bposd,codes]' 'ldpc==2.4.1'
python examples/decoder_comparison.py --code steane --quick
python examples/decoder_comparison.py --code tile72 --quick
python examples/workflows/tile_capacity_fixed_prior.py --help
```

These short examples demonstrate the interface; their sample counts do not establish research precision.
The core package can be installed with `python -m pip install .` without optional decoder dependencies.

## Data included in the release

The source snapshot contains code, documentation, selected validation tables and reports, and the data fixtures needed by its tests.
It does not contain the complete raw trace and weight-stratified sampling datasets.
Those datasets are being preserved separately; a public download location for the complete datasets has not yet been established.
The plan is a Zenodo dataset record after the low-noise validation completes, containing a redacted copy of the raw data with its own SHA-256 manifest.
The operational runbooks and evidence records come from the author's cluster environment.
User and host names were redacted before publication, so SHA-256 values recorded inside the evidence refer to the unredacted originals kept outside the repository.
Some referenced transport archives are not included in this source snapshot.
Use the runnable examples to check the installation; complete independent reanalysis of the reported scientific experiments requires the corresponding raw-data and execution bundles.

## Supported scope and limitations

- BP-LSD supports order 0. Positive orders are rejected, and zero syndrome uses an explicitly recorded identity-correction rule.
- BeliefFind defaults to inversion. Peeling requires a graphlike check matrix with column weights 1 or 2; tile codes cannot be passed directly to peeling.
- Standalone Union-Find is unweighted, accepts only the validated `ldpc==2.4.1` interface, and supports `bits_per_step=1`. Both Union-Find families reject zero columns.
- Keep the decoder prior, settings, and native environment fixed across every BAR rung and its reference calculation. For depolarizing noise, retain the joint Pauli noise model; a sector decoder prior of `2*p/3` does not make the physical sectors independent.
- BP-OSD produced a different failure label for one tested tile288 depolarizing state on Windows and Linux. Equal package versions do not establish equal failure sets across environments.
- The main four tile validation conditions have completed, but low-noise calibration and timing studies remain in progress. Observed mixing problems and interval undercoverage prevent a general claim of nominal 95% coverage or speed improvement.
- The new decoder interfaces have acceptance tests and small-code checks. Their BAR accuracy, coverage, and speed rankings have not been calibrated.

The [tile report](wp/tile_validation_report_2026-10-18_ja.md), [study status](wp/tile_validation_status_2026-10-17_ja.md), and [decoder validation](wp/basic_decoders_validation_2026-10-18_ja.md) describe the evidence and its limits in Japanese.
The [release readiness record](wp/experimental_release_readiness_2026-10-19_ja.md) distinguishes successful checks from pending or timed-out checks.

Long-running validation will continue after the experimental release.
Undefined diagnostics, missing intervals, and unconverged runs remain in the reported denominators.
Agreement between settings without an independent reference is not an accuracy or coverage guarantee.
