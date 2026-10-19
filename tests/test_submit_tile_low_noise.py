"""Measured low-noise budgets and one-shot, two-node qsub submission."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_study as m
import submit_tile_low_noise as s


def plans():
    return m.make_plan(0,0,capacity=False),m.make_plan(0,0,capacity=True)


def measurement(cap):
    result={}
    for phase in ("sample","anchors"):
        records=[dict(task=list(task),status="ok",wall_seconds=1.,cpu_seconds=.9,peak_rss_mb=128.)
                 for task in m.tasks(cap,phase)]
        result[phase]=dict(manifest=c.digest(cap),phase=phase,tasks=len(records),failed=0,records=records,
                           phase_wall_seconds=2.,native_preflight_sha256="a"*64)
    return result


def save_plan(root,capacity=True):
    root.mkdir(parents=True,exist_ok=True)
    plan=m.make_plan(0,0,capacity=capacity)
    c.atomic_json(root/"manifest.json",plan)
    for key,value in m.native.platform_inputs().items(): c.atomic_json(root/(key+".json"),value)
    return plan


def test_resource_extrapolation_includes_every_stratum_and_phase():
    prod,cap=plans()
    result=s.resource_plan(prod,cap,measurement(cap))
    # 80 capacity samples versus 122880 production samples; 2 versus 192 anchors.
    assert result["predicted_phase_seconds"]=={"sample":3072.,"anchors":192.}
    assert result["wall_seconds"]==7200 and result["memory_gb"]==32
    assert result["requested_nodes"]==1 and result["max_nodes"]==2
    assert s.capacity_resources()["wall_seconds"]==86400


@pytest.mark.parametrize("change",[
    lambda d:d["sample"]["records"].pop(),
    lambda d:d["sample"]["records"][0].update(status="failed"),
    lambda d:d["sample"]["records"][0].update(peak_rss_mb=None),
    lambda d:d["sample"]["records"][0].update(cpu_seconds=float("nan")),
    lambda d:d["sample"].update(phase_wall_seconds=100000),
    lambda d:d["sample"]["records"][0].update(peak_rss_mb=10000),
    lambda d:d["anchors"].update(failed=1),
])
def test_incomplete_invalid_or_excessive_measurements_rejected(change):
    prod,cap=plans();data=measurement(cap);change(data)
    with pytest.raises(ValueError):s.resource_plan(prod,cap,data)


def test_different_target_or_source_cannot_supply_capacity():
    prod,cap=plans()
    for key,value in (("target_index",1),("runtime",{})):
        changed=deepcopy(prod);changed[key]=value
        with pytest.raises(ValueError,match="differ"):
            s.resource_plan(changed,cap,measurement(cap))


def test_submit_guards_nodes_controller_and_writes_intent_before_qsub(tmp_path):
    bundle=tmp_path/"bundle";root=bundle/"runs/capacity";save_plan(root)
    dry=s.submit(bundle,root)
    assert dry["job_id"]=="dry-run"
    script=(root/"low-noise.sh").read_text()
    assert "qsub" in script and "mem=340gb" in script and "24:00:00" in script
    assert script.index(" anchors ")<script.index(" sample ")
    calls=[]
    def runner(cmd,**kwargs):
        assert cmd[0]=="qsub" and (root/"submission-intent.json").exists()
        assert (bundle.parent/"tile-low-noise-submission.lock").exists()
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd,0,stdout="456.cluster\n")
    for controller,jobs in ((["live"],{}),([],{"1":{"Resource_List":{"select":"1:ncpus=96"}},"2":{"Resource_List":{"select":"1:ncpus=96"}}})):
        with pytest.raises(ValueError):s.submit(bundle,root,execute=True,controller_query=lambda:controller,active_query=lambda:jobs,runner=runner)
    assert not calls
    result=s.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert result["job_id"]=="456.cluster"
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()
    with pytest.raises(ValueError):s.submit(bundle,root,execute=True)
    assert len(calls)==1


@pytest.mark.parametrize("timeout",[True,False])
def test_ambiguous_response_keeps_root_intent_and_global_lock(tmp_path,timeout):
    bundle=tmp_path/"bundle";root=bundle/"runs/capacity";save_plan(root)
    def runner(cmd,**kwargs):
        if timeout:raise subprocess.TimeoutExpired(cmd,30)
        return subprocess.CompletedProcess(cmd,0,stdout="unknown")
    with pytest.raises((subprocess.TimeoutExpired,RuntimeError)):
        s.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert (root/"submission-intent.json").exists()
    assert (bundle.parent/"tile-low-noise-submission.lock").exists()
    with pytest.raises(ValueError):s.submit(bundle,root)


def test_shared_lock_rejects_competing_root_before_qsub(tmp_path):
    bundle=tmp_path/"bundle";root=bundle/"runs/capacity";save_plan(root)
    (tmp_path/"tile-low-noise-submission.lock").write_text("busy")
    with pytest.raises(FileExistsError):
        s.submit(bundle,root,execute=True,runner=lambda *a,**k:pytest.fail("competing qsub"))


@pytest.mark.parametrize("existing",["sample-execution-intent.json","anchors-execution-intent.json","sample-summary.json","anchors-summary.json","traces","anchors"])
def test_existing_output_rejected(tmp_path,existing):
    save_plan(tmp_path)
    if existing in ("traces","anchors"):(tmp_path/existing).mkdir()
    else:(tmp_path/existing).write_text("{}")
    with pytest.raises(ValueError):s.submit(tmp_path,tmp_path)


def test_main_requires_capacity_and_native_inputs_are_bound(tmp_path):
    save_plan(tmp_path,False)
    with pytest.raises(ValueError,match="capacity"):s.submit(tmp_path,tmp_path)
    (tmp_path/"platform_fixture.json").write_text("{}")
    with pytest.raises(ValueError,match="native"):s.read_plan(tmp_path)


def test_actual_small_capacity_artifacts_are_bound_to_metadata_and_native_evidence(tmp_path,monkeypatch):
    original=m.make_plan
    def small(case,target_index,*,capacity):
        plan=original(case,target_index,capacity=capacity)
        plan["condition"]["steps"]=4
        plan["anchor_trials"]=4
        return plan
    monkeypatch.setattr(m,"make_plan",small)
    monkeypatch.setattr(c,"peak_rss_mb",lambda:128.)
    cap=save_plan(tmp_path)
    prod=m.make_plan(0,0,capacity=False)
    native_profile=m.native.platform_inputs()["platform_profile"]
    for phase in ("sample","anchors"):
        records=[]
        for task in m.tasks(cap,phase):
            record=(m.sample_task if phase=="sample" else m.anchor_task)((str(tmp_path),cap,task))
            assert record["status"]=="ok",record
            # Clock/RSS and compute-node provenance are fixtures; physical tasks are real.
            record["cpu_seconds"]=max(1e-6,record["cpu_seconds"])
            base=tmp_path/("traces" if phase=="sample" else "anchors")/c.task_id(task)
            identity=dict(manifest=c.digest(cap),task=list(task))
            arrays,_=c.load_artifact(base,identity)
            c.save_artifact(base,identity,arrays,record)
            records.append({key:record[key] for key in ("task","status","wall_seconds","cpu_seconds","peak_rss_mb")} if phase=="sample" else record)
        evidence=dict(manifest=c.digest(cap),pbs_job_id="1.fixture",hostname="compute-fixture",profile=native_profile)
        path=tmp_path/f"preflight-{phase}"/"native_preflight.json"
        c.atomic_json(path,evidence)
        c.atomic_json(tmp_path/f"{phase}-execution-intent.json",dict(evidence,phase=phase))
        summary=dict(manifest=c.digest(cap),phase=phase,tasks=len(records),failed=0,records=records,
                     phase_wall_seconds=1.,native_preflight_sha256=c.file_hash(path))
        c.atomic_json(tmp_path/f"{phase}-summary.json",summary)
    resource=s.measured_capacity(tmp_path,prod)
    assert resource["memory_gb"]==32
    task=next(m.tasks(cap))
    base=tmp_path/"traces"/c.task_id(task)
    identity=dict(manifest=c.digest(cap),task=list(task))
    arrays,record=c.load_artifact(base,identity)
    original_record=deepcopy(record)
    for change in (
        lambda r:r.update(init_seed=1),
        lambda r:r["metadata"].update(sampling_p=.2),
        lambda r:r["metadata"]["rng"].update(entropy=2),
        lambda r:r.update(decoder_prior=.003),
        lambda r:r["config"].update(samples=2),
    ):
        bad=deepcopy(original_record);change(bad)
        c.save_artifact(base,identity,arrays,bad)
        with pytest.raises(ValueError):s.measured_capacity(tmp_path,prod)
    c.save_artifact(base,identity,arrays,original_record)
    binding=tmp_path/"sample-execution-intent.json"
    original_binding=binding.read_bytes()
    value=json.loads(original_binding);value["pbs_job_id"]="2.fixture"
    c.atomic_json(binding,value)
    with pytest.raises(ValueError,match="binding"):s.measured_capacity(tmp_path,prod)
    binding.write_bytes(original_binding)
    evidence_path=tmp_path/"preflight-sample/native_preflight.json"
    evidence_path.write_bytes(evidence_path.read_bytes()+b" ")
    with pytest.raises(ValueError,match="native evidence"):s.measured_capacity(tmp_path,prod)
