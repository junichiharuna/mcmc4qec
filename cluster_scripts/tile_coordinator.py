"""Lightweight, fail-closed continuation of the frozen two-node PBS study.

Only existing submitters call qsub. This process does no sampling or analysis,
does not cancel jobs, and never retries an ambiguous submission automatically.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time

import calibration as c
import submit_tile_analysis as a
from submit_tile_capacity import requested_nodes


class ObservationError(RuntimeError):
    """A queue observation failed; no new submission is allowed this tick."""


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def choose(config,samples,analyses,nodes):
    if len(samples)!=4 or len(analyses)!=4 or any(x not in ("absent","live","complete") for x in samples+analyses) or nodes<0:
        raise ValueError("invalid scheduling state")
    if all(x=="complete" for x in analyses):
        return dict(action="finished")
    if nodes>=2:
        return dict(action="wait",reason="node_budget")
    for case in config["order"]:
        if samples[case]=="absent":
            return dict(action="sample",case=case)
    for case in config["analysis_order"]:
        if samples[case]=="complete" and analyses[case]=="absent":
            return dict(action="analyze",case=case)
    return dict(action="wait",reason="existing_jobs")


def ledger_path(config,action):
    prefix="submission" if action["action"]=="sample" else "analysis_submission"
    return Path(config["bundle"])/"runs/production"/f"{prefix}-{action['case']}.json"


def submit_action(config,action,state_dir,runner=subprocess.run):
    stage,case=action["action"],action["case"]
    if stage not in ("sample","analyze") or case not in range(4):
        raise ValueError("not a planned submission")
    state_dir=Path(state_dir)
    identity=f"{stage}-{case}"
    intent=state_dir/f"intent-{identity}.json"
    ledger=ledger_path(config,action)
    if intent.exists() or ledger.exists():
        raise ValueError("submission/intent exists; inspect existing job, never retry automatically")
    if stage=="sample":
        command=[config["python"],str(Path(config["bundle"])/"cluster_scripts/submit_tile_production.py"),
                 "next","--bundle",config["bundle"],"--execute"]
    else:
        command=[config["python"],str(Path(config["controller"])/"cluster_scripts/submit_tile_analysis.py"),
                 "submit","--bundle",config["bundle"],"--profile-root",config["profile_root"],"--case",str(case),"--execute"]
    with intent.open("xb") as stream:
        stream.write(c.canonical(dict(action=action,command=command,created_utc=now()))+b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    result=runner(command,text=True,capture_output=True,check=True,timeout=300)
    response=json.loads(result.stdout)
    record=read(ledger)
    if response["job_id"]!=record["job_id"] or record["case"]!=case or not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",record["job_id"]):
        raise ValueError("submission receipt differs from ledger")
    receipt=dict(action=action,job_id=record["job_id"],ledger=str(ledger),ledger_sha256=c.file_hash(ledger),
                 intent_sha256=c.file_hash(intent),acknowledged_utc=now())
    c.atomic_json(state_dir/f"receipt-{identity}.json",receipt)
    return receipt


def query_jobs(ids=None):
    command=["qstat",*( ["-x"] if ids is not None else []),"-f","-F","json",*(ids or [])]
    try:
        result=subprocess.run(command,text=True,capture_output=True,check=True,timeout=30)
        jobs=json.loads(result.stdout).get("Jobs",{})
        if ids is not None and any(job not in jobs for job in ids):
            raise ObservationError("a known job is absent from qstat; inspect, do not resubmit")
        return jobs
    except (subprocess.SubprocessError,ValueError,OSError) as error:
        raise ObservationError(str(error)) from error


def query_active():
    import pwd
    user=pwd.getpwuid(os.getuid()).pw_name
    return {job:data for job,data in query_jobs().items()
            if data.get("Job_Owner","").split("@")[0]==user and data.get("job_state") not in ("F","X")}


def snapshot(config,job_query=query_jobs,active_query=query_active):
    root=Path(config["bundle"])/"runs/production"
    plan=read(root/"manifest.json")
    context=read(root/"analysis_manifest.json")
    ledgers={}
    for stage in ("sample","analyze"):
        for case in range(4):
            path=ledger_path(config,dict(action=stage,case=case))
            if path.exists():
                record=read(path)
                if record["manifest"]!=c.digest(plan) or record["case"]!=case:
                    raise ValueError("submission ledger identity changed")
                ledgers[stage,case]=record["job_id"]
    ids=list(ledgers.values())
    if len(ids)!=len(set(ids)):
        raise ValueError("job ID reused across ledgers")
    jobs=job_query(ids) if ids else {}
    active=active_query()
    states={stage:["absent"]*4 for stage in ("sample","analyze")}
    for (stage,case),job in ledgers.items():
        status=jobs[job]["job_state"]
        if status!="F":
            if status not in ("Q","R","E","H","W","T","S","B","U"):
                raise ValueError(f"unrecognized PBS state {job}: {status}")
            states[stage][case]="live"
            continue
        if stage=="sample":
            # Nonzero exit with complete recorded failures is still analyzed.
            a.check_completed_case(plan,case,read(root/f"sample-{case}.json"),read(root/f"anchors-{case}.json"))
        else:
            summary=read(root/f"summary-{case}.json")
            if jobs[job].get("Exit_status")!=0 or summary["analysis"]!=c.digest(context) or summary["case"]!=case:
                raise ValueError("analysis failed or summary identity differs; inspect existing job")
        states[stage][case]="complete"
    for case,status in enumerate(states["analyze"]):
        if status!="absent" and states["sample"][case]!="complete":
            raise ValueError("analysis ledger precedes completed sampling")
    return dict(observed_utc=now(),jobs={job:dict(job_state=data["job_state"],exit_status=data.get("Exit_status")) for job,data in jobs.items()},
                active_jobs=list(active),requested_nodes=requested_nodes(active),**states)


def validate_pins(config,state_dir):
    for path,expected in config["pins"].items():
        if c.file_hash(path)!=expected:
            raise ValueError(f"pinned source/plan changed: {path}")
    for intent in Path(state_dir).glob("intent-*.json"):
        receipt=intent.with_name(intent.name.replace("intent-","receipt-",1))
        if not receipt.exists():
            raise ValueError("unacknowledged submission intent; inspect qstat before any restart")
        record=read(receipt)
        if record["intent_sha256"]!=c.file_hash(intent) or record["ledger_sha256"]!=c.file_hash(record["ledger"]):
            raise ValueError("submission acknowledgement changed")


def initialize(bundle,controller,profile,output):
    bundle,controller,profile,output=map(lambda path:Path(path).resolve(),(bundle,controller,profile,output))
    if output.exists():
        raise ValueError("coordinator config already exists")
    root=bundle/"runs/production"
    resources=read(root/"resource_plan.json")
    analysis_resources=read(root/"analysis_resource_plan.json")
    if resources["max_nodes"]!=2 or analysis_resources["max_nodes"]!=2 or sorted(resources["order"])!=list(range(4)):
        raise ValueError("fixed four-case/two-node plan required")
    paths={*bundle.joinpath("cluster_scripts").glob("*.py"),*controller.joinpath("cluster_scripts").glob("*.py"),
           *Path(__file__).resolve().parent.glob("*.py"),
           *(root/name for name in ("manifest.json","analysis_manifest.json","resource_plan.json","analysis_resource_plan.json","reference_summary.json")),
           profile/"manifest.json",profile/"summary.json",bundle/"capacity_manifest.json",bundle/"capacity_summary.json"}
    config=dict(bundle=str(bundle),controller=str(controller),profile_root=str(profile),
                python=str(bundle/"venv/bin/python"),order=resources["order"],
                analysis_order=[row["case"] for row in sorted(analysis_resources["cases"],key=lambda row:-row["predicted_analysis_seconds"])],
                poll_seconds=60,max_hours=72,max_nodes=2,pins={str(path):c.file_hash(path) for path in sorted(paths)},created_utc=now())
    c.atomic_json(output,config)
    return config


def run(config_path):
    config_path=Path(config_path).resolve()
    config=read(config_path)
    state_dir=config_path.parent
    validate_pins(config,state_dir)
    # A stale marker is not permission to restart. No cleanup/retry is automatic.
    with (state_dir/"process.json").open("x") as stream:
        json.dump(dict(pid=os.getpid(),hostname=socket.gethostname(),started_utc=now(),
                       config_sha256=c.file_hash(config_path),source_sha256=c.file_hash(__file__)),stream)
    deadline=time.monotonic()+3600*config["max_hours"]
    while time.monotonic()<deadline:
        try:
            if read(config_path)!=config:
                raise ValueError("coordinator config changed")
            validate_pins(config,state_dir)
            observation=snapshot(config)
            action=choose(config,observation["sample"],observation["analyze"],observation["requested_nodes"])
            event=dict(observation=observation,decision=action)
            if action["action"] in ("sample","analyze"):
                event["receipt"]=submit_action(config,action,state_dir)
        except ObservationError as error:
            event=dict(observed_utc=now(),decision=dict(action="wait",reason="observation_error"),error=str(error))
        except Exception as error:
            c.atomic_json(state_dir/"status.json",dict(observed_utc=now(),status="stopped_error",error=repr(error)))
            raise
        c.atomic_json(state_dir/"status.json",event)
        with (state_dir/"events.jsonl").open("ab") as stream:
            stream.write(c.canonical(event)+b"\n")
        if event["decision"]["action"]=="finished":
            return
        time.sleep(config["poll_seconds"])
    c.atomic_json(state_dir/"status.json",dict(observed_utc=now(),status="deadline_reached",warning="Existing jobs were not cancelled."))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("init","status","run"))
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--bundle",type=Path)
    parser.add_argument("--controller",type=Path)
    parser.add_argument("--profile-root",type=Path)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    if args.command=="init":
        initialize(args.bundle,args.controller,args.profile_root,args.config)
        print(json.dumps(dict(config=str(args.config),sha256=c.file_hash(args.config))))
    elif args.command=="status":
        config=read(args.config)
        validate_pins(config,args.config.parent)
        observation=snapshot(config)
        print(json.dumps(dict(observation=observation,decision=choose(config,observation["sample"],observation["analyze"],observation["requested_nodes"]))))
    else:
        if not args.execute:
            raise ValueError("run requires explicit --execute; use status for read-only inspection")
        run(args.config)


if __name__=="__main__":
    main()
