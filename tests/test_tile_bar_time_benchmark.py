"""Standalone BAR measurements must reproduce actual independent sampler inputs."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_bar_study as b
import tile_study as t
import tile_bar_time_benchmark as m


def settings():
    source=b.make_plan()
    records=[]
    for case in range(4):
        for epsilon in (.2,.1):
            records.append(dict(case=case,epsilon=epsilon,status="selected",condition=dict(
                case=case,kernel="ZH",init="logical",chains=4,burn=600,samples=600,
                ladder="coarse",method="cross_chain",block=None)))
    return dict(schema=1,purpose="standalone_bar_settings",sampling_manifest=c.digest(source),
                selection_evidence_sha256=["a"*64],records=records)


def small_plan(case):
    plan=m.make_plan(settings(),capacity=False)
    row=plan["conditions"][case*2]
    row["condition"].update(chains=2,burn=2,samples=8)
    row["rungs"]=[.1,row["target_p"]]
    plan.update(anchor_trials=128,bootstrap_replicates=8)
    return plan,(case*2,0)


def test_fixed_independent_cohorts_and_unmet_conditions():
    prod=m.make_plan(settings(),capacity=False)
    cap=m.make_plan(settings(),capacity=True)
    assert len(list(m.tasks(prod)))==1536 and len(list(m.tasks(cap)))==768
    assert (prod["seed_stage"],cap["seed_stage"])==(140,141)
    assert len({m.task_seed(plan,(0,0),0,0,p) for plan in (prod,cap) for p in range(4)})==8
    chosen=settings()
    chosen["records"][0]=dict(case=0,epsilon=.2,status="unmet",reason="No complete setting met the criterion")
    limited=m.make_plan(chosen,capacity=False)
    assert len(list(m.tasks(limited)))==7*192 and limited["conditions"][0]["status"]=="unmet"


@pytest.mark.parametrize("change",["missing","duplicate","grid","method","manifest","evidence"])
def test_settings_outside_fixed_calibration_or_missing_evidence_refused(change):
    chosen=settings()
    if change=="missing":chosen["records"].pop()
    elif change=="duplicate":chosen["records"][-1]=chosen["records"][0]
    elif change=="grid":chosen["records"][0]["condition"]["samples"]=1234
    elif change=="method":chosen["records"][0]["condition"]["block"]=32
    elif change=="manifest":chosen["sampling_manifest"]="wrong"
    elif change=="evidence":chosen["selection_evidence_sha256"]=[]
    with pytest.raises(ValueError):m.make_plan(chosen,capacity=False)


@pytest.mark.parametrize("case",range(4))
def test_actual_small_task_replays_fixed_prior_sampler_and_estimator(tmp_path,case):
    plan,task=small_plan(case)
    record=m.run_task((tmp_path,plan,task))
    assert record["status"]=="ok" and record["failed_chains"]==0
    row=plan["conditions"][task[0]]
    arrays,saved=c.load_artifact(tmp_path/"tasks"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
    assert saved==record and arrays["weight"].shape==(2,2,8)
    assert np.all(arrays["sector"]>0)
    _,problem=t.build_problem(row["size"],row["noise"],row["target_p"])
    first=record["chains"][0]
    assert first["metadata"]["sampling_p"]==.1
    assert first["metadata"]["rng"]["entropy"]==m.task_seed(plan,task,0,0,2)
    assert sum(stat["proposed"] for stat in first["acceptance"].values())==10
    replay=m.qec.sample_faulty(problem,.1,config=m.qec.SamplingConfig(samples=10,burn_in=0,kernels=t.KERNELS["ZH"],cache_cap=200000,cache_policy="lru"),
                              initial_state=arrays["initial"][0,0],seed=first["sample_seed"])
    compact=t.compact(problem,replay.states[0][2:])
    assert np.array_equal(compact["weight"],arrays["weight"][0,0])
    assert np.array_equal(compact["sector"],arrays["sector"][0,0])
    anchor=record["anchor"]
    base=c.estimate_window(list(arrays["weight"]),row["n"],row["rungs"],anchor["estimate"],block=None,
                           replicates=8,rng=np.random.default_rng(record["bootstrap_seed"]))
    expected=b.with_anchor_variance(base,anchor)
    assert record["estimate"]==expected["estimate"] and record["interval"]==expected["interval"]
    assert record["task_wall_seconds"]>=sum(v["wall_seconds"] for v in record["timing"].values())
    assert all(v["cpu_seconds"]>=0 for v in record["timing"].values())
    assert m.run_task((tmp_path,plan,task))==record


def test_logical_initialization_preserves_original_maximum_chain_stride():
    plan,task=small_plan(3)
    row=plan["conditions"][task[0]]
    assert row["initialization_stride"]==8
    assert m.logical_index(row,1,0)==8
    assert m.logical_index(row,0,1)==1


def test_failed_chains_remain_and_are_not_retried(tmp_path,monkeypatch):
    plan,task=small_plan(0)
    calls=[]
    def fail(*args,**kwargs):
        calls.append(kwargs["seed"])
        raise ValueError("deliberate sampled failure")
    monkeypatch.setattr(m.qec,"sample_faulty",fail)
    record=m.run_task((tmp_path,plan,task))
    assert record["status"]=="failed" and record["failed_chains"]==4
    assert record["estimate"] is None and record["interval"] is None and not record["available"]
    assert len(record["chains"])==4 and len(set(calls))==4
    assert m.run_task((tmp_path,plan,task))==record and len(calls)==4


def test_zero_anchor_not_reported_as_zero_logical_error(tmp_path,monkeypatch):
    plan,task=small_plan(0)
    original=m.qec.direct_mc
    def zero(*args,**kwargs):
        real=original(*args,**kwargs)
        return SimpleNamespace(metadata=real.metadata,trials=real.trials,failures=0,estimate=0.,interval=(0.,.1))
    monkeypatch.setattr(m.qec,"direct_mc",zero)
    record=m.run_task((tmp_path,plan,task))
    assert record["estimate"] is None and record["interval"] is None
    assert record["failure"]=="anchor_unavailable" and record["failed_chains"]==0
    assert len(record["chains"])==4


def test_run_requires_qsub_before_reading_or_writing(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="qsub"):m.run(tmp_path)
    assert not list(tmp_path.iterdir())


def test_block_uncertainty_keeps_same_pooled_point(tmp_path):
    plan,task=small_plan(0)
    cross=m.run_task((tmp_path/"cross",plan,task))
    plan["conditions"][0]["condition"].update(method="block",block=4)
    block=m.run_task((tmp_path/"block",plan,task))
    assert block["status"]=="ok" and block["estimate"]==cross["estimate"]
    assert block["anchor"]["seed"]==cross["anchor"]["seed"]


def prepare_run(root,monkeypatch):
    chosen=settings()
    plan=m.make_plan(chosen,capacity=True)
    for name,value in (("settings",chosen),("manifest",plan),*m.native.platform_inputs().items()):
        c.atomic_json(root/(name+".json"),value)
    monkeypatch.setenv("PBS_JOBID","test.bar_time")
    for key in m.THREADS:monkeypatch.setenv(key,"1")
    return plan


def test_native_mismatch_prevents_standalone_workers(tmp_path,monkeypatch):
    prepare_run(tmp_path,monkeypatch)
    actual=deepcopy(m.native.platform_inputs()["platform_profile"])
    actual["native_ldpc_sha256"]={"different":"binary"}
    monkeypatch.setattr(m.native.native_probe,"probe",lambda fixture:actual)
    monkeypatch.setattr(c,"parallel_map",lambda *args:pytest.fail("workers must not start"))
    with pytest.raises(ValueError,match="native decoder"):m.run(tmp_path)
    assert not (tmp_path/"summary.json").exists()


def test_run_sorts_fixed_cohort_and_distinguishes_cache_time(tmp_path,monkeypatch):
    plan=prepare_run(tmp_path,monkeypatch)
    monkeypatch.setattr(m.native.native_probe,"probe",lambda fixture:deepcopy(m.native.platform_inputs()["platform_profile"]))
    records=[dict(task=list(task),status="ok",available=True,reused=task[1]==0) for task in m.tasks(plan)]
    monkeypatch.setattr(c,"parallel_map",lambda *args:list(reversed(records)))
    result=m.run(tmp_path)
    assert result["tasks"]==768 and result["reused_tasks"]==8
    assert [tuple(row["task"]) for row in result["records"]]==list(m.tasks(plan))
    native=json.loads((tmp_path/"native_preflight.json").read_text())
    assert native["pbs_job_id"]=="test.bar_time" and native["hostname"]
    assert native["manifest"]==c.digest(plan) and result["native_preflight_sha256"]==c.file_hash(tmp_path/"native_preflight.json")
