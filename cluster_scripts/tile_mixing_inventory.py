"""Inventory saved full-cohort diagnostics without recomputing scientific values."""
import argparse
from collections import Counter
import itertools
import json
import math
import os
from pathlib import Path

import calibration as c
import tile_audited_results as audited


SCALARS=("mean","iat","ess","iat_mcse","cross_chain_se","rhat")
VECTORS=("chain_means","chain_iat","chain_ess")
FLAGS=("undefined","high_rhat","low_ess","flagged")
KEY=("kind","case","kernel","init","chains","burn","samples","rung","observable")
WARNING=("Saved diagnostic JSON inventory, not numerical reanalysis or a convergence/coverage guarantee. "
         "The saved successful full audit is reused; only current JSON and markers are rehashed here. "
         "NPZ, physical traces and native probes are not rechecked. Historical consumed-input hashes "
         "were not recorded by the original analysis. All planned replicates, including missing and "
         "undefined diagnostics, remain in the denominator. Production CPU and I/O costs are unmeasured.")


def require(ok,message):
    if not ok: raise ValueError(message)


def expected_diagnostics(plan,case):
    """Return the exact stored diagnostic census, without constructing a decoder."""
    spec=plan["cases"][case]
    require(spec["size"] in (6,12) and spec["noise"] in ("bit","depolarizing"),"fixed tile design required")
    bits=8 if spec["noise"]=="bit" else 16
    require(len(set(spec["rungs"]))==len(spec["rungs"]),"duplicate rungs")
    result={}
    def add(chains,burn,samples,rung,name):
        key=(chains,burn,samples,rung,name)
        require(key not in result,"duplicate diagnostic design")
        result[key]=dict(chains=chains,burn=burn,samples=samples,rung=rung,p=spec["rungs"][rung],observable=name)
    for chains,burn,samples in itertools.product(sorted(set((4,spec["chains"]))),plan["burns"],spec["windows"]):
        require(chains<=spec["chains"] and burn>=0 and samples>0 and burn+samples<=spec["steps"],"invalid diagnostic window")
        for rung in range(len(spec["rungs"])):
            for name in ("weight","syndrome_weight",*(f"logical_bit_{bit}" for bit in range(bits))):
                add(chains,burn,samples,rung,name)
        for label,ladder in (("coarse",spec["coarse"]),("fine",spec["rungs"])):
            require(len(ladder)>=2 and len(set(ladder))==len(ladder) and all(p in spec["rungs"] for p in ladder),"invalid ladder")
            for edge,(left,right) in enumerate(zip(ladder,ladder[1:])):
                for p in (left,right): add(chains,burn,samples,spec["rungs"].index(p),f"{label}_bennett_edge_{edge}")
    return result


def _numeric_values(saved,chains,*,sector=False):
    values={}; missing=[]; nonfinite=[]; nulls=[]
    fields=("sector_transitions","unique_sectors") if sector else SCALARS+VECTORS
    vectors=fields if sector else VECTORS
    def clean(value,path):
        if value is None:
            nulls.append(path); return None
        require(type(value) in (int,float),"nonnumeric diagnostic value")
        if not math.isfinite(value):
            nonfinite.append(path); return None
        return value
    for field in fields:
        if field not in saved: missing.append(field)
        value=saved.get(field)
        if field in vectors:
            if field not in saved: value=[None]*chains
            require(isinstance(value,list) and len(value)==chains,"diagnostic chain length differs")
            values[field]=[clean(v,f"{field}[{i}]") for i,v in enumerate(value)]
        else: values[field]=clean(value,field)
    return values,missing,nonfinite,nulls


def inventory_group(plan,case,group,record):
    """Normalize saved values and retain absent expected diagnostics as explicit rows."""
    group=tuple(group); spec=plan["cases"][case]
    require(len(group)==4 and group[0]==case and group[1] in range(2) and group[2] in range(2)
            and group[3] in range(plan["replicates"]),"unexpected group identity")
    require(record["status"]=="ok" and record["group"]==list(group),"analysis group identity/status differs")
    diagnostics=record["diagnostics"]
    require(record["diagnostic_count"]==len(diagnostics),"diagnostic count differs")
    expected=expected_diagnostics(plan,case); found={}
    for row in diagnostics:
        key=tuple(row[name] for name in ("chains","burn","samples","rung","observable"))
        require(key in expected and key not in found and row["p"]==expected[key]["p"],"duplicate or unexpected diagnostic identity")
        found[key]=row
    failed=set()
    for task in record["failed_tasks"]:
        task=tuple(task)
        require(len(task)==6 and task[:4]==group and task[4] in range(len(spec["rungs"]))
                and task[5] in range(spec["chains"]) and task not in failed,"invalid failed task census")
        failed.add(task)
    def is_failed(item):
        name=item["observable"]
        if "_bennett_edge_" in name:
            label=name.split("_bennett_edge_")[0]
            rungs={spec["rungs"].index(p) for p in (spec["coarse"] if label=="coarse" else spec["rungs"])}
        else: rungs={item["rung"]}
        return any(task[4] in rungs and task[5]<item["chains"] for task in failed)
    def normalized(item,saved,kind):
        failed_here=is_failed(item)
        require(not (failed_here and saved is not None),"diagnostic present despite recorded sampling failure")
        status="stored" if saved is not None else ("missing_recorded_sampling_failure" if failed_here else "missing_unexpected")
        values,missing,nonfinite,nulls=_numeric_values(saved or {},item["chains"],sector=kind=="sector")
        flags=None
        if saved is not None and kind=="diagnostic":
            require(all(type(saved.get(key)) is bool for key in FLAGS),"invalid stored flags")
            flags={key:saved[key] for key in FLAGS}
        return dict(kind=kind,case=case,kernel=list(plan["kernels"])[group[1]],init=plan["initializations"][group[2]],
            replicate=group[3],**item,status=status,values=values,stored_flags=flags,
            missing_fields=missing,nonfinite_paths=nonfinite,null_paths=nulls,
            undefined=bool(status!="stored" or missing or nonfinite or nulls or (flags and flags["undefined"])))
    result=[normalized(item,found.get(key),"diagnostic") for key,item in expected.items()]
    # Sector arrays repeat in every physical diagnostic; count each window/rung once.
    sector_groups={key[:4] for key in expected if "_bennett_edge_" not in key[4]}
    for window in sorted(sector_groups):
        copies=[row for key,row in found.items() if key[:4]==window and "_bennett_edge_" not in key[4]]
        present=[row for row in copies if "sector_transitions" in row or "unique_sectors" in row]
        if present:
            signature=_numeric_values(present[0],window[0],sector=True)
            require(all(_numeric_values(row,window[0],sector=True)==signature for row in present),"repeated sector statistics differ")
        chains,burn,samples,rung=window
        item=dict(chains=chains,burn=burn,samples=samples,rung=rung,p=spec["rungs"][rung],observable="sector")
        result.append(normalized(item,present[0] if present else None,"sector"))
    return result


class Evidence:
    """Track both lexical path and resolved target; rehash every consumed JSON."""
    def __init__(self,root):
        self.root=Path(root).absolute(); self.target=self.root.resolve(); self.files={}

    def read(self,path,*,production=False):
        path=Path(path).absolute(); target=path.resolve()
        if production: require(target.is_relative_to(self.target),"production input escaped root")
        payload=path.read_bytes(); import hashlib
        digest=hashlib.sha256(payload).hexdigest()
        previous=self.files.setdefault(str(path),(str(target),digest))
        require(previous==(str(target),digest),"input changed while reading")
        return payload,digest

    def json(self,path,*,production=False):
        data,sha=self.read(path,production=production)
        return json.loads(data),sha

    def finish(self):
        require(self.root.resolve()==self.target,"production root changed")
        for path,(target,sha) in self.files.items():
            require(str(Path(path).resolve())==target and c.file_hash(path)==sha,"input or source changed before completion")


def _add(cohorts,row):
    key=tuple(row[name] for name in KEY)
    acc=cohorts.setdefault(key,dict(ids=set(),statuses=Counter(),undefined=0,nonfinite=0,missing_fields=0,flags=Counter(),metrics={}))
    require(row["replicate"] not in acc["ids"],"duplicate replicate in diagnostic cohort")
    acc["ids"].add(row["replicate"]); acc["statuses"][row["status"]]+=1
    acc["undefined"]+=int(row["undefined"])
    acc["nonfinite"]+=bool(row["nonfinite_paths"])
    acc["missing_fields"]+=bool(row["missing_fields"] and row["status"]=="stored")
    for name,value in (row["stored_flags"] or {}).items(): acc["flags"][name]+=int(value)
    for name,value in row["values"].items():
        state=acc["metrics"].setdefault(name,dict(expected_values=0,finite_values=0,null_values=0,nonfinite_values=0,sum=0.,min=None,max=None))
        values=value if isinstance(value,list) else [value]
        for i,number in enumerate(values):
            path=f"{name}[{i}]" if isinstance(value,list) else name
            state["expected_values"]+=1
            if number is None:
                state["nonfinite_values" if path in row["nonfinite_paths"] else "null_values"]+=1
                continue
            state["finite_values"]+=1
            if state["sum"] is not None:
                total=state["sum"]+number
                state["sum"]=total if math.isfinite(total) else None
            state["min"]=number if state["min"] is None else min(state["min"],number)
            state["max"]=number if state["max"] is None else max(state["max"],number)


def _summaries(cohorts,replicates):
    reports=[]
    for key,acc in sorted(cohorts.items()):
        require(acc["ids"]==set(range(replicates)),"incomplete diagnostic seed cohort")
        for state in acc["metrics"].values():
            mean=state["sum"]/state["finite_values"] if state["sum"] is not None and state["finite_values"] else None
            state.update(available_only_mean=mean,mean=mean if state["finite_values"]==state["expected_values"] else None)
        reports.append(dict(zip(KEY,key),replicates=replicates,replicate_ids=sorted(acc["ids"]),
            status_counts=dict(acc["statuses"]),undefined=acc["undefined"],nonfinite=acc["nonfinite"],
            stored_missing_fields=acc["missing_fields"],stored_flag_counts=dict(acc["flags"]),metrics=acc["metrics"]))
    return reports


def run(root,audited_results,analysis_verification,case,output):
    root=Path(root).absolute(); output=Path(output).absolute()
    require(not output.exists(),"preserve existing output")
    require(not output.resolve().is_relative_to(root.resolve()) and not root.resolve().is_relative_to(output.resolve()),"separate output root required")
    evidence=Evidence(root)
    source={name:evidence.read(Path(module))[1] for name,module in
        (("inventory",__file__),("audited_results",audited.__file__),("calibration",c.__file__),("archive",audited.archive.__file__))}
    report,report_sha=evidence.json(audited_results)
    require(report.get("purpose")=="audited_calibration_results" and report.get("schema")==1 and
        report.get("case")==case and type(case) is int and case in range(4) and report.get("replicates")==192 and report.get("groups")==768 and
        report.get("current_archived_inputs_match_audited_inputs") is True and report.get("terminal_payload_stat_checked") is True and
        report.get("source_sha256")==source["audited_results"] and report.get("source_hashes",{}).get("adapter")==source["audited_results"] and
        report.get("historical_consumed_input_hashes_recorded") is False,"successful fixed full-audit report required")
    bound={}
    for path,sha in report["input_sha256"].items():
        key=str(Path(path).absolute())
        require(key not in bound,"duplicate audit input path")
        bound[key]=sha
    def linked(path,production=False):
        value,sha=evidence.json(path,production=production)
        require(bound.get(str(Path(path).absolute()))==sha,"input not bound to saved full audit")
        return value,sha
    plan,manifest_sha=linked(root/"manifest.json",True)
    context,context_sha=linked(root/"analysis_manifest.json",True)
    verification,verification_sha=linked(analysis_verification)
    require(plan["purpose"]=="calibration" and plan["replicates"]==192 and len(plan["kernels"])==len(plan["initializations"])==2
        and report["sampling_manifest"]==context["sampling_manifest"]==c.digest(plan)
        and report["analysis_context"]==c.digest(context) and context["runtime"]==plan["runtime"],"fixed plan/context differs")
    require(verification["payload_sha256"].get("analysis_manifest.json")==context_sha,"archive analysis context differs")
    expected=audited._verification(verification,"production-analysis",plan,case,manifest_sha,context)
    expected_diagnostics(plan,case)
    output.mkdir(parents=True,exist_ok=False)
    cohorts={}; total=0; failed_tasks=0
    with (output/"rows.jsonl").open("xb") as stream:
        for stem,identity in expected.items():
            record,record_sha=evidence.json(root/(stem+".json"),production=True)
            marker,marker_sha=evidence.json(root/(stem+".done.json"),production=True)
            require(marker["identity"]==identity and set(marker["sha256"])=={".json",".npz"}
                and marker["sha256"][".json"]==record_sha,"analysis artifact identity/hash differs")
            audited._match_payload(verification,stem,marker_sha,marker["sha256"])
            group=tuple(identity["group"])
            rows=inventory_group(plan,case,group,record)
            failed_tasks+=len(record["failed_tasks"])
            for row in rows:
                stream.write(c.canonical(row)+b"\n"); _add(cohorts,row); total+=1
    require(failed_tasks==report["failed_sampling"],"failed sampling denominator differs from full audit")
    records=_summaries(cohorts,192)
    complete=not any(row["status_counts"].get("missing_unexpected",0) or row["nonfinite"] or row["stored_missing_fields"] for row in records)
    result=dict(schema=1,purpose="saved_mixing_inventory",case=case,replicates=192,groups=len(expected),rows=total,
        conditions=len(records),records=records,inventory_complete=complete,failed_sampling=failed_tasks,
        sampling_manifest=c.digest(plan),analysis_context=c.digest(context),audited_results_sha256=report_sha,
        analysis_verification_sha256=verification_sha,rows_sha256=c.file_hash(output/"rows.jsonl"),source_sha256=source,
        input_sha256={path:value[1] for path,value in evidence.files.items()},
        diagnostics_recomputed=False,acf_arrays_rechecked=False,bootstrap_recomputed=False,decoder_reexecuted=False,
        native_probe_reexecuted=False,current_all_payloads_reaudited=False,historical_consumed_input_hashes_recorded=False,
        production_cpu_io_measured=False,warning=WARNING)
    evidence.finish()
    with (output/"summary.json").open("xb") as stream: stream.write(c.canonical(result)+b"\n")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("root","audited-results","analysis-verification","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4),required=True)
    args=vars(parser.parse_args())
    require(os.environ.get("PBS_JOBID"),"submit full JSON inventory through qsub")
    result=run(**args)
    print(json.dumps({key:result[key] for key in ("case","groups","rows","inventory_complete")}))


if __name__=="__main__": main()
