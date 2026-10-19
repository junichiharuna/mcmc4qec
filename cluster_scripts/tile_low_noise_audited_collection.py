"""Bind complete BAR collections to full saved-trace audit evidence."""
import json
from pathlib import Path
import re

import calibration as c
import tile_low_noise_analysis_partitions as p
import tile_low_noise_trace_audit_run as r

WARNING="Full trace payload hashes and analysis markers matched; only recorded initial/checkpoint states were re-decoded by the saved audit. Anchors receive artifact-integrity checks only, not MC replay. Reference auditing is separate. This does not certify decoder correctness, mixing, precision or coverage."


class Evidence:
    """Record file hashes and reject mutation before returning evidence."""
    def __init__(self,roots=None):
        self.hashes={}
        self.targets={}
        self.roots=None if roots is None else tuple(Path(root).resolve() for root in roots)

    def track(self,path):
        path=Path(path).absolute()
        target=path.resolve()
        if self.roots is not None and not any(path.is_relative_to(root) and target.is_relative_to(root) for root in self.roots):
            raise ValueError("evidence path escapes input roots")
        digest=c.file_hash(path)
        key=str(path)
        if key in self.hashes and (self.hashes[key]!=digest or self.targets[key]!=str(target)):
            raise ValueError("input changed during collection validation")
        self.hashes[key]=digest
        self.targets[key]=str(target)
        return digest

    def read(self,path):
        self.track(path)
        value=json.loads(Path(path).read_bytes())
        self.track(path)
        return value

    def artifact(self,base,identity):
        marker=self.read(base.with_suffix(".done.json"))
        if marker.get("identity")!=identity or set(marker.get("sha256",{}))!={".json",".npz"}:
            raise ValueError("artifact identity or checksum census differs")
        for ext,digest in marker["sha256"].items():
            if self.track(base.with_suffix(ext))!=digest:
                raise ValueError("artifact payload hash differs")
        value=c.load_artifact(base,identity)
        if value is None:raise ValueError("missing artifact")
        return value

    def finish(self):
        for name,digest in self.hashes.items():
            if str(Path(name).resolve())!=self.targets[name] or c.file_hash(name)!=digest:
                raise ValueError("input changed during collection validation")


def verify_group(source,root,plan,sampling,row,analysis,proof):
    """Check one saved group and its exact analysis input-marker join."""
    source,root=Path(source),Path(root)
    group=tuple(row["group"])
    identity=dict(manifest=c.digest(plan),group=list(group))
    arrays,measurement=proof.artifact(r.path_in(root,"measurements/"+c.task_id(group)),identity)
    if arrays or c.canonical(measurement)!=c.canonical(row):
        raise ValueError("measurement and full summary differ")
    base=r.path_in(root,"audit/groups/"+c.task_id(group))
    arrays,audited=proof.artifact(base,identity)
    if arrays or row["audit_marker_sha256"]!=proof.track(base.with_suffix(".done.json")):
        raise ValueError("audit marker or arrays differ")
    for key in ("group","status","planned_tasks","failed_audits","failed_sampling","redecoded_checkpoints","summary_group_digest_verified"):
        if audited[key]!=row[key]:raise ValueError("audit counts differ from measurement")
    tasks=list(r.tasks_for_group(sampling,group))
    if (analysis["group"]!=list(group) or row["status"]!="ok" or row["failed_audits"]!=0
            or row["summary_group_digest_verified"] is not True or audited["all_physical_states_redecoded"] is not False
            or [tuple(item["task"]) for item in audited["tasks"]]!=tasks or row["planned_tasks"]!=len(tasks)):
        raise ValueError("full audit group/task census differs")
    names={str(Path("traces")/(c.task_id(task)+ext)) for task in tasks for ext in (".done.json",".json",".npz")}
    if set(audited["input_sha256"])!=names:raise ValueError("audit input hash census differs")
    sample_keys={"sample/"+c.task_id(task) for task in tasks}
    if {key for key in analysis["input_artifact_markers"] if key.startswith("sample/")}!=sample_keys:
        raise ValueError("analysis sample census differs")
    failed=[];reduced=[];checked=0
    spec=sampling["condition"]
    checkpoints=len(range(0,spec["steps"],sampling["checkpoint_stride"]))
    if (spec["steps"]-1)%sampling["checkpoint_stride"]:checkpoints+=1
    for item,task in zip(audited["tasks"],tasks):
        name=c.task_id(task)
        base=r.path_in(source,"traces/"+name)
        marker_name=str(Path("traces")/(name+".done.json"))
        if analysis["input_artifact_markers"]["sample/"+name]!=audited["input_sha256"][marker_name]:
            raise ValueError("analysis and audited trace markers differ")
        for ext in (".done.json",".json",".npz"):
            if proof.track(base.with_suffix(ext))!=audited["input_sha256"][str(Path("traces")/(name+ext))]:
                raise ValueError("current trace payload differs from audit")
        marker=proof.read(base.with_suffix(".done.json"))
        if (marker.get("identity")!={"manifest":c.digest(sampling),"task":list(task)}
                or marker.get("sha256")!={ext:audited["input_sha256"][str(Path("traces")/(name+ext))] for ext in (".json",".npz")}):
            raise ValueError("trace marker identity/checksums differ")
        raw=proof.read(base.with_suffix(".json"))
        reduced.append({key:raw[key] for key in r.REDUCED_KEYS})
        result=item["result"]
        if (item["audit_status"]!="ok" or item["sampling_status"] not in ("ok","failed")
                or raw["status"]!=item["sampling_status"] or result["status"]!=raw["status"]
                or result["task"]!=list(task) or result["all_physical_states_redecoded"] is not False):
            raise ValueError("sampling/audit task status differs")
        if raw["status"]=="failed":
            failed.append(list(task))
            if not raw.get("error") or result.get("recorded_failure")!=raw["error"] or result["redecoded_checkpoints"]!=0:
                raise ValueError("recorded sampling failure differs")
        else:
            if (result["saved_steps"]!=spec["steps"] or result["redecoded_checkpoints"]!=checkpoints
                    or any(result[key] is not True for key in ("initial_state_checked","initial_coefficients_checked","recorded_seeds_checked"))):
                raise ValueError("saved checkpoint audit is incomplete")
            checked+=checkpoints
    if (failed!=analysis["failed_tasks"] or row["failed_sampling"]!=len(failed) or row["redecoded_checkpoints"]!=checked
            or c.digest(reduced)!=plan["completed_phase_evidence"]["sample"]["group_record_digests"][c.task_id(group)]):
        raise ValueError("failure census/checkpoints/completed sampling evidence differ")
    return dict(tasks=len(tasks),failed_sampling=len(failed),redecoded_checkpoints=checked)


def read_audited_collection(sampling_root,audit_root):
    """Fully validate and materialize a collection; performs full raw-file I/O."""
    source,root=Path(sampling_root).resolve(),Path(audit_root).resolve()
    sampling,iterator,collection=p.read_collection(source)
    rows=list(iterator)
    plan,bound_sampling=r.read_plan(root,source)
    if (plan["purpose"]!="low_noise_trace_audit_full" or type(plan["replicates"]) is not int
            or plan["replicates"]!=192 or c.canonical(sampling)!=c.canonical(bound_sampling)):
        raise ValueError("same full production sampling and full audit required")
    expected=r.groups(plan)
    if len(expected)!=768:raise ValueError("complete 768-group audit required")
    proof=Evidence((source,root))
    adapter_hash=c.file_hash(__file__)
    for name in ("manifest.json","sampling_manifest.json","platform_profile.json","platform_fixture.json"):
        proof.track(r.path_in(root,name))
    for name,digest in plan["input_sha256"].items():
        if proof.track(r.path_in(source,name))!=digest:raise ValueError("sampling input snapshot differs")
    summary=proof.read(root/"summary.json")
    if (summary["manifest"]!=c.digest(plan) or summary["groups"]!=768
            or [tuple(row["group"]) for row in summary["records"]]!=expected
            or summary["failed_audit_groups"]!=0 or summary["input_changes"] or summary["context_error"] is not None
            or summary["native_platform_verified"] is not True or summary["all_physical_states_redecoded"] is not False):
        raise ValueError("full audit completion differs")
    intent=proof.read(root/"execution-intent.json")
    native=proof.read(root/"native_preflight.json")
    if (intent.get("manifest")!=c.digest(plan) or intent.get("sampling_manifest")!=c.digest(sampling)
            or intent.get("workers")!=plan["workers"] or not intent.get("hostname")
            or not isinstance(intent.get("pbs_job_id"),str) or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",intent["pbs_job_id"])
            or {key:value for key,value in native.items() if key!="evidence"}!=intent
            or summary["native_preflight_sha256"]!=proof.track(root/"native_preflight.json")):
        raise ValueError("full audit native/PBS identity differs")
    actual=r.audit.validate_native_environment(sampling,
        platform_profile=proof.read(root/"platform_profile.json"),platform_fixture=proof.read(root/"platform_fixture.json"))
    if actual.get("native_platform_verified") is not True or actual!=native["evidence"]:
        raise ValueError("full audit native evidence differs from current platform")
    submission=proof.read(root/"submission.json")
    submitted=proof.read(root/"submission-intent.json")
    command=submission.get("command")
    if (submission.get("manifest")!=c.digest(plan) or submission.get("job_id")!=intent["pbs_job_id"]
            or {key:value for key,value in submission.items() if key!="job_id"}!=submitted
            or not isinstance(command,list) or len(command)!=2 or command[0]!="qsub"):
        raise ValueError("full audit submission ledger differs")
    script=Path(command[1])
    if not script.is_absolute() or not script.resolve().is_relative_to(root) or proof.track(script)!=submission["script_sha256"]:
        raise ValueError("full audit submission script differs")
    wrapper=p.read_plan(source)
    for name in ("analysis_manifest.json","partition_analysis_manifest.json","analysis-execution-intent.json",
                 "partition-collection/summary.json","partition-collection/rows.jsonl"):
        proof.track(r.path_in(source,name))
    for part in wrapper["resources"]["partitions"]:
        for name in ("summary.json","execution-intent.json","native_preflight.json"):
            proof.track(r.path_in(source,f"analysis-partitions/{part['index']}/{name}"))
    totals=dict(tasks=0,failed_sampling=0,redecoded_checkpoints=0)
    anchors=set()
    for row in summary["records"]:
        group=tuple(row["group"])
        analysis,_=p.read_group(source,wrapper,group)
        for ext in (".done.json",".json",".npz"):
            proof.track(r.path_in(source,"analysis/"+c.task_id(group)+ext))
        counts=verify_group(source,root,plan,sampling,row,analysis,proof)
        for key,value in counts.items():totals[key]+=value
        task=(group[0],group[1],0,0,group[4],0,0)
        name=c.task_id(task)
        base=r.path_in(source,"anchors/"+name)
        if analysis["input_artifact_markers"]["anchors/"+name]!=proof.track(base.with_suffix(".done.json")):
            raise ValueError("analysis anchor marker differs")
        if name not in anchors:
            _,record=proof.artifact(base,dict(manifest=c.digest(sampling),task=list(task)))
            if c.digest(record)!=plan["completed_phase_evidence"]["anchors"]["record_digests"][name]:
                raise ValueError("anchor differs from completed phase evidence")
            anchors.add(name)
    if (totals["tasks"]!=summary["planned_tasks"] or totals["failed_sampling"]!=summary["failed_sampling"]
            or len(anchors)!=192):raise ValueError("full audit/anchor denominator differs")
    after,again,after_collection=p.read_collection(source)
    if (c.canonical(after)!=c.canonical(sampling) or c.canonical(list(again))!=c.canonical(rows)
            or after_collection!=collection or c.canonical(r.read_plan(root,source)[0])!=c.canonical(plan)):
        raise ValueError("collection or audit context changed")
    proof.finish()
    if c.file_hash(__file__)!=adapter_hash:raise ValueError("adapter source changed")
    evidence=dict(sampling_manifest=c.digest(sampling),collection_digest=c.digest(collection),
        audit_manifest=c.digest(plan),audit_summary_sha256=proof.hashes[str(root/"summary.json")],
        evidence_sha256=proof.hashes,evidence_resolved_paths=proof.targets,groups=768,planned_tasks=totals["tasks"],failed_sampling=totals["failed_sampling"],
        redecoded_checkpoints=totals["redecoded_checkpoints"],anchors=len(anchors),pbs_job_id=intent["pbs_job_id"],
        native_platform_verified=True,analysis_trace_markers_matched=True,current_trace_payloads_rehashed=True,
        anchor_artifacts_validated=True,anchor_mc_replayed=False,all_physical_states_redecoded=False,
        reference_audited=False,adapter_source_sha256=adapter_hash,warning=WARNING)
    return sampling,rows,evidence
