"""Audit all sixteen original WSS conditions once, also measuring audit resources."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import time
import traceback

import calibration as c
import audit_tile_weight_reference as audit

THREADS={key:"1" for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")}
WARNING="Original reference plans and all sixteen outcomes retained. Full raw draws and counts are audited, but labels are re-decoded only at the original first-16-plus-last checkpoints. No independent decoder proof or nominal coverage guarantee. Initial resource request is a ceiling, not a measured prediction."


def source_hashes():
    return dict(audit.source_hashes(),**{str(Path(__file__).resolve()):c.file_hash(__file__)})


def make_plan(reference_root,evidence):
    context=evidence["context"]
    if context["purpose"]!="weight_reference_production" or len(context["reference"]["conditions"])!=16:
        raise ValueError("unchanged full sixteen-condition reference required")
    return dict(schema=1,purpose="full_weight_reference_audit",reference_root=str(Path(reference_root).resolve()),
                reference_context=context,reference_plan_digest=evidence["reference_plan_digest"],
                input_sha256=evidence["input_sha256"],source_sha256=source_hashes(),
                native_profile_digest=evidence["native_profile_digest"],
                actual_native_profile_digest=evidence["actual_native_profile_digest"],
                original_pbs_job_id=evidence["pbs_job_id"],conditions=list(range(16)),workers=16,
                required_threads=THREADS,resources=dict(requested_nodes=1,cpus=96,memory_gb=340,
                    wall_seconds=86400,walltime="24:00:00",max_nodes=2,measured=False),warning=WARNING)


def prepare(root,reference_root):
    root,reference_root=Path(root).resolve(),Path(reference_root).resolve()
    if root==reference_root or root.is_relative_to(reference_root):
        raise ValueError("audit output cannot be inside reference root")
    if root.exists() and any(root.iterdir()): raise ValueError("new empty audit root required")
    evidence=audit.read_evidence(reference_root)
    plan=make_plan(reference_root,evidence)
    root.mkdir(parents=True,exist_ok=True)
    c.atomic_json(root/"manifest.json",plan)
    return plan


def read_plan(root,reference_root):
    root,reference_root=Path(root).resolve(),Path(reference_root).resolve()
    if root==reference_root or root.is_relative_to(reference_root):
        raise ValueError("audit output cannot be inside reference root")
    path=root/"manifest.json"
    if not path.resolve().is_relative_to(root): raise ValueError("audit manifest escapes root")
    saved=json.loads(path.read_text())
    expected=make_plan(reference_root,audit.read_evidence(reference_root))
    if c.canonical(saved)!=c.canonical(expected):
        raise ValueError("audit plan, reference context, source or native binding changed")
    return saved


def report_binding(plan,index,report):
    context=plan["reference_context"]
    spec=context["reference"]["conditions"][index]
    condition=report["condition"]
    if (report["context_digest"]!=c.digest(context) or c.canonical(report["context"])!=c.canonical(context)
            or report["reference_plan_digest"]!=plan["reference_plan_digest"]
            or report["native_profile_digest"]!=plan["native_profile_digest"]
            or report["actual_native_profile_digest"]!=plan["actual_native_profile_digest"]
            or report["pbs_job_id"]!=plan["original_pbs_job_id"]
            or condition["condition"]!=index or condition["case"]!=spec["case"]
            or condition["physical_decoder_prior"]!=spec["physical_decoder_prior"]
            or report["available_labels"]!=condition["available_trials"]
            or report["checked_labels"]!=sum(len(chunk["checked_indices"]) for chunk in report["chunk_checks"])
            or not 0<=report["checked_labels"]<=report["available_labels"]
            or any(report[key] is not True for key in ("raw_reference_audited","raw_draws_regenerated",
                "raw_artifact_hashes_verified","summary_reproduced","native_platform_verified"))
            or report["all_labels_redecoded"] is not False
            or report["source_sha256"]!=audit.source_hashes()
            or any(report["input_sha256"].get(name)!=digest for name,digest in plan["input_sha256"].items())):
        raise ValueError("condition audit report differs from fixed reference evidence")


def audit_task(args):
    root,reference_root,plan,index=args
    root,reference_root=Path(root),Path(reference_root)
    if type(index) is not int or index not in plan["conditions"]:
        raise ValueError("invalid audit condition")
    path=root/"conditions"/str(index)
    if any(path.parent.glob(str(index)+".*")):
        raise ValueError("existing condition audit; no automatic rerun")
    started,cpu=time.perf_counter(),time.process_time()
    spec=plan["reference_context"]["reference"]["conditions"][index]
    record=dict(condition=index,case=spec["case"],physical_decoder_prior=spec["physical_decoder_prior"],
                status="ok",available_labels=None,checked_labels=None,reference_available=False,
                all_labels_redecoded=False,planned_trials=sum(layer["trials"] for layer in spec["layers"]),
                original_reference_context=c.digest(plan["reference_context"]))
    try:
        if source_hashes()!=plan["source_sha256"]: raise ValueError("audit source changed")
        report=audit.audit_saved_condition(reference_root,index)
        report_binding(plan,index,report)
        byte_count=0
        for name in report["input_sha256"]:
            if name.startswith("chunks/"):
                item=reference_root/name
                if not item.resolve().is_relative_to(reference_root.resolve()): raise ValueError("reference artifact escapes root")
                byte_count+=item.stat().st_size
        record.update(report=report,available_labels=report["available_labels"],checked_labels=report["checked_labels"],
                      reference_available=report["condition"]["available"],raw_artifact_bytes=byte_count,
                      chunks=len(report["chunk_checks"]))
        if source_hashes()!=plan["source_sha256"]: raise ValueError("audit source changed during task")
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc(),reference_available=False)
    record.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
                  peak_rss_mb=c.peak_rss_mb(),warning=WARNING)
    c.save_artifact(path,dict(manifest=c.digest(plan),condition=index),{},record)
    return {key:value for key,value in record.items() if key!="report"}


def run(root,reference_root):
    root,reference_root=Path(root).resolve(),Path(reference_root).resolve()
    job=os.environ.get("PBS_JOBID")
    if (not job or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job)
            or any(os.environ.get(key)!=value for key,value in THREADS.items())):
        raise ValueError("qsub and pinned single-thread environment required")
    plan=read_plan(root,reference_root)
    if any((root/name).exists() or (root/name).is_symlink()
           for name in ("execution-intent.json","native_preflight.json","conditions","summary.json")):
        raise ValueError("existing audit evidence; automatic rerun forbidden")
    intent=dict(manifest=c.digest(plan),reference_context=c.digest(plan["reference_context"]),
                reference_root=str(reference_root),conditions=plan["conditions"],workers=16,
                pbs_job_id=job,hostname=socket.gethostname())
    with (root/"execution-intent.json").open("xb") as stream: stream.write(c.canonical(intent)+b"\n")
    profile=json.loads((reference_root/"platform_profile.json").read_text())
    fixture=json.loads((reference_root/"platform_fixture.json").read_text())
    current=audit.driver.native_probe.probe(fixture)
    audit.driver.trace_audit.validate_platform(profile,current)
    if c.digest(current)!=plan["actual_native_profile_digest"]:
        raise ValueError("native profile changed before audit workers")
    c.atomic_json(root/"native_preflight.json",dict(**intent,profile=current,
                  original_pbs_job_id=plan["original_pbs_job_id"]))
    started=time.perf_counter()
    records=c.parallel_map(audit_task,[(str(root),str(reference_root),plan,index) for index in plan["conditions"]],16)
    records.sort(key=lambda record:record["condition"])
    if [record["condition"] for record in records]!=plan["conditions"]:
        raise ValueError("missing or duplicate condition audit outcome")
    hashes={}
    phase_failures=[]
    for record in records:
        index=record["condition"]
        path=root/"conditions"/str(index)
        marker=path.with_suffix(".done.json")
        try:
            if not marker.exists() or set(json.loads(marker.read_text())["sha256"])!={".json",".npz"}:
                raise ValueError("incomplete condition audit artifact")
            hashes[str(index)]=c.file_hash(marker)
            arrays,raw=c.load_artifact(path,dict(manifest=c.digest(plan),condition=index))
            if arrays or c.canonical(record)!=c.canonical({key:value for key,value in raw.items() if key!="report"}):
                raise ValueError("condition outcome differs from saved audit")
            if raw["status"]=="ok":
                report=raw["report"]
                try:
                    report_binding(plan,index,report)
                except Exception as error:
                    phase_failures.append(dict(stage="condition_report_binding",condition=index,error=repr(error)))
                # Include every completed condition's raw chunks and individual
                # summary even after a separate report-binding failure.
                audit.verify_unchanged(reference_root,report["input_sha256"],report["source_sha256"])
            elif raw["status"]!="failed" or not raw.get("error"):
                raise ValueError("invalid failed audit status")
        except Exception as error:
            phase_failures.append(dict(stage="condition_terminal_binding",condition=index,error=repr(error)))
    # A terminal binding failure invalidates the phase but does not erase outcomes.
    try:
        if c.canonical(read_plan(root,reference_root))!=c.canonical(plan):
            raise ValueError("reference changed during audit phase")
    except Exception as error:
        phase_failures.append(dict(stage="global_terminal_binding",error=repr(error)))
    phase_failure="; ".join(item["error"] for item in phase_failures) if phase_failures else None
    successful=[record for record in records if record["status"]=="ok"]
    summary=dict(**intent,tasks=16,failed=len(records)-len(successful),records=records,
                 reference_available_conditions=sum(record["reference_available"] for record in records),
                 available_labels=sum(record["available_labels"] for record in successful),
                 checked_labels=sum(record["checked_labels"] for record in successful),
                 all_labels_redecoded=False,all_conditions_audited=len(successful)==16 and phase_failure is None,
                 terminal_binding_valid=phase_failure is None,phase_failure=phase_failure,phase_failures=phase_failures,
                 raw_artifact_bytes=sum(record["raw_artifact_bytes"] for record in successful),
                 phase_wall_seconds=time.perf_counter()-started,condition_marker_sha256=hashes,
                 native_preflight_sha256=c.file_hash(root/"native_preflight.json"),
                 execution_intent_sha256=c.file_hash(root/"execution-intent.json"),warning=WARNING)
    c.atomic_json(root/"summary.json",summary)
    if phase_failure: raise RuntimeError("terminal binding failed; all condition outcomes retained")
    if summary["failed"]: raise RuntimeError("failed condition audits retained; no automatic retry")
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--reference-root",type=Path,required=True)
    args=parser.parse_args()
    if args.command=="plan":
        result=prepare(args.root,args.reference_root)
        print(json.dumps(dict(manifest=c.digest(result),conditions=16,workers=16,resources=result["resources"])))
    else:
        result=run(args.root,args.reference_root)
        print(json.dumps({key:value for key,value in result.items() if key!="records"}))


if __name__=="__main__": main()
