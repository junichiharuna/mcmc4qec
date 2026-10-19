"""Measured, longest-first tile production submissions; qsub and at most two nodes."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import re
from statistics import fmean
import subprocess

import calibration as c
import tile_bar_study as b
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes


def resource_plan(plan,capacity_plan,capacity):
    if plan["purpose"]!="calibration" or capacity_plan["purpose"]!="capacity":
        raise ValueError("wrong stage")
    if capacity["manifest"]!=c.digest(capacity_plan):
        raise ValueError("capacity manifest mismatch")
    expected=set(b.tasks(capacity_plan))
    keys=[tuple(r["task"]) for r in capacity["records"]]
    if set(keys)!=expected or len(keys)!=len(expected) or capacity["tasks"]!=len(keys) or capacity["failed"]:
        raise ValueError("complete successful capacity cohort required")
    strata=defaultdict(list)
    for record in capacity["records"]:
        if record["status"]!="ok" or not math.isfinite(record["wall_seconds"]) or record["wall_seconds"]<=0:
            raise ValueError("invalid capacity timing")
        case,kernel,init,rep,rung,chain=record["task"]
        strata[case,kernel,init,rung].append(record["wall_seconds"])
    output=[]
    for case,spec in enumerate(plan["cases"]):
        if spec!=capacity_plan["cases"][case]:
            raise ValueError("capacity does not cover production trace shape")
        predicted_cpu=0.
        for kernel in range(2):
            for init in range(2):
                extreme=max(fmean(strata[case,kernel,init,rung]) for rung in (0,len(spec["rungs"])-1))
                predicted_cpu+=extreme*plan["replicates"]*spec["chains"]*len(spec["rungs"])
        predicted=predicted_cpu/96
        seconds=3600*math.ceil((2*predicted+600)/3600)
        peak=max(r["peak_rss_mb"] for r in capacity["records"] if r["task"][0]==case)
        if not math.isfinite(peak) or peak<=0:
            raise ValueError("finite Linux RSS measurement required")
        memory=max(32,math.ceil(1.5*96*peak/1024+8))
        if seconds>86400 or memory>340:
            raise ValueError(f"case {case} requires further partitioning: {seconds}s/{memory}GB")
        output.append(dict(case=case,tasks=sum(1 for _ in b.tasks(plan,case)),cpus=96,
                           memory_gb=memory,wall_seconds=seconds,walltime=f"{seconds//3600:02d}:00:00",
                           predicted_sampling_seconds=predicted,observed_peak_worker_rss_mb=peak))
    return dict(manifest=c.digest(plan),capacity_manifest=c.digest(capacity_plan),cases=output,
                order=sorted(range(4),key=lambda case:-output[case]["predicted_sampling_seconds"]),
                max_nodes=2,warning="Resource extrapolation, not a completion-time guarantee.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["plan","next"])
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    root=bundle/"runs/production"
    plan=json.loads((root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(b.make_plan())):
        raise ValueError("production plan/runtime differs")
    cap_plan=json.loads((bundle/"capacity_manifest.json").read_text())
    if cap_plan!=json.loads(c.canonical(b.make_plan(capacity=True))):
        raise ValueError("capacity used a different sampling runtime")
    cap=json.loads((bundle/"capacity_summary.json").read_text())
    allocation=resource_plan(plan,cap_plan,cap)
    allocation.update(capacity_summary_sha256=c.file_hash(bundle/"capacity_summary.json"),
                      submit_source_sha256=c.file_hash(__file__))
    resource_path=root/"resource_plan.json"
    if args.command=="plan":
        if resource_path.exists():
            raise ValueError("resource plan exists")
        c.atomic_json(resource_path,allocation)
        print(json.dumps(allocation))
        return
    if allocation!=json.loads(resource_path.read_text()):
        raise ValueError("resource plan changed")
    remaining=[case for case in allocation["order"] if not (root/f"submission-{case}.json").exists()]
    if not remaining:
        raise ValueError("all cases already submitted; inspect existing jobs")
    if args.execute and requested_nodes(own_active_jobs())+1>2:
        raise ValueError("two-node budget exceeded; wait for an existing job")
    case=remaining[0]
    resource=allocation["cases"][case]
    script=root/f"sample-{case}.sh"
    script.write_text(f'''#!/bin/bash
#PBS -N m4q_tile{case}
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/sample-{case}.out
#PBS -e {root}/sample-{case}.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {bundle}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
# Fixed scientific seeds; capacity samples are not reused.
# 192 anchor tasks followed by the flattened case sampling tasks, 96 workers.
venv/bin/python -m pytest tests/test_tile_bar_study.py tests/test_submit_tile_production.py -q
venv/bin/python cluster_scripts/tile_bar_study.py anchors --root runs/production --case {case} --workers 96
venv/bin/python cluster_scripts/tile_bar_study.py sample --root runs/production --case {case} --workers 96
''',newline="\n")
    command=["qsub",str(script)]
    job="dry-run"
    if args.execute:
        job=subprocess.run(command,capture_output=True,text=True,check=True).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError(f"unexpected qsub response; inspect queue: {job}")
    record=dict(job_id=job,command=command,manifest=c.digest(plan),script_sha256=c.file_hash(script),
                resource_plan_sha256=c.file_hash(resource_path),requested_nodes=1,max_nodes=2,**resource)
    c.atomic_json(root/f"{'submission' if args.execute else 'dry_run'}-{case}.json",record)
    print(json.dumps(record))


if __name__=="__main__":
    main()
