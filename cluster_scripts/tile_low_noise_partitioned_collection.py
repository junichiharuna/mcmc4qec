"""Full final joins and reports for explicitly partitioned sampling provenance."""
import argparse
import json
import os
from pathlib import Path
import re
import socket

import calibration as c
import tile_low_noise_partitioned_analysis as p
import tile_low_noise_partitioned_trace_audit as r
import tile_low_noise_summary as description
import tile_low_noise_reference_comparison as comparison
from tile_low_noise_audited_collection import Evidence, verify_group, WARNING


def source_hashes():
    return {str(path): c.file_hash(path) for path in p.source_files((Path(__file__),Path(r.__file__))).values()}


def read_audited_collection(sampling_root,audit_root):
    """Fully validate and materialize a collection; performs full raw-file I/O."""
    source,root=Path(sampling_root).resolve(),Path(audit_root).resolve()
    sampling,iterator,collection=p.read_collection(source)
    rows=list(iterator)
    sources=source_hashes()
    plan,bound_sampling=r.read_plan(root,source)
    if (plan.get("mode")!="partitioned_sampling" or plan["purpose"]!="low_noise_trace_audit_full" or type(plan["replicates"]) is not int
            or plan["replicates"]!=192 or c.canonical(sampling)!=c.canonical(bound_sampling)):
        raise ValueError("same full production sampling and full audit required")
    expected=r.groups(plan)
    if len(expected)!=768:raise ValueError("complete 768-group audit required")
    proof=Evidence((source,root))
    adapter_hash=c.file_hash(__file__)
    terminal=r.read_terminal(root,plan)
    for name,digest in terminal["input_sha256"].items():
        if proof.track(r.path_in(root,name))!=digest:raise ValueError("audit terminal evidence changed")
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
        p.partition_evidence(source,wrapper,part["index"],proof)
        for name in ("summary.json","execution-intent.json","native_preflight.json"):
            proof.track(r.path_in(source,f"analysis-partitions/{part['index']}/{name}"))
    totals=dict(tasks=0,failed_sampling=0,redecoded_checkpoints=0)
    anchors=set()
    for row in summary["records"]:
        group=tuple(row["group"])
        analysis,_=p.p.read_group(source,wrapper,group)
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
    if source_hashes()!=sources or c.file_hash(__file__)!=adapter_hash:raise ValueError("adapter source changed")
    evidence=dict(sampling_manifest=c.digest(sampling),collection_digest=c.digest(collection),
        audit_manifest=c.digest(plan),audit_summary_sha256=proof.hashes[str(root/"summary.json")],
        evidence_sha256=proof.hashes,evidence_resolved_paths=proof.targets,groups=768,planned_tasks=totals["tasks"],failed_sampling=totals["failed_sampling"],
        redecoded_checkpoints=totals["redecoded_checkpoints"],anchors=len(anchors),pbs_job_id=intent["pbs_job_id"],
        native_platform_verified=True,analysis_trace_markers_matched=True,current_trace_payloads_rehashed=True,
        anchor_artifacts_validated=True,anchor_mc_replayed=False,all_physical_states_redecoded=False,
        reference_audited=False,adapter_source_sha256=adapter_hash,source_sha256=sources,
        sampling_pbs_jobs=plan["completed_phase_evidence"]["pbs_jobs"],audit_terminal=terminal,warning=WARNING)
    return sampling,rows,evidence


def verify_final_inputs(evidence):
    for name,digest in evidence["evidence_sha256"].items():
        if (str(Path(name).resolve())!=evidence["evidence_resolved_paths"][name] or c.file_hash(name)!=digest):
            raise ValueError("audited collection input changed before publication")


def run(root,audit_root,output,*,reference_root=None):
    """Write one exclusive report after the full audited collection is consumed."""
    p.require_pbs()
    root,audit_root,output=Path(root).resolve(),Path(audit_root).resolve(),Path(output).absolute()
    inputs=[root,audit_root]
    if reference_root is not None:
        reference_root=Path(reference_root).resolve();inputs.append(reference_root)
    if output.exists() or output.is_symlink():raise ValueError("report output exists")
    if any(output.resolve().is_relative_to(path) for path in inputs):
        raise ValueError("report output must be outside input roots")
    sources=source_hashes()
    plan,rows,evidence=read_audited_collection(root,audit_root)
    reference_report=None
    if reference_root is None:
        result=description.summarize_rows(plan,rows)
    else:
        import audit_tile_weight_reference as audit
        manifest=reference_root/"manifest.json"
        manifest_hash=c.file_hash(manifest)
        context=json.loads(manifest.read_bytes())
        index=comparison.compatible_condition(plan,context)
        reference_report=audit.audit_saved_condition(reference_root,index)
        if (c.canonical(reference_report["context"])!=c.canonical(context)
                or reference_report["context_digest"]!=c.digest(context)
                or reference_report["reference_plan_digest"]!=c.digest(context["reference"])
                or reference_report["native_profile_digest"]!=plan["native_input_digests"]["platform_profile"]
                or reference_report["native_platform_verified"] is not True
                or reference_report["raw_reference_audited"] is not True
                or reference_report["all_labels_redecoded"] is not False
                or reference_report["condition"]["condition"]!=index or c.file_hash(manifest)!=manifest_hash):
            raise ValueError("reference audit does not bind the fixed requested condition")
        result=comparison.compare_rows(plan,rows,reference_report["condition"])
        audit.verify_unchanged(reference_root,reference_report["input_sha256"],reference_report["source_sha256"])
    if result["rows"]!=len(rows):raise ValueError("report row denominator differs")
    verify_final_inputs(evidence)
    if source_hashes()!=sources:raise ValueError("report source changed before publication")
    result.update(manifest=c.digest(plan),audited_collection=evidence,reference_audit=reference_report,
                  source_sha256=sources,pbs_job_id=os.environ["PBS_JOBID"],hostname=socket.gethostname(),
                  current_trace_payloads_rehashed=True,all_physical_states_redecoded=False,
                  anchor_mc_replayed=False,raw_reference_audited=reference_report is not None,
                  nominal_coverage_certified=False,population_rmse_certified=False)
    output.parent.mkdir(parents=True,exist_ok=True)
    if any(output.resolve().is_relative_to(path) for path in inputs):raise ValueError("output path changed")
    with output.open("xb") as stream:stream.write(c.canonical(result)+b"\n")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--audit-root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--reference-root",type=Path)
    args=parser.parse_args()
    result=run(args.root,args.audit_root,args.output,reference_root=args.reference_root)
    print(json.dumps(dict(rows=result["rows"],reference_audited=result["raw_reference_audited"])))


if __name__=="__main__":main()
