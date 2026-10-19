"""Fixed audit cohorts, native provenance and honest resource measurements."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_bar_study as b
import tile_trace_audit_run as r


def inputs():
    fixture={"selected":"checkpoint"}
    profile={"fixture":c.digest(fixture),"native_ldpc_sha256":{"binary":"hash"}}
    return b.make_plan(),profile,fixture


def test_cohorts_fixed_before_outcomes_and_native_binding():
    sampling,profile,fixture=inputs()
    cap=r.make_plan(sampling,3,profile,fixture,capacity=True)
    full=r.make_plan(sampling,3,profile,fixture,capacity=False)
    assert len(r.groups(cap))==96 and len(r.groups(full))==768
    assert set(g[3] for g in r.groups(cap))==set(range(24))
    assert set((g[1],g[2]) for g in r.groups(cap))=={(0,0),(0,1),(1,0),(1,1)}
    assert set(r.groups(cap))<set(r.groups(full))
    for changed in (dict(profile,fixture="wrong"),dict(profile,native_ldpc_sha256={})):
        with pytest.raises(ValueError):
            r.make_plan(sampling,3,changed,fixture,capacity=True)
    with pytest.raises(ValueError):
        r.make_plan(dict(sampling,replicates=191),3,profile,fixture,capacity=True)


def test_measured_real_group_and_corrupt_input_are_distinct(tmp_path,monkeypatch):
    sampling,profile,fixture=inputs()
    sampling["cases"][0].update(steps=8,rungs=[.1],chains=1)
    monkeypatch.setattr(b,"make_plan",lambda:sampling)
    context=r.make_plan(sampling,0,profile,fixture,capacity=True)
    source=tmp_path/"source"
    group=(0,0,1,0)
    b.sample_task((str(source),sampling,(*group,0,0)))
    monkeypatch.setattr(c,"peak_rss_mb",lambda:100.)
    result=r.run_group((source,tmp_path/"good",sampling,context,group))
    assert result["status"]=="ok" and result["tasks"]==1
    assert result["redecoded_checkpoints"]==2 and result["failed_sampling"]==0
    assert result["wall_seconds"]>0 and result["cpu_seconds"]>=0
    assert result["peak_rss_mb"]==100. and result["audit_marker_sha256"]
    (source/"traces"/(c.task_id((*group,0,0))+".npz")).write_bytes(b"broken")
    failed=r.run_group((source,tmp_path/"bad",sampling,context,group))
    assert failed["status"]=="failed" and failed["error"] and failed["traceback"]
    saved=c.load_artifact(tmp_path/"bad/measurements"/c.task_id(group),dict(manifest=c.digest(context),group=list(group)))
    assert saved[1]==failed


def prepare(root,monkeypatch):
    sampling,profile,fixture=inputs()
    context=r.make_plan(sampling,3,profile,fixture,capacity=True)
    for name,value in (("sampling_manifest",sampling),("platform_profile",profile),("platform_fixture",fixture),("manifest",context)):
        c.atomic_json(root/(name+".json"),value)
    source=root.parent/"source"
    c.atomic_json(source/"manifest.json",sampling)
    return source,context,profile


def test_saved_input_tamper_rejected(tmp_path,monkeypatch):
    source,context,_=prepare(tmp_path/"run",monkeypatch)
    assert r.read_plan(tmp_path/"run",source)[0]==context
    c.atomic_json(tmp_path/"run/platform_fixture.json",{"different":True})
    with pytest.raises(ValueError):
        r.read_plan(tmp_path/"run",source)


def test_native_mismatch_stops_before_workers_and_preserves_intent(tmp_path,monkeypatch):
    root=tmp_path/"run"
    source,context,profile=prepare(root,monkeypatch)
    monkeypatch.setenv("PBS_JOBID","123.server")
    for key in r.THREADS:
        monkeypatch.setenv(key,"1")
    monkeypatch.setattr(r.a.platform_probe,"probe",lambda fixture:dict(profile,native_ldpc_sha256={"different":"binary"}))
    monkeypatch.setattr(c,"parallel_map",lambda *args:pytest.fail("workers must not start"))
    with pytest.raises(ValueError,match="native decoder"):
        r.run(root,source)
    assert (root/"execution_intent.json").exists()
    with pytest.raises(ValueError,match="existing execution"):
        r.run(root,source)


def test_native_evidence_bound_to_summary(tmp_path,monkeypatch):
    root=tmp_path/"run"
    source,context,profile=prepare(root,monkeypatch)
    monkeypatch.setenv("PBS_JOBID","123.server")
    for key in r.THREADS:
        monkeypatch.setenv(key,"1")
    monkeypatch.setattr(r.a.platform_probe,"probe",lambda fixture:profile)
    monkeypatch.setattr(r.a,"validate_platform",lambda expected,actual:None)
    rows=[dict(group=list(g),status="ok",tasks=40,failed_sampling=0,redecoded_checkpoints=760,
               wall_seconds=1.,cpu_seconds=.5,peak_rss_mb=100.,audit_marker_sha256="recorded") for g in r.groups(context)]
    monkeypatch.setattr(c,"parallel_map",lambda *args:list(reversed(rows)))
    result=r.run(root,source)
    assert result["native_preflight_sha256"]==c.file_hash(root/"native_preflight.json")
    observed=json.loads((root/"native_preflight.json").read_text())
    assert observed["pbs_job_id"]=="123.server" and observed["hostname"]
    assert observed["profile"]==profile and observed["manifest"]==c.digest(context)
    assert result["groups"]==96 and result["failed_audits"]==0
    assert [row["group"] for row in result["records"]]==[list(g) for g in r.groups(context)]


def test_run_requires_qsub_before_writes(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="qsub"):
        r.run(tmp_path,tmp_path)
    assert not list(tmp_path.iterdir())
