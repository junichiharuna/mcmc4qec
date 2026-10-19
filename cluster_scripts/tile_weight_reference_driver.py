"""Validate audited pilot inputs, freeze allocations, and run reference chunks in PBS."""
import argparse
import itertools
import json
import math
import os
from pathlib import Path
import socket
import time

import calibration as c
import tile_weight_pilot as p
import audit_tile_weight_pilot as pilot_audit
import tile_weight_reference as r
import tile_weight_stratified as w
import audit_tile_traces as trace_audit
import probe_tile_decoder_platform as native_probe


INPUTS=("allocation","pilot_manifest","pilot_audit","platform_profile","platform_fixture")


def validate_pilot(plan,audit):
    if c.canonical(plan)!=c.canonical(p.make_plan()):
        raise ValueError("pilot plan/source/runtime differs")
    if (audit["manifest"]!=c.digest(plan) or audit["purpose"]!="weight_pilot_allocation_audit"
        or audit["expected_tasks"]!=len(list(p.tasks(plan))) or audit["failed_tasks"]
        or any(audit[key] is not True for key in ("allocation_ready","resource_profile_complete","raw_draws_regenerated","successful_metadata_verified"))
        or audit["source_sha256"]!=c.file_hash(pilot_audit.__file__)
        or audit["strata_source_sha256"]!=c.file_hash(w.__file__)):
        raise ValueError("complete successful pinned pilot audit required")
    expected={(case,prior_index,weight) for case in range(len(plan["cases"]))
              for prior_index in range(len(plan["priors"][case])) for weight in plan["weights"]}
    keys=[(row["case"],row["prior_index"],row["w"]) for row in audit["strata"]]
    if set(keys)!=expected or len(keys)!=len(expected):
        raise ValueError("missing, duplicate or wrong pilot stratum")
    trials_total=0
    for row in audit["strata"]:
        case,prior_index,weight=row["case"],row["prior_index"],row["w"]
        size,noise=plan["cases"][case]
        prior=plan["priors"][case][prior_index]
        trials=plan["replicates"]*(1 if weight==0 else plan["samples"])
        expected_values=dict(n=2*size*size,noise=noise,physical_decoder_prior=prior,
            sector_prior=prior if noise=="bit" else 2*prior/3,pattern_count=w.class_size(2*size*size,weight,noise),
            expected_replicates=plan["replicates"],success_replicates=plan["replicates"],trials_available=trials,
            allocation_ready=True,resource_profile_complete=True)
        if any(row.get(key)!=value for key,value in expected_values.items()):
            raise ValueError("pilot layer identity or budget differs")
        failures=row["failures_available"]
        if type(failures) is not int or not 0<=failures<=trials or row["failure_rate"]!=failures/trials:
            raise ValueError("pilot counts and rate disagree")
        for key in ("task_wall_seconds_mean","task_wall_seconds_max","peak_rss_mb_max","observed_task_seconds_per_trial"):
            value=row[key]
            if value is None or not math.isfinite(value) or value<=0:
                raise ValueError("positive measured pilot timing and memory required")
        if row["task_wall_seconds_mean"]>row["task_wall_seconds_max"]:
            raise ValueError("pilot mean exceeds maximum duration")
        trials_total+=trials
    if audit["trials"]!=trials_total:
        raise ValueError("pilot total trial count differs")


def make_context(allocation,pilot,audit,profile,fixture):
    validate_pilot(pilot,audit)
    if allocation["pilot_audit_digest"]!=c.digest(audit) or allocation["platform_profile_digest"]!=c.digest(profile):
        raise ValueError("allocation points to different audit or native profile")
    if profile["fixture"]!=c.digest(fixture) or not profile["native_ldpc_sha256"]:
        raise ValueError("native profile fixture or binary provenance missing")
    expected={(case,prior) for case,priors in enumerate(pilot["priors"]) for prior in priors}
    pairs=[(row["case"],row["physical_decoder_prior"]) for row in allocation["conditions"]]
    if set(pairs)!=expected or len(pairs)!=len(expected):
        raise ValueError("all sixteen fixed pilot code/prior conditions required")
    reference=r.make_plan(allocation["conditions"],pilot_audit_digest=c.digest(audit),
                          platform_profile_digest=c.digest(profile),chunk_size=allocation["chunk_size"])
    return dict(schema=1,purpose="weight_reference_production",reference=reference,
                input_digests={key:c.digest(value) for key,value in zip(INPUTS,(allocation,pilot,audit,profile,fixture))},
                driver_sha256=c.file_hash(__file__),
                planned_trials=sum(layer["trials"] for condition in reference["conditions"] for layer in condition["layers"]),
                warning="Pilot evidence validates allocation inputs, not achieved precision. Pilot samples are excluded. Native preflight is mandatory at execution. Per-condition CP/Bonferroni bounds retain omitted mass; no full-cohort precision claim without completed references.")


def aggregate_from_root(args):
    root,plan,index=args
    def inputs():
        for task in r.tasks(plan,index):
            value=c.load_artifact(Path(root)/"chunks"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
            if value is None:
                raise ValueError("missing reference chunk is not a recorded failure")
            yield value
    result=r.aggregate_condition(plan,index,inputs())
    c.atomic_json(Path(root)/f"condition-{index}.json",result)
    return result


def estimated_task_cost(plan,pilot,audit,task):
    spec=r.chunk_spec(plan,task)
    candidates=[row for row in audit["strata"] if row["case"]==spec["case"] and row["physical_decoder_prior"]==spec["physical_decoder_prior"]]
    exact=[row for row in candidates if row["w"]==spec["w"]]
    return spec["trials"]*max(row["observed_task_seconds_per_trial"] for row in (exact or candidates))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run"))
    parser.add_argument("--root",type=Path,required=True)
    for key in INPUTS:
        parser.add_argument("--"+key.replace("_","-"),type=Path)
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if args.command=="run" and (not os.environ.get("PBS_JOBID") or args.workers!=96 or
        any(os.environ.get(key)!="1" for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"))):
        raise ValueError("reference execution requires qsub, 96 workers and single-thread environment")
    if args.command=="plan":
        if any(getattr(args,key) is None for key in INPUTS) or (args.root.exists() and any(args.root.iterdir())):
            raise ValueError("all fixed inputs and a new empty output root required")
        values=[json.loads(getattr(args,key).read_text()) for key in INPUTS]
    else:
        values=[json.loads((args.root/(key+".json")).read_text()) for key in INPUTS]
    allocation,pilot,audit,profile,fixture=values
    context=make_context(*values)
    if args.command=="run" and json.loads((args.root/"manifest.json").read_text())!=json.loads(c.canonical(context)):
        raise ValueError("production source, runtime, inputs or allocation changed")
    preflight_start=time.perf_counter()
    actual_profile=native_probe.probe(fixture)
    trace_audit.validate_platform(profile,actual_profile)
    evidence=dict(manifest=c.digest(context),profile=actual_profile,hostname=socket.gethostname(),
                  pbs_job_id=os.environ.get("PBS_JOBID"),wall_seconds=time.perf_counter()-preflight_start)
    if args.command=="plan":
        args.root.mkdir(parents=True,exist_ok=True)
        for key,value in zip(INPUTS,values):
            c.atomic_json(args.root/(key+".json"),value)
        c.atomic_json(args.root/"manifest.json",context)
        c.atomic_json(args.root/"native_preflight_plan.json",evidence)
        print(json.dumps(dict(manifest=c.digest(context),planned_trials=context["planned_trials"],conditions=16)))
        return
    evidence_path=args.root/"native_preflight_run.json"
    c.atomic_json(evidence_path,evidence)
    evidence_hash=c.file_hash(evidence_path)
    plan=context["reference"]
    jobs=sorted(r.tasks(plan),key=lambda task:(-estimated_task_cost(plan,pilot,audit,task),task))
    started=time.perf_counter()
    records=c.parallel_map(r.run_chunk,[(str(args.root),plan,task) for task in jobs],args.workers)
    if sorted(tuple(row["task"]) for row in records)!=list(r.tasks(plan)):
        raise ValueError("missing or duplicated completed reference task")
    sampling_wall=time.perf_counter()-started
    c.atomic_json(args.root/"chunks_summary.json",dict(manifest=c.digest(context),tasks=len(records),
        native_preflight_sha256=evidence_hash,
        failed=sum(row["status"]=="failed" for row in records),wall_seconds=sampling_wall,records=records))
    analysis_start=time.perf_counter()
    summaries=c.parallel_map(aggregate_from_root,[(str(args.root),plan,index) for index in range(len(plan["conditions"]))],args.workers)
    result=dict(manifest=c.digest(context),conditions=len(summaries),unavailable=sum(not row["available"] for row in summaries),
                native_preflight_sha256=evidence_hash,
                sampling_wall_seconds=sampling_wall,aggregation_wall_seconds=time.perf_counter()-analysis_start,
                phase_wall_seconds=time.perf_counter()-started,records=summaries,warning=context["warning"])
    c.atomic_json(args.root/"summary.json",result)
    print(json.dumps({key:value for key,value in result.items() if key!="records"}))
    if result["unavailable"]:
        raise RuntimeError("failed reference chunks retained; unavailable conditions remain recorded")


if __name__=="__main__":
    main()
