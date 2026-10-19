"""Measured MC resources and non-retrying, controller-aware qsub submission."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_mc_time_benchmark as m
import submit_tile_mc_time as s


def plans():
    budget=json.loads((Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json").read_text())
    return m.make_plan(budget,capacity=False),m.make_plan(budget,capacity=True)


def capacity(cap):
    rows=[dict(task=list(task),status="ok",seed=m.task_seed(cap,task),
               trials=cap["conditions"][task[0]]["planned_trials"],task_wall_seconds=10.,cpu_seconds=9.,peak_rss_mb=100.)
          for task in m.tasks(cap)]
    return dict(manifest=c.digest(cap),purpose=cap["purpose"],tasks=len(rows),failed=0,phase_wall_seconds=100.,records=rows)


def test_measured_resources_require_complete_matching_capacity():
    prod,cap=plans()
    data=capacity(cap)
    result=s.resource_plan(prod,cap,data)
    assert result["predicted_phase_seconds"]==200
    assert result["wall_seconds"]==1800 and result["memory_gb"]==32
    assert result["capacity_summary_digest"]==c.digest(data)
    for key,value in (("status","failed"),("seed",123),("trials",1),("peak_rss_mb",None),("cpu_seconds",float("nan"))):
        altered=capacity(cap)
        altered["records"][0][key]=value
        with pytest.raises(ValueError):
            s.resource_plan(prod,cap,altered)
    data["records"].pop()
    with pytest.raises(ValueError):
        s.resource_plan(prod,cap,data)


def test_resource_limit_and_condition_changes_rejected():
    prod,cap=plans()
    data=capacity(cap)
    data["phase_wall_seconds"]=100000.
    with pytest.raises(ValueError):
        s.resource_plan(prod,cap,data)
    data=capacity(cap)
    data["records"][0]["peak_rss_mb"]=10000.
    with pytest.raises(ValueError):
        s.resource_plan(prod,cap,data)
    prod["conditions"][0]["planned_trials"]+=1
    with pytest.raises(ValueError):
        s.resource_plan(prod,cap,capacity(cap))


def test_submit_dry_run_and_live_controller_or_node_limit(tmp_path):
    _,cap=plans()
    calls=[]
    def runner(*args,**kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args[0],0,stdout="123.cluster\n")
    resource=s.capacity_resources()
    for execute,controllers,jobs in ((False,["controller"],{}),(True,["controller"],{}),
                                     (True,[],{"a":{"Resource_List":{"select":"2:ncpus=96"}}})):
        kwargs=dict(execute=execute,controller_query=lambda:controllers,active_query=lambda:jobs,runner=runner)
        if execute:
            with pytest.raises(ValueError):
                s.submit(tmp_path,tmp_path,cap,resource,**kwargs)
        else:
            assert s.submit(tmp_path,tmp_path,cap,resource,**kwargs)["job_id"]=="dry-run"
    assert not calls and not (tmp_path/"submission_intent.json").exists()


@pytest.mark.parametrize("response",["123.cluster\n","unrecognized"])
def test_intent_written_before_qsub_and_no_automatic_retry(tmp_path,response):
    _,cap=plans()
    calls=[]
    def runner(command,**kwargs):
        assert (tmp_path/"submission_intent.json").exists()
        assert command[0]=="qsub"
        calls.append(command)
        return subprocess.CompletedProcess(command,0,stdout=response)
    kwargs=dict(execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    if response.startswith("123"):
        result=s.submit(tmp_path,tmp_path,cap,s.capacity_resources(),**kwargs)
        assert result["job_id"]=="123.cluster" and (tmp_path/"submission.json").exists()
    else:
        with pytest.raises(RuntimeError):
            s.submit(tmp_path,tmp_path,cap,s.capacity_resources(),**kwargs)
        assert not (tmp_path/"submission.json").exists()
    with pytest.raises(ValueError):
        s.submit(tmp_path,tmp_path,cap,s.capacity_resources(),**kwargs)
    assert len(calls)==1


def test_timeout_preserves_intent(tmp_path):
    _,cap=plans()
    def timeout(command,**kwargs):
        raise subprocess.TimeoutExpired(command,30)
    with pytest.raises(subprocess.TimeoutExpired):
        s.submit(tmp_path,tmp_path,cap,s.capacity_resources(),execute=True,
                 controller_query=lambda:[],active_query=lambda:{},runner=timeout)
    assert (tmp_path/"submission_intent.json").exists()


def test_controller_query_uses_actual_process_commands(monkeypatch):
    def runner(command,**kwargs):
        if command==["id","-un"]:
            return subprocess.CompletedProcess(command,0,stdout="user\n")
        assert command==["ps","-u","user","-o","args="]
        return subprocess.CompletedProcess(command,0,stdout="/env/python /bundle/tile_coordinator.py status\n/env/python /bundle/tile_coordinator.py run --config config.json\nps -u user -o args=\n")
    monkeypatch.setattr(s.subprocess,"run",runner)
    assert s.live_controllers()==["/env/python /bundle/tile_coordinator.py run --config config.json"]


def saved_capacity(root):
    prod,cap=plans()
    data=capacity(cap)
    budget=json.loads((Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json").read_text())
    c.atomic_json(root/"manifest.json",cap)
    c.atomic_json(root/"budget.json",budget)
    inputs=m.platform_inputs()
    for key,value in inputs.items():
        c.atomic_json(root/(key+".json"),value)
    binding=dict(manifest=c.digest(cap),pbs_job_id="12.cluster",hostname="compute")
    c.atomic_json(root/"execution_intent.json",binding)
    c.atomic_json(root/"native_preflight.json",dict(**binding,profile=inputs["platform_profile"],wall_seconds=.1))
    data["native_preflight_sha256"]=c.file_hash(root/"native_preflight.json")
    for row in data["records"]:
        task=row["task"]
        row["target_p"]=cap["conditions"][task[0]]["target_p"]
        row["metadata_sha256"]=c.digest(dict(sampling_p=row["target_p"],rng=dict(entropy=row["seed"])))
        c.save_artifact(root/"tasks"/c.task_id(task),dict(manifest=c.digest(cap),task=task),{},
                        dict(**row,metadata=dict(sampling_p=row["target_p"],rng=dict(entropy=row["seed"]))))
    c.atomic_json(root/"summary.json",data)
    return prod,cap,data


def test_capacity_loader_binds_raw_artifacts_native_and_execution(tmp_path):
    prod,cap,data=saved_capacity(tmp_path)
    assert s.measured_capacity(tmp_path,prod)==s.resource_plan(prod,cap,data)
    row=data["records"][0]
    base=tmp_path/"tasks"/c.task_id(row["task"])
    metadata=base.with_suffix(".json")
    original=metadata.read_bytes()
    metadata.write_bytes(original+b" ")
    with pytest.raises(ValueError):
        s.measured_capacity(tmp_path,prod)
    metadata.write_bytes(original)
    payload=base.with_suffix(".npz")
    payload_bytes=payload.read_bytes()
    payload.write_bytes(payload_bytes+b"changed")
    with pytest.raises(ValueError):
        s.measured_capacity(tmp_path,prod)
    payload.write_bytes(payload_bytes)
    marker=base.with_suffix(".done.json")
    marker_bytes=marker.read_bytes()
    altered=json.loads(marker_bytes)
    del altered["sha256"][".json"]
    c.atomic_json(marker,altered)
    with pytest.raises(ValueError):
        s.measured_capacity(tmp_path,prod)
    marker.write_bytes(marker_bytes)
    saved=json.loads(original)
    saved["metadata"]["rng"]["entropy"]+=1
    c.save_artifact(base,dict(manifest=c.digest(cap),task=row["task"]),{},saved)
    with pytest.raises(ValueError):
        s.measured_capacity(tmp_path,prod)
    metadata.write_bytes(original)
    payload.write_bytes(payload_bytes)
    marker.write_bytes(marker_bytes)
    data["records"][0]["cpu_seconds"]+=1
    c.atomic_json(tmp_path/"summary.json",data)
    with pytest.raises(ValueError):
        s.measured_capacity(tmp_path,prod)


    data["records"][0]["cpu_seconds"]-=1
    c.atomic_json(tmp_path/"summary.json",data)
    evidence=json.loads((tmp_path/"native_preflight.json").read_text())
    evidence["pbs_job_id"]="login"
    c.atomic_json(tmp_path/"native_preflight.json",evidence)
    data["native_preflight_sha256"]=c.file_hash(tmp_path/"native_preflight.json")
    c.atomic_json(tmp_path/"summary.json",data)
    with pytest.raises(ValueError):
        s.measured_capacity(tmp_path,prod)


@pytest.mark.parametrize("existing",["execution_intent.json","tasks","summary.json"])
def test_submit_rejects_prior_execution_without_qsub(tmp_path,existing):
    _,cap=plans()
    (tmp_path/existing).write_text("{}")
    with pytest.raises(ValueError):
        s.submit(tmp_path,tmp_path,cap,s.capacity_resources(),execute=True,
                 controller_query=lambda:[],active_query=lambda:{},
                 runner=lambda *args,**kwargs:pytest.fail("old timing run reached qsub"))
