"""Submit the full-shape synthetic analysis resource profile via qsub."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import calibration as c
import tile_analysis_capacity as a
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    root=bundle/"runs/analysis-capacity"
    plan=json.loads((root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(a.make_plan())):
        raise ValueError("analysis capacity manifest changed")
    if (root/"submission.json").exists():
        raise ValueError("existing ledger; inspect qstat instead of resubmitting")
    if args.execute and requested_nodes(own_active_jobs())+1>2:
        raise ValueError("two-node budget exceeded")
    script=root/"capacity.sh"
    script.write_text(f'''#!/bin/bash
#PBS -N m4q_tileacap
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=256gb
#PBS -l walltime=02:00:00
#PBS -o {root}/capacity.out
#PBS -e {root}/capacity.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {bundle}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
# 96 full-shape groups; artificial data used for timing/RSS only.
# Prefix-count bootstrap requires O(chains*steps*(n+1)) memory.
venv/bin/python -m pytest tests/test_tile_analysis_capacity.py tests/test_tile_bar_analysis.py tests/test_tile_summary.py -q
venv/bin/python cluster_scripts/tile_analysis_capacity.py run --root runs/analysis-capacity --workers 96
''',newline="\n")
    command=["qsub",str(script)]
    job="dry-run"
    if args.execute:
        job=subprocess.run(command,text=True,capture_output=True,check=True).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError(f"unexpected qsub response; inspect queue: {job}")
    record=dict(job_id=job,command=command,manifest=c.digest(plan),script_sha256=c.file_hash(script),
                requested_nodes=1,max_nodes=2,cpus=96,memory_gb=256,walltime="02:00:00",synthetic=True)
    c.atomic_json(root/("submission.json" if args.execute else "dry_run.json"),record)
    print(json.dumps(record))


if __name__=="__main__":
    main()
