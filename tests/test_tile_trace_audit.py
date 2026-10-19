"""Audit actual small sampler artifacts and deliberately corrupted trace content."""
from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_bar_study as b
import tile_study as t
import audit_tile_traces as a


@pytest.fixture(scope="module")
def actual(tmp_path_factory):
    root=tmp_path_factory.mktemp("trace_audit")
    output=[]
    for case in range(4):
        plan=b.make_plan()
        plan["cases"][case]["steps"]=8
        task=(case,0,1,1,0,0)
        record=b.sample_task((str(root),plan,task))
        assert record["status"]=="ok"
        arrays,record=c.load_artifact(root/"traces"/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
        spec=plan["cases"][case]
        code,problem=t.build_problem(spec["size"],spec["noise"],spec["target"])
        output.append((plan,task,arrays,record,code,problem))
    return output


@pytest.mark.parametrize("case",range(4))
def test_actual_small_sampler_checkpoint_audit(actual,case):
    result=a.audit_trace(*actual[case])
    assert result["status"]=="ok" and result["saved_steps"]==8
    assert result["redecoded_checkpoints"]==2
    assert not result["all_physical_states_redecoded"]


@pytest.mark.parametrize("field",["weight","syndrome_weight","sector","checkpoint_indices","checkpoints","final","initial","sample_seed","config"])
def test_corruption_rejected(actual,field):
    plan,task,arrays,record,code,problem=actual[0]
    arrays={key:value.copy() for key,value in arrays.items()}
    record=deepcopy(record)
    if field=="sample_seed":
        record[field]+=1
    elif field=="config":
        record[field]["burn_in"]+=1
    elif field=="checkpoint_indices":
        arrays[field][0]=1
    elif field in ("initial","final","checkpoints"):
        arrays[field][...]=0
    elif field=="sector":
        arrays[field][0]=0
    else:
        arrays[field][0]+=1
    with pytest.raises(ValueError):
        a.audit_trace(plan,task,arrays,record,code,problem)


def test_dtype_shape_and_failed_task_retention(actual):
    plan,task,arrays,record,code,problem=actual[0]
    wrong=dict(arrays,weight=arrays["weight"].astype(float))
    with pytest.raises(ValueError):
        a.audit_trace(plan,task,wrong,record,code,problem)
    wrong=dict(arrays,weight=arrays["weight"][:-1])
    with pytest.raises(ValueError):
        a.audit_trace(plan,task,wrong,record,code,problem)
    failed=dict(task=list(task),status="failed",error="fixed rejection budget exhausted",wall_seconds=1.,cpu_seconds=.9)
    result=a.audit_trace(plan,task,{},failed,code,problem)
    assert result["status"]=="failed" and result["recorded_failure"]==failed["error"]
    assert result["redecoded_checkpoints"]==0


def test_group_retains_failure_checks_input_markers_and_rejects_missing(tmp_path,monkeypatch):
    plan=b.make_plan()
    plan["replicates"]=1
    plan["cases"][0].update(steps=6,rungs=[.1],chains=2)
    source=tmp_path/"source"
    output=tmp_path/"audit"
    group=(0,0,1,0)
    first=(*group,0,0)
    assert b.sample_task((str(source),plan,first))["status"]=="ok"
    context=dict(manifest=c.digest(plan))
    args=(source,output,plan,context,group)
    with pytest.raises(ValueError,match="missing trace"):
        a.audit_group(args)
    def fail(*args,**kwargs):
        raise ValueError("deliberate sampled failure record")
    monkeypatch.setattr(b.qec,"sample_faulty",fail)
    second=(*group,0,1)
    assert b.sample_task((str(source),plan,second))["status"]=="failed"
    row=a.audit_group(args)
    assert row["tasks"]==2 and row["failed_sampling"]==1 and row["redecoded_checkpoints"]==2
    assert a.audit_group(args)==row
    marker=source/"traces"/(c.task_id(first)+".done.json")
    original=marker.read_bytes()
    marker.write_bytes(marker.read_bytes()+b" ")
    with pytest.raises(ValueError,match="marker changed"):
        a.audit_group(args)
    marker.write_bytes(original)
    payload=source/"traces"/(c.task_id(first)+".npz")
    payload.write_bytes(b"changed source payload")
    with pytest.raises(ValueError):
        a.audit_group(args)


def test_full_audit_cannot_start_outside_qsub(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    monkeypatch.setattr(sys,"argv",["audit_tile_traces.py","--source-root",str(tmp_path),"--root",str(tmp_path/"out"),"--case","0",
                                  "--platform-profile",str(tmp_path/"profile.json"),"--platform-fixture",str(tmp_path/"fixture.json")])
    with pytest.raises(ValueError,match="qsub"):
        a.main()
    assert not (tmp_path/"out").exists()


def test_platform_guard_rejects_same_versions_with_different_native_or_failure_response():
    keys=("fixture","source_sha256","runtime","platform","machine","python_build","byteorder",
          "thread_environment","native_ldpc_sha256","problem_hash","repeated","fresh","decoder_probe")
    profile={key:{"checked":"same"} for key in keys}
    a.validate_platform(profile,deepcopy(profile))
    for key in ("native_ldpc_sha256","repeated","fresh","platform","thread_environment"):
        changed=dict(profile,**{key:{"checked":"different"}})
        with pytest.raises(ValueError,match="native decoder"):
            a.validate_platform(profile,changed)
    with pytest.raises(ValueError):
        a.validate_platform({}, {})
