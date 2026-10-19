"""Audit full compact traces and re-decode saved checkpoints, never infer mixing."""
import argparse
from dataclasses import asdict
import itertools
import json
import math
import os
from pathlib import Path

import numpy as np
import mcmc4qec as qec
import calibration as c
import tile_bar_study as b
import tile_study as t
import probe_tile_decoder_platform as platform_probe


WARNING="Compact arrays checked at every saved step; only stored initial/checkpoint physical states re-decoded. Recorded seeds are checked, not full RNG trajectory replay. Uses the same decoder implementation, not an independent decoder correctness proof. No mixing or coverage inference. Failed sampling tasks remain in the denominator."


def validate_platform(expected,actual):
    keys=("fixture","source_sha256","runtime","platform","machine","python_build","byteorder",
          "thread_environment","native_ldpc_sha256","problem_hash","repeated","fresh","decoder_probe")
    if not expected.get("native_ldpc_sha256") or any(key not in expected or key not in actual or
        c.canonical(expected[key])!=c.canonical(actual[key]) for key in keys):
        raise ValueError("native decoder environment or fixture response differs from generating platform")


def audit_trace(plan,task,arrays,record,code,problem):
    case,kernel,init,rep,rung,chain=task
    if not 0<=case<len(plan["cases"]):
        raise ValueError("invalid trace case")
    spec=plan["cases"][case]
    if record["task"]!=list(task) or not (0<=kernel<len(plan["kernels"]) and 0<=init<len(plan["initializations"])
        and 0<=rep<plan["replicates"] and 0<=rung<len(spec["rungs"]) and 0<=chain<spec["chains"]):
        raise ValueError("trace task identity differs")
    for key in ("wall_seconds","cpu_seconds"):
        if not math.isfinite(record[key]) or record[key]<0:
            raise ValueError("invalid trace timing")
    out=dict(task=list(task),status=record["status"],redecoded_checkpoints=0,all_physical_states_redecoded=False)
    if record["status"]=="failed":
        return dict(out,recorded_failure=record["error"])
    if record["status"]!="ok" or record["problem_hash"]!=c.digest(problem.metadata()):
        raise ValueError("wrong status or fixed decoder/model")
    if record["init_seed"]!=b.task_seed(plan,task,0) or record["sample_seed"]!=b.task_seed(plan,task,1):
        raise ValueError("recorded trace seeds differ")
    steps=spec["steps"]
    if record["checked_saved_states"]!=steps:
        raise ValueError("wrong number of saved states")
    expected_keys={"weight","syndrome_weight","sector","checkpoint_indices","checkpoints","initial","final"}
    if set(arrays)!=expected_keys:
        raise ValueError("unexpected trace payload set")
    n=code.n
    logical_bits=len(code.lx)*(2 if spec["noise"]=="depolarizing" else 1)
    checks=len(code.hz)+(len(code.hx) if spec["noise"]=="depolarizing" else 0)
    for key,dtype,low,high in (("weight",np.uint16,0,n),("syndrome_weight",np.uint16,0,checks),("sector",np.uint32,1,2**logical_bits-1)):
        values=arrays[key]
        if values.dtype!=dtype or values.shape!=(steps,) or np.any(values<low) or np.any(values>high):
            raise ValueError(f"invalid compact trace: {key}")
    indices=np.unique(np.r_[np.arange(0,steps,1000),steps-1])
    stored=arrays["checkpoint_indices"]
    if stored.dtype.kind not in "iu" or not np.array_equal(stored,indices):
        raise ValueError("checkpoint schedule differs")
    alphabet=1 if spec["noise"]=="bit" else 3
    for key,shape in (("initial",(n,)),("final",(n,)),("checkpoints",(len(indices),n))):
        value=arrays[key]
        if value.dtype!=np.uint8 or value.shape!=shape or np.any(value>alphabet):
            raise ValueError(f"invalid physical states: {key}")
    if not np.array_equal(arrays["final"],arrays["checkpoints"][-1]):
        raise ValueError("final physical state differs from final checkpoint")
    name=list(plan["kernels"])[kernel]
    config=qec.SamplingConfig(samples=steps,burn_in=0,kernels=qec.KernelConfig(**plan["kernels"][name]),
                              cache_cap=plan["cache_cap"],cache_policy="lru")
    for key,value in asdict(config).items():
        if c.canonical(record["config"][key])!=c.canonical(value):
            raise ValueError("sampling configuration differs")
    if record["config"]["initialization"]!="provided" or record["config"]["initial_states"]!=[arrays["initial"].tolist()]:
        raise ValueError("recorded effective initialization differs")
    mode=plan["initializations"][init]
    attempts=record["initial_attempts"]
    if mode=="logical":
        basis=code.lx if spec["noise"]=="bit" else np.concatenate((code.lx,3*code.lz))
        expected=basis[(rep*spec["chains"]+chain)%len(basis)]
        if attempts!=0 or not np.array_equal(arrays["initial"],expected):
            raise ValueError("logical initialization differs from fixed basis selection")
    elif mode!="rejection" or not isinstance(attempts,int) or not 1<=attempts<=plan["max_initial_attempts"]:
        raise ValueError("invalid rejection initialization count")
    proposed=0
    for stats in record["acceptance"].values():
        values=[stats[key] for key in ("moved","accepted","proposed")]
        if any(not isinstance(value,int) for value in values) or not 0<=values[0]<=values[1]<=values[2]:
            raise ValueError("invalid acceptance counts")
        proposed+=values[2]
    if proposed!=steps:
        raise ValueError("acceptance counts omit steps")
    for index,state in [(None,arrays["initial"]),*zip(indices,arrays["checkpoints"])]:
        syndrome=problem.model.syndrome(state)
        residual=problem.model.observables(state)^problem.decoder.predict(syndrome)
        sector=sum(int(value)<<bit for bit,value in enumerate(residual))
        if sector==0 or not problem.is_faulty(state) or not math.isfinite(problem.log_prob(state,spec["rungs"][rung])):
            raise ValueError("stored physical state is outside supported failure set")
        if index is not None:
            expected={"weight":int(np.count_nonzero(state)),"syndrome_weight":int(syndrome.sum()),"sector":sector}
            if any(int(arrays[key][index])!=value for key,value in expected.items()):
                raise ValueError("re-decoded checkpoint differs from compact trace")
    return dict(out,saved_steps=steps,redecoded_checkpoints=len(indices),initial_state_checked=True,
                logical_initial_basis_checked=mode=="logical",recorded_seeds_checked=True,
                rejected_steps_retained_by_length_and_proposal_count=True)


def audit_group(args):
    source,root,plan,context,group=args
    path=Path(root)/"groups"/c.task_id(group)
    identity=dict(audit=c.digest(context),group=list(group))
    cached=c.load_artifact(path,identity)
    if cached is not None:
        for task_id,checksum in cached[1]["input_marker_sha256"].items():
            if c.file_hash(Path(source)/"traces"/(task_id+".done.json"))!=checksum:
                raise ValueError("sampling marker changed after audit")
            original=c.load_artifact(Path(source)/"traces"/task_id,
                                     dict(manifest=c.digest(plan),task=list(map(int,task_id.split("-")))))
            if original is None:
                raise ValueError("sampling input missing after audit")
        return cached[1]
    case,kernel,init,rep=group
    spec=plan["cases"][case]
    code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
    rows=[]
    input_markers={}
    for rung,chain in itertools.product(range(len(spec["rungs"])),range(spec["chains"])):
        task=(*group,rung,chain)
        value=c.load_artifact(Path(source)/"traces"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
        if value is None:
            raise ValueError(f"missing trace is not a recorded sampling failure: {task}")
        rows.append(audit_trace(plan,task,*value,code,problem))
        input_markers[c.task_id(task)]=c.file_hash(Path(source)/"traces"/(c.task_id(task)+".done.json"))
    record=dict(group=list(group),tasks=len(rows),failed_sampling=sum(row["status"]=="failed" for row in rows),
                redecoded_checkpoints=sum(row["redecoded_checkpoints"] for row in rows),records=rows,
                input_marker_sha256=input_markers,warning=WARNING)
    c.save_artifact(path,identity,{},record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4),required=True)
    parser.add_argument("--platform-profile",type=Path,required=True)
    parser.add_argument("--platform-fixture",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=96)
    args=parser.parse_args()
    if not os.environ.get("PBS_JOBID") or args.workers!=96:
        raise ValueError("full scientific audit requires a 96-worker qsub job")
    if any(os.environ.get(key)!="1" for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")):
        raise ValueError("single-thread worker environment required")
    plan=json.loads((args.source_root/"manifest.json").read_text())
    if plan!=json.loads(c.canonical(b.make_plan())):
        raise ValueError("sampling source/runtime differs from fixed plan")
    profile=json.loads(args.platform_profile.read_text())
    fixture=json.loads(args.platform_fixture.read_text())
    validate_platform(profile,platform_probe.probe(fixture))
    context=dict(sampling_manifest=c.digest(plan),case=args.case,audit_source_sha256=c.file_hash(__file__),runtime=b.runtime(),
                 decoder_platform_profile=c.digest(profile),decoder_platform_fixture=c.digest(fixture),warning=WARNING)
    manifest=args.root/"audit_manifest.json"
    if manifest.exists():
        if json.loads(manifest.read_text())!=context:
            raise ValueError("audit identity changed")
    else:
        c.atomic_json(manifest,context)
    groups=[(args.case,*tail) for tail in itertools.product(range(2),range(2),range(plan["replicates"]))]
    rows=c.parallel_map(audit_group,[(str(args.source_root),str(args.root),plan,context,group) for group in groups],args.workers)
    if [tuple(row["group"]) for row in rows]!=groups:
        raise ValueError("incomplete audit groups")
    summary=dict(audit=c.digest(context),groups=len(rows),tasks=sum(row["tasks"] for row in rows),
                 failed_sampling=sum(row["failed_sampling"] for row in rows),
                 redecoded_checkpoints=sum(row["redecoded_checkpoints"] for row in rows),warning=WARNING)
    c.atomic_json(args.root/"summary.json",summary)
    print(json.dumps(summary))


if __name__=="__main__":
    main()
