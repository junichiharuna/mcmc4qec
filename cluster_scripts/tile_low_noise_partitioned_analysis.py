"""BAR analysis entry points for explicitly partitioned sampling provenance."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import socket
import sys
import time

import calibration as c
import tile_low_noise_analysis as a
import tile_low_noise_analysis_capacity as cap
import tile_low_noise_analysis_partitions as p
import tile_low_noise_audited_collection as saved
import tile_low_noise_study as low

WARNING = p.WARNING + " Sampling provenance spans all recorded PBS partitions; metadata validation alone does not rehash current raw NPZ payloads."


def source_files(extra=()):
    """Return the static local import closure, including function-local imports."""
    directory = Path(__file__).resolve().parent
    pending = [Path(__file__).resolve(), directory/"submit_tile_low_noise_partitioned_analysis.py", *map(Path, extra)]
    found = {}
    while pending:
        path = pending.pop().resolve()
        if path.name in found:
            if found[path.name] != path: raise ValueError("ambiguous source basename")
            continue
        if path.parent != directory or not path.is_file(): raise ValueError("missing local source dependency")
        found[path.name] = path
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            names = ([item.name.split(".")[0] for item in node.names] if isinstance(node, ast.Import)
                     else [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            pending.extend(directory/(name+".py") for name in names if (directory/(name+".py")).is_file())
    return found


def source_hashes():
    return {str(path): c.file_hash(path) for path in source_files().values()}


def sampling_evidence(root, plan):
    from tile_low_noise_sampling_partitions import completed_partition_evidence
    return completed_partition_evidence(root, plan)


def contained(root, name):
    root = Path(root).resolve()
    path = root/name
    if not path.absolute().is_relative_to(root) or not path.resolve().is_relative_to(root):
        raise ValueError("input path escapes root")
    return path


def bind_sampling(root, evidence, proof):
    if (evidence.get("mode") != "partitioned_sampling" or not evidence.get("input_sha256")
            or not isinstance(evidence.get("source_sha256"), dict) or not evidence.get("pbs_jobs")):
        raise ValueError("explicit complete partitioned sampling evidence required")
    for name, digest in evidence["input_sha256"].items():
        if Path(name).is_absolute() or proof.track(contained(root, name)) != digest:
            raise ValueError("sampling metadata snapshot differs")
    for name, digest in evidence["source_sha256"].items():
        if not Path(name).is_absolute() or c.file_hash(name) != digest:
            raise ValueError("sampling reader source differs")


def snapshot(root, wrapper):
    proof = saved.Evidence((Path(root).resolve(),))
    for name in ("manifest.json", "analysis_manifest.json", "partition_analysis_manifest.json", "analysis-execution-intent.json"):
        proof.track(contained(root, name))
    bind_sampling(root, wrapper["analysis_context"]["completed_phase_evidence"], proof)
    return proof


def create_plan(root, capacity_root):
    root, capacity_root = Path(root).resolve(), Path(capacity_root).resolve()
    if any((root/name).exists() or (root/name).is_symlink() for name in
           ("partition_analysis_manifest.json", "analysis_manifest.json", "analysis-execution-intent.json",
            "analysis", "analysis-summary.json", "analysis-partitions", "partition-collection")):
        raise ValueError("existing analysis intent/output; no automatic replacement")
    sources = source_hashes()
    production = a.read_production_plan(root)
    capacity = json.loads((capacity_root/"manifest.json").read_bytes())
    if c.canonical(capacity["production"]) != c.canonical(production):
        raise ValueError("capacity production manifest differs")
    resource = cap.measured_profile(capacity_root, capacity)
    p.validate_partitions(production, resource)
    evidence = sampling_evidence(root, production)
    proof = saved.Evidence((root,))
    proof.track(contained(root, "manifest.json"))
    bind_sampling(root, evidence, proof)
    context = a.analysis_context(production, evidence)
    result = dict(schema=1, purpose="low_noise_partitioned_sampling_analysis", production=production,
                  analysis_context=context, capacity_root=str(capacity_root), capacity_manifest=c.digest(capacity),
                  resources=resource, source_sha256=sources, warning=WARNING)
    proof.finish()
    if source_hashes() != sources: raise ValueError("analysis source changed")
    reservation = dict(mode="partitioned", partition_manifest=c.digest(result), manifest=c.digest(production),
                       warning="Routing reservation only; not PBS execution evidence.")
    with (root/"analysis-execution-intent.json").open("xb") as stream: stream.write(c.canonical(reservation)+b"\n")
    c.atomic_json(root/"analysis_manifest.json", context)
    c.atomic_json(root/"partition_analysis_manifest.json", result)
    return result


def read_plan(root):
    root = Path(root).resolve()
    wrapper = json.loads(contained(root, "partition_analysis_manifest.json").read_bytes())
    if (wrapper.get("purpose") != "low_noise_partitioned_sampling_analysis"
            or wrapper["source_sha256"] != source_hashes()):
        raise ValueError("partitioned analysis source/purpose differs")
    proof = snapshot(root, wrapper)
    production = a.read_production_plan(root)
    if c.canonical(production) != c.canonical(wrapper["production"]): raise ValueError("production manifest differs")
    reservation = proof.read(root/"analysis-execution-intent.json")
    if (reservation.get("mode") != "partitioned" or reservation.get("pbs_job_id") is not None
            or reservation["partition_manifest"] != c.digest(wrapper) or reservation["manifest"] != c.digest(production)):
        raise ValueError("analysis routing reservation differs")
    capacity_root = Path(wrapper["capacity_root"])
    capacity = json.loads((capacity_root/"manifest.json").read_bytes())
    if (c.digest(capacity) != wrapper["capacity_manifest"] or c.canonical(capacity["production"]) != c.canonical(production)
            or cap.measured_profile(capacity_root, capacity) != wrapper["resources"]):
        raise ValueError("measured analysis capacity differs")
    context = wrapper["analysis_context"]
    a.validate_context(production, context)
    if (c.canonical(proof.read(root/"analysis_manifest.json")) != c.canonical(context)
            or sampling_evidence(root, production) != context["completed_phase_evidence"]):
        raise ValueError("sampling partition context changed")
    p.validate_partitions(production, wrapper["resources"])
    proof.finish()
    if source_hashes() != wrapper["source_sha256"]: raise ValueError("source changed while reading plan")
    return wrapper


def require_pbs():
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(key) != value for key, value in low.native.THREADS.items()):
        raise ValueError("PBS and pinned single-thread environment required")


def run_partition(root, wrapper, index):
    require_pbs()
    root = Path(root).resolve()
    if c.canonical(wrapper) != c.canonical(read_plan(root)): raise ValueError("partition plan changed")
    proof = snapshot(root, wrapper)
    parts = wrapper["resources"]["partitions"]
    if type(index) is not int or not 0 <= index < len(parts): raise ValueError("invalid partition index")
    selected = parts[index]
    destination = contained(root, f"analysis-partitions/{index}")
    if destination.exists() or any(contained(root, "analysis/"+c.task_id(group)+ext).exists()
                                   for group in selected["groups"] for ext in (".json", ".npz", ".done.json")):
        raise ValueError("existing partition evidence; automatic rerun forbidden")
    destination.mkdir(parents=True, exist_ok=False)
    plan, context = wrapper["production"], wrapper["analysis_context"]
    workers = wrapper["resources"]["workers"]
    intent = dict(partition_manifest=c.digest(wrapper), partition=index, groups=selected["groups"], workers=workers,
                  manifest=c.digest(plan), pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname())
    with (destination/"execution-intent.json").open("xb") as stream: stream.write(c.canonical(intent)+b"\n")
    for key in plan["native_input_digests"]:
        c.atomic_json(destination/(key+".json"), json.loads(contained(root, key+".json").read_bytes()))
    native_hash = low.native.native_preflight(destination, plan)
    started = time.perf_counter()
    results = c.parallel_map(a.analyze_group, [(str(root), plan, context, tuple(group)) for group in selected["groups"]], workers)
    if sorted(tuple(record["group"]) for record in results) != sorted(tuple(group) for group in selected["groups"]):
        raise ValueError("missing or duplicate completed partition group")
    hashes = {}
    for group in selected["groups"]:
        raw, digest = p.read_group(root, wrapper, tuple(group))
        returned = next(record for record in results if record["group"] == group)
        if c.canonical(returned) != c.canonical({key: value for key, value in raw.items() if key != "diagnostics"}):
            raise ValueError("worker return differs from saved group")
        hashes[c.task_id(group)] = digest
    proof.finish()
    if c.canonical(read_plan(root)) != c.canonical(wrapper): raise ValueError("analysis context changed during execution")
    summary = dict(**intent, native_preflight_sha256=native_hash,
                   execution_intent_sha256=c.file_hash(destination/"execution-intent.json"),
                   group_marker_sha256=hashes, phase_wall_seconds=time.perf_counter()-started,
                   rows=sum(len(record["rows"]) for record in results), warning=WARNING)
    c.atomic_json(destination/"summary.json", summary)
    return summary


def partition_evidence(root, wrapper, index, proof=None):
    root = Path(root).resolve()
    owns_proof = proof is None
    proof = proof or saved.Evidence((root,))
    execution = contained(root, f"analysis-partitions/{index}")
    destination = contained(root, f"analysis-submissions/{index}")
    for name in ("summary.json", "execution-intent.json", "native_preflight.json"):
        proof.track(execution/name)
    summary, digest = p.partition_evidence(root, wrapper, index)
    submission = proof.read(destination/"submission.json")
    submitted = proof.read(destination/"submission-intent.json")
    terminal = proof.read(destination/"terminal.json")
    command = submission.get("command")
    if (submission.get("partition_manifest") != c.digest(wrapper) or submission.get("partition") != index
            or submission.get("manifest") != c.digest(wrapper["production"])
            or submission.get("job_id") != summary["pbs_job_id"]
            or {key: value for key, value in submission.items() if key != "job_id"} != submitted
            or not isinstance(command, list) or len(command) != 2 or command[0] != "qsub"
            or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", submission["job_id"])):
        raise ValueError("analysis submission/PBS binding differs")
    script = Path(command[1])
    if (not script.is_absolute() or not script.resolve().is_relative_to(destination)
            or proof.track(script) != submission["script_sha256"]):
        raise ValueError("analysis submission script differs")
    selected = wrapper["resources"]["partitions"][index]
    fixed = wrapper["resources"]
    expected = dict(cpus=96, memory_gb=fixed["memory_gb"], workers=fixed["workers"],
                    wall_seconds=selected["wall_seconds"], walltime=selected["walltime"], requested_nodes=1, max_nodes=2)
    job = terminal.get("Jobs", {}).get(submission["job_id"], {})
    resource = job.get("Resource_List", {})
    memory = re.fullmatch(r"(\d+)(kb|mb|gb|tb)", str(resource.get("mem", "")).lower())
    memory_gb = None if memory is None else int(memory[1])*{"kb":1/1048576,"mb":1/1024,"gb":1,"tb":1024}[memory[2]]
    binding = submission.get("bundle_binding", {})
    expected_sources = {Path(name).name: digest for name, digest in wrapper["source_sha256"].items()}
    if (any(binding.get("source_sha256", {}).get(name) != digest for name, digest in expected_sources.items())
            or binding.get("package_sha256") != wrapper["production"]["runtime"]["package_sha256"]
            or binding.get("python_path") != str(Path(sys.executable).resolve())
            or binding.get("python_sha256") != c.file_hash(sys.executable)):
        raise ValueError("analysis submitted bundle/runtime binding differs")
    if (submission["resource"] != expected or job.get("job_state") != "F"
            or type(job.get("Exit_status")) is not int or job["Exit_status"] != 0
            or job.get("Submit_arguments") != str(script) or resource.get("walltime") != expected["walltime"]
            or resource.get("ncpus") != 96 or memory_gb != expected["memory_gb"]
            or resource.get("select") != f"1:ncpus=96:mem={expected['memory_gb']}gb"):
        raise ValueError("analysis terminal/resource differs")
    if owns_proof: proof.finish()
    return summary, digest


def validated_groups(root, wrapper, proof=None):
    for part in wrapper["resources"]["partitions"]:
        summary, digest = partition_evidence(root, wrapper, part["index"], proof)
        for group in part["groups"]:
            record, marker = p.read_group(root, wrapper, tuple(group))
            if marker != summary["group_marker_sha256"][c.task_id(group)]: raise ValueError("analysis group changed")
            if proof is not None:
                for ext in (".json", ".npz", ".done.json"):
                    proof.track(contained(root, "analysis/"+c.task_id(group)+ext))
                for key, expected in record["input_artifact_markers"].items():
                    phase, name = key.split("/")
                    if proof.track(contained(root, ("traces/" if phase == "sample" else "anchors/")+name+".done.json")) != expected:
                        raise ValueError("analysis input marker changed")
            yield record, part["index"], digest


def collect(root):
    require_pbs()
    root = Path(root).resolve()
    wrapper = read_plan(root)
    proof = snapshot(root, wrapper)
    for part in wrapper["resources"]["partitions"]: partition_evidence(root, wrapper, part["index"], proof)
    destination = contained(root, "partition-collection")
    destination.mkdir(exist_ok=False)
    counters, proofs = p.collection_counters(), {}
    rows_path = destination/"rows.jsonl"
    with rows_path.open("xb") as stream:
        for record, index, digest in validated_groups(root, wrapper, proof):
            p.count_record(counters, record)
            proofs[str(index)] = digest
            for row in record["rows"]: stream.write(c.canonical(row)+b"\n")
    if counters["groups"] != 768: raise ValueError("complete 192-replicate cohort required")
    proof.finish()
    if c.canonical(read_plan(root)) != c.canonical(wrapper): raise ValueError("collection context changed")
    result = dict(manifest=c.digest(wrapper["production"]), analysis=c.digest(wrapper["analysis_context"]),
                  partition_manifest=c.digest(wrapper), rows_sha256=c.file_hash(rows_path), partition_summary_sha256=proofs,
                  **counters, pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname(), warning=WARNING)
    c.atomic_json(destination/"summary.json", result)
    return result


def read_collection(root):
    """Exhaust the returned iterator to complete terminal validation."""
    root = Path(root).resolve()
    wrapper = read_plan(root)
    proof = snapshot(root, wrapper)
    destination = contained(root, "partition-collection")
    summary = proof.read(destination/"summary.json")
    rows_path = destination/"rows.jsonl"
    if (summary["manifest"] != c.digest(wrapper["production"]) or summary["analysis"] != c.digest(wrapper["analysis_context"])
            or summary["partition_manifest"] != c.digest(wrapper) or summary["rows_sha256"] != proof.track(rows_path)):
        raise ValueError("collection manifest or rows hash differs")
    def iterator():
        counters, proofs = p.collection_counters(), {}
        with rows_path.open("r", encoding="utf-8") as stream:
            for record, index, digest in validated_groups(root, wrapper, proof):
                p.count_record(counters, record); proofs[str(index)] = digest
                for row in record["rows"]:
                    line = stream.readline()
                    if not line or c.canonical(json.loads(line)) != c.canonical(row):
                        raise ValueError("collection row differs from raw group")
                    yield row
            if stream.read(): raise ValueError("unexpected collection rows")
        if (any(summary[key] != value for key, value in counters.items()) or counters["groups"] != 768
                or summary["partition_summary_sha256"] != proofs):
            raise ValueError("collection denominator or partition proof differs")
        proof.finish()
        if c.canonical(read_plan(root)) != c.canonical(wrapper): raise ValueError("collection context changed")
    return wrapper["production"], iterator(), summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "run", "collect"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--capacity-root", type=Path)
    parser.add_argument("--partition", type=int)
    args = parser.parse_args()
    if args.command == "plan":
        if args.capacity_root is None: raise ValueError("capacity root required")
        result = create_plan(args.root, args.capacity_root)
    elif args.command == "run": result = run_partition(args.root, read_plan(args.root), args.partition)
    else: result = collect(args.root)
    print(json.dumps(dict(manifest=c.digest(result))))


if __name__ == "__main__": main()
