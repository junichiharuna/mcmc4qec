"""Case-partitioned BAR timing and measured, non-retrying submission."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_bar_time_benchmark as m
import submit_tile_bar_time as s
from test_tile_bar_time_benchmark import settings


def plans():
    return m.make_plan(settings(),capacity=False,case=3),m.make_plan(settings(),capacity=True,case=3)


def measured(cap):
    rows=[]
    for task in m.tasks(cap):
        row=cap["conditions"][task[0]]
        rows.append(dict(task=list(task),status="ok",available=True,reused=False,case=3,
            epsilon=row["epsilon"],condition=row["condition"],replicate=task[1],
            anchor_seed=m.task_seed(cap,task,0,0,0),bootstrap_seed=m.task_seed(cap,task,0,0,3),
            task_wall_seconds=100.,cpu_seconds=90.,peak_rss_mb=1024.))
    return dict(manifest=c.digest(cap),records=rows,tasks=len(rows),failed=0,unavailable=0,reused_tasks=0,
                phase_wall_seconds=300.,native_preflight_sha256="a"*64)


def test_case_partition_preserves_seeds_and_all_selection_outcomes():
    full=m.make_plan(settings(),capacity=False)
    parts=[m.make_plan(settings(),capacity=False,case=case) for case in range(4)]
    assert [task for p in parts for task in m.tasks(p)]==list(m.tasks(full))
    for part in parts:
        assert part["conditions"]==full["conditions"]
        for task in m.tasks(part):
            assert m.task_seed(part,task,1,2,2)==m.task_seed(full,task,1,2,2)
    with pytest.raises(ValueError):m.make_plan(settings(),capacity=True,case=4)


def test_resource_plan_requires_full_fresh_same_case_capacity():
    prod,cap=plans()
    data=measured(cap)
    resource=s.resource_plan(prod,cap,data)
    assert resource["predicted_phase_seconds"]==600
    assert resource["wall_seconds"]==1800 and resource["memory_gb"]==152
    for field,value in (("status","failed"),("available",False),("reused",True),("anchor_seed",1),
                        ("bootstrap_seed",2),("peak_rss_mb",None),("cpu_seconds",float("nan"))):
        bad=deepcopy(data);bad["records"][0][field]=value
        with pytest.raises(ValueError):s.resource_plan(prod,cap,bad)
    for mutate in (lambda d:d["records"].pop(),lambda d:d.update(phase_wall_seconds=100000.),
                   lambda d:d["records"][0].update(peak_rss_mb=10000.)):
        bad=deepcopy(data);mutate(bad)
        with pytest.raises(ValueError):s.resource_plan(prod,cap,bad)
    prod["case"]=2
    with pytest.raises(ValueError):s.resource_plan(prod,cap,data)


def save_plan(root,capacity):
    root.mkdir(exist_ok=True)
    plan=m.make_plan(settings(),capacity=capacity,case=3)
    for name,value in (("settings",settings()),("manifest",plan),*m.native.platform_inputs().items()):
        c.atomic_json(root/(name+".json"),value)
    return plan


def test_submit_guards_and_qsub_intent(tmp_path):
    root=tmp_path/"run";save_plan(root,True)
    calls=[]
    def runner(command,**kwargs):
        assert (root/"submission_intent.json").exists()
        assert command[0]=="qsub"
        calls.append(command)
        return subprocess.CompletedProcess(command,0,stdout="123.cluster\n")
    assert s.submit(tmp_path,root)["job_id"]=="dry-run"
    script=(root/"timing.sh").read_text()
    assert "tile_bar_time_benchmark.py" in script and "mem=340gb" in script and "24:00:00" in script
    for controllers,jobs in ((["live"],{}),([],{"a":{"Resource_List":{"select":"2:ncpus=96"}}})):
        with pytest.raises(ValueError):s.submit(tmp_path,root,execute=True,controller_query=lambda:controllers,active_query=lambda:jobs,runner=runner)
    assert not calls
    assert s.submit(tmp_path,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)["job_id"]=="123.cluster"
    with pytest.raises(ValueError):s.submit(tmp_path,root,execute=True)
    assert len(calls)==1


@pytest.mark.parametrize("timeout",[True,False])
def test_ambiguous_submission_never_retries(tmp_path,timeout):
    save_plan(tmp_path,True)
    def runner(command,**kwargs):
        if timeout:raise subprocess.TimeoutExpired(command,30)
        return subprocess.CompletedProcess(command,0,stdout="unrecognized")
    with pytest.raises((subprocess.TimeoutExpired,RuntimeError)):
        s.submit(tmp_path,tmp_path,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert (tmp_path/"submission_intent.json").exists() and not (tmp_path/"submission.json").exists()
    with pytest.raises(ValueError):s.submit(tmp_path,tmp_path)


def test_capacity_artifact_and_native_evidence_are_checked(tmp_path):
    prod,cap=plans()
    save_plan(tmp_path,True)
    data=measured(cap)
    profile=m.native.platform_inputs()["platform_profile"]
    c.atomic_json(tmp_path/"native_preflight.json",dict(manifest=c.digest(cap),pbs_job_id="1.cluster",hostname="compute",profile=profile))
    data["native_preflight_sha256"]=c.file_hash(tmp_path/"native_preflight.json")
    for row in data["records"]:
        saved={k:v for k,v in row.items() if k!="reused"}
        saved.update(chains=[],anchor={})
        c.save_artifact(tmp_path/"tasks"/c.task_id(row["task"]),dict(manifest=c.digest(cap),task=row["task"]),{},saved)
    c.atomic_json(tmp_path/"summary.json",data)
    assert s.measured_capacity(tmp_path,prod)["memory_gb"]==152
    original=(tmp_path/"native_preflight.json").read_bytes()
    (tmp_path/"native_preflight.json").write_bytes(original+b" ")
    with pytest.raises(ValueError,match="native evidence"):s.measured_capacity(tmp_path,prod)
    (tmp_path/"native_preflight.json").write_bytes(original)
    data["records"][0]["task_wall_seconds"]+=1
    c.atomic_json(tmp_path/"summary.json",data)
    with pytest.raises(ValueError,match="raw task"):s.measured_capacity(tmp_path,prod)
    data["records"][0]["task_wall_seconds"]-=1
    c.atomic_json(tmp_path/"summary.json",data)
    task=data["records"][0]["task"]
    marker=(tmp_path/"tasks"/c.task_id(task)).with_suffix(".done.json")
    marker.unlink()
    with pytest.raises(ValueError):s.measured_capacity(tmp_path,prod)


def test_unpartitioned_empty_and_altered_plans_refused(tmp_path):
    plan=save_plan(tmp_path,True)
    plan["case"]=None
    c.atomic_json(tmp_path/"manifest.json",plan)
    with pytest.raises(ValueError):s.submit(tmp_path,tmp_path)
    chosen=settings()
    for i in (6,7):chosen["records"][i]=dict(case=3,epsilon=chosen["records"][i]["epsilon"],status="unmet",reason="unmet")
    c.atomic_json(tmp_path/"settings.json",chosen)
    c.atomic_json(tmp_path/"manifest.json",m.make_plan(chosen,capacity=True,case=3))
    with pytest.raises(ValueError,match="nonempty"):s.submit(tmp_path,tmp_path)


@pytest.mark.parametrize("existing",["execution_intent.json","tasks","summary.json"])
def test_run_rejects_old_measurement_before_workers(tmp_path,monkeypatch,existing):
    save_plan(tmp_path,True)
    monkeypatch.setenv("PBS_JOBID","test.cluster")
    for key,value in m.THREADS.items():monkeypatch.setenv(key,value)
    path=tmp_path/existing
    if existing=="tasks":path.mkdir()
    else:path.write_text("{}")
    monkeypatch.setattr(m.native,"native_preflight",lambda *args:pytest.fail("old run must not reach preflight"))
    with pytest.raises((ValueError,FileExistsError)):m.run(tmp_path)
