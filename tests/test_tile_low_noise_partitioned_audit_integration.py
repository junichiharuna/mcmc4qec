"""Actual completed-reader wiring, separately from physical short-trace fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_low_noise_partitioned_trace_audit as r
import tile_low_noise_partitioned_trace_audit_resources as resources
from test_tile_low_noise_sampling_partition_evidence import completed_fixture


def metadata_source(tmp_path, monkeypatch):
    """Full synthetic census with real collection reader; no raw payload claim."""
    source = tmp_path / "sampling"
    plan, wrapper = completed_fixture(source, monkeypatch)
    # The common fixture stubs its fixed-plan and platform boundary. Restore
    # real native input dictionaries needed by the new audit plan constructor.
    for name, value in r.low.native.platform_inputs().items():
        c.atomic_json(source / (name + ".json"), value)
    summary_path = source / "sampling-collection/summary.json"
    summary = json.loads(summary_path.read_text())
    summary["input_sha256"] = {name: c.file_hash(source / name) for name in r.partitions.proof_paths(wrapper)}
    c.atomic_json(summary_path, summary)
    monkeypatch.setattr(r.low, "make_plan", lambda *a, **k: deepcopy(plan))
    monkeypatch.setattr(r.analysis, "completed_phase_evidence", lambda *_: pytest.fail("singleton reader used"))
    return source, plan


def test_real_completed_reader_flows_to_capacity_and_full_plan(tmp_path, monkeypatch):
    source, sampling = metadata_source(tmp_path, monkeypatch)
    capacity = r.prepare(tmp_path / "capacity", source, capacity=True, workers=8)
    full = r.prepare(tmp_path / "full", source, capacity=False, workers=96)
    proof = capacity["completed_phase_evidence"]
    assert proof["sample"]["tasks"] == proof["sample"]["failed"] == 768
    assert proof["anchors"]["tasks"] == proof["anchors"]["failed"] == 192
    assert len(r.upstream_jobs(proof)) == 5
    assert len(r.groups(capacity)) == 8 and len(r.groups(full)) == 768
    assert r.read_plan(tmp_path / "capacity", source) == (capacity, sampling)
    assert r.read_plan(tmp_path / "full", source) == (full, sampling)
    terminal = source / "sampling-collection-submission/terminal.json"
    changed = json.loads(terminal.read_text())
    changed["job"]["Exit_status"] = 1
    c.atomic_json(terminal, changed)
    with pytest.raises(ValueError):
        r.read_plan(tmp_path / "full", source)


def test_missing_raw_payload_never_becomes_successful_capacity(tmp_path, monkeypatch):
    from test_tile_low_noise_partitioned_trace_audit import save_execution_submission
    source, sampling = metadata_source(tmp_path, monkeypatch)
    root = tmp_path / "audit"
    plan = r.prepare(root, source, capacity=True, workers=8)
    save_execution_submission(root, source, plan, sampling)
    monkeypatch.setenv("PBS_JOBID", "201.fixture")
    for name, value in r.THREADS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(r.audit, "validate_native_environment", lambda *a, **k: {"native_platform_verified": True})
    monkeypatch.setattr(c, "parallel_map", lambda fn, jobs, workers: [fn(job) for job in jobs])
    with pytest.raises(RuntimeError, match="failures"):
        r.run(root, source)
    summary = json.loads((root / "summary.json").read_text())
    assert summary["groups"] == summary["failed_audit_groups"] == 8
    assert summary["planned_tasks"] == 8
    assert len(summary["records"]) == 8
    full = r.make_plan(sampling, **r.low.native.platform_inputs(), capacity=False, workers=96,
                       completed_evidence=plan["completed_phase_evidence"], input_sha256=plan["input_sha256"])
    with pytest.raises(ValueError):
        resources.resource_plan(plan, summary, full)
