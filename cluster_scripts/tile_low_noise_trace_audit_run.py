"""Fresh PBS cohorts auditing full-dimensional low-noise production traces."""
import argparse
import itertools
import json
import os
from pathlib import Path
import socket
import time
import traceback

import calibration as c
import tile_low_noise_study as low
import tile_low_noise_analysis as analysis
import audit_tile_low_noise_traces as audit

THREADS=low.native.THREADS
REDUCED_KEYS=("task","status","wall_seconds","cpu_seconds","peak_rss_mb")
WARNING=audit.WARNING+" Capacity audits production replicates 0/1 with all rungs/chains; it is not the one-chain sampling-capacity plan."


def source_hashes():
    modules=(c,low,low.t,analysis,audit,audit.original,audit.platform_probe)
    result={str(Path(module.__file__).resolve()):c.file_hash(module.__file__) for module in modules}
    result[str(Path(__file__).resolve())]=c.file_hash(__file__)
    return result


def make_plan(sampling,platform_profile,platform_fixture,*,capacity,workers,completed_evidence,input_sha256=None):
    if type(capacity) is not bool or type(workers) is not int or not 1<=workers<=96:
        raise ValueError("explicit capacity flag and 1..96 integer workers required")
    expected=low.make_plan(sampling["case"],sampling["target_index"],capacity=False)
    if (sampling["purpose"]!="low_noise_production" or sampling["replicates"]!=192
            or c.canonical(sampling)!=c.canonical(expected)):
        raise ValueError("fixed full production sampling manifest required")
    values=dict(platform_profile=platform_profile,platform_fixture=platform_fixture)
    if ({key:c.digest(value) for key,value in values.items()}!=sampling["native_input_digests"]
            or platform_profile["fixture"]!=c.digest(platform_fixture) or not platform_profile["native_ldpc_sha256"]):
        raise ValueError("native profile/fixture binding differs")
    return dict(schema=1,purpose="low_noise_trace_audit_capacity" if capacity else "low_noise_trace_audit_full",
                case=sampling["case"],target_index=sampling["target_index"],replicates=2 if capacity else 192,
                workers=workers,sampling_manifest=c.digest(sampling),native_input_digests=sampling["native_input_digests"],
                completed_phase_evidence=completed_evidence,input_sha256=input_sha256 or {},
                runtime=low.t.runtime(),source_sha256=source_hashes(),required_threads=THREADS,warning=WARNING)


def groups(plan):
    return [(plan["case"],plan["target_index"],*tail)
            for tail in itertools.product(range(2),range(2),range(plan["replicates"]))]


def tasks_for_group(sampling,group):
    spec=sampling["condition"]
    return ((*group,rung,chain) for rung,chain in itertools.product(range(len(spec["rungs"])),range(spec["chains"])))


def path_in(root,name):
    path=Path(root)/name
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("input path escapes root")
    return path


def sampling_snapshot(source):
    names=["manifest.json","platform_profile.json","platform_fixture.json"]
    for phase in ("sample","anchors"):
        names.extend((f"{phase}-summary.json",f"{phase}-execution-intent.json",f"preflight-{phase}/native_preflight.json"))
    return {name:c.file_hash(path_in(source,name)) for name in names}


def separate_roots(root,source):
    root,source=Path(root).resolve(),Path(source).resolve()
    if root.is_relative_to(source) or source.is_relative_to(root):
        raise ValueError("audit and sampling roots must be separate")
    return root,source


def prepare(root,source,*,capacity,workers=96):
    root,source=separate_roots(root,source)
    if root.exists() and any(root.iterdir()):raise ValueError("new empty audit root required")
    sampling=analysis.read_production_plan(source)
    profile=json.loads(path_in(source,"platform_profile.json").read_text())
    fixture=json.loads(path_in(source,"platform_fixture.json").read_text())
    before=sampling_snapshot(source)
    evidence=analysis.completed_phase_evidence(source,sampling)
    if before!=sampling_snapshot(source):raise ValueError("sampling evidence changed")
    plan=make_plan(sampling,profile,fixture,capacity=capacity,workers=workers,
                   completed_evidence=evidence,input_sha256=before)
    for name,value in (("manifest",plan),("sampling_manifest",sampling),("platform_profile",profile),("platform_fixture",fixture)):
        c.atomic_json(root/(name+".json"),value)
    return plan


def read_plan(root,source):
    root,source=separate_roots(root,source)
    plan=json.loads(path_in(root,"manifest.json").read_text())
    if plan["purpose"] not in ("low_noise_trace_audit_capacity","low_noise_trace_audit_full"):
        raise ValueError("audit purpose differs")
    sampling=json.loads(path_in(root,"sampling_manifest.json").read_text())
    if c.canonical(sampling)!=c.canonical(analysis.read_production_plan(source)):
        raise ValueError("sampling manifest changed")
    profile=json.loads(path_in(root,"platform_profile.json").read_text())
    fixture=json.loads(path_in(root,"platform_fixture.json").read_text())
    before=sampling_snapshot(source)
    evidence=analysis.completed_phase_evidence(source,sampling)
    expected=make_plan(sampling,profile,fixture,capacity=plan["purpose"]=="low_noise_trace_audit_capacity",
                       workers=plan["workers"],completed_evidence=evidence,input_sha256=before)
    if before!=sampling_snapshot(source) or c.canonical(plan)!=c.canonical(expected):
        raise ValueError("audit plan/source or completed sampling evidence changed")
    return plan,sampling


def run_group(args):
    source,root,sampling,plan,group=args
    source,root=Path(source),Path(root)
    group=tuple(group)
    if group not in groups(plan):raise ValueError("group outside fixed cohort")
    path=root/"audit/groups"/c.task_id(group)
    measure=root/"measurements"/c.task_id(group)
    if any(base.with_suffix(ext).exists() for base in (path,measure) for ext in (".json",".npz",".done.json")):
        raise ValueError("cached/partial audit cannot be a fresh measurement")
    started,cpu=time.perf_counter(),time.process_time()
    tasks=list(tasks_for_group(sampling,group))
    rows=[];reduced=[];hashes={};construction_error=None
    try:
        spec=sampling["condition"]
        code,problem=low.t.build_problem(spec["size"],spec["noise"],spec["target"])
    except Exception as error:
        construction_error=repr(error)
    for task in tasks:
        item=dict(task=list(task),audit_status="failed",sampling_status=None)
        try:
            if construction_error is not None:raise ValueError(construction_error)
            base=path_in(source,"traces/"+c.task_id(task))
            current={ext:c.file_hash(path_in(source,str(base.with_suffix(ext).relative_to(source))))
                     for ext in (".done.json",".json",".npz")}
            marker=json.loads(base.with_suffix(".done.json").read_text())
            if marker.get("sha256")!={ext:current[ext] for ext in (".json",".npz")}:
                raise ValueError("complete valid payload checksum set required")
            loaded=c.load_artifact(base,dict(manifest=c.digest(sampling),task=list(task)))
            if loaded is None:raise ValueError("missing task artifact")
            arrays,record=loaded
            reduced.append({key:record[key] for key in REDUCED_KEYS})
            result=audit.audit_task(sampling,task,arrays,record,code,problem)
            for ext,digest in current.items():
                name=str(base.with_suffix(ext).relative_to(source))
                if c.file_hash(path_in(source,name))!=digest:
                    raise ValueError("trace input changed during audit")
                hashes[name]=digest
            item.update(audit_status="ok",sampling_status=record["status"],result=result)
        except Exception as error:
            item.update(error=repr(error),traceback=traceback.format_exc())
        rows.append(item)
    digest_ok=c.digest(reduced)==plan["completed_phase_evidence"]["sample"]["group_record_digests"][c.task_id(group)]
    failed=sum(row["audit_status"]!="ok" for row in rows)
    group_result=dict(group=list(group),tasks=rows,planned_tasks=len(tasks),failed_audits=failed,
        failed_sampling=sum(row["sampling_status"]=="failed" for row in rows),
        redecoded_checkpoints=sum(row.get("result",{}).get("redecoded_checkpoints",0) for row in rows),
        summary_group_digest_verified=digest_ok,input_sha256=hashes,all_physical_states_redecoded=False,
        status="ok" if failed==0 and digest_ok else "failed",warning=WARNING)
    identity=dict(manifest=c.digest(plan),group=list(group))
    c.save_artifact(path,identity,{},group_result)
    record={key:group_result[key] for key in ("group","status","planned_tasks","failed_audits","failed_sampling","redecoded_checkpoints","summary_group_digest_verified")}
    record.update(audit_marker_sha256=c.file_hash(path.with_suffix(".done.json")),wall_seconds=time.perf_counter()-started,
                  cpu_seconds=time.process_time()-cpu,peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(measure,identity,{},record)
    return record


def verify_group_inputs(source,root,plan,record):
    base=Path(root)/"audit/groups"/c.task_id(record["group"])
    if c.file_hash(base.with_suffix(".done.json"))!=record["audit_marker_sha256"]:
        raise ValueError("audit group artifact changed")
    _,result=c.load_artifact(base,dict(manifest=c.digest(plan),group=record["group"]))
    for name,digest in result["input_sha256"].items():
        if c.file_hash(path_in(source,name))!=digest:raise ValueError("trace input changed during cohort audit")


def run(root,source):
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(k)!=v for k,v in THREADS.items()):
        raise ValueError("PBS and pinned single-thread environment required")
    root,source=separate_roots(root,source)
    plan,sampling=read_plan(root,source)
    if any((root/name).exists() for name in ("execution-intent.json","native_preflight.json","audit","measurements","summary.json")):
        raise ValueError("existing audit execution; no automatic rerun")
    intent=dict(manifest=c.digest(plan),sampling_manifest=c.digest(sampling),workers=plan["workers"],
                pbs_job_id=os.environ["PBS_JOBID"],hostname=socket.gethostname())
    with (root/"execution-intent.json").open("xb") as stream:stream.write(c.canonical(intent)+b"\n")
    native=audit.validate_native_environment(sampling,
        platform_profile=json.loads((root/"platform_profile.json").read_text()),
        platform_fixture=json.loads((root/"platform_fixture.json").read_text()))
    c.atomic_json(root/"native_preflight.json",dict(intent,evidence=native))
    started=time.perf_counter()
    expected=groups(plan)
    records=c.parallel_map(run_group,[(str(source),str(root),sampling,plan,g) for g in expected],plan["workers"])
    records.sort(key=lambda row:row["group"])
    if [tuple(row["group"]) for row in records]!=expected:raise ValueError("missing or duplicate audit group")
    changes=[]
    for record in records:
        try:verify_group_inputs(source,root,plan,record)
        except Exception as error:changes.append(dict(group=record["group"],error=repr(error)))
    context_error=None
    try:
        if c.digest(read_plan(root,source)[0])!=c.digest(plan):raise ValueError("audit context changed")
    except Exception as error:context_error=repr(error)
    failed={tuple(row["group"]) for row in records if row["status"]!="ok"}|{tuple(row["group"]) for row in changes}
    result=dict(manifest=c.digest(plan),groups=len(expected),planned_tasks=sum(row["planned_tasks"] for row in records),
        failed_audit_groups=len(failed),failed_sampling=sum(row["failed_sampling"] for row in records),records=records,
        input_changes=changes,context_error=context_error,native_platform_verified=True,
        native_preflight_sha256=c.file_hash(root/"native_preflight.json"),all_physical_states_redecoded=False,
        phase_wall_seconds=time.perf_counter()-started,warning=WARNING)
    c.atomic_json(root/"summary.json",result)
    if failed or context_error:raise RuntimeError("audit failures/input changes retained in summary")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--capacity",action="store_true")
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    result=prepare(args.root,args.source_root,capacity=args.capacity,workers=args.workers) if args.command=="plan" else run(args.root,args.source_root)
    print(json.dumps({k:v for k,v in result.items() if k not in ("records","completed_phase_evidence")}))


if __name__=="__main__":main()
