"""Submit a single full-case final reaggregation with an unmeasured resource ceiling."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_final_reaggregation as r
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def contained(path, root):
    path, root = Path(path), Path(root).resolve()
    if not path.resolve().is_relative_to(root): raise ValueError("path escapes fixed root")
    return path


def bundle_binding(bundle, plan):
    bundle = Path(bundle).resolve()
    hashes = {}
    for name, source in r.source_files().items():
        path = contained(bundle / "cluster_scripts" / name, bundle)
        if not path.is_file() or c.file_hash(path) != c.file_hash(source):
            raise ValueError("bundle source differs: " + name)
        hashes[name] = c.file_hash(path)
    package = contained(bundle / "src/mcmc4qec", bundle)
    digest = hashlib.sha256()
    files = sorted(package.rglob("*.py"))
    if not files: raise ValueError("bundle source package missing")
    for path in files:
        contained(path, package)
        digest.update(path.relative_to(package).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    if digest.hexdigest() != plan["snapshot"]["runtime"]["package_sha256"]:
        raise ValueError("bundle core package differs")
    executable = (bundle / "venv/bin/python").resolve()
    if not executable.is_file() or c.file_hash(executable) != plan["snapshot"]["python_sha256"]:
        raise ValueError("bundle Python executable differs")
    return dict(source_sha256=hashes, package_sha256=digest.hexdigest(), python_path=str(executable),
                python_sha256=c.file_hash(executable))


def require_fresh(root):
    for name in ("submission-intent.json", "submission.json", "execution-intent.json", "phases", "summary.json"):
        path = contained(root / name, root)
        if path.exists() or path.is_symlink(): raise ValueError("existing submission/execution; never retry automatically")


def selected_completion(receipt, jobs):
    """Persist scheduler evidence without unrelated environment variables."""
    fields = ("job_state", "Exit_status", "Submit_arguments", "Resource_List", "resources_used", "Job_Name",
              "Job_Owner", "queue", "qtime", "stime", "mtime", "obittime", "exec_host", "exec_vnode")
    r.check_completion(receipt, jobs)
    return {"Jobs": {job: {key: value for key, value in receipt["Jobs"][job].items() if key in fields}
                     for job in jobs.values()}}


def submit(bundle, root, *, execute=False, controller_query=live_controllers,
           active_query=own_active_jobs, runner=subprocess.run):
    bundle, root = map(lambda value: Path(value).resolve(), (bundle, root))
    if root == bundle / "runs" or not root.is_relative_to(bundle / "runs"):
        raise ValueError("independent output root under bundle/runs required")
    if any(char.isspace() for path in (bundle, root) for char in str(path)):
        raise ValueError("PBS output paths must not contain whitespace")
    require_fresh(root)
    plan = r.read_plan(root)
    binding = bundle_binding(bundle, plan)
    invocation = shlex.join([str(bundle / "venv/bin/python"), str(bundle / "cluster_scripts/tile_final_reaggregation.py"),
                             "run", "--root", str(root)])
    script = f'''#!/bin/bash
#PBS -N m4q_final{plan['case']}
#PBS -q workq
#PBS -l select=1:ncpus=1:mem=32gb
#PBS -l walltime=02:00:00
#PBS -o {root}/reaggregate.out
#PBS -e {root}/reaggregate.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/'src')+':'+str(bundle/'cluster_scripts'))}
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
{invocation}
'''
    path = contained(root / "reaggregate.sh", root)
    if path.exists():
        if path.read_text() != script: raise ValueError("existing script differs")
    else:
        with path.open("x", newline="\n") as stream: stream.write(script)
    command = ["qsub", str(path)]
    record = dict(command=command, manifest=c.digest(plan), resource=r.resources(), bundle_binding=binding,
                  script_sha256=c.file_hash(path), submit_source_sha256=c.file_hash(__file__), warning=r.WARNING)
    if not execute:
        c.atomic_json(contained(root / "dry_run.json", root), dict(record, job_id="dry-run"))
        return dict(record, job_id="dry-run")
    lock = bundle.parent / "tile-low-noise-submission.lock"
    with lock.open("xb") as stream: stream.write(c.canonical(dict(root=str(root), pid=os.getpid())) + b"\n")
    uncertain = False
    try:
        require_fresh(root)
        if controller_query(): raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query()) + 1 > 2: raise ValueError("two-node budget exceeded, including queued requests")
        jobs = plan["snapshot"]["upstream_jobs"]
        result = runner(["qstat", "-x", "-f", "-F", "json", *jobs.values()],
                        capture_output=True, text=True, check=True, timeout=30)
        receipt = selected_completion(json.loads(result.stdout), jobs)
        if any(target.resolve() != target for target in (root, bundle)):
            raise ValueError("output path changed before qsub")
        current = r.read_plan(root)
        if c.digest(current) != record["manifest"] or bundle_binding(bundle, current) != binding or c.file_hash(path) != record["script_sha256"]:
            raise ValueError("input/source/script changed before qsub")
        # A second slot check follows potentially slow binding and qstat reads.
        if controller_query() or requested_nodes(active_query()) + 1 > 2:
            raise ValueError("controller or global node allocation changed")
        require_fresh(root)
        c.atomic_json(contained(root / "upstream-completion-at-submit.json", root), receipt)
        record["upstream_completion_sha256"] = c.file_hash(root / "upstream-completion-at-submit.json")
        with contained(root / "submission-intent.json", root).open("xb") as stream: stream.write(c.canonical(record) + b"\n")
        uncertain = True
        job = runner(command, capture_output=True, text=True, check=True, timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", job):
            raise RuntimeError("unrecognized qsub response; intent and lock retained")
        record["job_id"] = job
        c.atomic_json(contained(root / "submission.json", root), record)
        uncertain = False
        return record
    finally:
        if not uncertain: lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    print(json.dumps(submit(args.bundle, args.root, execute=args.execute)))


if __name__ == "__main__": main()
