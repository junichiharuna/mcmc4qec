"""Resource estimates from successful fixed eight-worker trace-audit capacity."""
import argparse
import json
import math
from pathlib import Path
import re

import calibration as c
import tile_low_noise_trace_audit_run as r

WARNING="Resource extrapolation only. Eight-worker capacity does not measure 96-worker I/O contention; the factor of two is not a completion guarantee. Sampling failures cannot supply a full-work capacity profile. Exceeding one-node limits requires a separate partition design."


def capacity_resources():
    return dict(workers=8,cpus=96,memory_gb=340,wall_seconds=86400,walltime="24:00:00",
                requested_nodes=1,max_nodes=2,warning="Initial capacity ceiling, not measured use or predicted completion.")


def positive(value):
    return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value) and value>0


def resource_plan(cap_plan,summary,full_plan):
    if (cap_plan["purpose"]!="low_noise_trace_audit_capacity" or cap_plan["replicates"]!=2
            or type(cap_plan["replicates"]) is not int or type(cap_plan["workers"]) is not int
            or cap_plan["workers"]!=8 or full_plan["purpose"]!="low_noise_trace_audit_full"
            or full_plan["replicates"]!=192 or type(full_plan["replicates"]) is not int or type(full_plan["workers"]) is not int
            or not 1<=full_plan["workers"]<=96):
        raise ValueError("fixed eight-worker capacity and full 192-replicate audit required")
    for key in set(cap_plan)|set(full_plan):
        if key not in ("purpose","replicates","workers") and cap_plan.get(key)!=full_plan.get(key):
            raise ValueError("capacity/full conditions, source or sampling evidence differ")
    expected=r.groups(cap_plan)
    rows=summary["records"]
    if (summary["manifest"]!=c.digest(cap_plan) or summary["groups"]!=8 or len(rows)!=8
            or [tuple(row["group"]) for row in rows]!=expected or summary["failed_audit_groups"]!=0
            or summary["failed_sampling"]!=0 or summary["context_error"] is not None
            or summary["input_changes"] or summary["native_platform_verified"] is not True):
        raise ValueError("complete successful capacity without sampling failures required")
    for row in rows:
        if (row["status"]!="ok" or row["failed_audits"]!=0 or row["failed_sampling"]!=0
                or row["summary_group_digest_verified"] is not True
                or type(row["planned_tasks"]) is not int or row["planned_tasks"]<=0
                or type(row["redecoded_checkpoints"]) is not int or row["redecoded_checkpoints"]<=0):
            raise ValueError("all capacity tasks must exercise successful checkpoint decoding")
        if any(not positive(row[key]) for key in ("wall_seconds","cpu_seconds","peak_rss_mb")):
            raise ValueError("positive finite wall/CPU/worker RSS measurements required")
    if (summary["planned_tasks"]!=sum(row["planned_tasks"] for row in rows)
            or len({row["planned_tasks"] for row in rows})!=1):
        raise ValueError("full-dimensional task count differs across capacity groups")
    wall=max(row["wall_seconds"] for row in rows)
    phase=summary["phase_wall_seconds"]
    if not positive(phase) or phase<wall:
        raise ValueError("phase must include its longest group and final input rehash")
    rss=max(row["peak_rss_mb"] for row in rows)
    workers=min(96,math.floor((340-8)*1024/(1.5*rss)))
    if workers<1:raise ValueError("one audit worker exceeds memory ceiling")
    count=len(r.groups(full_plan))
    group_time=wall*math.ceil(count/workers)
    overhead=(phase-wall)*count/len(rows)
    predicted=group_time+overhead
    seconds=1800*math.ceil((2*predicted+600)/1800)
    memory=max(32,math.ceil(1.5*workers*rss/1024+8))
    if seconds>86400 or memory>340:
        raise ValueError("full request exceeds one-node limits; partition design required")
    return dict(workers=workers,cpus=96,memory_gb=memory,wall_seconds=seconds,
                walltime=f"{seconds//3600:02d}:{seconds%3600//60:02d}:00",requested_nodes=1,max_nodes=2,
                predicted_seconds=predicted,predicted_group_seconds=group_time,predicted_phase_overhead_seconds=overhead,
                predicted_cpu_seconds=count*max(row["cpu_seconds"] for row in rows),
                observed_max_group_wall_seconds=wall,observed_phase_wall_seconds=phase,observed_peak_worker_rss_mb=rss,
                capacity_manifest=c.digest(cap_plan),full_manifest=c.digest(full_plan),
                sampling_manifest=cap_plan["sampling_manifest"],capacity_summary_digest=c.digest(summary),warning=WARNING)


def measured_capacity(root,source,full_plan):
    root,source=r.separate_roots(root,source)
    cap,sampling=r.read_plan(root,source)
    proof={}
    def read(name):
        path=r.path_in(root,name)
        proof[name]=c.file_hash(path)
        return json.loads(path.read_text())
    summary=read("summary.json")
    result=resource_plan(cap,summary,full_plan)
    profile=read("platform_profile.json")
    fixture=read("platform_fixture.json")
    expected=r.make_plan(sampling,profile,fixture,capacity=False,workers=full_plan["workers"],
                         completed_evidence=cap["completed_phase_evidence"],input_sha256=cap["input_sha256"])
    if c.canonical(expected)!=c.canonical(full_plan):
        raise ValueError("full audit plan/source differs from measured scientific condition")
    native=read("native_preflight.json")
    intent=read("execution-intent.json")
    if (summary["native_preflight_sha256"]!=proof["native_preflight.json"]
            or native.get("evidence",{}).get("native_platform_verified") is not True
            or {key:value for key,value in native.items() if key!="evidence"}!=intent
            or intent.get("manifest")!=c.digest(cap) or intent.get("sampling_manifest")!=c.digest(sampling)
            or intent.get("workers")!=8 or not intent.get("hostname")
            or not isinstance(intent.get("pbs_job_id"),str)
            or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",intent["pbs_job_id"])):
        raise ValueError("capacity native/PBS execution binding differs")
    actual=r.audit.validate_native_environment(sampling,platform_profile=profile,platform_fixture=fixture)
    if c.canonical(native["evidence"])!=c.canonical(actual):
        raise ValueError("capacity native evidence differs from current verified platform")
    submission=read("submission.json")
    submission_intent=read("submission-intent.json")
    if (submission.get("manifest")!=c.digest(cap) or submission.get("job_id")!=intent["pbs_job_id"]
            or {key:value for key,value in submission.items() if key!="job_id"}!=submission_intent):
        raise ValueError("capacity submission and execution differ")
    command=submission.get("command")
    if not isinstance(command,list) or len(command)!=2 or command[0]!="qsub":
        raise ValueError("recorded qsub command required")
    script=Path(command[1])
    if not script.is_absolute() or not script.resolve().is_relative_to(root):
        raise ValueError("capacity submission script must remain inside root")
    script_name=str(script.relative_to(root))
    proof[script_name]=c.file_hash(script)
    if submission.get("script_sha256")!=proof[script_name]:
        raise ValueError("capacity submission script changed")

    def load(base,identity):
        name=str(base.relative_to(root))
        marker=read(name+".done.json")
        if set(marker["sha256"])!={".json",".npz"}:
            raise ValueError("complete audit artifact hashes required")
        for ext in (".json",".npz"):
            proof[name+ext]=c.file_hash(r.path_in(root,name+ext))
        value=c.load_artifact(base,identity)
        if value is None:raise ValueError("missing capacity measurement/audit artifact")
        arrays,record=value
        if arrays:raise ValueError("unexpected capacity measurement/audit arrays")
        return record

    spec=sampling["condition"]
    checkpoints=len(range(0,spec["steps"],sampling["checkpoint_stride"]))
    if (spec["steps"]-1)%sampling["checkpoint_stride"]:checkpoints+=1
    for row in summary["records"]:
        group=tuple(row["group"])
        identity=dict(manifest=c.digest(cap),group=list(group))
        measurement=load(root/"measurements"/c.task_id(group),identity)
        if c.canonical(row)!=c.canonical(measurement):
            raise ValueError("capacity summary differs from measurement artifact")
        base=root/"audit/groups"/c.task_id(group)
        audited=load(base,identity)
        if row["audit_marker_sha256"]!=proof[str(base.relative_to(root))+".done.json"]:
            raise ValueError("measurement refers to different group audit")
        for key in ("group","status","planned_tasks","failed_audits","failed_sampling","redecoded_checkpoints","summary_group_digest_verified"):
            if audited[key]!=row[key]:raise ValueError("group audit and measurement counts differ")
        tasks=list(r.tasks_for_group(sampling,group))
        if ([tuple(item["task"]) for item in audited["tasks"]]!=tasks
                or audited["planned_tasks"]!=len(tasks) or audited["redecoded_checkpoints"]!=checkpoints*len(tasks)
                or audited["all_physical_states_redecoded"] is not False):
            raise ValueError("full-dimensional task/checkpoint census differs")
        expected_hashes={str(Path("traces")/(c.task_id(task)+ext)) for task in tasks for ext in (".done.json",".json",".npz")}
        if set(audited["input_sha256"])!=expected_hashes:
            raise ValueError("missing input trace hash")
        for task in audited["tasks"]:
            checked=task["result"]
            if (task["audit_status"]!="ok" or task["sampling_status"]!="ok" or checked["status"]!="ok"
                    or checked["saved_steps"]!=spec["steps"] or checked["redecoded_checkpoints"]!=checkpoints
                    or any(checked[key] is not True for key in ("initial_state_checked","initial_coefficients_checked","recorded_seeds_checked"))
                    or checked["all_physical_states_redecoded"] is not False):
                raise ValueError("capacity did not perform all required checkpoint checks")
        r.verify_group_inputs(source,root,cap,row)
    for name,digest in proof.items():
        if c.file_hash(r.path_in(root,name))!=digest:raise ValueError("capacity evidence changed during validation")
    if c.canonical(r.read_plan(root,source)[0])!=c.canonical(cap):
        raise ValueError("capacity context or source inputs changed")
    result.update(capacity_summary_sha256=proof["summary.json"],native_preflight_sha256=proof["native_preflight.json"],
                  evidence_sha256=proof,native_platform_verified=True,pbs_job_id=intent["pbs_job_id"],
                  resource_source_sha256=c.file_hash(__file__))
    return result


def prepare_full(root,source,capacity_root):
    """Choose workers before writing a new immutable full-audit manifest."""
    root,source=r.separate_roots(root,source)
    capacity_root=Path(capacity_root).resolve()
    if root.is_relative_to(capacity_root) or capacity_root.is_relative_to(root):
        raise ValueError("full and capacity roots must be separate")
    if root.exists() and any(root.iterdir()):raise ValueError("new empty full audit root required")
    cap,sampling=r.read_plan(capacity_root,source)
    profile=json.loads(r.path_in(capacity_root,"platform_profile.json").read_text())
    fixture=json.loads(r.path_in(capacity_root,"platform_fixture.json").read_text())
    provisional=r.make_plan(sampling,profile,fixture,capacity=False,workers=1,
                            completed_evidence=cap["completed_phase_evidence"],input_sha256=cap["input_sha256"])
    resource=measured_capacity(capacity_root,source,provisional)
    selected=r.make_plan(sampling,profile,fixture,capacity=False,workers=resource["workers"],
                         completed_evidence=cap["completed_phase_evidence"],input_sha256=cap["input_sha256"])
    resource=measured_capacity(capacity_root,source,selected)
    if resource["workers"]!=selected["workers"] or resource["full_manifest"]!=c.digest(selected):
        raise ValueError("selected workers/full manifest differ after capacity revalidation")
    current,current_sampling=r.read_plan(capacity_root,source)
    if (c.canonical(current)!=c.canonical(cap) or c.canonical(current_sampling)!=c.canonical(sampling)
            or c.file_hash(capacity_root/"summary.json")!=resource["capacity_summary_sha256"]
            or any(c.file_hash(r.path_in(capacity_root,name))!=digest for name,digest in resource["evidence_sha256"].items())):
        raise ValueError("capacity/source changed before creating full plan")
    plan=r.prepare(root,source,capacity=False,workers=resource["workers"])
    if c.canonical(plan)!=c.canonical(selected):
        raise ValueError("source changed while creating full plan; preserve partial root and investigate")
    if resource["workers"]!=plan["workers"] or resource["full_manifest"]!=c.digest(plan):
        raise ValueError("saved full plan differs from verified resource binding")
    return dict(plan=plan,resource=resource)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan-full",))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--capacity-root",type=Path,required=True)
    args=parser.parse_args()
    result=prepare_full(args.root,args.source_root,args.capacity_root)
    print(json.dumps(dict(manifest=c.digest(result["plan"]),resource=result["resource"])))


if __name__=="__main__":main()
