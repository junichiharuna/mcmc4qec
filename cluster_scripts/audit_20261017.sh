#!/bin/bash
#PBS -N m4q_audit
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=128gb
#PBS -l walltime=01:00:00
#PBS -o /home/user/workspace/mcmc4qec/20261017-tile-calibration-v1/audit.out
#PBS -e /home/user/workspace/mcmc4qec/20261017-tile-calibration-v1/audit.err
set -euo pipefail
: "${PBS_JOBID:?submit with qsub after analysis succeeds}"
cd /home/user/workspace/mcmc4qec/20261017-tile-calibration-v1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
# WHAT: all states/trace artifacts/rows, independent aggregation, lossless archives.
# SATURATION: 96 truth chunks, then 2304 groups, then 96 archive partitions.
# MEMORY: bounded per-group reads, compact summaries; 128 GB includes headroom.
# RESUME: originals read-only; use a NEW audit output after investigating failures.
venv/bin/python -m pytest tests/test_calibration_audit.py -q
venv/bin/python cluster_scripts/audit_calibration.py \
  --root runs/production --out runs/audit-v1 --workers 96 \
  --expected-manifest 3782bf338b0a0a1fa69d9f5c1a3157adb9e6ff288f3bcc873590a51021d0d89d
