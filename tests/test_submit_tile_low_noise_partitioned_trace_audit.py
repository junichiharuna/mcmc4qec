"""All real upstream jobs and immutable two-node qsub submission gates."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import submit_tile_low_noise_partitioned_trace_audit as s


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    root = bundle / "runs/audit"
    source = tmp_path / "sampling"
    root.mkdir(parents=True)
    source.mkdir()
    for name, path in s.source_files().items():
        target = bundle / "cluster_scripts" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    shutil.copytree(Path(c.qec.__file__).parent, bundle / "src/mcmc4qec", ignore=shutil.ignore_patterns("__pycache__"))
    python = bundle / "venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"mocked executable")
    sampling = dict(runtime=c.runtime())
    jobs = [dict(phase=p, index=i, job_id=j, exit_status=e, completion_class=k)
            for p, i, j, e, k in (("sample", 0, "101.fixture", 0, "success"),
                                  ("sample", 1, "102.fixture", 2, "recorded_task_failures"),
                                  ("anchors", 0, "103.fixture", 0, "success"))]
    plan = dict(purpose="low_noise_trace_audit_capacity", workers=8, replicates=2,
                sampling_manifest=c.digest(sampling),
                completed_phase_evidence=dict(mode="partitioned_sampling", pbs_jobs=jobs,
                    collector_pbs_job=dict(phase="collect", job_id="104.fixture", exit_status=0)))
    c.atomic_json(root / "manifest.json", plan)
    monkeypatch.setattr(s.r, "read_plan", lambda *_: (plan, sampling))
    return bundle, root, source, plan


def invocation(calls, *, state="F", wrong_exit=False, response="555.fixture", timeout=False):
    def run(command, **kwargs):
        calls.append(command)
        if command[0] == "qstat":
            job = command[-1]
            code = 2 if job == "102.fixture" else 0
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"Jobs": {job:
                dict(job_state=state, Exit_status=99 if wrong_exit else code)}}))
        assert command[0] == "qsub"
        if timeout:
            raise subprocess.TimeoutExpired(command, 30)
        return subprocess.CompletedProcess(command, 0, stdout=response)
    return run


def test_queries_all_real_jobs_and_preserves_recorded_failure(prepared):
    bundle, root, source, _ = prepared
    calls = []
    result = s.submit(bundle, root, source, execute=True, controller_query=lambda: [],
                      active_query=lambda: {}, runner=invocation(calls))
    assert {call[-1] for call in calls if call[0] == "qstat"} == {"101.fixture", "102.fixture", "103.fixture", "104.fixture"}
    assert sum(call[0] == "qsub" for call in calls) == 1
    assert result["job_id"] == "555.fixture"
    assert result["bundle_binding"]["source_sha256"] == {name: c.file_hash(path) for name, path in s.source_files().items()}
    script = (root / "trace-audit.sh").read_text()
    assert "tile_low_noise_partitioned_trace_audit.py" in script
    assert "select=1:ncpus=96:mem=340gb" in script
    with pytest.raises(ValueError):
        s.submit(bundle, root, source)


@pytest.mark.parametrize("mode", ["running", "wrong_exit", "controller", "queued", "timeout", "bad_response"])
def test_guards_and_ambiguous_qsub(prepared, mode):
    bundle, root, source, _ = prepared
    calls = []
    runner = invocation(calls, state="R" if mode == "running" else "F", wrong_exit=mode == "wrong_exit",
                        response="?" if mode == "bad_response" else "555.fixture", timeout=mode == "timeout")
    jobs = {"queued": {"Resource_List": {"select": "2:ncpus=96"}}} if mode == "queued" else {}
    with pytest.raises((ValueError, RuntimeError, subprocess.TimeoutExpired)):
        s.submit(bundle, root, source, execute=True,
                 controller_query=lambda: [1] if mode == "controller" else [],
                 active_query=lambda: jobs, runner=runner)
    uncertain = mode in ("timeout", "bad_response")
    assert (root / "submission-intent.json").exists() == uncertain
    assert (bundle.parent / "tile-low-noise-submission.lock").exists() == uncertain
    assert sum(call[0] == "qsub" for call in calls) == int(uncertain)


@pytest.mark.parametrize("bad", ["duplicate", "no_anchor", "singleton", "bad_job"])
def test_upstream_partition_census_rejected(prepared, bad):
    bundle, root, source, plan = prepared
    proof = plan["completed_phase_evidence"]
    if bad == "duplicate":
        proof["pbs_jobs"][1] = proof["pbs_jobs"][0]
    elif bad == "no_anchor":
        proof["pbs_jobs"].pop()
    elif bad == "singleton":
        proof["mode"] = "single"
    else:
        proof["pbs_jobs"][0]["job_id"] = "fake"
    c.atomic_json(root / "manifest.json", plan)
    with pytest.raises(ValueError):
        s.submit(bundle, root, source)


def test_changed_additional_reader_blocks_submission(prepared):
    bundle, root, source, _ = prepared
    def changed():
        (bundle / "cluster_scripts/tile_low_noise_sampling_partitions.py").write_text("changed")
        return []
    calls = []
    with pytest.raises(ValueError):
        s.submit(bundle, root, source, execute=True, controller_query=changed,
                 active_query=lambda: {}, runner=invocation(calls))
    assert not any(call[0] == "qsub" for call in calls)


def test_full_requires_resource_evidence_and_exact_workers(prepared, monkeypatch):
    bundle, root, source, plan = prepared
    capacity = bundle.parent / "capacity"
    capacity.mkdir()
    plan.update(purpose="low_noise_trace_audit_full", workers=16, replicates=192)
    c.atomic_json(root / "manifest.json", plan)
    resource = dict(s.res.capacity_resources(), workers=16, memory_gb=64)
    monkeypatch.setattr(s.res, "measured_capacity", lambda *_: resource)
    with pytest.raises(ValueError, match="capacity"):
        s.submit(bundle, root, source)
    assert s.submit(bundle, root, source, capacity_root=capacity)["resource"] == resource
    plan["workers"] = 8
    c.atomic_json(root / "manifest.json", plan)
    with pytest.raises(ValueError, match="worker"):
        s.submit(bundle, root, source, capacity_root=capacity)


def test_existing_shared_lock_stops_submission(prepared):
    bundle, root, source, _ = prepared
    (bundle.parent / "tile-low-noise-submission.lock").write_text("busy")
    with pytest.raises(FileExistsError):
        s.submit(bundle, root, source, execute=True)


@pytest.mark.parametrize("gate", ["controller", "nodes"])
def test_last_gate_is_rechecked_after_expensive_validation(prepared, gate):
    bundle, root, source, _ = prepared
    counts = {"controller": 0, "nodes": 0}
    def controller():
        counts["controller"] += 1
        return [1] if gate == "controller" and counts["controller"] == 2 else []
    def nodes():
        counts["nodes"] += 1
        return {"queued": {"Resource_List": {"select": "2:ncpus=96"}}} if gate == "nodes" and counts["nodes"] == 2 else {}
    calls = []
    with pytest.raises(ValueError):
        s.submit(bundle, root, source, execute=True, controller_query=controller,
                 active_query=nodes, runner=invocation(calls))
    assert counts[gate] == 2
    assert not any(call[0] == "qsub" for call in calls)
    assert not (root / "submission-intent.json").exists()
