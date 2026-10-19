"""One-shot scheduler contracts; no actual scheduler calls."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import submit_tile_low_noise_sampling_partitions as s


@pytest.fixture
def setup(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"; root = bundle / "runs/full"
    root.mkdir(parents=True)
    resource = dict(cpus=96, workers=96, memory_gb=32, requested_nodes=1, max_nodes=2,
                    partitions=[dict(index=0, replicate_range=[0, 192], tasks=1, wall_seconds=3600, walltime="01:00:00")])
    wrapper = dict(production={}, capacity_evidence=dict(pbs_job_id="1.x"), resources={"sample":resource,"anchors":resource})
    monkeypatch.setattr(s.p,"read_plan",lambda _:wrapper)
    monkeypatch.setattr(s.p,"tasks_for_partition",lambda *args:[(0,0,0,0,0,0,0)])
    monkeypatch.setattr(s,"bundle_binding",lambda *args:{"fixed":True})
    calls=[]
    def runner(command,**kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=json.dumps({"Jobs":{"1.x":dict(job_state="F",Exit_status=0)}}) if command[0]=="qstat" else "99.x\n")
    return bundle,root,wrapper,calls,runner


def test_dry_run_no_qsub(setup):
    bundle,root,wrapper,calls,runner=setup
    row=s.submit(bundle,root,"sample",0,runner=runner)
    assert row["job_id"]=="dry-run" and calls==[]
    script=(root/"sampling-submissions/sample/0/partition.sh").read_text()
    assert "select=1:ncpus=96:mem=32gb" in script and "walltime=01:00:00" in script
    assert "PYTHONDONTWRITEBYTECODE=1" in script and "--phase sample --index 0" in script


def test_once_no_retry(setup):
    bundle,root,wrapper,calls,runner=setup
    result=s.submit(bundle,root,"sample",0,execute=True,runner=runner,controller_query=lambda:[],active_query=lambda:{})
    assert result["job_id"]=="99.x" and sum(command[0]=="qsub" for command in calls)==1
    with pytest.raises(ValueError,match="existing"):
        s.submit(bundle,root,"sample",0,execute=True,runner=runner)


@pytest.mark.parametrize("controller,nodes",[(True,0),(False,2)])
def test_global_gates(setup,monkeypatch,controller,nodes):
    bundle,root,wrapper,calls,runner=setup
    monkeypatch.setattr(s,"requested_nodes",lambda _:nodes)
    with pytest.raises(ValueError):
        s.submit(bundle,root,"sample",0,execute=True,runner=runner,controller_query=lambda:controller,active_query=lambda:{})
    assert not calls


@pytest.mark.parametrize("kind",["timeout","ambiguous"])
def test_uncertain_keeps_lock_intent(setup,kind):
    bundle,root,wrapper,calls,runner=setup
    def uncertain(command,**kwargs):
        if command[0]=="qstat": return runner(command,**kwargs)
        if kind=="timeout": raise TimeoutError("uncertain")
        return SimpleNamespace(stdout="not a job id")
    with pytest.raises((TimeoutError,RuntimeError)):
        s.submit(bundle,root,"sample",0,execute=True,runner=uncertain,controller_query=lambda:[],active_query=lambda:{})
    assert (bundle.parent/"tile-low-noise-submission.lock").exists()
    assert (root/"sampling-submissions/sample/0/submission-intent.json").exists()


def test_qstat_then_mutation_prevents_qsub(setup):
    bundle,root,wrapper,calls,runner=setup
    def changed(command,**kwargs):
        result=runner(command,**kwargs)
        (root/"sampling-submissions/sample/0/partition.sh").write_text("changed")
        return result
    with pytest.raises(ValueError):
        s.submit(bundle,root,"sample",0,execute=True,runner=changed,controller_query=lambda:[],active_query=lambda:{})
    assert not any(command[0]=="qsub" for command in calls)


def test_collector_explicit_initial_budget(setup,monkeypatch):
    bundle,root,wrapper,calls,runner=setup
    monkeypatch.setattr(s,"completed_partitions",lambda *args,**kwargs:None)
    result=s.submit(bundle,root,"collect",None,runner=runner)
    assert result["resource"]["measured"] is False and result["resource"]["cpus"]==1
    assert "--phase" not in (root/"sampling-collection-submission/partition.sh").read_text()
