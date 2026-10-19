"""Small end-to-end BAR analysis with uncertain independent reference."""
from pathlib import Path
import sys
import itertools
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_bar_analysis as a
import tile_bar_study as b


def test_reference_uncertainty_coverage_bounds():
    ref=dict(estimate=.2,interval_999=[.18,.22])
    assert a.coverage_flags([.17,.23],ref)==dict(covered_reference_point=True,covered_reference_entire=True,covered_reference_possible=True)
    assert a.coverage_flags([.19,.21],ref)==dict(covered_reference_point=True,covered_reference_entire=False,covered_reference_possible=True)
    assert not any(a.coverage_flags(None,ref).values())
    assert not any(a.coverage_flags([.3,.4],ref).values())


def test_finite_group_uses_all_expected_conditions(tmp_path):
    plan=b.make_plan()
    plan.update(replicates=1,burns=[0],blocks=[4],bootstrap_replicates=8,anchor_trials=100)
    plan["cases"][0].update(chains=4,steps=32,windows=[32],coarse=[.1,.03],rungs=[.1,.03])
    group=(0,0,0,0)
    for rung,chain in itertools.product(range(2),range(4)):
        assert b.sample_task((str(tmp_path),plan,(*group,rung,chain)))["status"]=="ok"
    b.anchor_task((str(tmp_path),plan,0,0))
    ref=[dict(case=0,target_p=.03,estimate=.04,standard_error=.001,interval_999=[.037,.043])]
    context=a.analysis_context(plan,ref)
    record=a.analyze_group((str(tmp_path),plan,context,group))
    assert len(record["rows"])==4
    assert all(row["available"] for row in record["rows"])
    assert len({row["estimate"] for row in record["rows"]})==1
    assert all(row["anchor_log_variance"]>0 for row in record["rows"])
    assert record["diagnostic_count"]>0
