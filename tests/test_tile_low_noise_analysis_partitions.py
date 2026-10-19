"""Partition routing never drops a planned group or unavailable outcome."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_analysis as a
import tile_low_noise_analysis_capacity as cap
import tile_low_noise_analysis_partitions as p


def fixture_plan():
    capacity=cap.make_plan(0,0)
    production=capacity["production"]
    records=[dict(group=list(group),status="ok",synthetic=True,wall_seconds=4000,peak_rss_mb=20000)
             for group in cap.groups(capacity)]
    resource=cap.resource_plan(capacity,dict(manifest=c.digest(capacity),synthetic=True,failed=0,tasks=8,records=records))
    return production,resource


def test_partition_union_exactly_preserves_all_768_groups():
    plan,resource=fixture_plan()
    p.validate_partitions(plan,resource)
    flat=[tuple(group) for part in resource["partitions"] for group in part["groups"]]
    assert flat==list(a.groups(plan)) and len(set(flat))==768


@pytest.mark.parametrize("change",["duplicate","missing","wrong_target","manifest","index","workers","memory","wall"])
def test_bad_partition_contract_rejected(change):
    plan,resource=fixture_plan()
    if change=="duplicate": resource["partitions"][-1]["groups"][-1]=resource["partitions"][0]["groups"][0]
    elif change=="missing": resource["partitions"][-1]["groups"].pop()
    elif change=="wrong_target": resource["partitions"][0]["groups"][0][1]=2
    elif change=="manifest": resource["production_manifest"]="bad"
    elif change=="index": resource["partitions"][0]["index"]=5
    elif change=="workers": resource["workers"]=97
    elif change=="memory": resource["memory_gb"]=341
    else: resource["partitions"][0]["wall_seconds"]=86401
    with pytest.raises(ValueError): p.validate_partitions(plan,resource)


def rows_fixture(plan,group):
    rows=[]
    for chains,burn,samples,index,label,ladder,block in a.analysis_settings(plan):
        rows.append(dict(group=list(group),case=group[0],target_p=plan["condition"]["target"],
            replicate=group[4],kernel=list(plan["kernels"])[group[2]],init=plan["initializations"][group[3]],
            noise=plan["condition"]["noise"],n=72,chains=chains,burn=burn,samples=samples,ladder=label,
            method="cross_chain" if block is None else "block",block=block,available=False,interval=None,
            failure="sampling_failed",undefined=True,flagged=True))
    return rows


@pytest.mark.parametrize("change",[None,"missing","duplicate","wrong_target","wrong_group","method"])
def test_group_rows_preserve_all_settings(change):
    plan,_=fixture_plan()
    group=next(a.groups(plan))
    rows=rows_fixture(plan,group)
    if change=="missing": rows.pop()
    elif change=="duplicate": rows[-1]=deepcopy(rows[0])
    if change=="wrong_target": rows[0]["target_p"] = .003
    elif change=="wrong_group": rows[0]["group"][-1]=1
    elif change=="method": rows[0]["method"]="other"
    if change:
        with pytest.raises(ValueError): p.validate_rows(plan,group,rows)
    else:
        p.validate_rows(plan,group,rows)
        assert all(not row["available"] for row in rows)


def test_run_requires_pbs_before_work(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="qsub"):
        p.run_partition(tmp_path,{},0)


def test_create_plan_reserves_old_runner_and_refuses_repeat(tmp_path,monkeypatch):
    production,resource=fixture_plan()
    capacity=cap.make_plan(0,0)
    caproot=tmp_path/"capacity"
    caproot.mkdir()
    c.atomic_json(caproot/"manifest.json",capacity)
    monkeypatch.setattr(a,"read_production_plan",lambda root:production)
    monkeypatch.setattr(a,"completed_phase_evidence",lambda root,plan:{"fixture":True})
    monkeypatch.setattr(cap,"measured_profile",lambda root,plan:resource)
    result=p.create_plan(tmp_path,caproot)
    reservation=json.loads((tmp_path/"analysis-execution-intent.json").read_text())
    assert reservation["mode"]=="partitioned" and "pbs_job_id" not in reservation
    assert reservation["partition_manifest"]==c.digest(result)
    with pytest.raises(ValueError,match="existing"):
        p.create_plan(tmp_path,caproot)


def raw_group_fixture(root):
    plan,_=fixture_plan()
    plan["condition"].update(chains=1,rungs=[.1],coarse=[.1],windows=[8])
    plan.update(burns=[0],blocks=[2],chain_counts=["maximum"])
    group=next(a.groups(plan))
    wrapper=dict(production=plan,analysis_context={"fixture":"context"})
    inputs={}
    for phase in ("sample","anchors"):
        task=(*group,0,0)
        folder=root/("traces" if phase=="sample" else "anchors")
        path=folder/c.task_id(task)
        c.save_artifact(path,dict(manifest=c.digest(plan),task=list(task)),{},dict(status="failed"))
        inputs[f"{phase}/{c.task_id(task)}"]=c.file_hash(path.with_suffix(".done.json"))
    record=dict(group=list(group),status="ok",rows=rows_fixture(plan,group),diagnostics=[],diagnostic_count=0,
                input_artifact_markers=inputs,failed_tasks=[list((*group,0,0))])
    base=root/"analysis"/c.task_id(group)
    identity=dict(analysis=c.digest(wrapper["analysis_context"]),group=list(group),input_artifact_markers=inputs)
    c.save_artifact(base,identity,{},record)
    return wrapper,group,base,identity


@pytest.mark.parametrize("change",[None,"raw","marker","input","missing_input","rows","acf","failed_task","acf_shape"])
def test_raw_analysis_artifacts_and_input_markers(tmp_path,change):
    wrapper,group,base,identity=raw_group_fixture(tmp_path)
    if change=="raw": base.with_suffix(".json").write_text("{}")
    elif change=="marker":
        marker=json.loads(base.with_suffix(".done.json").read_text())
        marker["sha256"].pop(".npz")
        c.atomic_json(base.with_suffix(".done.json"),marker)
    elif change in ("input","missing_input"):
        path=tmp_path/"traces"/(c.task_id((*group,0,0))+".done.json")
        if change=="input": path.write_text("{}")
        else: path.unlink()
    elif change in ("rows","acf","failed_task","acf_shape"):
        arrays,record=c.load_artifact(base,identity)
        if change=="rows": record["rows"].pop()
        elif change=="failed_task": record["failed_tasks"][0][-1]=99
        elif change=="acf_shape":
            import numpy as np
            record["diagnostics"]=[dict(acf_key="fixture",chains=1,samples=8)]
            record["diagnostic_count"]=1
            arrays["fixture"]=np.zeros((2,1))
        else:
            import numpy as np
            arrays["unexpected"]=np.zeros((1,1))
        c.save_artifact(base,identity,arrays,record)
    if change:
        with pytest.raises(ValueError): p.read_group(tmp_path,wrapper,group)
    else:
        record,digest=p.read_group(tmp_path,wrapper,group)
        assert len(record["rows"])==4 and digest


def collection_fixture(monkeypatch):
    plan,resource=fixture_plan()
    plan["condition"]["windows"]=[8]
    plan.update(burns=[0],blocks=[2],chain_counts=[4])
    wrapper=dict(production=plan,analysis_context={"fixture":True},resources=resource)
    monkeypatch.setattr(p,"read_plan",lambda root:wrapper)
    monkeypatch.setattr(p,"partition_evidence",lambda root,wrapper,index:({},f"partition-{index}"))
    def records(root,wrapper):
        for part in resource["partitions"]:
            for group in part["groups"]:
                yield dict(rows=rows_fixture(plan,tuple(group)),failed_tasks=[["recorded failure"]]),part["index"],f"partition-{part['index']}"
    monkeypatch.setattr(p,"validated_groups",records)
    return wrapper


def test_collect_and_read_preserve_full_denominator(tmp_path,monkeypatch):
    wrapper=collection_fixture(monkeypatch)
    result=p.collect(tmp_path)
    assert result["groups"]==result["failed_sampling_groups"]==768
    assert result["rows"]==result["unavailable_intervals"]==result["undefined_diagnostics"]==3072
    plan,rows,summary=p.read_collection(tmp_path)
    assert len(list(rows))==3072 and summary==result and plan==wrapper["production"]
    with pytest.raises(FileExistsError): p.collect(tmp_path)


@pytest.mark.parametrize("change",["rows_hash","row_rewrite","denominator","partition_hash"])
def test_read_collection_rejects_changes(tmp_path,monkeypatch,change):
    collection_fixture(monkeypatch)
    p.collect(tmp_path)
    destination=tmp_path/"partition-collection"
    summary=json.loads((destination/"summary.json").read_text())
    if change in ("rows_hash","row_rewrite"):
        path=destination/"rows.jsonl"
        lines=path.read_text().splitlines()
        row=json.loads(lines[0]); row["undefined"]=False
        lines[0]=c.canonical(row).decode()
        path.write_text("\n".join(lines)+"\n")
        if change=="row_rewrite": summary["rows_sha256"]=c.file_hash(path)
    elif change=="denominator": summary["rows"]-=1
    else: summary["partition_summary_sha256"]["0"]="changed"
    c.atomic_json(destination/"summary.json",summary)
    with pytest.raises(ValueError):
        plan,rows,summary=p.read_collection(tmp_path)
        list(rows)


def test_missing_partition_does_not_create_collection(tmp_path,monkeypatch):
    plan,resource=fixture_plan()
    monkeypatch.setattr(p,"read_plan",lambda root:dict(production=plan,resources=resource))
    with pytest.raises(ValueError,match="missing partition"):
        p.collect(tmp_path)
    assert not (tmp_path/"partition-collection").exists()


def partition_proof_fixture(root,monkeypatch):
    plan,resource=fixture_plan()
    wrapper=dict(production=plan,analysis_context={"fixture":True},resources=resource)
    part=resource["partitions"][0]
    destination=root/"analysis-partitions"/"0"
    destination.mkdir(parents=True)
    profile={"native":"fixture"}
    c.atomic_json(root/"platform_profile.json",profile)
    monkeypatch.setattr(low_native(),"validate_platform",lambda expected,actual:None)
    intent=dict(partition_manifest=c.digest(wrapper),partition=0,groups=part["groups"],workers=resource["workers"],
                manifest=c.digest(plan),pbs_job_id="fixture.pbs",hostname="fixture")
    c.atomic_json(destination/"execution-intent.json",intent)
    proof=dict(manifest=c.digest(plan),pbs_job_id="fixture.pbs",hostname="fixture",profile=profile)
    c.atomic_json(destination/"native_preflight.json",proof)
    summary=dict(**intent,execution_intent_sha256=c.file_hash(destination/"execution-intent.json"),
        native_preflight_sha256=c.file_hash(destination/"native_preflight.json"),
        group_marker_sha256={c.task_id(group):"fixture-hash" for group in part["groups"]},
        rows=len(part["groups"])*len(list(a.analysis_settings(plan))))
    c.atomic_json(destination/"summary.json",summary)
    return wrapper,destination


def low_native():
    return p.low.native.trace_audit


@pytest.mark.parametrize("change",[None,"empty_intent","native_job","native_hash","workers","row_count","group_count"])
def test_partition_completion_native_and_census_binding(tmp_path,monkeypatch,change):
    wrapper,destination=partition_proof_fixture(tmp_path,monkeypatch)
    summary=json.loads((destination/"summary.json").read_text())
    if change=="empty_intent":
        c.atomic_json(destination/"execution-intent.json",{})
        summary["execution_intent_sha256"]=c.file_hash(destination/"execution-intent.json")
    elif change=="native_job":
        proof=json.loads((destination/"native_preflight.json").read_text())
        proof["pbs_job_id"]="other"
        c.atomic_json(destination/"native_preflight.json",proof)
        summary["native_preflight_sha256"]=c.file_hash(destination/"native_preflight.json")
    elif change=="native_hash": summary["native_preflight_sha256"]="changed"
    elif change=="workers": summary["workers"]+=1
    elif change=="row_count": summary["rows"]-=1
    elif change=="group_count": summary["group_marker_sha256"].pop(next(iter(summary["group_marker_sha256"])))
    c.atomic_json(destination/"summary.json",summary)
    if change:
        with pytest.raises(ValueError): p.partition_evidence(tmp_path,wrapper,0)
    else:
        actual,digest=p.partition_evidence(tmp_path,wrapper,0)
        assert actual==summary and digest


def test_run_partition_uses_fixed_workers_and_reserves_before_preflight(tmp_path,monkeypatch):
    plan,resource=fixture_plan()
    plan["condition"]["windows"]=[8]
    plan.update(burns=[0],blocks=[2],chain_counts=[4])
    wrapper=dict(production=plan,analysis_context={"fixture":True},resources=resource)
    monkeypatch.setattr(p,"read_plan",lambda root:wrapper)
    monkeypatch.setenv("PBS_JOBID","fixture.pbs")
    for key,value in p.low.native.THREADS.items(): monkeypatch.setenv(key,value)
    for key,value in p.low.native.platform_inputs().items(): c.atomic_json(tmp_path/(key+".json"),value)
    def native(destination,production):
        assert (destination/"execution-intent.json").exists()
        return "fixture-native"
    monkeypatch.setattr(p.low.native,"native_preflight",native)
    def raw(group):
        return dict(group=list(group),rows=rows_fixture(plan,tuple(group)),diagnostics=[],failed_tasks=[])
    def parallel(worker,jobs,workers):
        assert workers==resource["workers"]
        assert [list(job[-1]) for job in jobs]==resource["partitions"][0]["groups"]
        return [{key:value for key,value in raw(job[-1]).items() if key!="diagnostics"} for job in jobs]
    monkeypatch.setattr(c,"parallel_map",parallel)
    monkeypatch.setattr(p,"read_group",lambda root,wrapper,group:(raw(group),"fixture-marker"))
    result=p.run_partition(tmp_path,wrapper,0)
    assert result["workers"]==resource["workers"] and result["rows"]==4*len(result["groups"])
    with pytest.raises(ValueError,match="automatic rerun"):
        p.run_partition(tmp_path,wrapper,0)
