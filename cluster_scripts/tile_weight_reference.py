"""Fixed-budget independent weight-reference chunks; production allocation is external.

These primitives do not submit jobs or certify their input pilot audit. A future
production driver must validate the actual pilot evidence and native profile
before calling them. No pilot observations enter the reference counts.
"""
import itertools
import json
import math
from pathlib import Path
import re
import time
import traceback

import numpy as np
import calibration as c
import tile_study as t
import tile_weight_stratified as w


def make_plan(conditions,*,pilot_audit_digest,platform_profile_digest,chunk_size=4096):
    if type(chunk_size) is not int or not 1<=chunk_size<=4096 or not conditions:
        raise ValueError("bounded positive chunk size and conditions required")
    if any(not isinstance(value,str) or not re.fullmatch(r"[a-f0-9]{64}",value) for value in (pilot_audit_digest,platform_profile_digest)):
        raise ValueError("pilot and native profile digests required")
    seen=set()
    for condition in conditions:
        case,prior=condition["case"],condition["physical_decoder_prior"]
        if type(case) is not int or case not in range(4) or not 0<prior<1 or (case,prior) in seen:
            raise ValueError("invalid or duplicated code/prior condition")
        seen.add((case,prior))
        size,noise=t.CASES[case]
        n=2*size*size
        layers=condition["layers"]
        if not layers or any(type(row["w"]) is not int for row in layers) or [row["w"] for row in layers]!=list(range(len(layers))) or len(layers)>n+1:
            raise ValueError("contiguous complete weight grid required")
        for row in layers:
            if type(row["trials"]) is not int or row["trials"]<1 or row["mode"] not in ("enum","mc"):
                raise ValueError("positive fixed stratum budget and mode required")
            if row["mode"]=="enum" and row["trials"]!=w.class_size(n,row["w"],noise):
                raise ValueError("enumeration must include every pattern")
    return dict(schema=1,purpose="weight_reference_chunks",seed_stage=130,master_seed=t.MASTER,
                conditions=json.loads(c.canonical(conditions)),chunk_size=chunk_size,alpha=.001,
                pilot_audit_digest=pilot_audit_digest,platform_profile_digest=platform_profile_digest,
                decoder=t.SETTINGS,runtime=t.runtime(),driver_sha256=c.file_hash(__file__),
                strata_source_sha256=c.file_hash(w.__file__),
                warning="Fixed independent reference samples only. Allocation and native-platform validation are separate prerequisites. Missing or failed chunks never disappear from the planned budget. Partial estimates exclude the bounded tail.")


def tasks(plan,condition=None):
    for index,spec in enumerate(plan["conditions"]):
        if condition is not None and index!=condition:
            continue
        for layer in spec["layers"]:
            for chunk in range((layer["trials"]+plan["chunk_size"]-1)//plan["chunk_size"]):
                yield index,layer["w"],chunk


def chunk_spec(plan,task):
    index,weight,chunk=task
    if not 0<=index<len(plan["conditions"]):
        raise ValueError("unknown reference condition")
    condition=plan["conditions"][index]
    if not 0<=weight<len(condition["layers"]) or chunk<0:
        raise ValueError("unknown reference stratum/chunk")
    layer=condition["layers"][weight]
    start=chunk*plan["chunk_size"]
    stop=min(layer["trials"],start+plan["chunk_size"])
    if start>=stop:
        raise ValueError("chunk outside fixed trial range")
    case=condition["case"]
    size,noise=t.CASES[case]
    prior=condition["physical_decoder_prior"]
    return dict(task=list(task),case=case,n=2*size*size,noise=noise,physical_decoder_prior=prior,
                sector_prior=prior if noise=="bit" else 2*prior/3,w=weight,mode=layer["mode"],
                start=start,stop=stop,trials=stop-start,
                seed=t.seed((130,*task),0) if layer["mode"]=="mc" else None)


def raw_states(spec):
    if spec["mode"]=="enum":
        return np.stack(list(w.enum_patterns(spec["n"],spec["w"],spec["noise"],spec["start"],spec["stop"])))
    return w.draw_patterns(spec["n"],spec["w"],spec["noise"],spec["trials"],np.random.default_rng(spec["seed"]))


def run_chunk(args):
    root,plan,task=args
    identity=dict(manifest=c.digest(plan),task=list(task))
    path=Path(root)/"chunks"/c.task_id(task)
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    spec=chunk_spec(plan,task)
    started,cpu=time.perf_counter(),time.process_time()
    record=dict(spec,manifest=c.digest(plan),status="ok")
    arrays={}
    try:
        size,noise=t.CASES[spec["case"]]
        _,problem=t.build_problem(size,noise,spec["physical_decoder_prior"])
        states=raw_states(spec)
        failure=t.compact(problem,states)["sector"]!=0
        checked=min(16,len(states))
        mismatches=int(np.count_nonzero(failure[:checked]!=[problem.is_faulty(state) for state in states[:checked]]))
        if mismatches:
            raise ValueError("public/batch reference failure mismatch")
        arrays=dict(states=states,failure=failure)
        record.update(failures=int(failure.sum()),checked_public_states=checked,failure_mismatches=mismatches,
                      problem_hash=c.digest(problem.metadata()))
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(path,identity,arrays,record)
    return record


def aggregate_condition(plan,index,inputs):
    """Verify raw draws and counts; no independent failure-label re-decode here."""
    condition=plan["conditions"][index]
    size,noise=t.CASES[condition["case"]]
    code,problem=t.build_problem(size,noise,condition["physical_decoder_prior"])
    problem_hash=c.digest(problem.metadata())
    counts={layer["w"]:dict(layer,failures=0) for layer in condition["layers"]}
    failed=[]
    seeds=set()
    missing=object()
    available_trials=0
    chunks=0
    for task,item in itertools.zip_longest(tasks(plan,index),inputs,fillvalue=missing):
        if task is missing or item is missing:
            raise ValueError("missing or extra reference chunk")
        arrays,record=item
        spec=chunk_spec(plan,task)
        if record["manifest"]!=c.digest(plan) or any(record.get(key)!=value for key,value in spec.items()):
            raise ValueError("reference chunk metadata differs")
        if spec["seed"] is not None:
            if spec["seed"] in seeds:
                raise ValueError("reference seed collision")
            seeds.add(spec["seed"])
        chunks+=1
        if record["status"]=="failed":
            failed.append(list(task))
            continue
        if record["status"]!="ok" or record["problem_hash"]!=problem_hash or record["checked_public_states"]!=min(16,spec["trials"]) or record["failure_mismatches"]!=0:
            raise ValueError("reference model or failure-check metadata differs")
        if set(arrays)!={"states","failure"}:
            raise ValueError("unexpected raw reference payload set")
        states,mask=arrays["states"],arrays["failure"]
        if states.dtype!=np.uint8 or states.shape!=(spec["trials"],code.n) or mask.dtype!=np.bool_ or mask.shape!=(spec["trials"],):
            raise ValueError("invalid reference array shape or dtype")
        if np.any(states>(1 if noise=="bit" else 3)) or np.any(np.count_nonzero(states,axis=1)!=spec["w"]):
            raise ValueError("invalid reference weight or alphabet")
        if not np.array_equal(states,raw_states(spec)) or record["failures"]!=int(mask.sum()):
            raise ValueError("raw reference states/counts differ")
        if any(not math.isfinite(record[key]) or record[key]<0 for key in ("wall_seconds","cpu_seconds")):
            raise ValueError("invalid reference timing")
        counts[spec["w"]]["failures"]+=record["failures"]
        available_trials+=spec["trials"]
    reference=None if failed else w.synthesize(code.n,noise,condition["physical_decoder_prior"],list(counts.values()),plan["alpha"])
    return dict(condition=index,case=condition["case"],physical_decoder_prior=condition["physical_decoder_prior"],
                chunks=chunks,planned_trials=sum(row["trials"] for row in condition["layers"]),
                available_trials=available_trials,failed_chunks=failed,available=not failed,reference=reference,
                warning="All fixed chunks required. Raw draws/enumeration ranks and recorded counts audited; failure labels are not independently re-decoded here. Per-condition simultaneous interval, not simultaneous across all conditions. Unobserved tail stays explicit.")
