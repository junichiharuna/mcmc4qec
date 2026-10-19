"""Submit fixed MC timing cohorts after the existing coordinator has stopped."""
import argparse
import json
import math
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_mc_time_benchmark as m
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes


def capacity_resources():
    return dict(cpus=96,memory_gb=32,wall_seconds=1800,walltime="00:30:00",
                requested_nodes=1,max_nodes=2,stage="capacity")


def resource_plan(plan,cap,data):
    if plan["purpose"]!="mc_precision_benchmark" or cap["purpose"]!="mc_precision_capacity":
        raise ValueError("wrong timing stages")
    for key in ("conditions","runtime","budget_digest","cases","decoder","required_threads","native_input_digests"):
        if plan[key]!=cap[key]:
            raise ValueError("capacity conditions or runtime differ")
    if (plan["replicates"],cap["replicates"],plan["seed_stage"],cap["seed_stage"])!=(192,96,121,122):
        raise ValueError("fixed cohort sizes and separate namespaces required")
    expected=set(m.tasks(cap))
    keys=[tuple(row["task"]) for row in data["records"]]
    if (data["manifest"]!=c.digest(cap) or data["purpose"]!=cap["purpose"] or data["failed"]
        or set(keys)!=expected or len(keys)!=len(expected) or data["tasks"]!=len(keys)):
        raise ValueError("complete successful capacity required")
    for row in data["records"]:
        task=tuple(row["task"])
        if row["status"]!="ok" or row["seed"]!=m.task_seed(cap,task) or row["trials"]!=cap["conditions"][task[0]]["planned_trials"]:
            raise ValueError("capacity metadata differs")
        for key in ("task_wall_seconds","cpu_seconds","peak_rss_mb"):
            value=row[key]
            if value is None or not math.isfinite(value) or value<=0:
                raise ValueError("positive finite task timing and Linux RSS required")
    phase=data["phase_wall_seconds"]
    if not math.isfinite(phase) or phase<=0:
        raise ValueError("positive phase walltime required")
    predicted=phase*plan["replicates"]/cap["replicates"]
    seconds=1800*math.ceil((2*predicted+600)/1800)
    peak=max(row["peak_rss_mb"] for row in data["records"])
    memory=max(32,math.ceil(1.5*96*peak/1024+8))
    if seconds>86400 or memory>340:
        raise ValueError("measured request exceeds limits; partition before submission")
    return dict(cpus=96,memory_gb=memory,wall_seconds=seconds,
                walltime=f"{seconds//3600:02}:{(seconds%3600)//60:02}:00",requested_nodes=1,max_nodes=2,
                stage="benchmark",predicted_phase_seconds=predicted,observed_peak_worker_rss_mb=peak,
                manifest=c.digest(plan),capacity_manifest=c.digest(cap),capacity_summary_digest=c.digest(data),
                warning="Resource extrapolation only, not an accuracy or completion-time guarantee.")


def live_controllers():
    user=subprocess.run(["id","-un"],capture_output=True,text=True,check=True,timeout=30).stdout.strip()
    result=subprocess.run(["ps","-u",user,"-o","args="],capture_output=True,text=True,check=True,timeout=30)
    matches=[]
    for line in result.stdout.splitlines():
        tokens=shlex.split(line)
        if any(Path(token).name=="tile_coordinator.py" and index+1<len(tokens) and tokens[index+1]=="run"
               for index,token in enumerate(tokens)):
            matches.append(line)
    return matches


def measured_capacity(root,plan):
    root=Path(root)
    cap=json.loads((root/"manifest.json").read_text())
    budget=json.loads((root/"budget.json").read_text())
    if c.canonical(cap)!=c.canonical(m.make_plan(budget,capacity=True)):
        raise ValueError("capacity manifest, source or runtime changed")
    for key,digest in cap["native_input_digests"].items():
        if c.digest(json.loads((root/(key+".json")).read_text()))!=digest:
            raise ValueError("capacity native input changed")
    data=json.loads((root/"summary.json").read_text())
    if c.file_hash(root/"native_preflight.json")!=data["native_preflight_sha256"]:
        raise ValueError("capacity native evidence changed")
    preflight=json.loads((root/"native_preflight.json").read_text())
    intent=json.loads((root/"execution_intent.json").read_text())
    if (preflight["manifest"]!=c.digest(cap) or not preflight["pbs_job_id"] or not preflight["hostname"]
        or any(intent[key]!=preflight[key] for key in ("manifest","pbs_job_id","hostname"))):
        raise ValueError("capacity compute execution binding missing or different")
    m.trace_audit.validate_platform(json.loads((root/"platform_profile.json").read_text()),preflight["profile"])
    resource=resource_plan(plan,cap,data)
    for row in data["records"]:
        task=row["task"]
        base=root/"tasks"/c.task_id(task)
        marker=base.with_suffix(".done.json")
        if not marker.exists() or set(json.loads(marker.read_text())["sha256"])!={".json",".npz"}:
            raise ValueError("missing complete capacity artifact marker")
        saved=c.load_artifact(base,dict(manifest=c.digest(cap),task=task))
        if saved is None:
            raise ValueError("missing measured capacity task")
        record=saved[1]
        if c.canonical({k:v for k,v in record.items() if k!="metadata"})!=c.canonical(row):
            raise ValueError("capacity raw task and summary differ")
        metadata=record["metadata"]
        condition=cap["conditions"][task[0]]
        if (c.digest(metadata)!=record["metadata_sha256"] or metadata["sampling_p"]!=condition["target_p"]
            or metadata["rng"]["entropy"]!=m.task_seed(cap,task)):
            raise ValueError("capacity actual MC metadata differs")
    return resource


def submit(bundle,root,plan,resource,*,execute,controller_query=live_controllers,active_query=own_active_jobs,runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    root.mkdir(parents=True,exist_ok=True)
    intent=root/"submission_intent.json"
    ledger=root/"submission.json"
    if intent.exists() or ledger.exists() or (root/"execution_intent.json").exists() or (root/"tasks").exists() or (root/"summary.json").exists():
        raise ValueError("existing submission/intent; inspect the recorded job, never retry automatically")
    if resource["cpus"]!=96 or resource["requested_nodes"]!=1 or resource["max_nodes"]!=2 or not 1<=resource["memory_gb"]<=340 or not 0<resource["wall_seconds"]<=86400:
        raise ValueError("invalid resource request")
    if execute:
        if controller_query():
            raise ValueError("existing tile coordinator is running; do not compete for submission slots")
        if requested_nodes(active_query())+1>2:
            raise ValueError("two-node budget exceeded")
    path=root/"timing.sh"
    if any(char.isspace() for char in str(root)) or any(char.isspace() for char in str(bundle)):
        raise ValueError("PBS deployment paths must not contain whitespace")
    command_line=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_mc_time_benchmark.py"),
                             "run","--root",str(root),"--workers","96"])
    path.write_text(f'''#!/bin/bash
#PBS -N m4q_mctime
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
    record=dict(command=command,manifest=c.digest(plan),script_sha256=c.file_hash(path),
                resource=resource,submit_source_sha256=c.file_hash(__file__))
    job="dry-run"
    if execute:
        with intent.open("xb") as stream:
            stream.write(c.canonical(record)+b"\n")
        job=runner(command,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unrecognized qsub response; intent retained, inspect queue before any further action")
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
    plan=json.loads((args.root/"manifest.json").read_text())
    budget=json.loads((args.root/"budget.json").read_text())
    capacity=plan["purpose"]=="mc_precision_capacity"
    if plan!=json.loads(c.canonical(m.make_plan(budget,capacity=capacity))):
        raise ValueError("timing manifest or runtime changed")
    if capacity:
        resource=capacity_resources()
    else:
        if args.capacity_root is None:
            raise ValueError("completed capacity required for benchmark")
        resource=measured_capacity(args.capacity_root,plan)
    print(json.dumps(submit(args.bundle,args.root,plan,resource,execute=args.execute)))


if __name__=="__main__":
    main()
