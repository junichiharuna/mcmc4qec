"""Read-only binding of fixed calibration cohorts to existing scientific audits."""
from collections import defaultdict
import json
import math
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import artifact_archive as archive
import audit_tile_anchors as anchors
import tile_bar_analysis as bar
import tile_study as t
import tile_summary as summary
import tile_audited_results as reader


def sha(value):
    return c.digest(value)


@pytest.fixture
def saved(tmp_path, monkeypatch):
    root, audit = tmp_path / "production", tmp_path / "audit"
    plan = dict(purpose="calibration", replicates=192, kernels={"ZH": {}, "ZHS": {}},
                initializations=["rejection", "logical"], burns=[0], blocks=[], anchor_trials=10,
                runtime={"package_sha256": "package"}, cases=[dict(size=6, noise="bit", target=.03, rungs=[.1, .03],
                                       coarse=[.1, .03], chains=4, windows=[2], steps=2) for _ in range(4)])
    reference = dict(case=0, target_p=.03, estimate=.1, standard_error=.01, interval_999=[.07, .13])
    ref_summary = dict(records=[reference])
    c.atomic_json(root / "manifest.json", plan)
    c.atomic_json(root / "reference_summary.json", ref_summary)
    context = dict(sampling_manifest=sha(plan), references=[reference], runtime=plan["runtime"],
                   analysis_source_sha256=c.file_hash(bar.__file__),
                   reference_summary_sha256=c.file_hash(root / "reference_summary.json"))
    c.atomic_json(root / "analysis_manifest.json", context)
    audit_plan = dict(purpose="trace_audit_full", case=0, replicates=192, sampling_manifest=sha(plan))
    c.atomic_json(audit / "manifest.json", audit_plan)
    monkeypatch.setattr(reader.r, "read_plan", lambda *args: (audit_plan, plan))
    monkeypatch.setattr(reader, "_saved_native", lambda *args: {"pbs_job_id": "123.server"})
    records, payloads, artifact_markers = {}, {}, {}

    def add(path, identity, record):
        path = Path(path)
        marker = sha([str(path), identity, record])
        payload = {".json": sha(record), ".npz": sha([str(path), "array"])}
        records[str(path)] = (identity, record, marker, payload)
        if path.is_relative_to(root):
            stem = path.relative_to(root).as_posix()
            payloads[stem + ".done.json"] = marker
            payloads.update({stem + ext: value for ext, value in payload.items()})
            artifact_markers[stem] = marker

    anchor_rows = []
    for rep in range(192):
        row = dict(case=0, replicate=rep, seed=t.seed((32, 0, rep), 0), status="ok",
                   problem_hash="problem", trials=10, failures=5, estimate=.5,
                   interval=anchors.wilson(5, 10, .95), elapsed_seconds=1.)
        if rep == 1:
            row.update(failures=0, estimate=0., interval=anchors.wilson(0, 10, .95))
        if rep == 2:
            row.update(status="failed", error="recorded anchor failure")
        anchor_rows.append(row)
        add(root / "anchors" / f"0-{rep}", dict(manifest=sha(plan), case=0, replicate=rep), row)
    phase = dict(case=0, manifest=sha(plan), command="anchors", tasks=192, failed=1,
                 elapsed_seconds=2., records=anchor_rows)
    c.atomic_json(root / "anchors-0.json", phase)
    anchor_audit = anchors.audit_records(plan, 0, anchor_rows, "problem")
    anchor_audit.update(problem_hash="problem", phase_summary_reproduced=True,
                        anchor_phase_wall_seconds=2., archive_sha256="anchors",
                        summary_sha256=c.file_hash(root / "anchors-0.json"),
                        source_sha256=c.file_hash(anchors.__file__))
    all_rows, measurements = [], []
    for group in reader.r.groups(audit_plan):
        task_rows, input_markers = [], {}
        for rung in range(2):
            for chain in range(4):
                task = (*group, rung, chain)
                trace = dict(task=list(task), status="ok", problem_hash="problem")
                if task == (0, 0, 0, 0, 0, 0):
                    trace.update(status="failed", error="recorded sampling failure")
                path = root / "traces" / c.task_id(task)
                add(path, dict(manifest=sha(plan), task=list(task)), trace)
                input_markers[c.task_id(task)] = records[str(path)][2]
                task_rows.append(dict(task=list(task), status=trace["status"],
                                      redecoded_checkpoints=2 if trace["status"] == "ok" else 0,
                                      all_physical_states_redecoded=False, recorded_failure=trace.get("error"),
                                      saved_steps=2, initial_state_checked=True, recorded_seeds_checked=True,
                                      logical_initial_basis_checked=group[2] == 1,
                                      rejected_steps_retained_by_length_and_proposal_count=True))
        failed_tasks = [row["task"] for row in task_rows if row["status"] == "failed"]
        checkpoints = sum(row["redecoded_checkpoints"] for row in task_rows)
        audited = dict(group=list(group), tasks=8, failed_sampling=len(failed_tasks), redecoded_checkpoints=checkpoints,
                       records=task_rows, input_marker_sha256=input_markers)
        path = audit / "audit/groups" / c.task_id(group)
        add(path, dict(audit=sha(audit_plan), group=list(group)), audited)
        measurement = dict(group=list(group), status="ok", tasks=8, failed_sampling=len(failed_tasks),
                           redecoded_checkpoints=checkpoints, audit_marker_sha256=records[str(path)][2])
        add(audit / "measurements" / c.task_id(group),
            dict(manifest=sha(audit_plan), group=list(group)), measurement)
        measurements.append(measurement)
        group_rows = []
        for key in summary.expected_conditions(plan, 0, list(plan["kernels"])[group[1]], plan["initializations"][group[2]]):
            row = dict(zip(summary.CONDITION, key), group=list(group), replicate=group[3],
                       noise="bit", n=72, target_p=.03, estimate=.1, log_estimate=-2.3025850929940455,
                       log_se=.4, anchor_log_variance=.1,
                       interval=[math.exp(math.log(.1)-1.959963984540054*.4), math.exp(math.log(.1)+1.959963984540054*.4)],
                       covariance=[[.06]], adjacent_log_ratios=[math.log(.2)], available=True,
                       flagged=False, undefined=False, high_rhat=False, low_ess=False, failure=None,
                       reference=.1, reference_standard_error=.01, reference_interval_999=[.07, .13])
            if failed_tasks or group[3] in (1, 2):
                row.update(estimate=None, log_estimate=None, interval=None, available=False,
                           failure="sampling_failed" if failed_tasks else "anchor_unavailable")
                row.pop("covariance")
                row.pop("adjacent_log_ratios")
            row.update(bar.coverage_flags(row["interval"], reference))
            group_rows.append(row)
        add(root / "analysis" / c.task_id(group), dict(analysis=sha(context), group=list(group)),
            dict(status="ok", group=list(group), rows=group_rows, failed_tasks=failed_tasks))
        all_rows.extend(group_rows)
    c.atomic_json(audit / "summary.json", dict(manifest=sha(audit_plan), groups=768,
                  failed_audits=0, records=measurements))
    (root / "rows-0.jsonl").write_bytes(b"".join(c.canonical(row) + b"\n" for row in all_rows))
    cohorts = defaultdict(list)
    for row in all_rows:
        cohorts[tuple(row[k] for k in summary.CONDITION)].append(row)
    summaries = [dict(zip(summary.CONDITION, key), **summary.summarize_condition(rows, 192, reference))
                 for key, rows in cohorts.items()]
    c.atomic_json(root / "summary-0.json", dict(case=0, analysis=sha(context), conditions=len(summaries),
                  records=summaries, raw_rows_sha256=c.file_hash(root / "rows-0.jsonl"),
                  summary_source_sha256=c.file_hash(summary.__file__)))

    def verification(stage, archive_sha):
        expected = archive.expected_artifacts(plan, stage, 0, context if stage == "production-analysis" else None)
        data = {name: value for name, value in payloads.items()
                if any(name.endswith(ext) and name[:-len(ext)] in expected for ext in (".json", ".npz", ".done.json"))}
        data["manifest.json"] = c.file_hash(root / "manifest.json")
        if stage == "production-analysis":
            data.update({name: c.file_hash(root / name) for name in ("analysis_manifest.json", "reference_summary.json")})
        if stage == "production-anchors":
            data["anchors-0.json"] = c.file_hash(root / "anchors-0.json")
        return dict(stage=stage, case=0, archive_sha256=archive_sha, artifacts=len(expected),
                    manifest_sha256=c.file_hash(root / "manifest.json"), payload_sha256=data)

    evidence = dict(sampling_verification=verification("production-sampling", "sampling"),
                    analysis_verification=verification("production-analysis", "analysis"),
                    anchor_verification=verification("production-anchors", "anchors"), anchor_audit=anchor_audit,
                    reference_verification=dict(stage="reference", archive_sha256="reference",
                      payload_sha256={"summary.json": c.file_hash(root / "reference_summary.json")}),
                    reference_audit=dict(archive_sha256="reference", summary_sha256=c.file_hash(root / "reference_summary.json"),
                      summary_reproduced=True, all_seeds_verified=True, all_problem_metadata_verified=True,
                      model_hashes={"0": "problem"}, package_source_sha256=["package"],
                      source_sha256=c.file_hash(reader.reference_audit_module.__file__)))
    paths = {}
    for key, value in evidence.items():
        paths[key] = tmp_path / (key + ".json")
        c.atomic_json(paths[key], value)

    def artifact(path, identity, guards):
        identity_saved, record, marker, payload = records[str(path)]
        if identity != identity_saved:
            raise ValueError("artifact identity differs")
        return record, marker, payload
    monkeypatch.setattr(reader, "_artifact", artifact)
    return root, audit, paths, records, evidence


def run(saved):
    root, audit, paths, *_ = saved
    return reader.read_results(root, audit, 0, **paths)


def test_complete_fixed_cohort_and_honest_scope(saved):
    result = run(saved)
    assert result["groups"] == 768 and result["replicates"] == 192 and result["tasks"] == 6144
    assert result["failed_sampling"] == 1 and result["failed_anchors"] == [2] and result["zero_failure_anchors"] == [1]
    assert all(row["replicates"] == 192 for row in result["records"])
    assert {row["point_estimates"] for row in result["records"]} == {189, 190}
    assert all(row["bias"] is None for row in result["records"])
    assert result["current_archived_inputs_match_audited_inputs"]
    for flag in ("historical_consumed_input_hashes_recorded", "bar_bootstrap_recomputed",
                 "native_probe_reexecuted", "all_physical_states_redecoded", "archives_rehashed"):
        assert result[flag] is False


@pytest.mark.parametrize("kind", ["sampling", "analysis", "anchor", "reference"])
def test_mixed_archive_or_current_input_rejected(saved, kind):
    root, audit, paths, records, evidence = saved
    if kind == "reference":
        evidence["reference_audit"]["summary_sha256"] = "different"
        c.atomic_json(paths["reference_audit"], evidence["reference_audit"])
    elif kind == "anchor":
        evidence["anchor_audit"]["archive_sha256"] = "different"
        c.atomic_json(paths["anchor_audit"], evidence["anchor_audit"])
    else:
        key = "sampling_verification" if kind == "sampling" else "analysis_verification"
        stem = "traces/0-0-0-0-0-0.json" if kind == "sampling" else "analysis/0-0-0-0.json"
        evidence[key]["payload_sha256"][stem] = "different"
        c.atomic_json(paths[key], evidence[key])
    with pytest.raises(ValueError):
        run(saved)


@pytest.mark.parametrize("field", ["input_marker_sha256", "records", "tasks"])
def test_incomplete_or_changed_trace_audit_rejected(saved, field):
    root, audit, paths, records, evidence = saved
    row = records[str(audit / "audit/groups/0-0-0-0")][1]
    if field == "input_marker_sha256":
        row[field]["0-0-0-0-0-0"] = "changed"
    elif field == "records":
        row[field].pop()
    else:
        row[field] -= 1
    with pytest.raises(ValueError):
        run(saved)


def test_missing_group_is_not_sampling_failure(saved):
    root, audit, paths, records, evidence = saved
    data = json.loads((audit / "summary.json").read_text())
    data["records"].pop()
    c.atomic_json(audit / "summary.json", data)
    with pytest.raises(ValueError):
        run(saved)


def test_row_reference_and_summary_tampering_rejected(saved):
    root, audit, paths, records, evidence = saved
    records[str(root / "analysis/0-0-0-0")][1]["rows"][0]["reference"] = .2
    with pytest.raises(ValueError):
        run(saved)


def test_summary_arithmetic_change_rejected(saved):
    root, *_ = saved
    data = json.loads((root / "summary-0.json").read_text())
    data["records"][0]["replicates"] = 191
    c.atomic_json(root / "summary-0.json", data)
    with pytest.raises(ValueError):
        run(saved)


def test_successful_audit_checkpoint_schedule_required(saved):
    root, audit, paths, records, evidence = saved
    record = records[str(audit / "audit/groups/0-0-0-0")][1]["records"][1]
    record["initial_state_checked"] = False
    with pytest.raises(ValueError):
        run(saved)


def test_real_artifact_requires_both_payloads_and_detects_mutation(tmp_path):
    path = tmp_path / "one"
    c.save_artifact(path, {"id": 1}, {}, {"status": "failed"})
    guards = {}
    row, marker, payload = reader._artifact(path, {"id": 1}, guards)
    assert row["status"] == "failed" and set(payload) == {".npz", ".json"}
    path.with_suffix(".npz").write_bytes(b"changed")
    with pytest.raises(ValueError):
        reader._finish(guards)
    with pytest.raises(ValueError):
        reader._artifact(path, {"id": 1}, {})


def test_failure_denominator_and_zero_anchor_row_rules():
    spec = dict(noise="bit", size=6, target=.03, rungs=[.1, .03], coarse=[.1, .03])
    ref = dict(estimate=.1, standard_error=.01, interval_999=[.07, .13])
    row = dict(noise="bit", n=72, target_p=.03, reference=.1, reference_standard_error=.01,
               reference_interval_999=[.07, .13], ladder="fine", chains=4, estimate=None,
               log_estimate=None, interval=None, available=False, failure="anchor_unavailable")
    row.update(bar.coverage_flags(None, ref))
    anchor = dict(status="ok", failures=0, trials=10, estimate=0.)
    reader._check_row(row, spec, ref, anchor, set(), (0, 0, 0, 0))
    row["estimate"] = .1
    with pytest.raises(ValueError):
        reader._check_row(row, spec, ref, anchor, set(), (0, 0, 0, 0))


def test_saved_arithmetic_includes_independent_anchor_without_bootstrap():
    spec = dict(noise="bit", size=6, target=.03, rungs=[.1, .03], coarse=[.1, .03])
    ref = dict(estimate=.1, standard_error=.01, interval_999=[.07, .13])
    anchor = dict(status="ok", failures=5, trials=10, estimate=.5)
    row = dict(noise="bit", n=72, target_p=.03, reference=.1, reference_standard_error=.01,
               reference_interval_999=[.07, .13], ladder="fine", chains=4,
               covariance=[[.06]], adjacent_log_ratios=[math.log(.2)])
    row.update(bar.b.with_anchor_variance(dict(estimate=.1, log_estimate=math.log(.1), log_se=math.sqrt(.06)), anchor))
    row.update(bar.coverage_flags(row["interval"], ref))
    reader._check_row(row, spec, ref, anchor, set(), (0, 0, 0, 0))
    row["log_se"] = math.sqrt(.06)
    with pytest.raises(ValueError):
        reader._check_row(row, spec, ref, anchor, set(), (0, 0, 0, 0))
    row.update(log_estimate=None, log_se=None, interval=None, available=False, failure="ValueError('solver')")
    row.update(bar.coverage_flags(None, ref))
    with pytest.raises(ValueError):
        reader._check_row(row, spec, ref, anchor, set(), (0, 0, 0, 0))
    row["estimate"] = None
    reader._check_row(row, spec, ref, anchor, set(), (0, 0, 0, 0))


def test_saved_native_pbs_and_script_binding(tmp_path):
    root = tmp_path
    plan = {"full": True}
    keys = ("fixture", "source_sha256", "runtime", "platform", "machine", "python_build", "byteorder",
            "thread_environment", "native_ldpc_sha256", "problem_hash", "repeated", "fresh", "decoder_probe")
    profile = dict.fromkeys(keys, "same")
    for name, data in (("platform_profile", profile), ("platform_fixture", {}),
                       ("native_preflight", dict(manifest=sha(plan), profile=profile, pbs_job_id="123.server")),
                       ("execution_intent", dict(manifest=sha(plan), pbs_job_id="123.server"))):
        c.atomic_json(root / (name + ".json"), data)
    (root / "audit.sh").write_text("pinned command")
    submission = dict(manifest=sha(plan), job_id="123.server", command=["qsub", "/original/audit.sh"],
                      script_sha256=c.file_hash(root / "audit.sh"))
    c.atomic_json(root / "submission.json", submission)
    summary_data = dict(native_preflight_sha256=c.file_hash(root / "native_preflight.json"))
    assert reader._saved_native(root, plan, summary_data, {})["pbs_job_id"] == "123.server"
    submission["job_id"] = "124.server"
    c.atomic_json(root / "submission.json", submission)
    with pytest.raises(ValueError):
        reader._saved_native(root, plan, summary_data, {})


def test_source_or_metadata_change_before_completion_rejected(tmp_path):
    path = tmp_path / "source.py"
    path.write_text("original")
    guards = {}
    reader._guard(path, guards)
    path.write_text("changed")
    with pytest.raises(ValueError):
        reader._finish(guards)
