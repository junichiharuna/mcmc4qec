"""Submit case-partitioned BAR timing after complete measured capacity."""
import argparse
import json
import math
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_bar_time_benchmark as m
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def read_plan(root):
    root=Path(root)
    plan=json.loads((root/"manifest.json").read_text())
    settings=json.loads((root/"settings.json").read_text())
    if plan.get("case") not in range(4):
        raise ValueError("one case per timing job required")
    expected=m.make_plan(settings,capacity=plan["purpose"]=="bar_time_capacity",case=plan["case"])
    if c.canonical(plan)!=c.canonical(expected) or not list(m.tasks(plan)):
        raise ValueError("fixed nonempty case plan, source and runtime required")
    for key,digest in plan["native_input_digests"].items():
        if c.digest(json.loads((root/(key+".json")).read_text()))!=digest:
            raise ValueError("native input changed")
    return plan


def capacity_resources():
    return dict(cpus=96,memory_gb=340,wall_seconds=86400,walltime="24:00:00",requested_nodes=1,max_nodes=2,
                stage="capacity",warning="Initial per-case resource ceiling, not measured consumption or a completion guarantee.")


def resource_plan(plan,cap,data):
    if (plan["purpose"],cap["purpose"],plan["replicates"],cap["replicates"],plan["seed_stage"],cap["seed_stage"])!=("bar_time_benchmark","bar_time_capacity",192,96,140,141):
        raise ValueError("fixed separate timing stages required")
    different={k for k in set(plan)|set(cap) if plan.get(k)!=cap.get(k)}
    if different!={"purpose","replicates","seed_stage"} or plan["case"] not in range(4):
        raise ValueError("capacity and benchmark settings, case, source or runtime differ")
    expected=list(m.tasks(cap))
    records=data["records"]
    if (not expected or data["manifest"]!=c.digest(cap) or data["tasks"]!=len(expected)
        or [tuple(row["task"]) for row in records]!=expected or data["failed"] or data["unavailable"]
        or data["reused_tasks"] or not data.get("native_preflight_sha256")):
        raise ValueError("complete fresh successful capacity required")
    for row in records:
        task=tuple(row["task"])
        condition=cap["conditions"][task[0]]
        if (row["status"]!="ok" or not row["available"] or row["reused"] or row["replicate"]!=task[1]
            or any(row[k]!=condition[k] for k in ("case","epsilon","condition"))
            or row["anchor_seed"]!=m.task_seed(cap,task,0,0,0) or row["bootstrap_seed"]!=m.task_seed(cap,task,0,0,3)):
            raise ValueError("capacity task identity, seed or outcome differs")
        for key in ("task_wall_seconds","cpu_seconds","peak_rss_mb"):
            value=row[key]
            if value is None or not math.isfinite(value) or value<=0:
                raise ValueError("positive measured time and Linux RSS required")
    phase=data["phase_wall_seconds"]
    if not math.isfinite(phase) or phase<=0:
        raise ValueError("positive phase duration required")
    maxima={index:max(row["task_wall_seconds"] for row in records if row["task"][0]==index) for index in {t[0] for t in expected}}
    predicted=max(phase*2,sum(maxima.values())*192/96)
    seconds=1800*math.ceil((2*predicted+600)/1800)
    peak=max(row["peak_rss_mb"] for row in records)
    memory=max(32,math.ceil(1.5*96*peak/1024+8))
    if seconds>86400 or memory>340:
        raise ValueError("request exceeds per-node limits; partition before submission")
    return dict(cpus=96,memory_gb=memory,wall_seconds=seconds,walltime=f"{seconds//3600:02}:{seconds%3600//60:02}:00",
                requested_nodes=1,max_nodes=2,stage="benchmark",predicted_phase_seconds=predicted,
                observed_peak_worker_rss_mb=peak,manifest=c.digest(plan),capacity_manifest=c.digest(cap),
                capacity_summary_digest=c.digest(data),warning="Resource extrapolation only, not achieved precision or runtime guarantee.")


def measured_capacity(root,plan):
    root=Path(root)
    cap=read_plan(root)
    data=json.loads((root/"summary.json").read_text())
    if c.file_hash(root/"native_preflight.json")!=data["native_preflight_sha256"]:
        raise ValueError("capacity native evidence changed")
    preflight=json.loads((root/"native_preflight.json").read_text())
    if preflight["manifest"]!=c.digest(cap) or not preflight["pbs_job_id"] or not preflight["hostname"]:
        raise ValueError("capacity compute-node evidence missing")
    m.native.trace_audit.validate_platform(json.loads((root/"platform_profile.json").read_text()),preflight["profile"])
    resource=resource_plan(plan,cap,data)
    for row in data["records"]:
        task=row["task"]
        saved=c.load_artifact(root/"tasks"/c.task_id(task),dict(manifest=c.digest(cap),task=task))
        if saved is None:
            raise ValueError("missing measured task")
        reduced={k:v for k,v in saved[1].items() if k not in ("chains","anchor")}
        reduced["reused"]=False
        if c.canonical(reduced)!=c.canonical(row):
            raise ValueError("capacity raw task and summary differ")
    return resource


def submit(bundle,root,*,capacity_root=None,execute=False,controller_query=live_controllers,
           active_query=own_active_jobs,runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    intent,ledger=root/"submission_intent.json",root/"submission.json"
    if intent.exists() or ledger.exists() or (root/"execution_intent.json").exists():
        raise ValueError("existing intent or submission; inspect job, never retry automatically")
    plan=read_plan(root)
    if plan["purpose"]=="bar_time_capacity":
        resource=capacity_resources()
    else:
        if capacity_root is None:
            raise ValueError("complete measured capacity required")
        resource=measured_capacity(capacity_root,plan)
    if any(char.isspace() for path in (root,bundle) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    if execute:
        if controller_query():
            raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query())+1>2:
            raise ValueError("two-node budget exceeded")
    path=root/"timing.sh"
    command_line=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_bar_time_benchmark.py"),"run","--root",str(root),"--workers","96"])
    path.write_text(f'''#!/bin/bash
#PBS -N m4q_bartime
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/timing.out
#PBS -e {root}/timing.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{command_line}
''',newline="\n")
    command=["qsub",str(path)]
    record=dict(command=command,manifest=c.digest(plan),resource=resource,script_sha256=c.file_hash(path),submit_source_sha256=c.file_hash(__file__))
    job="dry-run"
    if execute:
        with intent.open("xb") as stream:
            stream.write(c.canonical(record)+b"\n")
        job=runner(command,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unrecognized qsub response; intent retained, inspect queue")
    record["job_id"]=job
    c.atomic_json(ledger if execute else root/"dry_run.json",record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--capacity-root",type=Path)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,capacity_root=args.capacity_root,execute=args.execute)))


if __name__=="__main__":
    main()
