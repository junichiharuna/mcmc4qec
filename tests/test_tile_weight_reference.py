"""Fixed independent strata: exact chunk coverage, raw provenance and failed cohorts."""
from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_study as t
import tile_weight_stratified as w
import tile_weight_reference as r


def plan(case=0):
    return r.make_plan([dict(case=case,physical_decoder_prior=.01,layers=[
        dict(w=0,mode="enum",trials=1),dict(w=1,mode="mc",trials=11),dict(w=2,mode="mc",trials=6)])],
        pilot_audit_digest="a"*64,platform_profile_digest="b"*64,chunk_size=4)


def test_fixed_chunk_partition_seed_namespace_and_invalid_enumeration():
    p=plan()
    tasks=list(r.tasks(p,0))
    assert tasks==[(0,0,0),(0,1,0),(0,1,1),(0,1,2),(0,2,0),(0,2,1)]
    specs=[r.chunk_spec(p,task) for task in tasks]
    assert [(s["start"],s["stop"]) for s in specs[1:4]]==[(0,4),(4,8),(8,11)]
    assert specs[0]["seed"] is None
    assert specs[1]["seed"]==t.seed((130,0,1,0),0)
    assert specs[1]["seed"]!=t.seed((110,0,1,0),0)
    conditions=deepcopy(p["conditions"])
    conditions[0]["layers"][1]["mode"]="enum"
    with pytest.raises(ValueError,match="enumeration"):
        r.make_plan(conditions,pilot_audit_digest="a"*64,platform_profile_digest="b"*64)
    conditions[0]["layers"]=conditions[0]["layers"][1:]
    with pytest.raises(ValueError):
        r.make_plan(conditions,pilot_audit_digest="a"*64,platform_profile_digest="b"*64)


@pytest.mark.parametrize("case",range(4))
def test_actual_small_raw_chunks_reproduce_stratified_sum(tmp_path,case):
    p=plan(case)
    inputs=[]
    for task in r.tasks(p,0):
        record=r.run_chunk((tmp_path,p,task))
        assert record["status"]=="ok"
        assert r.run_chunk((tmp_path,p,task))==record
        inputs.append(c.load_artifact(tmp_path/"chunks"/c.task_id(task),dict(manifest=c.digest(p),task=list(task))))
    output=r.aggregate_condition(p,0,inputs)
    assert output["available"] and output["failed_chunks"]==[]
    assert output["planned_trials"]==18
    manual=[dict(layer,failures=sum(record["failures"] for _,record in inputs if record["w"]==layer["w"]))
            for layer in p["conditions"][0]["layers"]]
    size,noise=t.CASES[case]
    expected=w.synthesize(2*size*size,noise,.01,manual)
    assert output["reference"]==expected
    import tile_weight_reference_comparison as comparison
    row=dict(replicate=0,estimate=None,interval=None,available=False,
             flagged=True,undefined=True,high_rhat=False,low_ess=False,failure="unavailable")
    compared=comparison.compare_condition([row],1,output,case=case,target_prior=.01)
    assert compared["reference"]["interval"]==expected["interval"]
    assert compared["assessment"]["metrics"]["point_estimates"]==0
    for altered in (inputs[:-1],inputs+[inputs[-1]],list(reversed(inputs))):
        with pytest.raises(ValueError):
            r.aggregate_condition(p,0,altered)
    for key in ("seed","physical_decoder_prior","failures"):
        bad=deepcopy(inputs)
        bad[1][1][key]+=1
        with pytest.raises(ValueError):
            r.aggregate_condition(p,0,bad)
    bad=deepcopy(inputs)
    bad[1][0]["states"][0]=np.roll(bad[1][0]["states"][0],1)
    with pytest.raises(ValueError):
        r.aggregate_condition(p,0,bad)
    failed=deepcopy(inputs)
    failed[1]=(dict(),dict(failed[1][1],status="failed",error="deliberate failure"))
    output=r.aggregate_condition(p,0,failed)
    assert not output["available"] and output["reference"] is None
    assert output["failed_chunks"]==[[0,1,0]] and output["planned_trials"]==18


def test_full_small_enumeration_chunks_cover_layer_exactly(tmp_path):
    p=r.make_plan([dict(case=0,physical_decoder_prior=.01,layers=[dict(w=0,mode="enum",trials=1),dict(w=1,mode="enum",trials=72)])],
        pilot_audit_digest="a"*64,platform_profile_digest="b"*64,chunk_size=32)
    inputs=[]
    for task in r.tasks(p,0):
        r.run_chunk((tmp_path,p,task))
        inputs.append(c.load_artifact(tmp_path/"chunks"/c.task_id(task),dict(manifest=c.digest(p),task=list(task))))
    states=np.concatenate([arrays["states"] for arrays,record in inputs if record["w"]==1])
    assert np.array_equal(states,np.stack(list(w.enum_patterns(72,1,"bit"))))
    result=r.aggregate_condition(p,0,inputs)
    assert result["reference"]["mc_standard_error_plugin"]==0
    assert result["reference"]["omitted_mass_upper"]>0


def test_failed_chunk_is_recorded_and_not_replaced_by_a_new_draw(tmp_path,monkeypatch):
    p=plan()
    calls=[]
    def fail(*args,**kwargs):
        calls.append(1)
        raise ValueError("deliberate decoder failure")
    monkeypatch.setattr(r.t,"compact",fail)
    task=(0,1,0)
    record=r.run_chunk((tmp_path,p,task))
    assert record["status"]=="failed" and "deliberate" in record["error"]
    assert r.run_chunk((tmp_path,p,task))==record and len(calls)==1
