"""Audit one fixed weight-reference condition with checkpoint label validation.

The full-draw audit may be expensive. This module neither submits jobs nor
implicitly audits all conditions. Re-decoding uses the same pinned decoder;
it is not an independent decoder implementation validation.
"""
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import re

import numpy as np
import calibration as c
import tile_weight_reference as r
import tile_weight_reference_driver as driver

EXTENSIONS={".done.json",".json",".npz"}
WARNING="All raw draws/counts and artifact hashes checked for this condition; only fixed first-16-plus-last labels re-decoded with the same native decoder. No independent decoder proof or coverage guarantee."


def audit_condition(plan,index,inputs,summary,chunk_records):
    """Read a stream of raw artifact-byte mappings, then verify one summary."""
    if type(index) is not int or not 0<=index<len(plan["conditions"]):
        raise ValueError("unknown condition index")
    condition=plan["conditions"][index]
    size,noise=r.t.CASES[condition["case"]]
    _,problem=r.t.build_problem(size,noise,condition["physical_decoder_prior"])
    expected=list(r.tasks(plan,index))
    records={}
    for record in chunk_records:
        task=tuple(record["task"])
        if task in records:
            raise ValueError("duplicate chunk summary")
        records[task]=record
    if set(records)!=set(expected):
        raise ValueError("missing or extra chunk summary")
    checks=[]
    checked=available=0
    missing=object()
    def verified_inputs():
        nonlocal checked,available
        for task,raw in itertools.zip_longest(expected,inputs,fillvalue=missing):
            if task is missing or raw is missing:
                raise ValueError("missing or extra reference artifact")
            if set(raw)!=EXTENSIONS or any(not isinstance(value,bytes) for value in raw.values()):
                raise ValueError("complete raw marker/json/npz bytes required")
            hashes={key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}
            marker=json.loads(raw[".done.json"])
            if (marker.get("identity")!={"manifest":c.digest(plan),"task":list(task)}
                    or marker.get("sha256")!={key:hashes[key] for key in (".json",".npz")}):
                raise ValueError("artifact identity or payload checksum differs")
            record=json.loads(raw[".json"])
            if c.canonical(record)!=c.canonical(records[task]):
                raise ValueError("raw chunk and summary differ")
            with np.load(io.BytesIO(raw[".npz"]),allow_pickle=False) as archive:
                arrays={key:archive[key] for key in archive.files}
            # The existing aggregate validates spec, shape, all draws and counts
            # before requesting this generator's next item.
            yield arrays,record
            indices=[]
            if record["status"]=="ok":
                states,labels=arrays["states"],arrays["failure"]
                indices=np.unique(np.r_[np.arange(min(16,len(states))),len(states)-1]).tolist()
                actual=np.array([problem.is_faulty(states[i]) for i in indices],dtype=bool)
                if not np.array_equal(actual,labels[indices]):
                    raise ValueError("precommitted failure-label checkpoint differs")
                checked+=len(indices)
                available+=len(states)
            checks.append(dict(task=list(task),status=record["status"],checked_indices=indices,sha256=hashes))
    aggregate=r.aggregate_condition(plan,index,verified_inputs())
    if c.canonical(aggregate)!=c.canonical(summary):
        raise ValueError("saved condition summary differs from raw aggregation")
    return dict(condition=aggregate,reference_plan_digest=c.digest(plan),raw_reference_audited=True,
                raw_draws_regenerated=True,raw_artifact_hashes_verified=True,summary_reproduced=True,
                checked_labels=checked,available_labels=available,all_labels_redecoded=False,
                checkpoint_rule="unique indices: first min(16,n), plus n-1 for every successful chunk",
                chunk_checks=checks,warning=WARNING)


def source_hashes():
    modules=(c,r,r.t,r.w,driver,driver.p,driver.pilot_audit,driver.trace_audit,driver.native_probe)
    values={str(Path(module.__file__).resolve()):c.file_hash(module.__file__) for module in modules}
    values[str(Path(__file__).resolve())]=c.file_hash(__file__)
    return values


def read_evidence(root):
    """Bind saved inputs, all summary identities and a current native probe."""
    root=Path(root).resolve()
    hashes={}
    sources=source_hashes()
    def read(name):
        path=root/name
        if not path.resolve().is_relative_to(root):
            raise ValueError("reference input escapes root")
        raw=path.read_bytes()
        hashes[name]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    values=[read(key+".json") for key in driver.INPUTS]
    context=driver.make_context(*values)
    saved=read("manifest.json")
    if c.canonical(context)!=c.canonical(saved):
        raise ValueError("fixed reference context/source/runtime changed")
    plan=context["reference"]
    run=read("native_preflight_run.json")
    intent=read("submission_intent.json")
    ledger=read("submission.json")
    script=root/"weight_reference.sh"
    if not script.resolve().is_relative_to(root):
        raise ValueError("reference script escapes root")
    hashes["weight_reference.sh"]=c.file_hash(script)
    job=run.get("pbs_job_id")
    if (not isinstance(job,str) or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job)
            or not run.get("hostname") or run.get("manifest")!=c.digest(context)
            or ledger.get("job_id")!=job or ledger.get("manifest")!=c.digest(context)
            or ledger.get("script_sha256")!=hashes["weight_reference.sh"]
            or c.canonical({k:v for k,v in ledger.items() if k!="job_id"})!=c.canonical(intent)):
        raise ValueError("reference PBS execution/submission binding differs")
    profile,fixture=values[3:]
    driver.trace_audit.validate_platform(profile,run["profile"])
    actual=driver.native_probe.probe(fixture)
    driver.trace_audit.validate_platform(profile,actual)
    chunks=read("chunks_summary.json")
    summary=read("summary.json")
    for value in (chunks,summary):
        if (value.get("manifest")!=c.digest(context)
                or value.get("native_preflight_sha256")!=hashes["native_preflight_run.json"]):
            raise ValueError("reference summary/native evidence binding differs")
    tasks=list(r.tasks(plan))
    rows=chunks["records"]
    keys=[tuple(row["task"]) for row in rows]
    if (len(keys)!=len(tasks) or set(keys)!=set(tasks) or chunks["tasks"]!=len(tasks)
            or any(row["status"] not in ("ok","failed") for row in rows)
            or chunks["failed"]!=sum(row["status"]=="failed" for row in rows)):
        raise ValueError("missing, duplicate or invalid global chunk summary")
    indices=[row["condition"] for row in summary["records"]]
    count=len(plan["conditions"])
    if (len(indices)!=count or set(indices)!=set(range(count)) or summary["conditions"]!=count
            or summary["unavailable"]!=sum(not row["available"] for row in summary["records"])):
        raise ValueError("missing or duplicate reference condition summary")
    for row in summary["records"]:
        spec=plan["conditions"][row["condition"]]
        if row["case"]!=spec["case"] or row["physical_decoder_prior"]!=spec["physical_decoder_prior"]:
            raise ValueError("reference condition case/prior differs")
    for key in ("sampling_wall_seconds","aggregation_wall_seconds","phase_wall_seconds"):
        if not math.isfinite(summary[key]) or summary[key]<0:
            raise ValueError("invalid reference timing")
    verify_unchanged(root,hashes,sources)
    return dict(context=context,context_digest=c.digest(context),manifest_digest=c.digest(context),
                reference_plan_digest=c.digest(plan),input_sha256=hashes,source_sha256=sources,
                native_profile_digest=c.digest(profile),actual_native_profile_digest=c.digest(actual),
                native_platform_verified=True,pbs_job_id=job,chunks_summary=chunks,summary=summary,
                warning="Summary identities are global; raw audit covers only the explicitly selected condition.")


def verify_unchanged(root,hashes,sources):
    for name,digest in hashes.items():
        path=Path(root)/name
        if not path.resolve().is_relative_to(Path(root).resolve()) or c.file_hash(path)!=digest:
            raise ValueError("reference evidence changed during audit")
    if sources!=source_hashes():
        raise ValueError("audit/decoder source changed during audit")


def audit_saved_condition(root,index):
    """Return a bound condition report; no outputs or implicit whole-run scan."""
    root=Path(root).resolve()
    evidence=read_evidence(root)
    plan=evidence["context"]["reference"]
    if type(index) is not int or not 0<=index<len(plan["conditions"]):
        raise ValueError("unknown reference condition")
    path=root/f"condition-{index}.json"
    if not path.resolve().is_relative_to(root):
        raise ValueError("condition summary escapes root")
    raw=path.read_bytes()
    evidence["input_sha256"][path.name]=hashlib.sha256(raw).hexdigest()
    saved=json.loads(raw)
    global_saved=next(row for row in evidence["summary"]["records"] if row["condition"]==index)
    if c.canonical(saved)!=c.canonical(global_saved):
        raise ValueError("individual/global condition summaries differ")
    def inputs():
        for task in r.tasks(plan,index):
            base=root/"chunks"/c.task_id(task)
            payload={}
            for extension in EXTENSIONS:
                item=base.with_suffix(extension)
                if not item.resolve().is_relative_to(root):
                    raise ValueError("chunk artifact escapes root")
                payload[extension]=item.read_bytes()
            yield payload
    records=[row for row in evidence["chunks_summary"]["records"] if row["task"][0]==index]
    report=audit_condition(plan,index,inputs(),saved,records)
    for chunk in report["chunk_checks"]:
        for extension,digest in chunk["sha256"].items():
            name="chunks/"+c.task_id(chunk["task"])+extension
            evidence["input_sha256"][name]=digest
    verify_unchanged(root,evidence["input_sha256"],evidence["source_sha256"])
    report.update({key:value for key,value in evidence.items() if key not in ("summary","chunks_summary","warning")})
    return report
