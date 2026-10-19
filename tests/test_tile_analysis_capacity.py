"""Synthetic capacity data can exercise analysis but cannot pass production guards."""
from pathlib import Path
import sys
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_analysis_capacity as p
import tile_bar_study as b


def test_capacity_namespace_and_real_analysis_on_small_arrays(tmp_path):
    plan=p.make_plan()
    assert plan["purpose"]=="synthetic_analysis_capacity"
    assert plan!=b.make_plan()
    plan.update(burns=[0],blocks=[4],bootstrap_replicates=8)
    plan["cases"][0].update(chains=4,steps=32,windows=[32],rungs=[.1,.03],coarse=[.1,.03])
    record=p.profile((str(tmp_path),plan,(0,0)))
    assert record["synthetic"] and record["rows"]==4
    assert record["status"]=="ok"
    assert record["analysis_seconds"]>0
    assert not list((tmp_path/"scratch").glob("*/traces"))
