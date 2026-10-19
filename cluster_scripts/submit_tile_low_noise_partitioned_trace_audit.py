"""One-shot qsub for fixed low-noise trace audit capacity and full cohorts."""
import argparse
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import types

import calibration as c
import tile_low_noise_partitioned_trace_audit as r
import tile_low_noise_partitioned_trace_audit_resources as res
import submit_tile_low_noise_analysis_capacity as common
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def source_files():
    return dict(r.partitions.source_files(), **r.partitions.source_files(Path(__file__),Path(r.__file__),Path(res.__file__)))


def bundle_binding(bundle, sampling):
    binding = common.bundle_binding(bundle, dict(production=sampling))
    for name, source in source_files().items():
        target = common.contained(bundle / "cluster_scripts" / name, bundle)
        if not target.is_file() or c.file_hash(target) != c.file_hash(source):
            raise ValueError("bundle source differs: " + name)
        binding["source_sha256"][name] = c.file_hash(target)
    return binding


def checked_plan(root, source, capacity_root):
    plan, sampling = r.read_plan(root, source)
    path = common.contained(root / "manifest.json", root)
    if c.canonical(json.loads(path.read_text())) != c.canonical(plan):
        raise ValueError("saved audit manifest differs")
    if plan["purpose"] == "low_noise_trace_audit_capacity":
        if capacity_root is not None or plan["replicates"] != 2 or plan["workers"] != 8:
            raise ValueError("capacity requires exactly eight workers and two replicates without capacity-root")
        resource = res.capacity_resources()
    elif plan["purpose"] == "low_noise_trace_audit_full":
        if capacity_root is None or plan["replicates"] != 192:
            raise ValueError("full audit requires measured capacity root and 192 replicates")
        resource = res.measured_capacity(capacity_root, source, plan)
    else:
        raise ValueError("unknown audit purpose")
    resource = json.loads(c.canonical(resource))
    if (resource["workers"] != plan["workers"] or type(resource["workers"]) is not int
            or not 1 <= resource["workers"] <= 96):
        raise ValueError("saved plan worker count differs from measured resources; create a new plan")
    seconds = resource["wall_seconds"]
    if (resource["cpus"] != 96 or resource["requested_nodes"] != 1 or resource["max_nodes"] != 2
            or type(resource["memory_gb"]) is not int or not 0 < resource["memory_gb"] <= 340
            or type(seconds) is not int or not 0 < seconds <= 86400 or seconds % 1800
            or resource["walltime"] != f"{seconds//3600:02d}:{seconds%3600//60:02d}:00"):
        raise ValueError("invalid fixed resource ceiling")
    evidence = plan["completed_phase_evidence"]
    if evidence.get("mode") != "partitioned_sampling" or not evidence.get("pbs_jobs"):
        raise ValueError("complete partitioned sampling job evidence required")
    jobs = r.upstream_jobs(evidence)
    identities = [(row["phase"], row.get("index")) for row in jobs]
    if (len(set(identities)) != len(identities)
            or len({row["job_id"] for row in jobs}) != len(jobs)
            or {row["phase"] for row in jobs} != {"sample", "anchors", "collect"}):
        raise ValueError("duplicate, missing or mixed sampling partition jobs")
    for row in jobs:
        if (not isinstance(row["job_id"], str) or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", row["job_id"])
                or type(row["exit_status"]) is not int):
            raise ValueError("explicit real partition job and expected exit required")
    return plan, sampling, resource, jobs


def require_fresh(root):
    for name in ("submission-intent.json", "submission.json", "execution-intent.json", "native_preflight.json",
                 "audit", "measurements", "summary.json", "trace-audit.out", "trace-audit.err"):
        path = common.contained(root / name, root)
        if path.exists() or path.is_symlink():
            raise ValueError("existing audit evidence; never retry automatically")


def submit(bundle, root, source_root, *, capacity_root=None, execute=False,
           controller_query=live_controllers, active_query=own_active_jobs, runner=subprocess.run):
    bundle, root, source = (Path(value).resolve() for value in (bundle, root, source_root))
    capacity_root = None if capacity_root is None else Path(capacity_root).resolve()
    roots = [root, source] + ([] if capacity_root is None else [capacity_root])
    if root == bundle / "runs" or not root.is_relative_to(bundle / "runs"):
        raise ValueError("audit output must be inside bundle/runs")
    for index, first in enumerate(roots):
        for second in roots[index + 1:]:
            if first.is_relative_to(second) or second.is_relative_to(first):
                raise ValueError("audit, sampling and capacity roots must be independent")
    if any(char.isspace() for path in [bundle, *roots] for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    require_fresh(root)
    plan, sampling, resource, jobs = checked_plan(root, source, capacity_root)
    binding = bundle_binding(bundle, sampling)
    invocation = shlex.join([str(bundle / "venv/bin/python"),
                            str(bundle / "cluster_scripts/tile_low_noise_partitioned_trace_audit.py"),
                            "run", "--root", str(root), "--source-root", str(source)])
    script = f'''#!/bin/bash
#PBS -N m4q_low_audit
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/trace-audit.out
#PBS -e {root}/trace-audit.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/'src'))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{invocation}
'''
    path = common.contained(root / "trace-audit.sh", root)
    if path.exists():
        if path.read_text() != script:
            raise ValueError("existing audit script differs")
    else:
        with path.open("x", newline="\n") as stream:
            stream.write(script)
    command = ["qsub", str(path)]
    record = dict(command=command, manifest=c.digest(plan), resource=resource, bundle_binding=binding,
                  resource_basis="initial_ceiling" if capacity_root is None else "measured_capacity",
                  sampling_root=str(source), capacity_root=None if capacity_root is None else str(capacity_root),
                  source_pbs_jobs=jobs, script_sha256=c.file_hash(path), submit_source_sha256=c.file_hash(__file__))
    if not execute:
        c.atomic_json(common.contained(root / "dry_run.json", root), dict(record, job_id="dry-run"))
        return dict(record, job_id="dry-run")
    lock = bundle.parent / "tile-low-noise-submission.lock"
    with lock.open("xb") as stream:
        stream.write(c.canonical(dict(root=str(root), pid=os.getpid())) + b"\n")
    uncertain = False
    try:
        require_fresh(root)
        if controller_query():
            raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query()) + 1 > 2:
            raise ValueError("two-node budget exceeded, including queued requests")
        for source_job in jobs:
            job=source_job["job_id"]
            query = runner(["qstat", "-x", "-f", "-F", "json", job],
                           capture_output=True, text=True, check=True, timeout=30)
            observed=json.loads(query.stdout).get("Jobs", {}).get(job, {})
            if (observed.get("job_state") != "F" or type(observed.get("Exit_status")) is not int
                    or observed["Exit_status"] != source_job["exit_status"]):
                raise ValueError("sampling partition is not at its recorded terminal exit")
        if any(item.resolve() != item for item in [bundle, *roots]):
            raise ValueError("fixed path changed before submission")
        current, current_sampling, current_resource, current_jobs = checked_plan(root, source, capacity_root)
        require_fresh(root)
        if (c.digest(current) != record["manifest"] or current_resource != resource or current_jobs != jobs
                or bundle_binding(bundle, current_sampling) != binding
                or c.file_hash(common.contained(path, root)) != record["script_sha256"]):
            raise ValueError("input, resource, source, executable or script changed before qsub")
        if controller_query():
            raise ValueError("tile coordinator started during validation")
        if requested_nodes(active_query()) + 1 > 2:
            raise ValueError("two-node budget exceeded after validation, including queued requests")
        with common.contained(root / "submission-intent.json", root).open("xb") as stream:
            stream.write(c.canonical(record) + b"\n")
        uncertain = True
        job = runner(command, capture_output=True, text=True, check=True, timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", job):
            raise RuntimeError("unrecognized qsub response; intent and lock retained, inspect queue")
        record["job_id"] = job
        c.atomic_json(common.contained(root / "submission.json", root), record)
        uncertain = False
        return record
    finally:
        if not uncertain:
            lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--capacity-root", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    print(json.dumps(submit(args.bundle, args.root, args.source_root,
                            capacity_root=args.capacity_root, execute=args.execute)))


if __name__ == "__main__":
    main()
