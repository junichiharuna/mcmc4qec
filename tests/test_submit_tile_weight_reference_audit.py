"""Full reference audit submission binds the source job and never retries."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

import pytest
for dependency in ("ldpc","bposd","pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import submit_tile_weight_reference_audit as s


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    bundle=tmp_path/"bundle"
    root=bundle/"runs/audit"
    source=tmp_path/"reference"
    root.mkdir(parents=True);source.mkdir()
    for name,path in s.source_files().items():
        target=bundle/"cluster_scripts"/name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(path,target)
    shutil.copytree(Path(c.qec.__file__).parent,bundle/"src/mcmc4qec",ignore=shutil.ignore_patterns("__pycache__"))
    python=bundle/"venv/bin/python"
    python.parent.mkdir(parents=True);python.write_bytes(b"fixture executable")
    plan=dict(reference_context=dict(reference=dict(runtime=c.runtime())),reference_root=str(source.resolve()),
              original_pbs_job_id="123.cluster",conditions=list(range(16)),workers=16,resources=s.resources())
    c.atomic_json(root/"manifest.json",plan)
    monkeypatch.setattr(s.r,"read_plan",lambda *_:plan)
    return bundle,root,source,plan


def runner(calls,state="F",response="555.cluster",error=None):
    def invoke(command,**kwargs):
        calls.append(command)
        if command[0]=="qstat":
            return subprocess.CompletedProcess(command,0,stdout=json.dumps({"Jobs":{"123.cluster":{"job_state":state}}}))
        assert command[0]=="qsub"
        if error: raise error(command,30)
        return subprocess.CompletedProcess(command,0,stdout=response)
    return invoke


def test_dry_run_then_terminal_source_and_exactly_one_qsub(prepared):
    bundle,root,source,_=prepared
    result=s.submit(bundle,root,source,controller_query=lambda:pytest.fail("dry-run query"))
    assert result["job_id"]=="dry-run" and result["resource"]["measured"] is False
    calls=[]
    def submit(command,**kwargs):
        if command[0]=="qsub":
            assert (root/"submission-intent.json").exists()
            assert (bundle.parent/"tile-low-noise-submission.lock").exists()
        return runner(calls)(command,**kwargs)
    result=s.submit(bundle,root,source,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=submit)
    assert [row[0] for row in calls]==["qstat","qsub"] and result["job_id"]=="555.cluster"
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()
    assert "--reference-root" in (root/"weight-reference-audit.sh").read_text()
    with pytest.raises(ValueError): s.submit(bundle,root,source)


@pytest.mark.parametrize("kind",["controller","queued","source_running","timeout","bad_id"])
def test_guards_and_ambiguous_submission(prepared,kind):
    bundle,root,source,_=prepared
    calls=[]
    jobs={"queued":{"job_state":"Q","Resource_List":{"select":"2:ncpus=96"}}} if kind=="queued" else {}
    call=runner(calls,state="R" if kind=="source_running" else "F",response="bad" if kind=="bad_id" else "555.cluster",
                error=subprocess.TimeoutExpired if kind=="timeout" else None)
    with pytest.raises((ValueError,RuntimeError,subprocess.SubprocessError)):
        s.submit(bundle,root,source,execute=True,controller_query=lambda:[1] if kind=="controller" else [],
                 active_query=lambda:jobs,runner=call)
    ambiguous=kind in ("timeout","bad_id")
    assert (root/"submission-intent.json").exists()==ambiguous
    assert (bundle.parent/"tile-low-noise-submission.lock").exists()==ambiguous
    assert sum(row[0]=="qsub" for row in calls)==int(ambiguous)


@pytest.mark.parametrize("name",["execution-intent.json","summary.json","conditions","submission.json","submission-intent.json"])
def test_existing_output_rejected(prepared,name):
    bundle,root,source,_=prepared
    (root/name).write_text("existing")
    with pytest.raises(ValueError): s.submit(bundle,root,source)


@pytest.mark.parametrize("name",["driver","package","python","script","manifest"])
def test_changed_input_refuses_qsub(prepared,name):
    bundle,root,source,_=prepared
    def mutate():
        paths=dict(driver=bundle/"cluster_scripts/tile_weight_reference_audit_run.py",
                   package=bundle/"src/mcmc4qec/__init__.py",python=bundle/"venv/bin/python",
                   script=root/"weight-reference-audit.sh",manifest=root/"manifest.json")
        paths[name].write_text("changed")
        return []
    calls=[]
    with pytest.raises(ValueError):
        s.submit(bundle,root,source,execute=True,controller_query=mutate,active_query=lambda:{},runner=runner(calls))
    assert not any(row[0]=="qsub" for row in calls)
    assert not (root/"submission-intent.json").exists()


def test_output_must_be_independent_and_contained(prepared):
    bundle,root,source,_=prepared
    for invalid in (bundle/"runs",bundle.parent/"outside",source):
        with pytest.raises(ValueError): s.submit(bundle,invalid,source)
    with pytest.raises(ValueError): s.submit(bundle,root,root)


@pytest.mark.parametrize("stage",["qstat","qsub"])
def test_nonzero_external_command_retains_intent_only_after_qsub(prepared,stage):
    bundle,root,source,_=prepared
    def invoke(command,**kwargs):
        if command[0]==stage: raise subprocess.CalledProcessError(1,command)
        return runner([])(command,**kwargs)
    with pytest.raises(subprocess.CalledProcessError):
        s.submit(bundle,root,source,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=invoke)
    assert (root/"submission-intent.json").exists()==(stage=="qsub")
    assert (bundle.parent/"tile-low-noise-submission.lock").exists()==(stage=="qsub")


@pytest.mark.parametrize("kind",["manifest","script","dependency"])
def test_symlink_escape_is_rejected(prepared,kind):
    bundle,root,source,_=prepared
    outside=bundle.parent/"outside"
    outside.mkdir()
    path=dict(manifest=root/"manifest.json",script=root/"weight-reference-audit.sh",
              dependency=bundle/"cluster_scripts/tile_weight_reference_audit_run.py")[kind]
    target=outside/path.name
    if path.exists(): path.replace(target)
    else: target.write_text("external")
    try: path.symlink_to(target)
    except OSError: pytest.skip("symlink unavailable")
    with pytest.raises(ValueError,match="escapes"): s.submit(bundle,root,source)
