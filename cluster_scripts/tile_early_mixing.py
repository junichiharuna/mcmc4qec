"""Read-only preregistered diagnostics for completed tile288 target traces."""
import argparse
import itertools
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np
import calibration as c
import tile_study as t
import tile_bar_study as b
import tile_bar_analysis as statistics
import audit_tile_traces as audit
import probe_tile_decoder_platform as native

GROUPS=list(itertools.product((1,3),(0,1),(0,1),(0,1)))
PILOT=(3,0,0,0)
WARNING="Preregistered early diagnostics only; no reference or BAR estimate. All planned groups and undefined outcomes retained. Checkpoint re-decoding is not all-physical-state replay. Mixing, convergence, independent decoder correctness, precision and coverage are not certified. Production settings/seeds are unchanged."


def source_hashes():
    return {name:c.file_hash(module.__file__) for name,module in
            (("statistics",c),("tile",t),("sampling",b),("screens",statistics),("trace_audit",audit),("native",native))}|{"driver":c.file_hash(__file__)}


def prepare(source,root,profile,fixture):
    source,root=Path(source).resolve(),Path(root).resolve()
    if root.is_relative_to(source) or source.is_relative_to(root):
        raise ValueError("separate output root required")
    if root.exists() and any(root.iterdir()):
        raise ValueError("fresh output root required")
    production=json.loads((source/"manifest.json").read_text())
    if c.canonical(production)!=c.canonical(b.make_plan()):
        raise ValueError("fixed production source/runtime differs")
    summaries={}
    for case in (1,3):
        path=source/f"sample-{case}.json"
        row=json.loads(path.read_text())
        tasks=[tuple(item["task"]) for item in row["records"]]
        expected=list(b.tasks(production,case))
        if row["manifest"]!=c.digest(production) or row["command"]!="sample" or len(tasks)!=len(expected) or set(tasks)!=set(expected):
            raise ValueError("sampling summary incomplete or different")
        summaries[str(case)]=dict(sha256=c.file_hash(path),tasks=row["tasks"],failed=row["failed"])
    pbs=json.loads(subprocess.run(["qstat","-x","-f","-F","json","265210","265200"],capture_output=True,text=True,check=True,timeout=15).stdout)["Jobs"]
    completed={}
    for key,row in pbs.items():
        if row["job_state"]!="F" or row["Exit_status"]!=0:
            raise ValueError("selected sampling PBS job is not successfully terminal")
        completed[key]={name:row[name] for name in ("job_state","Exit_status","resources_used","obittime")}
    plan=dict(schema=1,source=str(source),sampling_manifest=c.digest(production),sampling_manifest_file_sha256=c.file_hash(source/"manifest.json"),
              selection=dict(groups=[list(group) for group in GROUPS],pilot=list(PILOT),chains=8,burn=6000,samples=12000,rung="last"),
              sources=source_hashes(),runtime=b.runtime(),platform_profile=c.digest(profile),platform_fixture=c.digest(fixture),
              completed_summaries=summaries,completed_pbs=completed,warning=WARNING)
    root.mkdir(parents=True,exist_ok=True)
    for name,value in (("manifest",plan),("production_manifest",production),("platform_profile",profile),("platform_fixture",fixture)):
        c.atomic_json(root/(name+".json"),value)
    _,_,native_evidence=validate(root)
    c.atomic_json(root/"native_preflight.json",native_evidence)
    return plan


def validate(root):
    root=Path(root)
    plan=json.loads((root/"manifest.json").read_text())
    production=json.loads((root/"production_manifest.json").read_text())
    if plan["sources"]!=source_hashes() or c.canonical(plan["runtime"])!=c.canonical(b.runtime()):
        raise ValueError("early diagnostic source/runtime changed")
    if c.canonical(production)!=c.canonical(b.make_plan()) or c.digest(production)!=plan["sampling_manifest"]:
        raise ValueError("frozen production plan differs")
    source=Path(plan["source"])
    if c.file_hash(source/"manifest.json")!=plan["sampling_manifest_file_sha256"]:
        raise ValueError("production manifest changed")
    expected=dict(groups=[list(group) for group in GROUPS],pilot=list(PILOT),chains=8,burn=6000,samples=12000,rung="last")
    if plan["selection"]!=expected:
        raise ValueError("preregistered group/window selection changed")
    profile=json.loads((root/"platform_profile.json").read_text())
    fixture=json.loads((root/"platform_fixture.json").read_text())
    if c.digest(profile)!=plan["platform_profile"] or c.digest(fixture)!=plan["platform_fixture"]:
        raise ValueError("native inputs changed")
    start=time.perf_counter()
    actual=native.probe(fixture)
    audit.validate_platform(profile,actual)
    return plan,production,dict(profile=c.digest(actual),actual_profile=actual,seconds=time.perf_counter()-start)


def diagnose(values,name):
    try:
        result=c.diagnostic_record(values,name)
        return dict(result,**statistics.screen(result),available=True)
    except (ValueError,FloatingPointError,OverflowError) as error:
        return dict(observable=name,available=False,error=repr(error),mean=None,iat=None,ess=None,iat_mcse=None,
                    cross_chain_se=None,rhat=None,chain_iat=[None]*len(values),chain_ess=[None]*len(values),
                    undefined=True,high_rhat=False,low_ess=False,flagged=True)


def group(root,plan,production,coordinates,native_proof):
    root=Path(root)
    coordinates=tuple(coordinates)
    if coordinates not in GROUPS:
        raise ValueError("group outside fixed subset")
    path=root/"groups"/(c.task_id(coordinates)+".json")
    if path.exists():
        raise ValueError("preserve existing group outcome")
    started,cpu=time.perf_counter(),time.process_time()
    case,kernel,initial,rep=coordinates
    spec=production["cases"][case]
    rung=len(spec["rungs"])-1
    code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
    bits=len(code.lx)*(2 if spec["noise"]=="depolarizing" else 1)
    names=["weight","syndrome_weight"]+[f"logical_bit_{i}" for i in range(bits)]
    result=dict(group=list(coordinates),p=spec["rungs"][rung],decoder_prior=spec["target"],status="ok",
                planned_chains=8,burn=6000,samples=12000,native=native_proof,trace_audits=[],input_markers={},
                diagnostics=[],conditional_weight=None,conditional_weight_standard_error=None,warning=WARNING)
    loaded=[]
    errors=[]
    for chain in range(8):
        task=(case,kernel,initial,rep,rung,chain)
        artifact=Path(plan["source"])/"traces"/c.task_id(task)
        marker=artifact.with_suffix(".done.json")
        try:
            if not marker.exists() or set(json.loads(marker.read_text())["sha256"])!={".json",".npz"}:
                raise ValueError("missing or incomplete artifact marker")
            digest=c.file_hash(marker)
            arrays,record=c.load_artifact(artifact,dict(manifest=plan["sampling_manifest"],task=list(task)))
            proof=audit.audit_trace(production,task,arrays,record,code,problem)
            if c.file_hash(marker)!=digest:
                raise ValueError("artifact changed during audit")
            result["input_markers"][c.task_id(task)]=dict(marker_sha256=digest,payload_sha256=json.loads(marker.read_text())["sha256"])
            result["trace_audits"].append(proof)
            if record["status"]!="ok":
                errors.append(dict(task=list(task),kind="recorded_sampling_failure",error=record.get("error")))
            else:
                loaded.append(arrays)
        except Exception as error:
            errors.append(dict(task=list(task),kind="invalid_or_unavailable_input",error=repr(error)))
    result["input_errors"]=errors
    if errors:
        result["status"]="unavailable"
        result["diagnostics"]=[dict(observable=name,available=False,undefined=True,flagged=True,error="input unavailable") for name in names]
    else:
        compact={key:np.stack([array[key][6000:18000] for array in loaded]) for key in ("weight","syndrome_weight","sector")}
        observables={key:compact[key] for key in ("weight","syndrome_weight")}
        observables.update({f"logical_bit_{i}":(compact["sector"]>>i)&1 for i in range(bits)})
        result["diagnostics"]=[diagnose(values,name) for name,values in observables.items()]
        weight=result["diagnostics"][0]
        result.update(conditional_weight=weight["mean"],conditional_weight_standard_error=weight["iat_mcse"],
                      conditional_weight_error_method="IAT MCSE of conditional weight, not BAR logical-error uncertainty",
                      sector_transitions=np.count_nonzero(compact["sector"][:,1:]!=compact["sector"][:,:-1],axis=1).tolist(),
                      unique_sectors=[len(np.unique(row)) for row in compact["sector"]])
    result.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_mb=c.peak_rss_mb(),
                  undefined_observables=sum(row["undefined"] for row in result["diagnostics"]),
                  flagged_observables=sum(row["flagged"] for row in result["diagnostics"]),
                  physical_checkpoint_redecodes=sum(row["redecoded_checkpoints"] for row in result["trace_audits"]),
                  all_physical_states_redecoded=False)
    c.atomic_json(path,result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("plan","group","remaining"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--source",type=Path)
    parser.add_argument("--profile",type=Path)
    parser.add_argument("--fixture",type=Path)
    parser.add_argument("--group",type=int,nargs=4)
    args=parser.parse_args()
    if args.command=="plan":
        result=prepare(args.source,args.root,json.loads(args.profile.read_text()),json.loads(args.fixture.read_text()))
        print(json.dumps(dict(manifest=c.digest(result),groups=len(GROUPS),pilot=PILOT)))
        return
    plan,production,proof=validate(args.root)
    if args.command=="group":
        if tuple(args.group)!=PILOT and not (args.root/"groups"/(c.task_id(PILOT)+".json")).exists():
            raise ValueError("fixed pilot must run first")
        rows=[group(args.root,plan,production,args.group,proof)]
    else:
        pilot=json.loads((args.root/"groups"/(c.task_id(PILOT)+".json")).read_text())
        if 2*(proof["seconds"]+16*pilot["wall_seconds"])>=45:
            raise ValueError("pilot exceeds batch budget; report cost and use fixed individual groups")
        rows=[group(args.root,plan,production,key,proof) for key in GROUPS if key!=PILOT]
    print(json.dumps([dict(group=row["group"],status=row["status"],wall_seconds=row["wall_seconds"],
                           undefined_observables=row["undefined_observables"],flagged_observables=row["flagged_observables"]) for row in rows]))


if __name__=="__main__":main()
