"""Extrapolate audited pilot resources and submit a fixed weight reference via qsub."""
import argparse
import heapq
import json
import math
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_weight_reference as r
import tile_weight_reference_driver as d
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def candidates(pilot,audit,spec):
    rows=[row for row in audit["strata"] if row["case"]==spec["case"]
          and row["physical_decoder_prior"]==spec["physical_decoder_prior"]]
    exact=[row for row in rows if row["w"]==spec["w"]]
    return exact or [row for row in rows if row["w"]>0]


def chunk_cost(plan,pilot,audit,task):
    spec=r.chunk_spec(plan,task)
    return max(row["task_wall_seconds_max"]*max(1,spec["trials"]/(1 if row["w"]==0 else pilot["samples"]))
               for row in candidates(pilot,audit,spec))


def resource_plan(context,pilot,audit):
    d.validate_pilot(pilot,audit)
    if (context["purpose"]!="weight_reference_production"
        or context["input_digests"]["pilot_manifest"]!=c.digest(pilot)
        or context["input_digests"]["pilot_audit"]!=c.digest(audit)
        or context["reference"]["pilot_audit_digest"]!=c.digest(audit)):
        raise ValueError("context and measured pilot differ")
    plan=context["reference"]
    tasks=list(r.tasks(plan))
    costs=[(chunk_cost(plan,pilot,audit,task),task) for task in tasks]
    loads=[0.]*96
    condition_cost=[0.]*len(plan["conditions"])
    missing=set()
    raw_bytes=0
    for cost,task in sorted(costs,reverse=True):
        if not math.isfinite(cost) or cost<=0:
            raise ValueError("finite positive estimated task cost required")
        heapq.heapreplace(loads,loads[0]+cost)
        condition_cost[task[0]]+=cost
        spec=r.chunk_spec(plan,task)
        raw_bytes=max(raw_bytes,spec["trials"]*(spec["n"]+1))
        if spec["w"] not in pilot["weights"]:
            missing.add((task[0],spec["w"]))
    sampling=max(loads)
    aggregation=max(condition_cost)
    total=sampling+aggregation
    if not math.isfinite(total):
        raise ValueError("nonfinite resource extrapolation")
    seconds=1800*math.ceil((2*total+600)/1800)
    peak=max(row["peak_rss_mb_max"] for row in audit["strata"])
    memory=max(32,math.ceil(1.5*96*(peak+4*raw_bytes/2**20)/1024+8))
    if seconds>86400 or memory>340:
        raise ValueError("measured extrapolation exceeds limits; repartition or redesign before submission")
    return dict(cpus=96,memory_gb=memory,wall_seconds=seconds,
                walltime=f"{seconds//3600:02}:{seconds%3600//60:02}:00",requested_nodes=1,max_nodes=2,
                manifest=c.digest(context),pilot_audit_digest=c.digest(audit),tasks=len(tasks),
                planned_trials=context["planned_trials"],predicted_sampling_seconds=sampling,
                aggregation_allowance_seconds=aggregation,observed_peak_worker_rss_mb=peak,
                max_chunk_raw_bytes=raw_bytes,unmeasured_layers=[list(item) for item in sorted(missing)],
                warning="Pilot-based resource extrapolation, not a measured aggregation runtime, completion bound or precision guarantee. Unmeasured positive weights use the slowest positive measured layer at the same code/prior. Native preflight runs on the compute node before workers.")


def read_plan(root):
    values=[json.loads((root/(key+".json")).read_text()) for key in d.INPUTS]
    context=d.make_context(*values)
    if json.loads((root/"manifest.json").read_text())!=json.loads(c.canonical(context)):
        raise ValueError("production inputs, source, runtime or allocation changed")
    return context,values


def submit(bundle,root,*,execute,controller_query=live_controllers,
           active_query=own_active_jobs,runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    intent,ledger=root/"submission_intent.json",root/"submission.json"
    if intent.exists() or ledger.exists():
        raise ValueError("existing submission/intent; inspect the job and never retry automatically")
    context,values=read_plan(root)
    resource=resource_plan(context,values[1],values[2])
    if any(char.isspace() for path in (bundle,root) for char in str(path)):
        raise ValueError("PBS deployment paths must not contain whitespace")
    if execute:
        if controller_query():
            raise ValueError("tile coordinator is running; do not compete for submission slots")
        if requested_nodes(active_query())+1>2:
            raise ValueError("two-node budget exceeded")
    path=root/"weight_reference.sh"
    command_line=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_weight_reference_driver.py"),
                             "run","--root",str(root),"--workers","96"])
    path.write_text(f'''#!/bin/bash
#PBS -N m4q_weightref
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/weight_reference.out
#PBS -e {root}/weight_reference.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{command_line}
''',newline="\n")
    command=["qsub",str(path)]
    record=dict(command=command,manifest=c.digest(context),script_sha256=c.file_hash(path),
                resource=resource,submit_source_sha256=c.file_hash(__file__))
    job="dry-run"
    if execute:
        with intent.open("xb") as stream:
            stream.write(c.canonical(record)+b"\n")
        job=runner(command,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unrecognized qsub response; intent retained, inspect queue before further action")
    record["job_id"]=job
    c.atomic_json(ledger if execute else root/"dry_run.json",record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,execute=args.execute)))


if __name__=="__main__":
    main()
