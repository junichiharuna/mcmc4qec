"""Measure a fixed saved-diagnostic group, then run the unchanged full inventory."""
import argparse
import ast
import json
import math
import os
from pathlib import Path
import shlex
import socket
import sys
import time
import traceback

import calibration as c
import tile_audited_results as audited
import tile_final_reaggregation as final
import tile_mixing_inventory as inventory

THREADS = final.THREADS
WARNING = "Saved diagnostic inventory only; fixed one-group capacity extrapolation is not a completion guarantee. No new numerical diagnostics or convergence/coverage proof."


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resources(measured=None):
    wall, memory = 1800, 4
    if measured is not None:
        seconds, rss = measured["wall_seconds"], measured["peak_rss_mb"]
        if any(type(value) not in (int,float) or not math.isfinite(value) or value <= 0 for value in (seconds,rss)):
            raise ValueError("positive finite measured resources required")
        wall = max(1800, math.ceil((seconds * 768 * 2 + 600) / 1800) * 1800)
        memory = max(4, math.ceil(rss * 2 / 1024 + 1))
    if wall > 86400 or memory > 340: raise ValueError("capacity exceeds limits; partition before submission")
    return dict(requested_nodes=1,cpus=1,memory_gb=memory,wall_seconds=wall,
                walltime=f"{wall//3600:02d}:{wall%3600//60:02d}:00",max_nodes=2,measured=measured is not None)


def source_files():
    directory = Path(__file__).resolve().parent
    pending = [Path(__file__).name, "submit_tile_mixing_execution.py"]
    found = {}
    while pending:
        name = pending.pop()
        if name in found: continue
        path = directory / name
        if not path.is_file(): raise ValueError("missing source: " + name)
        found[name] = path
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            imports = ([item.name.split(".")[0] for item in node.names] if isinstance(node,ast.Import)
                       else [node.module.split(".")[0]] if isinstance(node,ast.ImportFrom) and node.module else [])
            pending.extend(name + ".py" for name in imports if (directory / (name + ".py")).is_file())
    return found


def check_job(receipt, job, script):
    data = receipt.get("Jobs",{}).get(job,{})
    if (data.get("job_state") != "F" or data.get("Exit_status") != 0
            or shlex.split(data.get("Submit_arguments", "")) != [str(script)]):
        raise ValueError("completed PBS job/script required")


def require_fresh(root):
    for name in ("submission-intent.json","submission.json","execution-intent.json","inventory","summary.json"):
        path = Path(root) / name
        if path.exists() or path.is_symlink(): raise ValueError("existing execution/submission; preserve and do not retry")


def inputs(final_root, completion_receipt):
    """Only saved metadata; no analysis group or raw NPZ reads during preparation."""
    final_root = Path(final_root).absolute()
    plan = final.read_plan(final_root)
    paths = [final_root / name for name in ("manifest.json","summary.json","submission.json","submission-intent.json",
                "execution-intent.json","reaggregate.sh","phases/audited.json","phases/audited.measurement.json")]
    paths += [Path(completion_receipt).absolute(),Path(plan["evidence"]["analysis_verification"])]
    paths += [Path(plan["production_root"]) / name for name in ("manifest.json","analysis_manifest.json")]
    guards = {str(path): [str(path.resolve()),c.file_hash(path)] for path in paths}
    summary, ledger, intent = (read_json(final_root / name) for name in ("summary.json","submission.json","submission-intent.json"))
    job = ledger["job_id"]
    check_job(read_json(completion_receipt),job,final_root / "reaggregate.sh")
    if ({k:v for k,v in ledger.items() if k != "job_id"} != intent or ledger["manifest"] != c.digest(plan)
            or ledger["script_sha256"] != c.file_hash(final_root / "reaggregate.sh")
            or ledger["command"] != ["qsub",str(final_root / "reaggregate.sh")]
            or summary.get("complete") is not True or summary.get("terminal_binding_valid") is not True
            or summary.get("manifest") != c.digest(plan) or summary.get("pbs_job_id") != job
            or summary.get("case") != plan["case"] or summary.get("groups") != 768 or summary.get("replicates") != 192
            or summary.get("execution_intent_sha256") != c.file_hash(final_root / "execution-intent.json")):
        raise ValueError("successful final reaggregation binding required")
    expected_binding=dict(job_id=job,submission_sha256=c.file_hash(final_root/"submission.json"),
                          intent_sha256=c.file_hash(final_root/"submission-intent.json"),script_sha256=ledger["script_sha256"])
    execution=read_json(final_root/"execution-intent.json")
    if (summary.get("submission_binding") != expected_binding or execution.get("submission_binding") != expected_binding
            or execution.get("pbs_job_id") != job or execution.get("manifest") != c.digest(plan)):
        raise ValueError("final execution intent differs")
    record = next(row for row in summary["records"] if row["phase"] == "audited")
    measurement = read_json(final_root / "phases/audited.measurement.json")
    output = final_root / "phases/audited.json"
    if (record["status"] != "ok" or record["returncode"] != 0 or record["measurement"] != measurement
            or record["measurement_sha256"] != c.file_hash(final_root / "phases/audited.measurement.json")
            or record["output_sha256"] != measurement["output_sha256"] or record["output_sha256"] != c.file_hash(output)
            or measurement["status"] != "ok" or measurement["manifest"] != c.digest(plan) or measurement["pbs_job_id"] != job):
        raise ValueError("audited phase output/measurement binding differs")
    report = read_json(output); final.validate_report(plan,"audited",report)
    guard_files(guards)
    return dict(final_root=str(final_root),production_root=plan["production_root"],case=plan["case"],
                audited_results=str(output),analysis_verification=plan["evidence"]["analysis_verification"],
                completion_receipt=str(Path(completion_receipt).absolute()),job_id=job,input_files=guards,
                source_sha256={name:c.file_hash(path) for name,path in source_files().items()},
                python_sha256=c.file_hash(Path(sys.executable).resolve()),runtime=plan["snapshot"]["runtime"])


def guard_files(files):
    for path,(target,digest) in files.items():
        if str(Path(path).resolve()) != target or c.file_hash(path) != digest:
            raise ValueError("input path/hash changed")


def capacity_evidence(root, receipt, snapshot):
    root = Path(root).absolute(); plan = read_plan(root)
    summary = read_json(root / "summary.json"); ledger = read_json(root / "submission.json")
    check_job(read_json(receipt),ledger["job_id"],root / "inventory.sh")
    if (plan["mode"] != "capacity" or plan["snapshot"] != snapshot or summary.get("complete") is not True
            or summary.get("manifest") != c.digest(plan) or summary.get("pbs_job_id") != ledger["job_id"]
            or summary.get("groups_measured") != 1 or summary.get("planned_groups") != 768
            or summary.get("group") != [plan["case"],0,0,0]
            or summary.get("rows_sha256") != c.file_hash(root / "inventory/rows.jsonl")):
        raise ValueError("same-case completed capacity required")
    bound=binding(root,plan,job=ledger["job_id"])
    execution=read_json(root/"execution-intent.json")
    if (summary.get("submission_binding") != bound or summary.get("execution_intent_sha256") != c.file_hash(root/"execution-intent.json")
            or execution.get("submission_binding") != bound or execution.get("manifest") != c.digest(plan)
            or execution.get("pbs_job_id") != ledger["job_id"] or summary.get("terminal_binding_valid") is not True):
        raise ValueError("capacity execution binding differs")
    validate_capacity_measurement(summary,snapshot)
    return dict(root=str(root),completion_receipt=str(Path(receipt).absolute()),
                files={str(path):[str(path.resolve()),c.file_hash(path)] for path in
                       (root / "summary.json",root / "manifest.json",root / "submission.json",root / "submission-intent.json",
                        root / "inventory.sh",root / "execution-intent.json",root / "inventory/rows.jsonl",Path(receipt).absolute())},
                measurement={key:summary[key] for key in ("wall_seconds","cpu_seconds","peak_rss_mb")})


def validate_capacity_measurement(summary,snapshot):
    production=Path(snapshot["production_root"]).absolute(); case=snapshot["case"]
    plan=read_json(production/"manifest.json")
    expected=inventory.expected_diagnostics(plan,case)
    rows=len(expected)+len({key[:4] for key in expected if "_bennett_edge_" not in key[4]})
    paths={str(production/"analysis"/(f"{case}-0-0-0"+suffix)) for suffix in (".json",".done.json")}
    if (summary.get("rows") != rows or set(summary.get("input_files",{})) != paths
            or any(not Path(path).resolve().is_relative_to(production.resolve()) for path in paths)):
        raise ValueError("capacity rows or consumed input census differs")
    guard_files(summary["input_files"])
    cpu=summary.get("cpu_seconds")
    if type(cpu) not in (int,float) or not math.isfinite(cpu) or cpu<0:
        raise ValueError("finite nonnegative CPU measurement required")
    resources(summary)


def prepare(root, final_root, completion_receipt, capacity_root=None, capacity_receipt=None):
    root = Path(root).absolute()
    if root.exists(): raise ValueError("new output root required")
    snapshot = inputs(final_root,completion_receipt)
    if any(root.resolve().is_relative_to(Path(snapshot[key]).resolve()) or Path(snapshot[key]).resolve().is_relative_to(root.resolve())
           for key in ("production_root","final_root")):
        raise ValueError("independent output required")
    capacity = None
    if (capacity_root is None) != (capacity_receipt is None): raise ValueError("both capacity paths required")
    if capacity_root is not None: capacity = capacity_evidence(capacity_root,capacity_receipt,snapshot)
    plan = dict(schema=1,purpose="mixing_inventory_execution",mode="full" if capacity else "capacity",case=snapshot["case"],
                planned_groups=768,replicates=192,snapshot=snapshot,capacity=capacity,
                resources=resources(capacity["measurement"] if capacity else None),required_threads=THREADS,warning=WARNING)
    root.mkdir(parents=True,exist_ok=False)
    with (root / "manifest.json").open("xb") as stream: stream.write(c.canonical(plan)+b"\n")
    return plan


def read_plan(root):
    root=Path(root).absolute(); plan=read_json(root / "manifest.json")
    snapshot=plan["snapshot"]
    if (plan.get("schema") != 1 or plan.get("purpose") != "mixing_inventory_execution" or plan.get("mode") not in ("capacity","full")
            or plan["case"] != snapshot["case"] or plan["planned_groups"] != 768 or plan["replicates"] != 192 or plan["required_threads"] != THREADS
            or inputs(snapshot["final_root"],snapshot["completion_receipt"]) != snapshot):
        raise ValueError("fixed execution snapshot changed")
    cap = plan["capacity"]
    if (plan["mode"] == "full") != (cap is not None): raise ValueError("capacity mode mismatch")
    if cap:
        guard_files(cap["files"])
        if capacity_evidence(cap["root"],cap["completion_receipt"],snapshot) != cap: raise ValueError("capacity changed")
    if plan["resources"] != resources(cap["measurement"] if cap else None): raise ValueError("resources changed")
    return plan


def binding(root,plan,job=None):
    import submit_tile_mixing_execution as submitter
    root=Path(root); ledger=read_json(root / "submission.json"); intent=read_json(root / "submission-intent.json")
    if ({k:v for k,v in ledger.items() if k != "job_id"} != intent or ledger["job_id"] != (job or os.environ.get("PBS_JOBID"))
            or ledger["manifest"] != c.digest(plan) or ledger["resource"] != plan["resources"]
            or ledger["script_sha256"] != c.file_hash(root / "inventory.sh")
            or ledger["command"] != ["qsub",str(root/"inventory.sh")]
            or ledger["submit_source_sha256"] != c.file_hash(submitter.__file__)
            or ledger["upstream_completion_sha256"] != c.file_hash(root/"upstream-completion-at-submit.json")
            or ledger["bundle_binding"] != submitter.bundle_binding(Path(__file__).resolve().parents[1],plan)):
        raise ValueError("PBS/submission/source binding differs")
    return {name:c.file_hash(root / name) for name in ("submission.json","submission-intent.json","inventory.sh")}


def capacity_group(root,plan,case,verification,expected,output):
    group=[case,0,0,0]
    if len(expected) != 768 or {tuple(v["group"]) for v in expected.values()} != {
            (case,k,i,rep) for k in range(2) for i in range(2) for rep in range(192)}:
        raise ValueError("full planned group census required")
    stem,identity=next((stem,identity) for stem,identity in expected.items() if identity["group"] == group)
    evidence=inventory.Evidence(root)
    record,record_sha=evidence.json(Path(root)/(stem+".json"),production=True)
    marker,marker_sha=evidence.json(Path(root)/(stem+".done.json"),production=True)
    if marker["identity"] != identity or set(marker["sha256"]) != {".json",".npz"} or marker["sha256"][".json"] != record_sha:
        raise ValueError("capacity artifact identity/hash differs")
    audited._match_payload(verification,stem,marker_sha,marker["sha256"])
    rows=inventory.inventory_group(plan,case,group,record); cohorts={}
    with (Path(output)/"rows.jsonl").open("xb") as stream:
        for row in rows:
            stream.write(c.canonical(row)+b"\n"); inventory._add(cohorts,row)
    evidence.finish()
    return dict(groups_measured=1,planned_groups=768,group=group,rows=len(rows),
                rows_sha256=c.file_hash(Path(output)/"rows.jsonl"),input_files=evidence.files,
                scientific_cohort_summary=False)


def run(root):
    root=Path(root).absolute()
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(k) != v for k,v in THREADS.items()):
        raise ValueError("qsub and fixed single-thread environment required")
    for name in ("execution-intent.json","inventory","summary.json"):
        if (root/name).exists(): raise ValueError("existing execution")
    started,cpu=time.perf_counter(),time.process_time()
    plan=read_plan(root); bound=binding(root,plan)
    intent=dict(manifest=c.digest(plan),pbs_job_id=os.environ["PBS_JOBID"],hostname=socket.gethostname(),submission_binding=bound)
    with (root/"execution-intent.json").open("xb") as stream: stream.write(c.canonical(intent)+b"\n")
    result=dict(**intent,mode=plan["mode"],case=plan["case"],complete=False,warning=WARNING)
    try:
        state=plan["snapshot"]; production=Path(state["production_root"])
        output=root/"inventory"
        if plan["mode"] == "capacity":
            production_plan=read_json(production/"manifest.json"); context=read_json(production/"analysis_manifest.json")
            verification=read_json(state["analysis_verification"])
            expected=audited._verification(verification,"production-analysis",production_plan,plan["case"],c.file_hash(production/"manifest.json"),context)
            output.mkdir()
            result.update(capacity_group(production,production_plan,plan["case"],verification,expected,output))
        else:
            report=inventory.run(production,state["audited_results"],state["analysis_verification"],plan["case"],output)
            if report["groups"] != 768 or report["replicates"] != 192: raise ValueError("full cohort denominator differs")
            result.update(groups=768,replicates=192,rows=report["rows"],inventory_complete=report["inventory_complete"],
                          rows_sha256=report["rows_sha256"],inventory_summary_sha256=c.file_hash(output/"summary.json"))
        if read_plan(root) != plan or binding(root,plan) != bound: raise ValueError("terminal snapshot changed")
        result.update(complete=True,terminal_binding_valid=True)
    except Exception as error:
        result.update(error=repr(error),traceback=traceback.format_exc(),terminal_binding_valid=False)
    result.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_mb=c.peak_rss_mb(),
                  execution_intent_sha256=c.file_hash(root/"execution-intent.json"))
    with (root/"summary.json").open("xb") as stream: stream.write(c.canonical(result)+b"\n")
    if not result["complete"]: raise RuntimeError("inventory execution failed; preserve outputs")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("prepare","run")); parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--config",type=Path)
    args=parser.parse_args()
    result=prepare(args.root,**read_json(args.config)) if args.command=="prepare" else run(args.root)
    print(json.dumps({k:result[k] for k in ("case","mode","complete","resources") if k in result}))


if __name__=="__main__": main()
