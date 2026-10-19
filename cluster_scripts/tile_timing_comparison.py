"""Validate independent timing artifacts before comparing complete-cohort costs."""
import argparse
import json
import math
import os
from pathlib import Path

import calibration as c
import tile_mc_time_benchmark as mc
import tile_bar_time_benchmark as bar
import tile_timing_metrics as metrics


WARNING=(metrics.WARNING+" This adapter verifies payload integrity and recorded seed/model metadata. "
         "It does not re-decode stored states, rerun native probes, or reanalyse the selection cohort.")


def _metadata(meta,p,seed,model_hash):
    if (meta["sampling_p"]!=p or meta["rng"]["entropy"]!=seed
        or c.digest({k:meta[k] for k in ("model","noise","decoder","failure")})!=model_hash):
        raise ValueError("actual timing metadata, seed or model differs")


def load_cohort(root,method,case):
    root=Path(root)
    if method not in ("mc","bar") or type(case) is not int or case not in range(4):
        raise ValueError("fixed method and case required")
    guards={}
    def read(path):
        path=Path(path)
        guards[str(path)]=c.file_hash(path)
        return json.loads(path.read_text())
    plan=read(root/"manifest.json")
    source=read(root/("budget.json" if method=="mc" else "settings.json"))
    expected=mc.make_plan(source,capacity=False) if method=="mc" else bar.make_plan(source,capacity=False,case=case)
    if c.canonical(plan)!=c.canonical(expected):
        raise ValueError("fixed benchmark source, runtime, settings or manifest differs")
    manifest_hash=c.digest(plan)
    native_inputs={key:read(root/(key+".json")) for key in plan["native_input_digests"]}
    if {key:c.digest(value) for key,value in native_inputs.items()}!=plan["native_input_digests"]:
        raise ValueError("native input changed")
    driver=mc if method=="mc" else bar
    tasks=list(driver.tasks(plan))
    if not tasks:
        if (root/"summary.json").exists() or (root/"tasks").exists():
            raise ValueError("unmet selection must not contain timing tasks")
        return dict(plan=plan,records=[],models={},guards=guards,artifact_markers={},phase_wall_seconds=None)
    summary=read(root/"summary.json")
    preflight=read(root/"native_preflight.json")
    intent=read(root/"execution_intent.json")
    if (summary["manifest"]!=manifest_hash or summary["tasks"]!=len(tasks)
        or [tuple(row["task"]) for row in summary["records"]]!=tasks):
        raise ValueError("missing, duplicate or unexpected timing task")
    if (summary["native_preflight_sha256"]!=guards[str(root/"native_preflight.json")]
        or preflight["manifest"]!=manifest_hash or not preflight["pbs_job_id"] or not preflight["hostname"]
        or any(intent[key]!=preflight[key] for key in ("manifest","pbs_job_id"))
        or ("hostname" in intent and intent["hostname"]!=preflight["hostname"])):
        raise ValueError("compute preflight and execution binding differs")
    mc.trace_audit.validate_platform(native_inputs["platform_profile"],preflight["profile"])
    phase=summary["phase_wall_seconds"]
    if isinstance(phase,bool) or not math.isfinite(phase) or phase<=0:
        raise ValueError("positive measured phase walltime required")
    if summary["failed"]!=sum(row["status"]=="failed" for row in summary["records"]):
        raise ValueError("failed task count differs")
    if method=="bar" and (summary["reused_tasks"] or any(row["reused"] for row in summary["records"])
        or summary["unavailable"]!=sum(not row["available"] for row in summary["records"])):
        raise ValueError("reused tasks or unavailable count differs")
    models={}
    markers={}
    for task,reduced in zip(tasks,summary["records"]):
        path=root/"tasks"/c.task_id(task)
        marker=read(path.with_suffix(".done.json"))
        if set(marker["sha256"])!={".json",".npz"}:
            raise ValueError("complete JSON and NPZ hashes required")
        saved=c.load_artifact(path,dict(manifest=manifest_hash,task=list(task)))
        if saved is None:
            raise ValueError("missing timing artifact")
        record=saved[1]
        omitted=("metadata",) if method=="mc" else ("chains","anchor")
        compact={k:v for k,v in record.items() if k not in omitted}
        if method=="bar":compact["reused"]=False
        if c.canonical(compact)!=c.canonical(reduced):
            raise ValueError("raw timing record and summary differ")
        condition=plan["conditions"][task[0]]
        if (record["task"]!=list(task) or record["replicate"]!=task[1]
            or any(record[key]!=condition[key] for key in ("case","epsilon"))
            or record["status"] not in ({"ok","failed"} if method=="mc" else {"ok","failed","unavailable"})):
            raise ValueError("task identity or status differs")
        model_hash=record.get("problem_hash")
        if record["status"]!="failed" and not model_hash:
            raise ValueError("successful timing record lacks model hash")
        if model_hash:
            key=str(record["case"])
            if key in models and models[key]!=model_hash:
                raise ValueError("multiple model hashes for one case")
            models[key]=model_hash
        if method=="mc":
            if record["seed"]!=mc.task_seed(plan,task) or record["target_p"]!=condition["target_p"]:
                raise ValueError("MC task seed or target differs")
            if record["status"]=="ok":
                if (record["trials"]!=condition["planned_trials"] or type(record["failures"]) is not int
                    or not 0<=record["failures"]<=record["trials"] or record["estimate"]!=record["failures"]/record["trials"]
                    or record["metadata_sha256"]!=c.digest(record["metadata"])):
                    raise ValueError("actual MC count or metadata differs")
                _metadata(record["metadata"],condition["target_p"],record["seed"],model_hash)
        else:
            if (record["condition"]!=condition["condition"] or record["anchor_seed"]!=bar.task_seed(plan,task,0,0,0)
                or record["bootstrap_seed"]!=bar.task_seed(plan,task,0,0,3)):
                raise ValueError("BAR condition or independent seed differs")
            anchor=record.get("anchor")
            if anchor is not None:
                if anchor["seed"]!=record["anchor_seed"] or anchor["trials"]!=plan["anchor_trials"]:
                    raise ValueError("BAR anchor metadata differs")
                _metadata(anchor["metadata"],condition["rungs"][0],record["anchor_seed"],model_hash)
            elif record["status"]!="failed":
                raise ValueError("successful BAR task lacks anchor")
            expected_chains={(r,k) for r in range(len(condition["rungs"])) for k in range(condition["condition"]["chains"])}
            seen=set()
            for chain in record["chains"]:
                key=(chain["rung"],chain["chain"])
                if key not in expected_chains or key in seen or chain["status"] not in ("ok","failed"):
                    raise ValueError("unexpected or duplicate chain")
                seen.add(key)
                if (chain["init_seed"]!=bar.task_seed(plan,task,*key,1)
                    or chain["sample_seed"]!=bar.task_seed(plan,task,*key,2)):
                    raise ValueError("BAR chain seed differs")
                if chain["status"]=="ok":
                    _metadata(chain["metadata"],condition["rungs"][key[0]],chain["sample_seed"],model_hash)
                elif record["status"]!="failed":
                    raise ValueError("failed chain in successful task")
            if record["status"]!="failed" and seen!=expected_chains:
                raise ValueError("successful BAR task omitted chains")
        markers[c.task_id(task)]=marker
    for path,sha in guards.items():
        if c.file_hash(path)!=sha:raise ValueError("input or completion marker changed during loading")
    return dict(plan=plan,records=summary["records"],models=models,guards=guards,
                artifact_markers=markers,phase_wall_seconds=phase)


def run(mc_root,bar_root,reference_path,audit_path,case,output):
    output=Path(output)
    if output.exists():raise ValueError("comparison exists; preserve prior evidence")
    reference_path,audit_path=Path(reference_path),Path(audit_path)
    hashes={str(path):c.file_hash(path) for path in (reference_path,audit_path)}
    reference=json.loads(reference_path.read_text())
    audit=json.loads(audit_path.read_text())
    if audit["summary_sha256"]!=hashes[str(reference_path)] or not all(audit.get(k) for k in (
        "all_seeds_verified","all_problem_metadata_verified","summary_reproduced")):
        raise ValueError("reference audit binding missing")
    refs=[r for r in reference["records"] if r["case"]==case]
    if len(refs)!=1:raise ValueError("one matching independent reference required")
    ref=refs[0]
    loaded={"mc":load_cohort(mc_root,"mc",case),"bar":load_cohort(bar_root,"bar",case)}
    for cohort in loaded.values():
        if any(audit["model_hashes"].get(key)!=value for key,value in cohort["models"].items()):
            raise ValueError("timing model differs from independently audited reference")
        hashes.update(cohort["guards"])
    results=[]
    for epsilon in (.2,.1):
        conditions={name:next(r for r in value["plan"]["conditions"] if r["case"]==case and r["epsilon"]==epsilon)
                    for name,value in loaded.items()}
        cond=conditions["mc"]
        if (cond["target_p"]!=ref["target_p"] or cond["reference_point"]!=ref["estimate"]
            or cond["reference_interval_999"]!=ref["interval_999"]):
            raise ValueError("MC budget and independent reference differ")
        rows={name:[r for r in value["records"] if r["case"]==case and r["epsilon"]==epsilon] for name,value in loaded.items()}
        if conditions["bar"]["status"]=="unmet":
            results.append(dict(case=case,epsilon=epsilon,status="selection_unmet",reason=conditions["bar"]["reason"],
                mc=metrics.assess("mc",rows["mc"],192,ref,epsilon),comparison=None))
        else:
            if conditions["bar"]["target_p"]!=ref["target_p"]:raise ValueError("BAR target differs from reference")
            results.append(dict(case=case,epsilon=epsilon,status="compared",condition=conditions["bar"]["condition"],
                comparison=metrics.compare(rows["mc"],rows["bar"],192,ref,epsilon)))
    for path,sha in hashes.items():
        if c.file_hash(path)!=sha:raise ValueError("input changed before comparison output")
    result=dict(schema=1,purpose="independent_timing_comparison",case=case,records=results,
        input_sha256=hashes,artifact_markers={name:value["artifact_markers"] for name,value in loaded.items()},
        job_phases={name:dict(wall_seconds=value["phase_wall_seconds"],scope="all_eight_conditions" if name=="mc" else "selected_conditions_for_case")
                    for name,value in loaded.items()},source_sha256=c.file_hash(__file__),metrics_source_sha256=c.file_hash(metrics.__file__),
        selection_reanalysed=False,physical_states_redecoded=False,native_probe_reexecuted=False,warning=WARNING)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("xb") as stream:stream.write(c.canonical(result)+b"\n")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ("mc-root","bar-root","reference-path","audit-path","output"):
        parser.add_argument("--"+arg,type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4),required=True)
    args=parser.parse_args()
    if not os.environ.get("PBS_JOBID"):
        raise ValueError("submit full artifact comparison through qsub; it reads every timing payload")
    result=run(**vars(args))
    print(json.dumps(dict(output=str(args.output),case=result["case"],warning=WARNING)))


if __name__=="__main__":main()
