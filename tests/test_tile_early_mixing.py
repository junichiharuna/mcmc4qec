"""Preregistered early diagnostics retain undefined and unavailable outcomes."""
from pathlib import Path
import sys

import numpy as np
import pytest

for name in ("ldpc","bposd","pymatching"):
    pytest.importorskip(name)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_early_mixing as early


def test_subset_and_window_cost_are_fixed_before_results():
    assert len(early.GROUPS)==len(set(early.GROUPS))==16
    assert early.PILOT==(3,0,0,0)
    assert all(set(group[i] for group in early.GROUPS)=={0,1} for i in (1,2,3))
    assert sum(10 if case==1 else 18 for case,*_ in early.GROUPS)==224


def test_constant_observable_remains_undefined_not_dropped():
    result=early.diagnose(np.ones((8,20)),"logical_bit_0")
    assert result["available"] and result["undefined"] and result["flagged"]
    assert result["rhat"] is None and result["mean"]==1
    assert result["iat_mcse"] is None


def test_diagnostic_exception_is_recorded(monkeypatch):
    def fail(*args,**kwargs): raise FloatingPointError("fixture")
    monkeypatch.setattr(early.c,"diagnostic_record",fail)
    result=early.diagnose(np.ones((8,20)),"weight")
    assert not result["available"] and result["undefined"]
    assert len(result["chain_ess"])==8 and result["mean"] is None


def test_all_failed_tasks_preserve_group_and_observable_denominators(tmp_path,monkeypatch):
    source=tmp_path/"source"
    (source/"traces").mkdir(parents=True)
    plan=dict(source=str(source),sampling_manifest="fixed")
    production=early.b.make_plan()
    coordinates=(1,0,0,0)
    rung=len(production["cases"][1]["rungs"])-1
    for chain in range(8):
        early.c.atomic_json(source/"traces"/(early.c.task_id((*coordinates,rung,chain))+".done.json"),
                            dict(sha256={".json":"fixture",".npz":"fixture"}))
    def load(path,identity):
        return {},dict(task=identity["task"],status="failed",wall_seconds=0.,cpu_seconds=0.,error="fixture failure")
    monkeypatch.setattr(early.c,"load_artifact",load)
    result=early.group(tmp_path/"out",plan,production,coordinates,dict(profile="unit-test"))
    assert result["status"]=="unavailable" and len(result["input_errors"])==8
    assert len(result["diagnostics"])==10 and result["undefined_observables"]==10
    assert result["conditional_weight"] is None and result["physical_checkpoint_redecodes"]==0
