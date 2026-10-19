"""Independent pilot-only allocation with bounded, explicit per-layer budgets."""
from copy import deepcopy
import math
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
from test_tile_weight_reference_driver import inputs
import calibration as c
import tile_weight_allocation as a
import tile_weight_reference_driver as d
import tile_weight_stratified as w


def test_tail_cut_is_minimal_and_includes_zero_without_distance_assumptions():
    for n,p in ((5,.2),(72,.001),(288,.05)):
        end,masses,tail=a.tail_cut(n,p,1e-14)
        assert tail==pytest.approx(math.fsum(masses[end+1:]),abs=1e-28)
        assert tail<=1e-14
        if end>0:
            assert math.fsum(masses[end:])>1e-14
        assert math.fsum(masses)==pytest.approx(1.,abs=1e-12)


def test_cost_weighted_allocation_ratio_and_zero_failure_floor():
    # Equal B,v: optimal N ratio is sqrt(c2/c1)=2; no rounding is used here.
    raw=a.ideal_mc_trials([.2,.2],[.25,.25],[1.,4.],300.)
    assert raw==pytest.approx([100.,50.])
    assert sum(n*c for n,c in zip(raw,[1.,4.]))==pytest.approx(300.)
    assert a.round_trials(0.,4096,4194304,4096)==4096
    assert a.round_trials(4097.,4096,4194304,4096)==8192
    assert a.round_trials(1e100,4096,4194304,4096)==4194304


def test_all_sixteen_conditions_are_reproducible_and_match_driver():
    allocation,pilot,audit,profile,fixture=inputs()
    result=a.make_allocation(pilot,audit,profile)
    assert result==a.make_allocation(pilot,audit,profile)
    assert result["pilot_audit_digest"]==c.digest(audit)
    assert result["platform_profile_digest"]==c.digest(profile)
    assert result["planner_sha256"]==c.file_hash(a.__file__)
    context=d.make_context(result,pilot,audit,profile,fixture)
    assert len(context["reference"]["conditions"])==16
    for condition,report in zip(result["conditions"],result["allocation_report"]):
        case=condition["case"]
        size,noise=pilot["cases"][case]
        n=2*size*size
        layers=condition["layers"]
        assert [row["w"] for row in layers]==list(range(report["w_max"]+1))
        enum_last={0:4,1:3,2:3,3:2}[case]
        assert max(row["w"] for row in layers if row["mode"]=="enum")==min(enum_last,report["w_max"])
        for row in layers:
            count=w.class_size(n,row["w"],noise)
            if row["mode"]=="enum":
                assert row["trials"]==count<=4000000
            else:
                assert count>4000000
                assert 4096<=row["trials"]<=4194304 and row["trials"]%4096==0
        assert report["omitted_mass_upper"]<=1e-14
        assert report["planned_worker_seconds"]>0
        assert report["pilot_observed_partial_sum"]==0. # Synthetic fixture has no failures.
    assert result["allocation_report"][0]["unmeasured_weights"]


def test_unmeasured_layer_uses_worst_positive_cost_and_maximum_variance():
    _,pilot,audit,_,_=inputs()
    rows=[row for row in audit["strata"] if row["case"]==0 and row["prior_index"]==0]
    for row in rows:
        row["task_wall_seconds_max"]=100. if row["w"]==0 else 2.
    cost,variance,observed=a.layer_design(rows,9,pilot["samples"])
    assert cost==2/512 and variance==.25 and observed is False
    cost,variance,observed=a.layer_design(rows,1,pilot["samples"])
    smooth=.5/4097
    assert variance==pytest.approx(smooth*(1-smooth)) and observed is True


def test_missing_or_altered_pilot_rejected_before_allocation():
    _,pilot,audit,profile,_=inputs()
    for change in ("missing","not_ready","count"):
        altered=deepcopy(audit)
        if change=="missing":
            altered["strata"].pop()
        elif change=="not_ready":
            altered["allocation_ready"]=False
        else:
            altered["strata"][0]["failures_available"]=100
        with pytest.raises(ValueError):
            a.make_allocation(pilot,altered,profile)
