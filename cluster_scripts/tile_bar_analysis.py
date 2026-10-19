"""Paired tile BAR windows with finite-reference coverage bounds."""
import argparse
import itertools
import json
import math
from pathlib import Path
import time

import numpy as np
import calibration as c
import tile_study as t
import tile_bar_study as b


def analysis_context(plan,references):
    return dict(schema=1,sampling_manifest=c.digest(plan),references=references,
                analysis_source_sha256=c.file_hash(__file__),runtime=b.runtime(),
                screens=dict(rhat_gt=1.01,min_chain_ess_lt=100),
                warning="Finite-reference coverage bounds; diagnostics are descriptive and no replicate is filtered.")


def coverage_flags(interval,reference):
    valid=interval is not None
    lo,hi=reference["interval_999"]
    return dict(covered_reference_point=bool(valid and interval[0]<=reference["estimate"]<=interval[1]),
                covered_reference_entire=bool(valid and interval[0]<=lo and hi<=interval[1]),
                covered_reference_possible=bool(valid and interval[0]<=hi and lo<=interval[1]))


def groups(plan,case_id=None):
    return ((case,kernel,init,rep) for case,kernel,init,rep in itertools.product(range(4),range(2),range(2),range(plan["replicates"]))
            if case_id is None or case==case_id)


def screen(diag):
    undefined=diag["rhat"] is None or any(x is None for x in diag["chain_ess"])
    high=diag["rhat"] is not None and diag["rhat"]>1.01
    low=any(x is not None and x<100 for x in diag["chain_ess"])
    return dict(undefined=undefined,high_rhat=high,low_ess=low,flagged=undefined or high or low)


def analyze_group(args):
    root,plan,context,group=args
    root=Path(root)
    identity=dict(analysis=c.digest(context),group=list(group))
    path=root/"analysis"/c.task_id(group)
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return {k:v for k,v in cached[1].items() if k!="diagnostics"}
    started=time.perf_counter()
    case,kernel,init,rep=group
    spec=plan["cases"][case]
    code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
    reference=next(r for r in context["references"] if r["case"]==case)
    if reference["target_p"]!=spec["target"]:
        raise ValueError("reference target mismatch")
    loaded,records={},{}
    for rung,chain in itertools.product(range(len(spec["rungs"])),range(spec["chains"])):
        task=(*group,rung,chain)
        artifact=c.load_artifact(root/"traces"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
        if artifact is None:
            raise ValueError(f"missing trace {task}; incomplete submission is not a sampling failure")
        arrays,record=artifact
        loaded[rung,chain]=arrays
        records[rung,chain]=record
        if record["status"]=="ok":
            if record["problem_hash"]!=c.digest(problem.metadata()):
                raise ValueError("model/decoder hash mismatch")
            if any(len(arrays[k])!=spec["steps"] for k in ("weight","syndrome_weight","sector")) or np.any(arrays["sector"]==0):
                raise ValueError("invalid full trace shape or failure support")
    anchored=c.load_artifact(root/"anchors"/f"{case}-{rep}",dict(manifest=c.digest(plan),case=case,replicate=rep))
    if anchored is None:
        raise ValueError("missing anchor")
    anchor=anchored[1]
    diagnostics,acf=[],{}
    output_rows=[]
    chain_counts=sorted(set([4,spec["chains"]]))
    diag_scalars=("mean","chain_means","chain_iat","chain_ess","iat","ess","iat_mcse","cross_chain_se","rhat")
    for chains,burn,samples in itertools.product(chain_counts,plan["burns"],spec["windows"]):
        compact={}
        rung_flags={}
        for rung in range(len(spec["rungs"])):
            if any(records[rung,j]["status"]!="ok" for j in range(chains)):
                rung_flags[rung]=dict(flagged=True,undefined=True,high_rhat=False,low_ess=False)
                continue
            obs={k:np.stack([loaded[rung,j][k][burn:burn+samples] for j in range(chains)]) for k in ("weight","syndrome_weight","sector")}
            if obs["weight"].shape!=(chains,samples):
                raise ValueError("short trace cannot provide window")
            compact[rung]=obs
            observable_values={k:obs[k] for k in ("weight","syndrome_weight")}
            observable_values.update({f"logical_bit_{bit}":(obs["sector"]>>bit)&1 for bit in range(len(code.lx)*(2 if spec["noise"]=="depolarizing" else 1))})
            flags=dict(flagged=False,undefined=False,high_rhat=False,low_ess=False)
            for name,values in observable_values.items():
                diag=c.diagnostic_record(values,name)
                flag=screen(diag)
                for key in flags:
                    flags[key]|=flag[key]
                acf_key=f"c{chains}_b{burn}_n{samples}_r{rung}_{name}"
                acf[acf_key]=np.asarray(diag["acf"]["chains"],dtype=float)
                diagnostics.append(dict(chains=chains,burn=burn,samples=samples,rung=rung,p=spec["rungs"][rung],observable=name,
                    **{k:diag[k] for k in diag_scalars},**flag,acf_key=acf_key,
                    sector_transitions=np.count_nonzero(obs["sector"][:,1:]!=obs["sector"][:,:-1],axis=1).tolist(),
                    unique_sectors=[len(np.unique(x)) for x in obs["sector"]]))
            rung_flags[rung]=flags
        for ladder_index,(label,ladder) in enumerate((("coarse",spec["coarse"]),("fine",spec["rungs"]))):
            rung_ids=[spec["rungs"].index(p) for p in ladder]
            flags={key:any(rung_flags[r][key] for r in rung_ids) for key in ("flagged","undefined","high_rhat","low_ess")}
            failed=[(*group,r,j) for r in rung_ids for j in range(chains) if records[r,j]["status"]!="ok"]
            overlaps=[]
            if not failed:
                for edge,(left,right) in enumerate(zip(rung_ids,rung_ids[1:])):
                    wleft,wright=compact[left]["weight"],compact[right]["weight"]
                    delta=c.log_density_difference(code.n,ladder[edge],ladder[edge+1])
                    ratio=c.histogram_bar(np.bincount(wleft.ravel(),minlength=code.n+1),
                                          np.bincount(wright.ravel(),minlength=code.n+1),delta)
                    means=[]
                    for rung,weights,sign in ((left,wleft,-1),(right,wright,1)):
                        values=np.exp(-np.logaddexp(0.,sign*(delta[weights]-ratio)))
                        means.append(float(values.mean()))
                        name=f"{label}_bennett_edge_{edge}"
                        diag=c.diagnostic_record(values,name)
                        flag=screen(diag)
                        for key in flags:
                            flags[key]|=flag[key]
                        acf_key=f"c{chains}_b{burn}_n{samples}_r{rung}_{name}"
                        acf[acf_key]=np.asarray(diag["acf"]["chains"],dtype=float)
                        diagnostics.append(dict(chains=chains,burn=burn,samples=samples,rung=rung,p=spec["rungs"][rung],
                            observable=name,**{k:diag[k] for k in diag_scalars},**flag,acf_key=acf_key))
                    overlaps.append(dict(edge=edge,left_mean=means[0],right_mean=means[1]))
            blocks=[v for v in plan["blocks"] if v<=samples and (v!=1024 or samples>=6000)]+[None]
            for block in blocks:
                row=dict(group=list(group),case=case,noise=spec["noise"],n=code.n,target_p=spec["target"],
                         kernel=list(plan["kernels"])[kernel],init=plan["initializations"][init],replicate=rep,
                         chains=chains,burn=burn,samples=samples,ladder=label,method="cross_chain" if block is None else "block",
                         block=block,estimate=None,log_estimate=None,log_se=None,interval=None,available=False,
                         failure=None,reference=reference["estimate"],reference_standard_error=reference["standard_error"],
                         reference_interval_999=reference["interval_999"],overlap=overlaps,**flags)
                if failed:
                    row["failure"]="sampling_failed"
                elif anchor["status"]!="ok" or not anchor["failures"]:
                    row["failure"]="anchor_unavailable"
                else:
                    estimate_start=time.perf_counter()
                    try:
                        result=c.estimate_window([compact[r]["weight"] for r in rung_ids],code.n,ladder,anchor["estimate"],block=block,
                            replicates=plan["bootstrap_replicates"],rng=np.random.default_rng(t.seed((33,*group,chains,burn,samples,ladder_index,block or 0),0)))
                        row.update(b.with_anchor_variance(result,anchor))
                    except (ValueError,FloatingPointError,OverflowError) as error:
                        row["failure"]=repr(error)
                    row["estimation_seconds"]=time.perf_counter()-estimate_start
                row.update(coverage_flags(row["interval"],reference))
                row["sampling_seconds_full_traces"]=sum(records[r,j].get("sampling_seconds",0) for r in rung_ids for j in range(chains))
                row["initialization_seconds"]=sum(records[r,j].get("initial_seconds",0) for r in rung_ids for j in range(chains))
                row["anchor_seconds"]=anchor.get("elapsed_seconds")
                output_rows.append(row)
    record=dict(status="ok",group=list(group),rows=output_rows,diagnostics=diagnostics,diagnostic_count=len(diagnostics),
                failed_tasks=[list((*group,*key)) for key,r in records.items() if r["status"]!="ok"],
                wall_seconds=time.perf_counter()-started,peak_rss_mb=c.peak_rss_mb(),warning=context["warning"])
    c.save_artifact(path,identity,acf,record)
    return {k:v for k,v in record.items() if k!="diagnostics"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["plan","run"])
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--reference",type=Path)
    parser.add_argument("--workers",type=int,default=96)
    parser.add_argument("--case",type=int,choices=range(4))
    args=parser.parse_args()
    plan=json.loads((args.root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(b.make_plan())):
        raise ValueError("production plan or runtime mismatch")
    context_path=args.root/"analysis_manifest.json"
    if args.command=="plan":
        if context_path.exists() or args.reference is None:
            raise ValueError("new analysis manifest and reference required")
        reference=json.loads(args.reference.read_text())
        if sorted(r["case"] for r in reference["records"])!=list(range(4)):
            raise ValueError("four completed independent references required")
        context=analysis_context(plan,reference["records"])
        context["reference_summary_sha256"]=c.file_hash(args.reference)
        (args.root/"reference_summary.json").write_bytes(args.reference.read_bytes())
        c.atomic_json(context_path,context)
        return
    context=json.loads(context_path.read_text())
    if context["analysis_source_sha256"]!=c.file_hash(__file__) or context["runtime"]!=b.runtime() or context["sampling_manifest"]!=c.digest(plan):
        raise ValueError("analysis source/runtime mismatch")
    if context["reference_summary_sha256"]!=c.file_hash(args.root/"reference_summary.json"):
        raise ValueError("reference changed")
    started=time.perf_counter()
    result=c.parallel_map(analyze_group,[(str(args.root),plan,context,g) for g in groups(plan,args.case)],args.workers)
    summary=dict(analysis=c.digest(context),groups=len(result),rows=sum(len(r["rows"]) for r in result),
                 unavailable_intervals=sum(not row["available"] for r in result for row in r["rows"]),
                 elapsed_seconds=time.perf_counter()-started)
    c.atomic_json(args.root/f"analysis_summary-{args.case}.json",summary)
    print(json.dumps(summary))


if __name__=="__main__":
    main()
