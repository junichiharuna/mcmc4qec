"""Finite study-specific BAR algebra and trace artifact acceptance."""
from pathlib import Path
import itertools
import sys
import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_bar_study as b
import calibration as c
import mcmc4qec as qec


def test_depolarizing_weight_sufficiency_includes_y_correlations():
    noise = qec.DepolarizingNoise(3)
    delta = c.log_density_difference(3, .1, .03)
    for state in itertools.product(range(4), repeat=3):
        a = np.array(state, dtype=np.uint8)
        assert delta[np.count_nonzero(a)] == pytest.approx(noise.log_prob(a, .03)-noise.log_prob(a, .1))


def test_independent_anchor_variance_preserves_pooled_point():
    rng = np.random.default_rng(87)
    weights = [rng.integers(1,4,(4,32)) for _ in range(2)]
    base = c.estimate_window(weights,3,[.1,.03],.2,block=None,replicates=4,rng=rng)
    result = b.with_anchor_variance(base, dict(estimate=.2,failures=20,trials=100,status="ok"))
    assert result["estimate"] == base["estimate"]
    assert result["log_se"]**2 == pytest.approx(base["log_se"]**2+.04)
    assert b.with_anchor_variance(base, dict(estimate=0.,failures=0,trials=100,status="ok"))["available"] is False


def test_small_trace_checks_all_steps_and_resume(tmp_path):
    plan=b.make_plan()
    plan["cases"][0]["steps"]=20
    task=(0,0,0,0,0,0)
    record=b.sample_task((str(tmp_path),plan,task))
    assert record["status"]=="ok"
    arrays, stored=c.load_artifact(tmp_path/"traces"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
    assert len(arrays["weight"])==20 and np.all(arrays["sector"]!=0)
    assert stored["checked_saved_states"]==20
    assert b.sample_task((str(tmp_path),plan,task))["resumed"]


def test_capacity_is_disjoint_and_node_accounting_is_explicit():
    from submit_tile_capacity import requested_nodes
    capacity=b.make_plan(capacity=True)
    production=b.make_plan()
    assert len(list(b.tasks(capacity)))==384
    task=next(b.tasks(capacity))
    assert b.task_seed(capacity,task,0)!=b.task_seed(production,task,0)
    assert requested_nodes({"a":{"Resource_List":{"select":"1:ncpus=96:mem=32gb"}}})==1
    assert requested_nodes({"a":{"Resource_List":{"select":"2:ncpus=96:mem=32gb+1:ncpus=96"}}})==3
