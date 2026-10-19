"""Measured-resource partitions for the complete low-noise BAR cohort."""
import argparse
import itertools
import json
import math
import os
from pathlib import Path
import socket
import time

import calibration as c
import tile_low_noise_analysis as a
import tile_low_noise_analysis_capacity as cap
import tile_low_noise_study as low

WARNING="All planned groups and unavailable outcomes retained. Analysis artifacts and input-marker bindings are verified; raw trace rehashing and independent numerical re-decoding are separate audits."


def validate_partitions(plan,resource):
    expected=list(a.groups(plan))
    if (resource["production_manifest"]!=c.digest(plan) or resource["groups"]!=len(expected)
            or type(resource["workers"]) is not int or not 1<=resource["workers"]<=96
            or resource["cpus"]!=96 or not 0<resource["memory_gb"]<=340 or resource["max_nodes"]!=2):
        raise ValueError("partition resource or production manifest differs")
    parts=resource["partitions"]
    flat=[]
    for index,part in enumerate(parts):
        seconds=part["wall_seconds"]
        if (part["index"]!=index or not part["groups"] or type(seconds) is not int
                or not 0<seconds<=86400 or seconds%1800
                or part["walltime"]!=f"{seconds//3600:02d}:{seconds%3600//60:02d}:00"):
            raise ValueError("partition index or walltime differs")
        flat.extend(tuple(group) for group in part["groups"])
    if flat!=expected or len(set(flat))!=len(expected):
        raise ValueError("partitions must preserve every planned group exactly once")


def create_plan(root,capacity_root):
    root,capacity_root=Path(root),Path(capacity_root).resolve()
    if any((root/name).exists() for name in ("partition_analysis_manifest.json","analysis-execution-intent.json",
                                            "analysis","analysis-summary.json","analysis-partitions","partition-collection")):
        raise ValueError("existing analysis intent/output; no automatic replacement")
    production=a.read_production_plan(root)
    capacity=json.loads((capacity_root/"manifest.json").read_text())
    if c.canonical(capacity["production"])!=c.canonical(production):
        raise ValueError("capacity production manifest differs")
    resource=cap.measured_profile(capacity_root,capacity)
    validate_partitions(production,resource)
    context=a.analysis_context(production,a.completed_phase_evidence(root,production))
    path=root/"analysis_manifest.json"
    if path.exists() and c.canonical(json.loads(path.read_text()))!=c.canonical(context):
        raise ValueError("existing analysis context differs")
    result=dict(schema=1,purpose="low_noise_partition_analysis",production=production,analysis_context=context,
                capacity_root=str(capacity_root),capacity_manifest=c.digest(capacity),resources=resource,
                sources=dict(partitions=c.file_hash(__file__),analysis=c.file_hash(a.__file__),capacity=c.file_hash(cap.__file__)),
                warning=WARNING)
    reservation=dict(mode="partitioned",partition_manifest=c.digest(result),manifest=c.digest(production),
                     warning="Routing reservation only; not PBS execution evidence.")
    with (root/"analysis-execution-intent.json").open("xb") as stream:
        stream.write(c.canonical(reservation)+b"\n")
    if not path.exists(): c.atomic_json(path,context)
    c.atomic_json(root/"partition_analysis_manifest.json",result)
    return result


def read_plan(root):
    root=Path(root)
    wrapper=json.loads((root/"partition_analysis_manifest.json").read_text())
    production=a.read_production_plan(root)
    if (wrapper["purpose"]!="low_noise_partition_analysis" or c.canonical(wrapper["production"])!=c.canonical(production)
            or wrapper["sources"]!={"partitions":c.file_hash(__file__),"analysis":c.file_hash(a.__file__),"capacity":c.file_hash(cap.__file__)}):
        raise ValueError("partition source or production plan differs")
    reservation=json.loads((root/"analysis-execution-intent.json").read_text())
    if (reservation.get("mode")!="partitioned" or reservation.get("pbs_job_id") is not None
            or reservation["partition_manifest"]!=c.digest(wrapper) or reservation["manifest"]!=c.digest(production)):
        raise ValueError("partition routing reservation differs")
    capacity_root=Path(wrapper["capacity_root"])
    capacity=json.loads((capacity_root/"manifest.json").read_text())
    if (c.digest(capacity)!=wrapper["capacity_manifest"] or c.canonical(capacity["production"])!=c.canonical(production)
            or cap.measured_profile(capacity_root,capacity)!=wrapper["resources"]):
        raise ValueError("measured capacity evidence differs")
    context=wrapper["analysis_context"]
    a.validate_context(production,context)
    if (c.canonical(json.loads((root/"analysis_manifest.json").read_text()))!=c.canonical(context)
            or a.completed_phase_evidence(root,production)!=context["completed_phase_evidence"]):
        raise ValueError("analysis context or sampling phase evidence differs")
    validate_partitions(production,wrapper["resources"])
    return wrapper


def validate_rows(plan,group,rows):
    expected=[(chains,burn,samples,label,"cross_chain" if block is None else "block",block)
              for chains,burn,samples,index,label,ladder,block in a.analysis_settings(plan)]
    observed=[]
    for row in rows:
        if (row["group"]!=list(group) or row["case"]!=group[0] or row["target_p"]!=plan["condition"]["target"]
                or row["replicate"]!=group[4] or row["kernel"]!=list(plan["kernels"])[group[2]]
                or row["init"]!=plan["initializations"][group[3]] or row["noise"]!=plan["condition"]["noise"]
                or row["n"]!=2*plan["condition"]["size"]**2 or row.get("reference") is not None
                or row.get("reference_available",False) is not False
                or any(type(row[key]) is not bool for key in ("available","undefined","flagged"))
                or row["available"]!=(row["interval"] is not None)):
            raise ValueError("analysis row identity or availability differs")
        if row["available"]:
            interval=row["interval"]
            if (len(interval)!=2 or any(not math.isfinite(value) for value in interval)
                    or not 0<interval[0]<=interval[1]<=1 or row.get("estimate") is None
                    or not 0<row["estimate"]<=1):
                raise ValueError("available interval or point differs")
        observed.append(tuple(row[key] for key in ("chains","burn","samples","ladder","method","block")))
    if observed!=expected:
        raise ValueError("all planned analysis rows must occur exactly once")


def read_group(root,wrapper,group):
    root=Path(root)
    plan,context=wrapper["production"],wrapper["analysis_context"]
    path=root/"analysis"/c.task_id(group)
    marker=path.with_suffix(".done.json")
    if not marker.exists(): raise ValueError("missing completed analysis group")
    marked=json.loads(marker.read_text())
    identity=marked["identity"]
    if (set(marked["sha256"])!={".json",".npz"} or set(identity)!={"analysis","group","input_artifact_markers"}
            or identity["analysis"]!=c.digest(context) or identity["group"]!=list(group)):
        raise ValueError("analysis artifact marker differs")
    arrays,record=c.load_artifact(path,identity)
    spec=plan["condition"]
    expected={f"sample/{c.task_id((*group,rung,chain))}" for rung,chain in
              itertools.product(range(len(spec["rungs"])),range(spec["chains"]))}
    expected.add(f"anchors/{c.task_id((group[0],group[1],0,0,group[4],0,0))}")
    inputs=identity["input_artifact_markers"]
    if (set(inputs)!=expected or record["input_artifact_markers"]!=inputs or record["group"]!=list(group)
            or record["status"]!="ok" or record["diagnostic_count"]!=len(record["diagnostics"])):
        raise ValueError("analysis group or input census differs")
    for key,digest in inputs.items():
        phase,task_id=key.split("/")
        marker_path=root/("traces" if phase=="sample" else "anchors")/(task_id+".done.json")
        if not marker_path.exists() or c.file_hash(marker_path)!=digest:
            raise ValueError("analysis input marker changed")
        item=json.loads(marker_path.read_text())
        if (item["identity"]!={"manifest":c.digest(plan),"task":[int(x) for x in task_id.split("-")]}
                or set(item["sha256"])!={".json",".npz"}):
            raise ValueError("analysis input marker identity differs")
    if set(arrays)!={item["acf_key"] for item in record["diagnostics"]}:
        raise ValueError("diagnostic ACF artifact keys differ")
    for item in record["diagnostics"]:
        values=arrays[item["acf_key"]]
        if (values.ndim!=2 or values.shape[0]!=item["chains"]
                or not 1<=values.shape[1]<=min(65,item["samples"])):
            raise ValueError("diagnostic ACF shape differs")
    failures=[tuple(task) for task in record["failed_tasks"]]
    if (len(set(failures))!=len(failures) or any(len(task)!=7 or task[:5]!=tuple(group)
            or not 0<=task[5]<len(spec["rungs"]) or not 0<=task[6]<spec["chains"] for task in failures)):
        raise ValueError("failed task census differs")
    validate_rows(plan,group,record["rows"])
    return record,c.file_hash(marker)


def run_partition(root,wrapper,index):
    root=Path(root)
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(key)!=value for key,value in low.native.THREADS.items()):
        raise ValueError("qsub and pinned single-thread environment required")
    if c.canonical(wrapper)!=c.canonical(read_plan(root)): raise ValueError("partition plan changed")
    parts=wrapper["resources"]["partitions"]
    if type(index) is not int or not 0<=index<len(parts): raise ValueError("invalid partition index")
    selected=parts[index]
    destination=root/"analysis-partitions"/str(index)
    if destination.exists() or any((root/"analysis"/(c.task_id(group)+ext)).exists()
                                   for group in selected["groups"] for ext in (".json",".npz",".done.json")):
        raise ValueError("existing partition evidence; automatic rerun forbidden")
    destination.mkdir(parents=True,exist_ok=False)
    plan,context=wrapper["production"],wrapper["analysis_context"]
    workers=wrapper["resources"]["workers"]
    intent=dict(partition_manifest=c.digest(wrapper),partition=index,groups=selected["groups"],workers=workers,
                manifest=c.digest(plan),pbs_job_id=os.environ["PBS_JOBID"],hostname=socket.gethostname())
    with (destination/"execution-intent.json").open("xb") as stream: stream.write(c.canonical(intent)+b"\n")
    for key in plan["native_input_digests"]:
        c.atomic_json(destination/(key+".json"),json.loads((root/(key+".json")).read_text()))
    native_hash=low.native.native_preflight(destination,plan)
    started=time.perf_counter()
    results=c.parallel_map(a.analyze_group,[(str(root),plan,context,tuple(group)) for group in selected["groups"]],workers)
    if sorted(tuple(record["group"]) for record in results)!=sorted(tuple(group) for group in selected["groups"]):
        raise ValueError("missing or duplicate completed partition group")
    hashes={}
    for group in selected["groups"]:
        raw,digest=read_group(root,wrapper,tuple(group))
        returned=next(record for record in results if record["group"]==group)
        if c.canonical(returned)!=c.canonical({key:value for key,value in raw.items() if key!="diagnostics"}):
            raise ValueError("worker return differs from saved group")
        hashes[c.task_id(group)]=digest
    summary=dict(**intent,native_preflight_sha256=native_hash,execution_intent_sha256=c.file_hash(destination/"execution-intent.json"),
                 group_marker_sha256=hashes,phase_wall_seconds=time.perf_counter()-started,
                 rows=sum(len(record["rows"]) for record in results),warning=WARNING)
    c.atomic_json(destination/"summary.json",summary)
    return summary


def partition_evidence(root,wrapper,index):
    destination=Path(root)/"analysis-partitions"/str(index)
    if not (destination/"summary.json").exists(): raise ValueError("missing partition completion; collection incomplete")
    summary=json.loads((destination/"summary.json").read_text())
    intent=json.loads((destination/"execution-intent.json").read_text())
    plan=wrapper["production"]
    selected=wrapper["resources"]["partitions"][index]
    if (set(intent)!={"partition_manifest","partition","groups","workers","manifest","pbs_job_id","hostname"}
            or summary["partition_manifest"]!=c.digest(wrapper) or summary["partition"]!=index
            or summary["groups"]!=selected["groups"] or summary["workers"]!=wrapper["resources"]["workers"]
            or summary["manifest"]!=c.digest(plan) or not summary["pbs_job_id"] or not summary["hostname"]
            or any(summary[key]!=value for key,value in intent.items())
            or summary["execution_intent_sha256"]!=c.file_hash(destination/"execution-intent.json")
            or summary["native_preflight_sha256"]!=c.file_hash(destination/"native_preflight.json")):
        raise ValueError("partition compute evidence differs")
    proof=json.loads((destination/"native_preflight.json").read_text())
    if any(proof[key]!=summary[key] for key in ("manifest","pbs_job_id","hostname")):
        raise ValueError("partition native execution identity differs")
    low.native.trace_audit.validate_platform(json.loads((Path(root)/"platform_profile.json").read_text()),proof["profile"])
    if set(summary["group_marker_sha256"])!={c.task_id(group) for group in selected["groups"]}:
        raise ValueError("partition group marker census differs")
    expected_rows=len(selected["groups"])*sum(1 for _ in a.analysis_settings(plan))
    if summary["rows"]!=expected_rows: raise ValueError("partition row denominator differs")
    return summary,c.file_hash(destination/"summary.json")


def validated_groups(root,wrapper):
    for part in wrapper["resources"]["partitions"]:
        summary,proof=partition_evidence(root,wrapper,part["index"])
        for group in part["groups"]:
            record,digest=read_group(root,wrapper,tuple(group))
            if digest!=summary["group_marker_sha256"][c.task_id(group)]:
                raise ValueError("group artifact changed after partition completion")
            yield record,part["index"],proof


def collection_counters():
    return dict(groups=0,rows=0,unavailable_intervals=0,undefined_diagnostics=0,flagged_rows=0,failed_sampling_groups=0)


def count_record(counters,record):
    counters["groups"]+=1
    counters["failed_sampling_groups"]+=bool(record["failed_tasks"])
    for row in record["rows"]:
        counters["rows"]+=1
        counters["unavailable_intervals"]+=not row["available"]
        counters["undefined_diagnostics"]+=row["undefined"]
        counters["flagged_rows"]+=row["flagged"]


def collect(root):
    root=Path(root)
    wrapper=read_plan(root)
    # Missing partitions are expected while jobs run; do not create partial output.
    for part in wrapper["resources"]["partitions"]:
        partition_evidence(root,wrapper,part["index"])
    destination=root/"partition-collection"
    destination.mkdir(exist_ok=False)
    counters=collection_counters()
    proofs={}
    rows_path=destination/"rows.jsonl"
    with rows_path.open("xb") as stream:
        for record,index,proof in validated_groups(root,wrapper):
            count_record(counters,record)
            proofs[str(index)]=proof
            for row in record["rows"]: stream.write(c.canonical(row)+b"\n")
    summary=dict(manifest=c.digest(wrapper["production"]),analysis=c.digest(wrapper["analysis_context"]),
                 partition_manifest=c.digest(wrapper),rows_sha256=c.file_hash(rows_path),partition_summary_sha256=proofs,
                 **counters,warning=WARNING)
    if counters["groups"]!=768: raise ValueError("complete 192-replicate cohort required")
    c.atomic_json(destination/"summary.json",summary)
    return summary


def read_collection(root):
    """Return verified metadata and an iterator; consume it fully to finish validation."""
    root=Path(root)
    wrapper=read_plan(root)
    destination=root/"partition-collection"
    summary=json.loads((destination/"summary.json").read_text())
    rows_path=destination/"rows.jsonl"
    if (summary["manifest"]!=c.digest(wrapper["production"]) or summary["analysis"]!=c.digest(wrapper["analysis_context"])
            or summary["partition_manifest"]!=c.digest(wrapper) or summary["rows_sha256"]!=c.file_hash(rows_path)):
        raise ValueError("collection manifest or rows hash differs")
    def iterator():
        counters=collection_counters()
        proofs={}
        with rows_path.open("r",encoding="utf-8") as stream:
            for record,index,proof in validated_groups(root,wrapper):
                count_record(counters,record)
                proofs[str(index)]=proof
                for row in record["rows"]:
                    line=stream.readline()
                    if not line or c.canonical(json.loads(line))!=c.canonical(row):
                        raise ValueError("collection row differs from raw group")
                    yield row
            if stream.read(): raise ValueError("unexpected collection rows")
        if (any(summary[key]!=value for key,value in counters.items()) or counters["groups"]!=768
                or summary["partition_summary_sha256"]!=proofs):
            raise ValueError("collection denominator or partition proof differs")
    return wrapper["production"],iterator(),summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run","collect"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--capacity-root",type=Path)
    parser.add_argument("--partition",type=int)
    args=parser.parse_args()
    if args.command=="plan":
        if args.capacity_root is None: raise ValueError("measured capacity root required")
        result=create_plan(args.root,args.capacity_root)
        print(json.dumps(dict(partition_manifest=c.digest(result),partitions=len(result["resources"]["partitions"]))))
    elif args.command=="run":
        print(json.dumps(run_partition(args.root,read_plan(args.root),args.partition)))
    else:
        print(json.dumps(collect(args.root)))


if __name__=="__main__": main()
