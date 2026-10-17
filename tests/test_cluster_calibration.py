"""Small finite acceptance tests for the external PBS calibration driver."""
from pathlib import Path
import sys

import numpy as np
import pytest

for backend in ("pymatching", "ldpc", "bposd"):
    pytest.importorskip(backend)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cluster_scripts"))
import calibration as c
from mcmc4qec import exact
from mcmc4qec.estimation import bennett_log_ratio, _block_indices


def test_fixed_manifest_counts_and_seed_independence():
    plan = c.make_plan()
    tasks = list(c.tasks(plan))
    assert len(tasks) == 46080
    assert len({c.task_id(t) for t in tasks}) == len(tasks)
    assert len({c.seed(t, 1) for t in tasks}) == len(tasks)
    assert [sum(t[3] % 4 == s for t in tasks) for s in range(4)] == [11520] * 4
    assert plan["expected_analysis_rows"] == 64512
    assert c.seed(tasks[0], 0) != c.seed(tasks[0], 1)
    assert c.seed(tasks[100], 1) == c.seed(list(reversed(tasks))[-101], 1)


def test_truth_bank_matches_public_failure_and_exact():
    _, problem = c.problem_for(2)
    bank = c.enumerate_bank(2)
    states = c.unpack(bank["index"], 7)
    assert all(problem.is_faulty(s) for s in states)
    all_states = c.unpack(np.arange(128), 7)
    expected = np.array([problem.is_faulty(s) for s in all_states])
    assert np.array_equal(bank["index"], np.flatnonzero(expected))
    for p in (.1, .03, .0001):
        assert c.failure_mass(bank, 7, p) == pytest.approx(exact(problem, p).estimate, rel=1e-12)
    starts = c.dispersed_indices(bank, 4)
    assert len(set(starts)) == 4
    for i in range(20):
        s = c.initial_index(bank, 7, .001, 0, i, np.random.default_rng(i))
        assert s in bank["index"]


def test_weighted_bennett_matches_public_unequal_counts():
    a = np.array([1, 2, 2, 4, 5])
    b = np.array([1, 1, 2, 3, 3, 4, 5])
    delta = c.log_density_difference(7, .1, .03)
    got = c.histogram_bar(np.bincount(a, minlength=8), np.bincount(b, minlength=8), delta)
    assert got == pytest.approx(bennett_log_ratio(delta[a], delta[b]), abs=1e-11)


@pytest.mark.parametrize("length", [2, 8, 13])
def test_circular_histograms_keep_truncated_tail_and_rng(length):
    weights = np.random.default_rng(12).integers(0, 8, (4, 29))
    got = c.bootstrap_histograms(weights, 7, length, 7, np.random.default_rng(45))
    rng = np.random.default_rng(45)
    for r in range(7):
        ids = _block_indices(weights.shape, length, rng)
        sampled = np.take_along_axis(weights, ids, axis=1)
        assert np.array_equal(got[r], np.bincount(sampled.ravel(), minlength=8))


def test_atomic_artifacts_detect_corruption_wrong_identity_and_incomplete(tmp_path):
    path = tmp_path / "test"
    identity = {"manifest": "abc", "task": [1, 2]}
    c.save_artifact(path, identity, {"weight": np.arange(5)}, {"status": "ok"})
    assert c.load_artifact(path, identity)[1]["status"] == "ok"
    with pytest.raises(ValueError, match="identity"):
        c.load_artifact(path, {"manifest": "other"})
    path.with_suffix(".npz").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        c.load_artifact(path, identity)
    path.with_suffix(".done.json").unlink()
    assert c.load_artifact(path, identity) is None


def test_two_lane_dependency_graph():
    import submit
    graph = submit.sampling_graph([3, 1, 0, 2])
    assert graph == [(3, None), (1, None), (0, 3), (2, 1)]
    for node, parent in graph[2:]:
        assert parent is not None


def test_shared_rung_covariance_and_point_match_public_equations():
    from mcmc4qec.estimation import _cross_chain_covariance
    weights = [np.random.default_rng(i).integers(1, 5, (4, 67)) for i in range(3)]
    ladder = [.1, .05, .02]
    deltas = [c.log_density_difference(7, p, q) for p, q in zip(ladder, ladder[1:])]
    edges = [(d[a], d[b]) for d, a, b in zip(deltas, weights, weights[1:])]
    cross = c.estimate_window(weights, 7, ladder, .1, block=None, replicates=20, rng=np.random.default_rng(1))
    np.testing.assert_allclose(cross["covariance"], _cross_chain_covariance(edges), atol=1e-12)
    points = [bennett_log_ratio(*e) for e in edges]
    np.testing.assert_allclose(cross["adjacent_log_ratios"], points, atol=1e-11)
    rng = np.random.default_rng(52)
    resampled = []
    for w in weights:
        resampled.append([np.take_along_axis(w, _block_indices(w.shape, 8, rng), axis=1) for _ in range(20)])
    draws = [[bennett_log_ratio(d[a[r]], d[b[r]]) for d, a, b in zip(deltas, resampled, resampled[1:])] for r in range(20)]
    block = c.estimate_window(weights, 7, ladder, .1, block=8, replicates=20, rng=np.random.default_rng(52))
    np.testing.assert_allclose(block["covariance"], np.cov(draws, rowvar=False, ddof=1), atol=1e-12)
    assert block["estimate"] == cross["estimate"]


def test_small_pipeline_records_failed_seed_in_denominator(tmp_path):
    plan = c.make_plan(smoke=True)
    plan.update(steps=48, windows=[32], burns=[8], blocks=[8], bootstrap_replicates=4)
    bank = c.enumerate_bank(2)
    c.save_artifact(tmp_path/"truth"/"2", dict(manifest=c.digest(plan), code=2, code_identity=c.code_identity(2)), bank, {"status": "ok"})
    group = (2, 0, 0, 0)
    for rung in range(4):
        for chain in range(4):
            task = (*group, rung, chain)
            record = c.sample_task((str(tmp_path), plan, task))
            assert record["status"] == "ok"
    record = c.analyze_group((str(tmp_path), plan, group))
    assert len(record["rows"]) == 2
    assert all(row["available"] for row in record["rows"])
    group = (2, 0, 0, 1)
    for rung in range(4):
        for chain in range(4):
            task = (*group, rung, chain)
            c.save_artifact(tmp_path/"traces"/c.task_id(task), dict(manifest=c.digest(plan), task=list(task)), {}, {"status": "failed", "error": "deliberate"})
    failed = c.analyze_group((str(tmp_path), plan, group))
    assert len(failed["rows"]) == 2
    assert all(not row["available"] and not row["covered"] for row in failed["rows"])


def test_pbs_scripts_use_full_node_and_no_side_effect_helpers(tmp_path):
    import submit
    script = submit.script(tmp_path, tmp_path/"run", "sample", "06:00:00", 64, 2)
    assert "select=1:ncpus=96:mem=64gb" in script
    assert "PBS_JOBID" in script and "--shard 2" in script
    assert "git " not in script and "ntfy" not in script
    assert submit.walltime(3700) == "02:30:00"
    with pytest.raises(ValueError, match="split"):
        submit.walltime(86400)
