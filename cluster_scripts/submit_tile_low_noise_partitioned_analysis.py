"""Submit one measured-resource low-noise BAR partition with qsub exactly once."""
import argparse
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

import calibration as c
import tile_low_noise_partitioned_analysis as p
import submit_tile_low_noise_analysis_capacity as common
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def source_files():
    return p.source_files()


def bundle_binding(bundle,wrapper):
    binding=common.bundle_binding(bundle,wrapper)
    for name,source in source_files().items():
        path=common.contained(Path(bundle)/"cluster_scripts"/name,bundle)
        if not path.is_file() or c.file_hash(path)!=c.file_hash(source):
            raise ValueError("bundle source differs: "+name)
        binding["source_sha256"][name]=c.file_hash(path)
    return binding


def checked_plan(root,index):
    root=Path(root)
    for name in ("manifest.json","analysis_manifest.json","analysis-execution-intent.json",
                 "platform_profile.json","platform_fixture.json"):
        common.contained(root/name,root)
    path=common.contained(root/"partition_analysis_manifest.json",root)
    wrapper=p.read_plan(root)
    if c.canonical(json.loads(path.read_text()))!=c.canonical(wrapper):
        raise ValueError("saved partition manifest differs")
    parts=wrapper["resources"]["partitions"]
    if type(index) is not int or not 0<=index<len(parts):
        raise ValueError("invalid partition index")
    p.p.validate_partitions(wrapper["production"],wrapper["resources"])
    return wrapper


def require_fresh(root,wrapper,index):
    root=Path(root)
    destination=common.contained(root/"analysis-submissions"/str(index),root)
    for name in ("submission-intent.json","submission.json"):
        path=common.contained(destination/name,root)
        if path.exists() or path.is_symlink():
            raise ValueError("existing submission intent/ledger; never retry automatically")
    execution=common.contained(root/"analysis-partitions"/str(index),root)
    if execution.exists() or execution.is_symlink():
        raise ValueError("existing partition execution evidence")
    analysis=common.contained(root/"analysis",root)
    for group in wrapper["resources"]["partitions"][index]["groups"]:
        if any(analysis.glob(c.task_id(group)+".*")):
            raise ValueError("existing analysis group artifact")
    return destination


def submit(bundle,root,index,*,execute=False,controller_query=live_controllers,
           active_query=own_active_jobs,runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    if root==bundle/"runs" or not root.is_relative_to(bundle/"runs"):
        raise ValueError("production root must be inside bundle/runs")
    if any(char.isspace() for path in (bundle,root) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    wrapper=checked_plan(root,index)
    destination=require_fresh(root,wrapper,index)
    binding=bundle_binding(bundle,wrapper)
    fixed=wrapper["resources"]
    partition=fixed["partitions"][index]
    resource=dict(cpus=fixed["cpus"],memory_gb=fixed["memory_gb"],workers=fixed["workers"],
                  wall_seconds=partition["wall_seconds"],walltime=partition["walltime"],
                  requested_nodes=1,max_nodes=2)
    destination.mkdir(parents=True,exist_ok=True)
    invocation=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_low_noise_partitioned_analysis.py"),
                           "run","--root",str(root),"--partition",str(index)])
    script=f'''#!/bin/bash
#PBS -N m4q_low_bar
#PBS -q workq
#PBS -l select=1:ncpus=96:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {destination}/partition.out
#PBS -e {destination}/partition.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/'src'))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{invocation}
'''
    path=common.contained(destination/"partition.sh",root)
    if path.exists():
        if path.read_text()!=script: raise ValueError("existing partition script differs")
    else:
        with path.open("x",newline="\n") as stream: stream.write(script)
    command=["qsub",str(path)]
    record=dict(command=command,partition=index,partition_manifest=c.digest(wrapper),
                manifest=c.digest(wrapper["production"]),resource=resource,bundle_binding=binding,
                script_sha256=c.file_hash(path),submit_source_sha256=c.file_hash(__file__))
    if not execute:
        c.atomic_json(common.contained(destination/"dry_run.json",root),dict(record,job_id="dry-run"))
        return dict(record,job_id="dry-run")
    lock=bundle.parent/"tile-low-noise-submission.lock"
    with lock.open("xb") as stream:
        stream.write(c.canonical(dict(root=str(root),partition=index,pid=os.getpid()))+b"\n")
    uncertain=False
    try:
        require_fresh(root,wrapper,index)
        if controller_query(): raise ValueError("tile coordinator is running; do not compete for slots")
        if requested_nodes(active_query())+1>2:
            raise ValueError("two-node budget exceeded, including queued requests")
        if root.resolve()!=root or bundle.resolve()!=bundle:
            raise ValueError("bundle/output root changed before submission")
        current=checked_plan(root,index)
        require_fresh(root,current,index)
        if (c.digest(current)!=record["partition_manifest"] or bundle_binding(bundle,current)!=binding
                or c.file_hash(common.contained(path,root))!=record["script_sha256"]):
            raise ValueError("manifest, source, executable or script changed before qsub")
        with common.contained(destination/"submission-intent.json",root).open("xb") as stream:
            stream.write(c.canonical(record)+b"\n")
        uncertain=True
        job=runner(command,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unrecognized qsub response; intent and lock retained, inspect queue")
        record["job_id"]=job
        c.atomic_json(common.contained(destination/"submission.json",root),record)
        uncertain=False
        return record
    finally:
        if not uncertain: lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--partition",type=int,required=True)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,args.partition,execute=args.execute)))


if __name__=="__main__": main()
