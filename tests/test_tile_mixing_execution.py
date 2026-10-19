"""Cluster orchestration acceptance, no production JSON scans."""
import json
import math
import shlex
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_mixing_execution as run


def test_capacity_resources():
    assert run.resources()["wall_seconds"] == 1800
    assert run.resources()["requested_nodes"] == 1
    assert run.resources()["cpus"] == 1


def test_measured_resources():
    value = run.resources(dict(wall_seconds=2., peak_rss_mb=200.))
    assert value["wall_seconds"] == 5400
    assert value["memory_gb"] == 4
    assert value["measured"] is True


@pytest.mark.parametrize("wall,rss", [(0, 2), (-1, 2), (math.nan, 2), (2, math.inf), (60, 2), (2, 200000)])
def test_invalid_resources(wall, rss):
    with pytest.raises(ValueError):
        run.resources(dict(wall_seconds=wall, peak_rss_mb=rss))


def test_completion_requires_exact_script_and_success(tmp_path):
    script = tmp_path / "job.sh"; script.write_text("abc")
    receipt = {"Jobs": {"1.server": dict(job_state="F", Exit_status=0, Submit_arguments=shlex.quote(str(script)))}}
    run.check_job(receipt, "1.server", script)
    for key, value in [("job_state", "R"), ("Exit_status", 1), ("Submit_arguments", str(tmp_path / "other.sh"))]:
        bad = json.loads(json.dumps(receipt)); bad["Jobs"]["1.server"][key] = value
        with pytest.raises(ValueError): run.check_job(bad, "1.server", script)


def test_capacity_keeps_full_design_but_counts_one(tmp_path, monkeypatch):
    import test_tile_mixing_inventory as fixture
    p = fixture.plan(); record = fixture.record(p)
    root = tmp_path / "production"; root.mkdir()
    stem = "analysis/0-0-0-0"; (root / "analysis").mkdir()
    identity = dict(group=[0, 0, 0, 0])
    c.atomic_json(root / (stem + ".json"), record)
    marker = dict(identity=identity, sha256={".json": c.file_hash(root / (stem + ".json")), ".npz": "unused"})
    c.atomic_json(root / (stem + ".done.json"), marker)
    expected = {f"analysis/0-{k}-{i}-{rep}": dict(group=[0,k,i,rep]) for k in range(2) for i in range(2) for rep in range(192)}
    monkeypatch.setattr(run.audited, "_match_payload", lambda *args: None)
    out = tmp_path / "out"; out.mkdir()
    result = run.capacity_group(root, p, 0, {}, expected, out)
    assert result["groups_measured"] == 1
    assert result["planned_groups"] == 768
    assert result["group"] == [0,0,0,0]
    assert result["rows"] == 26
    assert "records" not in result
    record["group"] = [0,0,0,1]
    c.atomic_json(root / (stem + ".json"), record)
    with pytest.raises(ValueError): run.capacity_group(root,p,0,{},expected,out)


def test_execution_freshness(tmp_path):
    run.require_fresh(tmp_path)
    (tmp_path / "execution-intent.json").write_text("{}")
    with pytest.raises(ValueError): run.require_fresh(tmp_path)


@pytest.mark.parametrize("mode", ["capacity", "full"])
def test_runner_delegation_and_terminal_failure(tmp_path, monkeypatch, mode):
    for key,value in run.THREADS.items(): monkeypatch.setenv(key,value)
    monkeypatch.setenv("PBS_JOBID","1.server")
    plan=dict(mode=mode,case=0,snapshot=dict(production_root=str(tmp_path/"prod"),audited_results="audit",analysis_verification="verification"))
    monkeypatch.setattr(run,"read_plan",lambda root:plan)
    monkeypatch.setattr(run,"binding",lambda root,plan:{"ok":True})
    monkeypatch.setattr(run,"read_json",lambda path:{})
    monkeypatch.setattr(run.c,"file_hash",lambda path:"hash")
    monkeypatch.setattr(run.audited,"_verification",lambda *args:{})
    calls=[]
    def capacity(*args): calls.append("capacity"); return dict(groups_measured=1,planned_groups=768,group=[0,0,0,0])
    def full(*args):
        calls.append("full"); return dict(groups=768,replicates=192,rows=20,inventory_complete=False,rows_sha256="hash")
    monkeypatch.setattr(run,"capacity_group",capacity); monkeypatch.setattr(run.inventory,"run",full)
    result=run.run(tmp_path)
    assert calls==[mode] and result["complete"]
    if mode=="full": assert result["inventory_complete"] is False
    with pytest.raises(ValueError): run.run(tmp_path)


def test_guard_rejects_path_hash_change(tmp_path):
    path=tmp_path/"input"; path.write_text("first")
    guard={str(path):[str(path.resolve()),c.file_hash(path)]}
    run.guard_files(guard)
    path.write_text("second")
    with pytest.raises(ValueError): run.guard_files(guard)


def test_runner_terminal_change_is_failure(tmp_path,monkeypatch):
    for key,value in run.THREADS.items(): monkeypatch.setenv(key,value)
    monkeypatch.setenv("PBS_JOBID","1.server")
    plan=dict(mode="full",case=0,snapshot=dict(production_root="prod",audited_results="audit",analysis_verification="verification"))
    reads=iter([plan,dict(plan,case=1)])
    monkeypatch.setattr(run,"read_plan",lambda root:next(reads))
    monkeypatch.setattr(run,"binding",lambda *args:{})
    monkeypatch.setattr(run.c,"file_hash",lambda path:"hash")
    monkeypatch.setattr(run.inventory,"run",lambda *args:dict(groups=768,replicates=192,rows=20,inventory_complete=True,rows_sha256="hash"))
    with pytest.raises(RuntimeError): run.run(tmp_path)
    assert json.loads((tmp_path/"summary.json").read_text())["complete"] is False


@pytest.mark.parametrize("active,controllers", [([dict(Resource_List=dict(select="2:ncpus=1"))],[]),([],["controller"])])
def test_submit_rejects_occupied_budget(tmp_path,monkeypatch,active,controllers):
    import submit_tile_mixing_execution as submit
    bundle=tmp_path/"bundle"; root=bundle/"runs/cap"; root.mkdir(parents=True)
    plan=dict(case=0,resources=run.resources())
    monkeypatch.setattr(run,"read_plan",lambda root:plan)
    monkeypatch.setattr(submit,"bundle_binding",lambda *args:{})
    monkeypatch.setattr(submit,"requested_nodes",lambda jobs:2 if jobs else 0)
    calls=[]
    with pytest.raises(ValueError):
        submit.submit(bundle,root,execute=True,active_query=lambda:active,controller_query=lambda:controllers,runner=lambda *a,**k:calls.append(a))
    assert not calls and not (root/"submission-intent.json").exists()
    assert not (tmp_path/"tile-low-noise-submission.lock").exists()


@pytest.mark.parametrize("reply",["22.server","unrecognized response"])
def test_submit_exact_once_and_ambiguous_keeps_lock(tmp_path,monkeypatch,reply):
    from types import SimpleNamespace
    import submit_tile_mixing_execution as submit
    bundle=tmp_path/"bundle"; root=bundle/"runs/cap"; root.mkdir(parents=True)
    upstream=tmp_path/"final"
    plan=dict(case=0,resources=run.resources(),capacity=None,snapshot=dict(job_id="21.server",final_root=str(upstream)))
    monkeypatch.setattr(run,"read_plan",lambda root:plan)
    monkeypatch.setattr(submit,"bundle_binding",lambda *args:{})
    calls=[]
    def external(command,**kwargs):
        calls.append(command)
        if command[0]=="qstat":
            return SimpleNamespace(stdout=json.dumps({"Jobs":{"21.server":dict(job_state="F",Exit_status=0,
                Submit_arguments=shlex.quote(str(upstream/"reaggregate.sh")))}}))
        return SimpleNamespace(stdout=reply)
    kwargs=dict(execute=True,active_query=lambda:{},controller_query=lambda:[],runner=external)
    if reply=="22.server":
        assert submit.submit(bundle,root,**kwargs)["job_id"]==reply
        assert not (tmp_path/"tile-low-noise-submission.lock").exists()
    else:
        with pytest.raises(RuntimeError): submit.submit(bundle,root,**kwargs)
        assert (tmp_path/"tile-low-noise-submission.lock").exists()
    assert len([command for command in calls if command[0]=="qsub"])==1
    assert (root/"submission-intent.json").exists()
    with pytest.raises(ValueError): submit.submit(bundle,root,**kwargs)


def test_fixed_final_snapshot(tmp_path,monkeypatch):
    root=tmp_path/"final"; root.mkdir(); (root/"phases").mkdir()
    production=tmp_path/"production"; production.mkdir()
    verification=tmp_path/"verification.json"; verification.write_text("{}")
    receipt=tmp_path/"completion.json"
    plan=dict(case=0,evidence=dict(analysis_verification=str(verification)),production_root=str(production),snapshot=dict(runtime={}))
    for name in ("manifest.json","analysis_manifest.json"): (production/name).write_text("{}")
    c.atomic_json(root/"manifest.json",plan); (root/"reaggregate.sh").write_text("script")
    ledger=dict(job_id="1.server",manifest=c.digest(plan),script_sha256=c.file_hash(root/"reaggregate.sh"),command=["qsub",str(root/"reaggregate.sh")])
    c.atomic_json(root/"submission.json",ledger)
    c.atomic_json(root/"submission-intent.json",{k:v for k,v in ledger.items() if k!="job_id"})
    bound=dict(job_id="1.server",submission_sha256=c.file_hash(root/"submission.json"),intent_sha256=c.file_hash(root/"submission-intent.json"),script_sha256=ledger["script_sha256"])
    c.atomic_json(root/"execution-intent.json",dict(submission_binding=bound,pbs_job_id="1.server",manifest=c.digest(plan)))
    c.atomic_json(root/"phases/audited.json",{})
    measurement=dict(status="ok",pbs_job_id="1.server",manifest=c.digest(plan),output_sha256=c.file_hash(root/"phases/audited.json"))
    c.atomic_json(root/"phases/audited.measurement.json",measurement)
    summary=dict(complete=True,terminal_binding_valid=True,manifest=c.digest(plan),pbs_job_id="1.server",case=0,groups=768,replicates=192,
        execution_intent_sha256=c.file_hash(root/"execution-intent.json"),submission_binding=bound,
        records=[dict(phase="audited",status="ok",returncode=0,measurement=measurement,measurement_sha256=c.file_hash(root/"phases/audited.measurement.json"),output_sha256=measurement["output_sha256"])])
    c.atomic_json(root/"summary.json",summary)
    c.atomic_json(receipt,{"Jobs":{"1.server":dict(job_state="F",Exit_status=0,Submit_arguments=shlex.quote(str(root/"reaggregate.sh")))}})
    monkeypatch.setattr(run.final,"read_plan",lambda root:plan)
    monkeypatch.setattr(run.final,"validate_report",lambda *args:None)
    monkeypatch.setattr(run,"source_files",lambda:{"runner":Path(run.__file__)})
    assert run.inputs(root,receipt)["case"]==0
    summary["terminal_binding_valid"]=False; c.atomic_json(root/"summary.json",summary)
    with pytest.raises(ValueError): run.inputs(root,receipt)


@pytest.mark.parametrize("mutation",["changed_input","omitted_input","wrong_rows","nonfinite_cpu","bool_cpu"])
def test_capacity_consumed_inputs_and_counts(tmp_path,mutation):
    import test_tile_mixing_inventory as fixture
    p=fixture.plan(); c.atomic_json(tmp_path/"manifest.json",p); (tmp_path/"analysis").mkdir()
    paths=[tmp_path/"analysis"/("0-0-0-0"+suffix) for suffix in (".json",".done.json")]
    for path in paths: path.write_text("{}")
    summary=dict(rows=26,input_files={str(path):[str(path.resolve()),c.file_hash(path)] for path in paths},
                 wall_seconds=1.,peak_rss_mb=100.,cpu_seconds=0.)
    snapshot=dict(production_root=str(tmp_path),case=0)
    run.validate_capacity_measurement(summary,snapshot)
    if mutation=="changed_input": paths[0].write_text("changed")
    elif mutation=="omitted_input": summary["input_files"].pop(str(paths[0]))
    elif mutation=="wrong_rows": summary["rows"]+=1
    elif mutation=="nonfinite_cpu": summary["cpu_seconds"]=float("nan")
    else: summary["cpu_seconds"]=True
    with pytest.raises(ValueError): run.validate_capacity_measurement(summary,snapshot)
