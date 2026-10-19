"""Submit immutable low-noise sampling partitions or collection exactly once."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import calibration as c
import tile_low_noise_sampling_partitions as p
import submit_tile_low_noise_analysis_capacity as common
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def bundle_binding(bundle, wrapper):
    binding = common.bundle_binding(bundle, wrapper)
    for name, source in p.source_files().items():
        path = common.contained(Path(bundle)/"cluster_scripts"/name, bundle)
        if not path.is_file() or c.file_hash(path) != c.file_hash(source):
            raise ValueError("bundle source differs: " + name)
        binding["source_sha256"][name] = c.file_hash(path)
    return binding


def completed_partitions(root, wrapper, *, runner=None):
    for phase in p.PHASES:
        for part in wrapper["resources"][phase]["partitions"]:
            p.partition_evidence(root, wrapper, phase, part["index"], runner=runner)


def require_fresh(root, wrapper, phase, index):
    destination = p.submission_directory(root, phase, index)
    if phase == "collect":
        execution = p.path_in(root,"sampling-collection")
    else:
        p.tasks_for_partition(wrapper,phase,index)
        execution = p.partition_directory(root,phase,index)
        for task in p.tasks_for_partition(wrapper,phase,index):
            base = p.path_in(root,("traces/" if phase=="sample" else "anchors/")+c.task_id(task))
            if any(base.with_suffix(ext).exists() for ext in (".json",".npz",".done.json")):
                raise ValueError("existing raw artifact; no cached retry")
    if execution.exists() or execution.is_symlink(): raise ValueError("existing execution evidence")
    if any((destination/name).exists() for name in ("submission-intent.json","submission.json")):
        raise ValueError("existing submission intent/ledger; never retry automatically")
    return destination


def submit(bundle,root,phase,index=None,*,execute=False,controller_query=live_controllers,
           active_query=own_active_jobs,runner=subprocess.run):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    if root==bundle/"runs" or not root.is_relative_to(bundle/"runs"):
        raise ValueError("production root must be inside bundle/runs")
    if any(char.isspace() for path in (bundle,root) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    if phase not in (*p.PHASES,"collect") or (phase=="collect" and index is not None):
        raise ValueError("invalid phase/index")
    wrapper=p.read_plan(root)
    destination=require_fresh(root,wrapper,phase,index)
    binding=bundle_binding(bundle,wrapper)
    resource=p.partition_resource(wrapper,phase,index)
    # Collection planning seals completed generator receipts with read-only qstat calls.
    if phase=="collect": completed_partitions(root,wrapper,runner=runner)
    destination.mkdir(parents=True,exist_ok=True)
    args=[str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_low_noise_sampling_partitions.py"),
          "collect" if phase=="collect" else "run","--root",str(root)]
    if phase!="collect": args.extend(["--phase",phase,"--index",str(index)])
    script=f'''#!/bin/bash
#PBS -N m4q_low_part
#PBS -q workq
#PBS -l select=1:ncpus={resource['cpus']}:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {destination}/partition.out
#PBS -e {destination}/partition.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/'src'))}
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{shlex.join(args)}
'''
    path=p.path_in(root,str((destination/"partition.sh").relative_to(root)))
    if path.exists():
        if path.read_text()!=script: raise ValueError("existing script differs")
    else:
        with path.open("x",newline="\n") as stream: stream.write(script)
    record=dict(command=["qsub",str(path)],manifest=c.digest(wrapper),phase=phase,partition=index,
                resource=resource,bundle=str(bundle),bundle_binding=binding,script_sha256=c.file_hash(path))
    if not execute:
        result=dict(record,job_id="dry-run")
        c.atomic_json(destination/"dry_run.json",result)
        return result
    lock=bundle.parent/"tile-low-noise-submission.lock"
    with lock.open("xb") as stream: stream.write(c.canonical(dict(root=str(root),phase=phase,index=index,pid=os.getpid())))
    uncertain=False
    try:
        require_fresh(root,wrapper,phase,index)
        if controller_query(): raise ValueError("tile coordinator running; do not compete for slots")
        if requested_nodes(active_query())+1>2: raise ValueError("two-node budget exceeded including queued jobs")
        if phase=="collect": completed_partitions(root,wrapper,runner=runner)
        else:
            job=wrapper["capacity_evidence"]["pbs_job_id"]
            result=runner(["qstat","-x","-f","-F","json",job],capture_output=True,text=True,check=True,timeout=30)
            state=json.loads(result.stdout).get("Jobs",{}).get(job,{})
            if state.get("job_state")!="F" or state.get("Exit_status")!=0:
                raise ValueError("capacity job is not successfully terminal")
        current=p.read_plan(root)
        require_fresh(root,current,phase,index)
        if (c.digest(current)!=record["manifest"] or bundle_binding(bundle,current)!=binding
                or c.file_hash(path)!=record["script_sha256"]):
            raise ValueError("source, plan, executable or script changed before qsub")
        if controller_query() or requested_nodes(active_query())+1>2:
            raise ValueError("global controller/node gate changed before qsub")
        with (destination/"submission-intent.json").open("xb") as stream: stream.write(c.canonical(record)+b"\n")
        uncertain=True
        job=runner(record["command"],capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job): raise RuntimeError("ambiguous qsub response; retain lock and inspect queue")
        result=dict(record,job_id=job)
        c.atomic_json(destination/"submission.json",result)
        uncertain=False
        return result
    finally:
        if not uncertain: lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--phase",choices=(*p.PHASES,"collect"),required=True)
    parser.add_argument("--index",type=int)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    print(json.dumps(submit(args.bundle,args.root,args.phase,args.index,execute=args.execute)))


if __name__=="__main__": main()
