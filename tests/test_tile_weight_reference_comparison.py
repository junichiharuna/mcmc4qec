"""Interval references must never silently become full point references."""
import copy
import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import tile_weight_reference_comparison as compare
import tile_weight_stratified as w


def row(rep, value=.2, interval=(.1, .3)):
    return dict(replicate=rep, estimate=value, interval=interval,
                available=interval is not None, flagged=False, undefined=False,
                high_rhat=False, low_ess=False, failure=None)


def condition():
    reference=w.synthesize(72, "bit", .01, [
        dict(w=0, mode="enum", trials=1, failures=0),
        dict(w=1, mode="enum", trials=72, failures=1)])
    return dict(condition=0, case=0, physical_decoder_prior=.01,
                chunks=2, failed_chunks=[], planned_trials=73, available_trials=73,
                available=True, reference=reference)


def test_full_small_enumeration_matches_known_probability():
    p=.2
    strata=[dict(w=k, mode="enum", trials=math.comb(3,k),
                 failures=math.comb(3,k) if k>=2 else 0) for k in range(4)]
    reference=w.synthesize(3,"bit",p,strata)
    exact=3*p*p*(1-p)+p**3
    out=compare.assess_bounds([row(0,.1),row(1,.2)],2,reference["interval"])
    assert out["metrics"]["bias_reference_range"]==pytest.approx([.15-exact]*2)
    expected=math.sqrt(((.1-exact)**2+(.2-exact)**2)/2)
    assert out["metrics"]["rmse_reference_range"]==pytest.approx([expected]*2)
    assert out["reference_point"] is None
    for key in ("bias","rmse","reference","coverage_reference_point","available_only_bias"):
        assert key not in out["metrics"]


def test_unknown_tail_is_not_zero_failure_reference():
    reference=w.synthesize(3,"bit",.2,[dict(w=0,mode="enum",trials=1,failures=0)])
    assert reference["partial_estimate"]==0
    out=compare.assess_bounds([row(0,.1)],1,reference["interval"])
    assert out["relative_rmse_reference_range"] is None
    assert all(x["classification"]=="reference_zero_boundary" for x in out["precision"])
    assert out["metrics"]["coverage_reference_entire"]==0
    assert out["metrics"]["coverage_reference_possible"]==1


def test_range_extrema_match_independent_grid():
    values=np.array([.12,.24,.3])
    out=compare.assess_bounds([row(i,float(x)) for i,x in enumerate(values)],3,[.1,.4])
    grid=np.linspace(.1,.4,20001)
    absolute=np.sqrt(((values[:,None]-grid)**2).mean(axis=0))
    relative=np.sqrt(((values[:,None]/grid-1)**2).mean(axis=0))
    assert out["metrics"]["rmse_reference_range"]==pytest.approx([absolute.min(),absolute.max()],abs=1e-8)
    assert out["relative_rmse_reference_range"]==pytest.approx([relative.min(),relative.max()],abs=1e-8)
    assert .1<out["relative_rmse_minimizer"]<.4


@pytest.mark.parametrize("missing_all",[False,True])
def test_unavailable_points_keep_full_denominator(missing_all):
    rows=[row(0,None,None),row(1,None if missing_all else .2,None)]
    rows[0].update(flagged=True,undefined=True,failure="initialization_failed")
    out=compare.assess_bounds(rows,2,[.15,.25])
    assert out["metrics"]["replicates"]==2
    assert out["metrics"]["unavailable_intervals"]==2
    assert out["metrics"]["undefined"]==1
    assert out["metrics"]["bias_reference_range"] is None
    assert out["relative_rmse_reference_range"] is None
    assert all(x["classification"]=="incomplete_points" for x in out["precision"])


def test_zero_mc_failures_keep_positive_bound():
    pytest.importorskip("scipy", reason="MC stratum confidence bounds require optional SciPy")
    ref=w.synthesize(3,"bit",.2,[dict(w=k,mode="mc",trials=8,failures=0) for k in range(4)])
    out=compare.assess_bounds([row(0,0,(0,0))],1,ref["interval"])
    assert ref["mc_standard_error_plugin"]==0 and ref["interval"][1]>0
    assert out["metrics"]["coverage_reference_entire"]==0
    assert out["population_rmse_certified"] is False


def test_condition_identity_and_explicit_partial_fields():
    item=condition()
    out=compare.compare_condition([row(0)],1,item,case=0,target_prior=.01)
    assert out["reference"]["partial_estimate"]==item["reference"]["partial_estimate"]
    assert out["reference"]["omitted_mass_upper"]>0
    assert out["reference"]["full_point_estimate"] is None
    assert out["raw_artifacts_audited"] is False
    assert out["assessment"]["reference_interval"]==item["reference"]["interval"]


@pytest.mark.parametrize("case,prior",[(1,.01),(0,.003)])
def test_different_case_or_prior_rejected(case,prior):
    with pytest.raises(ValueError,match="identity"):
        compare.compare_condition([row(0)],1,condition(),case=case,target_prior=prior)


@pytest.mark.parametrize("field",["partial_estimate","omitted_mass_upper","mc_standard_error_plugin"])
def test_changed_synthesis_rejected(field):
    item=condition()
    item["reference"][field]+=.001
    with pytest.raises(ValueError,match="synthesis"):
        compare.compare_condition([row(0)],1,item,case=0,target_prior=.01)


def test_count_mismatch_rejected():
    item=condition()
    item["available_trials"]-=1
    with pytest.raises(ValueError,match="trial"):
        compare.compare_condition([row(0)],1,item,case=0,target_prior=.01)


def test_unavailable_reference_keeps_diagnostics_without_metrics():
    item=condition()
    item.update(available=False,reference=None,failed_chunks=[dict(status="failed")],available_trials=1)
    out=compare.compare_condition([row(0)],1,item,case=0,target_prior=.01)["assessment"]
    assert out["metrics"]["point_estimates"]==1
    assert out["metrics"]["bias_reference_range"] is None
    assert out["metrics"]["coverage_reference_possible"] is None
    assert out["reference_interval"] is None
    assert all(x["classification"]=="reference_unavailable" for x in out["precision"])


@pytest.mark.parametrize("rows",[[row(0),row(0)],[row(0)]])
def test_duplicate_or_missing_replicates_rejected(rows):
    with pytest.raises(ValueError,match="replicate"):
        compare.assess_bounds(rows,2,[.1,.3])


@pytest.mark.parametrize("interval",[[-.1,.2],[.3,.1],[0,float("nan")]])
def test_invalid_bounds_rejected(interval):
    with pytest.raises(ValueError):
        compare.assess_bounds([row(0)],1,interval)


def test_finite_tiny_probabilities_are_not_rounded_to_zero():
    out=compare.assess_bounds([row(0,1e-120,(0,2e-120))],1,[.9e-120,1.1e-120])
    assert out["relative_rmse_reference_range"]==pytest.approx([0,1/9])


def test_inputs_not_modified():
    item=condition()
    before=copy.deepcopy(item)
    compare.compare_condition([row(0)],1,item,case=0,target_prior=.01)
    assert item==before
