"""Resource evidence and PBS submission guards for numerical trace audits."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_bar_study as b
import tile_trace_audit_run as r
import submit_tile_trace_audit as s


@pytest.fixture
def evidence():
    sampling=b.make_plan()
    fixture={"fixed":True}
    profile=dict(fixture=c.digest(fixture),native_ldpc_sha256={"binary":"hash"})
    cap=r.make_plan(sampling,3,profile,fixture,capacity=True)
    full=r.make_plan(sampling,3,profile,fixture,capacity=False)
    rows=[dict(group=list(g),status="ok",tasks=40,failed_sampling=0,redecoded_checkpoints=760,
               wall_seconds=10.,cpu_seconds=8.,peak_rss_mb=100.) for g in r.groups(cap)]
    summary=dict(manifest=c.digest(cap),groups=96,failed_audits=0,phase_wall_seconds=20.,records=rows,
                 native_preflight_sha256="observed-profile")
    return full,cap,summary


def test_measured_resource_extrapolation_and_stratum_max(evidence):
    full,cap,data=evidence
    resource=s.resource_plan(full,cap,data)
    assert resource["predicted_phase_seconds"]==160.
    assert resource["wall_seconds"]==1800 and resource["memory_gb"]==32
    data["records"][0]["wall_seconds"]=100.
    assert s.resource_plan(full,cap,data)["predicted_phase_seconds"]==260.


@pytest.mark.parametrize("mutation",["missing","duplicate","failed","nan","rss","case","native","phase","limit"])
def test_invalid_or_incomplete_measurement_refused(evidence,mutation):
    full,cap,data=deepcopy(evidence)
    if mutation=="missing": data["records"].pop()
    elif mutation=="duplicate": data["records"][-1]=data["records"][0]
    elif mutation=="failed": data["records"][0]["status"]="failed"
    elif mutation=="nan": data["records"][0]["wall_seconds"]=float("nan")
    elif mutation=="rss": data["records"][0]["peak_rss_mb"]=None
    elif mutation=="case": full["case"]=0
    elif mutation=="native": data["native_preflight_sha256"]=""
    elif mutation=="phase": data["phase_wall_seconds"]=0
    elif mutation=="limit": data["phase_wall_seconds"]=100000.
    with pytest.raises(ValueError): s.resource_plan(full,cap,data)


def test_failed_sampling_is_not_failed_audit(evidence):
    full,cap,data=evidence
    data["records"][0]["failed_sampling"]=1
    assert s.resource_plan(full,cap,data)["requested_nodes"]==1


def setup_submit(tmp_path,monkeypatch,evidence):
    _,cap,_=evidence
    root=tmp_path/"run"
    root.mkdir()
    monkeypatch.setattr(r,"read_plan",lambda root,source:(cap,{}))
    monkeypatch.setattr(s,"check_source_complete",lambda source,case,runner,execute:None)
    return root,dict(bundle=tmp_path,root=root,source=tmp_path/"source",execute=True,
                    controller_query=lambda:[],active_query=lambda:{},runner=lambda *a,**kw:SimpleNamespace(stdout="123.server\n"))


def test_dry_run_has_no_submission_intent(tmp_path,monkeypatch,evidence):
    root,args=setup_submit(tmp_path,monkeypatch,evidence)
    args.update(execute=False,runner=lambda *a,**kw:pytest.fail("no external call"))
    out=s.submit(**args)
    assert out["job_id"]=="dry-run" and not (root/"submission_intent.json").exists()
    assert "#PBS -l select=1:ncpus=96:mem=32gb" in (root/"audit.sh").read_text()


@pytest.mark.parametrize("block",["controller","nodes"])
def test_slot_guards(tmp_path,monkeypatch,evidence,block):
    root,args=setup_submit(tmp_path,monkeypatch,evidence)
    args["runner"]=lambda *a,**kw:pytest.fail("no qsub")
    if block=="controller":args["controller_query"]=lambda:["live"]
    else:
        args["active_query"]=lambda:{"running":{"Resource_List":{"select":"2:ncpus=96:mem=32gb"}}}
    with pytest.raises(ValueError):s.submit(**args)
    assert not (root/"submission_intent.json").exists()


def test_qsub_response_and_ambiguous_intent(tmp_path,monkeypatch,evidence):
    root,args=setup_submit(tmp_path,monkeypatch,evidence)
    calls=[]
    def runner(command,**kwargs):
        assert (root/"submission_intent.json").exists()
        calls.append(command)
        return SimpleNamespace(stdout="ambiguous output")
    args["runner"]=runner
    with pytest.raises(RuntimeError):s.submit(**args)
    with pytest.raises(ValueError,match="existing submission"):s.submit(**args)
    assert len(calls)==1 and calls[0][0]=="qsub"


def test_successful_submission_receipt(tmp_path,monkeypatch,evidence):
    root,args=setup_submit(tmp_path,monkeypatch,evidence)
    result=s.submit(**args)
    assert result["job_id"]=="123.server"
    assert json.loads((root/"submission.json").read_text())==result
    with pytest.raises(ValueError,match="existing submission"):s.submit(**args)


def test_measured_capacity_validates_persisted_evidence(tmp_path,monkeypatch,evidence):
    full,cap,data=deepcopy(evidence)
    monkeypatch.setattr(r,"read_plan",lambda root,source:(cap,{}))
    monkeypatch.setattr(r.a,"validate_platform",lambda expected,actual:None)
    c.atomic_json(tmp_path/"platform_profile.json",{})
    c.atomic_json(tmp_path/"native_preflight.json",dict(manifest=c.digest(cap),pbs_job_id="123.server",profile={}))
    data["native_preflight_sha256"]=c.file_hash(tmp_path/"native_preflight.json")
    for row in data["records"]:
        group=row["group"]
        audit=tmp_path/"audit/groups"/c.task_id(group)
        c.save_artifact(audit,dict(audit=c.digest(cap),group=group),{},dict(group=group))
        row["audit_marker_sha256"]=c.file_hash(audit.with_suffix(".done.json"))
        c.save_artifact(tmp_path/"measurements"/c.task_id(group),dict(manifest=c.digest(cap),group=group),{},row)
    c.atomic_json(tmp_path/"summary.json",data)
    assert s.measured_capacity(tmp_path,tmp_path,full)["wall_seconds"]==1800
    first=tmp_path/"audit/groups"/c.task_id(data["records"][0]["group"])
    first.with_suffix(".json").write_bytes(b"changed audit content")
    with pytest.raises(ValueError):s.measured_capacity(tmp_path,tmp_path,full)


def test_active_sampling_job_refused_before_qsub(tmp_path,monkeypatch):
    for name,value in (("manifest",{}),("sample-3",{}),("anchors-3",{}),("submission-3",{"job_id":"111.server"})):
        c.atomic_json(tmp_path/(name+".json"),value)
    monkeypatch.setattr(s,"check_completed_case",lambda *args:None)
    commands=[]
    def runner(command,**kwargs):
        commands.append(command)
        return SimpleNamespace(stdout=json.dumps({"Jobs":{"111.server":{"job_state":"R"}}}))
    with pytest.raises(ValueError,match="not terminal"):
        s.check_source_complete(tmp_path,3,runner,True)
    assert commands==[["qstat","-x","-f","-F","json","111.server"]]
