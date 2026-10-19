"""Production resources follow complete capacity evidence and a two-node cap."""
from pathlib import Path
import sys
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_bar_study as b
import calibration as c
import submit_tile_production as s


def capacity_fixture():
    plan=b.make_plan(capacity=True)
    rows=[dict(task=list(task),status="ok",wall_seconds=float(task[0]+1),peak_rss_mb=100.) for task in b.tasks(plan)]
    return plan,dict(manifest=c.digest(plan),tasks=384,failed=0,records=rows)


def test_resources_from_all_capacity_strata_and_all_production_tasks():
    cap,data=capacity_fixture()
    plan=b.make_plan()
    out=s.resource_plan(plan,cap,data)
    assert sum(r["tasks"] for r in out["cases"])==len(list(b.tasks(plan)))
    assert out["order"][0]==2
    for row in out["cases"]:
        assert row["memory_gb"]>=32 and row["cpus"]==96
        assert row["wall_seconds"]>=2*row["predicted_sampling_seconds"]+600
    data["records"].pop()
    with pytest.raises(ValueError):
        s.resource_plan(plan,cap,data)


def test_failed_capacity_does_not_authorize_production():
    cap,data=capacity_fixture()
    data["records"][0]["status"]="failed"
    with pytest.raises(ValueError):
        s.resource_plan(b.make_plan(),cap,data)
