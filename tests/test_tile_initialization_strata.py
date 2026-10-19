"""Initialization strata cannot hide failures or substitute for the full cohort."""
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_initialization_strata as s
import tile_summary as base
import tile_study as t
import tile_bar_study as b


REF=dict(estimate=.2,standard_error=.006,interval_999=[.18,.22])


def rows():
    return [dict(replicate=rep,estimate=.1 if rep%2==0 else .3,
                 interval=[.09,.11] if rep%2==0 else [.29,.31],available=True,
                 failure=None,flagged=False,undefined=False,high_rhat=False,low_ess=False) for rep in range(4)]


def test_opposite_initialization_biases_are_not_hidden_by_pooled_mean():
    out=s.summarize_strata(rows(),4,REF,"logical",4)
    assert out["primary"]["bias"]==pytest.approx(0)
    assert out["primary"]["rmse"]==pytest.approx(.1)
    x,z=out["strata"]
    assert x["label"]=="logical_X_basis" and z["label"]=="logical_Z_basis"
    assert x["original_replicate_ids"]==[0,2] and z["original_replicate_ids"]==[1,3]
    assert x["statistics"]["bias"]==pytest.approx(-.1)
    assert z["statistics"]["bias"]==pytest.approx(.1)
    assert x["basis_indices"]==[0,1,2,3] and z["basis_indices"]==[8,9,10,11]


def test_failed_seed_stays_in_both_primary_and_its_stratum():
    data=rows()
    data[2].update(estimate=None,interval=None,available=False,failure="sampling_failed",flagged=True,undefined=True)
    out=s.summarize_strata(data,4,REF,"logical",8)
    assert out["primary"]["replicates"]==4 and out["primary"]["bias"] is None
    x=out["strata"][0]["statistics"]
    assert x["replicates"]==2 and x["point_estimates"]==1 and x["bias"] is None
    assert x["unavailable_intervals"]==1 and x["undefined"]==1
    assert x["failures"]==dict(sampling_failed=1)


def test_rejection_parity_control_is_not_labelled_as_logical_start():
    out=s.summarize_strata(rows(),4,REF,"rejection",8)
    assert [x["label"] for x in out["strata"]]==["rejection_even","rejection_odd"]
    assert all(x["basis_indices"] is None for x in out["strata"])
    for bad in (rows()[:-1],[rows()[0]]*4):
        with pytest.raises(ValueError):
            s.summarize_strata(bad,4,REF,"logical",8)


@pytest.mark.parametrize("size",[6,12])
def test_basis_indices_match_actual_fixed_initializer(size):
    pytest.importorskip("ldpc")
    code,problem=t.build_problem(size,"depolarizing",.03 if size==6 else .05)
    basis=np.concatenate((code.lx,3*code.lz))
    for rep in range(3):
        indices=s.basis_indices(rep,8)
        for chain,index in enumerate(indices):
            state,_=t.initial_state(code,problem,.05,"depolarizing","logical",rep*8+chain,np.random.default_rng(1),10)
            assert np.array_equal(state,basis[index])
            expected=np.eye(16,dtype=np.uint8)[index]
            assert np.array_equal(problem.model.observables(state),expected)


def test_file_pipeline_reproduces_primary_summary_and_rejects_changes(tmp_path):
    plan=dict(replicates=4,cases=[{}, {},dict(size=6,noise="depolarizing",chains=8,windows=[32])],
              kernels={"ZH":{},"ZHS":{}},initializations=["logical","rejection"],burns=[0],blocks=[4],
              runtime=dict(tile_driver_sha256=c.file_hash(t.__file__),bar_sampler_sha256=c.file_hash(b.__file__)))
    reference=dict(case=2,**REF)
    c.atomic_json(tmp_path/"manifest.json",plan)
    c.atomic_json(tmp_path/"reference_summary.json",dict(records=[reference]))
    context=dict(sampling_manifest=c.digest(plan),references=[reference],reference_summary_sha256=c.file_hash(tmp_path/"reference_summary.json"))
    c.atomic_json(tmp_path/"analysis_manifest.json",context)
    entries=[]
    summaries=[]
    for kernel,initial in itertools.product(plan["kernels"],plan["initializations"]):
        for key in base.expected_conditions(plan,2,kernel,initial):
            condition=dict(zip(base.CONDITION,key))
            data=[dict(row,**condition) for row in rows()]
            entries.extend(data)
            summaries.append(dict(condition,**base.summarize_condition(data,4,reference)))
    raw=tmp_path/"rows-2.jsonl"
    raw.write_bytes(b"".join(c.canonical(row)+b"\n" for row in entries))
    summary=dict(case=2,analysis=c.digest(context),raw_rows_sha256=c.file_hash(raw),records=summaries)
    c.atomic_json(tmp_path/"summary-2.json",summary)
    out=s.run(tmp_path,2,tmp_path/"strata.json")
    assert out["primary_summaries_reproduced"] and out["conditions"]==32
    assert all(sum(len(g["original_replicate_ids"]) for g in x["strata"])==4 for x in out["records"])
    summary["records"][0]["bias"]=.123
    c.atomic_json(tmp_path/"summary-2.json",summary)
    with pytest.raises(ValueError,match="primary summary"):
        s.run(tmp_path,2,tmp_path/"bad.json")
