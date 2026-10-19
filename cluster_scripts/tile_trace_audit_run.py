"""Measure and run fixed trace-audit cohorts in the generating native environment."""
import argparse
import itertools
import json
import os
from pathlib import Path
import socket
import time
import traceback

import calibration as c
import tile_bar_study as b
import audit_tile_traces as a


THREADS={name:"1" for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")}
WARNING=a.WARNING+" Capacity is a fixed subset for resource measurement, not full-cohort validation. Timings include group audit persistence; the measurement record write is excluded."


def make_plan(sampling,case,profile,fixture,*,capacity):
    if c.canonical(sampling)!=c.canonical(b.make_plan()) or sampling["replicates"]!=192 or case not in range(4):
        raise ValueError("fixed production manifest and valid case required")
    if profile.get("fixture")!=c.digest(fixture) or not profile.get("native_ldpc_sha256"):
        raise ValueError("native profile/fixture binding required")
    return dict(schema=1,purpose="trace_audit_capacity" if capacity else "trace_audit_full",case=case,
                replicates=24 if capacity else 192,sampling_manifest=c.digest(sampling),
                platform_profile=c.digest(profile),platform_fixture=c.digest(fixture),
                runtime=b.runtime(),sources={"wrapper":c.file_hash(__file__),"audit":c.file_hash(a.__file__),
                    "native_probe":c.file_hash(a.platform_probe.__file__)},required_threads=THREADS,warning=WARNING)


def groups(plan):
    return [(plan["case"],*tail) for tail in itertools.product(range(2),range(2),range(plan["replicates"]))]


def read_plan(root,source):
    root,source=Path(root),Path(source)
    plan=json.loads((root/"manifest.json").read_text())
    sampling=json.loads((root/"sampling_manifest.json").read_text())
    if c.canonical(sampling)!=c.canonical(json.loads((source/"manifest.json").read_text())):
        raise ValueError("sampling manifest changed")
    profile=json.loads((root/"platform_profile.json").read_text())
    fixture=json.loads((root/"platform_fixture.json").read_text())
    if c.canonical(plan)!=c.canonical(make_plan(sampling,plan["case"],profile,fixture,
                                             capacity=plan["purpose"]=="trace_audit_capacity")):
        raise ValueError("audit plan, source, native inputs or runtime changed")
    return plan,sampling


def run_group(args):
    source,root,sampling,plan,group=args
    root=Path(root)
    started,cpu=time.perf_counter(),time.process_time()
    record=dict(group=list(group),status="ok")
    try:
        audit_path=root/"audit/groups"/c.task_id(group)
        if audit_path.with_suffix(".done.json").exists():
            raise ValueError("cached audit must not masquerade as fresh resource measurement")
        result=a.audit_group((source,root/"audit",sampling,plan,group))
        record.update({key:result[key] for key in ("tasks","failed_sampling","redecoded_checkpoints")})
        record["audit_marker_sha256"]=c.file_hash(audit_path.with_suffix(".done.json"))
    except Exception as error:
        record.update(status="failed",error=repr(error),traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
                  peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(root/"measurements"/c.task_id(group),dict(manifest=c.digest(plan),group=list(group)),{},record)
    return record


def run(root,source,*,workers=96):
    if not os.environ.get("PBS_JOBID") or workers!=96 or any(os.environ.get(k)!=v for k,v in THREADS.items()):
        raise ValueError("96-worker qsub job with pinned single-thread environment required")
    root,source=Path(root),Path(source)
    plan,sampling=read_plan(root,source)
    intent=root/"execution_intent.json"
    if intent.exists() or (root/"measurements").exists() or (root/"audit").exists():
        raise ValueError("existing execution; inspect recorded job, never reuse cached measurements")
    with intent.open("xb") as stream:
        stream.write(c.canonical(dict(manifest=c.digest(plan),pbs_job_id=os.environ["PBS_JOBID"]))+b"\n")
    started=time.perf_counter()
    actual=a.platform_probe.probe(json.loads((root/"platform_fixture.json").read_text()))
    a.validate_platform(json.loads((root/"platform_profile.json").read_text()),actual)
    c.atomic_json(root/"native_preflight.json",dict(manifest=c.digest(plan),profile=actual,
        hostname=socket.gethostname(),pbs_job_id=os.environ["PBS_JOBID"],wall_seconds=time.perf_counter()-started))
    started=time.perf_counter()
    expected=groups(plan)
    records=c.parallel_map(run_group,[(str(source),str(root),sampling,plan,g) for g in expected],workers)
    records.sort(key=lambda row:row["group"])
    if [tuple(row["group"]) for row in records]!=expected:
        raise ValueError("missing, duplicate or reordered audit groups")
    summary=dict(manifest=c.digest(plan),groups=len(records),failed_audits=sum(row["status"]!="ok" for row in records),
                 phase_wall_seconds=time.perf_counter()-started,records=records,
                 native_preflight_sha256=c.file_hash(root/"native_preflight.json"),warning=WARNING)
    c.atomic_json(root/"summary.json",summary)
    if summary["failed_audits"]:
        raise RuntimeError("audit failures retained; inspect inputs and provenance before further work")
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run"))
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4))
    parser.add_argument("--capacity",action="store_true")
    parser.add_argument("--platform-profile",type=Path)
    parser.add_argument("--platform-fixture",type=Path)
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if args.command=="plan":
        if args.case is None or args.platform_profile is None or args.platform_fixture is None or (args.root.exists() and any(args.root.iterdir())):
            raise ValueError("new empty root, case and native inputs required")
        sampling=json.loads((args.source_root/"manifest.json").read_text())
        profile=json.loads(args.platform_profile.read_text())
        fixture=json.loads(args.platform_fixture.read_text())
        plan=make_plan(sampling,args.case,profile,fixture,capacity=args.capacity)
        for name,value in (("sampling_manifest",sampling),("platform_profile",profile),("platform_fixture",fixture),("manifest",plan)):
            c.atomic_json(args.root/(name+".json"),value)
        print(json.dumps(plan))
        return
    summary=run(args.root,args.source_root,workers=args.workers)
    print(json.dumps({k:v for k,v in summary.items() if k!="records"}))


if __name__=="__main__":
    main()
