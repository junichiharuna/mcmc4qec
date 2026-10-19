"""Fixed-cohort tile traces and independent anchors; no default changes."""
from dataclasses import asdict
import argparse
import itertools
import json
import math
from pathlib import Path
import time
import traceback

import numpy as np
import mcmc4qec as qec
import calibration as c
import tile_study as t


def runtime():
    return dict(**t.runtime(), bar_sampler_sha256=c.file_hash(__file__))


def make_plan(*, capacity=False):
    cases=[]
    for case,(size,noise) in enumerate(t.CASES):
        target=.03 if size==6 else .05
        coarse=[.1,.07,.05,.03] if target==.03 else [.1,.07,.05]
        fine=[.1,.085,.07,.06,.05,.04,.03] if target==.03 else [.1,.085,.07,.06,.05]
        cases.append(dict(size=size,noise=noise,target=target,coarse=coarse,rungs=fine,
                          chains=16 if case==0 else 8,steps=66000 if case==0 else 18000,
                          windows=[600,6000,60000 if case==0 else 12000]))
    return dict(schema=1,purpose="capacity" if capacity else "calibration",master_seed=t.MASTER,
                cases=cases,replicates=24 if capacity else 192,
                initializations=["rejection","logical"],kernels={k:asdict(v) for k,v in t.KERNELS.items()},
                decoder=t.SETTINGS,burns=[600,6000],chain_counts=[4,"maximum"],
                blocks=[32,128,1024],bootstrap_replicates=1000,anchor_trials=16384,
                max_initial_attempts=20000,cache_cap=200000,runtime=runtime(),
                warning="All steps retained. Fixed decoder per target. Diagnostics are not convergence proofs.")


def tasks(plan,case_id=None):
    for case,spec in enumerate(plan["cases"]):
        if case_id is not None and case!=case_id:
            continue
        for kernel,initialization,rep in itertools.product(range(2),range(2),range(plan["replicates"])):
            if plan["purpose"]=="capacity":
                yield case,kernel,initialization,rep,0 if rep%2==0 else len(spec["rungs"])-1,rep%spec["chains"]
            else:
                for rung,chain in itertools.product(range(len(spec["rungs"])),range(spec["chains"])):
                    yield case,kernel,initialization,rep,rung,chain


def task_seed(plan,task,purpose):
    return t.seed((99 if plan["purpose"]=="capacity" else 31,*task),purpose)


def sample_task(args):
    root,plan,task=args
    path=Path(root)/"traces"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task))
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return dict(cached[1],resumed=True)
    started,cpu=time.perf_counter(),time.process_time()
    arrays={}
    record=dict(task=list(task),status="ok")
    try:
        case,kernel_index,init_index,rep,rung,chain=task
        spec=plan["cases"][case]
        code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
        p=spec["rungs"][rung]
        mode=plan["initializations"][init_index]
        name=list(plan["kernels"])[kernel_index]
        init_seed=task_seed(plan,task,0)
        sample_seed=task_seed(plan,task,1)
        init_start=time.perf_counter()
        initial,attempts=t.initial_state(code,problem,p,spec["noise"],mode,rep*spec["chains"]+chain,
                                         np.random.default_rng(init_seed),plan["max_initial_attempts"])
        init_seconds=time.perf_counter()-init_start
        sample_start=time.perf_counter()
        result=qec.sample_faulty(problem,p,config=qec.SamplingConfig(samples=spec["steps"],burn_in=0,
                  kernels=qec.KernelConfig(**plan["kernels"][name]),cache_cap=plan["cache_cap"],cache_policy="lru"),
                  initial_state=initial,seed=sample_seed)
        sample_seconds=time.perf_counter()-sample_start
        states=result.states[0]
        compact_start=time.perf_counter()
        comp=t.compact(problem,states)
        if np.any(comp["sector"]==0):
            raise ValueError("independent re-decode found a successful saved state")
        arrays={k:v for k,v in comp.items() if k!="logical"}
        indices=np.unique(np.r_[np.arange(0,len(states),1000),len(states)-1])
        arrays.update(checkpoint_indices=indices,checkpoints=states[indices],initial=initial,final=states[-1])
        record.update(init_seed=init_seed,sample_seed=sample_seed,initial_attempts=attempts,
                      initial_seconds=init_seconds,sampling_seconds=sample_seconds,
                      compact_seconds=time.perf_counter()-compact_start,checked_saved_states=len(states),
                      problem_hash=c.digest(problem.metadata()),config=result.metadata["config"],
                      acceptance=result.acceptance,diagnostics=result.diagnostics,warnings=result.warnings)
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(path,identity,arrays,record)
    return record


def sample_summary(args):
    r=sample_task(args)
    return {k:r[k] for k in ("task","status","wall_seconds","cpu_seconds","peak_rss_mb")}


def anchor_task(args):
    root,plan,case,rep=args
    path=Path(root)/"anchors"/f"{case}-{rep}"
    identity=dict(manifest=c.digest(plan),case=case,replicate=rep)
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    spec=plan["cases"][case]
    _,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
    rng_seed=t.seed((32,case,rep),0)
    try:
        mc=qec.direct_mc(problem,spec["rungs"][0],trials=plan["anchor_trials"],seed=rng_seed)
        record=dict(case=case,replicate=rep,status="ok",seed=rng_seed,estimate=mc.estimate,
                    failures=mc.failures,trials=mc.trials,interval=mc.interval,elapsed_seconds=mc.elapsed_seconds,
                    problem_hash=c.digest(problem.metadata()),warnings=mc.warnings)
    except Exception as error:
        record=dict(case=case,replicate=rep,status="failed",seed=rng_seed,error=repr(error),traceback=traceback.format_exc())
    c.save_artifact(path,identity,{},record)
    return record


def with_anchor_variance(record,anchor):
    output=dict(record)
    if anchor["status"]!="ok" or not anchor["failures"] or not anchor["estimate"]:
        output.update(available=False,interval=None,failure="anchor unavailable")
        return output
    var=(1-anchor["estimate"])/(anchor["trials"]*anchor["estimate"])
    se=math.sqrt(record["log_se"]**2+var)
    logp=record["log_estimate"]
    interval=None
    if record["estimate"] is not None and record["estimate"]>0 and logp-1.959963984540054*se>-745:
        interval=[math.exp(logp-1.959963984540054*se),math.exp(min(0.,logp+1.959963984540054*se))]
    output.update(log_se=se,anchor_log_variance=var,interval=interval,available=interval is not None,
                  failure=None if interval is not None else "interval unavailable")
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["plan","capacity","sample","anchors"])
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=96)
    parser.add_argument("--capacity",action="store_true")
    parser.add_argument("--case",type=int,choices=range(4))
    args=parser.parse_args()
    if args.command=="plan":
        if (args.root/"manifest.json").exists():
            raise ValueError("manifest exists")
        c.atomic_json(args.root/"manifest.json",make_plan(capacity=args.capacity))
        return
    plan=json.loads((args.root/"manifest.json").read_text())
    expected=make_plan(capacity=plan["purpose"]=="capacity")
    if plan!=json.loads(c.canonical(expected)):
        raise ValueError("plan or runtime differs")
    if (args.command=="capacity") != (plan["purpose"]=="capacity"):
        raise ValueError("capacity samples must never enter production")
    started=time.perf_counter()
    if args.command=="anchors":
        jobs=[(str(args.root),plan,case,rep) for case in range(4) for rep in range(plan["replicates"]) if args.case is None or case==args.case]
        records=c.parallel_map(anchor_task,jobs,args.workers)
    else:
        jobs=list(tasks(plan,args.case))
        # Larger codes first; each case has at least 96 capacity tasks.
        jobs.sort(key=lambda task:(-plan["cases"][task[0]]["size"],task))
        records=c.parallel_map(sample_summary,[(str(args.root),plan,task) for task in jobs],args.workers)
    summary=dict(manifest=c.digest(plan),command=args.command,case=args.case,tasks=len(records),
                 elapsed_seconds=time.perf_counter()-started,failed=sum(r["status"]!="ok" for r in records),records=records)
    c.atomic_json(args.root/f"{args.command}-{args.case}.json",summary)
    print(json.dumps({k:v for k,v in summary.items() if k!="records"}),flush=True)
    if summary["failed"]:
        raise RuntimeError("recorded failures retained; investigate before next stage")


if __name__=="__main__":
    main()
