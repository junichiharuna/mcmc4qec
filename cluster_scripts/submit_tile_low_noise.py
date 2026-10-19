"""One-shot PBS submission for one low-noise case/target, within two nodes."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_low_noise_study as m
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def read_plan(root):
    root=Path(root)
    plan=json.loads((root/"manifest.json").read_text())
    expected=m.make_plan(plan["case"],plan["target_index"],capacity=plan["purpose"]=="low_noise_capacity")
    if c.canonical(plan)!=c.canonical(expected):
        raise ValueError("fixed low-noise manifest/source/runtime differ")
    for key,digest in plan["native_input_digests"].items():
        if c.digest(json.loads((root/(key+".json")).read_text()))!=digest:
            raise ValueError("native input changed")
    return plan


def capacity_resources():
    return dict(cpus=96,memory_gb=340,wall_seconds=86400,walltime="24:00:00",requested_nodes=1,max_nodes=2,
                stage="capacity",warning="Initial resource ceiling, not measured consumption or a completion prediction.")


def resource_plan(plan, cap, measurements):
    if (plan["purpose"],cap["purpose"],plan["replicates"],cap["replicates"])!=("low_noise_production","low_noise_capacity",192,2):
        raise ValueError("separate fixed capacity and production stages required")
    differences={key for key in set(plan)|set(cap) if plan.get(key)!=cap.get(key)}
    if (differences!={"purpose","replicates","stages"}
            or cap["stages"]!={"sample":150,"anchors":154,"analysis":155}
            or plan["stages"]!={"sample":151,"anchors":152,"analysis":153}):
        raise ValueError("capacity and production conditions/source differ")
    predicted={}
    peak=0.
    for phase in ("sample","anchors"):
        data=measurements[phase]
        expected=sorted(m.tasks(cap,phase))
        rows=data["records"]
        if (data["manifest"]!=c.digest(cap) or data["phase"]!=phase or data["failed"]
                or data["tasks"]!=len(expected) or [tuple(row["task"]) for row in rows]!=expected
                or not data.get("native_preflight_sha256")):
            raise ValueError("complete successful capacity phase required")
        for row in rows:
            if row["status"]!="ok":
                raise ValueError("failed capacity cannot be extrapolated")
            for key in ("wall_seconds","cpu_seconds","peak_rss_mb"):
                value=row[key]
                if value is None or not math.isfinite(value) or value<=0:
                    raise ValueError("positive measured duration and Linux RSS required")
            peak=max(peak,row["peak_rss_mb"])
        elapsed=data["phase_wall_seconds"]
        if not math.isfinite(elapsed) or elapsed<=0:
            raise ValueError("positive phase duration required")
        count=sum(1 for _ in m.tasks(plan,phase))
        maxima={}
        for row in rows:
            _,_,kernel,initial,_,rung,_=row["task"]
            key=(kernel,initial,rung)
            maxima[key]=max(maxima.get(key,0.),row["wall_seconds"])
        copies=plan["replicates"]*(plan["condition"]["chains"] if phase=="sample" else 1)
        predicted[phase]=max(elapsed*count/len(expected),sum(maxima.values())*copies/96)
    seconds=1800*math.ceil((2*sum(predicted.values())+600)/1800)
    memory=max(32,math.ceil(1.5*96*peak/1024+8))
    if seconds>86400 or memory>340:
        raise ValueError("request exceeds limits; partition fixed tasks before submission")
    return dict(cpus=96,memory_gb=memory,wall_seconds=seconds,walltime=f"{seconds//3600:02}:{seconds%3600//60:02}:00",
                requested_nodes=1,max_nodes=2,stage="production",predicted_phase_seconds=predicted,
                observed_peak_worker_rss_mb=peak,manifest=c.digest(plan),capacity_manifest=c.digest(cap),
                capacity_summary_digests={key:c.digest(value) for key,value in measurements.items()},
                warning="Resource extrapolation only; no accuracy or completion guarantee. Full numerical trace audit is separate.")


def measured_capacity(root, plan):
    root=Path(root)
    cap=read_plan(root)
    measurements={phase:json.loads((root/f"{phase}-summary.json").read_text()) for phase in ("sample","anchors")}
    resource=resource_plan(plan,cap,measurements)
    spec=cap["condition"]
    _,problem=m.t.build_problem(spec["size"],spec["noise"],spec["target"])
    problem_hash=c.digest(problem.metadata())
    execution=None
    for phase,data in measurements.items():
        evidence_path=root/f"preflight-{phase}"/"native_preflight.json"
        if c.file_hash(evidence_path)!=data["native_preflight_sha256"]:
            raise ValueError("capacity native evidence changed")
        evidence=json.loads(evidence_path.read_text())
        intent=json.loads((root/f"{phase}-execution-intent.json").read_text())
        if (evidence["manifest"]!=c.digest(cap) or not evidence["pbs_job_id"] or not evidence["hostname"]
                or intent["phase"]!=phase or any(intent[key]!=evidence[key] for key in ("manifest","pbs_job_id","hostname"))):
            raise ValueError("capacity compute execution binding differs")
        current=(evidence["pbs_job_id"],evidence["hostname"])
        if execution is not None and current!=execution:
            raise ValueError("capacity phases must share their submitted job")
        execution=current
        m.native.trace_audit.validate_platform(json.loads((root/"platform_profile.json").read_text()),evidence["profile"])
        for row in data["records"]:
            task=tuple(row["task"])
            base=root/("traces" if phase=="sample" else "anchors")/c.task_id(task)
            marker=base.with_suffix(".done.json")
            if not marker.exists() or set(json.loads(marker.read_text())["sha256"])!={".json",".npz"}:
                raise ValueError("complete capacity artifact marker required")
            _,record=c.load_artifact(base,dict(manifest=c.digest(cap),task=list(task)))
            reduced={key:record[key] for key in row} if phase=="sample" else record
            if c.canonical(reduced)!=c.canonical(row):
                raise ValueError("capacity raw task and summary differ")
            seed=m.task_seed(cap,task,phase,1 if phase=="sample" else 0)
            p=spec["rungs"][task[5] if phase=="sample" else 0]
            meta=record["metadata"]
            if (record["stage"]!=cap["stages"][phase] or record["physical_p"]!=p
                    or record["decoder_prior"]!=spec["target"] or record["problem_hash"]!=problem_hash
                    or meta["sampling_p"]!=p or meta["rng"]["entropy"]!=seed
                    or c.digest({key:meta[key] for key in ("model","noise","decoder","failure")})!=problem_hash):
                raise ValueError("capacity fixed decoder, probability or actual RNG metadata differs")
            if phase=="sample":
                cfg=meta["config"]
                if (record["sample_seed"]!=seed or record["init_seed"]!=m.task_seed(cap,task,phase,0)
                        or record["checked_saved_states"]!=spec["steps"]
                        or record["initialization"]!=cap["initializations"][task[3]]
                        or record["config"]!=cfg or cfg["samples"]!=spec["steps"] or cfg["burn_in"]!=0
                        or cfg["kernels"]!=cap["kernels"][list(cap["kernels"])[task[2]]]):
                    raise ValueError("capacity sampling configuration differs")
            elif (record["seed"]!=seed or record["trials"]!=cap["anchor_trials"]
                    or meta["config"]["trials"]!=cap["anchor_trials"]):
                raise ValueError("capacity anchor budget differs")
    return resource


def require_fresh(root):
    names=("submission-intent.json","submission.json","sample-execution-intent.json","anchors-execution-intent.json",
           "sample-summary.json","anchors-summary.json","traces","anchors")
    if any((root/name).exists() for name in names):
        raise ValueError("existing intent or output; inspect job, never retry automatically")


def submit(bundle, root, *, capacity_root=None, execute=False, controller_query=live_controllers,
           active_query=own_active_jobs, runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    require_fresh(root)
    plan=read_plan(root)
    if plan["purpose"]=="low_noise_capacity":
        resource=capacity_resources()
    else:
        if capacity_root is None:
            raise ValueError("complete measured capacity required")
        resource=measured_capacity(capacity_root,plan)
    if any(char.isspace() for path in (root,bundle) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    commands=[shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_low_noise_study.py"),
                          phase,"--root",str(root),"--workers","96"]) for phase in ("anchors","sample")]
    script=f'''#!/bin/bash
#PBS -N m4q_tilelow
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/low-noise.out
#PBS -e {root}/low-noise.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{commands[0]}
{commands[1]}
'''
    path=root/"low-noise.sh"
    if path.exists():
        if path.read_text()!=script:
            raise ValueError("existing submission script differs; preserve evidence")
    else:
        with path.open("x",newline="\n") as stream:stream.write(script)
    command=["qsub",str(path)]
    record=dict(command=command,manifest=c.digest(plan),resource=resource,script_sha256=c.file_hash(path),
                submit_source_sha256=c.file_hash(__file__))
    if not execute:
        c.atomic_json(root/"dry_run.json",dict(record,job_id="dry-run"))
        return dict(record,job_id="dry-run")
    lock=bundle.parent/"tile-low-noise-submission.lock"
    with lock.open("xb") as stream:
        stream.write(c.canonical(dict(root=str(root),pid=os.getpid()))+b"\n")
    uncertain=False
    try:
        require_fresh(root)
        if controller_query():
            raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query())+1>2:
            raise ValueError("two-node budget exceeded")
        if c.digest(read_plan(root))!=record["manifest"] or c.file_hash(path)!=record["script_sha256"]:
            raise ValueError("manifest or script changed before submission")
        with (root/"submission-intent.json").open("xb") as stream:
            stream.write(c.canonical(record)+b"\n")
        uncertain=True
        job=runner(command,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unrecognized qsub response; intent and lock retained, inspect queue")
        record["job_id"]=job
        c.atomic_json(root/"submission.json",record)
        uncertain=False
        return record
    finally:
        if not uncertain:
            lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--capacity-root",type=Path)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,capacity_root=args.capacity_root,execute=args.execute)))


if __name__=="__main__":main()
