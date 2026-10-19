"""Size and submit trace-audit jobs without competing with the live coordinator."""
import argparse
import json
import math
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_bar_study as b
import tile_trace_audit_run as r
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers
from submit_tile_analysis import check_completed_case


def capacity_resources():
    return dict(cpus=96,memory_gb=32,wall_seconds=1800,walltime="00:30:00",requested_nodes=1,max_nodes=2,
                warning="Initial resource measurement budget, not a measured runtime or completion guarantee.")


def resource_plan(plan,cap,data):
    if (plan["purpose"],cap["purpose"],plan["replicates"],cap["replicates"])!=("trace_audit_full","trace_audit_capacity",192,24):
        raise ValueError("fixed full/capacity cohorts required")
    for key in ("case","sampling_manifest","platform_profile","platform_fixture","runtime","sources","required_threads"):
        if plan[key]!=cap[key]:
            raise ValueError("capacity and full audit conditions differ")
    records=data["records"]
    if (data["manifest"]!=c.digest(cap) or data["groups"]!=96 or data["failed_audits"] or
        not data.get("native_preflight_sha256") or [tuple(row["group"]) for row in records]!=r.groups(cap)):
        raise ValueError("complete successful fixed capacity and native evidence required")
    for row in records:
        if row["status"]!="ok":
            raise ValueError("failed audit cannot size full audit")
        for key in ("wall_seconds","cpu_seconds","peak_rss_mb"):
            value=row[key]
            if value is None or not math.isfinite(value) or value<=0:
                raise ValueError("positive finite measured time and Linux RSS required")
    phase=data["phase_wall_seconds"]
    if not math.isfinite(phase) or phase<=0:
        raise ValueError("positive measured phase duration required")
    maxima={tuple(row["group"][1:3]):max(other["wall_seconds"] for other in records if other["group"][1:3]==row["group"][1:3]) for row in records}
    predicted=max(phase*8,sum(maxima.values())*192/96)
    seconds=1800*math.ceil((2*predicted+600)/1800)
    peak=max(row["peak_rss_mb"] for row in records)
    memory=max(32,math.ceil(1.5*96*peak/1024+8))
    if seconds>86400 or memory>340:
        raise ValueError("measured request exceeds limits; partition before submission")
    return dict(cpus=96,memory_gb=memory,wall_seconds=seconds,walltime=f"{seconds//3600:02}:{seconds%3600//60:02}:00",
                requested_nodes=1,max_nodes=2,predicted_phase_seconds=predicted,observed_peak_worker_rss_mb=peak,
                capacity_manifest=c.digest(cap),capacity_summary_digest=c.digest(data),
                warning="Fixed-subset resource extrapolation, not a runtime bound or scientific validation.")


def check_source_complete(source,case,runner,execute):
    source=Path(source)
    sampling=json.loads((source/"manifest.json").read_text())
    check_completed_case(sampling,case,json.loads((source/f"sample-{case}.json").read_text()),
                         json.loads((source/f"anchors-{case}.json").read_text()))
    if execute:
        job=json.loads((source/f"submission-{case}.json").read_text())["job_id"]
        result=runner(["qstat","-x","-f","-F","json",job],capture_output=True,text=True,check=True,timeout=30)
        if json.loads(result.stdout)["Jobs"][job]["job_state"]!="F":
            raise ValueError("sampling job is not terminal")


def measured_capacity(root,source,plan):
    cap,_=r.read_plan(root,source)
    data=json.loads((root/"summary.json").read_text())
    if c.file_hash(root/"native_preflight.json")!=data["native_preflight_sha256"]:
        raise ValueError("capacity native evidence changed")
    preflight=json.loads((root/"native_preflight.json").read_text())
    if preflight["manifest"]!=c.digest(cap) or not preflight["pbs_job_id"]:
        raise ValueError("capacity native evidence not bound to actual job")
    r.a.validate_platform(json.loads((root/"platform_profile.json").read_text()),preflight["profile"])
    for row in data["records"]:
        group=tuple(row["group"])
        saved=c.load_artifact(root/"measurements"/c.task_id(group),dict(manifest=c.digest(cap),group=list(group)))
        if saved is None or c.canonical(saved[1])!=c.canonical(row):
            raise ValueError("capacity measurement missing or changed")
        audit=root/"audit/groups"/c.task_id(group)
        if c.file_hash(audit.with_suffix(".done.json"))!=row["audit_marker_sha256"]:
            raise ValueError("capacity audit artifact changed")
        if c.load_artifact(audit,dict(audit=c.digest(cap),group=list(group))) is None:
            raise ValueError("missing audited group")
    return resource_plan(plan,cap,data)


def submit(bundle,root,source,*,capacity_root=None,execute=False,controller_query=live_controllers,
           active_query=own_active_jobs,runner=subprocess.run):
    bundle,root,source=Path(bundle).resolve(),Path(root).resolve(),Path(source).resolve()
    intent,ledger=root/"submission_intent.json",root/"submission.json"
    if intent.exists() or ledger.exists():
        raise ValueError("existing submission/intent; inspect job and never retry automatically")
    plan,_=r.read_plan(root,source)
    if plan["purpose"]=="trace_audit_capacity":
        resource=capacity_resources()
    else:
        if capacity_root is None:
            raise ValueError("completed measured capacity required")
        resource=measured_capacity(Path(capacity_root).resolve(),source,plan)
    if any(char.isspace() for path in (bundle,root,source) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    if execute:
        if controller_query():
            raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query())+1>2:
            raise ValueError("two-node budget exceeded")
    check_source_complete(source,plan["case"],runner,execute)
    path=root/"audit.sh"
    command_line=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_trace_audit_run.py"),
                             "run","--root",str(root),"--source-root",str(source),"--workers","96"])
    path.write_text(f'''#!/bin/bash
#PBS -N m4q_traceaudit
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/audit.out
#PBS -e {root}/audit.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{command_line}
''',newline="\n")
    command=["qsub",str(path)]
    record=dict(command=command,manifest=c.digest(plan),script_sha256=c.file_hash(path),resource=resource,
                submit_source_sha256=c.file_hash(__file__),source_root=str(source))
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
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--capacity-root",type=Path)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,args.source_root,capacity_root=args.capacity_root,execute=args.execute)))


if __name__=="__main__":
    main()
