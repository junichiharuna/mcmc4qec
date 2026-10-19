"""Fixed-cohort sampling partition contracts and bounded actual worker witnesses."""
from copy import deepcopy
from pathlib import Path
import shlex
import sys

import numpy as np
import pytest
for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_low_noise_study as low
import tile_low_noise_sampling_partitions as p


def measurements(plan, sample_wall=35.811062539):
    result = {}
    for phase in ("sample", "anchors"):
        rows = [dict(task=list(task), status="ok", wall_seconds=34.17394052 if phase == "sample" else 6.77535623,
                     cpu_seconds=1., peak_rss_mb=122.7266 if phase == "sample" else 90.7891)
                for task in low.tasks(plan, phase)]
        result[phase] = dict(manifest=c.digest(plan), phase=phase, failed=0, records=rows, tasks=len(rows),
                             native_preflight_sha256="native", phase_wall_seconds=sample_wall if phase == "sample" else 8.33526555)
    return result


def fixture(case=0, target=0):
    cap = low.make_plan(case, target, capacity=True)
    plan = low.make_plan(case, target, capacity=False)
    data = measurements(cap)
    return plan, cap, data


def test_observed_first_capacity_splits_time_not_cohort():
    plan, cap, data = fixture()
    resource = p.resource_plan(plan, cap, data)
    assert resource["sample"]["workers"] == 96 and resource["sample"]["memory_gb"] == 32
    assert [x["replicate_range"] for x in resource["sample"]["partitions"]] == [[0, 96], [96, 192]]
    assert [x["tasks"] for x in resource["sample"]["partitions"]] == [61440, 61440]
    assert [x["wall_seconds"] for x in resource["sample"]["partitions"]] == [55800, 55800]
    assert resource["anchors"]["partitions"][0]["tasks"] == 192
    assert resource["anchors"]["partitions"][0]["wall_seconds"] == 3600


@pytest.mark.parametrize("case", range(4))
@pytest.mark.parametrize("target", range(3))
def test_all_fixed_tasks_covered_once_without_seed_rekeying(case, target):
    plan, cap, data = fixture(case, target)
    resource = p.resource_plan(plan, cap, data)
    wrapper = dict(production=plan, resources=resource)
    for phase in ("sample", "anchors"):
        tasks = [task for part in resource[phase]["partitions"] for task in p.tasks_for_partition(wrapper, phase, part["index"])]
        assert sorted(tasks) == sorted(low.tasks(plan, phase)) and len(tasks) == len(set(tasks))
        for task in (tasks[0], tasks[len(tasks)//2], tasks[-1]):
            assert low.task_seed(plan, task, phase, 0) == low.t.seed((plan["stages"][phase], *task), 0)


@pytest.mark.parametrize("change", ("failed", "missing", "rss", "wall", "target", "stage"))
def test_bad_capacity_cannot_allocate(change):
    plan, cap, data = fixture()
    if change == "failed": data["sample"]["failed"] = 1
    elif change == "missing": data["sample"]["records"].pop()
    elif change == "rss": data["sample"]["records"][0]["peak_rss_mb"] = None
    elif change == "wall": data["sample"]["phase_wall_seconds"] = float("nan")
    elif change == "target": cap["target_index"] = 1
    else: cap["stages"]["sample"] = 151
    with pytest.raises(ValueError): p.resource_plan(plan, cap, data)


def test_large_worker_memory_reduces_workers_without_changing_tasks():
    plan, cap, data = fixture()
    for row in data["sample"]["records"]: row["peak_rss_mb"] = 8000.
    result = p.resource_plan(plan, cap, data)
    assert 1 <= result["sample"]["workers"] < 96
    assert result["sample"]["memory_gb"] <= 340
    assert sum(x["tasks"] for x in result["sample"]["partitions"]) == 122880


def test_one_replicate_over_limit_is_blocked_not_shrunk():
    plan, cap, data = fixture()
    for row in data["sample"]["records"]: row["wall_seconds"] = 100000.
    data["sample"]["phase_wall_seconds"] = 100001.
    with pytest.raises(ValueError, match="replicate"): p.resource_plan(plan, cap, data)
    assert plan["replicates"] == 192 and plan["condition"]["steps"] == 66000


@pytest.mark.parametrize("case", range(4))
@pytest.mark.parametrize("target", range(3))
def test_actual_worker_trace_equal_under_partition_routing(tmp_path, case, target):
    plan = low.make_plan(case, target, capacity=False)
    plan["condition"]["steps"] = 8
    task = (case, target, case//2, case%2, (0,95,96,191)[case],
            len(plan["condition"]["rungs"])-1, 0 if target%2==0 else plan["condition"]["chains"]-1)
    first = low.sample_task((str(tmp_path / "direct"), plan, task))
    second = p.run_task((str(tmp_path / "partition"), plan, "sample", task))
    assert first["status"] == second["status"] == "ok"
    identity = dict(manifest=c.digest(plan), task=list(task))
    left, _ = c.load_artifact(tmp_path / "direct/traces" / c.task_id(task), identity)
    right, _ = c.load_artifact(tmp_path / "partition/traces" / c.task_id(task), identity)
    assert set(left) == set(right) and all(np.array_equal(left[key], right[key]) for key in left)
    assert first["sample_seed"] == second["sample_seed"] and first["init_seed"] == second["init_seed"]
    with pytest.raises(ValueError, match="existing"): p.run_task((str(tmp_path / "partition"), plan, "sample", task))


def capacity_fixture(root,monkeypatch):
    """Real artifact/hash format, synthetic resource measurements, no Monte Carlo."""
    cap=low.make_plan(0,0,capacity=True)
    data=measurements(cap)
    root.mkdir(parents=True,exist_ok=True)
    monkeypatch.setattr(p.original_submit,"read_plan",lambda _:cap)
    monkeypatch.setattr(p,"source_hashes",lambda:{"fixture":"fixed"})
    monkeypatch.setattr(p.analysis,"validate_record",lambda *args:None)
    monkeypatch.setattr(low.t,"build_problem",lambda *args:(None,None))
    monkeypatch.setattr(low.native.trace_audit,"validate_platform",lambda *args:None)
    profiles=low.native.platform_inputs()
    for name,value in (("manifest.json",cap),("platform_profile.json",profiles["platform_profile"]),("platform_fixture.json",profiles["platform_fixture"])):
        c.atomic_json(root/name,value)
    script=root/"low-noise.sh";script.write_text("#!/bin/bash\ntrue\n")
    c.atomic_json(root/"submission.json",dict(job_id="10.x",manifest=c.digest(cap),command=["qsub",str(script)],script_sha256=c.file_hash(script)))
    receipt=root/"pbs.json"
    c.atomic_json(receipt,{"Jobs":{"10.x":dict(job_state="F",Exit_status=0,Submit_arguments=shlex.quote(str(script)))}})
    for phase in p.PHASES:
        native=root/f"preflight-{phase}/native_preflight.json"
        c.atomic_json(native,dict(manifest=c.digest(cap),pbs_job_id="10.x",hostname="fixture",profile={}))
        c.atomic_json(root/f"{phase}-execution-intent.json",dict(phase=phase,manifest=c.digest(cap),pbs_job_id="10.x",hostname="fixture"))
        data[phase]["native_preflight_sha256"]=c.file_hash(native)
        for row in data[phase]["records"]:
            task=row["task"]
            c.save_artifact(root/("traces" if phase=="sample" else "anchors")/c.task_id(task),
                            dict(manifest=c.digest(cap),task=task),{},row)
        c.atomic_json(root/f"{phase}-summary.json",data[phase])
    return cap,receipt


def test_capacity_validation_does_not_call_rejected_monolithic_allocator(tmp_path,monkeypatch):
    cap,receipt=capacity_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(p.original_submit,"measured_capacity",lambda *args:pytest.fail("old rejecting allocator invoked"))
    proof=p.validate_capacity(tmp_path,receipt)
    assert proof["production"]["replicates"]==192 and proof["capacity"]["replicates"]==2
    assert proof["measurements"]["sample"]["tasks"]==80 and len(proof["input_sha256"])>240


@pytest.mark.parametrize("kind",["payload","native","pbs","summary"])
def test_capacity_artifact_native_receipt_corruption_rejected(tmp_path,monkeypatch,kind):
    cap,receipt=capacity_fixture(tmp_path,monkeypatch)
    if kind=="payload":
        task=next(iter(low.tasks(cap,"sample")))
        path=tmp_path/"traces"/(c.task_id(task)+".npz");path.write_bytes(b"changed")
    elif kind=="native":
        path=tmp_path/"preflight-sample/native_preflight.json";value=p.read_json(path);value["pbs_job_id"]="other";c.atomic_json(path,value)
    elif kind=="pbs":
        value=p.read_json(receipt);value["Jobs"]["10.x"]["Exit_status"]=2;c.atomic_json(receipt,value)
    else:
        path=tmp_path/"sample-summary.json";value=p.read_json(path);value["failed"]=1;c.atomic_json(path,value)
    with pytest.raises(ValueError):p.validate_capacity(tmp_path,receipt)


def test_prepare_read_and_reservation_bind_original_plan(tmp_path,monkeypatch):
    capacity=tmp_path/"capacity";root=tmp_path/"production"
    cap,receipt=capacity_fixture(capacity,monkeypatch)
    wrapper=p.prepare(root,capacity,receipt)
    assert p.read_plan(root)==wrapper and wrapper["production"]["replicates"]==192
    for phase in p.PHASES:
        assert p.read_json(root/f"{phase}-execution-intent.json")["mode"]=="partitioned"
    with pytest.raises(ValueError,match="new independent"):p.prepare(root,capacity,receipt)
    path=root/"sample-execution-intent.json";value=p.read_json(path);value["mode"]="single";c.atomic_json(path,value)
    with pytest.raises(ValueError,match="reservation"):p.read_plan(root)


def test_capacity_validation_detects_terminal_source_change(tmp_path,monkeypatch):
    cap,receipt=capacity_fixture(tmp_path,monkeypatch)
    values=iter(({"source":"before"},{"source":"after"}))
    monkeypatch.setattr(p,"source_hashes",lambda:next(values))
    with pytest.raises(ValueError,match="source/runtime changed"):p.validate_capacity(tmp_path,receipt)
