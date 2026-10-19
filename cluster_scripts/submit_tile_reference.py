"""Submit the pinned reference stage; only qsub, at most two full nodes."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import calibration as c
import tile_reference as r
from submit import own_active_jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    root = bundle/"runs/reference"
    plan = json.loads((root/"manifest.json").read_text())
    if plan != json.loads(c.canonical(r.make_plan())):
        raise ValueError("reference manifest differs")
    if (root/"submission.json").exists():
        raise ValueError("existing submission ledger; inspect qstat before any retry")
    if args.execute and own_active_jobs():
        raise ValueError("submit reference only after preceding pilot finishes")
    path = root/"reference.sh"
    path.write_text(f'''#!/bin/bash
#PBS -N m4q_tileref
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=32gb
#PBS -l walltime=02:00:00
#PBS -o {root}/reference.out
#PBS -e {root}/reference.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {bundle}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
# 1248 independent chunks, sorted longest first; each returns one bounded Result.
# 96-worker RSS budget is over twice pilot maxima; no full trajectory storage.
venv/bin/python -m pytest tests/test_tile_reference.py -q
venv/bin/python cluster_scripts/tile_reference.py run --root runs/reference --workers 96
''', newline="\n")
    command = ["qsub", str(path)]
    job_id = "dry-run"
    if args.execute:
        job_id = subprocess.run(command,capture_output=True,text=True,check=True).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", job_id):
            raise RuntimeError(f"unexpected qsub response; inspect queue: {job_id}")
    record = dict(job_id=job_id, command=command, manifest=c.digest(plan), script_sha256=c.file_hash(path),
                  requested_nodes=1, max_nodes=2, cpus=96, memory_gb=32, walltime="02:00:00")
    c.atomic_json(root/("submission.json" if args.execute else "dry_run.json"), record)
    print(json.dumps(record))


if __name__ == "__main__":
    main()
