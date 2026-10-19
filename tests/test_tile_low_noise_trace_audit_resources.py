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
import tile_low_noise_trace_audit_run as runner
import tile_low_noise_trace_audit_resources as m


def fixture_plans():
    sampling=low.make_plan(0,0,capacity=False);inputs=low.native.platform_inputs()
    cap=runner.make_plan(sampling,**inputs,capacity=True,workers=8,completed_evidence={})
    full=runner.make_plan(sampling,**inputs,capacity=False,workers=4,completed_evidence={})
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


def saved_capacity(tmp_path,monkeypatch):
    from test_tile_low_noise_trace_audit_run import tiny_fixture,completed_source
    source,root,sampling,_,_=tiny_fixture(tmp_path,monkeypatch)
    # Complete the fixed eight-group subset with actual short physical traces.
    for kernel in range(2):
        for initial in range(2):
            for rep in range(2):
                for task in runner.tasks_for_group(sampling,(0,0,kernel,initial,rep)):
                    assert low.sample_task((source,sampling,task))["status"]=="ok"
    completed_source(source,sampling)
    cap=runner.prepare(root,source,capacity=True,workers=8)
    profile=json.loads((root/"platform_profile.json").read_text())
    fixture=json.loads((root/"platform_fixture.json").read_text())
    full=runner.make_plan(sampling,profile,fixture,capacity=False,workers=4,
                         completed_evidence=cap["completed_phase_evidence"],input_sha256=cap["input_sha256"])
    monkeypatch.setenv("PBS_JOBID","456.fixture")
    for name,value in runner.THREADS.items():monkeypatch.setenv(name,value)
    native=dict(native_platform_verified=True,platform_profile=c.digest(profile),
                platform_fixture=c.digest(fixture),actual_profile="fixture current native digest")
    # Native platform and clocks are fixtures, raw numerical audit is real.
    monkeypatch.setattr(runner.audit,"validate_native_environment",lambda *a,**k:native)
    monkeypatch.setattr(c,"peak_rss_mb",lambda:128.)
    monkeypatch.setattr(c,"parallel_map",lambda fn,jobs,workers:[fn(job) for job in jobs])
    summary=runner.run(root,source)
    for row in summary["records"]:
        row.update(wall_seconds=1.,cpu_seconds=.8,peak_rss_mb=128.)
        identity=dict(manifest=c.digest(cap),group=row["group"])
        c.save_artifact(root/"measurements"/c.task_id(row["group"]),identity,{},row)
    summary["phase_wall_seconds"]=2.
    c.atomic_json(root/"summary.json",summary)
    script=root/"trace-audit.sh";script.write_text("fixture script")
    intent=dict(manifest=c.digest(cap),command=["qsub",str(script)],script_sha256=c.file_hash(script))
    c.atomic_json(root/"submission-intent.json",intent)
    c.atomic_json(root/"submission.json",dict(intent,job_id="456.fixture"))
    return source,root,sampling,cap,summary,full


def test_actual_saved_capacity_binding_and_tampered_evidence(tmp_path,monkeypatch):
    source,root,sampling,cap,summary,full=saved_capacity(tmp_path,monkeypatch)
    result=m.measured_capacity(root,source,full)
    assert result["workers"]==96 and result["native_platform_verified"]
    assert result["capacity_summary_sha256"]==c.file_hash(root/"summary.json")
    assert result["predicted_phase_overhead_seconds"]==96
    new_root=tmp_path/"full-audit"
    prepared=m.prepare_full(new_root,source,root)
    assert prepared["plan"]["workers"]==96
    assert prepared["resource"]["full_manifest"]==c.digest(prepared["plan"])
    assert json.loads((new_root/"manifest.json").read_text())==prepared["plan"]
    with pytest.raises(ValueError,match="new empty"):
        m.prepare_full(new_root,source,root)
    rejected_root=tmp_path/"rejected-full"
    saved_summary=(root/"summary.json").read_bytes()
    invalid=json.loads(saved_summary);invalid["failed_sampling"]=1
    c.atomic_json(root/"summary.json",invalid)
    with pytest.raises(ValueError):m.prepare_full(rejected_root,source,root)
    assert not rejected_root.exists()
    (root/"summary.json").write_bytes(saved_summary)
    for name,change in [
        ("execution-intent.json",lambda x:x.update(workers=4)),
        ("submission.json",lambda x:x.update(job_id="999.fixture")),
        ("native_preflight.json",lambda x:x["evidence"].update(actual_profile="different")),
        ("summary.json",lambda x:x["records"][0].update(wall_seconds=1.1))]:
        path=root/name;original=path.read_bytes();value=json.loads(original)
        change(value);c.atomic_json(path,value)
        with pytest.raises(ValueError):m.measured_capacity(root,source,full)
        path.write_bytes(original)
    # Even a self-consistently rehashed group artifact must retain every task.
    row=summary["records"][0];base=root/"audit/groups"/c.task_id(row["group"])
    identity=dict(manifest=c.digest(cap),group=row["group"])
    arrays,raw=c.load_artifact(base,identity)
    raw["tasks"].pop()
    c.save_artifact(base,identity,arrays,raw)
    row["audit_marker_sha256"]=c.file_hash(base.with_suffix(".done.json"))
    c.save_artifact(root/"measurements"/c.task_id(row["group"]),identity,{},row)
    c.atomic_json(root/"summary.json",summary)
    with pytest.raises(ValueError,match="task/checkpoint"):
        m.measured_capacity(root,source,full)


def test_prepare_full_rejects_capacity_alias_before_writes(tmp_path):
    with pytest.raises(ValueError,match="separate"):
        m.prepare_full(tmp_path/"capacity",tmp_path/"source",tmp_path/"capacity")
