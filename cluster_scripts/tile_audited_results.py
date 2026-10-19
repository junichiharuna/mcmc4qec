"""Bind complete calibration results to saved scientific audits, read-only."""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import math
import os
from pathlib import Path

import numpy as np

import calibration as c
import artifact_archive as archive
import audit_tile_anchors as anchor_module
import audit_tile_reference as reference_audit_module
import tile_bar_analysis as bar
import tile_summary as s
import tile_trace_audit_run as r


WARNING = ("Current recovered inputs are bound to saved audits. Historical consumed-input hashes were not recorded; "
           "this is not proof of the bytes consumed at analysis time. Use completed read-only snapshots. "
           "Only saved checkpoint re-decoding is evidenced, not full trajectory replay or independent decoder validation. "
           "Saved native evidence is checked without a fresh probe. No bootstrap recomputation or convergence/coverage guarantee. "
           "Archive verification reports are reused; archive bytes and raw reference trials are not re-read.")


def _require(ok, message):
    if not ok:
        raise ValueError(message + "; inspect inputs and recompute affected groups if necessary")


def _stat(path):
    value = Path(path).stat()
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _guard(path, guards):
    path = Path(path)
    before = _stat(path)
    checksum = c.file_hash(path)
    _require(before == _stat(path), "input changed during hashing")
    previous = guards.get(str(path))
    _require(previous is None or previous == (checksum, before), "input changed between reads")
    guards[str(path)] = (checksum, before)
    return checksum


def _json(path, guards):
    _guard(path, guards)
    return json.loads(Path(path).read_text())


def _finish(guards):
    for path, (checksum, stat) in guards.items():
        _require(_stat(path) == stat, "input file changed before completion")
        if not path.endswith(".npz"):
            _require(c.file_hash(path) == checksum, "input metadata changed before completion")


def _artifact(path, identity, guards):
    """Validate the existing marker contract without decompressing large arrays."""
    path = Path(path)
    marker_path = path.with_suffix(".done.json")
    _require(marker_path.is_file(), f"missing artifact {path}")
    marker = _json(marker_path, guards)
    _require(marker["identity"] == identity and set(marker["sha256"]) == {".json", ".npz"},
             "artifact identity or payload set differs")
    for extension, expected in marker["sha256"].items():
        _require(_guard(path.with_suffix(extension), guards) == expected, "artifact payload checksum differs")
    return json.loads(path.with_suffix(".json").read_text()), guards[str(marker_path)][0], marker["sha256"]


def _saved_native(root, plan, summary, guards):
    profile = _json(root / "platform_profile.json", guards)
    _json(root / "platform_fixture.json", guards)
    native = _json(root / "native_preflight.json", guards)
    intent = _json(root / "execution_intent.json", guards)
    submission = _json(root / "submission.json", guards)
    _require(guards[str(root / "native_preflight.json")][0] == summary["native_preflight_sha256"],
             "saved native evidence differs from audit summary")
    r.a.validate_platform(profile, native["profile"])
    job = native.get("pbs_job_id")
    _require(job and job != "dry-run" and intent.get("pbs_job_id") == job and submission.get("job_id") == job,
             "saved PBS job binding differs")
    for value in (native, intent, submission):
        _require(value.get("manifest") == c.digest(plan), "saved audit manifest binding differs")
    script = root / "audit.sh"
    command = submission.get("command", [])
    _require(len(command) == 2 and command[0] == "qsub" and Path(command[1]).name == "audit.sh",
             "saved audit was not submitted through qsub")
    _require(_guard(script, guards) == submission["script_sha256"], "saved qsub script differs")
    return dict(pbs_job_id=job, native_preflight_sha256=summary["native_preflight_sha256"])


def _verification(value, stage, plan, case, manifest_hash, context=None):
    _require(value.get("stage") == stage and value.get("case") == case and value.get("archive_sha256"),
             "archive verification stage/case differs")
    expected = archive.expected_artifacts(plan, stage, case, context)
    payloads = value["payload_sha256"]
    markers = {name[:-10] for name in payloads if name.endswith(".done.json")}
    arrays = {name[:-4] for name in payloads if name.endswith(".npz")}
    _require(markers == set(expected) and arrays == set(expected) and value["artifacts"] == len(expected),
             "archive verification omitted or duplicated planned artifacts")
    _require(value["manifest_sha256"] == manifest_hash and payloads.get("manifest.json") == manifest_hash,
             "archive sampling manifest differs")
    return expected


def _match_payload(verification, stem, marker, payload):
    wanted = verification["payload_sha256"]
    _require(wanted.get(stem + ".done.json") == marker and
             all(wanted.get(stem + extension) == checksum for extension, checksum in payload.items()),
             "current payload differs from verified archive")


def _check_row(row, spec, reference, anchor, failed_tasks, group):
    _require(row["noise"] == spec["noise"] and row["n"] == 2 * spec["size"] ** 2 and
             row["target_p"] == spec["target"], "analysis physical condition differs")
    for key, source in (("reference", "estimate"), ("reference_standard_error", "standard_error"),
                        ("reference_interval_999", "interval_999")):
        _require(row[key] == reference[source], "analysis row reference differs")
    ladder = spec["coarse"] if row["ladder"] == "coarse" else spec["rungs"]
    used = {spec["rungs"].index(p) for p in ladder}
    failed = any(task[-2] in used and task[-1] < row["chains"] for task in failed_tasks)
    unavailable = anchor["status"] != "ok" or not anchor["failures"]
    if failed or unavailable:
        _require(row["failure"] == ("sampling_failed" if failed else "anchor_unavailable") and
                 row["estimate"] is None and row["log_estimate"] is None and
                 row["interval"] is None and row["available"] is False,
                 "recorded sampling/anchor failure was not retained")
    else:
        _require(row["failure"] not in ("sampling_failed", "anchor_unavailable"),
                 "analysis failure does not match audited inputs")
        if row["estimate"] is not None:
            expected = (1 - anchor["estimate"]) / (anchor["trials"] * anchor["estimate"])
            _require(math.isclose(row["anchor_log_variance"], expected, rel_tol=1e-12, abs_tol=0),
                     "analysis anchor variance differs")
        if row["log_estimate"] is not None:
            edges = np.asarray(row["adjacent_log_ratios"], dtype=float)
            covariance = np.asarray(row["covariance"], dtype=float)
            count = len(ladder) - 1
            _require(edges.shape == (count,) and covariance.shape == (count, count) and
                     np.isfinite(edges).all() and np.isfinite(covariance).all() and
                     np.allclose(covariance, covariance.T, rtol=1e-12, atol=1e-14), "saved BAR arithmetic shape differs")
            logp = math.log(anchor["estimate"]) + float(edges.sum())
            reproduced = bar.b.with_anchor_variance(dict(log_estimate=logp,
                estimate=math.exp(logp) if logp <= 0 else None,
                log_se=math.sqrt(max(0., float(covariance.sum())))), anchor)
            for key in ("log_estimate", "estimate", "log_se", "interval", "anchor_log_variance"):
                left, right = row[key], reproduced[key]
                _require(left is None and right is None or left is not None and right is not None and
                         np.allclose(left, right, rtol=1e-12, atol=1e-14), "saved BAR/anchor arithmetic differs")
            _require(row["available"] == reproduced["available"] and row["failure"] == reproduced["failure"],
                     "saved BAR availability differs")
        else:
            _require(row["estimate"] is None and row["log_se"] is None and row["interval"] is None and
                     row["available"] is False and isinstance(row["failure"], str) and bool(row["failure"]),
                     "estimation exception row contains contradictory numerical results")
    _require(all(row[key] == value for key, value in bar.coverage_flags(row["interval"], reference).items()),
             "saved row coverage flags differ")


def read_results(root, audit_root, case, *, sampling_verification, analysis_verification,
                 anchor_verification, anchor_audit, reference_verification, reference_audit):
    """Read completed immutable snapshots; return a new report without writing inputs."""
    root, audit_root = Path(root), Path(audit_root)
    guards = {}
    source_files = {"adapter": __file__, **{module.__name__: module.__file__ for module in
        (c, archive, anchor_module, reference_audit_module, reference_audit_module.r,
         bar, bar.b, bar.t, s, r, r.a, r.a.platform_probe)}}
    source_hashes = {name: _guard(Path(path), guards) for name, path in source_files.items()}
    paths = dict(sampling_verification=sampling_verification, analysis_verification=analysis_verification,
                 anchor_verification=anchor_verification, anchor_audit=anchor_audit,
                 reference_verification=reference_verification, reference_audit=reference_audit)
    evidence = {name: _json(Path(path), guards) for name, path in paths.items()}
    plan = _json(root / "manifest.json", guards)
    context = _json(root / "analysis_manifest.json", guards)
    reference_summary = _json(root / "reference_summary.json", guards)
    summary = _json(root / f"summary-{case}.json", guards)
    raw_path = root / f"rows-{case}.jsonl"
    _guard(raw_path, guards)
    _require(plan["purpose"] == "calibration" and plan["replicates"] == 192 and
             len(plan["kernels"]) == len(plan["initializations"]) == 2 and case in range(4),
             "fixed 192-replicate production required")
    manifest, analysis = c.digest(plan), c.digest(context)
    _require(context["sampling_manifest"] == manifest and context["runtime"] == plan["runtime"] and
             context["analysis_source_sha256"] == c.file_hash(bar.__file__), "analysis context/source differs")
    ref_hash = guards[str(root / "reference_summary.json")][0]
    _require(context["reference_summary_sha256"] == ref_hash and summary["analysis"] == analysis and
             summary["case"] == case and summary["raw_rows_sha256"] == guards[str(raw_path)][0] and
             summary["summary_source_sha256"] == source_hashes[s.__name__],
             "summary/reference/raw rows binding differs")
    references = [v for v in context["references"] if v["case"] == case]
    _require(len(references) == 1 and references == [v for v in reference_summary["records"] if v["case"] == case],
             "independent reference identity differs")
    reference, spec = references[0], plan["cases"][case]
    _require(reference["target_p"] == spec["target"], "reference target differs")
    manifest_hash = guards[str(root / "manifest.json")][0]
    expected = {}
    for label, stage in (("sampling", "production-sampling"), ("analysis", "production-analysis"), ("anchor", "production-anchors")):
        expected[label] = _verification(evidence[label + "_verification"], stage, plan, case, manifest_hash,
                                        context if label == "analysis" else None)
    analysis_payloads = evidence["analysis_verification"]["payload_sha256"]
    _require(analysis_payloads.get("analysis_manifest.json") == guards[str(root / "analysis_manifest.json")][0] and
             analysis_payloads.get("reference_summary.json") == ref_hash, "analysis archive reference/context differs")
    aa, ra, rv = (evidence[key] for key in ("anchor_audit", "reference_audit", "reference_verification"))
    _require(aa["archive_sha256"] == evidence["anchor_verification"]["archive_sha256"] and
             aa["source_sha256"] == c.file_hash(anchor_module.__file__) and aa["phase_summary_reproduced"] is True,
             "anchor scientific audit binding differs")
    _require(rv["stage"] == "reference" and ra["archive_sha256"] == rv["archive_sha256"] and
             ra["summary_sha256"] == ref_hash == rv["payload_sha256"].get("summary.json") and
             all(ra.get(key) is True for key in ("summary_reproduced", "all_seeds_verified", "all_problem_metadata_verified")) and
             ra["source_sha256"] == c.file_hash(reference_audit_module.__file__) and
             ra["package_source_sha256"] == [plan["runtime"]["package_sha256"]] and
             ra["model_hashes"].get(str(case)) == aa["problem_hash"], "reference scientific audit binding differs")
    phase = _json(root / f"anchors-{case}.json", guards)
    _require(aa["summary_sha256"] == guards[str(root / f"anchors-{case}.json")][0] and
             phase["manifest"] == manifest and phase["case"] == case and phase["command"] == "anchors",
             "anchor phase summary binding differs")
    inventory = hashlib.sha256()
    count = 0

    def artifact(path, identity):
        nonlocal count
        record, marker, payload = _artifact(path, identity, guards)
        inventory.update(c.canonical(dict(path=str(path), marker=marker, payload=payload)) + b"\n")
        count += 1
        return record, marker, payload

    anchor_rows = []
    for rep in range(192):
        stem = f"anchors/{case}-{rep}"
        row, marker, payload = artifact(root / stem, expected["anchor"][stem])
        for label in ("sampling", "anchor"):
            _match_payload(evidence[label + "_verification"], stem, marker, payload)
        _require(row["replicate"] == rep, "anchor filename/replicate differs")
        anchor_rows.append(row)
    regenerated = anchor_module.audit_records(plan, case, anchor_rows, aa["problem_hash"])
    _require(all(c.canonical(aa[key]) == c.canonical(value) for key, value in regenerated.items()),
             "anchor audit counts differ from current anchors")
    _require(c.canonical(sorted(phase["records"], key=lambda row: row["replicate"])) == c.canonical(anchor_rows) and
             phase["tasks"] == 192 and phase["failed"] == len(regenerated["failed_replicates"]) and
             aa["anchor_phase_wall_seconds"] == phase["elapsed_seconds"], "anchor phase records differ")
    # read_plan validates pinned source/runtime/profile/fixture using the frozen runner.
    _json(audit_root / "manifest.json", guards)
    audit_plan, audited_sampling = r.read_plan(audit_root, root)
    _require(c.canonical(audited_sampling) == c.canonical(plan) and audit_plan["purpose"] == "trace_audit_full" and
             audit_plan["replicates"] == 192 and audit_plan["case"] == case and audit_plan["sampling_manifest"] == manifest,
             "full matching trace audit required")
    if (audit_root / "sampling_manifest.json").exists():
        _json(audit_root / "sampling_manifest.json", guards)
    audit_summary = _json(audit_root / "summary.json", guards)
    groups = r.groups(audit_plan)
    _require(len(groups) == 768 and audit_summary["manifest"] == c.digest(audit_plan) and
             audit_summary["groups"] == 768 and audit_summary["failed_audits"] == 0 and
             [tuple(v["group"]) for v in audit_summary["records"]] == groups, "incomplete full trace audit")
    native = _saved_native(audit_root, audit_plan, audit_summary, guards)
    cohorts, totals = defaultdict(list), dict(tasks=0, failed_sampling=0, redecoded_checkpoints=0)
    with raw_path.open(encoding="utf-8") as raw:
        for group, measurement in zip(groups, audit_summary["records"]):
            gid = c.task_id(group)
            saved, _, _ = artifact(audit_root / "measurements" / gid, dict(manifest=c.digest(audit_plan), group=list(group)))
            _require(c.canonical(saved) == c.canonical(measurement) and saved["status"] == "ok", "audit measurement differs")
            audited, marker, _ = artifact(audit_root / "audit/groups" / gid, dict(audit=c.digest(audit_plan), group=list(group)))
            _require(marker == measurement["audit_marker_sha256"] and audited["group"] == list(group), "audit group marker differs")
            tasks = [(*group, rung, chain) for rung, chain in itertools.product(range(len(spec["rungs"])), range(spec["chains"]))]
            _require([tuple(v["task"]) for v in audited["records"]] == tasks and
                     set(audited["input_marker_sha256"]) == {c.task_id(task) for task in tasks}, "audit task census differs")
            failed, checkpoints = set(), 0
            for task, audit_record in zip(tasks, audited["records"]):
                stem = "traces/" + c.task_id(task)
                trace, marker, payload = artifact(root / stem, expected["sampling"][stem])
                _match_payload(evidence["sampling_verification"], stem, marker, payload)
                _require(marker == audited["input_marker_sha256"][c.task_id(task)] and trace["task"] == list(task) and
                         trace["status"] in ("ok", "failed") and trace["status"] == audit_record["status"],
                         "current trace differs from scientifically audited input")
                if trace["status"] == "failed":
                    failed.add(task)
                    _require(audit_record["recorded_failure"] == trace["error"] and audit_record["redecoded_checkpoints"] == 0,
                             "failed trace audit differs")
                else:
                    _require(trace["problem_hash"] == aa["problem_hash"], "trace model differs from anchor/reference")
                    steps = spec["steps"]
                    checkpoint_count = (steps - 1) // 1000 + 1 + int((steps - 1) % 1000 != 0)
                    _require(audit_record["saved_steps"] == steps and
                             audit_record["redecoded_checkpoints"] == checkpoint_count and
                             audit_record["initial_state_checked"] is True and audit_record["recorded_seeds_checked"] is True and
                             audit_record["rejected_steps_retained_by_length_and_proposal_count"] is True and
                             audit_record["logical_initial_basis_checked"] == (plan["initializations"][group[2]] == "logical") and
                             audit_record["all_physical_states_redecoded"] is False,
                             "successful trace audit omitted scheduled scientific checks")
                checkpoints += audit_record["redecoded_checkpoints"]
            for key, value in dict(tasks=len(tasks), failed_sampling=len(failed), redecoded_checkpoints=checkpoints).items():
                _require(audited[key] == measurement[key] == value, "audit group counts differ")
                totals[key] += value
            stem = "analysis/" + gid
            record, marker, payload = artifact(root / stem, expected["analysis"][stem])
            _match_payload(evidence["analysis_verification"], stem, marker, payload)
            _require(record["status"] == "ok" and record["group"] == list(group) and
                     sorted(record["failed_tasks"]) == sorted(map(list, failed)), "analysis failed-task census differs")
            wanted = set(s.expected_conditions(plan, case, list(plan["kernels"])[group[1]], plan["initializations"][group[2]]))
            seen = set()
            for row in record["rows"]:
                key = tuple(row[name] for name in s.CONDITION)
                _require(key in wanted and key not in seen and row["group"] == list(group) and row["replicate"] == group[3],
                         "analysis condition/replicate census differs")
                seen.add(key)
                _check_row(row, spec, reference, anchor_rows[group[3]], failed, group)
                line = raw.readline()
                _require(line and c.canonical(json.loads(line)) == c.canonical(row), "raw rows differ from analysis artifact")
                cohorts[key].append({name: row[name] for name in ("replicate", "estimate", "interval", "available", "failure",
                                                                 "flagged", "undefined", "high_rhat", "low_ess")})
            _require(seen == wanted, "analysis omitted planned conditions")
        _require(not raw.read(), "unexpected trailing raw rows")
    stored = {tuple(row[name] for name in s.CONDITION): row for row in summary["records"]}
    _require(len(stored) == len(summary["records"]) == summary["conditions"] and set(stored) == set(cohorts),
             "summary condition census differs")
    results = []
    for key, rows in cohorts.items():
        result = dict(zip(s.CONDITION, key), **s.summarize_condition(rows, 192, reference))
        _require(c.canonical(result) == c.canonical(stored[key]), "summary arithmetic differs")
        results.append(result)
    final_plan, final_sampling = r.read_plan(audit_root, root)
    _require(c.canonical(final_plan) == c.canonical(audit_plan) and c.canonical(final_sampling) == c.canonical(plan),
             "pinned runtime or audit plan changed before completion")
    _finish(guards)
    return dict(schema=1, purpose="audited_calibration_results", case=case, replicates=192, groups=768,
                sampling_manifest=manifest, analysis_context=analysis, trace_audit_manifest=c.digest(audit_plan),
                conditions=len(results), records=results, **totals,
                failed_anchors=regenerated["failed_replicates"], zero_failure_anchors=regenerated["zero_failure_replicates"],
                input_artifacts=count, artifact_inventory_sha256=inventory.hexdigest(),
                input_sha256={path: value[0] for path, value in guards.items() if not path.endswith((".npz", ".done.json"))
                              and Path(path).parent in (root, audit_root, *(Path(p).parent for p in paths.values()))},
                native_evidence=native, source_sha256=source_hashes["adapter"], source_hashes=source_hashes,
                current_archived_inputs_match_audited_inputs=True, historical_consumed_input_hashes_recorded=False,
                bar_bootstrap_recomputed=False, native_probe_reexecuted=False, all_physical_states_redecoded=False,
                full_trajectory_replayed=False, archives_rehashed=False, raw_reference_trials_recounted=False,
                terminal_payload_stat_checked=True, warning=WARNING)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "audit-root", "sampling-verification", "analysis-verification", "anchor-verification",
                 "anchor-audit", "reference-verification", "reference-audit", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--case", type=int, choices=range(4), required=True)
    args = vars(parser.parse_args())
    output = args.pop("output")
    _require(os.environ.get("PBS_JOBID"), "submit full payload reading through qsub")
    _require(not output.exists(), "preserve existing report")
    result = read_results(**args)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(c.canonical(result) + b"\n")
    print(json.dumps(dict(output=str(output), case=result["case"], groups=result["groups"])))


if __name__ == "__main__":
    main()
