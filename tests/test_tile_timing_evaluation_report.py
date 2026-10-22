"""Reporting retains the fixed cohort and never upgrades selection diagnostics."""
import copy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("pymatching")
pytest.importorskip("bposd")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_timing_evaluation_report as r


def numerical_fixture():
    refs = {case: dict(case=case, target_p=.03 if case % 2 == 0 else .05,
                      estimate=.1, interval_999=[.0999, .1001], standard_error=.00001) for case in range(4)}
    selection = dict(records=[dict(case=case, epsilon=eps, status="selected", condition={"case": case},
        calibration_assessment={"metrics": {"replicates": 192, "flagged": 192}}, eligible_conditions=1)
        for case in range(4) for eps in (.2, .1)])
    records = [dict(case=case, epsilon=eps, replicate=i, status="ok", estimate=.1,
                    interval=[.09, .11], available=True, task_wall_seconds=2., cpu_seconds=1.)
               for case in range(4) for eps in (.2, .1) for i in range(192)]
    mc = dict(records=records, status="completed", execution={})
    bars = {case: dict(records=[dict(row, task_wall_seconds=1., cpu_seconds=.5) for row in records if row["case"] == case],
                       status="completed", execution={}) for case in range(4)}
    return selection, refs, mc, bars


def test_fixed_eight_rows_and_diagnostic_scope():
    selection, refs, mc, bars = numerical_fixture()
    rows = r.assess_rows(selection, refs, mc, bars)
    assert len(rows) == 8
    for row in rows:
        assert row["planned_replicates"] == 192
        assert row["selection"]["calibration_assessment"]["metrics"]["flagged"] == 192
        assert row["diagnostic_observation"] == {"mc": "not_applicable", "bar": "not_collected"}
        assert row["comparison"]["bar"]["precision"]["metrics"]["flagged"] == 192
        assert row["ratios_mc_over_bar"]["cpu_seconds"]["value"] == 2.
        assert row["ratios_mc_over_bar"]["task_wall_seconds"]["value"] == 2.


@pytest.mark.parametrize("kind", ["above", "sensitive", "failed", "interval_missing", "cost_missing", "incomplete", "not_started", "not_prepared"])
def test_failures_and_unobserved_remain_in_denominator(kind):
    selection, refs, mc, bars = numerical_fixture()
    if kind == "above":
        for row in mc["records"]: row["estimate"] = .13
    elif kind == "sensitive":
        refs[0]["interval_999"] = [.08, .12]
    elif kind == "failed":
        bars[0]["records"][0].update(status="failed", error="synthetic failure")
    elif kind == "interval_missing":
        bars[0]["records"][0].update(interval=None, available=False)
    elif kind == "cost_missing":
        bars[0]["records"][0]["cpu_seconds"] = None
    else:
        bars[0] = dict(status=kind, records=[], execution={})
    row = r.assess_rows(selection, refs, mc, bars)[0]
    assert row["planned_replicates"] == 192
    if kind == "interval_missing":
        assert row["comparison"]["bar"]["precision"]["metrics"]["unavailable_intervals"] == 1
        assert row["ratios_mc_over_bar"]["cpu_seconds"]["value"] == 2
    else:
        assert row["ratios_mc_over_bar"]["cpu_seconds"]["value"] is None
    if kind == "cost_missing": assert row["ratios_mc_over_bar"]["task_wall_seconds"]["value"] == 2
    if kind in ("incomplete", "not_started", "not_prepared"):
        assert row["bar"]["observed_tasks"] is None


def test_ratio_is_ratio_of_means():
    selected, refs, mc, bars = numerical_fixture()
    bars[0]["records"][0]["cpu_seconds"] = 9.5
    row = r.assess_rows(selected, refs, mc, bars)[0]
    assert row["ratios_mc_over_bar"]["cpu_seconds"]["value"] == pytest.approx(192 / (191 * .5 + 9.5))


def receipt_fixture(tmp_path, failed=0, exit_status=0):
    root = tmp_path / "cohort"
    root.mkdir()
    plan = {"purpose": "test", "replicates": 192}
    manifest = c.digest(plan)
    resource = dict(cpus=96, memory_gb=32, walltime="00:30:00", requested_nodes=1, max_nodes=2)
    script = root / "timing.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    ledger = dict(job_id="123.cluster", manifest=manifest, command=["qsub", "/original/timing.sh"],
                  resource=resource, script_sha256=c.file_hash(script))
    c.atomic_json(root / "submission.json", ledger)
    c.atomic_json(root / "submission_intent.json", {k: v for k, v in ledger.items() if k != "job_id"})
    c.atomic_json(root / "execution_intent.json", dict(manifest=manifest, pbs_job_id=ledger["job_id"]))
    c.atomic_json(root / "native_preflight.json", dict(manifest=manifest, pbs_job_id=ledger["job_id"], hostname="compute"))
    pbs = dict(job_state="F", Exit_status=exit_status, Submit_arguments="/original/timing.sh", exec_host="compute/0*96",
               Resource_List=dict(select="1:ncpus=96:mem=32gb", ncpus=96, mem="32gb", walltime="00:30:00"), resources_used={})
    terminal = tmp_path / "terminal.json"
    c.atomic_json(terminal, dict(job_id=ledger["job_id"], job=pbs))
    item = dict(root=str(root), terminal=dict(path=str(terminal), sha256=c.file_hash(terminal)))
    return item, plan, dict(failed=failed), pbs


@pytest.mark.parametrize("failed,code,accepted", [(0,0,True),(1,1,True),(0,1,False),(1,0,False),(1,271,False),(1,2,False)])
def test_recorded_failure_terminal_distinct_from_crash(tmp_path, failed, code, accepted):
    item, plan, summary, _ = receipt_fixture(tmp_path, failed, code)
    if accepted:
        result = r.execution_evidence(item, plan, summary, r.Evidence())
        assert result["status"] == ("completed" if not failed else "completed_with_recorded_task_failures")
        assert result["cpu_model"] == "unknown"
    else:
        with pytest.raises(ValueError): r.execution_evidence(item, plan, summary, r.Evidence())


@pytest.mark.parametrize("field,value", [("job_state","R"),("Submit_arguments","/wrong/script"),("exec_host","other/0*96"),("Resource_List",{})])
def test_terminal_rejects_wrong_execution(tmp_path, field, value):
    item, plan, summary, pbs = receipt_fixture(tmp_path)
    pbs[field] = value
    c.atomic_json(item["terminal"]["path"], dict(job_id="123.cluster", job=pbs))
    item["terminal"]["sha256"] = c.file_hash(item["terminal"]["path"])
    with pytest.raises(ValueError): r.execution_evidence(item, plan, summary, r.Evidence())


def test_external_pin_and_mutation(tmp_path):
    path = tmp_path / "pin.json"
    c.atomic_json(path, {"x":1})
    pin = dict(path=str(path), sha256=c.file_hash(path))
    proof = r.Evidence()
    assert r.read_pin(pin, proof) == {"x":1}
    c.atomic_json(path, {"x":2})
    with pytest.raises(ValueError): proof.finish()
    with pytest.raises(ValueError): r.read_pin(pin, r.Evidence())


def test_root_state_tracks_execution_not_operator_label(tmp_path):
    assert r.root_state(tmp_path / "absent") == "not_prepared"
    root = tmp_path / "present"
    root.mkdir()
    c.atomic_json(root / "manifest.json", {})
    assert r.root_state(root) == "not_started"
    c.atomic_json(root / "submission_intent.json", {})
    assert r.root_state(root) == "incomplete"
    c.atomic_json(root / "summary.json", {})
    assert r.root_state(root) == "complete_candidate"


def test_saved_mc_fixed_gate_counts():
    data = Path(__file__).resolve().parents[1] / "docs/wp/data_tile_validation_2026-10-17"
    mc = json.loads((data / "mc_timing_main_evidence_v1/mc-benchmark/summary.json").read_text())
    refs = {row["case"]: row for row in json.loads((data / "reference_summary.json").read_text())["records"]}
    selection = json.loads((data / "bar_timing_selected_settings_v1.json").read_text())
    bars = {case:dict(status="not_prepared", records=[], execution={}) for case in range(4)}
    result = r.assess_rows(selection, refs, dict(status="completed", records=mc["records"], execution={}), bars)
    labels = [row["mc"]["assessment"]["precision"]["precision"][0]["classification"] for row in result]
    assert labels.count("empirical_within_target") == 4
    assert labels.count("empirical_above_target") == 2
    assert labels.count("reference_sensitive") == 2
    assert all(row["ratios_mc_over_bar"]["cpu_seconds"]["value"] is None for row in result)


def test_pbs_guard_and_source_closure(tmp_path, monkeypatch):
    monkeypatch.delenv("PBS_JOBID", raising=False)
    with pytest.raises(ValueError, match="PBS"):
        r.run(tmp_path / "missing.json", tmp_path / "new")
    names = {path.name for path in r.source_files().values()}
    assert {"tile_timing_evaluation_report.py", "tile_timing_metrics.py", "tile_precision_assessment.py", "tile_summary.py"} <= names


def orchestration_fixture(tmp_path, monkeypatch):
    """Real preparation/report control flow; scientific cohort loading is stubbed."""
    chosen, refs, mc, bars = numerical_fixture()
    config = {}
    def pin(name, value):
        path = tmp_path / (name + ".json")
        c.atomic_json(path, value)
        return dict(path=str(path), sha256=c.file_hash(path))
    config["reference"] = pin("reference", dict(records=list(refs.values())))
    config["reference_audit"] = pin("audit", dict(summary_sha256=config["reference"]["sha256"],
        all_seeds_verified=True, all_problem_metadata_verified=True, summary_reproduced=True, model_hashes={}))
    config["selection_recoveries"] = [dict(case=i, **pin(f"recovery-{i}", dict(problems=[]))) for i in range(4)]
    chosen["final_audit_evidence"] = [dict(case=i, recovery_sha256=config["selection_recoveries"][i]["sha256"],
        reference_sha256=config["reference"]["sha256"]) for i in range(4)]
    config["settings"] = pin("settings", chosen)
    config["seed_census"] = pin("census", dict(planned_entries=10, checked_entries=10, unchecked_entries=0,
        unexpected_collisions=0, namespace_count=56, stages_140_141_all_planned_cases_checked=True,
        source_runtime_input_bindings_verified=True, submission_completion_pbs_verified=True))
    conditions = [dict(case=case, epsilon=eps, target_p=refs[case]["target_p"], reference_point=refs[case]["estimate"],
        reference_interval_999=refs[case]["interval_999"]) for case, eps in r.IDENTITIES]
    def make_plan(source, *, capacity, case=None):
        return dict(case=case, conditions=conditions, replicates=192)
    monkeypatch.setattr(r.comparison.mc, "make_plan", make_plan)
    monkeypatch.setattr(r.comparison.bar, "make_plan", make_plan)
    monkeypatch.setattr(r, "accepted_inventory", lambda *args: ({}, {}))
    config["mc"] = dict(root=str(tmp_path / "mc"))
    config["bar"] = [dict(case=i, root=str(tmp_path / f"bar-{i}")) for i in range(4)]
    for method, i, item in [("mc", None, config["mc"]), ("bar",0,config["bar"][0]), ("bar",1,config["bar"][1])]:
        root = Path(item["root"])
        c.atomic_json(root / "manifest.json", make_plan(None, capacity=False, case=i))
        c.atomic_json(root / ("budget.json" if method == "mc" else "settings.json"), {} if method == "mc" else chosen)
        if i != 1:
            c.atomic_json(root / "summary.json", {"fixture":True})
            item["proof"] = pin(method + "-proof", {})
            item["terminal"] = pin(method + "-terminal", {})
            (root / "tasks").mkdir()
            loaded = mc if method == "mc" else bars[i]
            loaded["task_census"] = r.task_census(root)
            loaded["accepted_file_census"] = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    c.atomic_json(Path(config["bar"][2]["root"]) / "submission_intent.json", {})
    config_path = tmp_path / "config.json"
    c.atomic_json(config_path, config)
    monkeypatch.setattr(r, "load_complete", lambda item, method, case, *args: mc if method == "mc" else bars[case])
    monkeypatch.setenv("PBS_JOBID", "report.synthetic")
    return config_path, config


def test_prepare_run_and_render_exclusive_fixed_eight(tmp_path, monkeypatch):
    config_path, config = orchestration_fixture(tmp_path, monkeypatch)
    plan_path = tmp_path / "plan.json"
    r.prepare(config_path, plan_path)
    result = r.run(plan_path, tmp_path / "report")
    assert len(result["records"]) == 8
    assert [result["records"][i * 2]["bar"]["status"] for i in range(4)] == ["completed", "not_started", "incomplete", "not_prepared"]
    assert result["low_noise_independent_timing"] == "unevaluated"
    path = tmp_path / "report/report.json"
    r.render(path, tmp_path / "rendered.md", c.file_hash(path))
    assert (tmp_path / "rendered.md").read_text(encoding="utf-8") == (tmp_path / "report/report_ja.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError): r.run(plan_path, tmp_path / "report")
    with pytest.raises(ValueError): r.prepare(config_path, plan_path)


@pytest.mark.parametrize("mutation", ["metadata", "new_execution", "source", "extra_task", "extra_source"])
def test_no_success_publication_after_end_mutation(tmp_path, monkeypatch, mutation):
    config_path, config = orchestration_fixture(tmp_path, monkeypatch)
    fake_source = tmp_path / "frozen_source.py"
    fake_source.write_text("# fixture\n")
    original_sources = r.source_files
    extra = tmp_path / "new_source.py"
    monkeypatch.setattr(r, "source_files", lambda: {**original_sources(), "mutation_fixture":fake_source,
        **({"new_source.py":extra} if extra.exists() else {})})
    plan_path = tmp_path / "plan.json"
    r.prepare(config_path, plan_path)
    original_assess = r.assess_rows
    def mutate(*args):
        result = original_assess(*args)
        if mutation == "metadata":
            c.atomic_json(Path(config["mc"]["root"]) / "summary.json", {"changed":True})
        elif mutation == "new_execution":
            c.atomic_json(Path(config["bar"][1]["root"]) / "execution_intent.json", {})
        elif mutation == "source":
            fake_source.write_text("# changed\n")
        elif mutation == "extra_task":
            (Path(config["mc"]["root"]) / "tasks/extra.npz").write_bytes(b"extra")
        else:
            extra.write_text("# extra source\n")
        return result
    monkeypatch.setattr(r, "assess_rows", mutate)
    with pytest.raises(ValueError): r.run(plan_path, tmp_path / "report")
    assert not (tmp_path / "report/report.json").exists()
    assert (tmp_path / "report/validation_failure.json").exists()


def test_same_bytes_symlink_retarget_rejected(tmp_path):
    a, b, link = (tmp_path / name for name in ("a.json", "b.json", "link.json"))
    a.write_text("{}")
    b.write_text("{}")
    try:
        link.symlink_to(a)
    except OSError:
        pytest.skip("symlink permission unavailable")
    proof = r.Evidence()
    proof.track(link)
    link.unlink()
    link.symlink_to(b)
    with pytest.raises(ValueError): proof.finish()


def test_real_cohort_loader_payload_and_terminal_binding(tmp_path):
    """Original artifact reader plus new recovery/receipt/final-rehash binding."""
    from test_tile_timing_comparison import fixture
    plans = fixture(tmp_path)
    root = tmp_path / "bar"
    plan = plans["bar"]
    manifest = c.digest(plan)
    resource = dict(cpus=96, memory_gb=32, walltime="00:30:00", requested_nodes=1, max_nodes=2)
    (root / "timing.sh").write_text("#!/bin/sh\nexit 0\n")
    ledger = dict(job_id="synthetic.cluster", manifest=manifest, command=["qsub", "/original/timing.sh"],
        resource=resource, script_sha256=c.file_hash(root / "timing.sh"),
        submit_source_sha256=c.file_hash(Path(r.__file__).parent / "submit_tile_bar_time.py"))
    c.atomic_json(root / "submission.json", ledger)
    c.atomic_json(root / "submission_intent.json", {k:v for k,v in ledger.items() if k != "job_id"})
    terminal = tmp_path / "terminal.json"
    c.atomic_json(terminal, dict(job_id=ledger["job_id"], job=dict(job_state="F", Exit_status=0,
        Submit_arguments="/original/timing.sh", exec_host="compute/0*96",
        Resource_List=dict(select="1:ncpus=96:mem=32gb", ncpus=96, mem="32gb", walltime="00:30:00"))))
    summary = json.loads((root / "summary.json").read_text())
    recovered = tmp_path / "recovery.json"
    inventory = {p.relative_to(root).as_posix():c.file_hash(p) for p in root.rglob("*") if p.is_file()}
    verification = tmp_path / "verification.json"
    transfer = tmp_path / "transfer.json"
    c.atomic_json(verification, dict(main_manifest=manifest, compute_native_profile_validated=True,
        validation_errors=[], all_artifacts_verified=True, receipt_verified=True, source_input_binding_verified=True,
        job_id=ledger["job_id"], file_sha256=inventory))
    c.atomic_json(transfer, dict(all_files_sha256_match=True, all_artifacts_verified=True, validation_errors=[], files=len(inventory)))
    c.atomic_json(recovered, dict(summary_sha256=c.file_hash(root / "summary.json"), mode="main", case=0,
        job_id=ledger["job_id"], tasks=summary["tasks"], failed=0, fixed_prior_rng_and_saved_shape_checked=True,
        verification_sha256=c.file_hash(verification), transfer_sha256=c.file_hash(transfer)))
    item = dict(root=str(root), proof=dict(path=str(recovered), sha256=c.file_hash(recovered)),
                terminal=dict(path=str(terminal), sha256=c.file_hash(terminal)),
                verification=dict(path=str(verification), sha256=c.file_hash(verification)),
                transfer=dict(path=str(transfer), sha256=c.file_hash(transfer)))
    evidence = r.Evidence()
    loaded = r.load_complete(item, "bar", 0, dict(manifest=plan), json.loads((tmp_path / "audit.json").read_text()), evidence)
    assert loaded["status"] == "completed" and len(loaded["records"]) == 192
    evidence.finish()
    path = next((root / "tasks").glob("*.npz"))
    path.write_bytes(path.read_bytes() + b"changed after read")
    with pytest.raises(ValueError): evidence.finish()
    # A freshly self-consistent marker is still not the externally accepted bytes.
    marker = path.with_suffix(".done.json")
    value = json.loads(marker.read_text())
    value["sha256"][".npz"] = c.file_hash(path)
    c.atomic_json(marker, value)
    with pytest.raises(ValueError, match="accepted artifact"):
        r.load_complete(item, "bar", 0, dict(manifest=plan), json.loads((tmp_path / "audit.json").read_text()), r.Evidence())


@pytest.mark.skip(reason="repository copies of the evidence are redacted (user and host names replaced); recorded SHA-256 values refer to the unredacted originals kept outside the repository")
def test_real_case0_saved_pbs_metadata_only():
    """Accepted case0 receipt/manifest only; no production task payload scan."""
    data = Path(__file__).resolve().parents[1] / "docs/wp/data_tile_validation_2026-10-17/bar_main_case0_evidence_v1"
    root = data / "recovered/benchmark-0"
    terminal = data / "terminal.json"
    plan = json.loads((root / "manifest.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    proof = r.Evidence()
    result = r.execution_evidence(dict(root=str(root), terminal=dict(path=str(terminal), sha256=c.file_hash(terminal))),
                                  plan, summary, proof)
    assert result["job_id"] == "265263.node-PRISM"
    assert result["status"] == "completed" and result["hostname"] == "node012"
    proof.finish()


@pytest.mark.skip(reason="repository copies of the evidence are redacted (user and host names replaced); recorded SHA-256 values refer to the unredacted originals kept outside the repository")
@pytest.mark.parametrize("method", ["mc", "bar"])
def test_real_accepted_inventory_metadata_chain_only(method):
    """Read accepted byte tables, without opening production task payloads."""
    data = Path(__file__).resolve().parents[1] / "docs/wp/data_tile_validation_2026-10-17"
    def pin(path): return dict(path=str(path), sha256=c.file_hash(path))
    if method == "mc":
        evidence = data / "mc_timing_main_evidence_v1"
        root = evidence / "mc-benchmark"
        item = dict(root=str(root), proof=pin(evidence / "local_verification.json"),
                    verification=pin(evidence / "benchmark_verification.json"),
                    submission_output=pin(data / "mc_timing_main_submission_v1_stdout.txt"))
    else:
        evidence = data / "bar_main_case0_evidence_v1"
        root = evidence / "recovered/benchmark-0"
        item = dict(root=str(root), proof=pin(evidence / "independent_payload_verification.json"),
                    verification=pin(evidence / "verification.json"), transfer=pin(evidence / "transfer_verification.json"))
    proof = r.Evidence()
    inventory, accepted = r.accepted_inventory(item, method, json.loads((root / "manifest.json").read_text()), proof)
    assert "tasks/0-0.npz" in inventory
    assert inventory["summary.json"] == accepted["summary_sha256"]
    assert not any("tasks" in Path(path).parts for path in proof.hashes)
    proof.finish()
