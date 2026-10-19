"""Synthetic low-noise analysis resources preserve the whole planned cohort."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_low_noise_analysis_capacity as capacity


def measurement(plan, *, seconds=20, rss=100):
    rows = [dict(group=list(group), status="ok", synthetic=True,
                 wall_seconds=seconds, peak_rss_mb=rss) for group in capacity.groups(plan)]
    return dict(manifest=c.digest(plan), synthetic=True, tasks=len(rows), failed=0, records=rows)


def test_profile_has_full_scientific_dimensions_but_separate_seeds():
    plan = capacity.make_plan(0, 2)
    assert plan["purpose"] == "low_noise_synthetic_analysis_capacity"
    assert plan["synthetic"] is True and plan["workers"] == 8
    assert len(list(capacity.groups(plan))) == 8
    production = plan["production"]
    assert production["purpose"] == "low_noise_production"
    assert production["replicates"] == 192
    assert production["condition"]["steps"] == 66000
    assert production["condition"]["chains"] == 16
    assert len(production["condition"]["rungs"]) == 15
    assert capacity.compute_plan(plan)["stages"]["analysis"] == 155
    assert production["stages"]["analysis"] == 153


def test_resource_plan_covers_all_groups_and_obeys_memory_wall_limits():
    plan = capacity.make_plan(0, 0)
    output = capacity.resource_plan(plan, measurement(plan, seconds=3600, rss=20000))
    assert output["workers"] == 11
    assert output["memory_gb"] <= 340
    observed = [tuple(group) for part in output["partitions"] for group in part["groups"]]
    assert observed == list(capacity.production_groups(plan))
    assert len(observed) == len(set(observed)) == 768
    assert len(output["partitions"]) > 1
    for part in output["partitions"]:
        assert part["wall_seconds"] <= 86400
        assert part["wall_seconds"] % 1800 == 0


@pytest.mark.parametrize("change", ["missing", "duplicate", "failed", "nonsynthetic", "manifest", "nan", "zero_rss"])
def test_incomplete_profiles_never_rescale_successes(change):
    plan = capacity.make_plan(1, 0)
    summary = measurement(plan)
    if change == "missing": summary["records"].pop()
    elif change == "duplicate": summary["records"][-1] = deepcopy(summary["records"][0])
    elif change == "failed": summary["records"][0]["status"] = "failed"
    elif change == "nonsynthetic": summary["synthetic"] = False
    elif change == "manifest": summary["manifest"] = "wrong"
    elif change == "nan": summary["records"][0]["wall_seconds"] = float("nan")
    else: summary["records"][0]["peak_rss_mb"] = 0
    with pytest.raises(ValueError):
        capacity.resource_plan(plan, summary)


def test_single_group_over_resource_limit_requires_further_design():
    plan = capacity.make_plan(0, 0)
    for summary in (measurement(plan, rss=400000), measurement(plan, seconds=50000)):
        with pytest.raises(ValueError):
            capacity.resource_plan(plan, summary)


def test_array_seed_namespace_is_distinct_for_every_role():
    plan = capacity.make_plan(0, 0)
    seeds = [capacity.synthetic_seed(plan, group, rung, chain)
             for group in capacity.groups(plan) for rung in range(2) for chain in range(2)]
    assert len(seeds) == len(set(seeds))
    other = capacity.make_plan(0, 1)
    assert capacity.synthetic_seed(plan, (0, 0, 0, 0, 0), 0, 0) != capacity.synthetic_seed(other, (0, 1, 0, 0, 0), 0, 0)


@pytest.mark.parametrize("case", range(4))
def test_real_numerical_pipeline_on_small_explicitly_synthetic_arrays(tmp_path, case):
    plan = capacity.make_plan(case, 0)
    base = plan["production"]
    base.update(burns=[0], blocks=[4], bootstrap_replicates=8)
    base["condition"].update(chains=4, steps=24, windows=[24], rungs=[.1, .01], coarse=[.1, .01])
    record = capacity.profile((str(tmp_path), plan, (case, 0, 0, 0, 0)))
    assert record["status"] == "ok", record
    assert record["synthetic"] is True
    assert record["rows"] == 4 and record["estimation_unavailable"] == 0
    assert record["analysis_seconds"] > 0
    assert "estimate" not in record and "diagnostics" not in record
    assert not (tmp_path/"traces").exists()
    assert not (tmp_path/"analysis").exists()


def test_native_preflight_precedes_workers_and_intent_blocks_retry(tmp_path, monkeypatch):
    plan = capacity.make_plan(0, 0)
    monkeypatch.setenv("PBS_JOBID", "test-profile")
    for key, value in plan["required_threads"].items(): monkeypatch.setenv(key, value)
    def broken(*args): raise ValueError("native mismatch")
    monkeypatch.setattr(capacity.low, "preflight", broken)
    monkeypatch.setattr(capacity.c, "parallel_map", lambda *a: pytest.fail("workers started"))
    with pytest.raises(ValueError, match="native mismatch"):
        capacity.run_phase(tmp_path, plan)
    assert (tmp_path/"execution-intent.json").exists()
    with pytest.raises(FileExistsError):
        capacity.run_phase(tmp_path, plan)


def test_failed_worker_preserved_in_summary_and_no_resource_result(tmp_path, monkeypatch):
    plan = capacity.make_plan(0, 0)
    monkeypatch.setenv("PBS_JOBID", "test-profile")
    for key, value in plan["required_threads"].items(): monkeypatch.setenv(key, value)
    monkeypatch.setattr(capacity.low, "preflight", lambda *args: "native-hash")
    rows = measurement(plan)["records"]
    rows[0]["status"] = "failed"
    monkeypatch.setattr(capacity.c, "parallel_map", lambda *a: rows)
    with pytest.raises(RuntimeError, match="failed profiles"):
        capacity.run_phase(tmp_path, plan)
    import json
    summary = json.loads((tmp_path/"summary.json").read_text())
    assert summary["failed"] == 1 and summary["tasks"] == 8
    with pytest.raises(ValueError): capacity.resource_plan(plan, summary)


def bound_measurement(root, monkeypatch):
    """Explicit mock compute evidence; tests binding, not native compatibility."""
    plan = capacity.make_plan(1, 0)
    monkeypatch.setattr(capacity, "make_plan", lambda *args: plan)
    inputs = capacity.low.native.platform_inputs()
    for key, value in inputs.items(): c.atomic_json(root/(key+".json"), value)
    c.atomic_json(root/"manifest.json", plan)
    evidence = dict(manifest=c.digest(plan), pbs_job_id="mock-job", hostname="mock-host",
                    profile={"mock": True})
    proof = root/"preflight-analysis-capacity"/"native_preflight.json"
    proof.parent.mkdir()
    c.atomic_json(proof, evidence)
    monkeypatch.setattr(capacity.low.native.trace_audit, "validate_platform", lambda *args: None)
    c.atomic_json(root/"execution-intent.json", dict(evidence, synthetic=True, workers=plan["workers"]))
    summary = measurement(plan)
    summary.update(workers=plan["workers"], native_preflight_sha256=c.file_hash(proof))
    for row in summary["records"]:
        row.update(rows=len(list(capacity.analysis.analysis_settings(plan["production"]))),
                   diagnostic_count=1, analysis_seconds=1, estimation_unavailable=0)
        base = root/"profiles"/c.task_id(row["group"])
        c.save_artifact(base, dict(manifest=c.digest(plan), group=row["group"], synthetic=True), {}, row)
    c.atomic_json(root/"summary.json", summary)
    return plan, summary, proof


def test_resource_cli_requires_bound_compute_evidence(tmp_path, monkeypatch):
    plan, summary, proof = bound_measurement(tmp_path, monkeypatch)
    result = capacity.measured_profile(tmp_path, plan)
    assert result["measurement"] == c.digest(summary)
    assert result["native_preflight_sha256"] == c.file_hash(proof)


@pytest.mark.parametrize("change", ["input", "native", "job", "workers", "raw", "marker", "count"])
def test_resource_binding_rejects_changed_evidence(tmp_path, monkeypatch, change):
    import json
    plan, summary, proof = bound_measurement(tmp_path, monkeypatch)
    base = tmp_path/"profiles"/c.task_id(summary["records"][0]["group"])
    if change == "input":
        c.atomic_json(tmp_path/"platform_profile.json", {"changed": True})
    elif change == "native":
        c.atomic_json(proof, {"changed": True})
    elif change in ("job", "workers"):
        path = tmp_path/"execution-intent.json"
        intent = json.loads(path.read_text())
        intent["pbs_job_id" if change == "job" else "workers"] = "changed"
        c.atomic_json(path, intent)
    elif change == "raw":
        c.atomic_json(base.with_suffix(".json"), {"changed": True})
    elif change == "marker":
        path = base.with_suffix(".done.json")
        marker = json.loads(path.read_text())
        del marker["sha256"][".npz"]
        c.atomic_json(path, marker)
    else:
        summary["records"][0]["rows"] = 0
        c.atomic_json(tmp_path/"summary.json", summary)
    with pytest.raises(ValueError):
        capacity.measured_profile(tmp_path, plan)
