"""Fixed independent MC cohorts with explicit task CPU/wall timing and provenance."""
import argparse
import itertools
import json
import os
from pathlib import Path
import socket
import time
import traceback

import mcmc4qec as qec
import calibration as c
import tile_study as t
import tile_mc_precision_budget as budget_module
import audit_tile_traces as trace_audit
import probe_tile_decoder_platform as native_probe


THREADS={name:"1" for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")}


def platform_inputs():
    root=Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17"
    values={key:json.loads((root/name).read_text()) for key,name in (
        ("platform_profile","decoder_platform_linux.json"),("platform_fixture","decoder_platform_fixture.json"))}
    profile,fixture=values["platform_profile"],values["platform_fixture"]
    if profile["fixture"]!=c.digest(fixture) or not profile["native_ldpc_sha256"]:
        raise ValueError("fixed native profile or fixture binding missing")
    return values


def native_preflight(root,plan):
    inputs={key:json.loads((root/(key+".json")).read_text()) for key in plan["native_input_digests"]}
    if {key:c.digest(value) for key,value in inputs.items()}!=plan["native_input_digests"]:
        raise ValueError("saved native inputs differ from fixed manifest")
    started=time.perf_counter()
    actual=native_probe.probe(inputs["platform_fixture"])
    trace_audit.validate_platform(inputs["platform_profile"],actual)
    evidence=dict(profile=actual,wall_seconds=time.perf_counter()-started,
                  manifest=c.digest(plan),hostname=socket.gethostname(),pbs_job_id=os.environ.get("PBS_JOBID"))
    c.atomic_json(root/"native_preflight.json",evidence)
    return c.file_hash(root/"native_preflight.json")


def make_plan(budget,*,capacity):
    if budget["stage"]!="direct_mc_time_to_accuracy_budget_v1" or budget["replicates"]!=192 or budget["seed_stage"]!=121 or budget["master_seed"]!=t.MASTER:
        raise ValueError("wrong fixed MC budget stage")
    if c.canonical(budget["cases"])!=c.canonical(t.CASES) or budget["decoder"]!=t.SETTINGS or budget["source_sha256"]!=c.file_hash(budget_module.__file__):
        raise ValueError("code, decoder or budget producer differs")
    conditions=budget["records"]
    if [(row["case"],row["epsilon"]) for row in conditions]!=[(case,epsilon) for case in range(4) for epsilon in (.2,.1)]:
        raise ValueError("all eight ordered precision conditions required")
    for row in conditions:
        expected=budget_module.budget_row(dict(case=row["case"],target_p=row["target_p"],
                                               estimate=row["reference_point"],interval_999=row["reference_interval_999"]),row["epsilon"])
        if row!=expected or row["target_p"]!=(.03 if t.CASES[row["case"]][0]==6 else .05):
            raise ValueError("fixed budget or target changed")
    if budget["total_planned_trials"]!=192*sum(row["planned_trials"] for row in conditions):
        raise ValueError("total fixed trial count differs")
    return dict(schema=1,purpose="mc_precision_capacity" if capacity else "mc_precision_benchmark",
                replicates=96 if capacity else 192,seed_stage=122 if capacity else 121,
                budget_digest=c.digest(budget),cases=json.loads(c.canonical(budget["cases"])),
                conditions=json.loads(c.canonical(conditions)),decoder=t.SETTINGS,
                runtime=dict(**t.runtime(),mc_timing_driver_sha256=c.file_hash(__file__),
                             budget_builder_sha256=c.file_hash(budget_module.__file__),
                             native_probe_sha256=c.file_hash(native_probe.__file__),
                             native_validator_sha256=c.file_hash(trace_audit.__file__)),required_threads=THREADS,
                native_input_digests={key:c.digest(value) for key,value in platform_inputs().items()},
                warning="Fixed-N independent MC. Capacity samples never enter the benchmark. Worker task clocks exclude artifact writes; phase walltime includes pool startup and persistence. CPU time is measured separately from elapsed time. Achieved precision and runtime comparisons require completed cohorts.")


def tasks(plan):
    return itertools.product(range(len(plan["conditions"])),range(plan["replicates"]))


def task_seed(plan,task):
    return t.seed((plan["seed_stage"],*task),0)


def run_task(args):
    root,plan,task=args
    path=Path(root)/"tasks"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task))
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return cached[1]
    condition_index,rep=task
    condition=plan["conditions"][condition_index]
    case=condition["case"]
    size,noise=plan["cases"][case]
    seed=task_seed(plan,task)
    record=dict(task=list(task),case=case,replicate=rep,epsilon=condition["epsilon"],
                target_p=condition["target_p"],seed=seed,status="ok",purpose=plan["purpose"])
    started,cpu=time.perf_counter(),time.process_time()
    try:
        code,problem=t.build_problem(size,noise,condition["physical_decoder_prior"])
        record["construction_wall_seconds"]=time.perf_counter()-started
        result=qec.direct_mc(problem,condition["target_p"],trials=condition["planned_trials"],seed=seed)
        metadata=result.metadata
        if metadata["sampling_p"]!=condition["target_p"] or metadata["rng"]["entropy"]!=seed or result.trials!=condition["planned_trials"]:
            raise ValueError("actual MC metadata differs from fixed inputs")
        problem_hash=c.digest(problem.metadata())
        if c.digest({key:metadata[key] for key in ("model","noise","decoder","failure")})!=problem_hash:
            raise ValueError("actual MC model/decoder metadata differs")
        record.update(n=code.n,noise=noise,failures=result.failures,trials=result.trials,estimate=result.estimate,
                      interval=None if result.interval is None else list(result.interval),conditional_weight=result.conditional_weight,
                      direct_mc_elapsed_seconds=result.elapsed_seconds,metadata=metadata,
                      metadata_sha256=c.digest(metadata),problem_hash=problem_hash,warnings=result.warnings)
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record.update(task_wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
                  peak_rss_mb=c.peak_rss_mb(),thread_environment={key:os.environ.get(key) for key in THREADS})
    c.save_artifact(path,identity,{},record)
    return record


def run_summary(args):
    return {key:value for key,value in run_task(args).items() if key!="metadata"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--budget",type=Path)
    parser.add_argument("--capacity",action="store_true")
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if args.command=="plan":
        if args.budget is None or (args.root.exists() and any(args.root.iterdir())):
            raise ValueError("fixed budget and new empty root required")
        budget=json.loads(args.budget.read_text())
        plan=make_plan(budget,capacity=args.capacity)
        args.root.mkdir(parents=True,exist_ok=True)
        (args.root/"budget.json").write_bytes(args.budget.read_bytes())
        for key,value in platform_inputs().items():
            c.atomic_json(args.root/(key+".json"),value)
        c.atomic_json(args.root/"manifest.json",plan)
        return
    if not os.environ.get("PBS_JOBID") or args.workers!=96 or any(os.environ.get(key)!=value for key,value in THREADS.items()):
        raise ValueError("submit the 96-worker run via qsub with the pinned single-thread environment")
    plan=json.loads((args.root/"manifest.json").read_text())
    budget=json.loads((args.root/"budget.json").read_text())
    if plan!=json.loads(c.canonical(make_plan(budget,capacity=plan["purpose"]=="mc_precision_capacity"))):
        raise ValueError("MC benchmark source/runtime/manifest changed")
    if (args.root/"summary.json").exists() or (args.root/"tasks").exists():
        raise ValueError("existing timing artifacts; phase timing requires a fresh execution")
    intent=dict(manifest=c.digest(plan),hostname=socket.gethostname(),pbs_job_id=os.environ["PBS_JOBID"])
    with (args.root/"execution_intent.json").open("xb") as stream:
        stream.write(c.canonical(intent)+b"\n")
    preflight_hash=native_preflight(args.root,plan)
    started=time.perf_counter()
    # Long code/high-trial/depolarizing tasks first, without outcome selection.
    ordered=sorted(tasks(plan),key=lambda task:(-plan["cases"][plan["conditions"][task[0]]["case"]][0],
                     -plan["conditions"][task[0]]["planned_trials"],task))
    records=c.parallel_map(run_summary,[(str(args.root),plan,task) for task in ordered],args.workers)
    records.sort(key=lambda row:row["task"])
    if [tuple(row["task"]) for row in records]!=list(tasks(plan)):
        raise ValueError("missing or duplicate completed task")
    summary=dict(manifest=c.digest(plan),purpose=plan["purpose"],tasks=len(records),failed=sum(row["status"]!="ok" for row in records),
                 native_preflight_sha256=preflight_hash,
                 phase_wall_seconds=time.perf_counter()-started,sum_task_cpu_seconds=sum(row["cpu_seconds"] for row in records),
                 records=records,warning=plan["warning"])
    c.atomic_json(args.root/"summary.json",summary)
    print(json.dumps({key:value for key,value in summary.items() if key!="records"}))
    if summary["failed"]:
        raise RuntimeError("failed MC tasks retained; inspect before next stage")


if __name__=="__main__":
    main()
