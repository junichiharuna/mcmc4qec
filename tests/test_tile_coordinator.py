"""Conservative two-node scheduling and durable no-retry submission intent."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_coordinator as c


CONFIG=dict(order=[3,0,1,2],analysis_order=[0,3,1,2])


def test_waits_for_both_queued_and_running_nodes():
    state=["absent"]*4
    state[3]="live"
    assert c.choose(CONFIG,state,["absent"]*4,2)==dict(action="wait",reason="node_budget")
    assert c.choose(CONFIG,state,["absent"]*4,1)==dict(action="sample",case=0)


def test_fixed_sampling_order_then_ready_analysis_in_measured_order():
    samples=["complete","live","live","complete"]
    assert c.choose(CONFIG,samples,["absent"]*4,1)==dict(action="analyze",case=0)
    analyses=["live","absent","absent","absent"]
    assert c.choose(CONFIG,samples,analyses,1)==dict(action="analyze",case=3)
    assert c.choose(CONFIG,["live"]*4,analyses,1)["action"]=="wait"
    assert c.choose(CONFIG,["complete"]*4,["complete"]*4,0)["action"]=="finished"


def test_invalid_stage_state_and_resource_count_rejected():
    with pytest.raises(ValueError):
        c.choose(CONFIG,["unknown"]*4,["absent"]*4,0)
    with pytest.raises(ValueError):
        c.choose(CONFIG,["complete"]*4,["absent"]*4,-1)


def setup_config(tmp_path):
    root=tmp_path/"production"/"runs"/"production"
    root.mkdir(parents=True)
    state=tmp_path/"coordinator"
    state.mkdir()
    config=dict(CONFIG,bundle=str(tmp_path/"production"),controller=str(tmp_path/"control"),
                profile_root=str(tmp_path/"profile"),python="fixed-python")
    return config,root,state


def test_submission_uses_existing_driver_and_records_receipt(tmp_path):
    config,root,state=setup_config(tmp_path)
    calls=[]
    def runner(command,**kwargs):
        calls.append(command)
        assert (state/"intent-sample-0.json").exists()
        (root/"submission-0.json").write_text(json.dumps(dict(job_id="123.server",case=0)))
        return subprocess.CompletedProcess(command,0,stdout='{"job_id":"123.server"}',stderr="")
    receipt=c.submit_action(config,dict(action="sample",case=0),state,runner)
    assert receipt["job_id"]=="123.server"
    assert "submit_tile_production.py" in calls[0][1]
    assert calls[0][-1]=="--execute"
    assert (state/"receipt-sample-0.json").exists()
    with pytest.raises(ValueError):
        c.submit_action(config,dict(action="sample",case=0),state,runner)
    assert len(calls)==1


def test_ambiguous_submission_is_not_automatically_retried(tmp_path):
    config,root,state=setup_config(tmp_path)
    calls=[]
    def uncertain(command,**kwargs):
        calls.append(command)
        # qsub may have succeeded before output/ledger recording failed.
        raise subprocess.CalledProcessError(1,command,stderr="lost acknowledgement")
    with pytest.raises(subprocess.CalledProcessError):
        c.submit_action(config,dict(action="sample",case=0),state,uncertain)
    assert (state/"intent-sample-0.json").exists()
    assert not (state/"receipt-sample-0.json").exists()
    with pytest.raises(ValueError):
        c.submit_action(config,dict(action="sample",case=0),state,uncertain)
    assert len(calls)==1


def test_wrong_job_receipt_is_not_accepted(tmp_path):
    config,root,state=setup_config(tmp_path)
    def runner(command,**kwargs):
        (root/"analysis_submission-3.json").write_text(json.dumps(dict(job_id="123.server",case=3)))
        return subprocess.CompletedProcess(command,0,stdout='{"job_id":"999.server"}',stderr="")
    with pytest.raises(ValueError,match="receipt"):
        c.submit_action(config,dict(action="analyze",case=3),state,runner)
    assert not (state/"receipt-analyze-3.json").exists()


def test_failed_sampling_exit_requires_complete_recorded_tasks(tmp_path):
    import calibration as helpers
    import tile_bar_study as b
    config,root,state=setup_config(tmp_path)
    plan=dict(purpose="calibration",replicates=1,cases=[dict(rungs=[.1],chains=1)]*4)
    context=dict(sampling_manifest=helpers.digest(plan))
    helpers.atomic_json(root/"manifest.json",plan)
    helpers.atomic_json(root/"analysis_manifest.json",context)
    helpers.atomic_json(root/"submission-3.json",dict(job_id="123.server",case=3,manifest=helpers.digest(plan)))
    rows=[dict(task=list(task),status="failed" if i==0 else "ok") for i,task in enumerate(b.tasks(plan,3))]
    samples=dict(manifest=helpers.digest(plan),case=3,command="sample",tasks=len(rows),failed=1,records=rows)
    anchors=dict(manifest=helpers.digest(plan),case=3,command="anchors",tasks=1,failed=0,
                 records=[dict(case=3,replicate=0,status="ok")])
    helpers.atomic_json(root/"sample-3.json",samples)
    helpers.atomic_json(root/"anchors-3.json",anchors)
    observed=lambda ids:{"123.server":dict(job_state="F",Exit_status=1)}
    result=c.snapshot(config,observed,lambda:{})
    assert result["sample"][3]=="complete"
    assert result["jobs"]["123.server"]["exit_status"]==1
    samples["records"].pop()
    helpers.atomic_json(root/"sample-3.json",samples)
    with pytest.raises(ValueError,match="incomplete or duplicate"):
        c.snapshot(config,observed,lambda:{})


def test_queue_observation_failure_is_distinct_from_a_terminal_job(monkeypatch):
    def timeout(*args,**kwargs):
        raise subprocess.TimeoutExpired(args[0],30)
    monkeypatch.setattr(c.subprocess,"run",timeout)
    with pytest.raises(c.ObservationError):
        c.query_jobs(["123.server"])


def test_source_pins_and_unacknowledged_intent_stop_continuation(tmp_path):
    import calibration as helpers
    config,root,state=setup_config(tmp_path)
    source=tmp_path/"source.py"
    source.write_text("original")
    config["pins"]={str(source):helpers.file_hash(source)}
    c.validate_pins(config,state)
    source.write_text("changed")
    with pytest.raises(ValueError,match="pinned"):
        c.validate_pins(config,state)
    source.write_text("original")
    (state/"intent-sample-0.json").write_text("{}")
    with pytest.raises(ValueError,match="unacknowledged"):
        c.validate_pins(config,state)
