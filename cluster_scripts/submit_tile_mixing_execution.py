"""Submit one measured-inventory job under the shared two-node lock."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_mixing_execution as r
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def bundle_binding(bundle,plan):
    bundle=Path(bundle).resolve(); hashes={}
    for name,source in r.source_files().items():
        path=bundle/"cluster_scripts"/name
        if not path.resolve().is_relative_to(bundle) or c.file_hash(path) != c.file_hash(source):
            raise ValueError("bundle source differs")
        hashes[name]=c.file_hash(path)
    package=bundle/"src/mcmc4qec"; digest=hashlib.sha256(); files=sorted(package.rglob("*.py"))
    if not files: raise ValueError("missing core package")
    for path in files:
        if not path.resolve().is_relative_to(package.resolve()): raise ValueError("package escaped")
        digest.update(path.relative_to(package).as_posix().encode()+b"\0"); digest.update(path.read_bytes())
    executable=(bundle/"venv/bin/python").resolve()
    if digest.hexdigest() != plan["snapshot"]["runtime"]["package_sha256"] or c.file_hash(executable) != plan["snapshot"]["python_sha256"]:
        raise ValueError("core/Python binding differs")
    return dict(source_sha256=hashes,package_sha256=digest.hexdigest(),python_sha256=c.file_hash(executable),python_path=str(executable))


def submit(bundle,root,*,execute=False,controller_query=live_controllers,active_query=own_active_jobs,runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    if root == bundle/"runs" or not root.is_relative_to(bundle/"runs") or any(ch.isspace() for p in (root,bundle) for ch in str(p)):
        raise ValueError("new root under bundle/runs without whitespace required")
    r.require_fresh(root); plan=r.read_plan(root); binding=bundle_binding(bundle,plan); res=plan["resources"]
    command=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_mixing_execution.py"),"run","--root",str(root)])
    script=f'''#!/bin/bash
#PBS -N m4q_mix{plan['case']}
#PBS -q workq
#PBS -l select=1:ncpus=1:mem={res['memory_gb']}gb
#PBS -l walltime={res['walltime']}
#PBS -o {root}/inventory.out
#PBS -e {root}/inventory.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/'src')+':'+str(bundle/'cluster_scripts'))}
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
{command}
'''
    path=root/"inventory.sh"
    if path.exists():
        if path.read_text() != script: raise ValueError("existing script differs")
    else:
        with path.open("x",newline="\n") as stream: stream.write(script)
    record=dict(command=["qsub",str(path)],manifest=c.digest(plan),resource=res,bundle_binding=binding,
                script_sha256=c.file_hash(path),submit_source_sha256=c.file_hash(__file__))
    if not execute:
        c.atomic_json(root/"dry_run.json",dict(record,job_id="dry-run")); return dict(record,job_id="dry-run")
    lock=bundle.parent/"tile-low-noise-submission.lock"
    with lock.open("xb") as stream: stream.write(c.canonical(dict(root=str(root),pid=os.getpid()))+b"\n")
    uncertain=False
    try:
        r.require_fresh(root)
        if controller_query() or requested_nodes(active_query()) + 1 > 2: raise ValueError("controller active or two-node budget exceeded")
        jobs=[plan["snapshot"]["job_id"]]
        scripts=[Path(plan["snapshot"]["final_root"])/"reaggregate.sh"]
        if plan["capacity"]:
            cap=Path(plan["capacity"]["root"]); jobs.append(r.read_json(cap/"submission.json")["job_id"]); scripts.append(cap/"inventory.sh")
        terminal=json.loads(runner(["qstat","-x","-f","-F","json",*jobs],capture_output=True,text=True,check=True,timeout=30).stdout)
        for job,script_path in zip(jobs,scripts): r.check_job(terminal,job,script_path)
        selected={"Jobs":{job:{k:v for k,v in terminal["Jobs"][job].items() if k in
                   ("job_state","Exit_status","Submit_arguments","Resource_List","resources_used","Job_Name","Job_Owner","queue","stime","obittime")}
                   for job in jobs}}
        if (r.read_plan(root) != plan or bundle_binding(bundle,plan) != binding or c.file_hash(path) != record["script_sha256"]):
            raise ValueError("input/source/script changed")
        if controller_query() or requested_nodes(active_query()) + 1 > 2: raise ValueError("controller or allocation changed")
        r.require_fresh(root); c.atomic_json(root/"upstream-completion-at-submit.json",selected)
        record["upstream_completion_sha256"]=c.file_hash(root/"upstream-completion-at-submit.json")
        with (root/"submission-intent.json").open("xb") as stream: stream.write(c.canonical(record)+b"\n")
        uncertain=True
        job=runner(record["command"],capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job): raise RuntimeError("ambiguous qsub; retain lock and intent")
        record["job_id"]=job; c.atomic_json(root/"submission.json",record); uncertain=False
        return record
    finally:
        if not uncertain: lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True); parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--execute",action="store_true"); args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,execute=args.execute)))


if __name__=="__main__": main()
