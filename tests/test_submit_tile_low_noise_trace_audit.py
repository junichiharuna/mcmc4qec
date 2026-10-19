"""One-shot low-noise trace audit submissions retain all immutable bindings."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import submit_tile_low_noise_trace_audit as s


def copy_bundle(bundle):
    for name, path in s.source_files().items():
        target = bundle / "cluster_scripts" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    shutil.copytree(Path(c.qec.__file__).parent, bundle / "src/mcmc4qec", ignore=shutil.ignore_patterns("__pycache__"))
    python = bundle / "venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"mocked executable")


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    root = bundle / "runs/audit"
    source = tmp_path / "sampling"
    capacity = tmp_path / "capacity"
    for path in (root, source, capacity):
        path.mkdir(parents=True)
    copy_bundle(bundle)
    sampling = dict(runtime=c.runtime())
    evidence = {}
    for index, phase in enumerate(("sample", "anchors")):
        path = source / f"{phase}-execution-intent.json"
        c.atomic_json(path, dict(phase=phase, manifest=c.digest(sampling), pbs_job_id=f"{123+index}.cluster"))
        evidence[phase] = dict(execution_intent_sha256=c.file_hash(path))
    plan = dict(purpose="low_noise_trace_audit_capacity", workers=8, replicates=2,
                sampling_manifest=c.digest(sampling), completed_phase_evidence=evidence)
    c.atomic_json(root / "manifest.json", plan)
    monkeypatch.setattr(s.r, "read_plan", lambda *_: (plan, sampling))
    return bundle, root, source, capacity, plan


def invocation(calls, *, state="F", response="555.cluster", error=None):
    def run(command, **kwargs):
        calls.append(command)
        if command[0] == "qstat":
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"Jobs": {command[-1]: {"job_state": state}}}))
        assert command[0] == "qsub"
        if error:
            raise error
        return subprocess.CompletedProcess(command, 0, stdout=response)
    return run


def test_capacity_dry_run_and_once(prepared):
    bundle, root, source, _, _ = prepared
    result = s.submit(bundle, root, source, controller_query=lambda: pytest.fail("dry query"))
    assert result["job_id"] == "dry-run" and result["resource"]["workers"] == 8
    assert "select=1:ncpus=96:mem=340gb" in (root / "trace-audit.sh").read_text()
    calls = []
    def run(command, **kwargs):
        if command[0] == "qsub":
            assert (root / "submission-intent.json").exists()
            assert (bundle.parent / "tile-low-noise-submission.lock").exists()
        return invocation(calls)(command, **kwargs)
    result = s.submit(bundle, root, source, execute=True, controller_query=lambda: [], active_query=lambda: {}, runner=run)
    assert [call[0] for call in calls] == ["qstat", "qstat", "qsub"]
    assert result["job_id"] == "555.cluster"
    assert not (bundle.parent / "tile-low-noise-submission.lock").exists()
    with pytest.raises(ValueError):
        s.submit(bundle, root, source)


@pytest.mark.parametrize("mode", ["controller", "queued", "source_running", "query_error", "timeout", "nonzero", "bad_id"])
def test_guards_and_uncertain_submissions(prepared, mode):
    bundle, root, source, _, _ = prepared
    calls = []
    def run(command, **kwargs):
        if mode == "query_error" and command[0] == "qstat":
            raise subprocess.CalledProcessError(1, command)
        error = (subprocess.TimeoutExpired(command, 30) if mode == "timeout" else
                 subprocess.CalledProcessError(1, command) if mode == "nonzero" else None)
        return invocation(calls, state="R" if mode == "source_running" else "F",
                          response="?" if mode == "bad_id" else "555.cluster", error=error)(command, **kwargs)
    jobs = {"q": {"Resource_List": {"select": "2:ncpus=96"}}} if mode == "queued" else {}
    with pytest.raises((ValueError, RuntimeError, subprocess.SubprocessError)):
        s.submit(bundle, root, source, execute=True, controller_query=lambda: [1] if mode == "controller" else [],
                 active_query=lambda: jobs, runner=run)
    ambiguous = mode in ("timeout", "nonzero", "bad_id")
    assert (root / "submission-intent.json").exists() == ambiguous
    assert (bundle.parent / "tile-low-noise-submission.lock").exists() == ambiguous
    assert sum(call[0] == "qsub" for call in calls) == int(ambiguous)


def full_plan(prepared, monkeypatch):
    bundle, root, source, capacity, plan = prepared
    plan.update(purpose="low_noise_trace_audit_full", workers=16, replicates=192)
    c.atomic_json(root / "manifest.json", plan)
    resource = dict(s.res.capacity_resources(), workers=16, memory_gb=64, measured=True)
    monkeypatch.setattr(s.res, "measured_capacity", lambda cap, src, full: resource)
    return resource


def test_full_requires_measured_capacity_and_matching_workers(prepared, monkeypatch):
    bundle, root, source, capacity, plan = prepared
    resource = full_plan(prepared, monkeypatch)
    with pytest.raises(ValueError, match="capacity"):
        s.submit(bundle, root, source)
    result = s.submit(bundle, root, source, capacity_root=capacity)
    assert result["resource"] == resource
    plan["workers"] = 8
    c.atomic_json(root / "manifest.json", plan)
    with pytest.raises(ValueError, match="worker"):
        s.submit(bundle, root, source, capacity_root=capacity)


def test_full_submits_measured_request_without_rewriting_plan(prepared, monkeypatch):
    bundle, root, source, capacity, _ = prepared
    resource = full_plan(prepared, monkeypatch)
    before = (root / "manifest.json").read_bytes()
    calls = []
    result = s.submit(bundle, root, source, capacity_root=capacity, execute=True,
                      controller_query=lambda: [], active_query=lambda: {}, runner=invocation(calls))
    assert result["resource"] == resource
    assert result["capacity_root"] == str(capacity.resolve())
    assert "mem=64gb" in (root / "trace-audit.sh").read_text()
    assert (root / "manifest.json").read_bytes() == before
    assert sum(call[0] == "qsub" for call in calls) == 1


def test_capacity_worker_count_is_fixed(prepared):
    bundle, root, source, _, plan = prepared
    plan["workers"] = 96
    c.atomic_json(root / "manifest.json", plan)
    with pytest.raises(ValueError, match="eight workers"):
        s.submit(bundle, root, source)


def test_shared_source_job_is_queried_once(prepared):
    bundle, root, source, _, plan = prepared
    path = source / "anchors-execution-intent.json"
    value = json.loads(path.read_text())
    value["pbs_job_id"] = "123.cluster"
    c.atomic_json(path, value)
    plan["completed_phase_evidence"]["anchors"]["execution_intent_sha256"] = c.file_hash(path)
    c.atomic_json(root / "manifest.json", plan)
    calls = []
    s.submit(bundle, root, source, execute=True, controller_query=lambda: [],
             active_query=lambda: {}, runner=invocation(calls))
    assert [call[0] for call in calls] == ["qstat", "qsub"]


def test_ledger_write_error_keeps_intent_and_lock(prepared, monkeypatch):
    bundle, root, source, _, _ = prepared
    original = c.atomic_json
    def write(path, value):
        if Path(path).name == "submission.json":
            raise OSError("ledger failure")
        return original(path, value)
    monkeypatch.setattr(c, "atomic_json", write)
    calls = []
    with pytest.raises(OSError):
        s.submit(bundle, root, source, execute=True, controller_query=lambda: [],
                 active_query=lambda: {}, runner=invocation(calls))
    assert sum(call[0] == "qsub" for call in calls) == 1
    assert (root / "submission-intent.json").exists()
    assert (bundle.parent / "tile-low-noise-submission.lock").exists()


@pytest.mark.parametrize("name", ["audit", "measurements", "execution-intent.json", "native_preflight.json", "summary.json", "submission.json", "submission-intent.json"])
def test_existing_evidence_rejected(prepared, name):
    bundle, root, source, _, _ = prepared
    (root / name).write_text("existing")
    with pytest.raises(ValueError):
        s.submit(bundle, root, source)


@pytest.mark.parametrize("target", ["driver", "package", "python", "script", "manifest", "source_intent"])
def test_mutated_binding_rejected_before_qsub(prepared, target):
    bundle, root, source, _, _ = prepared
    def change():
        path = {"driver": bundle / "cluster_scripts/tile_low_noise_trace_audit_run.py",
                "package": bundle / "src/mcmc4qec/__init__.py", "python": bundle / "venv/bin/python",
                "script": root / "trace-audit.sh", "manifest": root / "manifest.json",
                "source_intent": source / "sample-execution-intent.json"}[target]
        path.write_text("changed")
        return []
    calls = []
    with pytest.raises(ValueError):
        s.submit(bundle, root, source, execute=True, controller_query=change, active_query=lambda: {}, runner=invocation(calls))
    assert not any(call[0] == "qsub" for call in calls)
    assert not (root / "submission-intent.json").exists()


def test_full_resource_change_rejected(prepared, monkeypatch):
    bundle, root, source, capacity, _ = prepared
    resource = full_plan(prepared, monkeypatch)
    def change():
        resource["memory_gb"] = 128
        return []
    calls = []
    with pytest.raises(ValueError):
        s.submit(bundle, root, source, capacity_root=capacity, execute=True,
                 controller_query=change, active_query=lambda: {}, runner=invocation(calls))
    assert not any(call[0] == "qsub" for call in calls)


def test_roots_and_shared_lock(prepared):
    bundle, root, source, capacity, _ = prepared
    for invalid in (bundle / "runs", bundle.parent / "outside", source):
        with pytest.raises(ValueError): s.submit(bundle, invalid, source)
    with pytest.raises(ValueError): s.submit(bundle, root, root)
    with pytest.raises(ValueError): s.submit(bundle, root, source, capacity_root=root)
    (bundle.parent / "tile-low-noise-submission.lock").write_text("busy")
    with pytest.raises(FileExistsError): s.submit(bundle, root, source, execute=True)


@pytest.mark.parametrize("target", ["manifest", "script", "dependency", "source_intent"])
def test_symlink_escape(prepared, target):
    bundle, root, source, _, _ = prepared
    path = {"manifest": root / "manifest.json", "script": root / "trace-audit.sh",
            "dependency": bundle / "cluster_scripts/tile_low_noise_trace_audit_run.py",
            "source_intent": source / "sample-execution-intent.json"}[target]
    outside = bundle.parent / "outside-file"
    if path.exists(): path.replace(outside)
    else: outside.write_text("outside")
    try: path.symlink_to(outside)
    except OSError: pytest.skip("symlink unavailable")
    with pytest.raises(ValueError): s.submit(bundle, root, source)


def test_real_capacity_reader_prepare_full_and_submission_boundary(tmp_path, monkeypatch):
    from test_tile_low_noise_trace_audit_resources import saved_capacity
    # Uses actual short numerical trace audits and persisted measurement/group
    # artifacts. Native environment, clocks and PBS identity are explicit fixtures.
    source, capacity, _, cap_plan, summary, _ = saved_capacity(tmp_path, monkeypatch)
    bundle = tmp_path / "bundle"
    root = bundle / "runs/full-audit"
    copy_bundle(bundle)
    prepared_full = s.res.prepare_full(root, source, capacity)
    before = (root / "manifest.json").read_bytes()
    checked = s.res.measured_capacity(capacity, source, prepared_full["plan"])
    result = s.submit(bundle, root, source, capacity_root=capacity,
                      controller_query=lambda: pytest.fail("dry-run must not query"))
    assert result["resource"] == prepared_full["resource"] == checked
    assert result["resource"]["capacity_manifest"] == c.digest(cap_plan)
    assert result["resource"]["full_manifest"] == result["manifest"]
    assert result["resource"]["workers"] == prepared_full["plan"]["workers"]
    assert result["resource_basis"] == "measured_capacity"
    assert result["source_pbs_jobs"] == ["123.fixture"]
    assert (root / "manifest.json").read_bytes() == before
    assert not (root / "submission-intent.json").exists()
    raw = capacity / "measurements" / (c.task_id(summary["records"][0]["group"]) + ".json")
    raw.write_bytes(raw.read_bytes() + b" ")
    with pytest.raises(ValueError):
        s.submit(bundle, root, source, capacity_root=capacity)
