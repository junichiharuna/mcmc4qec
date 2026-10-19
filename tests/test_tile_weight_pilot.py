"""Tiny independent weight pilot uses fixed decoder and recorded failure checks."""
from pathlib import Path
import sys
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_weight_pilot as p


def test_pilot_has_full_fixed_task_set_and_small_task_resumes(tmp_path):
    plan=p.make_plan()
    assert len(list(p.tasks(plan)))==1536
    plan["samples"]=32
    for task in ((0,0,0,0),(0,0,3,0),(2,0,3,0)):
        record=p.run_task((str(tmp_path),plan,task))
        assert record["status"]=="ok" and record["failure_mismatches"]==0
        assert record["trials"]==(1 if task[2]==0 else 32)
        assert p.run_task((str(tmp_path),plan,task))==record
