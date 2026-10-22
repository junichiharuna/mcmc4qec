# Local calibration planning pilot

The predeclared scope is three codes, one fixed seed each, a fixed decoder,
bit-flip ladder `[0.10, 0.07, 0.05, 0.03]`, exact anchors and exact target truth,
four chains, 600 saved states, 600 burn-in steps, block length 32 and 100
bootstrap replicates. This is an API/timing pilot, not a coverage experiment.
It is separate from the proposed cluster cohorts and their seed namespace.
Initialization uses the public rejection initializer; the cluster design's
stationary/dispersed arms are not implemented or exercised here.

The initial three-case run exceeded the local approximately five-minute budget.
It was stopped at 307.84 seconds, after toric completed and while processing the
next case. Its emitted toric summary is preserved in `pilot_interrupted.json`;
the full toric Result was not flushed, so that run is not a complete artifact.
The exact enumeration alone took 279.85 seconds under concurrent local load.
Surface and Steane were rerun using their original seeds and scientific settings.
No seed or setting was selected based on interval coverage.

To reproduce the smaller local run from the repository root in PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" docs/wp/data_calibration_2026-10-17/pilot.py --cases surface_d3 steane --out docs/wp/data_calibration_2026-10-17/pilot_surface_steane.json
```

The script refuses to replace an existing output. Use a new output path for a
new experiment. The JSON includes full public results, warnings, package/source
provenance, Python/platform information and a digest of the pilot script.
Local elapsed times do not predict cluster throughput without a cluster smoke.
No external processes, job submission, publication or messages are performed.
Run the toric enumeration through the planned cluster smoke, rather than
repeating the slow local enumeration merely to obtain a timing number.

## Submitted cluster run

The paragraphs above describe the initial local pilot. The implemented PBS
driver subsequently submitted smoke `265188` (exit 0) and production jobs
`265189`–`265194` using `qsub` on 2026-10-17. Each job uses one 96-core node;
the two dependency lanes bound concurrent use to two nodes.

`cluster_smoke_timing.json` records actual smoke worker timings and production
extrapolations, **not completed production times**. Its capacity measurements
repeat traces only for timing; those repetitions never enter scientific results.
`cluster_*_manifest.json` fixes the cohorts and runtime hashes;
`cluster_*_submission.json` preserves exact qsub commands and returned IDs.
`cluster_environment.lock.txt` records the isolated venv, and `cluster_bundle.json`
records the deployed files and baseline commit. The deployed archive SHA-256 is
`482b3bfdb4100aacc014c880f7f6dc85ad649fb0f7d31dad202fa0b877cdc9b1`.
`cluster_truth_*.json` contains checked exact masses from the smoke bank.
The remote run is `/home/user/workspace/mcmc4qec/20261017-tile-calibration-v1`.
Production and audit jobs are now complete, all with exit status 0.
All 46,080 traces and 64,512 analysis rows were audited and recovered, with no
missing artifacts, recorded sampling failures, or unavailable BAR intervals.
See the [final report](../calibration_results_2026-10-17_ja.md) for scientific
conclusions, including the reducible default Z/H kernel in this fixed-decoder
Steane example. Computation completion does not certify nominal coverage.

## Results and verification

- `cluster_completion_status.txt`: PBS terminal status, walltimes, empty user queue.
- `cluster_audit_submission.json`: qsub command, dependency, and audit source hashes.
- `results/audit.json`: full remote audit; `results/recovery.json`: local verification.
- `results/archives.json`, `results/inventory.jsonl.gz`: archive and payload hashes.
- `results/coverage_rows.csv.gz`: all 64,512 rows; decompressed hash matches the audit CSV.
- `results/coverage_summary.csv`: 336 conditions, each retaining all 192 replicates.
- `results/mixing_summary.csv`: 1,776 observable/rung conditions, undefined counts included.
- `results/paired_comparisons.csv`: 816 contrasts, pairing and uncertainty recorded.
- `results/coverage_*.png` / `.pdf`: burn-in 600 comparison figures.
- `results/steane_components.json`: post-hoc finite-support explanation and candidate bridge.
- `audit_validation.json`: initial finite audit tests, recorded before remote completion.
- `completion_validation.json`, `completion_tests.log`: final evidence and focused checks.
- `verify_report.py`: checks published rows, cohort metrics, report tables, links,
  production hashes, terminal job evidence, and preservation of repository state.

Post-hoc R-hat > 1.01, minimum chain ESS < 100, or undefined diagnostics are
descriptive flags; no replicate is removed from primary coverage. Structurally
constant observables are distinguished from stuck traces with positive exact
variance. All production inputs and public sampling defaults remain unchanged.

The 97 raw archives (1,636,106,601 bytes, 145,449 verified payloads) are kept in
`A:/dev/mcmc4qec/output/cluster_results/20261017-calibration/archives/` (gitignored)
and remotely under the deployed bundle's `runs/audit-v1/archives/`.
The local audit directory also contains full covariance rows and diagnostics
in `rows.jsonl.gz` and `diagnostics.jsonl.gz`, plus the manifest and raw summaries.
The reproduction archive preserves the production wheel, driver, environment,
PBS scripts, and original run records; use these immutable files for a rerun.

To recover into a new local directory and reproduce checks/tables in PowerShell:

```powershell
$recovered = 'output/cluster_results/20261017-calibration-copy'
New-Item -ItemType Directory -Path $recovered
scp -r cluster:/home/user/workspace/mcmc4qec/20261017-tile-calibration-v1/runs/audit-v1/. $recovered
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" cluster_scripts/verify_recovery.py $recovered
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" cluster_scripts/summarize_calibration.py --root $recovered --out output/calibration-tables-copy --figures
$env:PYTHONPATH = (Resolve-Path src).Path
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" cluster_scripts/steane_components.py --out output/steane-components-copy.json
```

Verification needs only the standard library; figures require matplotlib.
The finite Steane analysis requires the recorded optional decoder dependencies.
It is a small enumeration, not a new production calibration.
From this original checkout, the final report checks can be repeated with
`Python311/python.exe docs/wp/data_calibration_2026-10-17/verify_report.py` using
the absolute Python 3.11 executable path above.
For sampling reruns use the [PBS driver instructions](../../../cluster_scripts/README.md)
and a new run directory, always qsub and at most two nodes.


## Redaction notice (2026-10-22)

The repository copies of these records are redacted: the cluster user name,
other users' home paths, host names, and the Windows user name were replaced
before publication. SHA-256 values recorded inside the records refer to the
unredacted originals, which are kept outside the repository, so verifying a
repository copy against a recorded hash fails by design. The hashes themselves
were not rewritten.
