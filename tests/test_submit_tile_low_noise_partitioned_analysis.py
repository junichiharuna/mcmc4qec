"""Partitioned-sampling BAR submission is one-shot and resource bounded."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import submit_tile_low_noise_partitioned_analysis as m


def fixture(tmp_path, monkeypatch):
    bundle = tmp_path/"bundle"
    root = bundle/"runs/production"
    root.mkdir(parents=True)
    wrapper = dict(production={"manifest": "fixture"}, resources=dict(cpus=96, memory_gb=32, workers=8,
        partitions=[dict(index=0, wall_seconds=1800, walltime="00:30:00", groups=[[0, 0, 0, 0, 0]])]))
    monkeypatch.setattr(m, "checked_plan", lambda *_: deepcopy(wrapper))
    monkeypatch.setattr(m, "bundle_binding", lambda *_: {"frozen": True})
    return bundle, root, wrapper


def test_qsub_once_then_ledger_blocks_repeat(tmp_path, monkeypatch):
    bundle, root, wrapper = fixture(tmp_path, monkeypatch)
    calls = []
    def runner(command, **kwargs):
        calls.append(command); return SimpleNamespace(stdout="123.fixture\n")
    result = m.submit(bundle, root, 0, execute=True, controller_query=lambda: [], active_query=lambda: {}, runner=runner)
    assert len(calls) == 1 and calls[0][0] == "qsub" and result["job_id"] == "123.fixture"
    assert "tile_low_noise_partitioned_analysis.py" in Path(calls[0][1]).read_text()
    with pytest.raises(ValueError, match="existing"):
        m.submit(bundle, root, 0, execute=True, controller_query=lambda: [], active_query=lambda: {}, runner=runner)
    assert len(calls) == 1


@pytest.mark.parametrize("guard", ["controller", "nodes", "lock", "ambiguous", "source"])
def test_submission_guards(tmp_path, monkeypatch, guard):
    bundle, root, wrapper = fixture(tmp_path, monkeypatch)
    calls = []
    def runner(command, **kwargs):
        calls.append(command); return SimpleNamespace(stdout="ambiguous response")
    controller = lambda: ["live"] if guard == "controller" else []
    if guard == "nodes": monkeypatch.setattr(m, "requested_nodes", lambda _: 2)
    if guard == "lock": (bundle.parent/"tile-low-noise-submission.lock").write_text("reserved")
    if guard == "source":
        count = []
        def binding(*args): count.append(1); return {"generation": len(count)}
        monkeypatch.setattr(m, "bundle_binding", binding)
    with pytest.raises((ValueError, FileExistsError, RuntimeError)):
        m.submit(bundle, root, 0, execute=True, controller_query=controller, active_query=lambda: {}, runner=runner)
    assert len(calls) == (1 if guard == "ambiguous" else 0)
    if guard == "ambiguous":
        assert (bundle.parent/"tile-low-noise-submission.lock").exists()
        assert (root/"analysis-submissions/0/submission-intent.json").exists()


def test_dry_run_has_no_scheduler_call(tmp_path, monkeypatch):
    bundle, root, _ = fixture(tmp_path, monkeypatch)
    result = m.submit(bundle, root, 0, runner=lambda *_args, **_kw: pytest.fail("qsub"))
    assert result["job_id"] == "dry-run"
    assert not (root/"analysis-submissions/0/submission-intent.json").exists()
