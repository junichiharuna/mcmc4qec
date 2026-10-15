# Controlled block-length calibration, 2026-10-15

This directory contains a predeclared, small toric d=3 experiment.
See `plan_ja.md` for the fixed design and `../calibration_2026-10-15_ja.md` for interpretation.
`block{8,32,128}_runs.csv` retain every seed, and matching summary CSVs and logs record elapsed time.
`truth_cache.json` was freshly enumerated with the measured package source.
`environment.json` records the source HEAD, package versions, and plan/benchmark hashes.
The package source hash is also embedded in the checked truth cache and every raw CSV row.
The benchmark differs from the recorded HEAD only by the additional target ESS/R-hat CSV columns.
No production package code was changed in this worktree.

From the repository root, set `PYTHONPATH` to its `src` directory and use the Python 3.11 environment with PyMatching installed.
The measured executable was `A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe`.
The commands were:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = (Resolve-Path src).Path
$py = 'A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe'
& $py benchmarks/bar_paper_protocol.py --make-truth-cache docs/wp/data_calibration_2026-10-15/truth_cache.json
foreach ($block in @(8, 32, 128)) {
    & $py benchmarks/bar_sensitivity.py --scenario anchor_exact --seeds 20 --seed-start 6100 --samples 600 --chains 4 --burn-in 180 --bootstrap-replicates 100 --block $block --label "block$block" --truth-cache docs/wp/data_calibration_2026-10-15/truth_cache.json --out docs/wp/data_calibration_2026-10-15
}
& $py docs/wp/data_calibration_2026-10-15/recompute.py
& $py -m pytest tests/test_bar_block_control.py -q
```

Use a separate output directory for new measurements to preserve these historical artifacts.
After source changes, regenerate a cache with the new source rather than bypassing its source check.
`recompute.py` needs only the standard library and recalculates `summary.csv` and `paired.csv` from the saved data without a sampling run.
It checks complete cohorts, fixed settings, cache digests, independently recalculated exact probability, interval arithmetic, and equality of paired point estimates and diagnostics.
Its assertions require normal Python execution (without `-O`).
Seeds are common across blocks; bootstrap child seeds are therefore common too, but different block lengths consume them differently.
The API regenerates the same sampling streams for each block instead of saving/reusing state arrays.
The small API regression test checks that the rung metadata, point estimates, and diagnostics remain identical across block lengths.
The raw cohort validation checks the paired quantities but does not claim a saved-state-array comparison.
An initial attempt to start block8 before cache generation finished failed with FileNotFoundError before any sampling; it was rerun after the cache completed.
No seed or setting was changed after observing results.
