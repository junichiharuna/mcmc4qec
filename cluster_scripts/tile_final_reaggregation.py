"""Run the complete audited calibration and fixed downstream reports once per case."""
import argparse
import ast
import json
import math
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time
import traceback

import calibration as c
import tile_audited_results as audited
import tile_comparisons as comparisons
import tile_precision_assessment as precision
import tile_weight_comparison as weight
import tile_initialization_strata as strata

THREADS = {key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
EVIDENCE = ("sampling_verification", "analysis_verification", "anchor_verification", "anchor_audit",
            "reference_verification", "reference_audit")
MODULES = dict(audited=audited, comparisons=comparisons, precision=precision, weight=weight, strata=strata)
WARNING = ("Complete fixed cohorts; failed, unavailable and undefined outcomes are retained by the original reports. "
           "Initial resource ceiling is not a measured prediction or completion guarantee. Read-only snapshots are required. "
           "No historical consumed-input proof, BAR bootstrap rerun, all-state decoding or nominal coverage guarantee.")


def resources():
    return dict(requested_nodes=1, cpus=1, memory_gb=32, wall_seconds=7200, walltime="02:00:00",
                max_nodes=2, measured=False)


def source_files():
    """Static local-import closure includes function-local imports without executing them."""
    directory = Path(__file__).resolve().parent
    pending = [Path(__file__).name, "submit_tile_final_reaggregation.py", *[Path(m.__file__).name for m in MODULES.values()]]
    found = {}
    while pending:
        name = pending.pop()
        if name in found: continue
        path = directory / name
        if not path.is_file(): raise ValueError("missing source dependency: " + name)
        found[name] = path
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            imports = ([alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import)
                       else [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            pending.extend(module + ".py" for module in imports if (directory / (module + ".py")).is_file())
    return found


def source_hashes():
    return {name: c.file_hash(path) for name, path in source_files().items()}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_completion(receipt, jobs):
    if len(jobs) != 3 or len(set(jobs.values())) != 3:
        raise ValueError("three distinct upstream job identities required")
    for job in jobs.values():
        value = receipt.get("Jobs", {}).get(job, {})
        if value.get("job_state") != "F" or value.get("Exit_status") != 0:
            raise ValueError("upstream job is not F/exit0: " + job)


def snapshot(production_root, audit_root, case, evidence, completion_receipt, receipts):
    """Metadata-only preparation; rows/payload hashing runs on the compute node."""
    production_root, audit_root = Path(production_root), Path(audit_root)
    paths = {"production_manifest": production_root / "manifest.json",
             "analysis_manifest": production_root / "analysis_manifest.json",
             "reference_summary": production_root / "reference_summary.json",
             "summary": production_root / f"summary-{case}.json",
             "analysis_summary": production_root / f"analysis_summary-{case}.json",
             "sample_summary": production_root / f"sample-{case}.json",
             "anchor_summary": production_root / f"anchors-{case}.json"}
    paths.update({"audit_" + name: audit_root / (name + ".json") for name in
                  ("manifest", "sampling_manifest", "summary", "platform_profile", "platform_fixture", "native_preflight")})
    paths.update({"evidence_" + key: Path(value) for key, value in evidence.items()})
    paths.update({"receipt_" + key: Path(value) for key, value in receipts.items()})
    paths["completion_receipt"] = Path(completion_receipt)
    ledgers = dict(sampling=production_root / f"submission-{case}.json",
                   analysis=production_root / f"analysis_submission-{case}.json",
                   trace_audit=audit_root / "submission.json")
    paths.update({"ledger_" + key: value for key, value in ledgers.items()})
    before = {str(path.resolve()): c.file_hash(path) for path in paths.values()}
    plan = read_json(paths["production_manifest"])
    context = read_json(paths["analysis_manifest"])
    if c.canonical(plan) != c.canonical(audited.bar.b.make_plan()) or plan["replicates"] != 192:
        raise ValueError("fixed production manifest and runtime required")
    if context["sampling_manifest"] != c.digest(plan) or context["runtime"] != plan["runtime"]:
        raise ValueError("analysis context differs")
    if context["analysis_source_sha256"] != c.file_hash(audited.bar.__file__):
        raise ValueError("analysis source differs")
    if context["reference_summary_sha256"] != c.file_hash(paths["reference_summary"]):
        raise ValueError("reference binding differs")
    audit_plan, audit_sampling = audited.r.read_plan(audit_root, production_root)
    summary = read_json(paths["audit_summary"])
    if (audit_plan["purpose"] != "trace_audit_full" or audit_plan["replicates"] != 192 or audit_plan["case"] != case
            or c.canonical(audit_sampling) != c.canonical(plan) or summary["manifest"] != c.digest(audit_plan)
            or summary["groups"] != 768 or summary["failed_audits"] != 0
            or [tuple(row["group"]) for row in summary["records"]] != audited.r.groups(audit_plan)
            or c.file_hash(paths["audit_native_preflight"]) != summary["native_preflight_sha256"]):
        raise ValueError("complete full trace audit required")
    formal = read_json(paths["summary"])
    analysis_summary = read_json(paths["analysis_summary"])
    if (formal["case"] != case or formal["conditions"] != 352 or formal["analysis"] != c.digest(context)
            or analysis_summary["groups"] != 768 or analysis_summary["rows"] != 67584):
        raise ValueError("complete fixed analysis required")
    jobs = {}
    receipt = read_json(completion_receipt)
    scripts = dict(sampling=production_root / f"sample-{case}.sh", analysis=production_root / f"analyze-{case}.sh",
                   trace_audit=audit_root / "audit.sh")
    for label, path in ledgers.items():
        ledger = read_json(path)
        expected_manifest = c.digest(audit_plan if label == "trace_audit" else plan)
        if ledger.get("manifest") != expected_manifest:
            raise ValueError("upstream ledger manifest differs")
        if label == "analysis" and ledger.get("analysis_manifest_sha256") != c.file_hash(paths["analysis_manifest"]):
            raise ValueError("upstream analysis context differs")
        job = ledger["job_id"]
        if not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", job): raise ValueError("invalid upstream job id")
        jobs[label] = job
        command = ledger["command"]
        if len(command) != 2 or command[0] != "qsub": raise ValueError("upstream qsub command differs")
        script = Path(command[1])
        if not script.is_absolute() or script != scripts[label] or c.file_hash(script) != ledger["script_sha256"]:
            raise ValueError("upstream script differs")
        before[str(script.resolve())] = c.file_hash(script)
        arguments = receipt.get("Jobs", {}).get(job, {}).get("Submit_arguments")
        if not arguments or shlex.split(arguments) != [str(script)]:
            raise ValueError("upstream PBS script binding differs")
    check_completion(receipt, jobs)
    if read_json(paths["audit_native_preflight"])["pbs_job_id"] != jobs["trace_audit"]:
        raise ValueError("native audit job differs")
    if any(c.file_hash(path) != digest for path, digest in before.items()):
        raise ValueError("inputs changed while preparing snapshot")
    rows = production_root / f"rows-{case}.jsonl"
    stat = rows.stat()
    return dict(production=plan, sampling_manifest=c.digest(plan), analysis_context=c.digest(context),
                trace_audit_manifest=c.digest(audit_plan), upstream_jobs=jobs, input_sha256=before,
                source_sha256=source_hashes(), python_sha256=c.file_hash(Path(sys.executable).resolve()),
                runtime=audited.bar.b.runtime(), rows_sha256=formal["raw_rows_sha256"],
                rows_stat=dict(size=stat.st_size, mtime_ns=stat.st_mtime_ns))


def prepare(root, production_root, audit_root, case, evidence, completion_receipt, receipts=None):
    root, production_root, audit_root = map(lambda value: Path(value).resolve(), (root, production_root, audit_root))
    if any(root == path or root.is_relative_to(path) or path.is_relative_to(root) for path in (production_root, audit_root)):
        raise ValueError("independent output root required")
    if type(case) is not int or case not in range(4) or set(evidence) != set(EVIDENCE):
        raise ValueError("valid case and exact six adapter evidence files required")
    if root.exists(): raise ValueError("new output root required")
    evidence = {key: str(Path(value).resolve()) for key, value in evidence.items()}
    receipts = {key: str(Path(value).resolve()) for key, value in (receipts or {}).items()}
    completion_receipt = str(Path(completion_receipt).resolve())
    state = snapshot(production_root, audit_root, case, evidence, completion_receipt, receipts)
    plan = dict(schema=1, purpose="final_calibration_reaggregation", case=case, replicates=192, groups=768,
                production_root=str(production_root), audit_root=str(audit_root), evidence=evidence, receipts=receipts,
                completion_receipt=completion_receipt, snapshot=state, resources=resources(), required_threads=THREADS,
                phases=["audited", "comparisons", "precision", "weight"] + (["strata"] if case in (2, 3) else []),
                warning=WARNING)
    root.mkdir(parents=True, exist_ok=False)
    with (root / "manifest.json").open("xb") as stream: stream.write(c.canonical(plan) + b"\n")
    return plan


def read_plan(root):
    root = Path(root).resolve()
    plan = read_json(root / "manifest.json")
    if (plan["purpose"] != "final_calibration_reaggregation" or type(plan["case"]) is not int or plan["case"] not in range(4)
            or plan["replicates"] != 192 or plan["groups"] != 768 or plan["resources"] != resources()
            or plan["required_threads"] != THREADS or set(plan["evidence"]) != set(EVIDENCE)
            or plan["phases"] != ["audited", "comparisons", "precision", "weight"] + (["strata"] if plan["case"] in (2, 3) else [])):
        raise ValueError("fixed reaggregation plan differs")
    for path in (Path(plan["production_root"]), Path(plan["audit_root"])):
        if root == path or root.is_relative_to(path) or path.is_relative_to(root): raise ValueError("independent root required")
    state = snapshot(plan["production_root"], plan["audit_root"], plan["case"], plan["evidence"],
                     plan["completion_receipt"], plan["receipts"])
    if c.canonical(state) != c.canonical(plan["snapshot"]): raise ValueError("input, source, runtime or receipt changed")
    return plan


def execution_binding(root, plan):
    import submit_tile_final_reaggregation as submitter
    ledger = read_json(root / "submission.json")
    intent = read_json(root / "submission-intent.json")
    if ({key: value for key, value in ledger.items() if key != "job_id"} != intent
            or ledger["job_id"] != os.environ.get("PBS_JOBID") or ledger["manifest"] != c.digest(plan)
            or ledger["resource"] != resources() or ledger["script_sha256"] != c.file_hash(root / "reaggregate.sh")
            or ledger["upstream_completion_sha256"] != c.file_hash(root / "upstream-completion-at-submit.json")
            or ledger["bundle_binding"] != submitter.bundle_binding(Path(__file__).resolve().parents[1], plan)):
        raise ValueError("PBS execution does not match submission intent/ledger/script")
    return dict(job_id=ledger["job_id"], submission_sha256=c.file_hash(root / "submission.json"),
                intent_sha256=c.file_hash(root / "submission-intent.json"), script_sha256=ledger["script_sha256"])


def analysis_stats(plan):
    """Guard the downstream metadata snapshot without a second numerical pass."""
    root = Path(plan["production_root"])
    paths = [root / f"rows-{plan['case']}.jsonl"]
    for ki in range(2):
        for ii in range(2):
            for rep in range(192):
                stem = root / "analysis" / f"{plan['case']}-{ki}-{ii}-{rep}"
                paths.extend(stem.with_suffix(suffix) for suffix in (".json", ".npz", ".done.json"))
    return {str(path): [path.stat().st_size, path.stat().st_mtime_ns, path.stat().st_ino] for path in paths}


def validate_report(plan, phase, report):
    state = plan["snapshot"]
    if report.get("case") != plan["case"]: raise ValueError("report case differs")
    if phase == "audited":
        expected = dict(purpose="audited_calibration_results", replicates=192, groups=768, conditions=352,
                        sampling_manifest=state["sampling_manifest"], analysis_context=state["analysis_context"],
                        trace_audit_manifest=state["trace_audit_manifest"], historical_consumed_input_hashes_recorded=False,
                        bar_bootstrap_recomputed=False, all_physical_states_redecoded=False,
                        current_archived_inputs_match_audited_inputs=True, terminal_payload_stat_checked=True)
        if any(report.get(key) != value for key, value in expected.items()) or not report.get("artifact_inventory_sha256"):
            raise ValueError("adapter full-cohort report contract differs")
        if len(report.get("records", [])) != 352: raise ValueError("missing adapter conditions")
        if report.get("source_sha256") != c.file_hash(audited.__file__): raise ValueError("adapter source differs")
        required = [Path(plan["production_root"]) / name for name in
                    ("manifest.json", "analysis_manifest.json", "reference_summary.json", f"summary-{plan['case']}.json")]
        required.extend(Path(value) for value in plan["evidence"].values())
        if any(report.get("input_sha256", {}).get(str(path)) != state["input_sha256"][str(path)] for path in required):
            raise ValueError("adapter input snapshot differs")
    elif phase in ("precision", "strata", "comparisons"):
        if report.get("conditions") != 352: raise ValueError("missing report conditions")
        if phase == "precision" and report.get("replicates") != 192: raise ValueError("partial precision cohort")
        if phase == "strata" and report.get("primary_summaries_reproduced") is not True: raise ValueError("strata primary not reproduced")
    elif phase == "weight":
        if report.get("conditions") != 48 or len(report.get("analysis_metadata", [])) != 768:
            raise ValueError("partial weight cohort")
    if phase in ("comparisons", "strata") and report.get("analysis") != state["analysis_context"]:
        raise ValueError("downstream context differs")
    if phase == "comparisons" and report.get("rows_sha256") != state["rows_sha256"]:
        raise ValueError("comparison rows differ")
    if phase == "strata" and report.get("raw_rows_sha256") != state["rows_sha256"]:
        raise ValueError("strata rows differ")
    if phase in ("precision", "weight"):
        paths = dict(sampling="manifest.json", analysis="analysis_manifest.json", reference="reference_summary.json")
        for label, name in paths.items():
            expected = state["input_sha256"][str(Path(plan["production_root"]) / name)]
            if report.get("input_sha256", {}).get(label) != expected: raise ValueError("downstream input differs")


def run_phase(root, phase):
    """Internal child process: one original API call and one resource record."""
    root = Path(root).resolve()
    started, cpu = time.perf_counter(), time.process_time()
    record = dict(phase=phase, status="failed", pbs_job_id=os.environ.get("PBS_JOBID"))
    output = root / "phases" / (phase + ".json")
    measurement = root / "phases" / (phase + ".measurement.json")
    if output.exists() or measurement.exists(): raise ValueError("existing phase; never retry")
    try:
        plan = read_plan(root)
        execution_binding(root, plan)
        if phase not in plan["phases"] or not (root / "execution-intent.json").is_file():
            raise ValueError("unplanned phase or missing execution intent")
        request = read_json(root / "phases" / (phase + ".request.json"))
        if request != dict(phase=phase, manifest=c.digest(plan), pbs_job_id=os.environ.get("PBS_JOBID")):
            raise ValueError("phase request binding differs")
        for previous in plan["phases"][:plan["phases"].index(phase)]:
            outcome = read_json(root / "phases" / (previous + ".outcome.json"))
            if outcome["status"] != "ok" or outcome["output_sha256"] != c.file_hash(root / "phases" / (previous + ".json")):
                raise ValueError("preceding phase is not complete and unchanged")
        record["manifest"] = c.digest(plan)
        source, case = Path(plan["production_root"]), plan["case"]
        if phase != "audited":
            adapter = root / "phases/audited.json"
            validate_report(plan, "audited", read_json(adapter))
            record["adapter_sha256"] = c.file_hash(adapter)
        if phase == "audited":
            report = audited.read_results(source, plan["audit_root"], case, **plan["evidence"])
            c.atomic_json(output, report)
        elif phase == "precision":
            report = precision.assess_calibration(source, case)
            c.atomic_json(output, report)
        elif phase == "weight": report = weight.run(source, case, plan["evidence"]["reference_audit"], output)
        else: report = MODULES[phase].run(source, case, output)
        validate_report(plan, phase, report)
        if c.digest(read_plan(root)) != record["manifest"]: raise ValueError("phase input changed")
        record.update(status="ok", output_sha256=c.file_hash(output))
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu,
                  peak_rss_mb=c.peak_rss_mb())
    with measurement.open("xb") as stream: stream.write(c.canonical(record) + b"\n")
    if record["status"] != "ok": raise RuntimeError("phase failed; measurement retained")
    return record


def run(root, *, runner=subprocess.run):
    root = Path(root).resolve()
    if (not re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", os.environ.get("PBS_JOBID", ""))
            or any(os.environ.get(key) != value for key, value in THREADS.items())):
        raise ValueError("qsub and pinned single-thread environment required")
    if any((root / name).exists() or (root / name).is_symlink() for name in ("execution-intent.json", "phases", "summary.json")):
        raise ValueError("existing execution; never retry automatically")
    plan = read_plan(root)
    binding = execution_binding(root, plan)
    intent = dict(manifest=c.digest(plan), pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname(),
                  submission_binding=binding, resource=resources())
    with (root / "execution-intent.json").open("xb") as stream: stream.write(c.canonical(intent) + b"\n")
    (root / "phases").mkdir()
    started = time.perf_counter()
    records, phase_failure, stats = [], None, None
    for phase in plan["phases"]:
        record = dict(phase=phase, status="not_run_dependency")
        if phase_failure is None:
            phase_start = time.perf_counter()
            record["status"] = "failed"
            try:
                read_plan(root)
                current = analysis_stats(plan)
                if stats is None: stats = current
                elif current != stats: raise ValueError("analysis snapshot changed between phases")
                command = [sys.executable, str(Path(__file__).resolve()), "phase", "--root", str(root), "--phase", phase]
                with (root / "phases" / (phase + ".request.json")).open("xb") as stream:
                    stream.write(c.canonical(dict(phase=phase, manifest=c.digest(plan), pbs_job_id=intent["pbs_job_id"])) + b"\n")
                with (root / "phases" / (phase + ".out")).open("x") as out, (root / "phases" / (phase + ".err")).open("x") as err:
                    result = runner(command, stdout=out, stderr=err, text=True, timeout=max(1, resources()["wall_seconds"] - (time.perf_counter() - started)))
                record.update(command=command, returncode=result.returncode)
                if result.returncode: raise RuntimeError("phase returned nonzero")
                measurement_path = root / "phases" / (phase + ".measurement.json")
                measurement = read_json(measurement_path)
                output = root / "phases" / (phase + ".json")
                if (measurement["phase"] != phase or measurement["status"] != "ok" or measurement["manifest"] != c.digest(plan)
                        or measurement["pbs_job_id"] != intent["pbs_job_id"] or measurement["output_sha256"] != c.file_hash(output)):
                    raise ValueError("phase measurement/output binding differs")
                for name in ("wall_seconds", "cpu_seconds", "peak_rss_mb"):
                    value = measurement.get(name)
                    if value is None or not math.isfinite(value) or value < 0 or (name != "cpu_seconds" and value == 0):
                        raise ValueError("invalid resource measurement: " + name)
                validate_report(plan, phase, read_json(output))
                if c.digest(read_plan(root)) != c.digest(plan): raise ValueError("phase input changed")
                record.update(status="ok", measurement=measurement, measurement_sha256=c.file_hash(measurement_path),
                              output_sha256=c.file_hash(output))
            except Exception as error:
                phase_failure = repr(error)
                record.update(error=phase_failure, traceback=traceback.format_exc())
            record["subprocess_wall_seconds"] = time.perf_counter() - phase_start
        records.append(record)
        c.atomic_json(root / "phases" / (phase + ".outcome.json"), record)
    terminal_error = None
    try:
        if c.digest(read_plan(root)) != c.digest(plan) or execution_binding(root, plan) != binding:
            raise ValueError("terminal input/submission binding differs")
        if stats is not None and analysis_stats(plan) != stats: raise ValueError("terminal analysis snapshot changed")
        for record in records:
            if record["status"] == "ok":
                phase = record["phase"]
                if (c.file_hash(root / "phases" / (phase + ".json")) != record["output_sha256"]
                        or c.file_hash(root / "phases" / (phase + ".measurement.json")) != record["measurement_sha256"]):
                    raise ValueError("completed output changed")
    except Exception as error: terminal_error = repr(error)
    summary = dict(**intent, case=plan["case"], replicates=192, groups=768, records=records,
                   complete=phase_failure is None and terminal_error is None, terminal_binding_valid=terminal_error is None,
                   phase_failure=phase_failure, terminal_failure=terminal_error, phase_wall_seconds=time.perf_counter() - started,
                   input_snapshot=c.digest(plan["snapshot"]), execution_intent_sha256=c.file_hash(root / "execution-intent.json"), warning=WARNING)
    c.atomic_json(root / "summary.json", summary)
    if not summary["complete"]: raise RuntimeError("reaggregation incomplete; outcomes retained, no automatic rerun")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "phase"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--phase", choices=tuple(MODULES))
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.root, **read_json(args.config))
    elif args.command == "phase": result = run_phase(args.root, args.phase)
    else: result = run(args.root)
    print(json.dumps({key: value for key, value in result.items() if key in ("purpose", "case", "phase", "status", "complete")}))


if __name__ == "__main__": main()
