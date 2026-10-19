"""Low-noise analysis preserves the planned denominator and fixed failure set."""
from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_study as low
import tile_low_noise_analysis as a


def short_plan(case=0):
    plan=low.make_plan(case,2,capacity=False)
    plan["condition"].update(rungs=[.1,.001],coarse=[.1,.001],chains=4,steps=10,windows=[8])
    plan.update(burns=[2],blocks=[2],bootstrap_replicates=8,anchor_trials=16)
    return plan


def short_group(root,case=0):
    plan=short_plan(case)
    group=(case,2,0,0,0)
    for rung in range(2):
        for chain in range(4):
            result=low.sample_task((str(root),plan,(*group,rung,chain)))
            assert result["status"]=="ok",result
    result=low.anchor_task((str(root),plan,(case,2,0,0,0,0,0)))
    assert result["status"]=="ok",result
    return plan,group


@pytest.mark.parametrize("case",range(4))
def test_actual_short_trace_analysis_all_cases(tmp_path,case):
    plan,group=short_group(tmp_path,case)
    loaded,records,anchor,digests=a.load_group(tmp_path,plan,group)
    result,acf=a.analyze_arrays(plan,group,loaded,records,anchor)
    assert len(result["rows"])==4
    assert len(acf)>0 and result["diagnostic_count"]==len(result["diagnostics"])
    assert all(row["reference"] is None and not row["reference_available"] for row in result["rows"])
    assert all(row["group"]==list(group) and row["target_p"]==.001 for row in result["rows"])
    assert all("covered_reference_point" not in row for row in result["rows"])
    assert len(digests)==9
    assert all(row["undefined"] or row["low_ess"] for row in result["rows"])
    if anchor["failures"]:
        assert all(row["log_estimate"] is not None for row in result["rows"])


def test_failed_task_preserves_every_affected_row(tmp_path):
    plan,group=short_group(tmp_path)
    loaded,records,anchor,_=a.load_group(tmp_path,plan,group)
    records[1,0]=dict(records[1,0],status="failed",error="fixture failure")
    loaded[1,0]={}
    record,_=a.analyze_arrays(plan,group,loaded,records,anchor)
    assert len(record["rows"])==4
    assert all(row["failure"]=="sampling_failed" and not row["available"] for row in record["rows"])
    assert record["failed_tasks"]==[[*group,1,0]]


def test_zero_anchor_keeps_rows_without_reference(tmp_path):
    plan,group=short_group(tmp_path)
    loaded,records,anchor,_=a.load_group(tmp_path,plan,group)
    anchor.update(failures=0,estimate=0.)
    record,_=a.analyze_arrays(plan,group,loaded,records,anchor)
    assert all(row["failure"]=="anchor_unavailable" for row in record["rows"])


def test_missing_artifact_is_not_failed_sampling(tmp_path):
    plan,group=short_group(tmp_path)
    (tmp_path/"traces"/"0-2-0-0-0-0-0.done.json").unlink()
    with pytest.raises(ValueError,match="missing"):
        a.load_group(tmp_path,plan,group)


@pytest.mark.parametrize("key,value",[("decoder_prior",.01),("sample_seed",4),("physical_p",.03),("checked_saved_states",9)])
def test_changed_raw_provenance_rejected(tmp_path,key,value):
    plan,group=short_group(tmp_path)
    task=(*group,0,0)
    base=tmp_path/"traces"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task))
    arrays,record=c.load_artifact(base,identity)
    record[key]=value
    c.save_artifact(base,identity,arrays,record)
    with pytest.raises(ValueError,match="differs"):
        a.load_group(tmp_path,plan,group)


def test_capacity_sampling_cannot_supply_bar():
    plan=low.make_plan(0,0,capacity=True)
    with pytest.raises(ValueError,match="capacity"):
        a.analysis_context(plan,{})


def test_bootstrap_stage_target_and_setting_namespace():
    seeds=[]
    for target in range(3):
        plan=low.make_plan(0,target,capacity=False)
        assert len(list(a.groups(plan)))==768
        group=(0,target,0,0,0)
        for chains,burn,samples,index,_,_,block in a.analysis_settings(plan):
            seed=a.bootstrap_seed(plan,group,chains,burn,samples,index,block)
            assert seed==low.t.seed((153,*group,chains,burn,samples,index,block or 0),0)
            seeds.append(seed)
    assert len(seeds)==len(set(seeds))


def test_phase_guard_without_pbs(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="qsub"):
        a.run_phase(tmp_path,short_plan(),{},96)


def test_context_rejects_source_or_sampling_change():
    plan=short_plan()
    context=a.analysis_context(plan,{"sample":"fixture","anchors":"fixture"})
    a.validate_context(plan,context)
    altered=deepcopy(context)
    altered["sampling_manifest"]="changed"
    with pytest.raises(ValueError,match="context"):
        a.validate_context(plan,altered)


def test_group_target_and_replicate_validation(tmp_path):
    for group in ((0,1,0,0,0),(0,2,0,0,192),(0,2,2,0,0)):
        with pytest.raises(ValueError,match="group"):
            a.load_group(tmp_path,short_plan(),group)


@pytest.mark.parametrize("kind",["diagnostics","estimation","overlap"])
def test_numerical_failure_does_not_drop_rows(tmp_path,monkeypatch,kind):
    plan,group=short_group(tmp_path)
    loaded,records,anchor,_=a.load_group(tmp_path,plan,group)
    anchor.update(failures=1,estimate=1/16)
    def fail(*args,**kwargs):
        raise FloatingPointError("fixture numerical failure")
    monkeypatch.setattr(c,{"diagnostics":"diagnostic_record","estimation":"estimate_window","overlap":"histogram_bar"}[kind],fail)
    result,_=a.analyze_arrays(plan,group,loaded,records,anchor)
    assert len(result["rows"])==4
    if kind=="diagnostics":
        assert all(row["undefined"] for row in result["rows"])
        assert all(diag["diagnostic_error"] for diag in result["diagnostics"])
    else:
        assert all(not row["available"] and "fixture numerical failure" in row["failure"] for row in result["rows"])


def test_analysis_cache_binds_input_marker_hashes(tmp_path):
    plan,group=short_group(tmp_path)
    _,records,anchor,_=a.load_group(tmp_path,plan,group)
    reduced=[{key:records[index][key] for key in ("task","status","wall_seconds","cpu_seconds","peak_rss_mb")}
             for index in sorted(records)]
    evidence=dict(sample={"group_record_digests":{c.task_id(group):c.digest(reduced)}},
                  anchors={"record_digests":{c.task_id(anchor["task"]):c.digest(anchor)}})
    context=a.analysis_context(plan,evidence)
    first=a.analyze_group((tmp_path,plan,context,group))
    assert a.analyze_group((tmp_path,plan,context,group))==first
    task=(*group,0,0)
    path=tmp_path/"traces"/c.task_id(task)
    identity=dict(manifest=c.digest(plan),task=list(task))
    arrays,record=c.load_artifact(path,identity)
    arrays["weight"][0]=(int(arrays["weight"][0])+1)%73
    c.save_artifact(path,identity,arrays,record)
    with pytest.raises(ValueError,match="identity mismatch"):
        a.analyze_group((tmp_path,plan,context,group))


@pytest.mark.parametrize("change",[None,"manifest","job","missing_task","native_hash","failed_count"])
def test_completed_phase_evidence_binds_census_and_native(tmp_path,monkeypatch,change):
    plan=short_plan()
    profile={"fixture":True}
    plan["native_input_digests"]={"platform_profile":c.digest(profile)}
    c.atomic_json(tmp_path/"platform_profile.json",profile)
    monkeypatch.setattr(low.native.trace_audit,"validate_platform",lambda expected,actual:None)
    task=(0,2,0,0,0,0,0)
    monkeypatch.setattr(low,"tasks",lambda p,phase:iter([task]))
    for phase in ("sample","anchors"):
        path=tmp_path/f"preflight-{phase}"/"native_preflight.json"
        path.parent.mkdir()
        native=dict(manifest=c.digest(plan),pbs_job_id="fixture.pbs",hostname="fixture",profile=profile)
        c.atomic_json(path,native)
        intent=dict(native,phase=phase)
        if phase=="sample" and change=="job": intent["pbs_job_id"]="other.pbs"
        c.atomic_json(tmp_path/f"{phase}-execution-intent.json",intent)
        summary=dict(manifest=c.digest(plan),phase=phase,tasks=1,records=[dict(task=list(task),status="failed")],
                     failed=1,native_preflight_sha256=c.file_hash(path))
        if phase=="sample":
            if change=="manifest": summary["manifest"]="changed"
            elif change=="missing_task": summary["records"]=[]
            elif change=="native_hash": summary["native_preflight_sha256"]="changed"
            elif change=="failed_count": summary["failed"]=0
        c.atomic_json(tmp_path/f"{phase}-summary.json",summary)
    if change:
        with pytest.raises(ValueError): a.completed_phase_evidence(tmp_path,plan)
    else:
        evidence=a.completed_phase_evidence(tmp_path,plan)
        assert evidence["sample"]["failed"]==1
        assert evidence["anchors"]["record_digests"]


def test_phase_preserves_full_cohort_denominator_and_worker_count(tmp_path,monkeypatch):
    plan=short_plan()
    evidence={"sample":"unit fixture","anchors":"unit fixture"}
    context=a.analysis_context(plan,evidence)
    monkeypatch.setenv("PBS_JOBID","unit-fixture.pbs")
    for key,value in low.native.THREADS.items(): monkeypatch.setenv(key,value)
    monkeypatch.setattr(a,"read_production_plan",lambda root:plan)
    monkeypatch.setattr(a,"completed_phase_evidence",lambda root,p:evidence)
    monkeypatch.setattr(low,"preflight",lambda *args:"unit-native-digest")
    def parallel(worker,jobs,workers):
        assert workers==8 and len(jobs)==768
        return [dict(group=list(job[3]),rows=[dict(available=False)]*4,failed_tasks=[["fixture"]]) for job in jobs]
    monkeypatch.setattr(c,"parallel_map",parallel)
    result=a.run_phase(tmp_path,plan,context,8)
    assert result["workers"]==8 and result["replicates"]==192
    assert result["rows"]==result["unavailable_intervals"]==3072
    assert result["failed_sampling_groups"]==768
    with pytest.raises(ValueError,match="automatic rerun"):
        a.run_phase(tmp_path,plan,context,8)
