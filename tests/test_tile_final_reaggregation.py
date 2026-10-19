"""Orchestration contracts use bounded synthetic reports, never production scans."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_final_reaggregation as r


@pytest.fixture
def planned(tmp_path, monkeypatch):
    source, audit = tmp_path / "production", tmp_path / "audit"
    source.mkdir(); audit.mkdir()
    evidence = {}
    for name in r.EVIDENCE:
        path = tmp_path / (name + ".json"); c.atomic_json(path, {})
        evidence[name] = str(path)
    receipt = tmp_path / "completion.json"; c.atomic_json(receipt, {})
    snapshot = dict(production=dict(runtime={}), sampling_manifest="sampling", analysis_context="analysis",
                    trace_audit_manifest="audit", upstream_jobs={"sampling": "1.x", "analysis": "2.x", "trace_audit": "3.x"},
                    input_sha256={}, source_sha256={}, python_sha256="python", runtime={}, rows_sha256="rows")
    monkeypatch.setattr(r, "snapshot", lambda *args: snapshot.copy())
    root = tmp_path / "new"
    plan = r.prepare(root, source, audit, 2, evidence, receipt)
    for key, value in r.THREADS.items(): monkeypatch.setenv(key, value)
    monkeypatch.setenv("PBS_JOBID", "4.x")
    monkeypatch.setattr(r, "execution_binding", lambda *args: {"job_id": "4.x"})
    monkeypatch.setattr(r, "analysis_stats", lambda plan: {})
    return root, plan, snapshot


def child(monkeypatch, failed=None, mutate=None):
    calls = []
    def execute(command, **kwargs):
        root = Path(command[command.index("--root") + 1]); name = command[-1]
        calls.append(name)
        if mutate: mutate(name)
        if name == failed: return SimpleNamespace(returncode=7)
        c.atomic_json(root / "phases" / (name + ".json"), {"case": 2})
        c.atomic_json(root / "phases" / (name + ".measurement.json"), dict(
            phase=name, status="ok", manifest=c.digest(r.read_plan(root)),
            output_sha256=c.file_hash(root / "phases" / (name + ".json")),
            wall_seconds=.1, cpu_seconds=.05, peak_rss_mb=10, pbs_job_id="4.x"))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(r, "validate_report", lambda *args: None)
    return execute, calls


def test_plan_full_case_and_new_root(planned):
    root, plan, _ = planned
    assert plan["replicates"] == 192 and plan["groups"] == 768
    assert plan["phases"] == ["audited", "comparisons", "precision", "weight", "strata"]
    assert plan["resources"] == r.resources() and plan["resources"]["measured"] is False
    with pytest.raises(ValueError, match="new"):
        r.prepare(root, plan["production_root"], plan["audit_root"], 2, plan["evidence"], plan["completion_receipt"])


def test_full_success_is_sequential_and_measured(planned, monkeypatch):
    root, plan, _ = planned
    execute, calls = child(monkeypatch)
    report = r.run(root, runner=execute)
    assert calls == plan["phases"] and report["complete"]
    assert len(report["records"]) == 5 and all(x["status"] == "ok" for x in report["records"])
    with pytest.raises(ValueError, match="existing"): r.run(root, runner=execute)


def test_failed_adapter_stops_all_dependents(planned, monkeypatch):
    root, plan, _ = planned
    execute, calls = child(monkeypatch, "audited")
    with pytest.raises(RuntimeError): r.run(root, runner=execute)
    report = json.loads((root / "summary.json").read_text())
    assert calls == ["audited"] and not report["complete"]
    assert [x["status"] for x in report["records"]] == ["failed"] + ["not_run_dependency"] * 4


def test_source_change_retains_summary(planned, monkeypatch):
    root, _, snapshot = planned
    def mutate(name): snapshot["source_sha256"] = {"changed": "hash"}
    execute, _ = child(monkeypatch, mutate=mutate)
    with pytest.raises(RuntimeError): r.run(root, runner=execute)
    report = json.loads((root / "summary.json").read_text())
    assert not report["terminal_binding_valid"] and len(report["records"]) == 5


def test_missing_measurement_is_failure(planned, monkeypatch):
    root, _, _ = planned
    with pytest.raises(RuntimeError): r.run(root, runner=lambda *a, **k: SimpleNamespace(returncode=0))
    assert json.loads((root / "summary.json").read_text())["records"][0]["status"] == "failed"


def test_qsub_and_threads_required(planned, monkeypatch):
    root, _, _ = planned
    monkeypatch.delenv("PBS_JOBID")
    with pytest.raises(ValueError, match="qsub"): r.run(root)
    assert not (root / "execution-intent.json").exists()


def test_adapter_report_rejects_partial_cohort(planned):
    root, plan, _ = planned
    with pytest.raises(ValueError): r.validate_report(plan, "audited", dict(case=2, replicates=191))


@pytest.mark.parametrize("phase", ("audited", "comparisons", "precision", "weight", "strata"))
def test_real_report_schemas_and_mismatched_bindings(planned, phase):
    _, plan, _ = planned
    state = plan["snapshot"]
    root = Path(plan["production_root"])
    paths = [root / name for name in ("manifest.json", "analysis_manifest.json", "reference_summary.json", "summary-2.json")]
    paths.extend(Path(value) for value in plan["evidence"].values())
    state["input_sha256"] = {str(path): "input-" + path.name for path in paths}
    adapter = dict(case=2, purpose="audited_calibration_results", replicates=192, groups=768, conditions=352,
                   sampling_manifest="sampling", analysis_context="analysis", trace_audit_manifest="audit",
                   historical_consumed_input_hashes_recorded=False, bar_bootstrap_recomputed=False,
                   all_physical_states_redecoded=False, current_archived_inputs_match_audited_inputs=True,
                   terminal_payload_stat_checked=True, artifact_inventory_sha256="inventory", records=[{}] * 352,
                   source_sha256=c.file_hash(r.audited.__file__), input_sha256=state["input_sha256"].copy())
    labels = {label: state["input_sha256"][str(root / name)] for label, name in
              dict(sampling="manifest.json", analysis="analysis_manifest.json", reference="reference_summary.json").items()}
    reports = dict(audited=adapter, comparisons=dict(case=2, conditions=352, analysis="analysis", rows_sha256="rows"),
                   precision=dict(case=2, conditions=352, replicates=192, input_sha256=labels.copy()),
                   weight=dict(case=2, conditions=48, analysis_metadata=[{}] * 768, input_sha256=labels.copy()),
                   strata=dict(case=2, conditions=352, analysis="analysis", primary_summaries_reproduced=True, raw_rows_sha256="rows"))
    report = reports[phase]
    r.validate_report(plan, phase, report)
    if phase == "audited": report["analysis_context"] = "wrong"
    elif phase == "comparisons": report["rows_sha256"] = "wrong"
    elif phase == "strata": report["raw_rows_sha256"] = "wrong"
    else: report["input_sha256"]["reference"] = "wrong"
    with pytest.raises(ValueError): r.validate_report(plan, phase, report)


def test_upstream_completion_requires_all_jobs_and_exit_zero():
    jobs = {"sampling": "1.x", "analysis": "2.x", "trace_audit": "3.x"}
    receipt = {"Jobs": {job: dict(job_state="F", Exit_status=0) for job in jobs.values()}}
    r.check_completion(receipt, jobs)
    receipt["Jobs"]["3.x"]["Exit_status"] = 1
    with pytest.raises(ValueError): r.check_completion(receipt, jobs)


def test_output_root_cannot_modify_production(planned):
    _, plan, _ = planned
    with pytest.raises(ValueError, match="independent"):
        r.prepare(Path(plan["production_root"]) / "new", plan["production_root"], plan["audit_root"],
                  2, plan["evidence"], plan["completion_receipt"])


@pytest.mark.parametrize("case", range(4))
def test_all_case_phase_plans(planned, case):
    root, plan, _ = planned
    other = r.prepare(root.parent / ("other" + str(case)), plan["production_root"], plan["audit_root"], case,
                      plan["evidence"], plan["completion_receipt"])
    assert ("strata" in other["phases"]) == (case in (2, 3))
    assert other["replicates"] == 192


def test_actual_child_dispatch_and_resource_persistence(planned, monkeypatch):
    root, plan, _ = planned
    (root / "phases").mkdir()
    c.atomic_json(root / "execution-intent.json", {})
    c.atomic_json(root / "phases/audited.request.json", dict(phase="audited", manifest=c.digest(plan), pbs_job_id="4.x"))
    calls = []
    def original_api(source, audit, case, **evidence):
        calls.append((source, audit, case, evidence))
        return dict(case=case, complete=True)
    monkeypatch.setattr(r.audited, "read_results", original_api)
    monkeypatch.setattr(r, "validate_report", lambda *args: None)
    monkeypatch.setattr(c, "peak_rss_mb", lambda: 10.)
    result = r.run_phase(root, "audited")
    assert result["status"] == "ok" and len(calls) == 1
    assert calls[0][2] == 2 and calls[0][3] == plan["evidence"]
    assert result["output_sha256"] == c.file_hash(root / "phases/audited.json")
    with pytest.raises(ValueError, match="existing"): r.run_phase(root, "audited")


def test_child_api_failure_retained(planned, monkeypatch):
    root, plan, _ = planned
    (root / "phases").mkdir(); c.atomic_json(root / "execution-intent.json", {})
    c.atomic_json(root / "phases/audited.request.json", dict(phase="audited", manifest=c.digest(plan), pbs_job_id="4.x"))
    def failed(*args, **kwargs): raise ValueError("scientific input mismatch")
    monkeypatch.setattr(r.audited, "read_results", failed)
    with pytest.raises(RuntimeError): r.run_phase(root, "audited")
    record = json.loads((root / "phases/audited.measurement.json").read_text())
    assert record["status"] == "failed" and "scientific input mismatch" in record["error"]


@pytest.mark.parametrize("corruption", ("pbs_script", "case_script", "manifest", "context"))
def test_real_metadata_snapshot_checks_script_context_and_receipt(tmp_path, monkeypatch, corruption):
    production, audit = tmp_path / "production", tmp_path / "audit"
    production.mkdir(); audit.mkdir()
    plan = dict(replicates=192, runtime=r.audited.bar.b.runtime())
    monkeypatch.setattr(r.audited.bar.b, "make_plan", lambda: plan)
    ap = dict(purpose="trace_audit_full", case=0, replicates=192)
    monkeypatch.setattr(r.audited.r, "read_plan", lambda *args: (ap, plan))
    c.atomic_json(production / "manifest.json", plan)
    c.atomic_json(production / "reference_summary.json", {})
    context = dict(sampling_manifest=c.digest(plan), runtime=plan["runtime"],
                   analysis_source_sha256=c.file_hash(r.audited.bar.__file__),
                   reference_summary_sha256=c.file_hash(production / "reference_summary.json"))
    c.atomic_json(production / "analysis_manifest.json", context)
    c.atomic_json(production / "summary-0.json", dict(case=0, conditions=352, analysis=c.digest(context), raw_rows_sha256="rows"))
    c.atomic_json(production / "analysis_summary-0.json", dict(analysis=c.digest(context), groups=768, rows=67584))
    for name in ("sample-0", "anchors-0"): c.atomic_json(production / (name + ".json"), {})
    (production / "rows-0.jsonl").write_text("")
    for name in ("manifest", "sampling_manifest", "platform_profile", "platform_fixture"): c.atomic_json(audit / (name + ".json"), {})
    c.atomic_json(audit / "native_preflight.json", dict(pbs_job_id="3.x"))
    c.atomic_json(audit / "summary.json", dict(manifest=c.digest(ap), groups=768, failed_audits=0,
                  records=[dict(group=list(g)) for g in r.audited.r.groups(ap)],
                  native_preflight_sha256=c.file_hash(audit / "native_preflight.json")))
    jobs = {}
    for index, (directory, name, script_name) in enumerate(((production, "submission-0", "sample-0.sh"),
             (production, "analysis_submission-0", "analyze-0.sh"), (audit, "submission", "audit.sh")), 1):
        script = directory / script_name; script.write_text("#!/bin/bash\ntrue\n")
        ledger = dict(job_id=f"{index}.x", command=["qsub", str(script)], script_sha256=c.file_hash(script),
                      manifest=c.digest(ap if index == 3 else plan))
        if index == 2: ledger["analysis_manifest_sha256"] = c.file_hash(production / "analysis_manifest.json")
        c.atomic_json(directory / (name + ".json"), ledger)
        jobs[f"{index}.x"] = dict(job_state="F", Exit_status=0, Submit_arguments=r.shlex.quote(str(script)))
    receipt = tmp_path / "completion.json"; c.atomic_json(receipt, {"Jobs": jobs})
    evidence = {}
    for name in r.EVIDENCE:
        path = tmp_path / (name + ".json"); c.atomic_json(path, {}); evidence[name] = str(path)
    result = r.snapshot(production, audit, 0, evidence, receipt, {})
    assert len(result["upstream_jobs"]) == 3 and result["rows_sha256"] == "rows"
    ledger_path = production / "analysis_submission-0.json"
    ledger = r.read_json(ledger_path)
    if corruption == "pbs_script": jobs["2.x"]["Submit_arguments"] = "/different/script.sh"
    elif corruption == "case_script":
        script = production / "analyze-1.sh"; script.write_text("#!/bin/bash\ntrue\n")
        ledger["command"][1] = str(script)
        jobs["2.x"]["Submit_arguments"] = r.shlex.quote(str(script))
    elif corruption == "manifest": ledger["manifest"] = "different"
    else: ledger["analysis_manifest_sha256"] = "different"
    c.atomic_json(ledger_path, ledger); c.atomic_json(receipt, {"Jobs": jobs})
    with pytest.raises(ValueError):
        r.snapshot(production, audit, 0, evidence, receipt, {})
