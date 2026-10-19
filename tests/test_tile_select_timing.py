"""Fixed full-cohort selection is a candidate, not an accuracy certificate."""
from copy import deepcopy
import itertools
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_bar_study as b
import tile_precision_assessment as p
import tile_summary as s
import tile_select_timing as select
import tile_bar_time_benchmark as timing
from test_tile_precision_assessment import row,ref


def reports(plan,estimate=.2):
    assessment=p.assess_condition([row(i,estimate,interval=(.18,.22)) for i in range(192)],192,ref(.2,.199,.201))
    result=[]
    for case in range(4):
        records=[dict(condition=dict(zip(s.CONDITION,key)),assessment=assessment)
                 for kernel,initial in itertools.product(plan["kernels"],plan["initializations"])
                 for key in s.expected_conditions(plan,case,kernel,initial)]
        result.append(dict(case=case,replicates=192,conditions=len(records),records=records,input_sha256={"sampling":"a"*64}))
    return result


def test_complete_candidate_selection_is_order_invariant_and_consumable():
    plan=b.make_plan();data=reports(plan)
    settings=select.choose(plan,data)
    assert len(settings["records"])==8
    for selected in settings["records"]:
        cfg=selected["condition"]
        assert selected["status"]=="selected" and selected["eligible_conditions"]>0
        assert cfg["method"]=="cross_chain" and cfg["kernel"]=="ZH" and cfg["init"]=="logical"
        assert cfg["burn"]==600 and cfg["samples"]==600 and cfg["chains"]==4 and cfg["ladder"]=="coarse"
        assert not selected["precision_independently_confirmed"] and not selected["recommended"]
    shuffled=deepcopy(data)
    shuffled.reverse()
    for report in shuffled:report["records"].reverse()
    assert select.choose(plan,shuffled)["records"]==settings["records"]
    assert len(list(timing.tasks(timing.make_plan(settings,capacity=False))))==1536


def test_no_candidates_and_partial_points_are_not_success():
    plan=b.make_plan();data=reports(plan,.5)
    result=select.choose(plan,data)
    assert all(row["status"]=="unmet" and "condition" not in row for row in result["records"])
    data=reports(plan)
    bad=deepcopy(data[0]["records"][0]["assessment"])
    bad["metrics"]["point_estimates"]=191
    for report in data:
        for record in report["records"]:record["assessment"]=bad
    assert all(row["status"]=="unmet" for row in select.choose(plan,data)["records"])


def test_diagnostics_and_missing_intervals_are_retained():
    plan=b.make_plan();data=reports(plan)
    # All point estimates exist; interval and diagnostics are separate outcomes.
    assessment=data[0]["records"][0]["assessment"]
    assessment["metrics"].update(flagged=100,undefined=20,unavailable_intervals=3)
    result=select.choose(plan,data)
    assert result["records"][0]["calibration_assessment"]["metrics"]["undefined"]==20
    assert result["records"][0]["calibration_assessment"]["metrics"]["unavailable_intervals"]==3


@pytest.mark.parametrize("bad",["case","condition","duplicate","replicates","reference"])
def test_incomplete_or_invalid_input_refused(bad):
    plan=b.make_plan();data=reports(plan)
    if bad=="case":data.pop()
    elif bad=="condition":data[0]["records"].pop()
    elif bad=="duplicate":data[0]["records"][-1]=data[0]["records"][0]
    elif bad=="replicates":data[0]["replicates"]=191
    else:data[0]["records"][0]["assessment"]["relative_rmse_reference_range"]=[0.,float("nan")]
    with pytest.raises(ValueError):select.choose(plan,data)


def test_step_count_is_not_measured_time_and_finer_grid_costs_more():
    plan=b.make_plan();data=reports(plan)
    cfg=data[0]["records"][0]["condition"]
    coarse=dict(cfg,ladder="coarse")
    fine=dict(cfg,ladder="fine")
    assert select.step_count(plan,fine)>select.step_count(plan,coarse)
    assert select.step_count(plan,coarse)==len(plan["cases"][0]["coarse"])*cfg["chains"]*(cfg["burn"]+cfg["samples"])


def test_write_preserves_existing_selection(tmp_path,monkeypatch):
    plan=b.make_plan();data=reports(plan)
    c.atomic_json(tmp_path/"manifest.json",plan)
    for report in data:report["input_sha256"]["sampling"]=c.file_hash(tmp_path/"manifest.json")
    monkeypatch.setattr(p,"assess_calibration",lambda root,case:data[case])
    target=tmp_path/"selection.json"
    selected=select.run(tmp_path,target)
    assert selected["sampling_manifest"]==c.digest(plan)
    assert all(len(h)==64 for h in selected["selection_evidence_sha256"])
    with pytest.raises(ValueError):select.run(tmp_path,target)


def test_run_recomputes_real_raw_cohorts_and_rejects_changed_rows(tmp_path,monkeypatch):
    plan=dict(replicates=192,cases=[dict(chains=4,windows=[600],target=.03,rungs=[.1,.03],coarse=[.1,.03]) for _ in range(4)],
              kernels={"ZH":{}},initializations=["logical"],burns=[600],blocks=[32])
    references=[dict(ref(.2,.199,.201),case=case,target_p=.03) for case in range(4)]
    c.atomic_json(tmp_path/"manifest.json",plan)
    c.atomic_json(tmp_path/"reference_summary.json",dict(records=references))
    context=dict(sampling_manifest=c.digest(plan),references=references,reference_summary_sha256=c.file_hash(tmp_path/"reference_summary.json"))
    c.atomic_json(tmp_path/"analysis_manifest.json",context)
    for case in range(4):
        saved=[];metrics=[]
        for key in s.expected_conditions(plan,case,"ZH","logical"):
            cfg=dict(zip(s.CONDITION,key))
            rows=[dict(row(rep,.2,interval=(.18,.22)),**cfg) for rep in range(192)]
            saved.extend(rows)
            metrics.append(dict(cfg,**s.summarize_condition(rows,192,references[case])))
        path=tmp_path/f"rows-{case}.jsonl"
        path.write_bytes(b"".join(c.canonical(x)+b"\n" for x in saved))
        c.atomic_json(tmp_path/f"summary-{case}.json",dict(case=case,analysis=c.digest(context),raw_rows_sha256=c.file_hash(path),conditions=len(metrics),records=metrics))
    monkeypatch.setattr(b,"make_plan",lambda:plan)
    chosen=select.run(tmp_path,tmp_path/"selected.json")
    assert all(x["status"]=="selected" for x in chosen["records"])
    assert chosen["assessment_evidence"][3]["input_sha256"]["rows"]==c.file_hash(tmp_path/"rows-3.jsonl")
    with (tmp_path/"rows-3.jsonl").open("ab") as stream:stream.write(b"\n")
    with pytest.raises(ValueError,match="hash"):select.run(tmp_path,tmp_path/"changed.json")
    assert not (tmp_path/"changed.json").exists()
