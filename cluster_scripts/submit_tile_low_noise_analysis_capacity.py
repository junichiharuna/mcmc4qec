"""One-shot qsub for synthetic low-noise analysis resource profiling only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import types

import calibration as c
import tile_low_noise_analysis_capacity as m
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def source_files():
    """Bind local driver dependencies used by the submitted Python command."""
    directory=Path(__file__).resolve().parent
    result={Path(__file__).name:Path(__file__).resolve()}
    pending=[m,c]
    seen=set()
    while pending:
        module=pending.pop()
        if id(module) in seen:
            continue
        seen.add(id(module))
        path=Path(module.__file__).resolve()
        if path.parent!=directory:
            continue
        result[path.name]=path
        pending.extend(value for value in vars(module).values()
                       if isinstance(value,types.ModuleType) and getattr(value,"__file__",None))
    return result


def contained(path, parent):
    path,parent=Path(path),Path(parent).resolve()
    if not path.resolve().is_relative_to(parent):
        raise ValueError("path escapes fixed root")
    return path


def read_plan(root):
    root=Path(root).resolve()
    plan=json.loads(contained(root/"manifest.json",root).read_text())
    if plan.get("purpose")!="low_noise_synthetic_analysis_capacity" or plan.get("synthetic") is not True:
        raise ValueError("synthetic analysis capacity manifest required")
    base=plan["production"]
    if c.canonical(plan)!=c.canonical(m.make_plan(base["case"],base["target_index"])):
        raise ValueError("fixed synthetic manifest/source/runtime differs")
    for key,digest in plan["native_input_digests"].items():
        if c.digest(json.loads(contained(root/(key+".json"),root).read_text()))!=digest:
            raise ValueError("native input changed")
    return plan


def bundle_binding(bundle, plan):
    bundle=Path(bundle).resolve()
    hashes={}
    for name,path in source_files().items():
        target=contained(bundle/"cluster_scripts"/name,bundle)
        if not target.is_file() or c.file_hash(target)!=c.file_hash(path):
            raise ValueError("bundle source differs: "+name)
        hashes[name]=c.file_hash(target)
    package=contained(bundle/"src/mcmc4qec",bundle)
    digest=hashlib.sha256()
    files=sorted(package.rglob("*.py"))
    if not files:
        raise ValueError("bundle source package missing")
    for path in files:
        contained(path,package)
        digest.update(path.relative_to(package).as_posix().encode()+b"\0")
        digest.update(path.read_bytes())
    if digest.hexdigest()!=plan["production"]["runtime"]["package_sha256"]:
        raise ValueError("bundle package differs")
    # Deployed bundles intentionally share the pinned external venv.
    executable=(bundle/"venv/bin/python").resolve()
    if not executable.is_file():
        raise ValueError("bundle Python executable missing")
    return dict(source_sha256=hashes,package_sha256=digest.hexdigest(),
                python_path=str(executable),python_sha256=c.file_hash(executable))


def capacity_resources():
    return dict(cpus=96,memory_gb=340,wall_seconds=86400,walltime="24:00:00",
                workers=8,requested_nodes=1,max_nodes=2,synthetic=True,
                warning="Initial resource ceiling, not measured use or completion prediction; synthetic data are not scientific evidence.")


def require_fresh(root):
    for name in ("submission-intent.json","submission.json","execution-intent.json","summary.json","profiles"):
        path=root/name
        if path.exists() or path.is_symlink():
            raise ValueError("existing intent/output; inspect job, never retry automatically")


def submit(bundle, root, *, execute=False, controller_query=live_controllers,
           active_query=own_active_jobs, runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    if root==bundle/"runs" or not root.is_relative_to(bundle/"runs"):
        raise ValueError("capacity root must be inside bundle/runs")
    if any(char.isspace() for path in (root,bundle) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    require_fresh(root)
    plan=read_plan(root)
    binding=bundle_binding(bundle,plan)
    resource=capacity_resources()
    command=shlex.join([str(bundle/"venv/bin/python"),
        str(bundle/"cluster_scripts/tile_low_noise_analysis_capacity.py"),"run","--root",str(root)])
    script=f'''#!/bin/bash
#PBS -N m4q_low_acap
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=340gb
#PBS -l walltime=24:00:00
#PBS -o {root}/analysis-capacity.out
#PBS -e {root}/analysis-capacity.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/"src"))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{command}
'''
    path=contained(root/"analysis-capacity.sh",root)
    if path.exists():
        if path.read_text()!=script:
            raise ValueError("existing submission script differs")
    else:
        with path.open("x",newline="\n") as stream:
            stream.write(script)
    command=["qsub",str(path)]
    record=dict(command=command,manifest=c.digest(plan),resource=resource,bundle_binding=binding,
                script_sha256=c.file_hash(path),submit_source_sha256=c.file_hash(__file__))
    if not execute:
        c.atomic_json(contained(root/"dry_run.json",root),dict(record,job_id="dry-run"))
        return dict(record,job_id="dry-run")
    lock=bundle.parent/"tile-low-noise-submission.lock"
    with lock.open("xb") as stream:
        stream.write(c.canonical(dict(root=str(root),pid=os.getpid()))+b"\n")
    uncertain=False
    try:
        require_fresh(root)
        if controller_query():
            raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query())+1>2:
            raise ValueError("two-node budget exceeded, including queued requests")
        if root.resolve()!=root or bundle.resolve()!=bundle:
            raise ValueError("bundle/output root changed before submission")
        current=read_plan(root)
        if (c.digest(current)!=record["manifest"] or bundle_binding(bundle,current)!=binding
                or c.file_hash(contained(path,root))!=record["script_sha256"]):
            raise ValueError("manifest, source, executable or script changed before qsub")
        with (root/"submission-intent.json").open("xb") as stream:
            stream.write(c.canonical(record)+b"\n")
        uncertain=True
        job=runner(command,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unrecognized qsub response; intent and lock retained, inspect queue")
        record["job_id"]=job
        c.atomic_json(root/"submission.json",record)
        uncertain=False
        return record
    finally:
        if not uncertain:
            lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,execute=args.execute)))


if __name__=="__main__":
    main()
