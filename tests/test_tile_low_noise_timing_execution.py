"""Small timing tasks and resource/terminal acceptance; no production execution."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shlex
import sys

import numpy as np
import pytest

for dep in ("ldpc","bposd","pymatching"): pytest.importorskip(dep)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_study as t
import tile_low_noise_timing_plan as plans
import tile_low_noise_timing_execution as r


def measurement(t=60,a=1,m=256,p=128):
    return dict(records=[dict(status="ok",available=True,task_wall_seconds=t,inclusive_wall_seconds=t+a,
                             cpu_seconds=t/2,inclusive_cpu_seconds=t/2+.1,peak_rss_mb=m) for _ in range(2)],
                pool_wall_seconds=t+a+5,outside_pool_wall_seconds=10,parent_peak_rss_mb=p)


@pytest.mark.parametrize("t,m,w,n,mem,wall",[(60,256,96,192,57,1800),(30000,256,96,96,57,61200),
    (43000,256,96,0,None,None),(60,4000,42,192,337,1800)])
def test_resource_examples_and_full_union(t,m,w,n,mem,wall):
    out=r.resource_plan(measurement(t=t,m=m))
    assert out["workers_limit"]==w and out["partition_size"]==n
    if not n:
        assert out["status"]=="execution_infeasible_wall_policy"
        return
    assert out["partitions"][0]["resource"]["memory_gb"]==mem
    assert out["partitions"][0]["resource"]["wall_seconds"]==wall
    assert [rep for part in out["partitions"] for rep in part["replicates"]]==list(range(192))


@pytest.mark.parametrize("key,value",[("task_wall_seconds",True),("task_wall_seconds",float('nan')),
    ("peak_rss_mb",0),("inclusive_wall_seconds",1),("cpu_seconds",-1)])
def test_invalid_capacity_numbers(key,value):
    data=measurement();data["records"][0][key]=value
    with pytest.raises(ValueError):r.resource_plan(data)


def test_capacity_unavailable_and_memory_infeasible():
    data=measurement();data["records"][0]["available"]=False
    assert r.resource_plan(data)["status"]=="capacity_unavailable"
    data=measurement(m=200000)
    assert r.resource_plan(data)["status"]=="execution_infeasible_memory_policy"


def small_plan(method="bar",noise="bit",replicates=2):
    role=f"low_timing.{method}."+("capacity" if replicates==2 else "benchmark")
    case=0 if noise=="bit" else 2
    cfg=dict(case=case,kernel="ZH",init="logical_basis",chains=2,burn=2,samples=8,ladder="coarse",method="cross_chain",block=None)
    row=dict(case=case,target_index=0,epsilon_index=0,epsilon=.2,target_p=.01,status="selected",planning_status="ready",condition=cfg,
        mc_budget=dict(trials=12),size=6,noise=noise,rungs=[.1,.01],fine_rung_indices=[0,9],initialization_stride=16 if case==0 else 8,
        anchor_trials=128,bootstrap_replicates=8,cache_cap=200000,decoder=t.SETTINGS,kernels={k:asdict(v) for k,v in t.KERNELS.items()})
    return dict(purpose=role,seed_stage=plans.STAGES[role],master_seed=t.MASTER,seed_version=1,replicates=replicates,rows=[row]),(case,0,0,0)


@pytest.mark.parametrize("noise",["bit","depolarizing"])
def test_actual_bar_fixed_prior_seed_initialization_and_replay(tmp_path,noise):
    plan,task=small_plan(noise=noise)
    result=r.run_task((str(tmp_path),plan,task));row=plan["rows"][0]
    arrays,saved=c.load_artifact(tmp_path/"tasks"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
    assert result["status"]=="ok" and result["available"]
    assert saved["bootstrap_rng_consumed"] is False and len(saved["chains"])==4
    assert all(entry["initialization_rng_consumed"] is False for entry in saved["chains"])
    assert arrays["weight"].shape==(2,2,8) and np.all(arrays["sector"]>0)
    assert saved["anchor_seed"]==plans.task_seed(plan,task,0,0,0)
    code,problem=t.build_problem(6,noise,.01)
    first=saved["chains"][0]
    replay=r.qec.sample_faulty(problem,.1,config=r.qec.SamplingConfig(samples=10,burn_in=0,kernels=t.KERNELS["ZH"],cache_cap=200000,cache_policy="lru"),
        initial_state=arrays["initial"][0,0],seed=plans.task_seed(plan,task,0,0,2))
    assert np.array_equal(t.compact(problem,replay.states[0][2:])["weight"],arrays["weight"][0,0])
    assert first["metadata"]["sampling_p"]==.1
    expected=c.estimate_window(list(arrays["weight"]),code.n,row["rungs"],saved["anchor"]["estimate"],block=None,replicates=8,
        rng=np.random.default_rng(saved["bootstrap_seed"]))
    assert saved["estimate"]==r.bar.with_anchor_variance(expected,saved["anchor"])["estimate"]
    with pytest.raises(ValueError):r.run_task((str(tmp_path),plan,task))


def test_mc_actual_budget_and_zero_failures_valid(tmp_path):
    plan,task=small_plan("mc")
    result=r.run_task((str(tmp_path),plan,task))
    _,problem=t.build_problem(6,"bit",.01)
    expected=r.qec.direct_mc(problem,.01,trials=12,seed=plans.task_seed(plan,task,0,0,0))
    assert result["status"]=="ok" and result["available"]
    assert result["trials"]==12 and result["failures"]==expected.failures


def test_task_failure_keeps_all_chains(tmp_path,monkeypatch):
    plan,task=small_plan()
    monkeypatch.setattr(r.qec,"sample_faulty",lambda *a,**k:(_ for _ in ()).throw(RuntimeError("fixture failure")))
    result=r.run_task((str(tmp_path),plan,task))
    assert result["status"]=="failed" and result["failed_chains"]==4 and not result["available"]


def test_actual_metadata_mismatch_is_validation_failure(tmp_path,monkeypatch):
    plan,task=small_plan("mc");actual=r.qec.direct_mc
    def changed(*args,**kwargs):
        out=actual(*args,**kwargs);out.metadata["sampling_p"] = .9;return out
    monkeypatch.setattr(r.qec,"direct_mc",changed)
    result=r.run_task((str(tmp_path),plan,task))
    assert result["status"]=="validation_failed" and not result["available"]


def test_pbs_binding_run_count_resource_host_and_exit():
    resource=r.capacity_resources();script=Path('/fixed/timing.sh')
    ledger=dict(command=['qsub',str(script)],resource=resource)
    job=dict(job_state='F',Exit_status=0,run_count=1,Submit_arguments=__import__("shlex").quote(str(script)),exec_host='node/0',
        Resource_List=dict(nodect=1,ncpus=2,select='1:ncpus=2:mem=340gb',mem='340gb',walltime='24:00:00'))
    r.check_pbs(ledger,job,terminal=True,hostname='node')
    for key,value in [('run_count',2),('exec_host','other/0'),('Exit_status',1),('Submit_arguments','wrong')]:
        changed=deepcopy(job);changed[key]=value
        with pytest.raises(ValueError):r.check_pbs(ledger,changed,terminal=True,hostname='node')


def test_requires_pbs_before_read(tmp_path,monkeypatch):
    monkeypatch.delenv('PBS_JOBID',raising=False)
    with pytest.raises(ValueError):r.run(tmp_path)
    assert not list(tmp_path.iterdir())


def test_actual_spawned_tasks_match_serial_science(tmp_path,monkeypatch):
    for key,value in r.THREADS.items():monkeypatch.setenv(key,value)
    plan,task=small_plan('mc');tasks=[task,(*task[:3],1)]
    serial=c.parallel_map(r.run_task,[(str(tmp_path/'serial'),plan,item) for item in tasks],1)
    parallel=c.parallel_map(r.run_task,[(str(tmp_path/'parallel'),plan,item) for item in tasks],2)
    parallel.sort(key=lambda row:row['task'])
    for first,second in zip(serial,parallel):
        for key in ('task','role','seed','problem_hash','metadata','trials','failures','estimate','interval','decoder_prior'):
            assert first[key]==second[key]


def test_combination_and_block_use_fixed_allocations(tmp_path,monkeypatch):
    for key,value in r.THREADS.items():monkeypatch.setenv(key,value)
    plan,task=small_plan();cfg=plan['rows'][0]['condition']
    cfg.update(init='logical_combination',method='block',block=2)
    record=r.run_task((str(tmp_path),plan,task))
    arrays,saved=c.load_artifact(tmp_path/'tasks'/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
    assert record['status']=='ok' and record['bootstrap_rng_consumed']
    assert all(entry['initialization_rng_consumed'] for entry in record['chains'])
    r.validate_record(plan,task,arrays,saved)


def test_huge_mc_budget_passed_unchanged_and_failure_cost_saved(tmp_path,monkeypatch):
    plan,task=small_plan('mc');huge=10**80;plan['rows'][0]['mc_budget']['trials']=huge;seen=[]
    def stop(*args,**kwargs):
        seen.append(kwargs['trials']);raise OverflowError('fixture API limit')
    monkeypatch.setattr(r.qec,'direct_mc',stop)
    record=r.run_task((str(tmp_path),plan,task))
    assert seen==[huge] and record['status']=='failed' and record['task_wall_seconds']>0
    assert plan['rows'][0]['mc_budget']['trials']==huge

