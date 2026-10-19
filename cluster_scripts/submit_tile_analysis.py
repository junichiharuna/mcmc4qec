"""Submit measured tile analysis after complete recorded sampling, including failures."""
import argparse
import itertools
import json
import math
from pathlib import Path
import re
from statistics import fmean
import subprocess

import calibration as c
import tile_bar_study as b
import tile_bar_analysis as a
import tile_analysis_capacity as p
import tile_summary as summary_module
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes


def resource_plan(plan,profile,data):
    if profile["purpose"]!="synthetic_analysis_capacity" or plan["purpose"]!="calibration":
        raise ValueError("wrong resource-profile stage")
    for key in ("cases","burns","blocks","bootstrap_replicates","chain_counts","runtime"):
        if plan[key]!=profile[key]:
            raise ValueError(f"profile does not cover production {key}")
    expected=set(itertools.product(range(4),range(profile["replicates"])))
    keys=[tuple(row["task"]) for row in data["records"]]
    if data["manifest"]!=c.digest(profile) or not data["synthetic"] or data["failed"] or data["tasks"]!=len(expected):
        raise ValueError("complete successful synthetic profile required")
    if set(keys)!=expected or len(keys)!=len(expected):
        raise ValueError("missing or duplicate resource-profile group")
    for row in data["records"]:
        if row["status"]!="ok" or not row["synthetic"] or not math.isfinite(row["analysis_seconds"]) or row["analysis_seconds"]<=0:
            raise ValueError("invalid measured profile")
    output=[]
    groups=4*plan["replicates"]
    for case in range(4):
        rows=[row for row in data["records"] if row["task"][0]==case]
        predicted=fmean(row["analysis_seconds"] for row in rows)*groups/96
        seconds=3600*math.ceil((2*predicted+600)/3600)
        peak=max(row["peak_rss_mb"] for row in rows)
        if not math.isfinite(peak) or peak<=0:
            raise ValueError("finite Linux peak RSS required")
        memory=max(32,math.ceil(1.5*96*peak/1024+8))
        if seconds>86400 or memory>340:
            raise ValueError(f"case {case} needs additional partitioning: {seconds}s/{memory}GB")
        output.append(dict(case=case,groups=groups,cpus=96,memory_gb=memory,wall_seconds=seconds,
                           walltime=f"{seconds//3600:02d}:00:00",predicted_analysis_seconds=predicted,
                           observed_peak_worker_rss_mb=peak))
    return dict(manifest=c.digest(plan),capacity_manifest=c.digest(profile),max_nodes=2,cases=output,
                warning="Synthetic profile sizes resources only; it does not measure scientific mixing or coverage.")


def check_completed_case(plan,case,samples,anchors):
    for name,record in (("sample",samples),("anchors",anchors)):
        if record["manifest"]!=c.digest(plan) or record["case"]!=case or record["command"]!=name:
            raise ValueError("wrong stage summary")
        rows=record["records"]
        if name=="sample":
            keys=[tuple(row["task"]) for row in rows]
            expected=set(b.tasks(plan,case))
        else:
            keys=[(row["case"],row["replicate"]) for row in rows]
            expected={(case,rep) for rep in range(plan["replicates"])}
        if set(keys)!=expected or len(keys)!=len(expected) or record["tasks"]!=len(keys):
            raise ValueError("incomplete or duplicate sampling/anchor tasks")
        if any(row["status"] not in ("ok","failed") for row in rows) or record["failed"]!=sum(row["status"]=="failed" for row in rows):
            raise ValueError("inconsistent failure accounting")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["plan","submit"])
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--profile-root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4))
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    root=bundle/"runs/production"
    plan=json.loads((root/"manifest.json").read_text())
    profile=json.loads((args.profile_root/"manifest.json").read_text())
    data=json.loads((args.profile_root/"summary.json").read_text())
    if plan!=json.loads(c.canonical(b.make_plan())) or profile!=json.loads(c.canonical(p.make_plan())):
        raise ValueError("pinned runtime/source differs")
    for module in (a,b,summary_module):
        if c.file_hash(bundle/"cluster_scripts"/Path(module.__file__).name)!=c.file_hash(module.__file__):
            raise ValueError("deployed analysis source differs from controller")
    allocation=resource_plan(plan,profile,data)
    allocation.update(profile_summary_sha256=c.file_hash(args.profile_root/"summary.json"),
                      submit_source_sha256=c.file_hash(__file__))
    resource_path=root/"analysis_resource_plan.json"
    if args.command=="plan":
        if resource_path.exists():
            raise ValueError("analysis resource plan already exists")
        c.atomic_json(resource_path,allocation)
        print(json.dumps(allocation))
        return
    if args.case is None or allocation!=json.loads(resource_path.read_text()):
        raise ValueError("case and unchanged resource plan required")
    case=args.case
    ledger=root/f"analysis_submission-{case}.json"
    if ledger.exists():
        raise ValueError("existing analysis submission; inspect existing job")
    check_completed_case(plan,case,json.loads((root/f"sample-{case}.json").read_text()),
                         json.loads((root/f"anchors-{case}.json").read_text()))
    if args.execute:
        sampling_job=json.loads((root/f"submission-{case}.json").read_text())["job_id"]
        result=subprocess.run(["qstat","-x","-f","-F","json",sampling_job],text=True,capture_output=True,check=True)
        state=json.loads(result.stdout)["Jobs"][sampling_job]
        if state["job_state"]!="F":
            raise ValueError("sampling job not yet terminal")
        if requested_nodes(own_active_jobs())+1>2:
            raise ValueError("two-node budget exceeded")
    resource=allocation["cases"][case]
    script=root/f"analyze-{case}.sh"
    script.write_text(f'''#!/bin/bash
#PBS -N m4q_tilebar{case}
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/analyze-{case}.out
#PBS -e {root}/analyze-{case}.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {bundle}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
# All 768 independent replicate/kernel/initialization groups are retained.
# The worker checks every input marker and payload hash before analysis.
venv/bin/python -m pytest tests/test_tile_bar_analysis.py tests/test_tile_summary.py -q
venv/bin/python cluster_scripts/tile_bar_analysis.py run --root runs/production --case {case} --workers 96
venv/bin/python cluster_scripts/tile_summary.py --root runs/production --case {case}
''',newline="\n")
    command=["qsub",str(script)]
    job="dry-run"
    if args.execute:
        job=subprocess.run(command,text=True,capture_output=True,check=True).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError(f"unexpected qsub response; inspect queue: {job}")
    record=dict(job_id=job,command=command,manifest=c.digest(plan),script_sha256=c.file_hash(script),
                analysis_manifest_sha256=c.file_hash(root/"analysis_manifest.json"),resource_plan_sha256=c.file_hash(resource_path),
                requested_nodes=1,max_nodes=2,**resource)
    c.atomic_json(ledger if args.execute else root/f"analysis_dry_run-{case}.json",record)
    print(json.dumps(record))


if __name__=="__main__":
    main()
