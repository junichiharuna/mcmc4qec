"""Relative RMSE ranges use the full cohort and vary the denominator too."""
import json
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_summary as s
import tile_precision_assessment as p


def row(rep,estimate,interval=None,**updates):
    return dict(replicate=rep,estimate=estimate,interval=interval,available=interval is not None,
                flagged=False,undefined=False,high_rhat=False,low_ess=False,failure=None,**updates)


def ref(point=.2,lo=.17,hi=.24):
    return dict(estimate=point,interval_999=[lo,hi],standard_error=.01)


def test_relative_minimum_is_second_moment_over_mean_not_absolute_minimum():
    result=p.assess_condition([row(0,.18),row(1,.22)],2,ref(),(.1,.2))
    assert result["relative_rmse_reference_point"]==pytest.approx(.1)
    optimum=(.18**2+.22**2)/(.18+.22)
    assert result["relative_rmse_minimizer"]==pytest.approx(.202)
    assert result["relative_rmse_reference_range"][0]==pytest.approx(math.sqrt(sum((x/optimum-1)**2 for x in (.18,.22))/2))
    endpoints=[math.sqrt(sum((x/t-1)**2 for x in (.18,.22))/2) for t in (.17,.24)]
    assert result["relative_rmse_reference_range"][1]==pytest.approx(max(endpoints))
    assert result["precision"][0]["classification"]=="reference_sensitive"


@pytest.mark.parametrize("scale",[1.,1e-150,1e-300])
def test_scale_invariance_without_second_moment_underflow(scale):
    result=p.assess_condition([row(0,.18*scale),row(1,.22*scale)],2,ref(.2*scale,.17*scale,.24*scale),(.2,))
    baseline=p.assess_condition([row(0,.18),row(1,.22)],2,ref(),(.2,))
    assert result["relative_rmse_reference_range"]==pytest.approx(baseline["relative_rmse_reference_range"])
    assert result["relative_rmse_minimizer"]/scale==pytest.approx(.202)


def test_missing_points_never_pass_using_available_subset():
    result=p.assess_condition([row(0,.2),row(1,None)],2,ref(.2,.19,.21),(.2,))
    assert result["metrics"]["point_estimates"]==1
    assert result["relative_rmse_reference_point"] is None and result["relative_rmse_reference_range"] is None
    assert result["precision"][0]["classification"]=="incomplete_points"


def test_undefined_diagnostics_and_missing_intervals_are_not_filtered():
    rows=[row(0,.2),row(1,.2,interval=(.19,.21))]
    rows[0].update(flagged=True,undefined=True)
    result=p.assess_condition(rows,2,ref(.2,.199,.201),(.1,))
    assert result["precision"][0]["classification"]=="empirical_within_target"
    assert result["metrics"]["unavailable_intervals"]==1 and result["metrics"]["undefined"]==1
    assert result["metrics"]["coverage_reference_point"]==.5
    assert not result["population_rmse_certified"] and not result["nominal_coverage_certified"]


def test_zero_estimates_and_zero_reference_boundary_are_distinct():
    result=p.assess_condition([row(0,0.),row(1,0.)],2,ref(),(.2,))
    assert result["relative_rmse_reference_range"]==[1.,1.]
    assert result["precision"][0]["classification"]=="empirical_above_target"
    boundary=p.assess_condition([row(0,0.),row(1,0.)],2,ref(0.,0.,.01),(.2,))
    assert boundary["relative_rmse_reference_range"] is None
    assert boundary["precision"][0]["classification"]=="reference_zero_boundary"


@pytest.mark.parametrize("reference",[ref(.2,.3,.4),ref(.2,-.1,.4),ref(float('nan'),.1,.3)])
def test_invalid_reference_rejected(reference):
    with pytest.raises(ValueError):p.assess_condition([row(0,.2)],1,reference,(.2,))


def test_duplicate_replicate_and_invalid_threshold_rejected():
    with pytest.raises(ValueError):p.assess_condition([row(0,.2),row(0,.2)],2,ref(),(.2,))
    for thresholds in ((0.,),(.2,.2),(float('nan'),)):
        with pytest.raises(ValueError):p.assess_condition([row(0,.2)],1,ref(),thresholds)


def test_floating_overflow_is_recorded_without_nonfinite_json():
    result=p.assess_condition([row(0,1.)],1,ref(1e-320,1e-320,1e-319),(.2,))
    assert result["precision"][0]["classification"]=="numerical_range"
    c.canonical(result)


def make_artifacts(root):
    plan=dict(replicates=2,cases=[dict(chains=4,windows=[32],target=.03)],kernels={"ZH":{}},initializations=["logical"],burns=[0],blocks=[4])
    reference=dict(ref(.2,.19,.21),case=0,target_p=.03)
    c.atomic_json(root/"reference_summary.json",dict(records=[reference]))
    context=dict(sampling_manifest=c.digest(plan),references=[reference],reference_summary_sha256=c.file_hash(root/"reference_summary.json"))
    c.atomic_json(root/"manifest.json",plan)
    c.atomic_json(root/"analysis_manifest.json",context)
    for rep in range(2):
        group=[0,0,0,rep]
        rows=[dict(row(rep,.2,interval=(.18,.22)),group=group,**dict(zip(s.CONDITION,key))) for key in s.expected_conditions(plan,0,"ZH","logical")]
        c.save_artifact(root/"analysis"/c.task_id(group),dict(analysis=c.digest(context),group=group),{},dict(status="ok",group=group,rows=rows))
    s.summarize(root,0)


def test_complete_persisted_cohort_and_tamper_refusal(tmp_path):
    make_artifacts(tmp_path)
    result=p.assess_calibration(tmp_path,0)
    assert result["conditions"]==4
    assert all(record["assessment"]["precision"][0]["classification"]=="empirical_within_target" for record in result["records"])
    with (tmp_path/"rows-0.jsonl").open("ab") as stream:stream.write(b"\n")
    with pytest.raises(ValueError,match="hash"):p.assess_calibration(tmp_path,0)


def test_mixed_summary_cannot_certify_raw_rows(tmp_path):
    make_artifacts(tmp_path)
    path=tmp_path/"summary-0.json"
    summary=json.loads(path.read_text())
    summary["records"][0]["rmse"]=.1
    c.atomic_json(path,summary)
    with pytest.raises(ValueError,match="summary"):p.assess_calibration(tmp_path,0)
