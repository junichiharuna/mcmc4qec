"""Conditional-weight comparisons retain missing and undefined fixed replicates."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_weight_comparison as w


def row(rep,mean):
    return dict(replicate=rep,mean=mean,missing=mean is None,undefined=mean is None,
                flagged=mean is None,high_rhat=False,low_ess=False,
                iat_mcse=.1 if mean is not None else None,cross_chain_se=.2 if mean is not None else None)


def test_mean_uncertainty_and_reference_difference():
    out=w.compare([row(0,1.),row(1,3.)],2,dict(mean=1.5,chunk_delta_standard_error=.1))
    assert out["mean"]==2 and out["mean_difference_from_reference"]==.5
    assert out["replicate_mean_standard_error"]==1
    assert out["difference_standard_error"]==pytest.approx(1.01**.5)
    assert out["rmse_at_reference_point"]==pytest.approx(1.25**.5)


def test_missing_points_keep_full_denominator_and_undefined_diagnostics():
    rows=[row(0,2.),row(1,None)]
    rows[0].update(undefined=True,flagged=True,iat_mcse=None)
    out=w.compare(rows,2,dict(mean=2.,chunk_delta_standard_error=.1))
    assert out["replicates"]==2 and out["missing"]==1 and out["undefined"]==2
    assert out["mean"] is None and out["mean_difference_from_reference"] is None
    assert out["rmse_at_reference_point"] is None and out["difference_standard_error"] is None
    assert out["available_only_mean"]==2


@pytest.mark.parametrize("kind",["duplicate","absent","nan","negative_se"])
def test_invalid_cohort_is_not_a_successful_subset(kind):
    rows=[row(0,1.),row(1,2.)]
    if kind=="duplicate":rows[1]["replicate"]=0
    elif kind=="absent":rows.pop()
    elif kind=="nan":rows[0]["mean"]=float("nan")
    else:rows[0]["iat_mcse"]=-1
    with pytest.raises(ValueError):w.compare(rows,2,dict(mean=2.,chunk_delta_standard_error=.1))


def group_record(failed=False):
    diag=dict(chains=4,burn=600,samples=600,rung=1,p=.03,observable="weight",mean=4.2,
              chain_means=[4.,4.1,4.3,4.4],chain_iat=[1.,2.,3.,4.],chain_ess=[600.,300.,200.,150.],
              iat_mcse=.1,cross_chain_se=.2,rhat=1.,undefined=False,flagged=False,high_rhat=False,low_ess=False,
              sector_transitions=[3,4,5,6],unique_sectors=[2,3,4,5])
    return dict(status="ok",group=[0,0,0,0],diagnostics=[] if failed else [diag],diagnostic_count=0 if failed else 1,
                failed_tasks=[[0,0,0,0,1,0]] if failed else [])


def test_missing_diagnostic_requires_target_sampling_failure():
    spec=dict(chains=4,windows=[600],target=.03,rungs=[.1,.03],size=6)
    rows=w.group_rows(dict(burns=[600]),spec,group_record())
    assert len(rows)==1 and rows[0]["mean"]==4.2 and rows[0]["sector_transitions"]==[3,4,5,6]
    missing=group_record(True)
    assert w.group_rows(dict(burns=[600]),spec,missing)[0]["missing"]
    missing["failed_tasks"]=[]
    with pytest.raises(ValueError):w.group_rows(dict(burns=[600]),spec,missing)
    bad=group_record();bad["diagnostics"].append(deepcopy(bad["diagnostics"][0]));bad["diagnostic_count"]=2
    with pytest.raises(ValueError):w.group_rows(dict(burns=[600]),spec,bad)


def test_json_only_reader_checks_identity_and_metadata_hash(tmp_path):
    path=tmp_path/"group"
    identity=dict(analysis="a",group=[0,0,0,0])
    record=group_record()
    c.save_artifact(path,identity,{},record)
    assert w.read_metadata(path,identity)[0]==record
    path.with_suffix(".json").write_text("{}")
    with pytest.raises(ValueError):w.read_metadata(path,identity)
    c.save_artifact(path,identity,{},record)
    with pytest.raises(ValueError):w.read_metadata(path,dict(analysis="different"))
    path.with_suffix(".done.json").unlink()
    with pytest.raises(ValueError):w.read_metadata(path,identity)


def test_persisted_comparison_binds_reference_and_keeps_missing_replicate(tmp_path,monkeypatch):
    spec=dict(chains=4,windows=[600],target=.03,rungs=[.1,.03],size=6,noise="bit")
    plan=dict(cases=[spec],burns=[600],replicates=2,kernels={"ZH":{}},initializations=["logical"])
    reference=dict(case=0,size=6,noise="bit",target_p=.03,conditional_weight=4.)
    c.atomic_json(tmp_path/"manifest.json",plan)
    c.atomic_json(tmp_path/"reference_summary.json",dict(records=[reference]))
    context=dict(sampling_manifest=c.digest(plan),analysis_source_sha256=c.file_hash(w.a.__file__),
                 reference_summary_sha256=c.file_hash(tmp_path/"reference_summary.json"),references=[reference])
    c.atomic_json(tmp_path/"analysis_manifest.json",context)
    c.atomic_json(tmp_path/"analysis_summary-0.json",dict(analysis=c.digest(context),groups=2))
    audit=dict(summary_sha256=context["reference_summary_sha256"],all_problem_metadata_verified=True,
               all_seeds_verified=True,summary_reproduced=True,
               conditional_weight=[dict(case=0,mean=4.,chunk_delta_standard_error=.1)])
    c.atomic_json(tmp_path/"audit.json",audit)
    for rep in range(2):
        record=group_record(failed=rep==1)
        group=[0,0,0,rep];record["group"]=group
        record["failed_tasks"]=[group+[1,0]] if rep==1 else []
        c.save_artifact(tmp_path/"analysis"/c.task_id(group),dict(analysis=c.digest(context),group=group),{},record)
    monkeypatch.setattr(w.b,"make_plan",lambda:plan)
    result=w.run(tmp_path,0,tmp_path/"audit.json",tmp_path/"result.json")
    assert result["conditions"]==1 and result["records"][0]["missing"]==1
    assert result["records"][0]["mean"] is None and len(result["records"][0]["rows"])==2
    assert result["records"][0]["available_only_mean"]==4.2
    assert not result["acf_arrays_rechecked"] and not result["physical_traces_reaudited"]
    with pytest.raises(ValueError):w.run(tmp_path,0,tmp_path/"audit.json",tmp_path/"result.json")
    audit["conditional_weight"][0]["mean"]=5.
    c.atomic_json(tmp_path/"audit.json",audit)
    with pytest.raises(ValueError,match="reference identity"):w.run(tmp_path,0,tmp_path/"audit.json",tmp_path/"bad.json")
    assert not (tmp_path/"bad.json").exists()


def test_real_small_analysis_weight_matches_saved_target_traces(tmp_path):
    pytest.importorskip("ldpc")
    import numpy as np
    from test_tile_bar_analysis import test_finite_group_uses_all_expected_conditions
    test_finite_group_uses_all_expected_conditions(tmp_path)
    record=json.loads((tmp_path/"analysis/0-0-0-0.json").read_text())
    spec=dict(chains=4,windows=[32],target=.03,rungs=[.1,.03],size=6)
    rows=w.group_rows(dict(burns=[0]),spec,record)
    values=[]
    for chain in range(4):
        with np.load(tmp_path/f"traces/0-0-0-0-1-{chain}.npz",allow_pickle=False) as stored:
            values.extend(stored["weight"].tolist())
    assert len(rows)==1 and not rows[0]["missing"]
    assert rows[0]["mean"]==pytest.approx(float(np.mean(values)))
    compared=w.compare(rows,1,dict(mean=4.,chunk_delta_standard_error=.1))
    assert compared["mean_difference_from_reference"]==pytest.approx(float(np.mean(values))-4.)
    assert compared["replicate_mean_standard_error"] is None
