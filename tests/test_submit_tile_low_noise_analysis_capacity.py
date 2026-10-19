"""One-shot synthetic capacity submission and mutable-input rejection."""
import json
from pathlib import Path
import shutil
import shlex
import subprocess
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_analysis_capacity as m
import submit_tile_low_noise_analysis_capacity as s


@pytest.fixture
def prepared(tmp_path):
    bundle=tmp_path/"bundle"
    root=bundle/"runs/capacity"
    root.mkdir(parents=True)
    for name,source in s.source_files().items():
        target=bundle/"cluster_scripts"/name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source,target)
    shutil.copytree(Path(c.qec.__file__).parent,bundle/"src/mcmc4qec",ignore=shutil.ignore_patterns("__pycache__"))
    python=bundle/"venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"fixture executable; qsub is mocked")
    c.atomic_json(root/"manifest.json",m.make_plan(0,0))
    for key,value in m.low.native.platform_inputs().items():
        c.atomic_json(root/(key+".json"),value)
    return bundle,root


def test_dry_run_and_success(prepared):
    bundle,root=prepared
    result=s.submit(bundle,root,controller_query=lambda:pytest.fail("dry-run query"))
    assert result["job_id"]=="dry-run" and result["resource"]["workers"]==8
    text=(root/"analysis-capacity.sh").read_text()
    assert "select=1:ncpus=96:mem=340gb" in text and "walltime=24:00:00" in text
    invocation=shlex.split(text.splitlines()[-1])
    assert invocation[1].endswith("tile_low_noise_analysis_capacity.py")
    assert invocation[2:]==["run","--root",str(root.resolve())]
    calls=[]
    def runner(cmd,**kwargs):
        assert cmd[0]=="qsub" and (root/"submission-intent.json").exists()
        assert (bundle.parent/"tile-low-noise-submission.lock").exists()
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd,0,stdout="123.cluster\n")
    result=s.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert result["job_id"]=="123.cluster" and len(calls)==1
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()
    with pytest.raises(ValueError):s.submit(bundle,root,execute=True)


@pytest.mark.parametrize("mode",["controller","nodes","query_error"])
def test_guard_releases_lock_without_intent(prepared,mode):
    bundle,root=prepared
    def controllers():
        if mode=="query_error":raise RuntimeError("query failed")
        return ["live"] if mode=="controller" else []
    jobs={"queued":{"job_state":"Q","Resource_List":{"select":"2:ncpus=96"}}} if mode=="nodes" else {}
    with pytest.raises((ValueError,RuntimeError)):
        s.submit(bundle,root,execute=True,controller_query=controllers,active_query=lambda:jobs,
                 runner=lambda *a,**k:pytest.fail("unauthorized qsub"))
    assert not (root/"submission-intent.json").exists()
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()


@pytest.mark.parametrize("mode",["timeout","bad_id","nonzero"])
def test_ambiguous_submission_retains_lock(prepared,mode):
    bundle,root=prepared
    def runner(cmd,**kwargs):
        if mode=="timeout":raise subprocess.TimeoutExpired(cmd,30)
        if mode=="nonzero":raise subprocess.CalledProcessError(1,cmd)
        return subprocess.CompletedProcess(cmd,0,stdout="unknown")
    with pytest.raises((RuntimeError,subprocess.SubprocessError)):
        s.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert (root/"submission-intent.json").exists()
    assert (bundle.parent/"tile-low-noise-submission.lock").exists()


@pytest.mark.parametrize("name",["submission-intent.json","submission.json","execution-intent.json","summary.json","profiles"])
def test_existing_outputs_rejected(prepared,name):
    bundle,root=prepared
    (root/name).write_text("prior")
    with pytest.raises(ValueError):s.submit(bundle,root)


def test_shared_lock_rejected(prepared):
    bundle,root=prepared
    (bundle.parent/"tile-low-noise-submission.lock").write_text("busy")
    with pytest.raises(FileExistsError):s.submit(bundle,root,execute=True)


@pytest.mark.parametrize("target",["source","package","native","manifest","purpose"])
def test_changed_inputs_rejected(prepared,target):
    bundle,root=prepared
    if target=="source":(bundle/"cluster_scripts/tile_bar_analysis.py").write_text("changed")
    if target=="package":(bundle/"src/mcmc4qec/__init__.py").write_text("changed")
    if target=="native":(root/"platform_fixture.json").write_text("{}")
    if target in ("manifest","purpose"):
        plan=json.loads((root/"manifest.json").read_text())
        plan["workers" if target=="manifest" else "purpose"]=96 if target=="manifest" else "low_noise_capacity"
        c.atomic_json(root/"manifest.json",plan)
    with pytest.raises(ValueError):s.submit(bundle,root)


def test_root_escape_rejected(prepared):
    bundle,root=prepared
    with pytest.raises(ValueError):s.submit(bundle,bundle.parent/"other")
    with pytest.raises(ValueError):s.submit(bundle,bundle)


def test_manifest_symlink_escape_rejected(prepared):
    bundle,root=prepared
    original=root/"manifest.json"
    outside=bundle.parent/"external-manifest.json"
    original.replace(outside)
    try:
        original.symlink_to(outside)
    except OSError:
        pytest.skip("Windows account cannot create symlinks")
    with pytest.raises(ValueError,match="escapes"):
        s.submit(bundle,root)


@pytest.mark.parametrize("target",["source","script","python"])
def test_qsub_recheck_detects_change(prepared,target):
    bundle,root=prepared
    def controllers():
        path={"source":bundle/"cluster_scripts/tile_bar_analysis.py",
              "script":root/"analysis-capacity.sh","python":bundle/"venv/bin/python"}[target]
        path.write_text("changed between checks")
        return []
    with pytest.raises(ValueError):
        s.submit(bundle,root,execute=True,controller_query=controllers,active_query=lambda:{},
                 runner=lambda *a,**k:pytest.fail("changed qsub"))
    assert not (root/"submission-intent.json").exists()
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()
