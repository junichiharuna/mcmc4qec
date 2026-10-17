# Fixed-cohort PBS calibration

This driver uses PBS `qsub`, full 96-core nodes, and at most two concurrent
nodes. It has its own deployment and Python environment. RIMC is a read-only
reference; no git commits, pushes, or notifications are performed by jobs.

The scientific plan is
[calibration_cluster_design_2026-10-17_ja.md](../docs/wp/calibration_cluster_design_2026-10-17_ja.md).
The implemented first stage has 46,080 chains and 64,512 final target rows:
toric3, surface3, Steane; two ladders; stationary and dispersed starts;
192 replicates; four independent chains per rung; 66,000 transitions each.
Rejections and lazy steps are retained. Tile72 and tile288 are exercised in
the smoke; their full calibration and uncertain reference budgets are later
stages, not silently substituted for exact truth.

## Deployment and submission

Build a wheel locally, run `package_bundle.py`, copy the resulting archive
with `scp`, and verify its printed SHA-256 before extracting. Create a new
run directory; do not overwrite a deployed bundle after its manifest exists.
On the cluster, use a **dedicated venv**, based on Python 3.11, then install:

```sh
venv/bin/python -m pip install -r cluster_scripts/requirements.txt dist/mcmc4qec-0.1.0.dev5-py3-none-any.whl
venv/bin/python -m pip freeze > environment.lock.txt
venv/bin/python cluster_scripts/calibration.py plan --root runs/smoke --smoke
venv/bin/python cluster_scripts/submit.py smoke --bundle . --root runs/smoke
venv/bin/python cluster_scripts/submit.py smoke --bundle . --root runs/smoke --execute
qstat -u "$USER"
```

`submit.py` defaults to dry-run. `--execute` invokes `qsub` directly and writes
each returned job ID to `submission.json` immediately. The generated scripts
refuse to run outside PBS. No large job arrays are used. Wait for successful
smoke completion, inspect `timing.json` and PBS exit status, then:

```sh
venv/bin/python cluster_scripts/calibration.py plan --root runs/production
venv/bin/python cluster_scripts/submit.py production --bundle . --root runs/production
venv/bin/python cluster_scripts/submit.py production --bundle . --root runs/production --execute
```

Production submits a truth job, four sampling shards in two dependency lanes,
and analysis after both lanes finish. Walltimes are twice the smoke
extrapolation, rounded upward; requests above 24 hours stop for repartitioning.
Memory is twice measured worker peak RSS × 96, with a 340 GB cap. Existing
active user jobs cause submission to stop so that they cannot silently exceed
the two-node budget. The submission ledger prevents accidental double-submit.
Inspect partial submissions with `qstat` before explicitly resubmitting any
individual generated script using `qsub` and its required `afterok` dependencies.

## Outputs and recovery

- `manifest.json`: fixed cohort, seeds, windows, kernels and runtime digests.
- `truth/`: exact failure banks; matrix and decoder identity checked.
- `traces/`: compact weight, syndrome weight and residual logical bitmask.
- `analysis/`: per-group BAR covariance, intervals and observable diagnostics.
- `coverage_rows.csv`, `summary.json`: every preregistered replicate, including
  unavailable intervals as failures in the unconditional coverage denominator.
- `*.done.json`: artifact identity and SHA-256 of both data and metadata.

Only a valid marker permits resume. A missing marker restarts the entire chain
with its original seed; trajectories from separate calls are never spliced.
A mismatched identity or checksum is an error requiring investigation.
Recorded sampling failures remain in the cohort; they are not replaced by new
seeds. Do not run two writers against the same task directory. If a PBS job
fails, check all earlier dependencies and the ledger before a manual `qsub`.

The analysis histogram formula is restricted to independent homogeneous bit
flips and a fixed deterministic decoder. Circular blocks preserve partial last
blocks and share each rung's bootstrap draw across adjacent BAR edges.
The capacity smoke repeats short traces **only for timing**, and never treats
those as independent scientific samples. Neither diagnostic agreement nor
these finite experiments certify nominal 95% coverage.

## Completion audit and recovery

After the analysis job succeeds, `audit_calibration.py` checks every expected
trace and analysis artifact, verifies exact-bank membership with the public
failure predicate, checks the defining BAR equations and interval arithmetic,
and independently recomputes all cohorts and paired coverage differences.
The scientific inputs remain read-only. Use a fresh audit output directory.
The submitted `audit_20261017.sh` runs through `qsub -W depend=afterok:265194.node-PRISM`;
its job ID and file hashes are in the repository's `cluster_audit_submission.json`.

The audit writes 96 disjoint group archives and one reproduction archive,
plus an inventory with per-file checksums. Copy the completed audit directory
to local `output/cluster_results/20261017-calibration`, then run:

```sh
python cluster_scripts/verify_recovery.py output/cluster_results/20261017-calibration
python cluster_scripts/summarize_calibration.py --root output/cluster_results/20261017-calibration --out docs/wp/data_calibration_2026-10-17/results --figures
```

`verify_recovery.py` verifies each archive and every inventoried file inside
without extracting it. `summarize_calibration.py` produces coverage, mixing and
paired-comparison tables. Its R-hat > 1.01 and per-chain ESS < 100 screens are
post-hoc descriptive flags; primary coverage retains every replicate.
Exactly constant logical indicators are distinguished from undefined
diagnostics for observables with positive exact variance.
