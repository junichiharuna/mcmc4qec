"""Measured eight-worker capacity gates and phase-overhead extrapolation."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_study as low
import tile_low_noise_partitioned_trace_audit as runner
import tile_low_noise_partitioned_trace_audit_resources as m
from test_tile_low_noise_partitioned_trace_audit import evidence


def fixture_plans():
    sampling=low.make_plan(0,0,capacity=False);inputs=low.native.platform_inputs()
    cap=runner.make_plan(sampling,**inputs,capacity=True,workers=8,completed_evidence=evidence())
    full=runner.make_plan(sampling,**inputs,capacity=False,workers=4,completed_evidence=evidence())
    rows=[dict(group=list(g),status="ok",planned_tasks=160,failed_audits=0,failed_sampling=0,
               redecoded_checkpoints=10720,summary_group_digest_verified=True,wall_seconds=10.,cpu_seconds=8.,peak_rss_mb=128.)
          for g in runner.groups(cap)]
    summary=dict(manifest=c.digest(cap),groups=8,planned_tasks=1280,failed_audit_groups=0,failed_sampling=0,
                 input_changes=[],context_error=None,native_platform_verified=True,phase_wall_seconds=12.,records=rows)
    return cap,summary,full


def test_phase_rehash_overhead_is_included_and_full_workers_not_an_input():
    cap,summary,full=fixture_plans()
    result=m.resource_plan(cap,summary,full)
    assert result["workers"]==96 and result["memory_gb"]==32
    assert result["predicted_group_seconds"]==80
    assert result["predicted_phase_overhead_seconds"]==192
    assert result["predicted_seconds"]==272 and result["wall_seconds"]==1800
    assert result["predicted_cpu_seconds"]==6144
    assert m.capacity_resources()["workers"]==8


@pytest.mark.parametrize("change",[
    lambda s:s["records"].pop(),lambda s:s.update(failed_audit_groups=1),
    lambda s:s.update(context_error="changed"),lambda s:s.update(input_changes=[{}]),
    lambda s:s.update(failed_sampling=1),lambda s:s["records"][0].update(failed_sampling=1),
    lambda s:s["records"][0].update(wall_seconds=float("nan")),
    lambda s:s["records"][0].update(peak_rss_mb=None),
    lambda s:s["records"][0].update(cpu_seconds=-1.),
    lambda s:s.update(phase_wall_seconds=9.),lambda s:s.update(phase_wall_seconds=1000.),
    lambda s:s["records"][0].update(peak_rss_mb=400000.),
    lambda s:s["records"][0].update(summary_group_digest_verified=False)])
def test_incomplete_failed_lower_bound_or_excessive_capacity_rejected(change):
    cap,summary,full=fixture_plans();change(summary)
    with pytest.raises(ValueError):m.resource_plan(cap,summary,full)


@pytest.mark.parametrize("field,value",[("workers",4),("replicates",3),("purpose","low_noise_trace_audit_full")])
def test_capacity_must_be_eight_workers_and_exact_subset(field,value):
    cap,summary,full=fixture_plans();cap[field]=value
    with pytest.raises(ValueError):m.resource_plan(cap,summary,full)


def test_different_full_sampling_or_source_rejected():
    cap,summary,full=fixture_plans()
    for field in ("sampling_manifest","source_sha256","completed_phase_evidence"):
        altered=deepcopy(full);altered[field]="different"
        with pytest.raises(ValueError):m.resource_plan(cap,summary,altered)


def test_measured_partition_capacity_checks_terminal_payloads_and_plan(tmp_path, monkeypatch):
    from test_tile_low_noise_partitioned_trace_audit import saved_partition_capacity
    source, root, sampling, cap, summary, _ = saved_partition_capacity(tmp_path, monkeypatch)
    inputs = low.native.platform_inputs()
    full = runner.make_plan(sampling, **inputs, capacity=False, workers=96,
        completed_evidence=cap["completed_phase_evidence"], input_sha256=cap["input_sha256"])
    result = m.measured_capacity(root, source, full)
    assert result["workers"] == 96 and result["native_platform_verified"] is True
    assert result["pbs_job_id"] == "201.fixture"
    assert "terminal.json" in result["evidence_sha256"]
    prepared = m.prepare_full(tmp_path / "full-audit", source, root)
    assert prepared["plan"]["workers"] == result["workers"]
    first = root / "measurements" / (c.task_id(summary["records"][0]["group"]) + ".json")
    first.write_bytes(first.read_bytes() + b" ")
    with pytest.raises(ValueError):
        m.measured_capacity(root, source, full)

