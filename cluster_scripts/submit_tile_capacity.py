"""Submit the long-trace capacity smoke without exceeding two nodes."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import calibration as c
import tile_bar_study as b
from submit import own_active_jobs


def requested_nodes(jobs):
    count=0
    for data in jobs.values():
        select=data["Resource_List"]["select"]
        for segment in select.split("+"):
            count+=int(segment.split(":")[0])
    return count


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    root=bundle/"runs/capacity"
    plan=json.loads((root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(b.make_plan(capacity=True))):
        raise ValueError("capacity manifest differs")
    pilot=json.loads((bundle/"pilot_summary.json").read_text())
    if pilot["failed"] or pilot["tasks"]!=96:
        raise ValueError("successful 96-task pilot required")
    if (root/"submission.json").exists():
        raise ValueError("existing ledger; inspect qstat before retry")
    if args.execute and requested_nodes(own_active_jobs())+1>2:
        raise ValueError("two-node budget exceeded")
    path=root/"capacity.sh"
    path.write_text(f'''#!/bin/bash
#PBS -N m4q_tilecap
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=64gb
#PBS -l walltime=00:30:00
#PBS -o {root}/capacity.out
#PBS -e {root}/capacity.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {bundle}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
# 384 long-trace tasks, 96 per code/noise; bounded cache, immutable outputs.
# These timing samples have a disjoint seed namespace and never enter cohorts.
venv/bin/python -m pytest tests/test_tile_bar_study.py -q
venv/bin/python cluster_scripts/tile_bar_study.py capacity --root runs/capacity --workers 96
''',newline="\n")
    command=["qsub",str(path)]
    job_id="dry-run"
    if args.execute:
        job_id=subprocess.run(command,capture_output=True,text=True,check=True).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job_id):
            raise RuntimeError(f"unexpected qsub response; inspect queue: {job_id}")
    record=dict(job_id=job_id,command=command,manifest=c.digest(plan),script_sha256=c.file_hash(path),
                requested_nodes=1,max_nodes=2,cpus=96,memory_gb=64,walltime="00:30:00")
    c.atomic_json(root/("submission.json" if args.execute else "dry_run.json"),record)
    print(json.dumps(record))


if __name__=="__main__":
    main()
