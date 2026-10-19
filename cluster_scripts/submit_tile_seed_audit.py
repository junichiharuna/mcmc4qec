"""Measured, one-shot PBS execution of the frozen planned-seed census."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import types

import calibration as c
import tile_seed_audit as audit
import submit_tile_low_noise_analysis_capacity as common
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers

THREADS={key:"1" for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")}
DATA=Path("docs/wp/data_tile_validation_2026-10-17")


def locations(bundle,root):
    bundle,root=Path(bundle).resolve(),Path(root).resolve()
    if root==bundle/"runs" or not root.is_relative_to(bundle/"runs"):
        raise ValueError("run root must be within bundle/runs")
    if any(char.isspace() for path in (root,bundle) for char in str(path)):
        raise ValueError("PBS paths must not contain whitespace")
    return bundle,root


def resources(pilot,total,rss,sqlite_bytes):
    values=(pilot["seconds"],pilot["checked_entries"],total,rss,sqlite_bytes)
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<=0 for x in values):
        raise ValueError("positive measured pilot time, RSS and database size required")
    predicted=2*pilot["seconds"]*total/pilot["checked_entries"]
    memory=max(2,math.ceil(1.5*rss/1024+1))
    if predicted+300>1800 or memory>4:
        raise ValueError("measured pilot exceeds 30-minute / 4 GiB ceiling")
    disk=max(4*1024**3,math.ceil(2*sqlite_bytes*total/pilot["checked_entries"]+1024**3))
    return dict(cpus=1,memory_gb=memory,wall_seconds=1800,walltime="00:30:00",requested_nodes=1,max_nodes=2,
                predicted_seconds=predicted,measured_peak_rss_mb=rss,measured_sqlite_bytes=sqlite_bytes,
                disk_required_bytes=disk,warning="Measured extrapolation and initial ceiling, not a completion guarantee.")


def baseline_runtime(bundle):
    baseline=json.loads((bundle/DATA/"production_manifest.json").read_text())["runtime"]
    current=c.runtime()
    if any(current[key]!=baseline[key] for key in ("package_sha256","python","packages","driver_sha256")):
        raise ValueError("production baseline core runtime required")
    return baseline


def binding(bundle,evidence):
    baseline=baseline_runtime(bundle)
    result=common.bundle_binding(bundle,{"production":{"runtime":baseline}})
    sources=dict(evidence["source_sha256"])
    sources.update({str(Path(audit.__file__).resolve()):c.file_hash(audit.__file__),
                    str(Path(__file__).resolve()):c.file_hash(__file__)})
    # Include imported local helpers, including weight-stratification utilities.
    pending=[audit]
    visited=set()
    directory=Path(__file__).resolve().parent
    while pending:
        module=pending.pop()
        if id(module) in visited:continue
        visited.add(id(module))
        path=Path(module.__file__).resolve()
        if path.parent!=directory:continue
        sources[str(path)]=c.file_hash(path)
        pending.extend(value for value in vars(module).values()
                       if isinstance(value,types.ModuleType) and getattr(value,"__file__",None))
    extra={}
    for path,digest in sources.items():
        actual=common.contained(bundle/"cluster_scripts"/Path(path).name,bundle)
        if c.file_hash(actual)!=digest:
            raise ValueError("seed source differs from audited source")
        extra[str(actual)]=digest
    inputs=dict(evidence["input_sha256"])
    for name in ("decoder_platform_linux.json","decoder_platform_fixture.json"):
        path=common.contained(bundle/DATA/name,bundle)
        inputs[str(path)]=c.file_hash(path)
    for path,digest in inputs.items():
        common.contained(path,bundle)
        if c.file_hash(path)!=digest:
            raise ValueError("stored seed manifest or native input changed")
    result.update(seed_source_sha256=extra,input_sha256=inputs,baseline_runtime=baseline)
    return result


def bar_manifest_inputs(bundle,paths):
    """Bind optional BAR plans to their settings without renumbering conditions."""
    if not paths:return []
    import tile_bar_time_benchmark as bt
    records=[]
    occupied=set()
    payloads=set()
    for value in paths:
        path=common.contained(Path(value).resolve(),bundle)
        settings_path=common.contained((path.parent/"settings.json").resolve(),bundle)
        hashes=(c.file_hash(path),c.file_hash(settings_path))
        plan=json.loads(path.read_text())
        settings=json.loads(settings_path.read_text())
        purpose=plan.get("purpose")
        if purpose not in ("bar_time_capacity","bar_time_benchmark"):
            raise ValueError("BAR timing manifest purpose differs")
        expected=bt.make_plan(settings,capacity=purpose=="bar_time_capacity",case=plan["case"])
        if c.canonical(plan)!=c.canonical(expected):
            raise ValueError("BAR timing manifest differs from settings/source/runtime")
        digest=c.digest(plan)
        keys={(plan["seed_stage"],case) for case in (range(4) if plan["case"] is None else (plan["case"],))}
        if digest in payloads or occupied.intersection(keys):
            raise ValueError("duplicate BAR timing content or overlapping stage/case")
        if hashes!=(c.file_hash(path),c.file_hash(settings_path)):
            raise ValueError("BAR timing input changed during validation")
        occupied.update(keys)
        payloads.add(digest)
        records.append(dict(path=str(path),sha256=hashes[0],settings_path=str(settings_path),
                            settings_sha256=hashes[1],plan_digest=digest,
                            seed_stage=plan["seed_stage"],case=plan["case"],selection_digest=c.digest(settings),
                            selected_cases=sorted({row["case"] for row in plan["conditions"] if row["status"]=="selected"})))
    if len({row["selection_digest"] for row in records})!=1:
        raise ValueError("BAR timing manifests must share all eight selection outcomes")
    expected={(140,case) for case in range(4)} | {(141,case) for case in records[0]["selected_cases"]}
    if occupied!=expected:
        raise ValueError("BAR timing stage/case coverage is incomplete or includes empty capacity cases")
    return records


def bar_binding_evidence(evidence,records):
    """Keep auditor evidence exact while extending submitter input protection."""
    if not records:return evidence
    names={"bar.timing."+str(i) for i in range(len(records))}
    if {key for key in evidence["plan_sha256"] if key.startswith("bar.timing.")}!=names:
        raise ValueError("BAR timing catalog membership differs")
    inputs=dict(evidence["input_sha256"])
    for index,row in enumerate(records):
        if (inputs.get(row["path"])!=row["sha256"] or
                evidence["plan_sha256"].get("bar.timing."+str(index))!=row["plan_digest"]):
            raise ValueError("BAR timing catalog input/plan binding differs")
        inputs[row["settings_path"]]=row["settings_sha256"]
    return dict(evidence,input_sha256=inputs)


def prepare(bundle,root,*,bar_timing_manifests=()):
    bundle,root=locations(bundle,root)
    if root.exists() and any(root.iterdir()):
        raise ValueError("new empty run root required")
    baseline_runtime(bundle)
    bar_inputs=bar_manifest_inputs(bundle,bar_timing_manifests)
    factories,evidence=(audit.catalog(bundle/DATA,bar_timing_manifests=[row["path"] for row in bar_inputs])
                        if bar_inputs else audit.catalog(bundle/DATA))
    binding_evidence=bar_binding_evidence(evidence,bar_inputs)
    before=binding(bundle,binding_evidence)
    root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pilot-",dir=root) as temporary:
        database=Path(temporary)/"seed.sqlite"
        pilot=audit.census(audit.round_robin([f() for f in factories.values()]),evidence["planned_total"],
                           database,limit=min(1000,evidence["planned_total"]))
        resource=resources(pilot,evidence["planned_total"],c.peak_rss_mb(),database.stat().st_size)
    if (before!=binding(bundle,binding_evidence) or
            bar_inputs!=bar_manifest_inputs(bundle,[row["path"] for row in bar_inputs])):
        raise ValueError("source/input changed during pilot")
    if shutil.disk_usage(root).free<resource["disk_required_bytes"]:
        raise ValueError("insufficient scratch disk for planned census")
    if pilot["unexpected_collisions"]:
        raise ValueError("pilot has unexpected collisions")
    plan=dict(schema=1,purpose="tile_seed_census",bundle=str(bundle),root=str(root),
              audit_evidence=evidence,binding=before,pilot=pilot,resource=resource,
              auditor_sha256=c.file_hash(audit.__file__),submitter_sha256=c.file_hash(__file__),
              warning="Planned seed census only. Reserved namespaces remain unverified; no statistical stream-independence claim.")
    if bar_inputs:
        plan["bar_timing_manifests"]=bar_inputs
        plan["bar_timing_coverage"]=dict(main_cases=list(range(4)),capacity_cases=bar_inputs[0]["selected_cases"],
                                       zero_planned_seed_stages=[] if bar_inputs[0]["selected_cases"] else [141])
    with (root/"manifest.json").open("xb") as stream:
        stream.write(c.canonical(plan)+b"\n")
    return plan


def read_plan(bundle,root):
    bundle,root=locations(bundle,root)
    plan=json.loads(common.contained(root/"manifest.json",root).read_text())
    if (plan["purpose"]!="tile_seed_census" or plan["bundle"]!=str(bundle) or plan["root"]!=str(root)
            or plan["auditor_sha256"]!=c.file_hash(audit.__file__)
            or plan["submitter_sha256"]!=c.file_hash(__file__)):
        raise ValueError("fixed seed audit identity/source differs")
    stored=plan.get("bar_timing_manifests",[])
    bar_inputs=bar_manifest_inputs(bundle,[row["path"] for row in stored])
    if bar_inputs!=stored:
        raise ValueError("BAR timing manifest/settings binding changed")
    if stored and plan.get("bar_timing_coverage")!=dict(main_cases=list(range(4)),capacity_cases=stored[0]["selected_cases"],
                                                       zero_planned_seed_stages=[] if stored[0]["selected_cases"] else [141]):
        raise ValueError("BAR timing coverage proof differs")
    if not stored and any(key.startswith("bar.timing.") for key in plan["audit_evidence"].get("plan_sha256",{})):
        raise ValueError("BAR timing catalog inputs missing from plan")
    if binding(bundle,bar_binding_evidence(plan["audit_evidence"],bar_inputs))!=plan["binding"]:
        raise ValueError("seed audit input/source/runtime binding changed")
    old=plan["resource"]
    expected=resources(plan["pilot"],plan["audit_evidence"]["planned_total"],old["measured_peak_rss_mb"],old["measured_sqlite_bytes"])
    if expected!=old:
        raise ValueError("resource request differs from pilot")
    return plan


def validate_result(plan,result):
    full=result.get("full")
    total=plan["audit_evidence"]["planned_total"]
    if (not full or full.get("complete") is not True or full.get("planned_entries")!=total
            or full.get("checked_entries")!=total or full.get("unchecked_entries")!=0
            or full.get("unexpected_collisions")!=0
            or result.get("auditor_sha256")!=plan["auditor_sha256"]
            or c.canonical(result.get("evidence"))!=c.canonical(plan["audit_evidence"])):
        raise ValueError("full census absent, incomplete, collided or changed")
    reserved=plan["audit_evidence"]["reserved_unenumerated_stages"]
    return dict(planned_namespace_complete=True,all_goal_namespaces_complete=not reserved,
                reserved_unenumerated_stages=reserved,checked_entries=total,
                warning="Finite planned uniqueness is not executed-metadata validation or stream independence.")


def fresh(root,*,submission):
    names=["execution-intent.json","result.json","completion.json","scratch"]
    if submission:names.extend(("submission-intent.json","submission.json"))
    if any((root/name).exists() or (root/name).is_symlink() for name in names):
        raise ValueError("existing intent/output; inspect before any retry")


def run(bundle,root,*,runner=subprocess.run):
    bundle,root=locations(bundle,root)
    plan=read_plan(bundle,root)
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(k)!=v for k,v in THREADS.items()):
        raise ValueError("PBS and pinned one-thread environment required")
    fresh(root,submission=False)
    if shutil.disk_usage(root).free<plan["resource"]["disk_required_bytes"]:
        raise ValueError("insufficient scratch disk")
    command=[str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/tile_seed_audit.py"),
             "--data",str(bundle/DATA),"--full","--max-seconds","1800","--output",str(root/"result.json")]
    for row in plan.get("bar_timing_manifests",[]):
        command.extend(("--bar-timing-manifest",row["path"]))
    intent=dict(manifest=c.digest(plan),pbs_job_id=os.environ["PBS_JOBID"],command=command)
    with (root/"execution-intent.json").open("xb") as stream:
        stream.write(c.canonical(intent)+b"\n")
    (root/"scratch").mkdir()
    env=dict(os.environ,TMPDIR=str(root/"scratch"),TEMP=str(root/"scratch"),TMP=str(root/"scratch"))
    started=time.perf_counter()
    runner(command,check=True,env=env,timeout=1750)
    if c.digest(read_plan(bundle,root))!=intent["manifest"]:
        raise ValueError("plan/source changed during census")
    result=json.loads((root/"result.json").read_text())
    gate=validate_result(plan,result)
    proof=dict(gate,manifest=intent["manifest"],result_sha256=c.file_hash(root/"result.json"),
               pbs_job_id=intent["pbs_job_id"],wall_seconds=time.perf_counter()-started)
    c.atomic_json(root/"completion.json",proof)
    return proof


def submit(bundle,root,*,execute=False,controller_query=live_controllers,active_query=own_active_jobs,runner=subprocess.run):
    bundle,root=locations(bundle,root)
    fresh(root,submission=True)
    plan=read_plan(bundle,root)
    command=shlex.join([str(bundle/"venv/bin/python"),str(bundle/"cluster_scripts/submit_tile_seed_audit.py"),
                        "run","--bundle",str(bundle),"--root",str(root)])
    script=f'''#!/bin/bash
#PBS -N m4q_seed_audit
#PBS -q workq
#PBS -l select=1:ncpus=1:mem={plan['resource']['memory_gb']}gb
#PBS -l walltime=00:30:00
#PBS -o {root}/seed-audit.out
#PBS -e {root}/seed-audit.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(bundle/"src"))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
{command}
'''
    path=common.contained(root/"seed-audit.sh",root)
    if path.exists():
        if path.read_text()!=script:raise ValueError("existing script changed")
    else:
        with path.open("x",newline="\n") as stream:stream.write(script)
    record=dict(command=["qsub",str(path)],manifest=c.digest(plan),script_sha256=c.file_hash(path),resource=plan["resource"])
    if not execute:
        c.atomic_json(common.contained(root/"dry_run.json",root),dict(record,job_id="dry-run"))
        return dict(record,job_id="dry-run")
    lock=bundle.parent/"tile-low-noise-submission.lock"
    with lock.open("xb") as stream:stream.write(c.canonical(dict(root=str(root),pid=os.getpid()))+b"\n")
    uncertain=False
    try:
        fresh(root,submission=True)
        if controller_query():raise ValueError("tile coordinator running")
        if requested_nodes(active_query())+1>2:raise ValueError("two-node budget including queued jobs exceeded")
        if (bundle.resolve()!=bundle or root.resolve()!=root or c.digest(read_plan(bundle,root))!=record["manifest"]
                or c.file_hash(common.contained(path,root))!=record["script_sha256"]):
            raise ValueError("input/source/script changed before qsub")
        with (root/"submission-intent.json").open("xb") as stream:stream.write(c.canonical(record)+b"\n")
        uncertain=True
        job=runner(record["command"],capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",job):
            raise RuntimeError("unknown qsub response; inspect queue, intent and lock retained")
        record["job_id"]=job
        c.atomic_json(root/"submission.json",record)
        uncertain=False
        return record
    finally:
        if not uncertain:lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","submit","run"))
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--bar-timing-manifest",type=Path,action="append",default=[])
    args=parser.parse_args()
    if args.bar_timing_manifest and args.command!="plan":
        parser.error("--bar-timing-manifest is fixed by the plan command")
    result=(prepare(args.bundle,args.root,bar_timing_manifests=args.bar_timing_manifest) if args.command=="plan" else run(args.bundle,args.root)
            if args.command=="run" else submit(args.bundle,args.root,execute=args.execute))
    print(json.dumps({k:v for k,v in result.items() if k not in ("audit_evidence","binding")}))


if __name__=="__main__":main()
