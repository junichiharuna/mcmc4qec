"""Production weight-reference input gates and immutable plans, without heavy runs."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_weight_pilot as p
import audit_tile_weight_pilot as audit_module
import tile_weight_stratified as w
import tile_weight_reference_driver as d


def inputs():
    pilot=p.make_plan()
    strata=[]
    conditions=[]
    for case,(size,noise) in enumerate(pilot["cases"]):
        for prior_index,prior in enumerate(pilot["priors"][case]):
            conditions.append(dict(case=case,physical_decoder_prior=prior,layers=[dict(w=0,mode="enum",trials=1)]))
            for weight in pilot["weights"]:
                trials=pilot["replicates"]*(1 if weight==0 else pilot["samples"])
                strata.append(dict(case=case,prior_index=prior_index,physical_decoder_prior=prior,
                    sector_prior=prior if noise=="bit" else 2*prior/3,n=2*size*size,noise=noise,w=weight,
                    pattern_count=w.class_size(2*size*size,weight,noise),allocation_ready=True,
                    expected_replicates=8,success_replicates=8,trials_available=trials,failures_available=0,
                    failure_rate=0.,resource_profile_complete=True,task_wall_seconds_mean=.1,
                    task_wall_seconds_max=.2,peak_rss_mb_max=100.,observed_task_seconds_per_trial=.001))
    audit=dict(manifest=c.digest(pilot),purpose="weight_pilot_allocation_audit",expected_tasks=1536,
        allocation_ready=True,failed_tasks=[],resource_profile_complete=True,trials=sum(r["trials_available"] for r in strata),
        strata=strata,raw_draws_regenerated=True,successful_metadata_verified=True,
        source_sha256=c.file_hash(audit_module.__file__),strata_source_sha256=c.file_hash(w.__file__))
    fixture={"synthetic":"plan validation only"}
    profile=dict(fixture=c.digest(fixture),native_ldpc_sha256={"fixture.so":"not an actual native preflight"})
    allocation=dict(conditions=conditions,chunk_size=4096,pilot_audit_digest=c.digest(audit),platform_profile_digest=c.digest(profile))
    return allocation,pilot,audit,profile,fixture


def test_all_sixteen_conditions_and_all_pilot_strata_are_bound_to_plan():
    values=inputs()
    context=d.make_context(*values)
    assert len(context["reference"]["conditions"])==16
    assert context["reference"]["seed_stage"]==130
    assert context["input_digests"]["pilot_audit"]==c.digest(values[2])
    assert context["planned_trials"]==16
    bad=list(deepcopy(values))
    bad[0]["conditions"].pop()
    with pytest.raises(ValueError):
        d.make_context(*bad)


@pytest.mark.parametrize("field",["failed_tasks","strata","trials","raw_draws_regenerated","source_sha256"])
def test_incomplete_or_changed_pilot_is_not_accepted(field):
    values=list(inputs())
    audit=values[2]
    if field=="strata":
        audit[field].pop()
    elif field=="failed_tasks":
        audit[field]=[[0,0,0,0]]
    elif field=="trials":
        audit[field]+=1
    elif field=="source_sha256":
        audit[field]="other"
    else:
        audit[field]=False
    values[0]["pilot_audit_digest"]=c.digest(audit)
    with pytest.raises(ValueError):
        d.make_context(*values)


@pytest.mark.parametrize("field,value",[("prior_index",99),("failures_available",999999),("peak_rss_mb_max",None),("success_replicates",7)])
def test_layer_identity_counts_and_resource_measurement_are_checked(field,value):
    values=list(inputs())
    values[2]["strata"][0][field]=value
    values[0]["pilot_audit_digest"]=c.digest(values[2])
    with pytest.raises(ValueError):
        d.make_context(*values)


def test_full_run_cannot_start_outside_pbs(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    monkeypatch.setattr(sys,"argv",["tile_weight_reference_driver.py","run","--root",str(tmp_path)])
    with pytest.raises(ValueError,match="qsub"):
        d.main()
    assert not list(tmp_path.iterdir())


def test_plan_freezes_inputs_and_run_records_unavailable_conditions(tmp_path,monkeypatch):
    values=inputs()
    arguments=["tile_weight_reference_driver.py","plan","--root",str(tmp_path/"run")]
    for key,value in zip(d.INPUTS,values):
        path=tmp_path/(key+".json")
        c.atomic_json(path,value)
        arguments.extend(["--"+key.replace("_","-"),str(path)])
    checks=[]
    monkeypatch.setattr(d.native_probe,"probe",lambda fixture:values[3])
    def guard(expected,actual):
        assert expected==actual==values[3]
        checks.append(1)
    monkeypatch.setattr(d.trace_audit,"validate_platform",guard)
    monkeypatch.setattr(sys,"argv",arguments)
    d.main()
    root=tmp_path/"run"
    context=json.loads((root/"manifest.json").read_text())
    assert context==json.loads(c.canonical(d.make_context(*values)))
    assert checks==[1]
    plan_evidence=json.loads((root/"native_preflight_plan.json").read_text())
    assert plan_evidence["manifest"]==c.digest(context)
    assert plan_evidence["profile"]==values[3]
    assert plan_evidence["hostname"] and plan_evidence["wall_seconds"]>=0
    def parallel(function,jobs,workers):
        assert workers==96
        run_evidence=json.loads((root/"native_preflight_run.json").read_text())
        assert run_evidence["manifest"]==c.digest(context)
        assert run_evidence["profile"]==values[3]
        assert run_evidence["pbs_job_id"]=="unit-test-no-job"
        assert run_evidence["hostname"] and run_evidence["wall_seconds"]>=0
        if function is d.r.run_chunk:
            return [dict(task=list(task),status="failed" if task[0]==0 else "ok") for _,_,task in jobs]
        assert function is d.aggregate_from_root
        return [dict(condition=index,available=index!=0,reference=None) for _,_,index in jobs]
    monkeypatch.setattr(d.c,"parallel_map",parallel)
    monkeypatch.setenv("PBS_JOBID","unit-test-no-job")
    for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
        monkeypatch.setenv(key,"1")
    monkeypatch.setattr(sys,"argv",["tile_weight_reference_driver.py","run","--root",str(root)])
    def mismatch(expected,actual):
        raise ValueError("native mismatch test")
    monkeypatch.setattr(d.trace_audit,"validate_platform",mismatch)
    with pytest.raises(ValueError,match="native mismatch"):
        d.main()
    assert not (root/"native_preflight_run.json").exists()
    assert not (root/"chunks_summary.json").exists()
    monkeypatch.setattr(d.trace_audit,"validate_platform",guard)
    with pytest.raises(RuntimeError,match="failed reference chunks retained"):
        d.main()
    assert checks==[1,1]
    summary=json.loads((root/"summary.json").read_text())
    chunks=json.loads((root/"chunks_summary.json").read_text())
    assert summary["conditions"]==16 and summary["unavailable"]==1
    assert chunks["tasks"]==16 and chunks["failed"]==1
    evidence_hash=c.file_hash(root/"native_preflight_run.json")
    assert summary["native_preflight_sha256"]==chunks["native_preflight_sha256"]==evidence_hash
    altered=deepcopy(values[0])
    altered["chunk_size"]=2048
    c.atomic_json(root/"allocation.json",altered)
    with pytest.raises(ValueError,match="changed"):
        d.main()
    assert c.file_hash(root/"native_preflight_run.json")==evidence_hash


def test_task_order_uses_measured_layer_or_conservative_missing_layer_cost():
    values=inputs()
    context=d.make_context(*values)
    plan=context["reference"]
    plan["conditions"][0]["layers"]=[dict(w=i,mode="mc",trials=8) for i in range(10)]
    audit=values[2]
    for row in audit["strata"]:
        row["observed_task_seconds_per_trial"]=3. if row["w"]==1 else 1.
    assert d.estimated_task_cost(plan,values[1],audit,(0,0,0))==8
    assert d.estimated_task_cost(plan,values[1],audit,(0,1,0))==24
    assert d.estimated_task_cost(plan,values[1],audit,(0,9,0))==24
