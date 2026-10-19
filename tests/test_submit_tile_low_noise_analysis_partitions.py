"""Fixed-resource partition qsub is exclusive and never automatically retried."""
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest

for dependency in ("ldpc","bposd","pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_analysis_capacity as cap
import submit_tile_low_noise_analysis_partitions as s


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    bundle=tmp_path/"bundle"
    root=bundle/"runs/production"
    root.mkdir(parents=True)
    for name,source in s.source_files().items():
        target=bundle/"cluster_scripts"/name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source,target)
    shutil.copytree(Path(c.qec.__file__).parent,bundle/"src/mcmc4qec",ignore=shutil.ignore_patterns("__pycache__"))
    python=bundle/"venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"fixture executable; qsub mocked")
    capacity=cap.make_plan(0,0)
    records=[dict(group=list(group),status="ok",synthetic=True,wall_seconds=4000,peak_rss_mb=20000)
             for group in cap.groups(capacity)]
    resource=cap.resource_plan(capacity,dict(manifest=c.digest(capacity),synthetic=True,failed=0,tasks=8,records=records))
    wrapper=dict(production=capacity["production"],resources=resource)
    monkeypatch.setattr(s.p,"read_plan",lambda path:wrapper)
    c.atomic_json(root/"partition_analysis_manifest.json",wrapper)
    return bundle,root,wrapper


def test_dry_run_and_single_qsub(prepared):
    bundle,root,wrapper=prepared
    result=s.submit(bundle,root,0,controller_query=lambda:pytest.fail("dry-run query"))
    destination=root/"analysis-submissions/0"
    assert result["job_id"]=="dry-run" and result["resource"]["workers"]==wrapper["resources"]["workers"]
    assert not (root/"analysis-partitions").exists()
    script=(destination/"partition.sh").read_text()
    assert f"select=1:ncpus=96:mem={wrapper['resources']['memory_gb']}gb" in script
    command=shlex.split(script.splitlines()[-1])
    assert command[1].endswith("tile_low_noise_analysis_partitions.py")
    assert command[2:]==["run","--root",str(root.resolve()),"--partition","0"]
    calls=[]
    def runner(command,**kwargs):
        assert command[0]=="qsub" and (destination/"submission-intent.json").exists()
        assert (bundle.parent/"tile-low-noise-submission.lock").exists()
        calls.append(command)
        return subprocess.CompletedProcess(command,0,stdout="555.cluster\n")
    result=s.submit(bundle,root,0,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert result["job_id"]=="555.cluster" and len(calls)==1
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()
    with pytest.raises(ValueError): s.submit(bundle,root,0)


@pytest.mark.parametrize("mode",["controller","queued_nodes","query_error"])
def test_guard_blocks_without_leaving_submission_intent(prepared,mode):
    bundle,root,_=prepared
    def controllers():
        if mode=="query_error": raise RuntimeError("query failed")
        return ["live"] if mode=="controller" else []
    jobs={"queued":{"job_state":"Q","Resource_List":{"select":"2:ncpus=96"}}} if mode=="queued_nodes" else {}
    with pytest.raises((ValueError,RuntimeError)):
        s.submit(bundle,root,0,execute=True,controller_query=controllers,active_query=lambda:jobs,
                 runner=lambda *args,**kw:pytest.fail("qsub called"))
    assert not (root/"analysis-submissions/0/submission-intent.json").exists()
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()


@pytest.mark.parametrize("mode",["timeout","nonzero","bad_id"])
def test_ambiguous_response_keeps_shared_lock(prepared,mode):
    bundle,root,_=prepared
    def runner(command,**kwargs):
        if mode=="timeout": raise subprocess.TimeoutExpired(command,30)
        if mode=="nonzero": raise subprocess.CalledProcessError(1,command)
        return subprocess.CompletedProcess(command,0,stdout="unknown")
    with pytest.raises((RuntimeError,subprocess.SubprocessError)):
        s.submit(bundle,root,0,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert (root/"analysis-submissions/0/submission-intent.json").exists()
    assert (bundle.parent/"tile-low-noise-submission.lock").exists()


@pytest.mark.parametrize("name",["submission-intent.json","submission.json","execution_directory","group_json","group_npz","group_marker"])
def test_existing_evidence_rejected(prepared,name):
    bundle,root,wrapper=prepared
    if name=="execution_directory": (root/"analysis-partitions/0").mkdir(parents=True)
    elif name.startswith("group_"):
        ext={"group_json":".json","group_npz":".npz","group_marker":".done.json"}[name]
        path=root/"analysis"/(c.task_id(wrapper["resources"]["partitions"][0]["groups"][0])+ext)
        path.parent.mkdir();path.write_text("existing")
    else:
        path=root/"analysis-submissions/0"/name
        path.parent.mkdir(parents=True);path.write_text("existing")
    with pytest.raises(ValueError): s.submit(bundle,root,0)


@pytest.mark.parametrize("target",["driver","dependency","package","python","script","plan"])
def test_changes_between_checks_reject_before_qsub(prepared,target):
    bundle,root,wrapper=prepared
    def controllers():
        path={"driver":bundle/"cluster_scripts/tile_low_noise_analysis_partitions.py",
              "dependency":bundle/"cluster_scripts/tile_bar_analysis.py",
              "package":bundle/"src/mcmc4qec/__init__.py","python":bundle/"venv/bin/python",
              "script":root/"analysis-submissions/0/partition.sh","plan":root/"partition_analysis_manifest.json"}[target]
        path.write_text("changed")
        return []
    with pytest.raises(ValueError):
        s.submit(bundle,root,0,execute=True,controller_query=controllers,active_query=lambda:{},
                 runner=lambda *args,**kwargs:pytest.fail("changed qsub"))
    assert not (root/"analysis-submissions/0/submission-intent.json").exists()
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()


def test_shared_lock_and_root_escape_rejected(prepared):
    bundle,root,_=prepared
    with pytest.raises(ValueError): s.submit(bundle,bundle.parent/"outside",0)
    with pytest.raises(ValueError): s.submit(bundle,bundle/"runs",0)
    (bundle.parent/"tile-low-noise-submission.lock").write_text("busy")
    with pytest.raises(FileExistsError): s.submit(bundle,root,0,execute=True)


@pytest.mark.parametrize("index",[-1,999,True,None])
def test_invalid_partition_rejected(prepared,index):
    bundle,root,_=prepared
    with pytest.raises(ValueError): s.submit(bundle,root,index)


def test_other_partition_ledger_does_not_block_one_remaining_node(prepared):
    bundle,root,_=prepared
    other=root/"analysis-submissions/1"
    other.mkdir(parents=True)
    c.atomic_json(other/"submission.json",dict(job_id="prior.cluster"))
    jobs={"prior":{"job_state":"Q","Resource_List":{"select":"1:ncpus=96"}}}
    result=s.submit(bundle,root,0,execute=True,controller_query=lambda:[],active_query=lambda:jobs,
                    runner=lambda command,**kwargs:subprocess.CompletedProcess(command,0,stdout="556.cluster"))
    assert result["job_id"]=="556.cluster"


@pytest.mark.parametrize("kind",["manifest","submissions","dependency"])
def test_symlink_escape_rejected(prepared,kind):
    bundle,root,_=prepared
    outside=bundle.parent/"outside"
    outside.mkdir()
    if kind=="manifest":
        original=root/"partition_analysis_manifest.json"
        target=outside/"manifest.json"
        original.replace(target)
    elif kind=="dependency":
        original=bundle/"cluster_scripts/tile_bar_analysis.py"
        target=outside/"dependency.py"
        original.replace(target)
    else:
        original=root/"analysis-submissions"
        target=outside
    try:
        original.symlink_to(target,target_is_directory=kind=="submissions")
    except OSError:
        pytest.skip("account cannot create symlinks")
    with pytest.raises(ValueError,match="escapes"):
        s.submit(bundle,root,0)
