"""Partition provenance boundaries and unchanged low-level numerical audits."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_low_noise_study as low
import tile_low_noise_trace_audit_run as original
import tile_low_noise_partitioned_trace_audit as m


def evidence():
    sampling = low.make_plan(0, 0, capacity=False)
    digests = {c.task_id(g): "a" * 64 for g in m.analysis.groups(sampling)}
    anchors = {c.task_id(t): "b" * 64 for t in low.tasks(sampling, "anchors")}
    return dict(mode="partitioned_sampling", sample=dict(tasks=122880, failed=0, group_record_digests=digests),
                anchors=dict(tasks=192, failed=0, record_digests=anchors), input_sha256={},
                source_sha256={__file__: c.file_hash(__file__)},
                collector_pbs_job=dict(phase="collect", job_id="104.fixture", exit_status=0),
                pbs_jobs=[dict(phase="sample", index=0, job_id="101.fixture", exit_status=0,
                               completion_class="success"),
                          dict(phase="sample", index=1, job_id="102.fixture", exit_status=0,
                               completion_class="success"),
                          dict(phase="anchors", index=0, job_id="103.fixture", exit_status=0,
                               completion_class="success")])


def test_plan_keeps_full_dimensions_and_all_receipts():
    sampling = low.make_plan(0, 0, capacity=False)
    inputs = low.native.platform_inputs()
    proof = evidence()
    cap = m.make_plan(sampling, **inputs, capacity=True, workers=8, completed_evidence=proof)
    full = m.make_plan(sampling, **inputs, capacity=False, workers=96, completed_evidence=proof)
    assert len(m.groups(cap)) == 8 and len(m.groups(full)) == 768
    assert cap["mode"] == "partitioned_sampling"
    assert cap["completed_phase_evidence"] == proof
    assert len(list(m.tasks_for_group(sampling, m.groups(cap)[0]))) == 160
    assert m.run_group is original.run_group
    assert m.verify_group_inputs is original.verify_group_inputs
    assert Path(m.__file__).resolve().as_posix() in {Path(p).as_posix() for p in cap["source_sha256"]}
    assert any(Path(p).name == "tile_low_noise_sampling_partitions.py" for p in cap["source_sha256"])


@pytest.mark.parametrize("bad", [{}, {"mode": "single"}, dict(evidence(), pbs_jobs=[]),
                                 dict(evidence(), source_sha256={})])
def test_singleton_or_incomplete_evidence_rejected(bad):
    with pytest.raises(ValueError, match="partition"):
        m.make_plan(low.make_plan(0, 0, capacity=False), **low.native.platform_inputs(),
                    capacity=True, workers=8, completed_evidence=bad)


def test_snapshot_binds_every_partition_receipt_and_blocks_escape(tmp_path):
    for name in ("manifest.json", "platform_profile.json", "platform_fixture.json", "receipt.json"):
        c.atomic_json(tmp_path / name, {})
    proof = evidence()
    proof["input_sha256"] = {"receipt.json": c.file_hash(tmp_path / "receipt.json")}
    before = m.sampling_snapshot(tmp_path, proof)
    assert set(before) == {"manifest.json", "platform_profile.json", "platform_fixture.json", "receipt.json"}
    (tmp_path / "receipt.json").write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        m.sampling_snapshot(tmp_path, proof)
    proof["input_sha256"] = {"../escape": "bad"}
    with pytest.raises(ValueError, match="escapes"):
        m.sampling_snapshot(tmp_path, proof)


def saved_terminal(root):
    root.mkdir()
    plan = {"workers": 8}
    script = root / "trace-audit.sh"
    script.write_text("#!/bin/bash\n")
    resource = dict(cpus=96, requested_nodes=1, memory_gb=32, walltime="00:30:00")
    submit = dict(manifest=c.digest(plan), command=["qsub", str(script)],
                  script_sha256=c.file_hash(script), resource=resource)
    c.atomic_json(root / "submission-intent.json", submit)
    c.atomic_json(root / "submission.json", dict(submit, job_id="201.fixture"))
    intent = dict(manifest=c.digest(plan), pbs_job_id="201.fixture", workers=8, hostname="compute",
                  submission_sha256=c.file_hash(root / "submission.json"),
                  submission_intent_sha256=c.file_hash(root / "submission-intent.json"),
                  script_sha256=c.file_hash(script))
    native = dict(intent, evidence={"native_platform_verified": True})
    receipt = {"Jobs": {"201.fixture": dict(job_state="F", Exit_status=0, Submit_arguments=str(script),
        Resource_List=dict(select="1:ncpus=96:mem=32gb", ncpus=96, mem="32gb", walltime="00:30:00"))}}
    for name, value in (("submission-intent", submit), ("submission", dict(submit, job_id="201.fixture")),
                        ("execution-intent", intent), ("native_preflight", native), ("terminal", receipt)):
        c.atomic_json(root / (name + ".json"), value)
    return plan


def test_terminal_tracks_all_proofs_and_real_pbs_job(tmp_path):
    root = tmp_path / "audit"
    plan = saved_terminal(root)
    result = m.read_terminal(root, plan)
    assert result["job_id"] == "201.fixture"
    assert set(result["input_sha256"]) == {"terminal.json", "submission.json", "submission-intent.json",
        "execution-intent.json", "native_preflight.json", "trace-audit.sh"}


@pytest.mark.parametrize("field,value", [("job_state", "R"), ("Exit_status", 1),
    ("Submit_arguments", "different.sh"), ("Resource_List", {"select": "2:ncpus=96:mem=32gb"})])
def test_terminal_rejects_wrong_state_script_resource(tmp_path, field, value):
    root = tmp_path / "audit"
    plan = saved_terminal(root)
    path = root / "terminal.json"
    saved = json.loads(path.read_text())
    saved["Jobs"]["201.fixture"][field] = value
    c.atomic_json(path, saved)
    with pytest.raises(ValueError):
        m.read_terminal(root, plan)


def test_terminal_rejects_foreign_partition_native(tmp_path):
    root = tmp_path / "audit"
    plan = saved_terminal(root)
    path = root / "native_preflight.json"
    saved = json.loads(path.read_text())
    saved["pbs_job_id"] = "999.fixture"
    c.atomic_json(path, saved)
    with pytest.raises(ValueError):
        m.read_terminal(root, plan)


def test_short_real_group_uses_unchanged_numerics(tmp_path, monkeypatch):
    from test_tile_low_noise_trace_audit_run import tiny_fixture
    source, root, sampling, plan, group = tiny_fixture(tmp_path, monkeypatch)
    result = m.run_group((source, root, sampling, plan, group))
    assert result["status"] == "ok" and result["planned_tasks"] == 2
    assert result["redecoded_checkpoints"] == 6
    assert result["failed_sampling"] == 0


def test_run_rejects_non_pbs_before_any_sampling_read(tmp_path, monkeypatch):
    monkeypatch.delenv("PBS_JOBID", raising=False)
    with pytest.raises(ValueError, match="PBS"):
        m.run(tmp_path / "audit", tmp_path / "source")


def saved_partition_capacity(tmp_path, monkeypatch):
    """Real short audit; the separately tested partition reader is a boundary fixture."""
    from test_tile_low_noise_trace_audit_run import tiny_fixture
    source, root, sampling, _, _ = tiny_fixture(tmp_path, monkeypatch)
    proof = evidence()
    proof["sample"]["tasks"] = 768 * 2
    for kernel in range(2):
        for initial in range(2):
            for rep in range(2):
                group = (0, 0, kernel, initial, rep)
                rows = []
                for task in m.tasks_for_group(sampling, group):
                    result = low.sample_task((source, sampling, task))
                    assert result["status"] == "ok"
                    rows.append({key: result[key] for key in m.REDUCED_KEYS})
                proof["sample"]["group_record_digests"][c.task_id(group)] = c.digest(rows)
    inputs = low.native.platform_inputs()
    for name, value in dict(manifest=sampling, **inputs).items():
        c.atomic_json(source / (name + ".json"), value)
    c.atomic_json(source / "partition-receipts.json", proof["pbs_jobs"])
    proof["input_sha256"] = {"partition-receipts.json": c.file_hash(source / "partition-receipts.json")}
    monkeypatch.setattr(m.partitions, "completed_partition_evidence", lambda *_: deepcopy(proof))
    monkeypatch.setattr(m.analysis, "completed_phase_evidence", lambda *_: pytest.fail("singleton reader called"))
    plan = m.prepare(root, source, capacity=True, workers=8)
    assert m.read_plan(root, source)[0] == plan
    monkeypatch.setenv("PBS_JOBID", "201.fixture")
    for name, value in m.THREADS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(m.audit, "validate_native_environment", lambda *a, **k: {"native_platform_verified": True})
    monkeypatch.setattr(c, "parallel_map", lambda fn, jobs, workers: [fn(job) for job in jobs])
    monkeypatch.setattr(c, "peak_rss_mb", lambda: 128.)
    save_execution_submission(root, source, plan, sampling)
    summary = m.run(root, source)
    # Resource clocks are fixtures: short Windows tasks can have zero CPU ticks.
    for row in summary["records"]:
        row.update(wall_seconds=1., cpu_seconds=.8, peak_rss_mb=128.)
        c.save_artifact(root / "measurements" / c.task_id(row["group"]),
                        dict(manifest=c.digest(plan), group=row["group"]), {}, row)
    summary["phase_wall_seconds"] = 2.
    c.atomic_json(root / "summary.json", summary)
    script = root / "trace-audit.sh"
    c.atomic_json(root / "terminal.json", {"Jobs": {"201.fixture": dict(job_state="F", Exit_status=0,
        Submit_arguments=str(script), Resource_List=dict(select="1:ncpus=96:mem=340gb", ncpus=96,
                                                         mem="348160mb", walltime="24:00:00"))}})
    return source, root, sampling, plan, summary, proof


def save_execution_submission(root, source, plan, sampling):
    import submit_tile_low_noise_partitioned_trace_audit as submitter
    script = root / "trace-audit.sh"
    script.write_text("#!/bin/bash\n")
    binding = dict(source_sha256={name: c.file_hash(path) for name, path in submitter.source_files().items()},
                   package_sha256=sampling["runtime"]["package_sha256"],
                   python_path=str(Path(sys.executable).resolve()), python_sha256=c.file_hash(Path(sys.executable).resolve()))
    submit = dict(manifest=c.digest(plan), command=["qsub", str(script)], script_sha256=c.file_hash(script),
                  resource=dict(cpus=96, workers=plan["workers"], requested_nodes=1, max_nodes=2,
                                memory_gb=340, wall_seconds=86400, walltime="24:00:00"),
                  sampling_root=str(source), source_pbs_jobs=m.upstream_jobs(plan["completed_phase_evidence"]),
                  bundle_binding=binding, submit_source_sha256=c.file_hash(submitter.__file__))
    c.atomic_json(root / "submission-intent.json", submit)
    c.atomic_json(root / "submission.json", dict(submit, job_id="201.fixture"))


def test_prepare_run_read_bind_receipts_and_never_call_singleton(tmp_path, monkeypatch):
    source, root, _, plan, summary, proof = saved_partition_capacity(tmp_path, monkeypatch)
    assert summary["groups"] == 8 and summary["planned_tasks"] == 16
    assert summary["failed_audit_groups"] == 0 and summary["failed_sampling"] == 0
    assert m.read_terminal(root, plan)["job_id"] == "201.fixture"
    with pytest.raises(ValueError, match="existing"):
        m.run(root, source)
    (source / "partition-receipts.json").write_text("modified")
    with pytest.raises(ValueError, match="changed"):
        m.read_plan(root, source)


def test_source_closure_change_invalidates_prepared_plan(tmp_path, monkeypatch):
    source, root, _, _, _, _ = saved_partition_capacity(tmp_path, monkeypatch)
    actual = m.source_hashes()
    changed = dict(actual)
    changed[next(iter(changed))] = "0" * 64
    monkeypatch.setattr(m, "source_hashes", lambda: changed)
    with pytest.raises(ValueError, match="source"):
        m.read_plan(root, source)


@pytest.mark.parametrize("mutation", ["job", "source", "python", "script", "resource", "collector"])
def test_execution_rejects_wrong_submission_before_native_or_output(tmp_path, monkeypatch, mutation):
    root, source = tmp_path / "audit", tmp_path / "sampling"
    root.mkdir()
    source.mkdir()
    sampling = low.make_plan(0, 0, capacity=False)
    plan = m.make_plan(sampling, **low.native.platform_inputs(), capacity=True, workers=8,
                       completed_evidence=evidence())
    save_execution_submission(root, source, plan, sampling)
    monkeypatch.setenv("PBS_JOBID", "201.fixture" if mutation != "job" else "999.fixture")
    for name, value in m.THREADS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(m, "read_plan", lambda *_: (plan, sampling))
    monkeypatch.setattr(m.audit, "validate_native_environment", lambda *a, **k: pytest.fail("native before ledger gate"))
    value = json.loads((root / "submission.json").read_text())
    if mutation == "source":
        value["bundle_binding"]["source_sha256"]["tile_low_noise_sampling_partitions.py"] = "bad"
    elif mutation == "python":
        value["bundle_binding"]["python_sha256"] = "bad"
    elif mutation == "script":
        (root / "trace-audit.sh").write_text("changed")
    elif mutation == "resource":
        value["resource"]["workers"] = 96
    elif mutation == "collector":
        value["source_pbs_jobs"] = [row for row in value["source_pbs_jobs"] if row["phase"] != "collect"]
    c.atomic_json(root / "submission.json", value)
    c.atomic_json(root / "submission-intent.json", {key: item for key, item in value.items() if key != "job_id"})
    with pytest.raises(ValueError):
        m.run(root, source)
    assert not (root / "execution-intent.json").exists()
    assert not (root / "native_preflight.json").exists()
