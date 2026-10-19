"""Full reference audit scheduling preserves the original sixteen conditions."""
from pathlib import Path
import json
import shutil
import sys

import pytest
for dependency in ("ldpc","bposd","pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_weight_reference_audit_run as run
from test_tile_weight_reference_audit import saved_root


@pytest.fixture(scope="module")
def reference(tmp_path_factory):
    root=tmp_path_factory.mktemp("small-full-reference")
    patch=pytest.MonkeyPatch()
    context,values=saved_root(root,patch)
    yield root,context,values
    patch.undo()


def environment(monkeypatch):
    monkeypatch.setenv("PBS_JOBID","456.fixture")
    for key,value in run.THREADS.items(): monkeypatch.setenv(key,value)


def test_prepare_preserves_full_reference_and_resource_ceiling(tmp_path,reference):
    source,context,_=reference
    plan=run.prepare(tmp_path/"audit",source)
    assert plan["reference_context"]==context
    assert plan["conditions"]==list(range(16)) and plan["workers"]==16
    assert plan["resources"]["measured"] is False
    assert plan["resources"]["requested_nodes"]==1 and plan["resources"]["memory_gb"]==340
    assert run.read_plan(tmp_path/"audit",source)==plan
    with pytest.raises(ValueError,match="new"):
        run.prepare(tmp_path/"audit",source)
    with pytest.raises(ValueError,match="reference root"):
        run.prepare(source/"audit",source)


def test_actual_condition_task_keeps_original_audit_report(tmp_path,reference):
    source,context,_=reference
    plan=run.prepare(tmp_path/"audit",source)
    record=run.audit_task((str(tmp_path/"audit"),str(source),plan,5))
    assert record["status"]=="ok",record
    arrays,raw=c.load_artifact(tmp_path/"audit/conditions/5",dict(manifest=c.digest(plan),condition=5))
    assert not arrays and raw["report"]["context"]==context
    assert record["available_labels"]==record["checked_labels"]==1
    assert record["all_labels_redecoded"] is False and record["raw_artifact_bytes"]>0
    assert record["wall_seconds"]>0
    with pytest.raises(ValueError,match="existing"):
        run.audit_task((str(tmp_path/"audit"),str(source),plan,5))


def test_corrupt_condition_is_retained_as_failed(tmp_path,reference,monkeypatch):
    source,_,_=reference
    plan=run.prepare(tmp_path/"audit",source)
    def failed(root,index): raise ValueError("raw corruption fixture")
    monkeypatch.setattr(run.audit,"audit_saved_condition",failed)
    record=run.audit_task((str(tmp_path/"audit"),str(source),plan,5))
    assert record["status"]=="failed" and "raw corruption" in record["error"]
    assert record["available_labels"] is None and record["checked_labels"] is None


def test_run_requires_pbs(tmp_path,reference,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="qsub"): run.run(tmp_path,reference[0])


def test_all_sixteen_real_audits_are_preserved(tmp_path,reference,monkeypatch):
    source,_,_=reference
    root=tmp_path/"audit"
    run.prepare(root,source)
    environment(monkeypatch)
    def sequential(worker,jobs,workers):
        assert workers==16 and [job[-1] for job in jobs]==list(range(16))
        return [worker(job) for job in jobs]
    monkeypatch.setattr(c,"parallel_map",sequential)
    summary=run.run(root,source)
    assert summary["tasks"]==16 and summary["failed"]==0
    assert [record["condition"] for record in summary["records"]]==list(range(16))
    assert summary["available_labels"]==summary["checked_labels"]==16
    assert len(summary["condition_marker_sha256"])==16
    with pytest.raises(ValueError,match="automatic rerun"): run.run(root,source)


def test_failed_task_still_writes_complete_summary(tmp_path,reference,monkeypatch):
    source,_,_=reference
    root=tmp_path/"audit"
    run.prepare(root,source)
    environment(monkeypatch)
    original=run.audit.audit_saved_condition
    def injected(root,index):
        if index==5: raise ValueError("fixture audit failure")
        return original(root,index)
    monkeypatch.setattr(run.audit,"audit_saved_condition",injected)
    monkeypatch.setattr(c,"parallel_map",lambda worker,jobs,workers:[worker(job) for job in jobs])
    with pytest.raises(RuntimeError,match="failed"):
        run.run(root,source)
    summary=json.loads((root/"summary.json").read_text())
    assert summary["tasks"]==16 and summary["failed"]==1 and len(summary["records"])==16
    assert summary["records"][5]["status"]=="failed"


@pytest.mark.parametrize("change",["plan","source","native"])
def test_changed_binding_rejected(tmp_path,reference,monkeypatch,change):
    source,_,_=reference
    root=tmp_path/"audit"
    run.prepare(root,source)
    if change=="plan":
        plan=json.loads((root/"manifest.json").read_text());plan["workers"]=8
        c.atomic_json(root/"manifest.json",plan)
    elif change=="source": monkeypatch.setattr(run,"source_hashes",lambda:{"changed":"source"})
    else: monkeypatch.setattr(run.audit.driver.native_probe,"probe",lambda fixture:{"changed":True})
    with pytest.raises(ValueError): run.read_plan(root,source)


def test_terminal_binding_error_preserves_every_failed_outcome(tmp_path,reference,monkeypatch):
    source,_,_=reference
    root=tmp_path/"audit"
    run.prepare(root,source)
    environment(monkeypatch)
    original=run.read_plan
    calls=[]
    def changed_after_workers(*args):
        calls.append(1)
        if len(calls)>1: raise ValueError("terminal source change")
        return original(*args)
    monkeypatch.setattr(run,"read_plan",changed_after_workers)
    def fail(root,index): raise ValueError("condition failure")
    monkeypatch.setattr(run.audit,"audit_saved_condition",fail)
    monkeypatch.setattr(c,"parallel_map",lambda worker,jobs,workers:[worker(job) for job in jobs])
    with pytest.raises(RuntimeError,match="binding"):
        run.run(root,source)
    summary=json.loads((root/"summary.json").read_text())
    assert summary["tasks"]==summary["failed"]==16
    assert summary["terminal_binding_valid"] is False and not summary["all_conditions_audited"]
    assert "terminal source change" in summary["phase_failure"]


@pytest.mark.parametrize("change",["audit_source","raw_chunk","condition_summary"])
def test_successful_conditions_remain_recorded_when_evidence_changes_at_phase_end(tmp_path,reference,monkeypatch,change):
    original,_,_=reference
    source=tmp_path/"reference"
    shutil.copytree(original,source)
    root=tmp_path/"audit"
    run.prepare(root,source)
    environment(monkeypatch)
    terminal_checks=[]
    def completed_then_change(worker,jobs,workers):
        records=[worker(job) for job in jobs]
        assert all(record["status"]=="ok" for record in records)
        original_verify=run.audit.verify_unchanged
        def track_terminal(root,hashes,sources):
            if any(name.startswith("chunks/") for name in hashes): terminal_checks.append(hashes)
            return original_verify(root,hashes,sources)
        monkeypatch.setattr(run.audit,"verify_unchanged",track_terminal)
        if change=="audit_source":
            monkeypatch.setattr(run.audit,"source_hashes",lambda:{"changed":"dependency source"})
        else:
            path=source/("chunks/0-0-0.npz" if change=="raw_chunk" else "condition-0.json")
            path.write_bytes(path.read_bytes()+b" ")
        return records
    monkeypatch.setattr(c,"parallel_map",completed_then_change)
    with pytest.raises(RuntimeError,match="binding"):
        run.run(root,source)
    summary=json.loads((root/"summary.json").read_text())
    assert summary["tasks"]==16 and summary["failed"]==0
    assert len(summary["records"])==16 and all(record["status"]=="ok" for record in summary["records"])
    assert summary["terminal_binding_valid"] is False and summary["all_conditions_audited"] is False
    assert summary["phase_failure"] and len(summary["condition_marker_sha256"])==16
    assert len(terminal_checks)==16
