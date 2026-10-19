"""Submit one full-node tile pilot via qsub, with a persistent submission ledger."""
import argparse
import json
from pathlib import Path
import re
import subprocess

import calibration as c
import tile_study as t
from submit import own_active_jobs


def submit(bundle, execute=False):
    bundle = Path(bundle).resolve()
    root = bundle/"runs/tile-pilot"
    plan = json.loads((root/"manifest.json").read_text())
    if plan != json.loads(c.canonical(t.make_plan())):
        raise ValueError("pilot plan differs from fixed plan or runtime")
    ledger_path = root/"submission.json"
    if ledger_path.exists():
        raise ValueError("existing ledger: inspect qstat; do not submit twice")
    if execute and own_active_jobs():
        raise ValueError("active jobs exist; reconcile the two-node budget first")
    script = root/"pilot.sh"
    script.write_text(f'''#!/bin/bash
#PBS -N m4q_tilepilot
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=128gb
#PBS -l walltime=00:30:00
#PBS -o {root}/pilot.out
#PBS -e {root}/pilot.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {bundle}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
# 96 independent tasks; bounded 512-step traces and 20k-entry decode caches.
# Immutable artifacts permit resume only after matching both payload hashes.
venv/bin/python -m pytest tests/test_tile_study.py -q
venv/bin/python cluster_scripts/tile_study.py pilot --root runs/tile-pilot --workers 96
''', newline="\n")
    command = ["qsub", str(script)]
    job_id = "dry-run"
    if execute:
        job_id = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", job_id):
            raise RuntimeError(f"unexpected qsub response; inspect qstat before retry: {job_id}")
    record = dict(job_id=job_id, command=command, manifest=c.digest(plan), script_sha256=c.file_hash(script),
                  max_nodes=2, requested_nodes=1, cpus=96, memory_gb=128, walltime="00:30:00")
    c.atomic_json(ledger_path if execute else root/"dry_run.json", record)
    print(json.dumps(record))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    submit(args.bundle, args.execute)
