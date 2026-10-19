"""Resource profiling on explicitly synthetic data, never scientific estimates."""
import argparse
import itertools
import json
from pathlib import Path
import tempfile
import time
import traceback

import numpy as np
import calibration as c
import tile_study as t
import tile_bar_study as b
import tile_bar_analysis as a


def make_plan():
    plan=b.make_plan()
    plan.update(purpose="synthetic_analysis_capacity",replicates=24,
                capacity_source_sha256=c.file_hash(__file__),analysis_source_sha256=c.file_hash(a.__file__),
                warning="ARTIFICIAL DATA for resource profiling only. No physical or coverage interpretation.")
    return plan


def profile(args):
    root,plan,task=args
    if plan["purpose"]!="synthetic_analysis_capacity":
        raise ValueError("synthetic input cannot enter production")
    root=Path(root).resolve()
    path=root/"profiles"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task),synthetic=True)
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    started=time.perf_counter()
    record=dict(task=list(task),synthetic=True,status="ok")
    scratch=root/"scratch"
    scratch.mkdir(parents=True,exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="profile-",dir=scratch) as temporary:
            work=Path(temporary).resolve()
            if not work.is_relative_to(scratch.resolve()):
                raise ValueError("scratch escaped root")
            case,rep=task
            spec=plan["cases"][case]
            code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
            group=(case,0,0,rep)
            model_hash=c.digest(problem.metadata())
            rng=np.random.default_rng(t.seed((100,*task),0))
            bits=len(code.lx)*(2 if spec["noise"]=="depolarizing" else 1)
            for rung,chain in itertools.product(range(len(spec["rungs"])),range(spec["chains"])):
                trace=(*group,rung,chain)
                arrays=dict(weight=np.maximum(1,rng.binomial(code.n,spec["rungs"][rung],spec["steps"])).astype(np.uint16),
                            syndrome_weight=rng.binomial(len(code.hz),.2,spec["steps"]).astype(np.uint16),
                            sector=rng.integers(1,2**bits,size=spec["steps"],dtype=np.uint32))
                c.save_artifact(work/"traces"/c.task_id(trace),dict(manifest=c.digest(plan),task=list(trace)),arrays,
                                dict(status="ok",synthetic=True,problem_hash=model_hash))
            c.save_artifact(work/"anchors"/f"{case}-{rep}",dict(manifest=c.digest(plan),case=case,replicate=rep),{},
                            dict(status="ok",synthetic=True,estimate=.5,failures=8192,trials=16384))
            context=a.analysis_context(plan,[dict(case=case,target_p=spec["target"],estimate=.04,standard_error=.001,interval_999=[.037,.043])])
            context.update(synthetic=True,warning=plan["warning"])
            analysis=a.analyze_group((str(work),plan,context,group))
            record.update(rows=len(analysis["rows"]),analysis_seconds=analysis["wall_seconds"],
                          peak_rss_mb=analysis["peak_rss_mb"],diagnostic_count=analysis["diagnostic_count"])
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record["wall_seconds"]=time.perf_counter()-started
    c.save_artifact(path,identity,{},record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["plan","run"])
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if args.command=="plan":
        if (args.root/"manifest.json").exists():
            raise ValueError("manifest already exists")
        c.atomic_json(args.root/"manifest.json",make_plan())
        return
    plan=json.loads((args.root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(make_plan())):
        raise ValueError("profile plan/runtime changed")
    started=time.perf_counter()
    jobs=[(str(args.root),plan,(case,rep)) for case,rep in itertools.product(range(4),range(plan["replicates"]))]
    records=c.parallel_map(profile,jobs,args.workers)
    summary=dict(manifest=c.digest(plan),synthetic=True,tasks=len(records),failed=sum(r["status"]!="ok" for r in records),
                 wall_seconds=time.perf_counter()-started,records=records)
    c.atomic_json(args.root/"summary.json",summary)
    print(json.dumps({k:v for k,v in summary.items() if k!="records"}))
    if summary["failed"]:
        raise RuntimeError("resource profile failed")


if __name__=="__main__":
    main()
