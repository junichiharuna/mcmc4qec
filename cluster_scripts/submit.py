"""Render and optionally qsub fixed PBS jobs in two dependency lanes.

Run on the cluster login node. Default is dry-run; --execute submits. Each job
uses a dedicated pinned environment and a full 96-core node. No git operations,
notifications, job arrays, or modifications of RIMC are performed.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shlex
import subprocess

from calibration import atomic_json, digest, read_plan, file_hash


def sampling_graph(order):
    if sorted(order) != list(range(4)):
        raise ValueError("four distinct sampling shards required")
    return [(shard, None if i < 2 else order[i-2]) for i, shard in enumerate(order)]


def walltime(seconds):
    # 2x measured extrapolation, rounded up to half-hour, bounded by queue policy.
    hours = max(.5, math.ceil(seconds*2/1800)/2)
    if hours > 24:
        raise ValueError(f"predicted budget {hours} h exceeds 24 h; split the stage before submission")
    return f"{int(hours):02}:{30 if hours % 1 else 0:02}:00"


def script(bundle, root, stage, wall, memory, shard=None):
    bundle, root = Path(bundle).resolve(), Path(root).resolve()
    if not 1 <= memory <= 340:
        raise ValueError("memory must be <= 340 GB")
    command = f"{shlex.quote(str(bundle/'venv/bin/python'))} {shlex.quote(str(bundle/'cluster_scripts/calibration.py'))} {stage} --root {shlex.quote(str(root))} --workers 96"
    if shard is not None:
        command += f" --shard {shard}"
    label = f"m4q_{stage}{'' if shard is None else shard}"
    return f"""#!/bin/bash
#PBS -N {label}
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={memory}gb
#PBS -l walltime={wall}
#PBS -o {root}/logs/{label}.out
#PBS -e {root}/logs/{label}.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
{command}
"""


def own_active_jobs():
    result = subprocess.run(["qstat", "-f", "-F", "json"], capture_output=True, text=True, check=True)
    user = subprocess.run(["id", "-un"], capture_output=True, text=True, check=True).stdout.strip()
    jobs = json.loads(result.stdout).get("Jobs", {})
    return {job: data for job, data in jobs.items() if data.get("Job_Owner", "").split("@")[0] == user and data.get("job_state") not in ("F", "X")}


def submit_jobs(bundle, root, mode, execute):
    bundle, root = Path(bundle).resolve(), Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root/"logs").mkdir(exist_ok=True)
    (root/"pbs").mkdir(exist_ok=True)
    plan = read_plan(root)
    if execute and (root/"submission.json").exists():
        raise ValueError("submission ledger already exists; inspect qstat and resume explicitly, never double-submit")
    if mode == "smoke":
        jobs = [("smoke", "smoke", None, [], "00:30:00", 128)]
    else:
        timing = json.loads((root.parent/"smoke"/"timing.json").read_text())
        if timing["status"] != "ok" or timing["workers"] != 96:
            raise ValueError("successful full-node smoke required")
        sample_mem = max(32, math.ceil(timing["sample_peak_worker_rss_mb"]*96*2/1024))
        analysis_mem = max(32, math.ceil(timing["analysis_peak_worker_rss_mb"]*96*2/1024))
        order = sorted(range(4), key=lambda i: timing["predicted_sample_shard_seconds"][i], reverse=True)
        jobs = [("truth", "truth", None, [], "00:30:00", 32)]
        for shard, parent in sampling_graph(order):
            deps = ["truth"] if parent is None else [f"sample{parent}"]
            jobs.append((f"sample{shard}", "sample", shard, deps, walltime(timing["predicted_sample_shard_seconds"][shard]), sample_mem))
        jobs.append(("analyze", "analyze", None, [f"sample{s}" for s in order[-2:]], walltime(timing["predicted_analysis_seconds"]), analysis_mem))
    if execute:
        active = own_active_jobs()
        if active:
            raise ValueError(f"active user jobs exist; include them in the two-node budget before submitting: {list(active)}")
    ledger = dict(manifest=digest(plan), mode=mode, max_nodes=2, jobs=[])
    ids = {}
    for name, stage, shard, dependencies, wall, memory in jobs:
        path = root/"pbs"/f"{name}.sh"
        path.write_text(script(bundle, root, stage, wall, memory, shard), newline="\n")
        args = ["qsub"]
        if dependencies:
            args += ["-W", "depend=afterok:" + ":".join(ids[d] for d in dependencies)]
        args.append(str(path))
        if execute:
            output = subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()
            if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", output):
                raise RuntimeError(f"unexpected qsub response; inspect qstat before retry: {output}")
            ids[name] = output
        else:
            ids[name] = f"DRY_{name}"
        entry = dict(name=name, id=ids[name], dependencies=dependencies, command=args, script_sha256=file_hash(path), walltime=wall, memory_gb=memory)
        ledger["jobs"].append(entry)
        # Persist after EVERY qsub; a partially submitted batch must not be blindly retried.
        atomic_json(root/("submission.json" if execute else "submission_dry_run.json"), ledger)
        print(json.dumps(entry), flush=True)
    return ledger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["smoke", "production"])
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    submit_jobs(args.bundle, args.root, args.mode, args.execute)
