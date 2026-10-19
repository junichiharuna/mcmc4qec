"""Fixed-cohort statistics must retain unavailable and flagged replicates."""
import math
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_summary as s


def row(rep, estimate=.2, interval=(.15,.25), **kwargs):
    return dict(replicate=rep, estimate=estimate, interval=interval,
                available=interval is not None, flagged=False, undefined=False,
                high_rhat=False, low_ess=False, failure=None, **kwargs)


def test_missing_interval_and_diagnostics_stay_in_denominator():
    rows=[row(0),row(1,.3,None),row(2)]
    rows[0].update(flagged=True, undefined=True)
    ref=dict(estimate=.2,interval_999=[.18,.22],standard_error=.006)
    out=s.summarize_condition(rows,3,ref)
    assert out["replicates"]==3
    assert out["covered_reference_point"]==2
    assert out["coverage_reference_point"]==pytest.approx(2/3)
    assert out["unavailable_intervals"]==1
    assert out["undefined"]==1 and out["flagged"]==1
    assert out["bias"]==pytest.approx(.1/3)
    assert out["rmse"]==pytest.approx(math.sqrt(.01/3))
    assert out["bias_reference_range"]==pytest.approx([.7/3-.22,.7/3-.18])


def test_missing_point_does_not_turn_available_subset_into_full_rmse():
    rows=[row(0,.2),row(1,None,None)]
    out=s.summarize_condition(rows,2,dict(estimate=.2,interval_999=[.18,.22],standard_error=.006))
    assert out["point_estimates"]==1
    assert out["bias"] is None and out["rmse"] is None
    assert out["available_only_bias"]==0 and out["available_only_rmse"]==0
    assert out["coverage_reference_point"]==.5


def test_duplicate_missing_and_nonfinite_replicates_rejected():
    ref=dict(estimate=.2,interval_999=[.18,.22],standard_error=.006)
    for rows in ([row(0),row(0)],[row(0)],[row(0),row(1,float('nan'))]):
        with pytest.raises(ValueError):
            s.summarize_condition(rows,2,ref)


def test_rmse_reference_range_can_have_interior_minimum():
    out=s.summarize_condition([row(0,.18),row(1,.22)],2,
                             dict(estimate=.2,interval_999=[.17,.24],standard_error=.01))
    assert out["rmse_reference_range"]==pytest.approx([.02,math.sqrt(.002)])


def test_artifact_aggregation_requires_every_condition_and_keeps_failures(tmp_path):
    import calibration as c
    plan=dict(replicates=2,cases=[dict(chains=4,windows=[32])],kernels={"ZH":{}},
              initializations=["logical"],burns=[0],blocks=[4])
    reference=dict(case=0,estimate=.2,interval_999=[.18,.22],standard_error=.006)
    c.atomic_json(tmp_path/"reference_summary.json",dict(records=[reference]))
    context=dict(sampling_manifest=c.digest(plan),references=[reference],
                 reference_summary_sha256=c.file_hash(tmp_path/"reference_summary.json"))
    c.atomic_json(tmp_path/"manifest.json",plan)
    c.atomic_json(tmp_path/"analysis_manifest.json",context)
    for rep in range(2):
        group=[0,0,0,rep]
        rows=[]
        for key in s.expected_conditions(plan,0,"ZH","logical"):
            entry=row(rep,estimate=.2 if rep==0 else None,interval=(.15,.25) if rep==0 else None)
            rows.append(dict(entry,group=group,**dict(zip(s.CONDITION,key))))
        c.save_artifact(tmp_path/"analysis"/c.task_id(group),dict(analysis=c.digest(context),group=group),{},
                        dict(status="ok",group=group,rows=rows))
    out=s.summarize(tmp_path,0)
    assert out["conditions"]==4
    assert all(r["replicates"]==2 and r["bias"] is None and r["coverage_reference_point"]==.5 for r in out["records"])
    assert len((tmp_path/"rows-0.jsonl").read_text().splitlines())==8
    # A row omitted by analysis is incomplete output, not an unavailable interval.
    rows.pop()
    c.save_artifact(tmp_path/"analysis"/c.task_id(group),dict(analysis=c.digest(context),group=group),{},
                    dict(status="ok",group=group,rows=rows))
    with pytest.raises(ValueError,match="omitted"):
        s.summarize(tmp_path,0)
