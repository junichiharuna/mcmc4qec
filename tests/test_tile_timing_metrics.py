"""Complete independent timing cohorts gate descriptive cost ratios by precision."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_timing_metrics as metrics


REFERENCE=dict(estimate=.2,interval_999=[.199,.201],standard_error=.001)


def rows(method,values=(.2,.2),walls=(2.,6.),cpus=(1.,3.)):
    return [dict(replicate=i,status="ok",estimate=value,interval=[.18,.22],available=True,
                 task_wall_seconds=walls[i],cpu_seconds=cpus[i],
                 **(dict(timing={key:dict(wall_seconds=0.,cpu_seconds=0.) for key in metrics.BAR_PHASES})
                    if method=="bar" else dict(construction_wall_seconds=.1,direct_mc_elapsed_seconds=walls[i]-.2)))
            for i,value in enumerate(values)]


def test_cost_ratio_is_ratio_of_complete_means_not_mean_of_task_ratios():
    result=metrics.compare(rows("mc"),rows("bar",walls=(1.,2.),cpus=(.5,1.)),2,REFERENCE,.1)
    assert result["ratios_mc_over_bar"]["task_wall_seconds"]["value"]==pytest.approx(8/3)
    assert result["ratios_mc_over_bar"]["cpu_seconds"]["value"]==pytest.approx(8/3)
    assert result["bar"]["precision"]["metrics"]["undefined"]==2
    assert result["bar"]["diagnostics_status"]=="not_collected"
    assert result["mc"]["precision"]["metrics"]["undefined"]==0
    assert result["mc"]["diagnostics_status"]=="not_applicable"
    assert result["phase_time_apportioned"] is False


@pytest.mark.parametrize("change",["above_target","failed","missing_point"])
def test_precision_failure_suppresses_ratio_and_keeps_all_costs(change):
    bar=rows("bar")
    if change=="above_target":
        bar[0]["estimate"]=.8
    elif change=="failed":
        bar[0].update(status="failed",failure="sampling_failed",estimate=None,interval=None,available=False)
    else:
        bar[0].update(status="unavailable",failure="point unavailable",estimate=None,interval=None,available=False)
    result=metrics.compare(rows("mc"),bar,2,REFERENCE,.1)
    assert result["bar"]["costs"]["task_wall_seconds"]["sum"]==8
    assert result["bar"]["precision"]["metrics"]["replicates"]==2
    assert all(row["value"] is None and row["reason"]=="precision_not_confirmed" for row in result["ratios_mc_over_bar"].values())


def test_missing_cost_cannot_pass_through_available_only_mean():
    bar=rows("bar")
    bar[0]["cpu_seconds"]=None
    result=metrics.compare(rows("mc"),bar,2,REFERENCE,.1)
    cost=result["bar"]["costs"]["cpu_seconds"]
    assert cost["missing"]==1 and cost["mean"] is None and cost["sum"] is None
    assert cost["available_only_mean"]==3
    assert result["ratios_mc_over_bar"]["cpu_seconds"]["value"] is None
    assert result["ratios_mc_over_bar"]["task_wall_seconds"]["value"]==1


def test_interval_missing_is_retained_separately_from_point_precision():
    bar=rows("bar")
    bar[0].update(status="unavailable",interval=None,available=False,failure="interval unavailable")
    result=metrics.compare(rows("mc"),bar,2,REFERENCE,.1)
    assert result["ratios_mc_over_bar"]["task_wall_seconds"]["value"]==1
    assert result["bar"]["precision"]["metrics"]["coverage_reference_point"]==.5
    assert result["bar"]["precision"]["metrics"]["unavailable_intervals"]==1
    assert not result["nominal_coverage_certified"]


@pytest.mark.parametrize("value",[-1.,float("nan"),float("inf"),True])
def test_invalid_cost_rejected(value):
    bar=rows("bar")
    bar[0]["task_wall_seconds"]=value
    with pytest.raises(ValueError):
        metrics.compare(rows("mc"),bar,2,REFERENCE,.1)


def test_duplicate_replicate_and_unknown_status_rejected():
    bar=rows("bar")
    bar[0]["replicate"]=1
    with pytest.raises(ValueError):metrics.compare(rows("mc"),bar,2,REFERENCE,.1)
    bar=rows("bar")
    bar[0]["status"]="skipped"
    with pytest.raises(ValueError):metrics.compare(rows("mc"),bar,2,REFERENCE,.1)


def test_zero_reference_and_zero_time_do_not_produce_nonfinite_ratios():
    result=metrics.compare(rows("mc"),rows("bar",walls=(0.,0.)),2,REFERENCE,.1)
    assert result["ratios_mc_over_bar"]["task_wall_seconds"]["reason"]=="zero_bar_cost"
    result=metrics.compare(rows("mc"),rows("bar"),2,dict(estimate=.2,interval_999=[0.,.3],standard_error=.1),.1)
    assert all(row["value"] is None for row in result["ratios_mc_over_bar"].values())
    json.dumps(result,allow_nan=False)


def test_short_actual_mc_record_can_be_assessed(tmp_path):
    pytest.importorskip("ldpc")
    import tile_mc_time_benchmark as m
    budget=json.loads((Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json").read_text())
    plan=m.make_plan(budget,capacity=False)
    plan["conditions"][0]["planned_trials"]=12
    record=m.run_task((tmp_path,plan,(0,0)))
    assert record["status"]=="ok"
    result=metrics.assess("mc",[record],1,REFERENCE,.2)
    assert result["costs"]["task_wall_seconds"]["mean"]==record["task_wall_seconds"]
    assert result["costs"]["construction_wall_seconds"]["mean"]==record["construction_wall_seconds"]
    assert result["precision"]["metrics"]["point_estimates"]==1
