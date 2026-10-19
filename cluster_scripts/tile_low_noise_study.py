"""Fixed-prior low-noise tile traces and independent anchors, executed via PBS.

Each root contains exactly one case/target and one capacity or production plan.
Raw artifacts preserve failures. Resource planning and qsub are separate.
"""
import argparse
from dataclasses import asdict
import itertools
import json
import math
import os
from pathlib import Path
import socket
import time
import traceback

import numpy as np
import mcmc4qec as qec
import calibration as c
import tile_study as t
import tile_mc_time_benchmark as native


TARGETS = (.01, .003, .001)
FINE = (.1,.085,.07,.06,.05,.04,.03,.02,.015,.01,.007,.005,.003,.002,.001)
COARSE = (.1,.07,.05,.03,.015,.01,.005,.003,.001)
WARNING = "Fixed-prior low-noise study. All failed tasks retained. Logical initialization is not stationary. Diagnostics, support checks and setting agreement do not certify convergence, accuracy or coverage. Capacity samples never enter production."


def make_plan(case, target_index, *, capacity):
    if type(case) is not int or case not in range(4) or type(target_index) is not int or target_index not in range(3):
        raise ValueError("valid case and target index required")
    if type(capacity) is not bool:
        raise ValueError("explicit capacity flag required")
    size, noise = t.CASES[case]
    target = TARGETS[target_index]
    return dict(schema=1, purpose="low_noise_capacity" if capacity else "low_noise_production",
                case=case, target_index=target_index, master_seed=t.MASTER,
                replicates=2 if capacity else 192,
                stages=dict(sample=150 if capacity else 151, anchors=154 if capacity else 152,
                            analysis=155 if capacity else 153),
                condition=dict(size=size, noise=noise, target=target,
                               rungs=[p for p in FINE if p>=target], coarse=[p for p in COARSE if p>=target],
                               chains=16 if case==0 else 8, steps=66000 if case==0 else 18000,
                               windows=[600,6000,60000 if case==0 else 12000]),
                initializations=["logical_basis","logical_combination"],
                kernels={name:asdict(kernel) for name,kernel in t.KERNELS.items()},
                decoder=t.SETTINGS, burns=[600,6000], chain_counts=[4,"maximum"],
                blocks=[32,128,1024], bootstrap_replicates=1000, anchor_trials=16384,
                cache_cap=200000, checkpoint_stride=1000,
                runtime=t.runtime(), sources=dict(driver=c.file_hash(__file__),
                    native=c.file_hash(native.__file__), probe=c.file_hash(native.native_probe.__file__),
                    validator=c.file_hash(native.trace_audit.__file__)),
                native_input_digests={key:c.digest(value) for key,value in native.platform_inputs().items()},
                required_threads=native.THREADS, warning=WARNING)


def tasks(plan, phase="sample"):
    case,target=plan["case"],plan["target_index"]
    if phase=="anchors":
        for rep in range(plan["replicates"]):
            yield case,target,0,0,rep,0,0
    elif phase=="sample":
        for kernel,initial,rep,rung in itertools.product(range(2),range(2),range(plan["replicates"]),range(len(plan["condition"]["rungs"]))):
            chains=[rep] if plan["purpose"]=="low_noise_capacity" else range(plan["condition"]["chains"])
            for chain in chains:
                yield case,target,kernel,initial,rep,rung,chain
    else:
        raise ValueError("unknown task phase")


def validate_task(plan, task, phase):
    if len(task)!=7 or any(type(x) is not int or x<0 for x in task):
        raise ValueError("invalid task coordinates")
    case,target,kernel,initial,rep,rung,chain=task
    if (case!=plan["case"] or target!=plan["target_index"] or rep>=plan["replicates"]
            or kernel>=2 or initial>=2 or rung>=len(plan["condition"]["rungs"])
            or chain>=plan["condition"]["chains"]):
        raise ValueError("task outside fixed condition")
    if phase=="anchors":
        if any((kernel,initial,rung,chain)):
            raise ValueError("invalid anchor task")
    elif phase=="sample":
        if plan["purpose"]=="low_noise_capacity" and chain!=rep:
            raise ValueError("invalid capacity task chain")
    else:
        raise ValueError("invalid task phase")


def task_seed(plan, task, phase, purpose):
    return t.seed((plan["stages"][phase],*task),purpose)


def logical_state(code, noise, mode, index, rng):
    if noise=="bit":
        basis=np.asarray(code.lx,dtype=np.uint8)
    elif noise=="depolarizing":
        basis=np.stack((code.lx,3*code.lz),axis=1).reshape(-1,code.lx.shape[1]).astype(np.uint8)
    else:
        raise ValueError("unknown logical noise")
    count=len(basis)
    if not 0<count<63:
        raise ValueError("bounded nonempty logical basis required")
    coefficients=np.zeros(count,dtype=np.uint8)
    if mode=="logical_basis":
        coefficients[index%count]=1
    elif mode=="logical_combination":
        value=int(rng.integers(1,1<<count))
        coefficients=np.array([(value>>i)&1 for i in range(count)],dtype=np.uint8)
    else:
        raise ValueError("unknown logical initialization")
    # I/X/Y/Z = 0/1/2/3: bitwise XOR is Pauli multiplication modulo phase.
    return np.bitwise_xor.reduce(basis[coefficients.astype(bool)],axis=0),coefficients


def check_metadata(result, problem, p, seed):
    meta=result.metadata
    if (meta["sampling_p"]!=p or meta["rng"]["entropy"]!=seed
            or c.digest({key:meta[key] for key in ("model","noise","decoder","failure")})!=c.digest(problem.metadata())):
        raise ValueError("actual probability, RNG or fixed decoder differs")


def sample_task(args):
    root,plan,task=args
    validate_task(plan,task,"sample")
    path=Path(root)/"traces"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task))
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    spec=plan["condition"]
    _,_,kernel,initial,rep,rung,chain=task
    mode=plan["initializations"][initial]
    p=spec["rungs"][rung]
    record=dict(task=list(task),status="ok",stage=plan["stages"]["sample"],
                physical_p=p,decoder_prior=spec["target"],initialization=mode,
                init_seed=task_seed(plan,task,"sample",0),sample_seed=task_seed(plan,task,"sample",1))
    started,cpu=time.perf_counter(),time.process_time()
    arrays={}
    try:
        code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
        record["construction_seconds"]=time.perf_counter()-started
        record["problem_hash"]=c.digest(problem.metadata())
        init_start=time.perf_counter()
        state,coeff=logical_state(code,spec["noise"],mode,rep*spec["chains"]+chain,
                                  np.random.default_rng(record["init_seed"]))
        arrays.update(initial=state,initial_coefficients=coeff,initial_syndrome=problem.model.syndrome(state))
        if not problem.is_faulty(state) or not math.isfinite(problem.log_prob(state,p)):
            raise ValueError("initial state outside supported failure set")
        record["initial_sector"]=int(t.compact(problem,state[None,:])["sector"][0])
        if not record["initial_sector"]:
            raise ValueError("initial residual logical sector is zero")
        record["initial_seconds"]=time.perf_counter()-init_start
        name=list(plan["kernels"])[kernel]
        sample_start=time.perf_counter()
        result=qec.sample_faulty(problem,p,config=qec.SamplingConfig(samples=spec["steps"],burn_in=0,
            kernels=qec.KernelConfig(**plan["kernels"][name]),cache_cap=plan["cache_cap"],cache_policy="lru"),
            initial_state=state,seed=record["sample_seed"])
        record["sampling_seconds"]=time.perf_counter()-sample_start
        check_metadata(result,problem,p,record["sample_seed"])
        states=result.states[0]
        if len(states)!=spec["steps"]:
            raise ValueError("saved trace length differs")
        compact_start=time.perf_counter()
        compact=t.compact(problem,states)
        if np.any(compact["sector"]==0):
            raise ValueError("saved state independently re-decoded as successful")
        arrays.update({key:value for key,value in compact.items() if key!="logical"})
        indices=np.unique(np.r_[np.arange(0,len(states),plan["checkpoint_stride"]),len(states)-1])
        arrays.update(checkpoint_indices=indices,checkpoints=states[indices],final=states[-1])
        record.update(compact_seconds=time.perf_counter()-compact_start,checked_saved_states=len(states),
                      metadata=result.metadata,config=result.metadata["config"],acceptance=result.acceptance,
                      diagnostics=result.diagnostics,warnings=result.warnings)
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
                  peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(path,identity,arrays,record)
    return record


def anchor_task(args):
    root,plan,task=args
    validate_task(plan,task,"anchors")
    path=Path(root)/"anchors"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task))
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    spec=plan["condition"]
    record=dict(task=list(task),status="ok",stage=plan["stages"]["anchors"],physical_p=spec["rungs"][0],
                decoder_prior=spec["target"],seed=task_seed(plan,task,"anchors",0))
    started,cpu=time.perf_counter(),time.process_time()
    try:
        _,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
        result=qec.direct_mc(problem,record["physical_p"],trials=plan["anchor_trials"],seed=record["seed"])
        check_metadata(result,problem,record["physical_p"],record["seed"])
        if result.trials!=plan["anchor_trials"]:
            raise ValueError("anchor trial budget differs")
        record.update(problem_hash=c.digest(problem.metadata()),metadata=result.metadata,estimate=result.estimate,
                      failures=result.failures,trials=result.trials,interval=result.interval,
                      elapsed_seconds=result.elapsed_seconds,warnings=result.warnings)
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(path,identity,{},record)
    return record


def sample_summary(args):
    record=sample_task(args)
    return {key:record[key] for key in ("task","status","wall_seconds","cpu_seconds","peak_rss_mb")}


def preflight(root, plan, phase):
    destination=Path(root)/f"preflight-{phase}"
    destination.mkdir(exist_ok=False)
    for key,digest in plan["native_input_digests"].items():
        value=json.loads((Path(root)/(key+".json")).read_text())
        if c.digest(value)!=digest:
            raise ValueError("saved native input differs")
        c.atomic_json(destination/(key+".json"),value)
    return native.native_preflight(destination,plan)


def run_phase(root, plan, phase, workers):
    root=Path(root)
    if not os.environ.get("PBS_JOBID") or workers!=96 or any(os.environ.get(k)!=v for k,v in native.THREADS.items()):
        raise ValueError("qsub with 96 workers and pinned single-thread environment required")
    if phase not in ("sample","anchors"):
        raise ValueError("unknown phase")
    expected=make_plan(plan["case"],plan["target_index"],capacity=plan["purpose"]=="low_noise_capacity")
    if c.canonical(plan)!=c.canonical(expected):
        raise ValueError("manifest source/runtime or fixed configuration changed")
    artifact_dir=root/("traces" if phase=="sample" else "anchors")
    if artifact_dir.exists() or (root/f"{phase}-summary.json").exists():
        raise ValueError("existing phase artifacts; automatic rerun forbidden")
    intent=dict(manifest=c.digest(plan),phase=phase,pbs_job_id=os.environ["PBS_JOBID"],hostname=socket.gethostname())
    with (root/f"{phase}-execution-intent.json").open("xb") as stream:
        stream.write(c.canonical(intent)+b"\n")
    native_hash=preflight(root,plan,phase)
    jobs=list(tasks(plan,phase))
    started=time.perf_counter()
    records=c.parallel_map(sample_summary if phase=="sample" else anchor_task,
                           [(str(root),plan,task) for task in jobs],workers)
    records.sort(key=lambda row:row["task"])
    if [tuple(row["task"]) for row in records]!=sorted(jobs):
        raise ValueError("missing or duplicate completed task")
    summary=dict(manifest=c.digest(plan),phase=phase,tasks=len(records),records=records,
                 failed=sum(row["status"]!="ok" for row in records),native_preflight_sha256=native_hash,
                 phase_wall_seconds=time.perf_counter()-started,warning=WARNING)
    c.atomic_json(root/f"{phase}-summary.json",summary)
    if summary["failed"]:
        raise RuntimeError("failed tasks retained; no seed replacement or automatic retry")
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","sample","anchors"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4))
    parser.add_argument("--target-index",type=int,choices=range(3))
    parser.add_argument("--capacity",action="store_true")
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if args.command=="plan":
        if args.root.exists() and any(args.root.iterdir()):
            raise ValueError("new empty output root required")
        plan=make_plan(args.case,args.target_index,capacity=args.capacity)
        args.root.mkdir(parents=True,exist_ok=True)
        for key,value in native.platform_inputs().items():
            c.atomic_json(args.root/(key+".json"),value)
        c.atomic_json(args.root/"manifest.json",plan)
        preflight(args.root,plan,"plan")
        print(json.dumps(dict(manifest=c.digest(plan),sampling_tasks=sum(1 for _ in tasks(plan)))))
    else:
        plan=json.loads((args.root/"manifest.json").read_text())
        summary=run_phase(args.root,plan,args.command,args.workers)
        print(json.dumps({key:value for key,value in summary.items() if key!="records"}))


if __name__=="__main__":
    main()
