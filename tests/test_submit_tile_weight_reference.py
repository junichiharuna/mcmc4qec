"""Pilot-based resource extrapolation and guarded weight-reference submission."""
from pathlib import Path
import subprocess
import sys
import shlex

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
from test_tile_weight_reference_driver import inputs
import calibration as c
import tile_weight_reference_driver as d
import submit_tile_weight_reference as s


def planned_root(root):
    values=inputs()
    root.mkdir(parents=True,exist_ok=True)
    for key,value in zip(d.INPUTS,values):
        c.atomic_json(root/(key+".json"),value)
    context=d.make_context(*values)
    c.atomic_json(root/"manifest.json",context)
    return context,values


def test_resources_include_sampling_and_separate_aggregation_allowance():
    values=inputs()
    context=d.make_context(*values)
    resource=s.resource_plan(context,values[1],values[2])
    assert resource["predicted_sampling_seconds"]==pytest.approx(.2)
    assert resource["aggregation_allowance_seconds"]==pytest.approx(.2)
    assert resource["wall_seconds"]==1800 and resource["walltime"]=="00:30:00"
    assert resource["memory_gb"]==32 and resource["tasks"]==16
    assert resource["unmeasured_layers"]==[]
    assert resource["manifest"]==c.digest(context)
    assert resource["pilot_audit_digest"]==c.digest(values[2])


def test_unmeasured_positive_weight_uses_positive_pilot_maximum():
    values=inputs()
    values[0]["conditions"][0]["layers"]=[dict(w=i,mode="mc",trials=8192) for i in range(10)]
    values[0]["conditions"][0]["layers"][0]=dict(w=0,mode="enum",trials=1)
    # A slow zero-weight construction must not be extrapolated as per-error cost.
    for row in values[2]["strata"]:
        if row["case"]==0 and row["prior_index"]==0:
            row["task_wall_seconds_max"]=10. if row["w"]==0 else 2.
    values[0]["pilot_audit_digest"]=c.digest(values[2])
    context=d.make_context(*values)
    resource=s.resource_plan(context,values[1],values[2])
    assert resource["unmeasured_layers"]==[[0,9]]
    assert s.chunk_cost(context["reference"],values[1],values[2],(0,9,0))==16.
    assert s.chunk_cost(context["reference"],values[1],values[2],(0,0,0))==10.


@pytest.mark.parametrize("change",["incomplete","digest","wall","memory"])
def test_invalid_pilot_binding_and_excessive_resources_rejected(change):
    values=inputs()
    if change=="incomplete":
        values[2]["allocation_ready"]=False
    elif change=="wall":
        for row in values[2]["strata"]:
            row["task_wall_seconds_max"]=100000.
    elif change=="memory":
        values[2]["strata"][0]["peak_rss_mb_max"]=10000.
    values[0]["pilot_audit_digest"]=c.digest(values[2])
    if change=="incomplete":
        context=d.make_context(*inputs())
    else:
        context=d.make_context(*values)
    if change=="digest":
        context["input_digests"]["pilot_audit"]="changed"
    with pytest.raises(ValueError):
        s.resource_plan(context,values[1],values[2])


def test_dry_run_reconstructs_plan_and_generates_qsub_script(tmp_path):
    context,values=planned_root(tmp_path)
    record=s.submit(tmp_path,tmp_path,execute=False)
    assert record["job_id"]=="dry-run" and record["manifest"]==c.digest(context)
    script=(tmp_path/"weight_reference.sh").read_text()
    assert "#PBS -l select=1:ncpus=96:mem=32gb" in script
    command=shlex.split(script.splitlines()[-1])
    assert Path(command[1]).name=="tile_weight_reference_driver.py"
    assert command[2:4]==["run","--root"] and command[-2:]==["--workers","96"]
    assert "OMP_NUM_THREADS=1" in script and "PBS_JOBID" in script
    assert not (tmp_path/"submission_intent.json").exists()
    values[0]["chunk_size"]=1024
    c.atomic_json(tmp_path/"allocation.json",values[0])
    with pytest.raises(ValueError,match="changed"):
        s.submit(tmp_path,tmp_path,execute=False)


@pytest.mark.parametrize("gate",["controller","nodes"])
def test_live_submission_gates_precede_intent(tmp_path,gate):
    planned_root(tmp_path)
    with pytest.raises(ValueError):
        s.submit(tmp_path,tmp_path,execute=True,
                 controller_query=lambda:["running"] if gate=="controller" else [],
                 active_query=lambda:{"queued":{"Resource_List":{"select":"2:ncpus=96"}}},
                 runner=lambda *a,**k:pytest.fail("must not submit"))
    assert not (tmp_path/"submission_intent.json").exists()


@pytest.mark.parametrize("response",["123.cluster","ambiguous","timeout"])
def test_durable_intent_and_no_retry_after_any_qsub_response(tmp_path,response):
    planned_root(tmp_path)
    calls=[]
    def runner(command,**kwargs):
        assert (tmp_path/"submission_intent.json").exists()
        assert command[0]=="qsub"
        calls.append(command)
        if response=="timeout":
            raise subprocess.TimeoutExpired(command,30)
        return subprocess.CompletedProcess(command,0,stdout=response)
    kwargs=dict(execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    if response=="123.cluster":
        assert s.submit(tmp_path,tmp_path,**kwargs)["job_id"]==response
        assert (tmp_path/"submission.json").exists()
    else:
        with pytest.raises((RuntimeError,subprocess.TimeoutExpired)):
            s.submit(tmp_path,tmp_path,**kwargs)
        assert not (tmp_path/"submission.json").exists()
    with pytest.raises(ValueError,match="intent"):
        s.submit(tmp_path,tmp_path,**kwargs)
    assert len(calls)==1
