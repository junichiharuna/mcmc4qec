"""Validate low-noise compact traces and re-decode saved physical checkpoints."""
from dataclasses import asdict
import json
import math
from pathlib import Path

import numpy as np
import mcmc4qec as qec
import calibration as c
import tile_study as t
import tile_low_noise_study as low
import tile_low_noise_analysis as analysis
import audit_tile_traces as original
import probe_tile_decoder_platform as platform_probe

WARNING = "All compact entries checked; only stored initial/checkpoint physical states re-decoded. Seed/initialization checks are not full RNG trajectory replay. This is the same decoder implementation, not independent decoder correctness evidence or a mixing, convergence, accuracy or coverage guarantee. Failed sampling tasks are retained. The pure audit_task helper alone does not validate the native execution platform."


def validate_native_environment(plan, *, platform_profile, platform_fixture):
    """Probe this process and reject changed inputs, source or native behavior."""
    if plan["purpose"] not in ("low_noise_capacity", "low_noise_production"):
        raise ValueError("low-noise sampling plan required")
    values=dict(platform_profile=platform_profile,platform_fixture=platform_fixture)
    if {key:c.digest(value) for key,value in values.items()}!=plan["native_input_digests"]:
        raise ValueError("native input binding differs")
    if (c.canonical(plan["runtime"])!=c.canonical(t.runtime())
            or c.canonical(platform_profile["runtime"])!=c.canonical(plan["runtime"])
            or platform_profile["fixture"]!=c.digest(platform_fixture)):
        raise ValueError("native profile, source runtime or fixture differs")
    actual=platform_probe.probe(platform_fixture)
    original.validate_platform(platform_profile,actual)
    return dict(native_platform_verified=True,platform_profile=c.digest(platform_profile),
                platform_fixture=c.digest(platform_fixture),actual_profile=c.digest(actual))


def _array(arrays,key,dtype,shape,low_value,high_value):
    value=arrays[key]
    if (not isinstance(value,np.ndarray) or value.dtype!=dtype or value.shape!=shape
            or np.any(value<low_value) or np.any(value>high_value)):
        raise ValueError("invalid trace array: "+key)
    return value


def audit_task(plan, task, arrays, record, code, problem):
    """Check one loaded task; caller supplies its fixed-plan code and Problem.

    This pure numerical helper performs no native-profile or artifact I/O check.
    Scientific artifact execution must enter through audit_saved_task (or an
    equally strict native/profile/hash gate in a future full-cohort runner).
    """
    if plan["purpose"] not in ("low_noise_capacity", "low_noise_production"):
        raise ValueError("low-noise sampling plan required")
    low.validate_task(plan,task,"sample")
    analysis.validate_record(plan,task,"sample",record,problem)
    for key in ("wall_seconds","cpu_seconds"):
        value=record[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise ValueError("invalid trace timing")
    rss=record["peak_rss_mb"]
    if rss is not None and (isinstance(rss,bool) or not isinstance(rss,(int,float)) or not math.isfinite(rss) or rss<0):
        raise ValueError("invalid trace RSS")
    out=dict(task=list(task),status=record["status"],redecoded_checkpoints=0,
             all_physical_states_redecoded=False,native_platform_verified=False,rss_available=rss is not None,warning=WARNING)
    if record["status"]=="failed":
        return dict(out,recorded_failure=record["error"])
    for key in ("construction_seconds","initial_seconds","sampling_seconds","compact_seconds"):
        if isinstance(record[key],bool) or not math.isfinite(record[key]) or record[key]<0:
            raise ValueError("invalid phase timing")
    spec=plan["condition"]
    _,_,kernel,initial,rep,rung,chain=task
    steps,stride=spec["steps"],plan["checkpoint_stride"]
    if type(steps) is not int or steps<=0 or type(stride) is not int or stride<=0:
        raise ValueError("positive saved length/checkpoint stride required")
    expected_keys={"weight","syndrome_weight","sector","checkpoint_indices","checkpoints",
                   "initial","final","initial_coefficients","initial_syndrome"}
    if set(arrays)!=expected_keys:
        raise ValueError("unexpected trace payload set")
    if spec["noise"] not in ("bit","depolarizing"):
        raise ValueError("unsupported low-noise model")
    n=code.n
    bits=len(code.lx)*(2 if spec["noise"]=="depolarizing" else 1)
    checks=len(code.hz)+(len(code.hx) if spec["noise"]=="depolarizing" else 0)
    for key,dtype,lower,upper in (("weight",np.uint16,0,n),
            ("syndrome_weight",np.uint16,0,checks),("sector",np.uint32,1,(1<<bits)-1)):
        _array(arrays,key,dtype,(steps,),lower,upper)
    indices=np.unique(np.r_[np.arange(0,steps,stride),steps-1])
    stored=arrays["checkpoint_indices"]
    if not isinstance(stored,np.ndarray) or stored.dtype.kind not in "iu" or not np.array_equal(stored,indices):
        raise ValueError("checkpoint schedule differs")
    alphabet=1 if spec["noise"]=="bit" else 3
    for key,shape in (("initial",(n,)),("final",(n,)),("checkpoints",(len(indices),n))):
        _array(arrays,key,np.uint8,shape,0,alphabet)
    _array(arrays,"initial_syndrome",np.uint8,(checks,),0,1)
    coefficients=_array(arrays,"initial_coefficients",np.uint8,(bits,),0,1)
    if not np.array_equal(arrays["final"],arrays["checkpoints"][-1]):
        raise ValueError("final state differs from last checkpoint")
    name=list(plan["kernels"])[kernel]
    config=qec.SamplingConfig(samples=steps,burn_in=0,kernels=qec.KernelConfig(**plan["kernels"][name]),
                              cache_cap=plan["cache_cap"],cache_policy="lru")
    if any(c.canonical(record["config"][key])!=c.canonical(value) for key,value in asdict(config).items()):
        raise ValueError("effective sampling configuration differs")
    if (record["config"]["initialization"]!="provided"
            or record["config"]["initial_states"]!=[arrays["initial"].tolist()]):
        raise ValueError("recorded initialization differs")
    if not 0<bits<63:
        raise ValueError("bounded nonempty logical basis required")
    mode=plan["initializations"][initial]
    if mode=="logical_basis":
        expected_coeff=np.zeros(bits,dtype=np.uint8)
        expected_coeff[(rep*spec["chains"]+chain)%bits]=1
    elif mode=="logical_combination":
        value=int(np.random.default_rng(record["init_seed"]).integers(1,1<<bits))
        expected_coeff=np.array([(value>>bit)&1 for bit in range(bits)],dtype=np.uint8)
    else:
        raise ValueError("unknown logical initialization")
    if not np.array_equal(coefficients,expected_coeff):
        raise ValueError("initial logical coefficients differ from seed/basis selection")
    basis=np.asarray(code.lx,dtype=np.uint8) if spec["noise"]=="bit" else np.stack(
        (code.lx,3*code.lz),axis=1).reshape(-1,n).astype(np.uint8)
    expected_initial=np.bitwise_xor.reduce(basis[expected_coeff.astype(bool)],axis=0)
    if not np.array_equal(arrays["initial"],expected_initial):
        raise ValueError("initial physical state differs from logical coefficients")
    proposed=0
    for statistics in record["acceptance"].values():
        moved,accepted,count=(statistics[key] for key in ("moved","accepted","proposed"))
        if any(type(value) is not int for value in (moved,accepted,count)) or not 0<=moved<=accepted<=count:
            raise ValueError("invalid acceptance counts")
        proposed+=count
    if proposed!=steps:
        raise ValueError("acceptance counts omit saved steps")
    for index,state in [(None,arrays["initial"]),*zip(indices,arrays["checkpoints"])]:
        syndrome=problem.model.syndrome(state)
        residual=problem.model.observables(state)^problem.decoder.predict(syndrome)
        sector=sum(int(value)<<bit for bit,value in enumerate(residual))
        if not sector or not problem.is_faulty(state) or not math.isfinite(problem.log_prob(state,spec["rungs"][rung])):
            raise ValueError("physical state outside supported failure set")
        if index is None:
            if record["initial_sector"]!=sector or not np.array_equal(arrays["initial_syndrome"],syndrome):
                raise ValueError("initial syndrome/sector differs")
        else:
            observed=dict(weight=int(np.count_nonzero(state)),syndrome_weight=int(syndrome.sum()),sector=sector)
            if any(int(arrays[key][index])!=value for key,value in observed.items()):
                raise ValueError("re-decoded checkpoint differs from compact trace")
    return dict(out,saved_steps=steps,redecoded_checkpoints=len(indices),initial_state_checked=True,
                initial_coefficients_checked=True,recorded_seeds_checked=True,
                rejected_steps_retained_by_length_and_proposal_count=True)


def audit_saved_task(root, plan, task, *, platform_profile, platform_fixture):
    """Require the actual native environment and payload hashes before auditing."""
    evidence=validate_native_environment(plan,platform_profile=platform_profile,platform_fixture=platform_fixture)
    expected=low.make_plan(plan["case"],plan["target_index"],capacity=plan["purpose"]=="low_noise_capacity")
    if c.canonical(plan)!=c.canonical(expected):
        raise ValueError("fixed sampling plan/source/runtime differs")
    low.validate_task(plan,task,"sample")
    path=Path(root)/"traces"/c.task_id(task)
    marker=path.with_suffix(".done.json")
    if not marker.exists():
        raise ValueError("missing trace artifact is not a recorded failure")
    if set(json.loads(marker.read_text())["sha256"])!={".json",".npz"}:
        raise ValueError("incomplete artifact checksum set")
    marker_digest=c.file_hash(marker)
    value=c.load_artifact(path,dict(manifest=c.digest(plan),task=list(task)))
    if value is None:
        raise ValueError("missing trace artifact is not a recorded failure")
    spec=plan["condition"]
    code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
    result=audit_task(plan,task,*value,code,problem)
    if c.file_hash(marker)!=marker_digest:
        raise ValueError("artifact marker changed during audit")
    result.update(evidence)
    return dict(result,input_marker_sha256=marker_digest,
                sampling_manifest=c.digest(plan),audit_source_sha256=c.file_hash(__file__))
