"""Standalone fixed-setting BAR cohorts with fresh anchors and separate phase clocks."""
import argparse
from contextlib import contextmanager
import itertools
import json
import os
from pathlib import Path
import re
import socket
import time
import traceback

import numpy as np
import mcmc4qec as qec
import calibration as c
import tile_study as t
import tile_bar_study as b
import tile_mc_time_benchmark as native


THREADS=native.THREADS
WARNING="Standalone selected-setting measurement, not evidence that selection met a precision target. Fresh independent anchor per replicate. All failed replicates retained. Task clocks include compact re-decoding but exclude artifact writes. Cached task time is historical. No mixing or nominal coverage guarantee."


def make_plan(settings,*,capacity,case=None):
    if case is not None and (type(case) is not int or case not in range(4)):
        raise ValueError("case must be one of 0, 1, 2, 3")
    selected_case=case
    source=b.make_plan()
    if (settings.get("schema")!=1 or settings.get("purpose")!="standalone_bar_settings" or
        settings.get("sampling_manifest")!=c.digest(source)):
        raise ValueError("settings must bind the fixed calibration manifest")
    evidence=settings.get("selection_evidence_sha256",[])
    if not evidence or any(not isinstance(x,str) or not re.fullmatch(r"[0-9a-f]{64}",x) for x in evidence):
        raise ValueError("selection evidence hashes required; they are not an accuracy certification")
    rows=settings["records"]
    if [(r["case"],r["epsilon"]) for r in rows]!=list(itertools.product(range(4),(.2,.1))):
        raise ValueError("all eight ordered case/precision outcomes required")
    conditions=[]
    for row in rows:
        case=row["case"]
        spec=source["cases"][case]
        if row["status"]=="unmet":
            if not row.get("reason") or "condition" in row:
                raise ValueError("unmet condition needs reason and no selected configuration")
            conditions.append(dict(row))
            continue
        cfg=row.get("condition",{})
        if (row["status"]!="selected" or set(cfg)!={"case","kernel","init","chains","burn","samples","ladder","method","block"}
            or cfg["case"]!=case or cfg["kernel"] not in source["kernels"] or cfg["init"] not in source["initializations"]
            or cfg["chains"] not in (4,spec["chains"]) or cfg["burn"] not in source["burns"]
            or cfg["samples"] not in spec["windows"] or cfg["ladder"] not in ("coarse","fine")):
            raise ValueError("selected setting is outside fixed calibration grid")
        block=cfg["block"]
        if not ((cfg["method"]=="cross_chain" and block is None) or
                (cfg["method"]=="block" and block in source["blocks"] and block<=cfg["samples"] and (block!=1024 or cfg["samples"]>=6000))):
            raise ValueError("selected uncertainty method differs from calibration grid")
        conditions.append(dict(row,size=spec["size"],noise=spec["noise"],n=2*spec["size"]**2,target_p=spec["target"],
                               rungs=spec["coarse"] if cfg["ladder"]=="coarse" else spec["rungs"],
                               initialization_stride=spec["chains"]))
    inputs=native.platform_inputs()
    return dict(schema=1,case=selected_case,purpose="bar_time_capacity" if capacity else "bar_time_benchmark",replicates=96 if capacity else 192,
                seed_stage=141 if capacity else 140,master_seed=t.MASTER,selection_digest=c.digest(settings),conditions=conditions,
                kernels=source["kernels"],decoder=source["decoder"],anchor_trials=source["anchor_trials"],
                bootstrap_replicates=source["bootstrap_replicates"],cache_cap=source["cache_cap"],
                max_initial_attempts=source["max_initial_attempts"],runtime=b.runtime(),
                sources={"benchmark":c.file_hash(__file__),"native_driver":c.file_hash(native.__file__),
                    "native_probe":c.file_hash(native.native_probe.__file__),"native_validator":c.file_hash(native.trace_audit.__file__)},
                required_threads=THREADS,native_input_digests={k:c.digest(v) for k,v in inputs.items()},warning=WARNING)


def tasks(plan):
    return ((index,rep) for index,row in enumerate(plan["conditions"]) if row["status"]=="selected"
            and (plan["case"] is None or row["case"]==plan["case"]) for rep in range(plan["replicates"]))


def task_seed(plan,task,rung,chain,purpose):
    return t.seed((plan["seed_stage"],*task,rung,chain),purpose)


def logical_index(condition,rep,chain):
    return rep*condition["initialization_stride"]+chain


@contextmanager
def clock(timing,key):
    started,cpu=time.perf_counter(),time.process_time()
    try:
        yield
    finally:
        timing[key]["wall_seconds"]+=time.perf_counter()-started
        timing[key]["cpu_seconds"]+=time.process_time()-cpu


def check_metadata(result,problem,p,seed):
    meta=result.metadata
    if meta["sampling_p"]!=p or meta["rng"]["entropy"]!=seed or c.digest({k:meta[k] for k in ("model","noise","decoder","failure")})!=c.digest(problem.metadata()):
        raise ValueError("actual model, fixed decoder, sampling p or RNG differs")


def run_task(args):
    root,plan,task=args
    path=Path(root)/"tasks"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task))
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    started,cpu=time.perf_counter(),time.process_time()
    row=plan["conditions"][task[0]]
    cfg=row["condition"]
    timing={k:dict(wall_seconds=0.,cpu_seconds=0.) for k in ("construction","anchor","initialization","sampling","compact","analysis")}
    record=dict(task=list(task),case=row["case"],epsilon=row["epsilon"],replicate=task[1],status="ok",condition=cfg,
                estimate=None,interval=None,available=False,failure=None,failed_chains=0,chains=[],timing=timing,
                anchor_seed=task_seed(plan,task,0,0,0),bootstrap_seed=task_seed(plan,task,0,0,3))
    arrays={}
    try:
        with clock(timing,"construction"):
            code,problem=t.build_problem(row["size"],row["noise"],row["target_p"])
        record["problem_hash"]=c.digest(problem.metadata())
        with clock(timing,"anchor"):
            mc=qec.direct_mc(problem,row["rungs"][0],trials=plan["anchor_trials"],seed=record["anchor_seed"])
            check_metadata(mc,problem,row["rungs"][0],record["anchor_seed"])
            if mc.trials!=plan["anchor_trials"]:
                raise ValueError("anchor trial count differs")
            record["anchor"]=dict(status="ok",seed=record["anchor_seed"],estimate=mc.estimate,failures=mc.failures,
                                  trials=mc.trials,interval=None if mc.interval is None else list(mc.interval),metadata=mc.metadata)
        shape=(len(row["rungs"]),cfg["chains"],cfg["samples"])
        arrays={key:np.zeros(shape,dtype=dtype) for key,dtype in (("weight",np.uint16),("syndrome_weight",np.uint16),("sector",np.uint32))}
        arrays["initial"]=np.zeros((*shape[:2],code.n),dtype=np.uint8)
        arrays["final"]=np.zeros_like(arrays["initial"])
        arrays["chain_ok"]=np.zeros(shape[:2],dtype=np.bool_)
        for rung,p in enumerate(row["rungs"]):
            for chain in range(cfg["chains"]):
                entry=dict(rung=rung,chain=chain,status="ok",init_seed=task_seed(plan,task,rung,chain,1),sample_seed=task_seed(plan,task,rung,chain,2))
                try:
                    with clock(timing,"initialization"):
                        initial,attempts=t.initial_state(code,problem,p,row["noise"],cfg["init"],logical_index(row,task[1],chain),
                            np.random.default_rng(entry["init_seed"]),plan["max_initial_attempts"])
                    entry["initial_attempts"]=attempts
                    arrays["initial"][rung,chain]=initial
                    with clock(timing,"sampling"):
                        sampled=qec.sample_faulty(problem,p,config=qec.SamplingConfig(samples=cfg["burn"]+cfg["samples"],burn_in=0,
                            kernels=qec.KernelConfig(**plan["kernels"][cfg["kernel"]]),cache_cap=plan["cache_cap"],cache_policy="lru"),
                            initial_state=initial,seed=entry["sample_seed"])
                    check_metadata(sampled,problem,p,entry["sample_seed"])
                    entry.update(metadata=sampled.metadata,acceptance=sampled.acceptance,warnings=sampled.warnings)
                    with clock(timing,"compact"):
                        kept=sampled.states[0][cfg["burn"]:]
                        if kept.shape!=(cfg["samples"],code.n):
                            raise ValueError("standalone trace length differs")
                        compact=t.compact(problem,kept)
                        if np.any(compact["sector"]==0):
                            raise ValueError("independent re-decode found a successful stored state")
                        for key in ("weight","syndrome_weight","sector"):
                            arrays[key][rung,chain]=compact[key]
                        arrays["final"][rung,chain]=kept[-1]
                        arrays["chain_ok"][rung,chain]=True
                except Exception as error:
                    entry.update(status="failed",error=repr(error),traceback=traceback.format_exc())
                    record["failed_chains"]+=1
                record["chains"].append(entry)
        if record["failed_chains"]:
            record.update(status="failed",failure="sampling_failed")
        elif not record["anchor"]["failures"]:
            record.update(status="unavailable",failure="anchor_unavailable")
        else:
            with clock(timing,"analysis"):
                result=c.estimate_window(list(arrays["weight"]),code.n,row["rungs"],record["anchor"]["estimate"],
                    block=cfg["block"],replicates=plan["bootstrap_replicates"],rng=np.random.default_rng(record["bootstrap_seed"]))
                record.update(b.with_anchor_variance(result,record["anchor"]))
            if not record["available"]:
                record["status"]="unavailable"
    except Exception as error:
        record.update(status="failed",failure=repr(error),traceback=traceback.format_exc())
    record.update(task_wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_mb=c.peak_rss_mb(),warning=WARNING)
    c.save_artifact(path,identity,arrays,record)
    return record


def run_summary(args):
    root,plan,task=args
    reused=(Path(root)/"tasks"/c.task_id(task)).with_suffix(".done.json").exists()
    result=run_task(args)
    return dict({k:v for k,v in result.items() if k not in ("chains","anchor")},reused=reused)


def run(root,*,workers=96):
    if not os.environ.get("PBS_JOBID") or workers!=96 or any(os.environ.get(k)!=v for k,v in THREADS.items()):
        raise ValueError("96-worker qsub job with pinned single-thread environment required")
    root=Path(root)
    plan=json.loads((root/"manifest.json").read_text())
    settings=json.loads((root/"settings.json").read_text())
    if c.canonical(plan)!=c.canonical(make_plan(settings,capacity=plan["purpose"]=="bar_time_capacity",case=plan["case"])):
        raise ValueError("settings, source, runtime or plan changed")
    if not list(tasks(plan)) or (root/"summary.json").exists() or (root/"tasks").exists():
        raise ValueError("fresh nonempty cohort required for standalone timing")
    with (root/"execution_intent.json").open("xb") as stream:
        stream.write(c.canonical(dict(manifest=c.digest(plan),pbs_job_id=os.environ["PBS_JOBID"]))+b"\n")
    native.native_preflight(root,plan)
    observed=json.loads((root/"native_preflight.json").read_text())
    observed.update(manifest=c.digest(plan),pbs_job_id=os.environ["PBS_JOBID"],hostname=socket.gethostname())
    c.atomic_json(root/"native_preflight.json",observed)
    started=time.perf_counter()
    expected=list(tasks(plan))
    records=c.parallel_map(run_summary,[(str(root),plan,task) for task in expected],workers)
    records.sort(key=lambda row:row["task"])
    if [tuple(row["task"]) for row in records]!=expected:
        raise ValueError("missing or duplicate standalone BAR task")
    summary=dict(manifest=c.digest(plan),tasks=len(records),records=records,
                 unmet_conditions=[row for row in plan["conditions"] if row["status"]=="unmet"],
                 failed=sum(row["status"]=="failed" for row in records),unavailable=sum(not row["available"] for row in records),
                 reused_tasks=sum(row["reused"] for row in records),phase_wall_seconds=time.perf_counter()-started,
                 native_preflight_sha256=c.file_hash(root/"native_preflight.json"),warning=WARNING)
    c.atomic_json(root/"summary.json",summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--settings",type=Path)
    parser.add_argument("--capacity",action="store_true")
    parser.add_argument("--case",type=int,choices=range(4))
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if args.command=="plan":
        if args.settings is None or (args.root.exists() and any(args.root.iterdir())):
            raise ValueError("settings JSON and new empty root required")
        settings=json.loads(args.settings.read_text())
        plan=make_plan(settings,capacity=args.capacity,case=args.case)
        for name,value in (("settings",settings),("manifest",plan),*native.platform_inputs().items()):
            c.atomic_json(args.root/(name+".json"),value)
        print(json.dumps(plan))
        return
    result=run(args.root,workers=args.workers)
    print(json.dumps({k:v for k,v in result.items() if k!="records"}))
    if result["failed"]:
        raise RuntimeError("failed standalone BAR tasks retained; inspect before further work")


if __name__=="__main__":
    main()
