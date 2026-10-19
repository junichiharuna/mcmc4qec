"""Anchor count audit retains zero failures and failed fixed-budget tasks."""
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import audit_tile_anchors as a
import tile_study as t
from tile_reference import wilson


def fixture():
    plan=dict(replicates=3,anchor_trials=20,cases=[dict(rungs=[.1,.03],target=.03)])
    rows=[dict(case=0,replicate=rep,seed=t.seed((32,0,rep),0),status="ok",problem_hash="fixed",
               trials=20,failures=k,estimate=k/20,interval=wilson(k,20,.95),elapsed_seconds=1.)
          for rep,k in enumerate((0,10,20))]
    return plan,rows


def test_boundary_counts_and_independent_anchor_variance_are_preserved():
    plan,rows=fixture()
    out=a.audit_records(plan,0,rows,"fixed")
    assert out["replicates"]==3 and out["trials_available"]==60
    assert out["pooled_anchor_estimate_for_audit_only"]==.5
    assert out["zero_failure_replicates"]==[0]
    assert out["failed_replicates"]==[]
    assert out["anchor_log_standard_error_range_positive_counts"]==pytest.approx([0,math.sqrt(.05)])
    assert out["physical_sampling_p_from_pinned_source"]==.1
    assert out["physical_decoder_prior"]==.03
    rows[1]=dict(case=0,replicate=1,seed=rows[1]["seed"],status="failed",error="failed")
    out=a.audit_records(plan,0,rows,"fixed")
    assert out["replicates"]==3 and out["successful_replicates"]==2
    assert out["pooled_anchor_estimate_for_audit_only"] is None
    assert out["available_only_pooled_estimate"]==.5 and out["failed_replicates"]==[1]


@pytest.mark.parametrize("kind",["seed","prior","count","interval","missing","duplicate"])
def test_inconsistent_or_incomplete_anchor_cohort_rejected(kind):
    plan,rows=fixture()
    if kind=="seed":
        rows[0]["seed"]+=1
    elif kind=="prior":
        rows[0]["problem_hash"]="different decoder"
    elif kind=="count":
        rows[0]["failures"]+=1
    elif kind=="interval":
        rows[0]["interval"]=[.1,.2]
    elif kind=="missing":
        rows.pop()
    else:
        rows[-1]=rows[0]
    with pytest.raises(ValueError):
        a.audit_records(plan,0,rows,"fixed")
