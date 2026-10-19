"""Finite reference aggregation and immutable identity acceptance."""
from pathlib import Path
import sys
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_reference as r


def test_fixed_budget_and_disjoint_seeds():
    plan = r.make_plan()
    tasks = list(r.tasks(plan))
    assert len(tasks) == 1248
    assert sum(plan["trials_per_chunk"] for _ in tasks) == 81788928
    assert len({r.chunk_seed(task) for task in tasks}) == len(tasks)


def test_aggregate_keeps_zero_chunks_and_requires_complete_cohort():
    plan = r.make_plan()
    plan["chunks"] = [2]*4
    plan["trials_per_chunk"] = 10
    records = [dict(task=[case, chunk], status="ok", failures=chunk, trials=10,
                    conditional_weight=3. if chunk else None, elapsed_seconds=1.)
               for case, chunk in r.tasks(plan)]
    result = r.aggregate(plan, records)
    assert len(result) == 4
    assert all(x["trials"] == 20 and x["failures"] == 1 and x["estimate"] == .05 for x in result)
    assert all(x["interval_999"][0] <= .05 <= x["interval_999"][1] for x in result)
    with pytest.raises(ValueError, match="complete"):
        r.aggregate(plan, records[:-1])
