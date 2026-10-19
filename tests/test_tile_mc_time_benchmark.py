"""Fixed-budget MC timing records real RNG provenance and separate CPU/wall clocks."""
import json
import copy
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_mc_time_benchmark as m
import tile_study as t
import mcmc4qec as qec


def budget():
    path=Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json"
    return json.loads(path.read_text())


def test_fixed_plans_have_separate_capacity_seeds_and_exact_budgets():
    prod=m.make_plan(budget(),capacity=False)
    cap=m.make_plan(budget(),capacity=True)
    assert len(list(m.tasks(prod)))==1536 and len(list(m.tasks(cap)))==768
    assert prod["seed_stage"]==121 and cap["seed_stage"]==122
    assert prod["conditions"]==cap["conditions"]
    assert sum(r["planned_trials"] for r in prod["conditions"])*prod["replicates"]==10358784
    assert m.task_seed(prod,(0,0))!=m.task_seed(cap,(0,0))
    altered=budget()
    altered["records"][0]["planned_trials"]+=64
    with pytest.raises(ValueError):
        m.make_plan(altered,capacity=False)


@pytest.mark.parametrize("condition",[0,2,4,6])
def test_small_task_records_actual_p_rng_and_replays_public_mc(tmp_path,condition):
    plan=m.make_plan(budget(),capacity=False)
    plan["conditions"][condition]["planned_trials"]=12
    task=(condition,0)
    record=m.run_task((tmp_path,plan,task))
    assert record["status"]=="ok" and record["trials"]==12
    assert record["metadata"]["sampling_p"]==record["target_p"]
    assert record["metadata"]["rng"]["entropy"]==record["seed"]==m.task_seed(plan,task)
    assert record["cpu_seconds"]>=0 and record["task_wall_seconds"]>=record["direct_mc_elapsed_seconds"]
    size,noise=plan["cases"][record["case"]]
    _,problem=t.build_problem(size,noise,record["target_p"])
    replay=qec.direct_mc(problem,record["target_p"],trials=12,seed=record["seed"])
    assert replay.failures==record["failures"] and replay.estimate==record["estimate"]
    assert m.run_task((tmp_path,plan,task))==record


def test_failed_task_is_saved_and_never_silently_retried(tmp_path,monkeypatch):
    plan=m.make_plan(budget(),capacity=True)
    plan["conditions"][0]["planned_trials"]=2
    calls=[]
    def fail(*args,**kwargs):
        calls.append(kwargs["seed"])
        raise ValueError("deliberate finite test failure")
    monkeypatch.setattr(m.qec,"direct_mc",fail)
    record=m.run_task((tmp_path,plan,(0,0)))
    assert record["status"]=="failed" and "deliberate" in record["error"]
    assert m.run_task((tmp_path,plan,(0,0)))==record and len(calls)==1


def test_full_run_requires_qsub_and_cannot_start_on_local_login_context(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    monkeypatch.setattr(sys,"argv",["tile_mc_time_benchmark.py","run","--root",str(tmp_path)])
    with pytest.raises(ValueError,match="qsub"):
        m.main()
    assert not list(tmp_path.iterdir())


def prepare_run(root,monkeypatch):
    plan=m.make_plan(budget(),capacity=True)
    m.c.atomic_json(root/"manifest.json",plan)
    m.c.atomic_json(root/"budget.json",budget())
    inputs=m.platform_inputs()
    for key,value in inputs.items():
        m.c.atomic_json(root/(key+".json"),value)
    monkeypatch.setenv("PBS_JOBID","test.native")
    for key,value in m.THREADS.items():
        monkeypatch.setenv(key,value)
    monkeypatch.setattr(sys,"argv",["tile_mc_time_benchmark.py","run","--root",str(root)])
    return plan,inputs


@pytest.mark.parametrize("change",["saved_fixture","actual_decode"])
def test_native_mismatch_prevents_worker_start(tmp_path,monkeypatch,change):
    plan,inputs=prepare_run(tmp_path,monkeypatch)
    actual=copy.deepcopy(inputs["platform_profile"])
    if change=="saved_fixture":
        fixture=copy.deepcopy(inputs["platform_fixture"])
        fixture["changed"]=True
        m.c.atomic_json(tmp_path/"platform_fixture.json",fixture)
    else:
        actual["repeated"][0]["sector"]=0
        actual["repeated"][0]["failure"]=False
    monkeypatch.setattr(m.native_probe,"probe",lambda fixture:actual)
    def forbidden(*args,**kwargs):
        pytest.fail("worker must not start after native/input mismatch")
    monkeypatch.setattr(m.c,"parallel_map",forbidden)
    with pytest.raises(ValueError):
        m.main()
    assert not (tmp_path/"summary.json").exists()
    assert not (tmp_path/"native_preflight.json").exists()


def test_native_success_is_saved_before_sampling(tmp_path,monkeypatch):
    plan,inputs=prepare_run(tmp_path,monkeypatch)
    monkeypatch.setattr(m.native_probe,"probe",lambda fixture:copy.deepcopy(inputs["platform_profile"]))
    def completed(function,jobs,workers):
        evidence=json.loads((tmp_path/"native_preflight.json").read_text())
        assert evidence["profile"]==inputs["platform_profile"]
        assert evidence["wall_seconds"]>=0
        assert evidence["manifest"]==m.c.digest(plan)
        assert evidence["pbs_job_id"]=="test.native" and evidence["hostname"]
        intent=json.loads((tmp_path/"execution_intent.json").read_text())
        assert all(intent[key]==evidence[key] for key in ("manifest","pbs_job_id","hostname"))
        return [dict(task=list(task),status="ok",cpu_seconds=1.) for task in m.tasks(plan)]
    monkeypatch.setattr(m.c,"parallel_map",completed)
    m.main()
    summary=json.loads((tmp_path/"summary.json").read_text())
    assert summary["native_preflight_sha256"]==m.c.file_hash(tmp_path/"native_preflight.json")
    assert summary["tasks"]==768 and summary["failed"]==0


@pytest.mark.parametrize("existing",["tasks","summary.json","execution_intent.json"])
def test_run_refuses_previous_artifacts_before_preflight(tmp_path,monkeypatch,existing):
    prepare_run(tmp_path,monkeypatch)
    path=tmp_path/existing
    if existing=="tasks":
        path.mkdir()
        (path/"old.done.json").write_text("{}")
    else:
        path.write_text("{}")
    monkeypatch.setattr(m,"native_preflight",lambda *args:pytest.fail("existing run reached native probe"))
    with pytest.raises((ValueError,FileExistsError)):
        m.main()
