"""Small-fixture gates for the separate seed census PBS job."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import submit_tile_seed_audit as s


def test_resources_from_measured_pilot():
    result=s.resources(dict(checked_entries=1000,seconds=.06),3855274,256.,4096)
    assert result["cpus"]==1 and result["memory_gb"]==2
    assert result["wall_seconds"]==1800 and result["requested_nodes"]==1
    assert result["disk_required_bytes"]>=4*1024**3
    assert result["predicted_seconds"]==pytest.approx(462.63288)


@pytest.mark.parametrize("seconds,rss",[(1.,256.),(.06,4096.),(0.,256.),(.06,None),(.06,float("nan"))])
def test_invalid_or_excessive_pilot_rejected(seconds,rss):
    with pytest.raises(ValueError):s.resources(dict(checked_entries=1000,seconds=seconds),3855274,rss,4096)


def result_fixture():
    evidence={"planned_total":12,"reserved_unenumerated_stages":{"140":"pending","141":"pending"}}
    plan=dict(audit_evidence=evidence,auditor_sha256="a"*64)
    result=dict(evidence=evidence,auditor_sha256="a"*64,
                full=dict(complete=True,planned_entries=12,checked_entries=12,unchecked_entries=0,unexpected_collisions=0))
    return plan,result


def test_full_gate_does_not_erase_reservations():
    plan,result=result_fixture()
    gate=s.validate_result(plan,result)
    assert gate["planned_namespace_complete"] is True
    assert gate["all_goal_namespaces_complete"] is False
    assert set(gate["reserved_unenumerated_stages"])=={"140","141"}


@pytest.mark.parametrize("change",[
    lambda r:r.update(full=None),lambda r:r["full"].update(complete=False),
    lambda r:r["full"].update(checked_entries=11),lambda r:r["full"].update(unexpected_collisions=1),
    lambda r:r.update(auditor_sha256="b"*64),lambda r:r["evidence"].update(planned_total=13)])
def test_full_gate_rejects_partial_collided_or_changed_result(change):
    from copy import deepcopy
    plan,result=result_fixture()
    plan=deepcopy(plan)
    change(result)
    with pytest.raises(ValueError):s.validate_result(plan,result)


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    bundle=tmp_path/"bundle";root=bundle/"runs/seed-audit"
    root.mkdir(parents=True)
    plan=dict(resource=dict(cpus=1,memory_gb=2,walltime="00:30:00",disk_required_bytes=1),
              bundle=str(bundle),root=str(root))
    c.atomic_json(root/"manifest.json",plan)
    monkeypatch.setattr(s,"read_plan",lambda b,r:plan)
    return bundle,root,plan


def test_submit_success_intent_and_exact_command(prepared):
    bundle,root,plan=prepared
    dry=s.submit(bundle,root)
    assert dry["job_id"]=="dry-run"
    script=(root/"seed-audit.sh").read_text()
    assert "select=1:ncpus=1:mem=2gb" in script and "walltime=00:30:00" in script
    calls=[]
    def runner(cmd,**kwargs):
        assert (root/"submission-intent.json").exists()
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd,0,stdout="987.cluster\n")
    out=s.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert out["job_id"]=="987.cluster" and calls==[["qsub",str(root/"seed-audit.sh")]]
    assert not (bundle.parent/"tile-low-noise-submission.lock").exists()
    with pytest.raises(ValueError):s.submit(bundle,root)


@pytest.mark.parametrize("mode",["controller","nodes","unknown","timeout"])
def test_submit_failures_preserve_correct_intent_state(prepared,mode):
    bundle,root,_=prepared
    def runner(cmd,**kwargs):
        if mode=="timeout":raise subprocess.TimeoutExpired(cmd,30)
        if mode=="unknown":return subprocess.CompletedProcess(cmd,0,stdout="?")
        pytest.fail("qsub must not run")
    jobs={"q":{"job_state":"Q","Resource_List":{"select":"2:ncpus=96"}}} if mode=="nodes" else {}
    with pytest.raises((ValueError,RuntimeError,subprocess.TimeoutExpired)):
        s.submit(bundle,root,execute=True,controller_query=lambda:[1] if mode=="controller" else [],
                 active_query=lambda:jobs,runner=runner)
    assert (root/"submission-intent.json").exists()==(mode in ("unknown","timeout"))
    assert (bundle.parent/"tile-low-noise-submission.lock").exists()==(mode in ("unknown","timeout"))


def test_run_requires_pbs_and_refuses_existing_outputs(prepared,monkeypatch):
    bundle,root,_=prepared
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="PBS"):s.run(bundle,root)
    monkeypatch.setenv("PBS_JOBID","123.fixture")
    for name,value in s.THREADS.items():monkeypatch.setenv(name,value)
    (root/"result.json").write_text("prior")
    with pytest.raises(ValueError,match="existing"):s.run(bundle,root)


def test_small_actual_pilot_prepare_and_full_gate_runner(tmp_path,monkeypatch):
    import tile_seed_audit as audit
    bundle=tmp_path/"bundle";root=bundle/"runs/census"
    evidence=dict(planned_total=12,reserved_unenumerated_stages={"140":"pending","141":"pending"})
    monkeypatch.setattr(s,"baseline_runtime",lambda b:{})
    monkeypatch.setattr(s,"binding",lambda b,e:{"source":"fixture"})
    monkeypatch.setattr(s.audit,"catalog",lambda data:({"test":lambda:(audit.Entry("fixture",(777,i),0) for i in range(12))},evidence))
    monkeypatch.setattr(c,"peak_rss_mb",lambda:128.)
    plan=s.prepare(bundle,root)
    assert plan["pilot"]["checked_entries"]==12
    assert plan["resource"]["memory_gb"]==2
    assert s.read_plan(bundle,root)==plan
    with pytest.raises(ValueError,match="new empty"):s.prepare(bundle,root)
    monkeypatch.setenv("PBS_JOBID","123.fixture")
    for key,value in s.THREADS.items():monkeypatch.setenv(key,value)
    calls=[]
    def runner(command,**kwargs):
        calls.append(command)
        assert (root/"execution-intent.json").exists()
        assert command[-5:]==["--full","--max-seconds","1800","--output",str(root/"result.json")]
        assert kwargs["env"]["TMPDIR"]==str(root/"scratch")
        c.atomic_json(root/"result.json",dict(evidence=evidence,auditor_sha256=plan["auditor_sha256"],full=plan["pilot"]))
        return subprocess.CompletedProcess(command,0)
    result=s.run(bundle,root,runner=runner)
    assert result["planned_namespace_complete"] and not result["all_goal_namespaces_complete"]
    assert len(calls)==1 and (root/"completion.json").exists()
    with pytest.raises(ValueError):s.run(bundle,root,runner=runner)


def test_baseline_runtime_rejects_different_core(tmp_path):
    root=tmp_path/s.DATA
    root.mkdir(parents=True)
    value=c.runtime();value["package_sha256"]="changed"
    c.atomic_json(root/"production_manifest.json",dict(runtime=value))
    with pytest.raises(ValueError,match="baseline"):s.baseline_runtime(tmp_path)


def test_submission_rechecks_manifest_and_keeps_shared_lock(prepared,monkeypatch):
    bundle,root,plan=prepared
    (bundle.parent/"tile-low-noise-submission.lock").write_text("other submitter")
    with pytest.raises(FileExistsError):s.submit(bundle,root,execute=True)
    (bundle.parent/"tile-low-noise-submission.lock").unlink()
    def controller():
        plan["changed"]=True
        return []
    with pytest.raises(ValueError,match="changed"):
        s.submit(bundle,root,execute=True,controller_query=controller,active_query=lambda:{},
                 runner=lambda *a,**k:pytest.fail("changed input qsub"))
    assert not (root/"submission-intent.json").exists()


@pytest.fixture
def bar_inputs(tmp_path,monkeypatch):
    import tile_bar_time_benchmark as bt
    bundle=tmp_path/"bundle"
    def make_plan(settings,*,capacity,case):
        return dict(purpose="bar_time_capacity" if capacity else "bar_time_benchmark",
                    seed_stage=141 if capacity else 140,replicates=96 if capacity else 192,
                    case=case,conditions=settings["records"])
    monkeypatch.setattr(bt,"make_plan",make_plan)
    def create(name,*,capacity=False,case=None):
        root=bundle/"runs"/name;root.mkdir(parents=True)
        settings=dict(records=[dict(case=i,status="selected") for i in range(4)])
        c.atomic_json(root/"settings.json",settings)
        c.atomic_json(root/"manifest.json",make_plan(settings,capacity=capacity,case=case))
        return root/"manifest.json"
    return bundle,create


def test_bar_inputs_preserve_full_conditions(bar_inputs):
    bundle,create=bar_inputs
    paths=[create("main"),create("capacity",capacity=True)]
    records=s.bar_manifest_inputs(bundle,paths)
    assert [row["seed_stage"] for row in records]==[140,141]
    assert [row["case"] for row in records]==[None,None]
    for row,path in zip(records,paths):
        assert row["path"]==str(path.resolve()) and row["sha256"]==c.file_hash(path)
        assert row["settings_sha256"]==c.file_hash(path.parent/"settings.json")
        assert len(json.loads(path.read_text())["conditions"])==4


@pytest.mark.parametrize("mode",["same_path","same_payload","overlap_all","changed_replicates","missing_settings","escape","partial"])
def test_bar_inputs_reject_bad_or_duplicate_inputs(bar_inputs,tmp_path,mode):
    bundle,create=bar_inputs
    first=create("first")
    paths=[first]
    if mode=="same_path":paths.append(first)
    elif mode=="same_payload":paths.append(create("alias"))
    elif mode=="overlap_all":paths.append(create("all",case=None))
    elif mode=="changed_replicates":
        value=json.loads(first.read_text());value["replicates"]=1;c.atomic_json(first,value)
    elif mode=="missing_settings":(first.parent/"settings.json").unlink()
    elif mode=="escape":
        outside=tmp_path/"outside.json";outside.write_text(first.read_text());paths=[outside]
    with pytest.raises((ValueError,FileNotFoundError)):
        s.bar_manifest_inputs(bundle,paths)


def test_additional_bar_inputs_catalog_binding_and_run_forwarding(bar_inputs,monkeypatch):
    import tile_seed_audit as audit
    bundle,create=bar_inputs
    paths=[create("main"),create("capacity",capacity=True)]
    root=bundle/"runs/census"
    calls=[]
    def catalog(data,bar_timing_manifests=()):
        calls.append(list(bar_timing_manifests))
        evidence=dict(planned_total=12,reserved_unenumerated_stages={},
                      input_sha256={str(p.resolve()):c.file_hash(p) for p in paths},
                      plan_sha256={"bar.timing."+str(i):c.digest(json.loads(p.read_text())) for i,p in enumerate(paths)})
        return {"test":lambda:(audit.Entry("fixture",(777,i),0) for i in range(12))},evidence
    monkeypatch.setattr(s.audit,"catalog",catalog)
    monkeypatch.setattr(s,"baseline_runtime",lambda b:{})
    monkeypatch.setattr(s,"binding",lambda b,e:{"input_sha256":dict(e["input_sha256"])})
    monkeypatch.setattr(c,"peak_rss_mb",lambda:128.)
    plan=s.prepare(bundle,root,bar_timing_manifests=paths)
    assert calls==[[str(p.resolve()) for p in paths]]
    assert len(plan["bar_timing_manifests"])==2
    assert all(str(p.parent/"settings.json") in plan["binding"]["input_sha256"] for p in paths)
    assert s.read_plan(bundle,root)==plan
    monkeypatch.setenv("PBS_JOBID","123.fixture")
    for key,value in s.THREADS.items():monkeypatch.setenv(key,value)
    def runner(command,**kwargs):
        assert command[-4:]==["--bar-timing-manifest",str(paths[0]),"--bar-timing-manifest",str(paths[1])]
        c.atomic_json(root/"result.json",dict(evidence=plan["audit_evidence"],auditor_sha256=plan["auditor_sha256"],full=plan["pilot"]))
        return subprocess.CompletedProcess(command,0)
    assert s.run(bundle,root,runner=runner)["all_goal_namespaces_complete"]
    for path in (paths[0],paths[0].parent/"settings.json"):
        original=path.read_bytes();path.write_bytes(original+b" ")
        with pytest.raises(ValueError):s.read_plan(bundle,root)
        path.write_bytes(original)
        path.unlink()
        with pytest.raises(FileNotFoundError):s.read_plan(bundle,root)
        path.write_bytes(original)
    from copy import deepcopy
    for mode in ("duplicate","escape","removed"):
        changed=deepcopy(plan)
        if mode=="duplicate":changed["bar_timing_manifests"].append(changed["bar_timing_manifests"][0])
        elif mode=="escape":changed["bar_timing_manifests"][0]["path"]=str(bundle.parent/"outside.json")
        else:changed.pop("bar_timing_manifests")
        c.atomic_json(root/"manifest.json",changed)
        with pytest.raises(ValueError):s.read_plan(bundle,root)
    c.atomic_json(root/"manifest.json",plan)
    saved=json.loads((root/"manifest.json").read_text())
    saved["audit_evidence"]["plan_sha256"]["bar.timing.0"]="changed"
    c.atomic_json(root/"manifest.json",saved)
    with pytest.raises(ValueError):s.read_plan(bundle,root)


@pytest.mark.parametrize("unmet_cases",[(),(3,),(0,1,2,3)])
def test_real_bar_plan_reconstruction_retains_original_case_indices(tmp_path,unmet_cases):
    import tile_bar_time_benchmark as bt
    source=bt.b.make_plan()
    rows=[dict(case=case,epsilon=epsilon,status="selected",condition=dict(
        case=case,kernel="ZH",init="logical",chains=4,burn=600,samples=600,
        ladder="coarse",method="cross_chain",block=None)) for case in range(4) for epsilon in (.2,.1)]
    settings=dict(schema=1,purpose="standalone_bar_settings",sampling_manifest=c.digest(source),
                  selection_evidence_sha256=["a"*64],records=rows)
    for index,row in enumerate(rows):
        if row["case"] in unmet_cases:
            rows[index]=dict(case=row["case"],epsilon=row["epsilon"],status="unmet",reason="fixture")
    paths=[]
    for capacity in (False,True):
        for case in range(4):
            if capacity and case in unmet_cases:continue
            root=tmp_path/"runs"/(str(capacity)+str(case));root.mkdir(parents=True)
            plan=bt.make_plan(settings,capacity=capacity,case=case)
            c.atomic_json(root/"settings.json",settings)
            c.atomic_json(root/"manifest.json",plan)
            paths.append(root/"manifest.json")
            assert {task[0] for task in bt.tasks(plan)}==(set() if case in unmet_cases else {2*case,2*case+1})
            assert len(list(bt.tasks(plan)))==(0 if case in unmet_cases else 2*(96 if capacity else 192))
    records=s.bar_manifest_inputs(tmp_path,paths)
    assert [row["case"] for row in records]==list(range(4))+[case for case in range(4) if case not in unmet_cases]
    assert records[0]["selected_cases"]==[case for case in range(4) if case not in unmet_cases]


def test_all_unmet_plan_records_zero_capacity_without_clearing_reservation(bar_inputs,monkeypatch):
    import tile_seed_audit as audit
    import tile_bar_time_benchmark as bt
    bundle,create=bar_inputs
    path=create("empty-main")
    settings=dict(records=[dict(case=i,status="unmet",reason="fixture") for i in range(4)])
    payload=bt.make_plan(settings,capacity=False,case=None)
    c.atomic_json(path,payload);c.atomic_json(path.parent/"settings.json",settings)
    evidence=dict(planned_total=12,reserved_unenumerated_stages={"141":"not supplied"},
                  input_sha256={str(path):c.file_hash(path)},plan_sha256={"bar.timing.0":c.digest(payload)})
    monkeypatch.setattr(s.audit,"catalog",lambda *a,**k:({"test":lambda:(audit.Entry("fixture",(777,i),0) for i in range(12))},evidence))
    monkeypatch.setattr(s,"baseline_runtime",lambda b:{})
    monkeypatch.setattr(s,"binding",lambda b,e:{"input_sha256":dict(e["input_sha256"])})
    monkeypatch.setattr(c,"peak_rss_mb",lambda:128.)
    root=bundle/"runs/census"
    plan=s.prepare(bundle,root,bar_timing_manifests=[path])
    assert plan["bar_timing_coverage"]==dict(main_cases=[0,1,2,3],capacity_cases=[],zero_planned_seed_stages=[141])
    assert s.read_plan(bundle,root)==plan
    result=dict(evidence=evidence,auditor_sha256=plan["auditor_sha256"],full=plan["pilot"])
    assert not s.validate_result(plan,result)["all_goal_namespaces_complete"]


def test_cli_rejects_plan_input_override_for_run(monkeypatch):
    monkeypatch.setattr(sys,"argv",["submit_tile_seed_audit.py","run","--bundle","bundle","--root","root",
                                    "--bar-timing-manifest","extra.json"])
    with pytest.raises(SystemExit) as error:s.main()
    assert error.value.code==2
