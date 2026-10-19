"""Reference raw-byte provenance and precommitted checkpoint re-decoding."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_weight_reference as r
import audit_tile_weight_reference as a


def make_chunks(root,case=0):
    plan=r.make_plan([dict(case=case,physical_decoder_prior=.01,layers=[
        dict(w=0,mode="enum",trials=1),dict(w=1,mode="mc",trials=20)])],
        pilot_audit_digest="a"*64,platform_profile_digest="b"*64,chunk_size=20)
    records=[];raw=[];loaded=[]
    for task in r.tasks(plan,0):
        record=r.run_chunk((root,plan,task));assert record["status"]=="ok"
        base=root/"chunks"/c.task_id(task)
        records.append(record)
        raw.append({ext:base.with_suffix(ext).read_bytes() for ext in (".done.json",".json",".npz")})
        loaded.append(c.load_artifact(base,dict(manifest=c.digest(plan),task=list(task))))
    return plan,raw,records,r.aggregate_condition(plan,0,loaded)


@pytest.mark.parametrize("case",range(4))
def test_actual_small_reference_audit_first16_and_last(tmp_path,case):
    plan,raw,records,summary=make_chunks(tmp_path,case)
    result=a.audit_condition(plan,0,iter(raw),summary,records)
    assert result["condition"]==summary
    assert result["checked_labels"]==18 and result["available_labels"]==21
    assert result["all_labels_redecoded"] is False
    assert result["raw_draws_regenerated"] and result["raw_artifact_hashes_verified"]
    assert result["chunk_checks"][1]["checked_indices"]==list(range(16))+[19]


def rewrite(raw,record=None,arrays=None):
    raw=dict(raw)
    if record is not None:raw[".json"]=c.canonical(record)
    if arrays is not None:
        stream=io.BytesIO();np.savez_compressed(stream,**arrays);raw[".npz"]=stream.getvalue()
    marker=json.loads(raw[".done.json"])
    marker["sha256"]={ext:hashlib.sha256(raw[ext]).hexdigest() for ext in (".json",".npz")}
    raw[".done.json"]=c.canonical(marker)
    return raw


def test_corrupt_payload_missing_marker_and_input_count_rejected(tmp_path):
    plan,raw,records,summary=make_chunks(tmp_path)
    changed=deepcopy(raw);changed[1][".json"]+=b" "
    for items in (changed,raw[:-1],raw+raw[-1:],list(reversed(raw))):
        with pytest.raises(ValueError):a.audit_condition(plan,0,items,summary,records)
    changed=deepcopy(raw);del changed[0][".done.json"]
    with pytest.raises(ValueError):a.audit_condition(plan,0,changed,summary,records)


def test_last_label_tampering_is_redecoded_even_with_rehashed_artifact(tmp_path):
    plan,raw,records,summary=make_chunks(tmp_path)
    with np.load(io.BytesIO(raw[1][".npz"])) as archive:arrays={k:archive[k] for k in archive.files}
    arrays["failure"][-1]=not arrays["failure"][-1]
    records[1]=dict(records[1],failures=int(arrays["failure"].sum()))
    raw[1]=rewrite(raw[1],records[1],arrays)
    with pytest.raises(ValueError,match="label"):
        a.audit_condition(plan,0,raw,summary,records)


def test_recorded_failure_retained_without_redecoding(tmp_path):
    plan,raw,records,_=make_chunks(tmp_path)
    records[1]=dict(records[1],status="failed",error="fixed failure")
    raw[1]=rewrite(raw[1],records[1],{})
    with np.load(io.BytesIO(raw[0][".npz"])) as archive:arrays={k:archive[k] for k in archive.files}
    summary=r.aggregate_condition(plan,0,[(arrays,records[0]),({},records[1])])
    report=a.audit_condition(plan,0,raw,summary,records)
    assert report["condition"]["planned_trials"]==21
    assert report["condition"]["failed_chunks"]==[[0,1,0]]
    assert report["condition"]["reference"] is None
    assert report["checked_labels"]==1 and report["available_labels"]==1


def test_rehashed_changed_draw_is_not_accepted(tmp_path):
    plan,raw,records,summary=make_chunks(tmp_path)
    with np.load(io.BytesIO(raw[1][".npz"])) as archive:arrays={k:archive[k] for k in archive.files}
    arrays["states"][0]=np.roll(arrays["states"][0],1)
    raw[1]=rewrite(raw[1],arrays=arrays)
    with pytest.raises(ValueError,match="raw reference states"):
        a.audit_condition(plan,0,raw,summary,records)


def saved_root(root,monkeypatch):
    # Input metadata and native profiles are fixtures, physical chunk tasks are real.
    from test_tile_weight_reference_driver import inputs
    values=inputs()
    context=a.driver.make_context(*values)
    for key,value in zip(a.driver.INPUTS,values):c.atomic_json(root/(key+".json"),value)
    c.atomic_json(root/"manifest.json",context)
    evidence=dict(manifest=c.digest(context),profile=values[3],hostname="fixture-host",pbs_job_id="123.fixture",wall_seconds=.1)
    c.atomic_json(root/"native_preflight_run.json",evidence)
    script=root/"weight_reference.sh";script.write_text("fixture PBS script")
    intent=dict(manifest=c.digest(context),script_sha256=c.file_hash(script),command=["qsub",str(script)])
    c.atomic_json(root/"submission_intent.json",intent)
    c.atomic_json(root/"submission.json",dict(intent,job_id="123.fixture"))
    plan=context["reference"];records=[];summaries=[]
    for index in range(16):
        loaded=[]
        for task in r.tasks(plan,index):
            record=r.run_chunk((root,plan,task));assert record["status"]=="ok"
            records.append(record)
            loaded.append(c.load_artifact(root/"chunks"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task))))
        summary=r.aggregate_condition(plan,index,loaded)
        summaries.append(summary)
        c.atomic_json(root/f"condition-{index}.json",summary)
    digest=c.file_hash(root/"native_preflight_run.json")
    c.atomic_json(root/"chunks_summary.json",dict(manifest=c.digest(context),native_preflight_sha256=digest,
                  tasks=len(records),failed=0,records=records,wall_seconds=.1))
    c.atomic_json(root/"summary.json",dict(manifest=c.digest(context),native_preflight_sha256=digest,
        conditions=16,unavailable=0,records=summaries,sampling_wall_seconds=.1,aggregation_wall_seconds=.1,phase_wall_seconds=.2))
    monkeypatch.setattr(a.driver.native_probe,"probe",lambda fixture:values[3])
    def guard(expected,actual):
        if expected!=actual:raise ValueError("native fixture mismatch")
    monkeypatch.setattr(a.driver.trace_audit,"validate_platform",guard)
    return context,values


def test_saved_condition_native_pbs_summary_binding_and_corruptions(tmp_path,monkeypatch):
    context,values=saved_root(tmp_path,monkeypatch)
    report=a.audit_saved_condition(tmp_path,5)
    assert report["context"]==context and report["context_digest"]==c.digest(context)
    assert report["condition"]["case"]==1 and report["condition"]["physical_decoder_prior"]==.01
    assert report["native_platform_verified"] and report["raw_reference_audited"]
    assert report["checked_labels"]==1 and report["all_labels_redecoded"] is False
    assert report["reference_plan_digest"]==c.digest(context["reference"])
    assert "condition-5.json" in report["input_sha256"]
    changes=[("submission.json",lambda x:x.update(job_id="999.fixture")),
             ("summary.json",lambda x:x.update(native_preflight_sha256="changed")),
             ("condition-5.json",lambda x:x.update(available=False)),
             ("chunks_summary.json",lambda x:x["records"][5].update(failures=1)),
             ("chunks_summary.json",lambda x:x["records"].pop()),
             ("manifest.json",lambda x:x["reference"].update(seed_stage=131)),
             ("platform_fixture.json",lambda x:x.update(changed=True))]
    for name,mutate in changes:
        path=tmp_path/name;original=path.read_bytes();value=json.loads(original)
        mutate(value);c.atomic_json(path,value)
        with pytest.raises(ValueError):a.audit_saved_condition(tmp_path,5)
        path.write_bytes(original)
    original_audit=a.audit_condition
    changed_path=tmp_path/"chunks/5-0-0.npz"
    original_payload=changed_path.read_bytes()
    def change_after_read(*args,**kwargs):
        result=original_audit(*args,**kwargs)
        changed_path.write_bytes(original_payload+b"changed after payload read")
        return result
    monkeypatch.setattr(a,"audit_condition",change_after_read)
    with pytest.raises(ValueError,match="changed during audit"):
        a.audit_saved_condition(tmp_path,5)
    changed_path.write_bytes(original_payload)
    monkeypatch.setattr(a,"audit_condition",original_audit)
    monkeypatch.setattr(a.driver.native_probe,"probe",lambda fixture:{"different":"platform"})
    with pytest.raises(ValueError,match="native"):a.audit_saved_condition(tmp_path,5)
