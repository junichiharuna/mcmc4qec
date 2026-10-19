#!/bin/bash
#PBS -N m4q_bartime
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=32gb
#PBS -l walltime=00:30:00
#PBS -o /home/user/workspace/mcmc4qec/20261018-tile-bar-seed-audit-v1/runs/benchmark-0/timing.out
#PBS -e /home/user/workspace/mcmc4qec/20261018-tile-bar-seed-audit-v1/runs/benchmark-0/timing.err
set -euo pipefail
: "${PBS_JOBID:?submit with qsub}"
cd /home/user/workspace/mcmc4qec/20261018-tile-bar-seed-audit-v1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
/home/user/workspace/mcmc4qec/20261018-tile-bar-seed-audit-v1/venv/bin/python /home/user/workspace/mcmc4qec/20261018-tile-bar-seed-audit-v1/cluster_scripts/tile_bar_time_benchmark.py run --root /home/user/workspace/mcmc4qec/20261018-tile-bar-seed-audit-v1/runs/benchmark-0 --workers 96
