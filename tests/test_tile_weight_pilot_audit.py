"""Audit pilot allocation inputs, including failed tasks and state provenance."""
import copy
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("scipy")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_study as t
import tile_weight_stratified as w
import audit_tile_weight_pilot as a


def fixture_records():
    plan=dict(purpose="weight_stratified_pilot",schema=1,cases=[[6,"bit"]],
              priors=[[.01]],weights=[0,2],replicates=2,samples=5,decoder=t.SETTINGS)
    records=[]
    arrays=[]
    for task in a.expected_tasks(plan):
        case,prior,weight_index,rep=task
        weight=plan["weights"][weight_index]
        trials=1 if weight==0 else plan["samples"]
        seed=t.seed((110,*task),0)
        states=w.draw_patterns(72,weight,"bit",trials,np.random.default_rng(seed))
        failure=(states[:,0]!=0)
        records.append(dict(task=list(task),status="ok",case=case,n=72,noise="bit",
                            physical_decoder_prior=.01,sector_prior=.01,w=weight,seed=seed,
                            trials=trials,failures=int(failure.sum()),failure_mismatches=0,
                            checked_public_states=min(16,trials),problem_hash="fixture",
                            wall_seconds=2.,peak_rss_mb=64.))
        arrays.append(dict(states=states,failure=failure))
    return plan,records,arrays


def summarize(plan,records,arrays):
    return a.aggregate(plan,list(zip(arrays,records)),{(0,0):(72,"fixture")})


def test_complete_raw_layers_and_failed_tasks_remain_explicit():
    plan,records,arrays=fixture_records()
    result=summarize(plan,records,arrays)
    assert result["allocation_ready"] and result["expected_tasks"]==4
    assert result["trials"]==12 and result["failed_tasks"]==[]
    assert len(result["strata"])==2
    zero,two=result["strata"]
    assert zero["pattern_count"]==1 and zero["duplicate_states"]==1
    assert two["pattern_count"]==2556 and two["trials_available"]==10
    assert two["task_wall_seconds_mean"]==2
    assert "logical_error_rate" not in result
    records[-1]=dict(task=records[-1]["task"],status="failed",error="fixed task failed",
                     wall_seconds=3.,peak_rss_mb=64.)
    arrays[-1]={}
    result=summarize(plan,records,arrays)
    assert not result["allocation_ready"]
    assert result["failed_tasks"]==[records[-1]]
    assert result["strata"][1]["expected_replicates"]==2
    assert result["strata"][1]["success_replicates"]==1
    assert result["strata"][1]["failure_rate"] is None
    assert result["strata"][1]["failure_rate_available_only"] is not None


@pytest.mark.parametrize("mutation",["missing","duplicate","seed","prior","count","weight","draw","contradiction"])
def test_reject_incomplete_or_inconsistent_pilot(mutation):
    plan,records,arrays=fixture_records()
    if mutation=="missing":
        records.pop(); arrays.pop()
    elif mutation=="duplicate":
        records[-1]=copy.deepcopy(records[-2]); arrays[-1]=arrays[-2]
    elif mutation=="seed":
        records[-1]["seed"]+=1
    elif mutation=="prior":
        records[-1]["physical_decoder_prior"]*=2
    elif mutation=="count":
        records[-1]["failures"]+=1
    elif mutation=="weight":
        arrays[-1]["states"][0]=0
    elif mutation=="draw":
        arrays[-1]["states"]=np.roll(arrays[-1]["states"],1,axis=1)
    else:
        # All weight-zero samples are identical, with conflicting outcomes.
        arrays[1]["failure"][0]=True
        records[1]["failures"]=1
    with pytest.raises(ValueError):
        summarize(plan,records,arrays)


def test_checked_artifact_roundtrip_and_corruption(tmp_path):
    plan,records,arrays=fixture_records()
    for raw,record in zip(arrays,records):
        identity=dict(manifest=c.digest(plan),task=record["task"])
        c.save_artifact(tmp_path/"layers"/c.task_id(record["task"]),identity,raw,record)
    result=a.aggregate(plan,a.load_inputs(tmp_path,plan),{(0,0):(72,"fixture")})
    assert result["allocation_ready"]
    path=tmp_path/"layers"/f"{c.task_id(records[0]['task'])}.json"
    path.write_text("{}")
    with pytest.raises(ValueError,match="checksum mismatch"):
        a.aggregate(plan,a.load_inputs(tmp_path,plan),{(0,0):(72,"fixture")})


def test_real_pilot_records_match_seed_and_fixed_problem(tmp_path):
    pytest.importorskip("ldpc")
    import tile_weight_pilot as p
    plan=p.make_plan()
    plan.update(cases=[[6,"bit"],[6,"depolarizing"]],priors=[[.01],[.01]],
                weights=[0,2],replicates=1,samples=8)
    models={}
    for case,(size,noise) in enumerate(plan["cases"]):
        code,problem=t.build_problem(size,noise,.01)
        models[(case,0)]=(code.n,c.digest(problem.metadata()))
    for task in a.expected_tasks(plan):
        assert p.run_task((tmp_path,plan,task))["status"]=="ok"
    result=a.aggregate(plan,a.load_inputs(tmp_path,plan),models)
    assert result["allocation_ready"] and result["trials"]==18
    assert len(result["strata"])==4
