"""Full-dimensional fixed subset audit and retained audit failures."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_study as low
import tile_low_noise_trace_audit_run as m


def fixed_plan(capacity=True):
    sampling=low.make_plan(0,0,capacity=False)
    inputs=low.native.platform_inputs()
    return sampling,m.make_plan(sampling,inputs["platform_profile"],inputs["platform_fixture"],
                               capacity=capacity,workers=4,completed_evidence={"fixed":"fixture"})


def test_full_and_fixed_subset_coordinates():
    sampling,cap=fixed_plan()
    _,full=fixed_plan(False)
    assert len(m.groups(cap))==8 and len(m.groups(full))==768
    assert set(m.groups(cap))<=set(m.groups(full))
    assert {g[-1] for g in m.groups(cap)}=={0,1}
    group=m.groups(cap)[0]
    tasks=list(m.tasks_for_group(sampling,group))
    assert len(tasks)==10*16 and all(len(t)==7 for t in tasks)


@pytest.mark.parametrize("workers",[0,97,True,1.5])
def test_invalid_worker_count_rejected(workers):
    sampling=low.make_plan(0,0,capacity=False);inputs=low.native.platform_inputs()
    with pytest.raises(ValueError):
        m.make_plan(sampling,**inputs,capacity=True,workers=workers,completed_evidence={})


def tiny_fixture(tmp_path,monkeypatch):
    original=low.make_plan
    def small(case,target_index,*,capacity):
        value=original(case,target_index,capacity=capacity)
        value["condition"].update(rungs=[.01],coarse=[.01],chains=2,steps=4)
        value["checkpoint_stride"]=2
        return value
    monkeypatch.setattr(low,"make_plan",small)
    sampling=low.make_plan(0,0,capacity=False)
    inputs=low.native.platform_inputs()
    source=tmp_path/"sampling";root=tmp_path/"audit"
    source.mkdir();root.mkdir()
    group=(0,0,0,0,0)
    records=[]
    for task in m.tasks_for_group(sampling,group):
        result=low.sample_task((source,sampling,task));assert result["status"]=="ok"
        records.append({key:result[key] for key in m.REDUCED_KEYS})
    evidence={"sample":{"group_record_digests":{c.task_id(group):c.digest(records)}}}
    plan=m.make_plan(sampling,inputs["platform_profile"],inputs["platform_fixture"],
                     capacity=True,workers=1,completed_evidence=evidence)
    return source,root,sampling,plan,group


def test_actual_group_constructs_problem_once_and_checks_all_tasks(tmp_path,monkeypatch):
    source,root,sampling,plan,group=tiny_fixture(tmp_path,monkeypatch)
    original=m.low.t.build_problem;calls=[]
    def counted(*args,**kwargs):calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(m.low.t,"build_problem",counted)
    result=m.run_group((str(source),str(root),sampling,plan,group))
    assert result["status"]=="ok" and result["planned_tasks"]==2
    assert result["failed_sampling"]==0 and result["redecoded_checkpoints"]==6
    assert len(calls)==1
    report=c.load_artifact(root/"audit/groups"/c.task_id(group),dict(manifest=c.digest(plan),group=list(group)))[1]
    assert len(report["tasks"])==2 and report["all_physical_states_redecoded"] is False
    with pytest.raises(ValueError):m.run_group((str(source),str(root),sampling,plan,group))


@pytest.mark.parametrize("bad",["missing","corrupt","recorded_failure"])
def test_failed_tasks_remain_in_denominator(tmp_path,monkeypatch,bad):
    source,root,sampling,plan,group=tiny_fixture(tmp_path,monkeypatch)
    task=next(m.tasks_for_group(sampling,group));base=source/"traces"/c.task_id(task)
    if bad=="missing":base.with_suffix(".done.json").unlink()
    elif bad=="corrupt":base.with_suffix(".npz").write_bytes(b"bad")
    else:
        identity=dict(manifest=c.digest(sampling),task=list(task));arrays,record=c.load_artifact(base,identity)
        record.update(status="failed",error="fixed sampling failure")
        c.save_artifact(base,identity,{},record)
        rows=[]
        for item in m.tasks_for_group(sampling,group):
            raw=c.load_artifact(source/"traces"/c.task_id(item),dict(manifest=c.digest(sampling),task=list(item)))[1]
            rows.append({key:raw[key] for key in m.REDUCED_KEYS})
        plan["completed_phase_evidence"]["sample"]["group_record_digests"][c.task_id(group)]=c.digest(rows)
    result=m.run_group((str(source),str(root),sampling,plan,group))
    assert result["planned_tasks"]==2
    assert result["status"]==("ok" if bad=="recorded_failure" else "failed")
    assert result["failed_sampling"]==int(bad=="recorded_failure")
    report=c.load_artifact(root/"audit/groups"/c.task_id(group),dict(manifest=c.digest(plan),group=list(group)))[1]
    assert len(report["tasks"])==2


def test_run_rejects_non_pbs_before_reading(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="PBS"):m.run(tmp_path/"audit",tmp_path/"source")


def test_decode_time_input_change_is_retained_as_audit_failure(tmp_path,monkeypatch):
    source,root,sampling,plan,group=tiny_fixture(tmp_path,monkeypatch)
    original=m.audit.audit_task
    def mutate(plan,task,arrays,record,code,problem):
        result=original(plan,task,arrays,record,code,problem)
        target=source/"traces"/(c.task_id(task)+".json")
        target.write_bytes(target.read_bytes()+b" ")
        return result
    monkeypatch.setattr(m.audit,"audit_task",mutate)
    result=m.run_group((source,root,sampling,plan,group))
    assert result["status"]=="failed" and result["failed_audits"]==2


def completed_source(source,sampling):
    c.atomic_json(source/"manifest.json",sampling)
    inputs=low.native.platform_inputs()
    for key,value in inputs.items():c.atomic_json(source/(key+".json"),value)
    for phase in ("sample","anchors"):
        evidence=dict(manifest=c.digest(sampling),pbs_job_id="123.fixture",hostname="fixture-host",profile=inputs["platform_profile"])
        proof=source/f"preflight-{phase}/native_preflight.json"
        c.atomic_json(proof,evidence)
        c.atomic_json(source/f"{phase}-execution-intent.json",dict(evidence,phase=phase))
        rows=[]
        for task in low.tasks(sampling,phase):
            base=source/("traces" if phase=="sample" else "anchors")/c.task_id(task)
            if base.with_suffix(".done.json").exists():
                record=c.load_artifact(base,dict(manifest=c.digest(sampling),task=list(task)))[1]
                rows.append({key:record[key] for key in m.REDUCED_KEYS})
            else:
                rows.append(dict(task=list(task),status="failed",wall_seconds=1.,cpu_seconds=1.,peak_rss_mb=128.))
        c.atomic_json(source/f"{phase}-summary.json",dict(manifest=c.digest(sampling),phase=phase,
            tasks=len(rows),records=rows,failed=sum(r["status"]=="failed" for r in rows),native_preflight_sha256=c.file_hash(proof)))


def test_complete_evidence_run_retains_missing_groups_and_refuses_rerun(tmp_path,monkeypatch):
    source,root,sampling,_,group=tiny_fixture(tmp_path,monkeypatch)
    completed_source(source,sampling)
    plan=m.prepare(root,source,capacity=True,workers=1)
    assert m.read_plan(root,source)[0]==plan and len(m.groups(plan))==8
    monkeypatch.setenv("PBS_JOBID","456.fixture")
    for name,value in m.THREADS.items():monkeypatch.setenv(name,value)
    calls=[]
    def native(plan,**kwargs):calls.append(1);return dict(native_platform_verified=True)
    monkeypatch.setattr(m.audit,"validate_native_environment",native)
    # Native probe is a fixture; real group numerical checks execute serially.
    monkeypatch.setattr(c,"parallel_map",lambda fn,jobs,workers:[fn(job) for job in jobs])
    with pytest.raises(RuntimeError,match="failures"):
        m.run(root,source)
    summary=json.loads((root/"summary.json").read_text())
    assert summary["groups"]==8 and summary["planned_tasks"]==16
    assert summary["failed_audit_groups"]==7 and len(summary["records"])==8
    assert calls==[1]
    with pytest.raises(ValueError,match="existing"):
        m.run(root,source)
    # Changed phase provenance is rejected independently of cached outputs.
    path=source/"sample-execution-intent.json"
    value=json.loads(path.read_text());value["pbs_job_id"]="999.fixture";c.atomic_json(path,value)
    with pytest.raises(ValueError,match="binding"):
        m.read_plan(root,source)


def test_sampling_capacity_cannot_be_used_as_audit_capacity():
    sampling=low.make_plan(0,0,capacity=True);inputs=low.native.platform_inputs()
    with pytest.raises(ValueError,match="production"):
        m.make_plan(sampling,**inputs,capacity=True,workers=1,completed_evidence={})
