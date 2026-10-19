"""Low-noise trace checks distinguish compact arrays from physical checkpoints."""
from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_study as t
import tile_low_noise_study as low
import audit_tile_low_noise_traces as audit


def generate(root, case=0, capacity=False, initial=0):
    plan=low.make_plan(case,2,capacity=capacity)
    plan["condition"].update(chains=2,steps=7,rungs=[.1,.001],coarse=[.1,.001])
    plan["checkpoint_stride"]=3
    task=(case,2,0,initial,1,1,1)
    record=low.sample_task((str(root),plan,task))
    assert record["status"]=="ok",record
    arrays,record=c.load_artifact(root/"traces"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
    code,problem=t.build_problem(plan["condition"]["size"],plan["condition"]["noise"],.001)
    return plan,task,arrays,record,code,problem


@pytest.fixture(scope="module")
def saved(tmp_path_factory):
    return generate(tmp_path_factory.mktemp("low-audit"))


def clone(saved):
    # Native decoder objects cannot be deep-copied; only inputs are mutated.
    return (*deepcopy(saved[:4]),*saved[4:])


@pytest.mark.parametrize("case",range(4))
@pytest.mark.parametrize("capacity,initial",[(False,0),(False,1),(True,0),(True,1)])
def test_actual_short_traces_all_cases_and_initializations(tmp_path,case,capacity,initial):
    data=generate(tmp_path,case,capacity,initial)
    result=audit.audit_task(*data)
    assert result["status"]=="ok" and result["saved_steps"]==7
    assert result["redecoded_checkpoints"]==3 and result["initial_state_checked"]
    assert result["initial_coefficients_checked"] and result["recorded_seeds_checked"]
    assert result["rejected_steps_retained_by_length_and_proposal_count"]
    assert not result["all_physical_states_redecoded"]
    assert not result["native_platform_verified"]


@pytest.mark.parametrize("change",[
    "task_target","task_bool","capacity_chain","purpose","prior","physical_p","stage","sample_seed","init_seed",
    "problem_hash","metadata_prior","metadata_seed","config","metadata_config","initialization",
    "wall_nan","cpu_negative","rss_negative","checked_length","initial_sector",
    "acceptance_sum","acceptance_boolean","coefficients","initial_syndrome","final",
    "weight_dtype","sector_dtype","length","sector_zero","sector_high","syndrome_high","weight_high",
    "checkpoint_schedule","checkpoint_dtype","checkpoint_alphabet","initial_dtype","extra_payload",
    "compact_checkpoint","initial_config","coeff_nonbinary"])
def test_corrupt_trace_is_rejected(saved,change):
    plan,task,arrays,record,code,problem=clone(saved)
    if change=="task_target": task=(0,1,*task[2:])
    elif change=="task_bool": task=(False,*task[1:])
    elif change=="capacity_chain": plan["purpose"]="low_noise_capacity"; task=(*task[:-1],0)
    elif change=="purpose": plan["purpose"]="synthetic"
    elif change in ("prior","physical_p","stage","sample_seed","init_seed"):
        key="decoder_prior" if change=="prior" else change
        record[key]=record[key]+1
    elif change=="problem_hash": record[change]="wrong"
    elif change=="metadata_prior": record["metadata"]["sampling_p"]+=.01
    elif change=="metadata_seed": record["metadata"]["rng"]["entropy"]+=1
    elif change=="config": record["config"]["thin"]=2
    elif change=="metadata_config": record["metadata"]["config"]["thin"]=2
    elif change=="initialization": record[change]="rejection"
    elif change=="wall_nan": record["wall_seconds"]=np.nan
    elif change=="cpu_negative": record["cpu_seconds"]=-1
    elif change=="rss_negative": record["peak_rss_mb"]=-1
    elif change=="checked_length": record["checked_saved_states"]-=1
    elif change=="initial_sector": record[change]=0
    elif change=="acceptance_sum": record["acceptance"]={"fake":dict(proposed=1,accepted=0,moved=0)}
    elif change=="acceptance_boolean": record["acceptance"]={"fake":dict(proposed=True,accepted=0,moved=0)}
    elif change=="coefficients": arrays["initial_coefficients"]=np.roll(arrays["initial_coefficients"],1)
    elif change=="coeff_nonbinary": arrays["initial_coefficients"][0]=2
    elif change=="initial_syndrome": arrays[change][0]^=1
    elif change=="final": arrays[change]=arrays[change].copy(); arrays[change][0]^=1
    elif change=="weight_dtype": arrays["weight"]=arrays["weight"].astype(np.uint32)
    elif change=="sector_dtype": arrays["sector"]=arrays["sector"].astype(np.uint16)
    elif change=="length": arrays["weight"]=arrays["weight"][:-1]
    elif change=="sector_zero": arrays["sector"][1]=0
    elif change=="sector_high": arrays["sector"][1]=2**len(code.lx)
    elif change=="syndrome_high": arrays["syndrome_weight"][1]=len(code.hz)+1
    elif change=="weight_high": arrays["weight"][1]=code.n+1
    elif change=="checkpoint_schedule": arrays["checkpoint_indices"][1]=2
    elif change=="checkpoint_dtype": arrays["checkpoint_indices"]=arrays["checkpoint_indices"].astype(float)
    elif change=="checkpoint_alphabet": arrays["checkpoints"][0,0]=2
    elif change=="initial_dtype": arrays["initial"]=arrays["initial"].astype(np.int64)
    elif change=="extra_payload": arrays["extra"]=np.array([1])
    elif change=="compact_checkpoint": arrays["weight"][0]=(arrays["weight"][0]+1)%(code.n+1)
    elif change=="initial_config": record["config"]["initial_states"][0][0]^=1
    with pytest.raises(ValueError):
        audit.audit_task(plan,task,arrays,record,code,problem)


def test_failed_task_is_retained_with_provenance(saved):
    plan,task,arrays,record,code,problem=clone(saved)
    record.update(status="failed",error="test failure")
    for key in ("metadata","problem_hash","checked_saved_states","config","acceptance","initial_sector"):
        record.pop(key)
    result=audit.audit_task(plan,task,{},record,code,problem)
    assert result["status"]=="failed" and result["recorded_failure"]=="test failure"
    assert result["redecoded_checkpoints"]==0 and not result["all_physical_states_redecoded"]
    record["sample_seed"]+=1
    with pytest.raises(ValueError): audit.audit_task(plan,task,{},record,code,problem)


def test_actual_driver_failure_keeps_partial_payload_and_task(tmp_path,monkeypatch):
    plan=low.make_plan(0,2,capacity=True)
    task=next(low.tasks(plan))
    def broken(*args,**kwargs): raise RuntimeError("injected sampling failure")
    monkeypatch.setattr(low.qec,"sample_faulty",broken)
    low.sample_task((str(tmp_path),plan,task))
    arrays,record=c.load_artifact(tmp_path/"traces"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
    assert record["status"]=="failed" and "initial" in arrays
    code,problem=t.build_problem(6,"bit",.001)
    result=audit.audit_task(plan,task,arrays,record,code,problem)
    assert result["task"]==list(task) and result["status"]=="failed"
    assert result["redecoded_checkpoints"]==0
    assert "injected sampling failure" in result["recorded_failure"]


def test_supplied_initial_is_not_required_to_equal_first_post_step(saved):
    plan,task,arrays,record,code,problem=clone(saved)
    state=arrays["checkpoints"][0]^np.asarray(code.hx[0],dtype=np.uint8)
    assert not np.array_equal(state,arrays["initial"]) and problem.is_faulty(state)
    arrays["checkpoints"][0]=state
    compact=t.compact(problem,state[None,:])
    for key in ("weight","syndrome_weight","sector"): arrays[key][0]=compact[key][0]
    assert audit.audit_task(plan,task,arrays,record,code,problem)["status"]=="ok"


def test_native_preflight_binds_inputs_runtime_and_actual_probe(monkeypatch):
    plan=low.make_plan(0,2,capacity=True)
    values=deepcopy(low.native.platform_inputs())
    values["platform_profile"]["runtime"]=deepcopy(plan["runtime"])
    plan["native_input_digests"]={key:c.digest(value) for key,value in values.items()}
    calls=[]
    def probe(fixture):
        calls.append(fixture)
        return deepcopy(values["platform_profile"])
    monkeypatch.setattr(audit.platform_probe,"probe",probe)
    result=audit.validate_native_environment(plan,**values)
    assert calls and result["native_platform_verified"]
    wrong=deepcopy(values)
    wrong["platform_profile"]["runtime"]["package_sha256"]="different"
    with pytest.raises(ValueError): audit.validate_native_environment(plan,**wrong)
    monkeypatch.setattr(audit.platform_probe,"probe",lambda fixture:{})
    with pytest.raises(ValueError): audit.validate_native_environment(plan,**values)


def test_artifact_entry_requires_native_preflight_before_loading(saved,tmp_path,monkeypatch):
    plan,task,*_=saved
    def reject(*args,**kwargs): raise ValueError("native preflight required")
    monkeypatch.setattr(audit,"validate_native_environment",reject)
    with pytest.raises(ValueError,match="native preflight"):
        audit.audit_saved_task(tmp_path,plan,task,platform_profile={},platform_fixture={})


def test_artifact_entry_binds_marker_payload_and_keeps_missing_distinct(tmp_path,monkeypatch):
    plan,task,*_=generate(tmp_path)
    monkeypatch.setattr(audit,"validate_native_environment",lambda *a,**k:dict(native_platform_verified=True))
    monkeypatch.setattr(low,"make_plan",lambda *a,**k:deepcopy(plan))
    result=audit.audit_saved_task(tmp_path,plan,task,platform_profile={},platform_fixture={})
    assert result["native_platform_verified"] and result["input_marker_sha256"]
    assert result["sampling_manifest"]==c.digest(plan)
    path=tmp_path/"traces"/c.task_id(task)
    payload=path.with_suffix(".json")
    original=payload.read_bytes()
    payload.write_bytes(original+b" ")
    with pytest.raises(ValueError):
        audit.audit_saved_task(tmp_path,plan,task,platform_profile={},platform_fixture={})
    payload.write_bytes(original)
    path.with_suffix(".done.json").unlink()
    with pytest.raises(ValueError,match="missing"):
        audit.audit_saved_task(tmp_path,plan,task,platform_profile={},platform_fixture={})
