"""Mocked qsub accepts one immutable case job and never retries uncertainty."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import submit_tile_final_reaggregation as s


@pytest.fixture
def setup(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"; root = bundle / "runs" / "case2"
    root.mkdir(parents=True)
    plan = dict(case=2, snapshot=dict(upstream_jobs={"sampling": "1.x", "analysis": "2.x", "trace_audit": "3.x"}))
    c.atomic_json(root / "manifest.json", plan)
    monkeypatch.setattr(s.r, "read_plan", lambda path: plan)
    monkeypatch.setattr(s, "bundle_binding", lambda *args: {"fixed": True})
    jobs = {job: dict(job_state="F", Exit_status=0) for job in plan["snapshot"]["upstream_jobs"].values()}
    calls = []
    def execute(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=json.dumps({"Jobs": jobs}) if command[0] == "qstat" else "99.cluster\n")
    return bundle, root, calls, execute


def test_dry_run_no_scheduler_call(setup):
    bundle, root, calls, runner = setup
    result = s.submit(bundle, root, runner=runner)
    assert not calls and result["job_id"] == "dry-run"
    script = (root / "reaggregate.sh").read_text()
    assert "select=1:ncpus=1:mem=32gb" in script and "walltime=02:00:00" in script
    assert "PYTHONDONTWRITEBYTECODE=1" in script


def test_submit_once_and_no_retry(setup):
    bundle, root, calls, runner = setup
    result = s.submit(bundle, root, execute=True, runner=runner, controller_query=lambda: [], active_query=lambda: {})
    assert result["job_id"] == "99.cluster" and sum(call[0] == "qsub" for call in calls) == 1
    assert not (bundle.parent / "tile-low-noise-submission.lock").exists()
    with pytest.raises(ValueError, match="existing"):
        s.submit(bundle, root, execute=True, runner=runner)


@pytest.mark.parametrize("controller,nodes", [(True, 0), (False, 2)])
def test_slot_and_controller_gates(setup, monkeypatch, controller, nodes):
    bundle, root, calls, runner = setup
    monkeypatch.setattr(s, "requested_nodes", lambda jobs: nodes)
    with pytest.raises(ValueError):
        s.submit(bundle, root, execute=True, runner=runner, controller_query=lambda: controller, active_query=lambda: {})
    assert not calls and not (root / "submission-intent.json").exists()


def test_uncertain_qsub_retains_intent_and_lock(setup):
    bundle, root, calls, runner = setup
    def ambiguous(command, **kwargs):
        if command[0] == "qsub": raise TimeoutError("unknown submission")
        return runner(command, **kwargs)
    with pytest.raises(TimeoutError):
        s.submit(bundle, root, execute=True, runner=ambiguous, controller_query=lambda: [], active_query=lambda: {})
    assert (root / "submission-intent.json").exists()
    assert (bundle.parent / "tile-low-noise-submission.lock").exists()


def test_script_mutation_before_qsub_rejected(setup):
    bundle, root, calls, runner = setup
    def changed(command, **kwargs):
        result = runner(command, **kwargs)
        (root / "reaggregate.sh").write_text("changed")
        return result
    with pytest.raises(ValueError):
        s.submit(bundle, root, execute=True, runner=changed, controller_query=lambda: [], active_query=lambda: {})
    assert not any(call[0] == "qsub" for call in calls)


def test_scheduler_environment_is_not_persisted():
    jobs = dict(sampling="1.x", analysis="2.x", trace_audit="3.x")
    original = {"Jobs": {job: dict(job_state="F", Exit_status=0, Submit_arguments="/script.sh",
                                  Variable_List={"UNRELATED": "private"}) for job in jobs.values()}, "server": "unused"}
    selected = s.selected_completion(original, jobs)
    assert set(selected) == {"Jobs"}
    assert all("Variable_List" not in row for row in selected["Jobs"].values())
    assert selected["Jobs"]["1.x"]["Submit_arguments"] == "/script.sh"
