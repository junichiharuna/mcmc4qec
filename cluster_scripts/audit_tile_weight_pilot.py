"""Audit raw weight-pilot states and report allocation inputs, never a P_L reference."""
import argparse
import itertools
import json
import math
from pathlib import Path
from statistics import fmean

import numpy as np

import calibration as c
import tile_study as t
import tile_weight_stratified as w


def expected_tasks(plan):
    if plan["purpose"]!="weight_stratified_pilot" or plan["schema"]!=1:
        raise ValueError("unsupported pilot manifest")
    if plan["decoder"]!=t.SETTINGS:
        raise ValueError("fixed decoder settings differ")
    if not plan["cases"] or len(plan["cases"])!=len(plan["priors"]) or plan["replicates"]<1 or plan["samples"]<1:
        raise ValueError("invalid pilot dimensions")
    if not plan["weights"] or len(set(plan["weights"]))!=len(plan["weights"]):
        raise ValueError("empty or repeated weights")
    for case in range(len(plan["cases"])):
        priors=plan["priors"][case]
        if not priors or len(set(priors))!=len(priors) or any(not 0<p<1 for p in priors):
            raise ValueError("invalid prior grid")
        yield from ((case,prior,weight,rep) for prior,weight,rep in itertools.product(
            range(len(priors)),range(len(plan["weights"])),range(plan["replicates"])))


def load_inputs(root,plan):
    """Read one checked artifact at a time in canonical manifest order."""
    for task in expected_tasks(plan):
        value=c.load_artifact(Path(root)/"layers"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
        if value is None:
            raise ValueError(f"missing or corrupt pilot artifact: {task}")
        yield value


def aggregate(plan,inputs,models):
    """Retain failures; re-create all successful draws without repeating decoding.

Inputs must follow manifest order. Only one stratum's duplicate-state table is
retained, keeping audit memory independent of the number of priors/strata.
"""
    rows=[]
    failed=[]
    seeds=set()
    group=None
    current=None
    seen={}
    task_count=0

    def finish(row):
        complete=row["success_replicates"]==row["expected_replicates"]
        trials=row["trials_available"]
        failures=row["failures_available"]
        rate=failures/trials if trials else None
        times=row.pop("times")
        memory=row.pop("memory")
        row.update(allocation_ready=complete,failure_rate=rate if complete else None,
                   failure_rate_available_only=rate,
                   exploratory_cp95=list(w.clopper_pearson(failures,trials,.05)) if complete else None,
                   task_wall_seconds_mean=fmean(times),
                   task_wall_seconds_max=max(times),
                   resource_profile_complete=all(value is not None for value in memory),
                   peak_rss_mb_max=max(memory) if all(value is not None for value in memory) else None)
        # This includes Problem construction and the public failure checks.
        row["observed_task_seconds_per_trial"]=row.pop("success_seconds")/trials if trials else None
        rows.append(row)

    missing=object()
    for task,item in itertools.zip_longest(expected_tasks(plan),inputs,fillvalue=missing):
        if task is missing or item is missing:
            raise ValueError("missing or extra pilot task")
        arrays,record=item
        if record["task"]!=list(task):
            raise ValueError("duplicate, out-of-order or wrong pilot task")
        case,prior_index,weight_index,_=task
        n,problem_hash=models[(case,prior_index)]
        noise=plan["cases"][case][1]
        prior=plan["priors"][case][prior_index]
        weight=plan["weights"][weight_index]
        if group!=task[:3]:
            if current is not None:
                finish(current)
            group=task[:3]
            seen={}
            current=dict(case=case,prior_index=prior_index,physical_decoder_prior=prior,
                         sector_prior=prior if noise=="bit" else 2*prior/3,n=n,noise=noise,w=weight,
                         pattern_count=w.class_size(n,weight,noise),expected_replicates=plan["replicates"],
                         success_replicates=0,trials_available=0,failures_available=0,duplicate_states=0,
                         times=[],memory=[],success_seconds=0.)
        duration,memory=record["wall_seconds"],record["peak_rss_mb"]
        if not math.isfinite(duration) or duration<0 or (memory is not None and (not math.isfinite(memory) or memory<0)):
            raise ValueError("invalid pilot resource timing")
        current["times"].append(duration)
        current["memory"].append(memory)
        task_count+=1
        if record["status"]=="failed":
            failed.append(record)
            continue
        if record["status"]!="ok":
            raise ValueError("unknown task status")
        seed=t.seed((110,*task),0)
        trials=1 if weight==0 else plan["samples"]
        expected=dict(case=case,n=n,noise=noise,physical_decoder_prior=prior,
                      sector_prior=prior if noise=="bit" else 2*prior/3,w=weight,seed=seed,
                      trials=trials,failure_mismatches=0,checked_public_states=min(16,trials),
                      problem_hash=problem_hash)
        if any(record.get(key)!=value for key,value in expected.items()):
            raise ValueError(f"pilot metadata differs: {task}")
        if seed in seeds:
            raise ValueError("pilot seed collision")
        seeds.add(seed)
        states,mask=arrays["states"],arrays["failure"]
        if states.dtype!=np.uint8 or states.shape!=(trials,n) or mask.dtype!=np.bool_ or mask.shape!=(trials,):
            raise ValueError("wrong raw pilot shape or type")
        if np.any(states>(1 if noise=="bit" else 3)) or np.any(np.count_nonzero(states,axis=1)!=weight):
            raise ValueError("wrong pilot alphabet or weight")
        if record["failures"]!=int(mask.sum()):
            raise ValueError("pilot raw failure count differs")
        regenerated=w.draw_patterns(n,weight,noise,trials,np.random.default_rng(seed))
        if not np.array_equal(regenerated,states):
            raise ValueError("pilot states differ from declared seed")
        for state,failure in zip(states,mask):
            key=state.tobytes()
            value=bool(failure)
            if key in seen:
                current["duplicate_states"]+=1
                if seen[key]!=value:
                    raise ValueError("conflicting failure labels for identical pilot state")
            else:
                seen[key]=value
        current["success_replicates"]+=1
        current["trials_available"]+=trials
        current["failures_available"]+=int(mask.sum())
        current["success_seconds"]+=duration
    if current is not None:
        finish(current)
    return dict(manifest=c.digest(plan),purpose="weight_pilot_allocation_audit",expected_tasks=task_count,
                allocation_ready=not failed,failed_tasks=failed,
                resource_profile_complete=all(row["resource_profile_complete"] for row in rows),
                trials=sum(row["trials_available"] for row in rows),strata=rows,
                raw_draws_regenerated=True,successful_metadata_verified=True,
                warning="Pilot only: incomplete weight grid, not a logical-error reference. Per-layer CP95 intervals are exploratory, not simultaneous. Failure labels are internally audited, not independently decoded. Task timing includes setup and public checks. Failed tasks are retained and prohibit allocation-ready status. Missing RSS is explicit and cannot size job memory.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    plan=json.loads((args.root/"manifest.json").read_text())
    models={}
    for case,(size,noise) in enumerate(plan["cases"]):
        for prior_index,prior in enumerate(plan["priors"][case]):
            code,problem=t.build_problem(size,noise,prior)
            models[(case,prior_index)]=(code.n,c.digest(problem.metadata()))
    result=aggregate(plan,load_inputs(args.root,plan),models)
    result.update(source_sha256=c.file_hash(__file__),strata_source_sha256=c.file_hash(w.__file__),
                  numpy_version=np.__version__)
    c.atomic_json(args.output,result)
    print(json.dumps({key:result[key] for key in ("manifest","expected_tasks","trials","allocation_ready")}))
    if not result["allocation_ready"]:
        raise RuntimeError("failed pilot tasks retained; allocation is not ready")


if __name__=="__main__":
    main()
