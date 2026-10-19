"""Explicit trace-audit entry point for a completed partitioned sampling cohort."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import sys
import time

import calibration as c
import tile_low_noise_study as low
import tile_low_noise_analysis as analysis
import tile_low_noise_sampling_partitions as partitions
import tile_low_noise_trace_audit_run as original

THREADS = original.THREADS
WARNING = original.WARNING
REDUCED_KEYS = original.REDUCED_KEYS
audit = original.audit
groups = original.groups
tasks_for_group = original.tasks_for_group
path_in = original.path_in
separate_roots = original.separate_roots
run_group = original.run_group
verify_group_inputs = original.verify_group_inputs


def source_hashes():
    directory = Path(__file__).resolve().parent
    roots = [Path(__file__), Path(partitions.__file__),
             directory / "tile_low_noise_partitioned_trace_audit_resources.py",
             directory / "submit_tile_low_noise_partitioned_trace_audit.py"]
    files = dict(partitions.source_files(), **partitions.source_files(*roots))
    return {str(path.resolve()): c.file_hash(path) for path in files.values()}


def make_plan(sampling, platform_profile, platform_fixture, *, capacity, workers,
              completed_evidence, input_sha256=None):
    proof = completed_evidence
    if (proof.get("mode") != "partitioned_sampling" or not proof.get("pbs_jobs")
            or not proof.get("source_sha256") or not isinstance(proof.get("input_sha256"), dict)
            or not isinstance(proof.get("sample", {}).get("group_record_digests"), dict)
            or not isinstance(proof.get("anchors", {}).get("record_digests"), dict)):
        raise ValueError("complete explicit partition evidence required")
    upstream_jobs(proof)
    group_ids = {c.task_id(group) for group in analysis.groups(sampling)}
    anchor_ids = {c.task_id(task) for task in low.tasks(sampling, "anchors")}
    count = len(group_ids) * len(sampling["condition"]["rungs"]) * sampling["condition"]["chains"]
    if (set(proof["sample"]["group_record_digests"]) != group_ids
            or set(proof["anchors"]["record_digests"]) != anchor_ids
            or proof["sample"].get("tasks") != count or proof["anchors"].get("tasks") != len(anchor_ids)):
        raise ValueError("partition evidence must retain the full production task census")
    # This helper only constructs a dictionary; it never reads singleton evidence.
    plan = original.make_plan(sampling, platform_profile, platform_fixture, capacity=capacity,
                              workers=workers, completed_evidence=proof, input_sha256=input_sha256)
    plan.update(mode="partitioned_sampling", source_sha256=source_hashes())
    return plan


def upstream_jobs(evidence):
    collector = evidence.get("collector_pbs_job", {})
    if (collector.get("phase") != "collect" or type(collector.get("exit_status")) is not int
            or collector["exit_status"] != 0 or not isinstance(collector.get("job_id"), str)
            or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", collector["job_id"])):
        raise ValueError("completed partition collector real PBS evidence required")
    return sorted([*evidence["pbs_jobs"], collector], key=lambda row: (row["phase"], row.get("index", -1)))


def sampling_snapshot(source, evidence):
    names = {"manifest.json", "platform_profile.json", "platform_fixture.json"}
    expected = evidence["input_sha256"]
    if any(Path(name).is_absolute() for name in expected):
        raise ValueError("sampling evidence path escapes the root-relative contract")
    current = {name: c.file_hash(path_in(source, name)) for name in sorted(names | set(expected))}
    if any(current[name] != digest for name, digest in expected.items()):
        raise ValueError("partition sampling evidence changed")
    return current


def prepare(root, source, *, capacity, workers=8):
    root, source = separate_roots(root, source)
    if root.exists() and any(root.iterdir()):
        raise ValueError("new empty audit root required")
    sampling = analysis.read_production_plan(source)
    proof = partitions.completed_partition_evidence(source, sampling)
    before = sampling_snapshot(source, proof)
    inputs = {key: json.loads(path_in(source, key + ".json").read_text())
              for key in ("platform_profile", "platform_fixture")}
    plan = make_plan(sampling, **inputs, capacity=capacity, workers=workers,
                     completed_evidence=proof, input_sha256=before)
    if before != sampling_snapshot(source, proof):
        raise ValueError("sampling evidence changed")
    for name, value in dict(manifest=plan, sampling_manifest=sampling, **inputs).items():
        c.atomic_json(root / (name + ".json"), value)
    return plan


def read_plan(root, source):
    root, source = separate_roots(root, source)
    plan = json.loads(path_in(root, "manifest.json").read_text())
    if (plan.get("mode") != "partitioned_sampling" or plan.get("purpose") not in
            ("low_noise_trace_audit_capacity", "low_noise_trace_audit_full")):
        raise ValueError("explicit partitioned sampling audit required")
    sampling = json.loads(path_in(root, "sampling_manifest.json").read_text())
    if c.canonical(sampling) != c.canonical(analysis.read_production_plan(source)):
        raise ValueError("sampling manifest changed")
    proof = partitions.completed_partition_evidence(source, sampling)
    before = sampling_snapshot(source, proof)
    inputs = {key: json.loads(path_in(root, key + ".json").read_text())
              for key in ("platform_profile", "platform_fixture")}
    expected = make_plan(sampling, **inputs,
                         capacity=plan["purpose"] == "low_noise_trace_audit_capacity",
                         workers=plan["workers"], completed_evidence=proof, input_sha256=before)
    if before != sampling_snapshot(source, proof) or c.canonical(expected) != c.canonical(plan):
        raise ValueError("audit source/runtime/partition receipts or sampling evidence changed")
    return plan, sampling


def read_terminal(root, plan):
    """Bind a selected PBS terminal receipt to the actual audit script and job."""
    root = Path(root).resolve()
    hashes = {}
    def read(name):
        path = path_in(root, name)
        hashes[name] = c.file_hash(path)
        return json.loads(path.read_text())
    terminal = read("terminal.json")
    submission = read("submission.json")
    submitted = read("submission-intent.json")
    intent = read("execution-intent.json")
    native = read("native_preflight.json")
    job = submission.get("job_id")
    if (not isinstance(job, str) or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", job)
            or submission.get("manifest") != c.digest(plan)
            or {k: v for k, v in submission.items() if k != "job_id"} != submitted
            or intent.get("manifest") != c.digest(plan) or intent.get("pbs_job_id") != job
            or intent.get("sampling_manifest") != plan.get("sampling_manifest")
            or intent.get("submission_sha256") != hashes["submission.json"]
            or intent.get("submission_intent_sha256") != hashes["submission-intent.json"]
            or intent.get("script_sha256") != submission.get("script_sha256")
            or intent.get("workers") != plan["workers"] or not intent.get("hostname")
            or {k: v for k, v in native.items() if k != "evidence"} != intent
            or native.get("evidence", {}).get("native_platform_verified") is not True):
        raise ValueError("audit submission/execution/native job binding differs")
    script = path_in(root, "trace-audit.sh")
    hashes["trace-audit.sh"] = c.file_hash(script)
    if (submission.get("command") != ["qsub", str(script)]
            or submission.get("script_sha256") != hashes["trace-audit.sh"]):
        raise ValueError("audit qsub script binding differs")
    jobs = terminal.get("Jobs", {})
    row = jobs.get(job, {})
    if (set(jobs) != {job} or row.get("job_state") != "F"
            or type(row.get("Exit_status")) is not int or row["Exit_status"] != 0
            or row.get("Submit_arguments") != str(script)):
        raise ValueError("successful matching terminal PBS receipt required")
    resource = submission["resource"]
    actual = row.get("Resource_List", {})
    memory = str(actual.get("mem", "")).lower()
    match = re.fullmatch(r"(\d+)(kb|mb|gb|tb)", memory)
    memory_gb = None if match is None else int(match[1]) * {"kb": 1 / 1048576, "mb": 1 / 1024, "gb": 1, "tb": 1024}[match[2]]
    selection = str(actual.get("select", ""))
    fields = selection.split(":")
    selected = dict(part.split("=", 1) for part in fields[1:] if "=" in part)
    if (fields[0] != "1" or "+" in selection or selected.get("ncpus") != "96"
            or selected.get("mem", "").lower() != f"{resource['memory_gb']}gb"
            or actual.get("ncpus") != 96 or resource.get("cpus") != 96
            or resource.get("requested_nodes") != 1 or memory_gb != resource["memory_gb"]
            or actual.get("walltime") != resource["walltime"]):
        raise ValueError("terminal PBS resources differ from fixed audit allocation")
    for name, digest in hashes.items():
        if c.file_hash(path_in(root, name)) != digest:
            raise ValueError("terminal audit evidence changed")
    return dict(job_id=job, exit_status=0, terminal_sha256=hashes["terminal.json"], input_sha256=hashes)


def execution_submission(root, source, plan, sampling):
    """Check the actual producer job before any native probe or audit output."""
    root, source = Path(root).resolve(), Path(source).resolve()
    hashes = {name: c.file_hash(path_in(root, name)) for name in
              ("submission.json", "submission-intent.json", "trace-audit.sh")}
    submission = json.loads(path_in(root, "submission.json").read_text())
    submitted = json.loads(path_in(root, "submission-intent.json").read_text())
    resource = submission.get("resource", {})
    seconds = resource.get("wall_seconds")
    if (submission.get("job_id") != os.environ.get("PBS_JOBID")
            or submission.get("manifest") != c.digest(plan)
            or {k: v for k, v in submission.items() if k != "job_id"} != submitted
            or submission.get("command") != ["qsub", str(root / "trace-audit.sh")]
            or submission.get("script_sha256") != hashes["trace-audit.sh"]
            or submission.get("sampling_root") != str(source)
            or submission.get("source_pbs_jobs") != upstream_jobs(plan["completed_phase_evidence"])
            or resource.get("workers") != plan["workers"] or resource.get("cpus") != 96
            or resource.get("requested_nodes") != 1 or resource.get("max_nodes") != 2
            or type(resource.get("memory_gb")) is not int or not 0 < resource["memory_gb"] <= 340
            or type(seconds) is not int or not 0 < seconds <= 86400 or seconds % 1800
            or resource.get("walltime") != f"{seconds//3600:02d}:{seconds%3600//60:02d}:00"):
        raise ValueError("actual audit job differs from fixed qsub submission")
    from submit_tile_low_noise_partitioned_trace_audit import source_files
    expected_sources = {name: c.file_hash(path) for name, path in source_files().items()}
    binding = submission.get("bundle_binding", {})
    if (binding.get("source_sha256") != expected_sources
            or binding.get("package_sha256") != sampling["runtime"]["package_sha256"]
            or binding.get("python_path") != str(Path(sys.executable).resolve())
            or binding.get("python_sha256") != c.file_hash(Path(sys.executable).resolve())
            or submission.get("submit_source_sha256") != c.file_hash(Path(__file__).with_name("submit_tile_low_noise_partitioned_trace_audit.py"))):
        raise ValueError("audit submitted source/runtime/executable binding differs")
    if any(c.file_hash(path_in(root, name)) != value for name, value in hashes.items()):
        raise ValueError("audit submission changed while validating")
    return dict(submission_sha256=hashes["submission.json"],
                submission_intent_sha256=hashes["submission-intent.json"], script_sha256=hashes["trace-audit.sh"])


def run(root, source):
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(k) != v for k, v in THREADS.items()):
        raise ValueError("PBS and pinned single-thread environment required")
    root, source = separate_roots(root, source)
    plan, sampling = read_plan(root, source)
    if any((root / name).exists() for name in ("execution-intent.json", "native_preflight.json", "audit", "measurements", "summary.json")):
        raise ValueError("existing audit execution; no automatic rerun")
    submitted = execution_submission(root, source, plan, sampling)
    intent = dict(manifest=c.digest(plan), sampling_manifest=c.digest(sampling), workers=plan["workers"],
                  pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname(), **submitted)
    with (root / "execution-intent.json").open("xb") as stream:
        stream.write(c.canonical(intent) + b"\n")
    native = audit.validate_native_environment(sampling,
        platform_profile=json.loads((root / "platform_profile.json").read_text()),
        platform_fixture=json.loads((root / "platform_fixture.json").read_text()))
    c.atomic_json(root / "native_preflight.json", dict(intent, evidence=native))
    started = time.perf_counter()
    expected = groups(plan)
    records = c.parallel_map(run_group, [(str(source), str(root), sampling, plan, g) for g in expected], plan["workers"])
    records.sort(key=lambda row: row["group"])
    if [tuple(row["group"]) for row in records] != expected:
        raise ValueError("missing or duplicate audit group")
    changes = []
    for record in records:
        try:
            verify_group_inputs(source, root, plan, record)
        except Exception as error:
            changes.append(dict(group=record["group"], error=repr(error)))
    context_error = None
    try:
        if c.digest(read_plan(root, source)[0]) != c.digest(plan):
            raise ValueError("audit context changed")
        if execution_submission(root, source, plan, sampling) != submitted:
            raise ValueError("audit qsub evidence changed during execution")
    except Exception as error:
        context_error = repr(error)
    failed = {tuple(row["group"]) for row in records if row["status"] != "ok"} | {tuple(row["group"]) for row in changes}
    result = dict(manifest=c.digest(plan), groups=len(expected), planned_tasks=sum(row["planned_tasks"] for row in records),
        failed_audit_groups=len(failed), failed_sampling=sum(row["failed_sampling"] for row in records), records=records,
        input_changes=changes, context_error=context_error, native_platform_verified=True,
        native_preflight_sha256=c.file_hash(root / "native_preflight.json"), all_physical_states_redecoded=False,
        phase_wall_seconds=time.perf_counter() - started, warning=WARNING)
    c.atomic_json(root / "summary.json", result)
    if failed or context_error:
        raise RuntimeError("audit failures/input changes retained in summary")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "run"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--capacity", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    result = prepare(args.root, args.source_root, capacity=args.capacity, workers=args.workers) if args.command == "plan" else run(args.root, args.source_root)
    print(json.dumps({k: v for k, v in result.items() if k not in ("records", "completed_phase_evidence")}))


if __name__ == "__main__":
    main()
