"""Persisted fixed timing cohorts retain failures and bind native/reference evidence."""
import json
import hashlib
import io
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_mc_time_benchmark as mc
import tile_bar_time_benchmark as bar
import tile_timing_comparison as compare
from test_tile_bar_time_benchmark import settings


def fixture(root):
    budget=json.loads((Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json").read_text())
    chosen=settings()
    chosen["records"][1]=dict(case=0,epsilon=.1,status="unmet",reason="synthetic selection unmet")
    plans={"mc":mc.make_plan(budget,capacity=False),"bar":bar.make_plan(chosen,capacity=False,case=0)}
    references=[]
    models={}
    for case in range(4):
        r=budget["records"][case*2]
        # Minimal synthetic models exercise hash/identity binding without repeatedly
        # serializing hundreds of MB of parity matrices in a read-side unit test.
        models[case]={key:dict(synthetic_case=case,kind=key) for key in ("model","noise","decoder","failure")}
        references.append(dict(case=case,target_p=r["target_p"],estimate=r["reference_point"],
            interval_999=r["reference_interval_999"],standard_error=.0001))
    c.atomic_json(root/"reference.json",dict(records=references))
    c.atomic_json(root/"audit.json",dict(summary_sha256=c.file_hash(root/"reference.json"),all_seeds_verified=True,
        all_problem_metadata_verified=True,summary_reproduced=True,model_hashes={str(k):c.digest(v) for k,v in models.items()}))
    for method,plan in plans.items():
        path=root/method
        c.atomic_json(path/"manifest.json",plan)
        c.atomic_json(path/("budget.json" if method=="mc" else "settings.json"),budget if method=="mc" else chosen)
        inputs=mc.platform_inputs()
        for key,value in inputs.items():c.atomic_json(path/(key+".json"),value)
        bind=dict(manifest=c.digest(plan),pbs_job_id="synthetic.cluster",hostname="compute")
        c.atomic_json(path/"execution_intent.json",bind)
        c.atomic_json(path/"native_preflight.json",dict(**bind,profile=inputs["platform_profile"],wall_seconds=.1))
        records=[]
        driver=mc if method=="mc" else bar
        manifest_hash=c.digest(plan)
        (path/"tasks").mkdir()
        payload_cache={}
        for task in driver.tasks(plan):
            cond=plan["conditions"][task[0]]
            case=cond["case"]
            metadata=lambda p,seed:dict(**models[case],sampling_p=p,rng=dict(entropy=seed))
            arrays={}
            record=dict(task=list(task),replicate=task[1],case=case,epsilon=cond["epsilon"],status="ok",
                task_wall_seconds=2.,cpu_seconds=1.,problem_hash=c.digest(models[case]),estimate=references[case]["estimate"],
                interval=references[case]["interval_999"],available=True)
            if method=="mc":
                trials=cond["planned_trials"]
                failures=round(trials*record["estimate"])
                meta=metadata(cond["target_p"],mc.task_seed(plan,task))
                record.update(seed=mc.task_seed(plan,task),target_p=cond["target_p"],trials=trials,failures=failures,
                    estimate=failures/trials,metadata=meta,metadata_sha256=c.digest(meta))
            else:
                cfg=cond["condition"]
                anchor_seed=bar.task_seed(plan,task,0,0,0)
                record.update(condition=cfg,anchor_seed=anchor_seed,bootstrap_seed=bar.task_seed(plan,task,0,0,3),
                    anchor=dict(seed=anchor_seed,trials=plan["anchor_trials"],metadata=metadata(cond["rungs"][0],anchor_seed)),chains=[])
                for rung,p in enumerate(cond["rungs"]):
                    for chain in range(cfg["chains"]):
                        seed=bar.task_seed(plan,task,rung,chain,2)
                        record["chains"].append(dict(rung=rung,chain=chain,status="ok",init_seed=bar.task_seed(plan,task,rung,chain,1),
                            sample_seed=seed,metadata=metadata(p,seed)))
                arrays={"weight":np.ones((len(cond["rungs"]),cfg["chains"],cfg["samples"]),dtype=np.uint16)}
            # Construct static fixtures directly; atomic-writer behavior is tested separately.
            # Avoid thousands of fsync/replace/checksum cycles in this read-side test.
            if method not in payload_cache:
                buffer=io.BytesIO()
                np.savez_compressed(buffer,**arrays)
                payload_cache[method]=buffer.getvalue()
            payload=payload_cache[method]
            data=c.canonical(record)
            base=path/"tasks"/c.task_id(task)
            base.with_suffix(".npz").write_bytes(payload)
            base.with_suffix(".json").write_bytes(data)
            base.with_suffix(".done.json").write_bytes(c.canonical(dict(identity=dict(manifest=manifest_hash,task=list(task)),
                sha256={".npz":hashlib.sha256(payload).hexdigest(),".json":hashlib.sha256(data).hexdigest()})))
            reduced={k:v for k,v in record.items() if k not in (("metadata",) if method=="mc" else ("chains","anchor"))}
            if method=="bar":reduced["reused"]=False
            records.append(reduced)
        summary=dict(manifest=c.digest(plan),tasks=len(records),records=records,failed=0,phase_wall_seconds=100.,
                     native_preflight_sha256=c.file_hash(path/"native_preflight.json"))
        if method=="bar":summary.update(unavailable=0,reused_tasks=0)
        c.atomic_json(path/"summary.json",summary)
    return plans


def test_complete_artifacts_comparison_and_corruption_rejection(tmp_path):
    plans=fixture(tmp_path)
    kwargs=dict(mc_root=tmp_path/"mc",bar_root=tmp_path/"bar",reference_path=tmp_path/"reference.json",
                audit_path=tmp_path/"audit.json",case=0)
    result=compare.run(**kwargs,output=tmp_path/"result.json")
    assert len(result["records"])==2
    assert result["records"][0]["comparison"]["mc"]["replicates"]==192
    assert result["records"][0]["comparison"]["ratios_mc_over_bar"]["task_wall_seconds"]["value"]==1
    assert result["records"][1]["status"]=="selection_unmet"
    assert result["job_phases"]["mc"]["scope"]=="all_eight_conditions"
    assert result["job_phases"]["bar"]["scope"]=="selected_conditions_for_case"
    with pytest.raises(ValueError):compare.run(**kwargs,output=tmp_path/"result.json")
    audit=tmp_path/"audit.json"
    audit_bytes=audit.read_bytes()
    altered=json.loads(audit_bytes)
    altered["summary_sha256"]="0"*64
    c.atomic_json(audit,altered)
    with pytest.raises(ValueError):compare.run(**kwargs,output=tmp_path/"invalid.json")
    assert not (tmp_path/"invalid.json").exists()
    audit.write_bytes(audit_bytes)
    summary=tmp_path/"bar/summary.json"
    summary_bytes=summary.read_bytes()
    altered=json.loads(summary_bytes)
    altered["records"].pop()
    c.atomic_json(summary,altered)
    with pytest.raises(ValueError):compare.load_cohort(tmp_path/"bar","bar",0)
    summary.write_bytes(summary_bytes)
    preflight=tmp_path/"bar/native_preflight.json"
    preflight_bytes=preflight.read_bytes()
    preflight.write_bytes(preflight_bytes+b" ")
    with pytest.raises(ValueError):compare.load_cohort(tmp_path/"bar","bar",0)
    preflight.write_bytes(preflight_bytes)
    payload=tmp_path/"bar/tasks/0-0.npz"
    payload_bytes=payload.read_bytes()
    payload.write_bytes(payload_bytes+b"changed")
    with pytest.raises(ValueError):compare.load_cohort(tmp_path/"bar","bar",0)
    payload.write_bytes(payload_bytes)
    marker=tmp_path/"bar/tasks/0-0.done.json"
    original=marker.read_bytes()
    marker.unlink()
    with pytest.raises((ValueError,FileNotFoundError)):compare.load_cohort(tmp_path/"bar","bar",0)
    marker.write_bytes(original)
    changed=json.loads(original)
    changed["identity"]["task"]=[0,1]
    c.atomic_json(marker,changed)
    with pytest.raises(ValueError):compare.load_cohort(tmp_path/"bar","bar",0)
    marker.write_bytes(original)
    meta=tmp_path/"bar/tasks/0-0.json"
    raw=json.loads(meta.read_text())
    raw["chains"][0]["sample_seed"]+=1
    with np.load(tmp_path/"bar/tasks/0-0.npz") as data:arrays={k:data[k] for k in data.files}
    c.save_artifact(tmp_path/"bar/tasks/0-0",changed["identity"]|dict(task=[0,0]),arrays,raw)
    with pytest.raises(ValueError):compare.load_cohort(tmp_path/"bar","bar",0)
    base=tmp_path/"mc/tasks/0-0"
    raw=json.loads(base.with_suffix(".json").read_text())
    raw.update(status="failed",error="synthetic failure")
    c.save_artifact(base,dict(manifest=c.digest(plans["mc"]),task=[0,0]),{},raw)
    summary=tmp_path/"mc/summary.json"
    changed=json.loads(summary.read_text())
    changed["failed"]=1
    changed["records"][0]={k:v for k,v in raw.items() if k!="metadata"}
    c.atomic_json(summary,changed)
    loaded=compare.load_cohort(tmp_path/"mc","mc",0)
    rows=[r for r in loaded["records"] if r["case"]==0 and r["epsilon"]==.2]
    ref=json.loads((tmp_path/"reference.json").read_text())["records"][0]
    result=compare.metrics.assess("mc",rows,192,ref,.2)
    assert result["precision"]["metrics"]["point_estimates"]==191
    assert result["precision"]["precision"][0]["classification"]=="incomplete_points"
    assert result["costs"]["task_wall_seconds"]["mean"]==2


def test_capacity_and_incomplete_root_rejected(tmp_path):
    budget=json.loads((Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json").read_text())
    c.atomic_json(tmp_path/"manifest.json",mc.make_plan(budget,capacity=True))
    c.atomic_json(tmp_path/"budget.json",budget)
    with pytest.raises(ValueError):compare.load_cohort(tmp_path,"mc",0)


def test_actual_mc_metadata_binding(tmp_path):
    budget=json.loads((Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json").read_text())
    plan=mc.make_plan(budget,capacity=False)
    plan["conditions"][0]["planned_trials"]=12
    record=mc.run_task((tmp_path,plan,(0,0)))
    assert record["status"]=="ok"
    compare._metadata(record["metadata"],record["target_p"],record["seed"],record["problem_hash"])
    with pytest.raises(ValueError):
        compare._metadata(record["metadata"],record["target_p"],record["seed"]+1,record["problem_hash"])


def test_all_unmet_case_needs_no_compute_run(tmp_path):
    chosen=settings()
    for i in (0,1):chosen["records"][i]=dict(case=0,epsilon=(.2,.1)[i],status="unmet",reason="synthetic unmet")
    c.atomic_json(tmp_path/"manifest.json",bar.make_plan(chosen,capacity=False,case=0))
    c.atomic_json(tmp_path/"settings.json",chosen)
    for key,value in mc.platform_inputs().items():c.atomic_json(tmp_path/(key+".json"),value)
    result=compare.load_cohort(tmp_path,"bar",0)
    assert result["records"]==[] and result["phase_wall_seconds"] is None
    (tmp_path/"tasks").mkdir()
    with pytest.raises(ValueError):compare.load_cohort(tmp_path,"bar",0)
