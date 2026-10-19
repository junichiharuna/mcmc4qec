"""Submit the complete fixed weight-reference audit once, with a resource ceiling."""
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
import tile_weight_reference_audit_run as r
import submit_tile_low_noise_analysis_capacity as common
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def resources():
    return dict(requested_nodes=1,cpus=96,memory_gb=340,wall_seconds=86400,
                walltime="24:00:00",max_nodes=2,measured=False)


def source_files():
    files=common.source_files()
    directory=Path(__file__).resolve().parent
    pending=[r,c,*[inspect.getmodule(function) for function in (own_active_jobs,requested_nodes,live_controllers)]]
    seen=set()
    while pending:
        module=pending.pop()
        if id(module) in seen: continue
        seen.add(id(module))
        path=Path(module.__file__).resolve()
        if path.parent!=directory: continue
        files[path.name]=path
        pending.extend(value for value in vars(module).values()
                       if isinstance(value,types.ModuleType) and getattr(value,"__file__",None))
    files[Path(__file__).name]=Path(__file__).resolve()
    return files


def bundle_binding(bundle,plan):
    binding=common.bundle_binding(bundle,dict(production=plan["reference_context"]["reference"]))
    for name,source in source_files().items():
        path=common.contained(Path(bundle)/"cluster_scripts"/name,bundle)
        if not path.is_file() or c.file_hash(path)!=c.file_hash(source):
            raise ValueError("bundle source differs: "+name)
        binding["source_sha256"][name]=c.file_hash(path)
    return binding


def checked_plan(root,reference_root):
    plan=r.read_plan(root,reference_root)
    path=common.contained(root/"manifest.json",root)
    if (c.canonical(json.loads(path.read_text()))!=c.canonical(plan)
            or plan["reference_root"]!=str(reference_root)
            or plan["conditions"]!=list(range(16)) or plan["workers"]!=16
            or any(plan["resources"].get(key)!=value for key,value in resources().items())):
        raise ValueError("fixed audit plan differs")
    return plan


def require_fresh(root):
    for name in ("submission-intent.json","submission.json","execution-intent.json","native_preflight.json","summary.json","conditions"):
        path=common.contained(root/name,root)
        if path.exists() or path.is_symlink():
            raise ValueError("existing audit evidence; never retry automatically")


def submit(bundle,root,reference_root,*,execute=False,controller_query=live_controllers,
           active_query=own_active_jobs,runner=subprocess.run):
    bundle,root,reference_root=map(lambda value:Path(value).resolve(),(bundle,root,reference_root))
    if (root==bundle/"runs" or not root.is_relative_to(bundle/"runs")
            or root.is_relative_to(reference_root) or reference_root.is_relative_to(root)):
        raise ValueError("independent output root inside bundle/runs required")
    if any(char.isspace() for path in (bundle,root,reference_root) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    require_fresh(root)
    plan=checked_plan(root,reference_root)
    binding=bundle_binding(bundle,plan)
    invocation=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_weight_reference_audit_run.py"),
                           "run","--root",str(root),"--reference-root",str(reference_root)])
    script=f'''#!/bin/bash
#PBS -N m4q_wref_audit
#PBS -q workq
#PBS -l select=1:ncpus=96:mem=340gb
#PBS -l walltime=24:00:00
#PBS -o {root}/weight-reference-audit.out
#PBS -e {root}/weight-reference-audit.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/'src'))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{invocation}
'''
    path=common.contained(root/"weight-reference-audit.sh",root)
    if path.exists():
        if path.read_text()!=script: raise ValueError("existing audit script differs")
    else:
        with path.open("x",newline="\n") as stream: stream.write(script)
    command=["qsub",str(path)]
    record=dict(command=command,manifest=c.digest(plan),resource=resources(),workers=16,
                bundle_binding=binding,script_sha256=c.file_hash(path),submit_source_sha256=c.file_hash(__file__),
                warning="Initial resource ceiling, not measured use, runtime prediction or completion guarantee.")
    if not execute:
        c.atomic_json(common.contained(root/"dry_run.json",root),dict(record,job_id="dry-run"))
        return dict(record,job_id="dry-run")
    lock=bundle.parent/"tile-low-noise-submission.lock"
    with lock.open("xb") as stream:
        stream.write(c.canonical(dict(root=str(root),pid=os.getpid()))+b"\n")
    uncertain=False
    try:
        require_fresh(root)
        if controller_query(): raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query())+1>2: raise ValueError("two-node budget exceeded, including queued requests")
        job=plan["original_pbs_job_id"]
        query=runner(["qstat","-x","-f","-F","json",job],capture_output=True,text=True,check=True,timeout=30)
        if json.loads(query.stdout).get("Jobs",{}).get(job,{}).get("job_state")!="F":
            raise ValueError("reference generation job is not terminal")
        if any(path.resolve()!=path for path in (bundle,root,reference_root)):
            raise ValueError("fixed path changed before submission")
        current=checked_plan(root,reference_root)
        require_fresh(root)
        if (c.digest(current)!=record["manifest"] or bundle_binding(bundle,current)!=binding
                or c.file_hash(common.contained(path,root))!=record["script_sha256"]):
            raise ValueError("input, source, executable or script changed before qsub")
        with common.contained(root/"submission-intent.json",root).open("xb") as stream:
            stream.write(c.canonical(record)+b"\n")
        uncertain=True
        job=runner(command,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unrecognized qsub response; intent and lock retained, inspect queue")
        record["job_id"]=job
        c.atomic_json(common.contained(root/"submission.json",root),record)
        uncertain=False
        return record
    finally:
        if not uncertain: lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--reference-root",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,args.reference_root,execute=args.execute)))


if __name__=="__main__": main()
