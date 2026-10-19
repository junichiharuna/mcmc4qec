"""Partition unchanged low-noise tasks and bind their multiple PBS executions."""
import argparse
import ast
from collections import defaultdict
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time
import traceback

import calibration as c
import tile_low_noise_study as low
import tile_low_noise_analysis as analysis
import submit_tile_low_noise as original_submit

PHASES = ("anchors", "sample")
REDUCED = ("task", "status", "wall_seconds", "cpu_seconds", "peak_rss_mb")
WARNING = ("Partitioning preserves every original task, seed and shared anchor. All recorded failures remain in the denominator. "
           "Resource extrapolation is not a completion guarantee. Multiple real PBS receipts are required; no aggregate job is "
           "represented as the generator. Metadata collection is distinct from full checkpoint audit and scientific accuracy.")


def source_files(*root_paths):
    directory = Path(__file__).resolve().parent
    pending = [Path(path).resolve() for path in root_paths] if root_paths else [Path(__file__).resolve(), directory / "submit_tile_low_noise_sampling_partitions.py"]
    result = {}
    while pending:
        path = pending.pop()
        if path.name in result: continue
        if not path.is_file() or path.parent != directory: raise ValueError("source outside cluster_scripts")
        result[path.name] = path
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            names = ([item.name.split(".")[0] for item in node.names] if isinstance(node, ast.Import)
                     else [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            pending.extend(directory / (name + ".py") for name in names if (directory / (name + ".py")).is_file())
    return result


def source_hashes():
    return {str(path): c.file_hash(path) for path in source_files().values()}


def read_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def path_in(root, name):
    root = Path(root).resolve()
    path = root / name
    if not path.resolve().is_relative_to(root): raise ValueError("path escapes production root")
    return path


def snapshot_paths(root, names):
    return {name:dict(sha256=c.file_hash(path_in(root,name)),resolved=str(path_in(root,name).resolve())) for name in names}


def verify_snapshot(root, snapshot):
    for name, value in snapshot.items():
        path=path_in(root,name)
        if str(path.resolve())!=value["resolved"] or c.file_hash(path)!=value["sha256"]:
            raise ValueError("consumed metadata changed while reading: "+name)


def positive(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value > 0


def validate_measurements(cap, measurements):
    for phase in PHASES:
        data = measurements[phase]
        rows = data["records"]
        expected = sorted(low.tasks(cap, phase))
        if (data["manifest"] != c.digest(cap) or data["phase"] != phase or data["tasks"] != len(expected)
                or [tuple(row["task"]) for row in rows] != expected or data["failed"] != 0
                or not data.get("native_preflight_sha256") or any(row["status"] != "ok" for row in rows)
                or not positive(data["phase_wall_seconds"])):
            raise ValueError("complete successful capacity phase required")
        if any(not positive(row[key]) for row in rows for key in ("wall_seconds", "cpu_seconds", "peak_rss_mb")):
            raise ValueError("finite positive capacity resource measurements required")
        if data["phase_wall_seconds"] < max(row["wall_seconds"] for row in rows):
            raise ValueError("capacity phase cannot be shorter than its worker")


def resource_plan(plan, cap, measurements):
    if (plan["purpose"], cap["purpose"], plan["replicates"], cap["replicates"]) != ("low_noise_production", "low_noise_capacity", 192, 2):
        raise ValueError("fixed production and separate capacity required")
    differences = {key for key in set(plan) | set(cap) if plan.get(key) != cap.get(key)}
    if (differences != {"purpose", "replicates", "stages"}
            or plan["stages"] != dict(sample=151, anchors=152, analysis=153)
            or cap["stages"] != dict(sample=150, anchors=154, analysis=155)):
        raise ValueError("capacity conditions or seed stages differ")
    validate_measurements(cap, measurements)
    output = {}
    for phase in PHASES:
        data = measurements[phase]
        rows = data["records"]
        expected = sorted(low.tasks(cap, phase))
        peak = max(row["peak_rss_mb"] for row in rows)
        workers = min(96, math.floor((340-8)*1024/(1.5*peak)))
        if workers < 1: raise ValueError("one worker exceeds memory ceiling")
        memory = max(32, math.ceil(1.5*workers*peak/1024+8))
        maxima = {}
        for row in rows:
            task = row["task"]
            key = tuple(task[index] for index in (2, 3, 5))
            maxima[key] = max(maxima.get(key, 0.), row["wall_seconds"])
        per_rep = 4*len(plan["condition"]["rungs"])*plan["condition"]["chains"] if phase == "sample" else 1
        copies_per_rep = plan["condition"]["chains"] if phase == "sample" else 1
        chosen = None
        for count in range(1, 193):
            parts = []
            for index in range(count):
                start, stop = index*192//count, (index+1)*192//count
                tasks = (stop-start)*per_rep
                predicted = max(data["phase_wall_seconds"]*tasks/len(expected)*96/workers,
                                sum(maxima.values())*(stop-start)*copies_per_rep/workers, max(maxima.values()))
                seconds = 1800*math.ceil((2*predicted+600)/1800)
                parts.append(dict(index=index, replicate_range=[start, stop], tasks=tasks,
                                  predicted_seconds=predicted, wall_seconds=seconds,
                                  walltime=f"{seconds//3600:02d}:{seconds%3600//60:02d}:00"))
            if all(part["wall_seconds"] <= 86400 for part in parts):
                chosen = parts; break
        if chosen is None: raise ValueError("one replicate cannot fit; unchanged cohort is blocked")
        output[phase] = dict(workers=workers, cpus=96, memory_gb=memory, requested_nodes=1, max_nodes=2,
                             partitions=chosen, observed_peak_worker_rss_mb=peak,
                             capacity_summary_digest=c.digest(data), warning=WARNING)
    return output


def tasks_for_partition(wrapper, phase, index):
    if phase not in PHASES or type(index) is not int or not 0 <= index < len(wrapper["resources"][phase]["partitions"]):
        raise ValueError("invalid phase or partition")
    plan = wrapper["production"]
    start, stop = wrapper["resources"][phase]["partitions"][index]["replicate_range"]
    if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= 192:
        raise ValueError("invalid replicate interval")
    return [task for task in low.tasks(plan, phase) if start <= task[4] < stop]


def selected_job(data):
    keys = ("job_state", "Exit_status", "Submit_arguments", "Resource_List", "resources_used", "Job_Name", "stime", "mtime", "obittime", "exec_host", "exec_vnode")
    return {key: value for key, value in data.items() if key in keys}


def validate_capacity(capacity_root, receipt):
    root = Path(capacity_root).resolve()
    original_sources = source_hashes()
    cap = original_submit.read_plan(root)
    if cap["purpose"] != "low_noise_capacity": raise ValueError("sampling capacity required")
    hashes = {}
    def track(path):
        path = Path(path).resolve(); digest = c.file_hash(path); hashes[str(path)] = digest; return digest
    def read(path): track(path); return read_json(path)
    for name in ("manifest.json", "platform_profile.json", "platform_fixture.json"): track(root / name)
    ledger = read(root / "submission.json")
    job = ledger["job_id"]
    script = root / "low-noise.sh"
    terminal = read(receipt).get("Jobs", {}).get(job, {})
    if (ledger["manifest"] != c.digest(cap) or ledger["command"] != ["qsub", str(script)]
            or ledger["script_sha256"] != track(script) or terminal.get("job_state") != "F" or terminal.get("Exit_status") != 0
            or shlex.split(terminal.get("Submit_arguments", "")) != [str(script)]):
        raise ValueError("capacity PBS/ledger/script binding differs")
    production = low.make_plan(cap["case"], cap["target_index"], capacity=False)
    measurements = {phase: read(root / f"{phase}-summary.json") for phase in PHASES}
    # Validate measurement structure without imposing the rejected monolithic budget.
    validate_measurements(cap, measurements)
    _, problem = low.t.build_problem(cap["condition"]["size"], cap["condition"]["noise"], cap["condition"]["target"])
    common_execution = None
    for phase, data in measurements.items():
        native_path = root / f"preflight-{phase}/native_preflight.json"
        native = read(native_path)
        intent = read(root / f"{phase}-execution-intent.json")
        if (hashes[str(native_path)] != data["native_preflight_sha256"] or native["manifest"] != c.digest(cap)
                or native["pbs_job_id"] != job or not native["hostname"] or intent["phase"] != phase
                or any(intent[key] != native[key] for key in ("manifest", "pbs_job_id", "hostname"))):
            raise ValueError("capacity native/PBS execution differs")
        execution = (native["pbs_job_id"], native["hostname"])
        if common_execution is not None and common_execution != execution: raise ValueError("capacity phases used different jobs")
        common_execution = execution
        low.native.trace_audit.validate_platform(read_json(root / "platform_profile.json"), native["profile"])
        for row in data["records"]:
            task = tuple(row["task"])
            low.validate_task(cap, task, phase)
            base = root / ("traces" if phase == "sample" else "anchors") / c.task_id(task)
            marker = read(base.with_suffix(".done.json"))
            if marker.get("identity") != dict(manifest=c.digest(cap), task=list(task)) or set(marker["sha256"]) != {".json", ".npz"}:
                raise ValueError("capacity artifact identity differs")
            for ext in (".json", ".npz"):
                if track(base.with_suffix(ext)) != marker["sha256"][ext]: raise ValueError("capacity payload changed")
            _, record = c.load_artifact(base, marker["identity"])
            actual = {key: record[key] for key in row} if phase == "sample" else record
            if c.canonical(actual) != c.canonical(row): raise ValueError("capacity summary/raw task differ")
            analysis.validate_record(cap, task, phase, record, problem)
    if any(c.file_hash(path) != digest for path, digest in hashes.items()): raise ValueError("capacity inputs changed")
    if source_hashes()!=original_sources or c.canonical(original_submit.read_plan(root))!=c.canonical(cap):
        raise ValueError("capacity source/runtime changed during validation")
    return dict(capacity=cap, production=production, measurements=measurements, input_sha256=hashes,
                pbs_job_id=job, completion=selected_job(terminal), source_sha256=original_sources)


def prepare(root, capacity_root, capacity_receipt):
    root, capacity_root = Path(root).resolve(), Path(capacity_root).resolve()
    if root.exists() or root.is_relative_to(capacity_root) or capacity_root.is_relative_to(root):
        raise ValueError("new independent production root required")
    proof = validate_capacity(capacity_root, capacity_receipt)
    plan = proof["production"]
    resources = resource_plan(plan, proof["capacity"], proof["measurements"])
    wrapper = dict(schema=1, purpose="low_noise_partitioned_sampling", production=plan, capacity_root=str(capacity_root),
                   capacity_evidence=proof, resources=resources, source_sha256=source_hashes(), warning=WARNING)
    root.mkdir(parents=True, exist_ok=False)
    for name in ("platform_profile", "platform_fixture"):
        c.atomic_json(root / (name + ".json"), read_json(capacity_root / (name + ".json")))
    c.atomic_json(root / "manifest.json", plan)
    c.atomic_json(root / "sampling_partition_manifest.json", wrapper)
    for phase in PHASES:
        with (root / f"{phase}-execution-intent.json").open("xb") as stream:
            stream.write(c.canonical(dict(mode="partitioned", phase=phase, manifest=c.digest(plan),
                                         partition_manifest=c.digest(wrapper))) + b"\n")
    return wrapper


def read_plan(root):
    root = Path(root).resolve()
    wrapper = read_json(path_in(root, "sampling_partition_manifest.json"))
    plan = analysis.read_production_plan(root)
    proof = wrapper["capacity_evidence"]
    if (wrapper["purpose"] != "low_noise_partitioned_sampling" or c.canonical(wrapper["production"]) != c.canonical(plan)
            or wrapper["source_sha256"] != source_hashes() or proof["source_sha256"] != source_hashes()
            or c.canonical(proof["production"]) != c.canonical(plan)
            or wrapper["resources"] != resource_plan(plan, proof["capacity"], proof["measurements"])):
        raise ValueError("partition source/production/capacity allocation differs")
    for path, digest in proof["input_sha256"].items():
        if c.file_hash(path) != digest: raise ValueError("capacity evidence changed")
    for key, digest in plan["native_input_digests"].items():
        if c.digest(read_json(path_in(root, key + ".json"))) != digest: raise ValueError("native input changed")
    for phase in PHASES:
        wanted = dict(mode="partitioned", phase=phase, manifest=c.digest(plan), partition_manifest=c.digest(wrapper))
        if read_json(path_in(root, f"{phase}-execution-intent.json")) != wanted:
            raise ValueError("partition routing reservation differs")
    return wrapper


def run_task(args):
    root, plan, phase, task = args
    low.validate_task(plan, task, phase)
    base = Path(root) / ("traces" if phase == "sample" else "anchors") / c.task_id(task)
    if any(base.with_suffix(ext).exists() for ext in (".json", ".npz", ".done.json")):
        raise ValueError("existing task evidence; cached execution is forbidden")
    return (low.sample_task if phase == "sample" else low.anchor_task)((root, plan, task))


def run_summary_task(args):
    record = run_task(args)
    return {key: record[key] for key in REDUCED} if args[2] == "sample" else record


def partition_directory(root, phase, index):
    return path_in(root, f"sampling-partitions/{phase}/{index}")


def submission_directory(root, phase, index):
    if phase == "collect": return path_in(root, "sampling-collection-submission")
    return path_in(root, f"sampling-submissions/{phase}/{index}")


def partition_resource(wrapper, phase, index):
    if phase == "collect":
        return dict(workers=1, cpus=1, memory_gb=32, requested_nodes=1, max_nodes=2,
                    wall_seconds=7200, walltime="02:00:00", measured=False,
                    warning="Initial full-collection budget; not a measured completion prediction.")
    section = wrapper["resources"][phase]
    part = section["partitions"][index]
    return {key: section[key] for key in ("workers", "cpus", "memory_gb", "requested_nodes", "max_nodes")} | {
        key: part[key] for key in ("wall_seconds", "walltime")}


def submission_evidence(root, wrapper, phase, index, *, executing=False):
    directory = submission_directory(root, phase, index)
    ledger, intent = read_json(directory / "submission.json"), read_json(directory / "submission-intent.json")
    script = directory / "partition.sh"
    if (ledger.get("manifest") != c.digest(wrapper) or ledger.get("phase") != phase or ledger.get("partition") != index
            or ledger.get("resource") != partition_resource(wrapper, phase, index)
            or {key: value for key, value in ledger.items() if key != "job_id"} != intent
            or ledger.get("command") != ["qsub", str(script)] or c.file_hash(script) != ledger.get("script_sha256")
            or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", ledger.get("job_id", ""))):
        raise ValueError("partition submission evidence differs")
    if executing and ledger["job_id"] != os.environ.get("PBS_JOBID"):
        raise ValueError("actual PBS job differs from submitted partition")
    from submit_tile_low_noise_sampling_partitions import bundle_binding
    if bundle_binding(ledger["bundle"], wrapper) != ledger["bundle_binding"]:
        raise ValueError("submitted bundle/executable/source binding differs")
    return ledger


def artifact_record(root, plan, phase, task, problem):
    base = path_in(root, ("traces/" if phase == "sample" else "anchors/") + c.task_id(task))
    marker = read_json(base.with_suffix(".done.json"))
    identity = dict(manifest=c.digest(plan), task=list(task))
    if marker.get("identity") != identity or set(marker.get("sha256", {})) != {".json", ".npz"}:
        raise ValueError("task identity or checksum set differs")
    hashes = {ext: c.file_hash(base.with_suffix(ext)) for ext in (".done.json", ".json", ".npz")}
    if marker["sha256"] != {ext: hashes[ext] for ext in (".json", ".npz")}:
        raise ValueError("task payload changed")
    record = read_json(base.with_suffix(".json"))
    # save_artifact serializes the record directly; no array decompression is needed here.
    analysis.validate_record(plan, task, phase, record, problem)
    return record, hashes


def run_partition(root, phase, index):
    root = Path(root).resolve()
    if (not os.environ.get("PBS_JOBID") or any(os.environ.get(key) != value for key, value in low.native.THREADS.items())):
        raise ValueError("qsub with pinned threads required")
    wrapper = read_plan(root)
    selected = tasks_for_partition(wrapper, phase, index)
    plan = wrapper["production"]
    ledger = submission_evidence(root, wrapper, phase, index, executing=True)
    destination = partition_directory(root, phase, index)
    if destination.exists(): raise ValueError("existing partition; automatic rerun forbidden")
    for task in selected:
        base = root / ("traces" if phase == "sample" else "anchors") / c.task_id(task)
        if any(base.with_suffix(ext).exists() for ext in (".json", ".npz", ".done.json")):
            raise ValueError("existing partition task; cached results forbidden")
    destination.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    intent = dict(manifest=c.digest(plan), partition_manifest=c.digest(wrapper), phase=phase, partition=index,
                  tasks=len(selected), task_digest=c.digest(selected), resource=partition_resource(wrapper, phase, index),
                  pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname(),
                  submission_sha256=c.file_hash(submission_directory(root, phase, index) / "submission.json"))
    c.atomic_json(destination / "execution-intent.json", intent)
    records, markers, errors = [], {}, []
    native_hash = None
    try:
        for key in plan["native_input_digests"]: c.atomic_json(destination / (key + ".json"), read_json(root / (key + ".json")))
        native_hash = low.native.native_preflight(destination, plan)
        results = c.parallel_map(run_summary_task, [(str(root), plan, phase, task) for task in selected], intent["resource"]["workers"])
        if sorted(tuple(row["task"]) for row in results) != sorted(selected): raise ValueError("worker task census differs")
        returned = {tuple(row["task"]): row for row in results}
        spec = plan["condition"]
        _, problem = low.t.build_problem(spec["size"], spec["noise"], spec["target"])
        for task in selected:
            record, hashes = artifact_record(root, plan, phase, task, problem)
            reduced = {key: record[key] for key in REDUCED} if phase == "sample" else record
            if c.canonical(reduced) != c.canonical(returned[task]): raise ValueError("returned task differs from raw record")
            records.append(reduced)
            markers[c.task_id(task)] = hashes[".done.json"]
        if c.canonical(read_plan(root)) != c.canonical(wrapper): raise ValueError("partition context changed")
        if submission_evidence(root, wrapper, phase, index, executing=True) != ledger: raise ValueError("submission changed")
    except Exception as error:
        errors.append(dict(error=repr(error), traceback=traceback.format_exc()))
        # Preserve readable outcomes even if pool delivery or a later proof check failed.
        observed = {tuple(row["task"]) for row in records}
        spec = plan["condition"]
        try:
            _, problem = low.t.build_problem(spec["size"], spec["noise"], spec["target"])
            for task in selected:
                if task in observed: continue
                base = root / ("traces" if phase == "sample" else "anchors") / c.task_id(task)
                if not base.with_suffix(".done.json").exists(): continue
                try:
                    record, hashes = artifact_record(root, plan, phase, task, problem)
                    records.append({key: record[key] for key in REDUCED} if phase == "sample" else record)
                    markers[c.task_id(task)] = hashes[".done.json"]
                except Exception as recovery_error:
                    errors.append(dict(task=list(task), error=repr(recovery_error)))
        except Exception as recovery_error:
            errors.append(dict(error=repr(recovery_error)))
    records.sort(key=lambda row: row["task"])
    complete = not errors and [tuple(row["task"]) for row in records] == sorted(selected)
    failed = sum(row["status"] == "failed" for row in records)
    completion = "incomplete" if not complete else "recorded_task_failures" if failed else "success"
    status = 1 if not complete else 2 if failed else 0
    summary = dict(**intent, complete=complete, completion_class=completion, exit_status=status,
                   records=records, failed=failed, observed_tasks=len(records), missing_tasks=len(selected)-len(records),
                   marker_sha256=markers, errors=errors, native_preflight_sha256=native_hash,
                   execution_intent_sha256=c.file_hash(destination / "execution-intent.json"),
                   phase_wall_seconds=time.perf_counter()-started, warning=WARNING)
    c.atomic_json(destination / "summary.json", summary)
    return summary


def partition_evidence(root, wrapper, phase, index, *, runner=None):
    """Validate saved metadata; optionally obtain the current terminal receipt."""
    root = Path(root).resolve()
    plan = wrapper["production"]
    selected = sorted(tasks_for_partition(wrapper, phase, index))
    directory = partition_directory(root, phase, index)
    subdir = submission_directory(root, phase, index)
    ledger = submission_evidence(root, wrapper, phase, index)
    intent, summary = read_json(directory / "execution-intent.json"), read_json(directory / "summary.json")
    expected = dict(manifest=c.digest(plan), partition_manifest=c.digest(wrapper), phase=phase, partition=index,
                    tasks=len(selected), task_digest=c.digest(tasks_for_partition(wrapper, phase, index)),
                    resource=partition_resource(wrapper, phase, index), pbs_job_id=ledger["job_id"],
                    submission_sha256=c.file_hash(subdir / "submission.json"))
    if (not intent.get("hostname") or any(intent.get(key) != value or summary.get(key) != value for key, value in expected.items())
            or any(summary.get(key) != value for key, value in intent.items()) or summary.get("complete") is not True
            or summary.get("observed_tasks") != len(selected) or summary.get("missing_tasks") != 0 or summary.get("errors")
            or [tuple(row["task"]) for row in summary["records"]] != selected
            or any(row["status"] not in ("ok", "failed") for row in summary["records"])
            or summary["failed"] != sum(row["status"] == "failed" for row in summary["records"])
            or set(summary["marker_sha256"]) != {c.task_id(task) for task in selected}
            or summary["execution_intent_sha256"] != c.file_hash(directory / "execution-intent.json")
            or summary["native_preflight_sha256"] != c.file_hash(directory / "native_preflight.json")):
        raise ValueError("incomplete or changed partition execution")
    native = read_json(directory / "native_preflight.json")
    if any(native.get(key) != intent[key] for key in ("manifest", "pbs_job_id", "hostname")):
        raise ValueError("partition native identity differs")
    low.native.trace_audit.validate_platform(read_json(root / "platform_profile.json"), native["profile"])
    classification = "recorded_task_failures" if summary["failed"] else "success"
    exit_status = 2 if summary["failed"] else 0
    if summary["completion_class"] != classification or summary["exit_status"] != exit_status:
        raise ValueError("partition task failures and exit classification differ")
    terminal_path = subdir / "terminal.json"
    if runner is not None:
        query = runner(["qstat", "-x", "-f", "-F", "json", ledger["job_id"]], capture_output=True, text=True, check=True, timeout=30)
        terminal = selected_job(json.loads(query.stdout).get("Jobs", {}).get(ledger["job_id"], {}))
        value = dict(job_id=ledger["job_id"], job=terminal)
    else:
        value = read_json(terminal_path)
        if value["job_id"] != ledger["job_id"]: raise ValueError("terminal job differs")
        terminal = value["job"]
    resource = expected["resource"]
    selected_resource = terminal.get("Resource_List", {})
    if (terminal.get("job_state") != "F" or terminal.get("Exit_status") != exit_status
            or shlex.split(terminal.get("Submit_arguments", "")) != [str(subdir / "partition.sh")]
            or selected_resource.get("select") != f"1:ncpus=96:mem={resource['memory_gb']}gb"
            or selected_resource.get("walltime") != resource["walltime"]):
        raise ValueError("terminal PBS state/resource/script differs")
    if runner is not None:
        if terminal_path.exists():
            if read_json(terminal_path) != value: raise ValueError("saved terminal receipt differs")
        else:
            with terminal_path.open("xb") as stream: stream.write(c.canonical(value)+b"\n")
    return summary, dict(phase=phase, index=index, job_id=ledger["job_id"], exit_status=exit_status, completion_class=classification)


def proof_paths(wrapper):
    names = ["manifest.json", "platform_profile.json", "platform_fixture.json", "sampling_partition_manifest.json"]
    names.extend("sampling-collection-submission/"+name for name in ("submission-intent.json","submission.json","partition.sh"))
    for phase in PHASES:
        names.append(f"{phase}-execution-intent.json")
        for part in wrapper["resources"][phase]["partitions"]:
            index = part["index"]
            names.extend(f"sampling-partitions/{phase}/{index}/{name}.json" for name in
                         ("execution-intent", "native_preflight", "summary"))
            names.extend(f"sampling-submissions/{phase}/{index}/{name}" for name in
                         ("submission-intent.json", "submission.json", "terminal.json", "partition.sh"))
    return names


def collector_terminal(root, wrapper, *, runner=None):
    """Seal/read the collector's real terminal PBS receipt after it exits."""
    root = Path(root).resolve()
    ledger = submission_evidence(root,wrapper,"collect",None)
    directory = submission_directory(root,"collect",None)
    summary = read_json(root/"sampling-collection/summary.json")
    if (summary.get("complete") is not True or summary.get("errors")
            or summary.get("pbs_job_id")!=ledger["job_id"]
            or summary.get("submission_sha256")!=c.file_hash(directory/"submission.json")):
        raise ValueError("collector did not complete with matching submission")
    path = directory/"terminal.json"
    if runner is None: value=read_json(path)
    else:
        response=runner(["qstat","-x","-f","-F","json",ledger["job_id"]],capture_output=True,text=True,check=True,timeout=30)
        value=dict(job_id=ledger["job_id"],job=selected_job(json.loads(response.stdout).get("Jobs",{}).get(ledger["job_id"],{})))
    job=value["job"]
    resource=partition_resource(wrapper,"collect",None)
    if (value.get("job_id")!=ledger["job_id"] or job.get("job_state")!="F" or job.get("Exit_status")!=0
            or shlex.split(job.get("Submit_arguments",""))!=[str(directory/"partition.sh")]
            or job.get("Resource_List",{}).get("select")!="1:ncpus=1:mem=32gb"
            or job.get("Resource_List",{}).get("walltime")!=resource["walltime"]):
        raise ValueError("collector terminal state/resource/script differs")
    if runner is not None:
        if path.exists():
            if read_json(path)!=value: raise ValueError("collector terminal receipt changed")
        else:
            with path.open("xb") as stream: stream.write(c.canonical(value)+b"\n")
    return dict(phase="collect",job_id=ledger["job_id"],exit_status=0)


def collect(root, *, runner=subprocess.run):
    root = Path(root).resolve()
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(key) != value for key, value in low.native.THREADS.items()):
        raise ValueError("full payload collection requires qsub and pinned threads")
    wrapper = read_plan(root)
    plan = wrapper["production"]
    ledger = submission_evidence(root, wrapper, "collect", None, executing=True)
    original_sources = source_hashes()
    destination = path_in(root, "sampling-collection")
    if destination.exists(): raise ValueError("existing collection; no automatic rerun")
    destination.mkdir(exist_ok=False)
    intent = dict(mode="partitioned_sampling_collection", manifest=c.digest(plan), partition_manifest=c.digest(wrapper),
                  pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname(),
                  submission_sha256=c.file_hash(submission_directory(root,"collect",None)/"submission.json"),
                  resource=partition_resource(wrapper,"collect",None))
    c.atomic_json(destination / "execution-intent.json", intent)
    started = time.perf_counter()
    records, jobs, errors = {}, [], []
    inputs, group_rows, anchors = {}, defaultdict(list), {}
    native_hash = None
    tasks_path = destination / "tasks.jsonl"
    try:
        for key in plan["native_input_digests"]: c.atomic_json(destination / (key+".json"), read_json(root / (key+".json")))
        native_hash = low.native.native_preflight(destination, plan)
        spec = plan["condition"]
        _, problem = low.t.build_problem(spec["size"], spec["noise"], spec["target"])
        names=proof_paths(wrapper)
        initial=snapshot_paths(root,[name for name in names if path_in(root,name).exists()])
        saved_partitions = {}
        for phase in PHASES:
            for part in wrapper["resources"][phase]["partitions"]:
                saved_partitions[phase,part["index"]] = partition_evidence(root,wrapper,phase,part["index"],runner=runner)
        verify_snapshot(root,initial)
        initial.update(snapshot_paths(root,[name for name in names if name not in initial]))
        inputs={name:value["sha256"] for name,value in initial.items()}
        with tasks_path.open("xb") as stream:
            for phase in PHASES:
                failed, count = 0, 0
                records[phase] = dict(tasks=0, failed=0)
                for part in wrapper["resources"][phase]["partitions"]:
                    index = part["index"]
                    summary, job = saved_partitions[phase,index]
                    jobs.append(job)
                    saved_rows = {tuple(row["task"]): row for row in summary["records"]}
                    for task in sorted(tasks_for_partition(wrapper, phase, index)):
                        record, hashes = artifact_record(root, plan, phase, task, problem)
                        reduced = {key: record[key] for key in REDUCED} if phase == "sample" else record
                        if (c.canonical(saved_rows[task]) != c.canonical(reduced)
                                or summary["marker_sha256"][c.task_id(task)] != hashes[".done.json"]):
                            raise ValueError("collection raw artifact differs from partition")
                        stream.write(c.canonical(dict(phase=phase, partition=index, task=list(task), status=record["status"], sha256=hashes))+b"\n")
                        count += 1; failed += int(record["status"] == "failed")
                        records[phase] = dict(tasks=count, failed=failed)
                        if phase == "sample": group_rows[c.task_id(task[:5])].append(reduced)
                        else: anchors[c.task_id(task)] = c.digest(record)
                records[phase] = dict(tasks=count, failed=failed)
        if c.canonical(read_plan(root)) != c.canonical(wrapper): raise ValueError("sampling plan changed during collection")
        for phase in PHASES:
            if records[phase]["tasks"] != sum(1 for _ in low.tasks(plan, phase)): raise ValueError("collection task census differs")
        if len(group_rows) != 768 or len(anchors) != 192: raise ValueError("group or shared anchor census differs")
        # All source marker/payload hashes are rechecked, without decoding or decompressing arrays.
        with tasks_path.open() as stream:
            for line in stream:
                row = json.loads(line)
                base = root / ("traces" if row["phase"] == "sample" else "anchors") / c.task_id(row["task"])
                if any(c.file_hash(base.with_suffix(ext)) != digest for ext, digest in row["sha256"].items()):
                    raise ValueError("raw task changed during collection")
        verify_snapshot(root,initial)
        if source_hashes()!=original_sources or submission_evidence(root,wrapper,"collect",None,executing=True)!=ledger:
            raise ValueError("collector source/submission changed")
    except Exception as error:
        errors.append(dict(error=repr(error), traceback=traceback.format_exc()))
    if "sample" in records:
        records["sample"]["group_record_digests"] = {key: c.digest(sorted(rows, key=lambda row: row["task"][5:])) for key, rows in group_rows.items()}
    if "anchors" in records: records["anchors"]["record_digests"] = anchors
    summary = dict(**intent, complete=not errors, records=records, pbs_jobs=jobs, errors=errors,
                   input_sha256=inputs, source_sha256=original_sources, native_preflight_sha256=native_hash,
                   execution_intent_sha256=c.file_hash(destination / "execution-intent.json"),
                   tasks_sha256=c.file_hash(tasks_path) if tasks_path.exists() else None,
                   phase_wall_seconds=time.perf_counter()-started, warning=WARNING)
    c.atomic_json(destination / "summary.json", summary)
    if errors: raise RuntimeError("collection incomplete; retained outcomes must not be retried automatically")
    return summary


def completed_partition_evidence(root, plan):
    """Revalidate metadata and task-index hashes, leaving payload scans to audits."""
    root = Path(root).resolve()
    initial_names=["manifest.json","sampling_partition_manifest.json","platform_profile.json","platform_fixture.json"]
    initial_names.extend("sampling-collection/"+name for name in ("summary.json","tasks.jsonl","execution-intent.json","native_preflight.json"))
    initial_names.extend("sampling-collection-submission/"+name for name in ("submission.json","submission-intent.json","partition.sh","terminal.json"))
    initial=snapshot_paths(root,initial_names)
    wrapper = read_plan(root)
    initial.update(snapshot_paths(root,[name for name in proof_paths(wrapper) if name not in initial]))
    if c.canonical(plan) != c.canonical(wrapper["production"]): raise ValueError("completed sampling plan differs")
    directory = path_in(root, "sampling-collection")
    summary, intent = read_json(directory / "summary.json"), read_json(directory / "execution-intent.json")
    ledger = submission_evidence(root,wrapper,"collect",None)
    collector_job = collector_terminal(root,wrapper)
    if (intent.get("pbs_job_id")!=ledger["job_id"]
            or intent.get("resource")!=partition_resource(wrapper,"collect",None)
            or intent.get("submission_sha256")!=c.file_hash(submission_directory(root,"collect",None)/"submission.json")):
        raise ValueError("collector submission binding differs")
    if (summary.get("complete") is not True or summary.get("errors") or intent.get("mode") != "partitioned_sampling_collection"
            or intent.get("manifest") != c.digest(plan) or intent.get("partition_manifest") != c.digest(wrapper)
            or not intent.get("pbs_job_id") or not intent.get("hostname")
            or any(summary.get(key) != value for key, value in intent.items())
            or summary["source_sha256"] != source_hashes()
            or summary["native_preflight_sha256"] != c.file_hash(directory / "native_preflight.json")
            or summary["execution_intent_sha256"] != c.file_hash(directory / "execution-intent.json")
            or summary["tasks_sha256"] != c.file_hash(directory / "tasks.jsonl")):
        raise ValueError("collection completion/source/native/index binding differs")
    native = read_json(directory / "native_preflight.json")
    if any(native.get(key) != intent[key] for key in ("manifest", "pbs_job_id", "hostname")):
        raise ValueError("collection native execution differs")
    low.native.trace_audit.validate_platform(read_json(root / "platform_profile.json"), native["profile"])
    expected_names = proof_paths(wrapper)
    if set(summary["input_sha256"]) != set(expected_names): raise ValueError("collection proof census differs")
    hashes = {name: c.file_hash(path_in(root, name)) for name in expected_names}
    if hashes != summary["input_sha256"]: raise ValueError("partition proof changed after collection")
    jobs, groups, anchors = [], defaultdict(list), {}
    indexed = defaultdict(list)
    with (directory / "tasks.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row["phase"] not in PHASES: raise ValueError("unexpected indexed phase")
            indexed[row["phase"], row["partition"]].append(row)
    for phase in PHASES:
        count, failed = 0, 0
        for part in wrapper["resources"][phase]["partitions"]:
            index = part["index"]
            saved, job = partition_evidence(root, wrapper, phase, index)
            jobs.append(job)
            task_index = indexed.pop((phase, index), [])
            if [row["task"] for row in task_index] != [row["task"] for row in saved["records"]]:
                raise ValueError("task index census differs")
            for item, row in zip(task_index, saved["records"]):
                if (item["status"] != row["status"] or set(item["sha256"]) != {".done.json", ".json", ".npz"}
                        or item["sha256"][".done.json"] != saved["marker_sha256"][c.task_id(row["task"])]):
                    raise ValueError("task index differs from partition summary")
                count += 1; failed += int(row["status"] == "failed")
                if phase == "sample": groups[c.task_id(row["task"][:5])].append(row)
                else: anchors[c.task_id(row["task"])] = c.digest(row)
        expected = dict(tasks=count, failed=failed)
        if phase == "sample": expected["group_record_digests"] = {key: c.digest(sorted(rows, key=lambda row: row["task"][5:])) for key, rows in groups.items()}
        else: expected["record_digests"] = anchors
        if summary["records"][phase] != expected: raise ValueError("completed phase digest or count differs")
    if indexed or jobs != summary["pbs_jobs"] or len(groups) != 768 or len(anchors) != 192:
        raise ValueError("completed job/group/anchor census differs")
    for name in ("summary.json", "tasks.jsonl", "execution-intent.json", "native_preflight.json"):
        hashes["sampling-collection/"+name] = initial["sampling-collection/"+name]["sha256"]
    hashes["sampling-collection-submission/terminal.json"] = initial["sampling-collection-submission/terminal.json"]["sha256"]
    verify_snapshot(root,initial)
    if c.canonical(read_plan(root))!=c.canonical(wrapper): raise ValueError("completed source/runtime changed while reading")
    verify_snapshot(root,initial)
    return dict(mode="partitioned_sampling", **summary["records"], input_sha256=hashes,
                input_resolved={name:value["resolved"] for name,value in initial.items()},
                source_sha256=source_hashes(), pbs_jobs=jobs, collector_pbs_job=collector_job, raw_payloads_rehashed=False,
                collection_manifest=c.digest(wrapper), warning=WARNING)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "collect", "seal-collection"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--capacity-root", type=Path)
    parser.add_argument("--capacity-receipt", type=Path)
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--index", type=int)
    args = parser.parse_args()
    if args.command == "prepare": result = prepare(args.root, args.capacity_root, args.capacity_receipt)
    elif args.command == "run": result = run_partition(args.root, args.phase, args.index)
    elif args.command == "collect": result = collect(args.root)
    else: result = collector_terminal(args.root,read_plan(args.root),runner=subprocess.run)
    print(json.dumps({key: value for key, value in result.items() if key in ("purpose", "complete", "phase", "partition", "completion_class")}))
    if args.command == "run": raise SystemExit(result["exit_status"])


if __name__ == "__main__": main()
