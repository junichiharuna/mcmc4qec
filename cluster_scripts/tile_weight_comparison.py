"""Compare full-cohort target conditional weight against independent MC."""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import fmean,variance

import calibration as c
import tile_bar_study as b
import tile_bar_analysis as a


WARNING="Conditional-weight observable comparison, not BAR error-rate uncertainty or coverage. Reference SE uses an independent-chunk delta approximation. Replicate variability does not prove mixing. JSON metadata and marker identities are checked; unused ACF NPZ files and physical traces are not re-audited here."
FIELDS=("mean","chain_means","chain_iat","chain_ess","iat_mcse","cross_chain_se","rhat","undefined","flagged","high_rhat","low_ess","sector_transitions","unique_sectors")


def compare(rows,replicates,reference):
    if replicates<1 or len(rows)!=replicates or {row["replicate"] for row in rows}!=set(range(replicates)):
        raise ValueError("complete fixed replicate identities required")
    mean,ref_se=reference["mean"],reference["chunk_delta_standard_error"]
    if not all(math.isfinite(v) and v>=0 for v in (mean,ref_se)):
        raise ValueError("finite reference mean and delta SE required")
    values=[]
    for row in rows:
        if row["missing"]!=(row["mean"] is None):
            raise ValueError("missing mean accounting differs")
        for key in ("mean","iat_mcse","cross_chain_se"):
            value=row[key]
            if value is not None and (not math.isfinite(value) or value<0):
                raise ValueError("invalid mean or MCSE")
        if row["mean"] is not None:values.append(row["mean"])
    full=len(values)==replicates
    estimate=fmean(values) if values else None
    se=math.sqrt(variance(values)/replicates) if full and replicates>1 else None
    return dict(replicates=replicates,observed=len(values),missing=replicates-len(values),reference=reference,
        **{key:sum(bool(row[key]) for row in rows) for key in ("undefined","flagged","high_rhat","low_ess")},
        undefined_iat_mcse=sum(row["iat_mcse"] is None for row in rows),
        undefined_cross_chain_se=sum(row["cross_chain_se"] is None for row in rows),
        mean=estimate if full else None,available_only_mean=estimate,
        mean_difference_from_reference=estimate-mean if full else None,
        rmse_at_reference_point=math.sqrt(fmean((value-mean)**2 for value in values)) if full else None,
        replicate_mean_standard_error=se,difference_standard_error=math.hypot(se,ref_se) if se is not None else None,
        rows=sorted(rows,key=lambda row:row["replicate"]))


def read_metadata(path,identity):
    path=Path(path)
    marker=path.with_suffix(".done.json")
    if not marker.exists():raise ValueError("missing completed analysis metadata")
    marker_bytes=marker.read_bytes()
    stored=json.loads(marker_bytes)
    if c.canonical(stored["identity"])!=c.canonical(identity):
        raise ValueError("analysis identity differs")
    payload=path.with_suffix(".json").read_bytes()
    sha=hashlib.sha256(payload).hexdigest()
    if stored["sha256"].get(".json")!=sha or marker.read_bytes()!=marker_bytes:
        raise ValueError("analysis metadata checksum or marker changed")
    return json.loads(payload),dict(marker_sha256=hashlib.sha256(marker_bytes).hexdigest(),json_sha256=sha)


def group_rows(plan,spec,record):
    group=record["group"]
    target=len(spec["rungs"])-1
    if spec["rungs"][target]!=spec["target"] or record["status"]!="ok" or record["diagnostic_count"]!=len(record["diagnostics"]):
        raise ValueError("invalid target or analysis record")
    expected=set(itertools.product(sorted(set((4,spec["chains"]))),plan["burns"],spec["windows"]))
    found={}
    for diag in record["diagnostics"]:
        if diag["observable"]!="weight" or diag["rung"]!=target:continue
        key=tuple(diag[k] for k in ("chains","burn","samples"))
        if key not in expected or key in found or diag["p"]!=spec["target"]:
            raise ValueError("unexpected or duplicate target weight diagnostic")
        if not math.isfinite(diag["mean"]) or not 0<=diag["mean"]<=2*spec["size"]**2:
            raise ValueError("invalid physical weight mean")
        for name in ("chain_means","chain_iat","chain_ess","sector_transitions","unique_sectors"):
            if len(diag[name])!=key[0]:raise ValueError("wrong chain count in weight diagnostics")
        if not math.isclose(fmean(diag["chain_means"]),diag["mean"],rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError("chain means disagree with pooled mean")
        found[key]=diag
    failed=[]
    for task in record["failed_tasks"]:
        if len(task)!=6 or task[:4]!=group or not 0<=task[4]<len(spec["rungs"]) or not 0<=task[5]<spec["chains"]:
            raise ValueError("unexpected failed sampling task")
        failed.append(task)
    rows=[]
    for chains,burn,samples in sorted(expected):
        key=chains,burn,samples
        missing=any(task[4]==target and task[5]<chains for task in failed)
        if (key not in found)!=missing:
            raise ValueError("weight diagnostic missing without target sampling failure, or present despite failure")
        row=dict(chains=chains,burn=burn,samples=samples,replicate=group[3],missing=missing)
        if missing:
            row.update({key:None for key in FIELDS})
            row.update(undefined=True,flagged=True,high_rhat=False,low_ess=False)
        else:
            row.update({name:found[key][name] for name in FIELDS})
        rows.append(row)
    return rows


def run(root,case,reference_audit,output):
    root,reference_audit,output=Path(root),Path(reference_audit),Path(output)
    if output.exists():raise ValueError("report exists; preserve prior evidence")
    paths=dict(sampling=root/"manifest.json",analysis=root/"analysis_manifest.json",reference=root/"reference_summary.json",
               reference_audit=reference_audit,phase=root/f"analysis_summary-{case}.json")
    hashes={key:c.file_hash(path) for key,path in paths.items()}
    values={key:json.loads(path.read_text()) for key,path in paths.items()}
    plan,context,reference,audit,phase=(values[k] for k in ("sampling","analysis","reference","reference_audit","phase"))
    if c.canonical(plan)!=c.canonical(b.make_plan()) or case not in range(4):
        raise ValueError("fixed production manifest required")
    if (context["sampling_manifest"]!=c.digest(plan) or context["analysis_source_sha256"]!=c.file_hash(a.__file__)
        or context["reference_summary_sha256"]!=hashes["reference"] or phase["analysis"]!=c.digest(context)
        or phase["groups"]!=len(plan["kernels"])*len(plan["initializations"])*plan["replicates"]):
        raise ValueError("complete matching analysis and reference required")
    if audit["summary_sha256"]!=hashes["reference"] or not all(audit.get(k) for k in ("all_problem_metadata_verified","all_seeds_verified","summary_reproduced")):
        raise ValueError("matching audited reference required")
    refs=[r for r in reference["records"] if r["case"]==case]
    weights=[r for r in audit["conditional_weight"] if r["case"]==case]
    spec=plan["cases"][case]
    context_refs=[r for r in context["references"] if r["case"]==case]
    if (len(refs)!=1 or len(weights)!=1 or c.canonical(refs)!=c.canonical(context_refs)
        or refs[0]["target_p"]!=spec["target"] or refs[0]["size"]!=spec["size"] or refs[0]["noise"]!=spec["noise"]
        or refs[0]["conditional_weight"]!=weights[0]["mean"]):
        raise ValueError("conditional reference identity or mean differs")
    cohorts=defaultdict(list);inputs=[]
    for ki,kernel in enumerate(plan["kernels"]):
        for ii,initial in enumerate(plan["initializations"]):
            for rep in range(plan["replicates"]):
                group=[case,ki,ii,rep]
                record,evidence=read_metadata(root/"analysis"/c.task_id(group),dict(analysis=c.digest(context),group=group))
                if record["group"]!=group:raise ValueError("analysis group differs")
                inputs.append(dict(group=group,**evidence))
                for row in group_rows(plan,spec,record):
                    key=kernel,initial,row["chains"],row["burn"],row["samples"]
                    cohorts[key].append(row)
    reports=[dict(case=case,kernel=key[0],init=key[1],chains=key[2],burn=key[3],samples=key[4],
                  **compare(rows,plan["replicates"],weights[0])) for key,rows in sorted(cohorts.items())]
    if hashes!={key:c.file_hash(path) for key,path in paths.items()}:raise ValueError("inputs changed during comparison")
    result=dict(case=case,conditions=len(reports),records=reports,input_sha256=hashes,analysis_metadata=inputs,
                source_sha256=c.file_hash(__file__),acf_arrays_rechecked=False,physical_traces_reaudited=False,warning=WARNING)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("xb") as stream:stream.write(c.canonical(result)+b"\n")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4),required=True)
    parser.add_argument("--reference-audit",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.root,args.case,args.reference_audit,args.output)
    print(json.dumps(dict(case=result["case"],conditions=result["conditions"],warning=WARNING)))


if __name__=="__main__":main()
