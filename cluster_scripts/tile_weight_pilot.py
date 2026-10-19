"""Independent weight-layer pilot for allocation and resource timing only."""
import argparse
import itertools
import json
from pathlib import Path
import time
import traceback

import numpy as np
import calibration as c
import tile_study as t
import tile_weight_stratified as w


def make_plan():
    return dict(purpose="weight_stratified_pilot",schema=1,cases=t.CASES,
                priors=[[.03,.01,.003,.001],[.05,.01,.003,.001],[.03,.01,.003,.001],[.05,.01,.003,.001]],
                weights=[0,1,2,3,4,5,6,7,8,10,12,16],replicates=8,samples=512,decoder=t.SETTINGS,
                runtime=t.runtime(),driver_sha256=c.file_hash(__file__),strata_source_sha256=c.file_hash(w.__file__),
                warning="Allocation/timing pilot only. Missing weight layers prohibit use as a logical-error reference.")


def tasks(plan):
    return itertools.product(range(len(plan["cases"])),range(4),range(len(plan["weights"])),range(plan["replicates"]))


def run_task(args):
    root,plan,task=args
    identity=dict(manifest=c.digest(plan),task=list(task))
    path=Path(root)/"layers"/c.task_id(task)
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    started=time.perf_counter()
    arrays={}
    record=dict(task=list(task),status="ok")
    try:
        case,prior_index,weight_index,rep=task
        size,noise=plan["cases"][case]
        prior=plan["priors"][case][prior_index]
        weight=plan["weights"][weight_index]
        code,problem=t.build_problem(size,noise,prior)
        seed=t.seed((110,*task),0)
        rng=np.random.default_rng(seed)
        trials=1 if weight==0 else plan["samples"]
        states=w.draw_patterns(code.n,weight,noise,trials,rng)
        mask=t.compact(problem,states)["sector"]!=0
        checked=min(16,trials)
        mismatches=int(np.count_nonzero(mask[:checked]!=[problem.is_faulty(state) for state in states[:checked]]))
        if mismatches:
            raise ValueError("batch/public failure mismatch")
        arrays=dict(states=states,failure=mask)
        record.update(case=case,n=code.n,noise=noise,physical_decoder_prior=prior,
                      sector_prior=prior if noise=="bit" else 2*prior/3,w=weight,
                      seed=seed,trials=trials,failures=int(mask.sum()),failure_mismatches=mismatches,
                      checked_public_states=checked,problem_hash=c.digest(problem.metadata()))
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started,peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(path,identity,arrays,record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["plan","run"])
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if args.command=="plan":
        if (args.root/"manifest.json").exists():
            raise ValueError("manifest exists")
        c.atomic_json(args.root/"manifest.json",make_plan())
        return
    plan=json.loads((args.root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(make_plan())):
        raise ValueError("pilot source/runtime changed")
    started=time.perf_counter()
    jobs=sorted(tasks(plan),key=lambda task:(-plan["cases"][task[0]][0],-plan["weights"][task[2]],task))
    records=c.parallel_map(run_task,[(str(args.root),plan,task) for task in jobs],args.workers)
    records.sort(key=lambda row:row["task"])
    summary=dict(manifest=c.digest(plan),tasks=len(records),failed=sum(row["status"]!="ok" for row in records),
                 wall_seconds=time.perf_counter()-started,records=records,warning=plan["warning"])
    c.atomic_json(args.root/"summary.json",summary)
    print(json.dumps({k:v for k,v in summary.items() if k!="records"}))
    if summary["failed"]:
        raise RuntimeError("weight pilot failed; failures retained")


if __name__=="__main__":
    main()
