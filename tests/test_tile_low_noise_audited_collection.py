"""Saved artifact joins preserve failures and reject changed provenance."""
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_audited_collection as m
from test_tile_low_noise_trace_audit_resources import saved_capacity


def fixture(tmp_path,monkeypatch):
    source,root,sampling,plan,summary,_=saved_capacity(tmp_path,monkeypatch)
    row=summary["records"][0]
    _,raw=c.load_artifact(root/"audit/groups"/c.task_id(row["group"]),
                         dict(manifest=c.digest(plan),group=row["group"]))
    markers={"sample/"+c.task_id(task["task"]):raw["input_sha256"][str(Path("traces")/(c.task_id(task["task"])+".done.json"))]
             for task in raw["tasks"]}
    analysis=dict(group=row["group"],input_artifact_markers=markers,failed_tasks=[])
    return source,root,sampling,plan,row,analysis


def test_actual_group_and_payload_change(tmp_path,monkeypatch):
    source,root,sampling,plan,row,analysis=fixture(tmp_path,monkeypatch)
    proof=m.Evidence()
    result=m.verify_group(source,root,plan,sampling,row,analysis,proof)
    assert result==dict(tasks=2,failed_sampling=0,redecoded_checkpoints=6)
    proof.finish()
    path=source/"traces"/(c.task_id((*row["group"],0,0))+".npz")
    path.write_bytes(path.read_bytes()+b"changed")
    with pytest.raises(ValueError):
        m.verify_group(source,root,plan,sampling,row,analysis,m.Evidence())
    with pytest.raises(ValueError,match="changed"):
        proof.finish()


@pytest.mark.parametrize("change",["marker","failed","task_count"])
def test_join_rejects_mismatch(tmp_path,monkeypatch,change):
    source,root,sampling,plan,row,analysis=fixture(tmp_path,monkeypatch)
    if change=="marker":analysis["input_artifact_markers"][next(iter(analysis["input_artifact_markers"]))]="bad"
    elif change=="failed":analysis["failed_tasks"]=[[*row["group"],0,0]]
    else:row["planned_tasks"]-=1
    with pytest.raises(ValueError):
        m.verify_group(source,root,plan,sampling,row,analysis,m.Evidence())


def test_collection_iterator_is_fully_consumed(tmp_path,monkeypatch):
    def rows():
        yield {"first":1}
        raise ValueError("iterator terminal check")
    monkeypatch.setattr(m.p,"read_collection",lambda root:({},rows(),{}))
    with pytest.raises(ValueError,match="terminal"):
        m.read_audited_collection(tmp_path/"sample",tmp_path/"audit")


def test_snapshot_detects_change_and_path_escape(tmp_path):
    path=tmp_path/"data.json";c.atomic_json(path,{"x":1})
    proof=m.Evidence();assert proof.read(path)=={"x":1}
    c.atomic_json(path,{"x":2})
    with pytest.raises(ValueError,match="changed"):proof.finish()
    with pytest.raises(ValueError):m.r.path_in(tmp_path,"../escape")


def test_recorded_sampling_failure_kept_and_task_omission_rejected(tmp_path,monkeypatch):
    source,root,sampling,plan,row,analysis=fixture(tmp_path,monkeypatch)
    group=row["group"]
    audit_base=root/"audit/groups"/c.task_id(group)
    _,audited=c.load_artifact(audit_base,dict(manifest=c.digest(plan),group=group))
    task=audited["tasks"][0]["task"]
    base=source/"traces"/c.task_id(task)
    _,record=c.load_artifact(base,dict(manifest=c.digest(sampling),task=task))
    record.update(status="failed",error="precommitted failure fixture")
    c.save_artifact(base,dict(manifest=c.digest(sampling),task=task),{},record)
    for ext in (".done.json",".json",".npz"):
        audited["input_sha256"][str(base.with_suffix(ext).relative_to(source))]=c.file_hash(base.with_suffix(ext))
    analysis["input_artifact_markers"]["sample/"+c.task_id(task)]=c.file_hash(base.with_suffix(".done.json"))
    analysis["failed_tasks"]=[task]
    audited["tasks"][0].update(sampling_status="failed",result=dict(task=task,status="failed",redecoded_checkpoints=0,
        recorded_failure=record["error"],all_physical_states_redecoded=False))
    audited.update(failed_sampling=1,redecoded_checkpoints=3)
    reduced=[]
    for item in audited["tasks"]:
        raw=json.loads((source/"traces"/(c.task_id(item["task"])+".json")).read_text())
        reduced.append({key:raw[key] for key in m.r.REDUCED_KEYS})
    plan["completed_phase_evidence"]["sample"]["group_record_digests"][c.task_id(group)]=c.digest(reduced)
    identity=dict(manifest=c.digest(plan),group=group)
    c.save_artifact(audit_base,identity,{},audited)
    row.update(failed_sampling=1,redecoded_checkpoints=3,audit_marker_sha256=c.file_hash(audit_base.with_suffix(".done.json")))
    c.save_artifact(root/"measurements"/c.task_id(group),identity,{},row)
    result=m.verify_group(source,root,plan,sampling,row,analysis,m.Evidence())
    assert result==dict(tasks=2,failed_sampling=1,redecoded_checkpoints=3)
    audited["tasks"].pop()
    c.save_artifact(audit_base,identity,{},audited)
    row["audit_marker_sha256"]=c.file_hash(audit_base.with_suffix(".done.json"))
    c.save_artifact(root/"measurements"/c.task_id(group),identity,{},row)
    with pytest.raises(ValueError,match="task census"):
        m.verify_group(source,root,plan,sampling,row,analysis,m.Evidence())


def test_real_collection_reader_then_capacity_rejection(tmp_path,monkeypatch):
    from test_tile_low_noise_analysis_partitions import collection_fixture
    wrapper=collection_fixture(monkeypatch)
    m.p.collect(tmp_path)
    monkeypatch.setattr(m.r,"read_plan",lambda *args:({"purpose":"low_noise_trace_audit_capacity"},wrapper["production"]))
    with pytest.raises(ValueError,match="full audit"):
        m.read_audited_collection(tmp_path,tmp_path.parent/"audit")
    summary=tmp_path/"partition-collection/summary.json"
    value=json.loads(summary.read_text());value["rows"]-=1;c.atomic_json(summary,value)
    with pytest.raises(ValueError,match="denominator"):
        m.read_audited_collection(tmp_path,tmp_path.parent/"audit")


def test_full_join_control_flow_with_explicit_io_and_group_fixtures(tmp_path,monkeypatch):
    # Group payload checks and the real collection iterator are tested separately.
    # This test exercises the 768-group orchestration, not a real full census.
    source=(tmp_path/"source").resolve();root=(tmp_path/"audit").resolve()
    sampling=dict(case=0,target_index=0,replicates=192)
    plan=dict(purpose="low_noise_trace_audit_full",case=0,target_index=0,replicates=192,workers=8,
              input_sha256={"manifest.json":"fixture"},completed_phase_evidence={"anchors":{"record_digests":{}}})
    group_list=m.r.groups(plan)
    anchors={c.task_id((0,0,0,0,rep,0,0)):dict(task=[0,0,0,0,rep,0,0],status="failed") for rep in range(192)}
    plan["completed_phase_evidence"]["anchors"]["record_digests"]={name:c.digest(value) for name,value in anchors.items()}
    identity=dict(manifest=c.digest(plan),sampling_manifest=c.digest(sampling),workers=8,pbs_job_id="123.fixture",hostname="fixture")
    native=dict(native_platform_verified=True,fixture=True)
    summary=dict(manifest=c.digest(plan),groups=768,records=[dict(group=list(group)) for group in group_list],
                 failed_audit_groups=0,input_changes=[],context_error=None,native_platform_verified=True,
                 all_physical_states_redecoded=False,native_preflight_sha256="fixture",planned_tasks=1536,failed_sampling=768)
    ledger=dict(manifest=c.digest(plan),command=["qsub",str(root/"trace-audit.sh")],script_sha256="fixture")
    values={"summary.json":summary,"execution-intent.json":identity,"native_preflight.json":dict(identity,evidence=native),
            "platform_profile.json":{},"platform_fixture.json":{},"submission-intent.json":ledger,
            "submission.json":dict(ledger,job_id="123.fixture")}
    calls=dict(iterator=0,group=0,finish=0)
    class FixtureEvidence:
        def __init__(self,*args):self.hashes={};self.targets={}
        def track(self,path):
            self.hashes[str(path)]="fixture";self.targets[str(path)]=str(path);return "fixture"
        def read(self,path):self.track(path);return values[Path(path).name]
        def artifact(self,base,identity):return {},anchors[base.name]
        def finish(self):calls["finish"]+=1
    def collection(_):
        def iterator():
            for group in group_list:yield dict(group=list(group),available=False)
            calls["iterator"]+=1
        return sampling,iterator(),dict(rows=768)
    def group_read(_,wrapper,group):
        name=c.task_id((0,0,0,0,group[4],0,0))
        return dict(group=list(group),input_artifact_markers={"anchors/"+name:"fixture"}),"fixture"
    def verify(*args):
        calls["group"]+=1
        return dict(tasks=2,failed_sampling=1,redecoded_checkpoints=3)
    monkeypatch.setattr(m,"Evidence",FixtureEvidence)
    monkeypatch.setattr(m.r,"read_plan",lambda *args:(plan,sampling))
    monkeypatch.setattr(m.r.audit,"validate_native_environment",lambda *args,**kwargs:native)
    monkeypatch.setattr(m.p,"read_collection",collection)
    monkeypatch.setattr(m.p,"read_plan",lambda *args:dict(resources=dict(partitions=[dict(index=0)])))
    monkeypatch.setattr(m.p,"read_group",group_read)
    monkeypatch.setattr(m,"verify_group",verify)
    actual,rows,evidence=m.read_audited_collection(source,root)
    assert actual==sampling and len(rows)==768 and calls==dict(iterator=2,group=768,finish=1)
    assert evidence["planned_tasks"]==1536 and evidence["failed_sampling"]==768 and evidence["anchors"]==192
    assert evidence["analysis_trace_markers_matched"] and evidence["current_trace_payloads_rehashed"]
    assert not evidence["reference_audited"] and not evidence["anchor_mc_replayed"] and not evidence["all_physical_states_redecoded"]
    summary["failed_sampling"]-=1
    with pytest.raises(ValueError,match="denominator"):
        m.read_audited_collection(source,root)


def test_symlink_escape_and_retarget_detected(tmp_path):
    inside=tmp_path/"inside";inside.mkdir()
    first=inside/"first";first.write_text("same")
    second=inside/"second";second.write_text("same")
    outside=tmp_path/"outside";outside.write_text("same")
    link=inside/"link"
    try:link.symlink_to(first)
    except OSError:pytest.skip("OS does not grant symlink creation")
    proof=m.Evidence((inside,));proof.track(link)
    link.unlink();link.symlink_to(second)
    with pytest.raises(ValueError,match="changed"):proof.finish()
    link.unlink();link.symlink_to(outside)
    with pytest.raises(ValueError,match="escapes"):m.Evidence((inside,)).track(link)
