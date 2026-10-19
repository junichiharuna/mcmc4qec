"""Fixed-prior low-noise BAR analysis; independent references are compared later."""
import argparse
import itertools
import json
import math
import os
from pathlib import Path
import socket
import time

import numpy as np
import calibration as c
import tile_study as t
import tile_bar_study as b
import tile_bar_analysis as old
import tile_low_noise_study as low

WARNING = "All planned outcomes retained. No independent reference point is supplied here. Diagnostics and setting agreement do not certify convergence, accuracy or coverage. Native fixture validation is finite; full numerical trace audit remains separate."
screen = old.screen

def diagnostic_record(values,name):
    """Preserve numerical diagnostic failures without dropping an outcome."""
    try:
        return c.diagnostic_record(values,name)
    except (ValueError,FloatingPointError,OverflowError) as error:
        chains=values.shape[0]
        return dict(mean=None,chain_means=[None]*chains,chain_iat=[None]*chains,
                    chain_ess=[None]*chains,iat=None,ess=None,iat_mcse=None,
                    cross_chain_se=None,rhat=None,acf={"chains":np.full((chains,1),np.nan)},
                    error=repr(error))

def selected_chain_counts(plan):
    return sorted(set(plan["condition"]["chains"] if value=="maximum" else value
                      for value in plan["chain_counts"]))


def groups(plan):
    return ((plan["case"],plan["target_index"],kernel,initial,rep)
            for kernel,initial,rep in itertools.product(range(2),range(2),range(plan["replicates"])))


def analysis_settings(plan):
    spec=plan["condition"]
    for chains,burn,samples in itertools.product(selected_chain_counts(plan),plan["burns"],spec["windows"]):
        for index,(label,ladder) in enumerate((("coarse",spec["coarse"]),("fine",spec["rungs"]))):
            for block in [v for v in plan["blocks"] if v<=samples and (v!=1024 or samples>=6000)]+[None]:
                yield chains,burn,samples,index,label,ladder,block


def bootstrap_seed(plan,group,chains,burn,samples,ladder_index,block):
    return t.seed((plan["stages"]["analysis"],*group,chains,burn,samples,ladder_index,block or 0),0)


def analysis_context(plan,evidence):
    if plan["purpose"]!="low_noise_production" or plan["replicates"]!=192 or plan["stages"]["analysis"]!=153:
        raise ValueError("production cohort required; sampling capacity cannot supply BAR chains")
    return dict(schema=1,purpose="low_noise_analysis",sampling_manifest=c.digest(plan),
                sources={name:c.file_hash(module.__file__) for name,module in
                         (("sampling",low),("statistics",c),("bar",b),("diagnostics",old))},
                analysis_source_sha256=c.file_hash(__file__),runtime=b.runtime(),
                completed_phase_evidence=evidence,replicates=192,seed_stage=153,
                screens=dict(rhat_gt=1.01,min_chain_ess_lt=100),warning=WARNING)


def validate_context(plan,context):
    if c.canonical(context)!=c.canonical(analysis_context(plan,context["completed_phase_evidence"])):
        raise ValueError("analysis context/source/runtime differs")


def completed_phase_evidence(root,plan):
    """Bind full task census, pinned native profile, and each PBS phase identity."""
    root=Path(root)
    manifest=c.digest(plan)
    for key,digest in plan["native_input_digests"].items():
        if c.digest(json.loads((root/(key+".json")).read_text()))!=digest:
            raise ValueError("native input differs")
    evidence={}
    for phase in ("sample","anchors"):
        summary_path=root/f"{phase}-summary.json"
        summary=json.loads(summary_path.read_text())
        expected=sorted(low.tasks(plan,phase))
        rows=summary["records"]
        if (summary["manifest"]!=manifest or summary["phase"]!=phase
                or summary["tasks"]!=len(expected) or [tuple(row["task"]) for row in rows]!=expected
                or any(row["status"] not in ("ok","failed") for row in rows)
                or summary["failed"]!=sum(row["status"]=="failed" for row in rows)):
            raise ValueError("complete phase task census differs")
        native_path=root/f"preflight-{phase}"/"native_preflight.json"
        if c.file_hash(native_path)!=summary["native_preflight_sha256"]:
            raise ValueError("native phase evidence differs")
        native=json.loads(native_path.read_text())
        intent_path=root/f"{phase}-execution-intent.json"
        intent=json.loads(intent_path.read_text())
        if (native["manifest"]!=manifest or not native["pbs_job_id"] or not native["hostname"]
                or intent["phase"]!=phase or any(intent[key]!=native[key] for key in ("manifest","pbs_job_id","hostname"))):
            raise ValueError("PBS phase execution binding differs")
        low.native.trace_audit.validate_platform(json.loads((root/"platform_profile.json").read_text()),native["profile"])
        evidence[phase]=dict(summary_sha256=c.file_hash(summary_path),native_preflight_sha256=c.file_hash(native_path),
                             execution_intent_sha256=c.file_hash(intent_path),tasks=len(rows),failed=summary["failed"])
        if phase=="sample":
            by_group={}
            for row in rows:
                by_group.setdefault(c.task_id(row["task"][:5]),[]).append(row)
            evidence[phase]["group_record_digests"]={key:c.digest(value) for key,value in by_group.items()}
        else:
            evidence[phase]["record_digests"]={c.task_id(row["task"]):c.digest(row) for row in rows}
    return evidence


def validate_record(plan,task,phase,record,problem):
    spec=plan["condition"]
    p=spec["rungs"][task[5] if phase=="sample" else 0]
    seed=low.task_seed(plan,task,phase,1 if phase=="sample" else 0)
    if (record["task"]!=list(task) or record["status"] not in ("ok","failed")
            or record["stage"]!=plan["stages"][phase] or record["physical_p"]!=p
            or record["decoder_prior"]!=spec["target"]
            or record["sample_seed" if phase=="sample" else "seed"]!=seed):
        raise ValueError("task prior/probability/seed/status differs")
    if phase=="sample" and (record["init_seed"]!=low.task_seed(plan,task,phase,0)
                              or record["initialization"]!=plan["initializations"][task[3]]):
        raise ValueError("initialization provenance differs")
    if record["status"]=="failed":
        if not record.get("error"):
            raise ValueError("failed task reason missing")
        return
    if record["problem_hash"]!=c.digest(problem.metadata()):
        raise ValueError("fixed Problem differs")
    low.check_metadata(type("SavedResult",(),{"metadata":record["metadata"]})(),problem,p,seed)
    cfg=record["metadata"]["config"]
    if phase=="sample":
        if (record["checked_saved_states"]!=spec["steps"] or record["config"]!=cfg
                or cfg["samples"]!=spec["steps"] or cfg["burn_in"]!=0
                or c.canonical(cfg["kernels"])!=c.canonical(plan["kernels"][list(plan["kernels"])[task[2]]])
                or cfg["cache_cap"]!=plan["cache_cap"] or cfg["cache_policy"]!="lru"):
            raise ValueError("sampling configuration differs")
    elif (record["trials"]!=plan["anchor_trials"] or cfg["trials"]!=plan["anchor_trials"]
          or type(record["failures"]) is not int or not 0<=record["failures"]<=record["trials"]
          or record["estimate"]!=record["failures"]/record["trials"]):
        raise ValueError("anchor budget/count differs")


def load_group(root,plan,group):
    root=Path(root)
    if (len(group)!=5 or any(type(x) is not int for x in group)
            or group[:2]!=(plan["case"],plan["target_index"])
            or not 0<=group[2]<2 or not 0<=group[3]<2 or not 0<=group[4]<plan["replicates"]):
        raise ValueError("invalid analysis group")
    spec=plan["condition"]
    code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
    loaded,records,digests={},{},{}
    def read(task,phase):
        path=root/("traces" if phase=="sample" else "anchors")/c.task_id(task)
        marker=path.with_suffix(".done.json")
        if not marker.exists():
            raise ValueError(f"missing {phase} artifact {task}; not a recorded failure")
        if set(json.loads(marker.read_text())["sha256"])!={".json",".npz"}:
            raise ValueError("incomplete artifact checksums")
        arrays,record=c.load_artifact(path,dict(manifest=c.digest(plan),task=list(task)))
        validate_record(plan,task,phase,record,problem)
        digests[f"{phase}/{c.task_id(task)}"]=c.file_hash(marker)
        return arrays,record
    for rung,chain in itertools.product(range(len(spec["rungs"])),range(spec["chains"])):
        arrays,record=read((*group,rung,chain),"sample")
        if record["status"]=="ok":
            limits=dict(weight=code.n,syndrome_weight=len(code.hz)+(len(code.hx) if spec["noise"]=="depolarizing" else 0),
                        sector=(1<<(len(code.lx)*(2 if spec["noise"]=="depolarizing" else 1)))-1)
            for key,limit in limits.items():
                value=arrays[key]
                if (value.shape!=(spec["steps"],) or value.dtype.kind not in "iu"
                        or np.any(value<(1 if key=="sector" else 0)) or np.any(value>limit)):
                    raise ValueError("compact trace shape/range/support differs")
        loaded[rung,chain],records[rung,chain]=arrays,record
    anchor=read((group[0],group[1],0,0,group[4],0,0),"anchors")[1]
    return loaded,records,anchor,digests

def analyze_arrays(plan, group, loaded, records, anchor):
    """Compute planned windows from validated compact inputs; not a provenance gate.

    loaded and records map (rung, chain) to arrays and task records. Successful
    arrays contain one-dimensional integer weight, syndrome_weight, sector of
    length steps; failed records may have empty arrays. Synthetic callers must
    mark their outputs as resource fixtures and never publish scientific rows.
    """
    started=time.perf_counter()
    case,target_index,kernel,init,rep=group
    spec=plan["condition"]
    code,_=t.build_problem(spec["size"],spec["noise"],spec["target"])
    diagnostics,acf=[],{}
    output_rows=[]
    chain_counts=selected_chain_counts(plan)
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
                diag=diagnostic_record(values,name)
                flag=screen(diag)
                for key in flags:
                    flags[key]|=flag[key]
                acf_key=f"c{chains}_b{burn}_n{samples}_r{rung}_{name}"
                acf[acf_key]=np.asarray(diag["acf"]["chains"],dtype=float)
                diagnostics.append(dict(chains=chains,burn=burn,samples=samples,rung=rung,p=spec["rungs"][rung],observable=name,
                    **{k:diag[k] for k in diag_scalars},**flag,acf_key=acf_key,diagnostic_error=diag.get("error"),
                    sector_transitions=np.count_nonzero(obs["sector"][:,1:]!=obs["sector"][:,:-1],axis=1).tolist(),
                    unique_sectors=[len(np.unique(x)) for x in obs["sector"]]))
            rung_flags[rung]=flags
        for ladder_index,(label,ladder) in enumerate((("coarse",spec["coarse"]),("fine",spec["rungs"]))):
            rung_ids=[spec["rungs"].index(p) for p in ladder]
            flags={key:any(rung_flags[r][key] for r in rung_ids) for key in ("flagged","undefined","high_rhat","low_ess")}
            failed=[(*group,r,j) for r in rung_ids for j in range(chains) if records[r,j]["status"]!="ok"]
            overlaps=[]
            overlap_errors=[]
            if not failed:
                for edge,(left,right) in enumerate(zip(rung_ids,rung_ids[1:])):
                    wleft,wright=compact[left]["weight"],compact[right]["weight"]
                    delta=c.log_density_difference(code.n,ladder[edge],ladder[edge+1])
                    try:
                        ratio=c.histogram_bar(np.bincount(wleft.ravel(),minlength=code.n+1),
                                              np.bincount(wright.ravel(),minlength=code.n+1),delta)
                        if not np.isfinite(ratio):
                            raise FloatingPointError("nonfinite overlap BAR ratio")
                    except (ValueError,FloatingPointError,OverflowError) as error:
                        overlap_errors.append(dict(edge=edge,error=repr(error)))
                        flags.update(flagged=True,undefined=True)
                        continue
                    means=[]
                    for rung,weights,sign in ((left,wleft,-1),(right,wright,1)):
                        values=np.exp(-np.logaddexp(0.,sign*(delta[weights]-ratio)))
                        means.append(float(values.mean()))
                        name=f"{label}_bennett_edge_{edge}"
                        diag=diagnostic_record(values,name)
                        flag=screen(diag)
                        for key in flags:
                            flags[key]|=flag[key]
                        acf_key=f"c{chains}_b{burn}_n{samples}_r{rung}_{name}"
                        acf[acf_key]=np.asarray(diag["acf"]["chains"],dtype=float)
                        diagnostics.append(dict(chains=chains,burn=burn,samples=samples,rung=rung,p=spec["rungs"][rung],
                            observable=name,**{k:diag[k] for k in diag_scalars},**flag,acf_key=acf_key,
                            diagnostic_error=diag.get("error")))
                    overlaps.append(dict(edge=edge,left_mean=means[0],right_mean=means[1]))
            blocks=[v for v in plan["blocks"] if v<=samples and (v!=1024 or samples>=6000)]+[None]
            for block in blocks:
                row=dict(group=list(group),case=case,noise=spec["noise"],n=code.n,target_p=spec["target"],
                         kernel=list(plan["kernels"])[kernel],init=plan["initializations"][init],replicate=rep,
                         chains=chains,burn=burn,samples=samples,ladder=label,method="cross_chain" if block is None else "block",
                         block=block,estimate=None,log_estimate=None,log_se=None,interval=None,available=False,
                         failure=None,reference=None,reference_available=False,reference_standard_error=None,
                         reference_interval_999=None,overlap=overlaps,overlap_errors=overlap_errors,**flags)
                if failed:
                    row["failure"]="sampling_failed"
                elif anchor["status"]!="ok" or not anchor["failures"]:
                    row["failure"]="anchor_unavailable"
                else:
                    estimate_start=time.perf_counter()
                    try:
                        result=c.estimate_window([compact[r]["weight"] for r in rung_ids],code.n,ladder,anchor["estimate"],block=block,
                            replicates=plan["bootstrap_replicates"],rng=np.random.default_rng(bootstrap_seed(plan,group,chains,burn,samples,ladder_index,block)))
                        if any(not math.isfinite(result[key]) for key in ("log_estimate","log_se")):
                            raise FloatingPointError("nonfinite BAR uncertainty or point")
                        row.update(b.with_anchor_variance(result,anchor))
                    except (ValueError,FloatingPointError,OverflowError) as error:
                        row["failure"]=repr(error)
                    row["estimation_seconds"]=time.perf_counter()-estimate_start
                row["sampling_seconds_full_traces"]=sum(records[r,j].get("sampling_seconds",0) for r in rung_ids for j in range(chains))
                row["initialization_seconds"]=sum(records[r,j].get("initial_seconds",0) for r in rung_ids for j in range(chains))
                row["anchor_seconds"]=anchor.get("elapsed_seconds")
                output_rows.append(row)
    record=dict(status="ok",group=list(group),rows=output_rows,diagnostics=diagnostics,diagnostic_count=len(diagnostics),
                failed_tasks=[list((*group,*key)) for key,r in records.items() if r["status"]!="ok"],
                wall_seconds=time.perf_counter()-started,peak_rss_mb=c.peak_rss_mb(),warning=WARNING)
    return record,acf


def analyze_group(args):
    root,plan,context,group=args
    root=Path(root)
    validate_context(plan,context)
    loaded,records,anchor,digests=load_group(root,plan,group)
    evidence=context["completed_phase_evidence"]
    reduced=[{key:records[index][key] for key in ("task","status","wall_seconds","cpu_seconds","peak_rss_mb")}
             for index in sorted(records)]
    if (c.digest(reduced)!=evidence["sample"]["group_record_digests"][c.task_id(group)]
            or c.digest(anchor)!=evidence["anchors"]["record_digests"][c.task_id(anchor["task"])]):
        raise ValueError("raw artifact and completed phase summary differ")
    identity=dict(analysis=c.digest(context),group=list(group),input_artifact_markers=digests)
    path=root/"analysis"/c.task_id(group)
    cached=c.load_artifact(path,identity)
    if cached is not None:
        return {key:value for key,value in cached[1].items() if key!="diagnostics"}
    record,acf=analyze_arrays(plan,group,loaded,records,anchor)
    record["input_artifact_markers"]=digests
    c.save_artifact(path,identity,acf,record)
    return {key:value for key,value in record.items() if key!="diagnostics"}


def read_production_plan(root):
    plan=json.loads((Path(root)/"manifest.json").read_text())
    if c.canonical(plan)!=c.canonical(low.make_plan(plan["case"],plan["target_index"],capacity=False)):
        raise ValueError("production manifest/source/runtime differs")
    return plan


def run_phase(root,plan,context,workers):
    root=Path(root)
    if (not os.environ.get("PBS_JOBID") or type(workers) is not int or not 1<=workers<=96
            or any(os.environ.get(key)!=value for key,value in low.native.THREADS.items())):
        raise ValueError("qsub with 1..96 workers and pinned single-thread environment required")
    if c.canonical(plan)!=c.canonical(read_production_plan(root)):
        raise ValueError("production plan differs")
    validate_context(plan,context)
    if completed_phase_evidence(root,plan)!=context["completed_phase_evidence"]:
        raise ValueError("completed phase evidence changed")
    if any((root/name).exists() for name in ("analysis","analysis-summary.json","analysis-execution-intent.json","preflight-analysis")):
        raise ValueError("existing analysis evidence; automatic rerun forbidden")
    intent=dict(manifest=c.digest(plan),analysis=c.digest(context),phase="analysis",workers=workers,
                pbs_job_id=os.environ["PBS_JOBID"],hostname=socket.gethostname())
    with (root/"analysis-execution-intent.json").open("xb") as stream:
        stream.write(c.canonical(intent)+b"\n")
    native_hash=low.preflight(root,plan,"analysis")
    started=time.perf_counter()
    jobs=list(groups(plan))
    results=c.parallel_map(analyze_group,[(str(root),plan,context,group) for group in jobs],workers)
    results.sort(key=lambda row:row["group"])
    expected=sorted(jobs)
    if [tuple(row["group"]) for row in results]!=expected:
        raise ValueError("missing or duplicate analysis group")
    row_count=sum(1 for _ in analysis_settings(plan))
    if any(len(result["rows"])!=row_count for result in results):
        raise ValueError("missing planned analysis settings")
    summary=dict(analysis=c.digest(context),manifest=c.digest(plan),groups=len(results),replicates=plan["replicates"],
                 rows=sum(len(result["rows"]) for result in results),workers=workers,
                 unavailable_intervals=sum(not row["available"] for result in results for row in result["rows"]),
                 failed_sampling_groups=sum(bool(result["failed_tasks"]) for result in results),
                 phase_wall_seconds=time.perf_counter()-started,native_preflight_sha256=native_hash,
                 warning=WARNING)
    c.atomic_json(root/"analysis-summary.json",summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","run"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    plan=read_production_plan(args.root)
    context_path=args.root/"analysis_manifest.json"
    if args.command=="plan":
        if context_path.exists():
            raise ValueError("analysis manifest exists")
        context=analysis_context(plan,completed_phase_evidence(args.root,plan))
        c.atomic_json(context_path,context)
        print(json.dumps(dict(analysis=c.digest(context),groups=sum(1 for _ in groups(plan)),
                              rows_per_group=sum(1 for _ in analysis_settings(plan)))))
    else:
        context=json.loads(context_path.read_text())
        print(json.dumps(run_phase(args.root,plan,context,args.workers)))


if __name__=="__main__":
    main()
