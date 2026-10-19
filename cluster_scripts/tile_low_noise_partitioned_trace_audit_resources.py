"""Resource estimates from successful fixed eight-worker trace-audit capacity."""
import argparse
import json
import math
from pathlib import Path
import re

import calibration as c
import tile_low_noise_partitioned_trace_audit as r
import tile_low_noise_trace_audit_resources as original

WARNING="Resource extrapolation only. Eight-worker capacity does not measure 96-worker I/O contention; the factor of two is not a completion guarantee. Sampling failures cannot supply a full-work capacity profile. Exceeding one-node limits requires a separate partition design."


capacity_resources = original.capacity_resources
resource_plan = original.resource_plan


def measured_capacity(root,source,full_plan):
    root,source=r.separate_roots(root,source)
    cap,sampling=r.read_plan(root,source)
    terminal=r.read_terminal(root,cap)
    proof=dict(terminal["input_sha256"])
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
    if r.read_terminal(root,cap)!=terminal:
        raise ValueError("capacity terminal receipt changed")
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
