"""Submit the independent weight-stratum pilot through qsub, within two nodes."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import calibration as c
import tile_weight_pilot as w
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    root=bundle/"runs/weight-pilot"
    plan=json.loads((root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(w.make_plan())):
        raise ValueError("weight pilot manifest/runtime differs")
    if (root/"submission.json").exists():
        raise ValueError("existing ledger; inspect existing job")
    if args.execute and requested_nodes(own_active_jobs())+1>2:
        raise ValueError("two-node budget exceeded")
    script=root/"pilot.sh"
    script.write_text(f'''#!/bin/bash
#PBS -N m4q_tileweight
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=32gb
#PBS -l walltime=00:30:00
#PBS -o {root}/pilot.out
#PBS -e {root}/pilot.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {bundle}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
# 1536 bounded independent tasks, sorted large-code/high-weight first.
# These allocation/timing samples are excluded from subsequent reference MC.
venv/bin/python -m pytest tests/test_tile_weight_stratified.py tests/test_tile_weight_pilot.py -q
venv/bin/python cluster_scripts/tile_weight_pilot.py run --root runs/weight-pilot --workers 96
''',newline="\n")
    command=["qsub",str(script)]
    job="dry-run"
    if args.execute:
        job=subprocess.run(command,text=True,capture_output=True,check=True).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError(f"unexpected qsub response; inspect queue: {job}")
    record=dict(job_id=job,command=command,manifest=c.digest(plan),script_sha256=c.file_hash(script),
                requested_nodes=1,max_nodes=2,cpus=96,memory_gb=32,walltime="00:30:00")
    c.atomic_json(root/("submission.json" if args.execute else "dry_run.json"),record)
    print(json.dumps(record))


if __name__=="__main__":
    main()
