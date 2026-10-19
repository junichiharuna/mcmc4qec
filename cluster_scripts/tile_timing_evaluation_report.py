"""Report all eight independent timing outcomes without changing precision gates.

Config pins are {path, sha256}: settings, reference, reference_audit, seed_census,
and four selection_recoveries (case plus pin). Completed entries contain root,
proof, terminal and verification pins. BAR also needs transfer; MC needs
submission_output (saved qsub stdout, JSON-equal to the ledger). BAR has case.
Roots are authoritative read-only snapshots. Unprepared roots do not assert that
no remote job exists. prepare is metadata-only; run scans payloads on PBS only.
"""
import argparse
import ast
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import sys

import calibration as c
import tile_timing_comparison as comparison
import tile_timing_metrics as metrics
from tile_low_noise_audited_collection import Evidence

IDENTITIES = [(case, eps) for case in range(4) for eps in (.2, .1)]
COMPLETE = {"completed", "completed_with_recorded_task_failures"}
METADATA = ("manifest.json", "budget.json", "settings.json", "platform_profile.json", "platform_fixture.json",
            "execution_intent.json", "native_preflight.json", "submission.json", "submission_intent.json",
            "timing.sh", "summary.json")
WARNING = (metrics.WARNING + " Selection diagnostics and independent evaluation diagnostics are separate. "
           "BAR flagged/undefined placeholders are not measured R-hat/ESS failures. The finite 99.9% reference "
           "is shared by selection, budgeting and evaluation, not a simultaneous guarantee. Low-noise "
           "independent timing remains unevaluated. No state re-decoding or native-probe replay is performed.")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source_files():
    """Include local static imports and installed package Python implementation."""
    directory = Path(__file__).resolve().parent
    pending = [Path(__file__).name, "submit_tile_mc_time.py", "submit_tile_bar_time.py"]
    found = {}
    while pending:
        name = pending.pop()
        if name in found:
            continue
        path = directory / name
        found[name] = path
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            names = ([a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import)
                     else [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            pending.extend(m + ".py" for m in names if (directory / (m + ".py")).is_file())
    package = Path(c.qec.__file__).resolve().parent
    found.update({"package/" + p.relative_to(package).as_posix(): p for p in package.rglob("*.py")})
    return found


def sources(proof):
    return {name: proof.track(path) for name, path in source_files().items()}


def runtime():
    from importlib.metadata import version
    return dict(**c.runtime(), scipy=version("scipy"), python_binary_sha256=c.file_hash(sys.executable))


def read_pin(pin, proof):
    require(isinstance(pin, dict) and isinstance(pin.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]), "external SHA256 pin required")
    require(proof.track(pin["path"]) == pin["sha256"], "external input pin differs")
    return proof.read(pin["path"])


def root_state(root):
    root = Path(root)
    if not root.exists():
        return "not_prepared"
    require(root.is_dir(), "cohort root must be a directory")
    if (root / "summary.json").exists():
        return "complete_candidate"
    if any((root / name).exists() for name in ("execution_intent.json", "native_preflight.json", "submission.json",
                                              "submission_intent.json", "tasks")):
        return "incomplete"
    return "not_started" if (root / "manifest.json").exists() else "not_prepared"


def task_census(root):
    root = Path(root).absolute()
    path = root / "tasks"
    return dict(root=str(root), target=str(root.resolve()), task_target=str(path.resolve()),
                entries={p.name: dict(target=str(p.resolve()), is_file=p.is_file()) for p in path.iterdir()})


def accepted_inventory(item, method, plan, proof):
    """Follow externally accepted proof hashes to the original complete byte table."""
    require(all(key in item for key in ("proof", "verification")), "accepted artifact inventory pin required")
    accepted = read_pin(item["proof"], proof)
    verified = read_pin(item["verification"], proof)
    field = "benchmark_verification_sha256" if method == "mc" else "verification_sha256"
    require(accepted.get(field) == item["verification"]["sha256"], "accepted verification binding differs")
    require(verified["main_manifest"] == c.digest(plan) and verified["compute_native_profile_validated"] is True,
            "accepted manifest/native verification differs")
    if method == "bar":
        require("transfer" in item, "accepted transfer pin required")
        transferred = read_pin(item["transfer"], proof)
        require(accepted["transfer_sha256"] == item["transfer"]["sha256"]
                and transferred["all_files_sha256_match"] is True and transferred["all_artifacts_verified"] is True
                and transferred["validation_errors"] == [] and verified["validation_errors"] == []
                and verified["all_artifacts_verified"] is True and verified["receipt_verified"] is True
                and verified["source_input_binding_verified"] is True and verified["job_id"] == accepted["job_id"],
                "accepted BAR transfer/verification differs")
    else:
        require("submission_output" in item, "saved MC submission stdout pin required")
        submission = read_pin(item["submission_output"], proof)
        require(accepted["submission_sha256"] == item["submission_output"]["sha256"]
                and submission == proof.read(Path(item["root"]) / "submission.json")
                and verified["full_task_artifacts_metadata_verified"] is True
                and verified["job_id"] == submission["job_id"], "accepted MC stdout/ledger binding differs")
    inventory = verified["file_sha256"]
    require(isinstance(inventory, dict) and bool(inventory), "nonempty accepted byte inventory required")
    for name, digest in inventory.items():
        relative = PurePosixPath(name)
        require(isinstance(name, str) and not relative.is_absolute() and ".." not in relative.parts
                and "\\" not in name and relative.as_posix() == name
                and isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "unsafe accepted inventory entry")
    if method == "bar":
        require(transferred["files"] == len(inventory), "accepted transfer census differs")
    else:
        require(accepted["files"] == len(inventory), "accepted MC transfer census differs")
    return inventory, accepted


def metadata_snapshot(item, method, case, settings, proof):
    root = Path(item["root"]).absolute()
    state = root_state(root)
    files = {name: proof.track(root / name) for name in METADATA if (root / name).exists()}
    driver = comparison.mc if method == "mc" else comparison.bar
    source = proof.read(root / "budget.json") if method == "mc" else settings
    plan = driver.make_plan(source, capacity=False, **({"case": case} if method == "bar" else {}))
    if "manifest.json" in files:
        require(proof.read(root / "manifest.json") == plan, "fixed timing manifest/runtime differs")
    if "settings.json" in files:
        require(proof.read(root / "settings.json") == settings, "timing selection differs")
    if state == "complete_candidate":
        require("proof" in item and "terminal" in item, "complete candidate needs external recovery and terminal pins")
        read_pin(item["proof"], proof)
        read_pin(item["terminal"], proof)
        accepted_inventory(item, method, plan, proof)
    return dict(root=str(root), resolved_root=str(root.resolve()), state=state, files=files, manifest=plan)


def inputs(config, proof):
    settings = read_pin(config["settings"], proof)
    require([(r["case"], r["epsilon"]) for r in settings["records"]] == IDENTITIES,
            "all eight ordered selection identities required")
    recovery = config["selection_recoveries"]
    require([r["case"] for r in recovery] == list(range(4)), "four ordered externally pinned selection recoveries required")
    expected = {r["case"]: r for r in settings["final_audit_evidence"]}
    for pin in recovery:
        value = read_pin(pin, proof)
        require(pin["sha256"] == expected[pin["case"]]["recovery_sha256"] and value["problems"] == [],
                "selection recovery binding differs")
    reference = read_pin(config["reference"], proof)
    audit = read_pin(config["reference_audit"], proof)
    require(audit["summary_sha256"] == config["reference"]["sha256"] and all(audit.get(k) is True for k in
            ("all_seeds_verified", "all_problem_metadata_verified", "summary_reproduced")), "reference audit differs")
    require([row["case"] for row in reference["records"]] == list(range(4)), "four reference cases required")
    for case in range(4):
        require(expected[case]["reference_sha256"] == config["reference"]["sha256"], "selection and evaluation reference differ")
    census = read_pin(config["seed_census"], proof)
    require(census["planned_entries"] == census["checked_entries"] > 0 and census["unchecked_entries"] == 0
            and census["unexpected_collisions"] == 0 and census["namespace_count"] >= 56
            and census["stages_140_141_all_planned_cases_checked"] is True
            and census["source_runtime_input_bindings_verified"] is True
            and census["submission_completion_pbs_verified"] is True, "complete accepted timing seed census required")
    require([item["case"] for item in config["bar"]] == list(range(4)), "all four ordered BAR roots required")
    roots = [Path(item["root"]).resolve() for item in [config["mc"], *config["bar"]]]
    require(len(set(roots)) == 5 and all(not a.is_relative_to(b) for a in roots for b in roots if a != b),
            "cohort roots must be distinct and disjoint")
    snapshots = {"mc": metadata_snapshot(config["mc"], "mc", 0, settings, proof),
                 "bar": [metadata_snapshot(item, "bar", item["case"], settings, proof) for item in config["bar"]]}
    return settings, {r["case"]: r for r in reference["records"]}, audit, snapshots


def prepare(config_path, output_plan):
    output_plan = Path(output_plan)
    require(not output_plan.exists(), "preserve existing report plan")
    proof = Evidence()
    config = proof.read(config_path)
    require(all(not output_plan.resolve().is_relative_to(Path(item["root"]).resolve())
                for item in [config["mc"], *config["bar"]]), "report plan must be outside cohort roots")
    src = sources(proof)
    _, _, _, snapshots = inputs(config, proof)
    result = dict(schema=1, purpose="main_timing_evaluation_report", config=config, snapshots=snapshots,
                  source_sha256=src, runtime=runtime(), input_sha256=proof.hashes, input_targets=proof.targets)
    proof.finish()
    output_plan.parent.mkdir(parents=True, exist_ok=True)
    with output_plan.open("xb") as stream:
        stream.write(c.canonical(result) + b"\n")
    return result


def execution_evidence(item, plan, summary, proof):
    root = Path(item["root"])
    ledger = proof.read(root / "submission.json")
    intent = proof.read(root / "submission_intent.json")
    execution = proof.read(root / "execution_intent.json")
    native = proof.read(root / "native_preflight.json")
    terminal = read_pin(item["terminal"], proof)
    job = ledger["job_id"]
    pbs = terminal.get("Jobs", {}).get(job) if "Jobs" in terminal else terminal.get("job")
    require(isinstance(pbs, dict) and ("Jobs" in terminal or terminal.get("job_id") == job), "terminal job differs")
    command = ledger["command"]
    require(isinstance(command, list) and len(command) == 2 and command[0] == "qsub"
            and shlex.split(pbs["Submit_arguments"]) == command[1:] and pbs["job_state"] == "F", "formal terminal/script binding differs")
    require({k: v for k, v in ledger.items() if k != "job_id"} == intent
            and ledger["script_sha256"] == proof.track(root / "timing.sh")
            and ledger["manifest"] == c.digest(plan), "submission binding differs")
    require(execution["manifest"] == native["manifest"] == c.digest(plan)
            and execution["pbs_job_id"] == native["pbs_job_id"] == job, "native/execution job binding differs")
    hosts = {part.split("/")[0] for part in pbs["exec_host"].split("+")}
    require(hosts == {native["hostname"]}, "PBS/native host differs")
    resource, actual = ledger["resource"], pbs["Resource_List"]
    require(resource["requested_nodes"] == 1 and resource["max_nodes"] == 2
            and actual.get("select") == f"1:ncpus={resource['cpus']}:mem={resource['memory_gb']}gb"
            and actual.get("ncpus") == resource["cpus"] and actual.get("mem") == f"{resource['memory_gb']}gb"
            and actual.get("walltime") == resource["walltime"], "PBS resource differs")
    code = pbs["Exit_status"]
    # Both frozen drivers raise RuntimeError (exit 1) after retaining task failures.
    # Kills, timeouts and argparse exits are not classified as recorded failure completion.
    require(type(code) is int and ((code == 0 and summary["failed"] == 0) or (code == 1 and summary["failed"] > 0)),
            "terminal and complete task outcomes contradict")
    return dict(status="completed" if code == 0 else "completed_with_recorded_task_failures", job_id=job,
                hostname=native["hostname"], resource=resource, pbs_resources=actual, pbs_resources_used=pbs.get("resources_used", {}),
                native_profile=native.get("profile"), cpu_model="unknown", frequency="unknown", affinity="unknown",
                numa="unknown", concurrent_load="unknown", hardware_equivalence_certified=False)


def load_complete(item, method, case, snapshot, audit, proof):
    root = Path(item["root"])
    plan = snapshot["manifest"]
    driver = comparison.mc if method == "mc" else comparison.bar
    tasks = list(driver.tasks(plan))
    require(tasks, "complete timing job cannot have no selected tasks")
    expected_files = {c.task_id(task) + ext for task in tasks for ext in (".json", ".npz", ".done.json")}
    census = task_census(root)
    require(set(census["entries"]) == expected_files and all(v["is_file"] for v in census["entries"].values()),
            "task payload census differs")
    inventory, recovered = accepted_inventory(item, method, plan, proof)
    require({name[6:] for name in inventory if name.startswith("tasks/")} == expected_files,
            "accepted task census differs")
    require({p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} == set(inventory),
            "accepted root file census differs")
    for name, digest in inventory.items():
        path = root / name
        require(path.resolve().is_relative_to(root.resolve()) and proof.track(path) == digest,
                "accepted artifact bytes differ")
    # Track before the old reader opens payloads; finish rehashes all bytes and targets.
    for name in sorted(expected_files):
        path = root / "tasks" / name
        require(path.resolve().is_relative_to(root.resolve()), "payload escapes cohort root")
        proof.track(path)
    loaded = comparison.load_cohort(root, method, case)
    require(loaded["plan"] == plan, "loaded plan differs from fixed snapshot")
    for path, digest in loaded["guards"].items():
        require(proof.track(path) == digest, "cohort changed during loading")
    require(all(audit["model_hashes"].get(k) == v for k, v in loaded["models"].items()), "timing/reference model differs")
    summary = proof.read(root / "summary.json")
    require(recovered["summary_sha256"] == proof.track(root / "summary.json"), "external recovery summary differs")
    execution = execution_evidence(item, plan, summary, proof)
    if method == "mc":
        require(recovered["all_files_sha256_match"] is True
                and recovered["native_preflight_sha256"] == proof.track(root / "native_preflight.json")
                and recovered["terminal_sha256"] == item["terminal"]["sha256"], "MC recovery binding differs")
    else:
        require(recovered["mode"] == "main" and recovered["case"] == case
                and recovered["job_id"] == execution["job_id"] and recovered["tasks"] == len(tasks)
                and recovered["failed"] == summary["failed"] and recovered["fixed_prior_rng_and_saved_shape_checked"] is True,
                "BAR recovery binding differs")
    submit_path = Path(__file__).parent / ("submit_tile_mc_time.py" if method == "mc" else "submit_tile_bar_time.py")
    require(proof.read(root / "submission.json")["submit_source_sha256"] == proof.track(submit_path),
            "accepted submit source differs")
    return dict(status=execution["status"], records=loaded["records"], execution=execution,
                phase_wall_seconds=loaded["phase_wall_seconds"],
                task_census=census, accepted_file_census=sorted(inventory),
                phase_scope="all_eight_conditions" if method == "mc" else "selected_conditions_for_case")


def assess_rows(selection, references, mc, bars):
    require([(r["case"], r["epsilon"]) for r in selection["records"]] == IDENTITIES, "eight selection identities required")
    results = []
    for chosen in selection["records"]:
        case, epsilon = chosen["case"], chosen["epsilon"]
        cohorts = {"mc": mc, "bar": bars[case]}
        rows, assessed = {}, {}
        for method, cohort in cohorts.items():
            rows[method] = [r for r in cohort["records"] if r["case"] == case and r["epsilon"] == epsilon]
            complete = cohort["status"] in COMPLETE
            assessed[method] = dict(status=cohort["status"], planned_replicates=192,
                observed_tasks=len(rows[method]) if complete else None,
                assessment=metrics.assess(method, rows[method], 192, references[case], epsilon) if complete else None)
        compared = None
        reason = "selection_unmet" if chosen["status"] == "unmet" else "independent_cohort_incomplete"
        ratios = {clock: dict(value=None, reason=reason) for clock in ("task_wall_seconds", "cpu_seconds")}
        if chosen["status"] == "selected" and all(cohorts[m]["status"] in COMPLETE for m in cohorts):
            compared = metrics.compare(rows["mc"], rows["bar"], 192, references[case], epsilon)
            ratios = compared["ratios_mc_over_bar"]
        results.append(dict(case=case, epsilon=epsilon, target_p=references[case]["target_p"], planned_replicates=192,
            selection=chosen, mc=assessed["mc"], bar=assessed["bar"], comparison=compared, ratios_mc_over_bar=ratios,
            diagnostic_observation=dict(mc="not_applicable", bar="not_collected"),
            bar_internal_flagged_undefined_are_unobserved_placeholders=True))
    return results


def report_text(report):
    lines = ["# main 独立計時の達成精度と費用", "", "全8条件・各192 replicateを保持する。",
             "校正時の診断と独立BARの診断未取得を区別し、内部flagを実測R-hat/ESS失敗数にしない。",
             "有限reference全域の経験的RMSEを両手法が満たす場合だけ平均task費用比を表示する。", "",
             "|case|epsilon|MC状態/精度|BAR状態/精度|wall比|CPU比|", "|---|---:|---|---|---:|---:|"]
    for row in report["records"]:
        labels = []
        for method in ("mc", "bar"):
            value = row[method]
            label = value["assessment"]["precision"]["precision"][0]["classification"] if value["assessment"] else "未評価"
            labels.append(value["status"] + "/" + label)
        values = [str(row["ratios_mc_over_bar"][k]["value"]) for k in ("task_wall_seconds", "cpu_seconds")]
        lines.append(f"|{row['case']}|{row['epsilon']}|{labels[0]}|{labels[1]}|{values[0]}|{values[1]}|")
    lines += ["", "費用比は記録環境での未補正の記述量であり、母精度・母時間比・最速設定・名目被覆を保証しない。",
              "pool経過時間の条件別按分は行わず、task wall・process CPU・job/PBS wallを分ける。",
              "低ノイズの独立計時は未評価であり、mainの結果で完了扱いしない。", ""]
    return "\n".join(lines)


def run(plan_path, output_root):
    require(bool(os.environ.get("PBS_JOBID")), "full payload reporting requires PBS")
    output_root = Path(output_root).absolute()
    require(not output_root.exists(), "preserve existing report root")
    proof = Evidence()
    plan = proof.read(plan_path)
    require(plan["schema"] == 1 and plan["purpose"] == "main_timing_evaluation_report", "wrong report plan")
    require(sources(proof) == plan["source_sha256"] and runtime() == plan["runtime"], "report source/runtime changed")
    for path, digest in plan["input_sha256"].items():
        require(proof.track(path) == digest and str(Path(path).resolve()) == plan["input_targets"][path], "prepared input changed")
    config = plan["config"]
    settings, refs, audit, snapshots = inputs(config, proof)
    require(snapshots == plan["snapshots"], "cohort state changed; prepare a new report plan")
    roots = [Path(config["mc"]["root"]).resolve(), *[Path(v["root"]).resolve() for v in config["bar"]]]
    require(all(not output_root.resolve().is_relative_to(root) and not root.is_relative_to(output_root.resolve()) for root in roots),
            "report output overlaps cohort inputs")
    mc = None
    bars = {}
    for method, case, item, snapshot in [("mc", 0, config["mc"], snapshots["mc"]),
            *[("bar", i, item, snapshots["bar"][i]) for i, item in enumerate(config["bar"])]]:
        if snapshot["state"] == "complete_candidate":
            loaded = load_complete(item, method, case, snapshot, audit, proof)
        else:
            loaded = dict(status=snapshot["state"], records=[], execution={}, phase_wall_seconds=None,
                          phase_scope="unknown", observation_scope="authoritative_saved_root_only_not_live_scheduler")
        if method == "mc":
            mc = loaded
        else:
            bars[case] = loaded
    # Bind budget/selection references even before a BAR cohort is available.
    for cond in snapshots["mc"]["manifest"]["conditions"]:
        ref = refs[cond["case"]]
        require(cond["target_p"] == ref["target_p"] and cond["reference_point"] == ref["estimate"]
                and cond["reference_interval_999"] == ref["interval_999"], "MC budget/reference differs")
    result = dict(schema=1, purpose="main_independent_timing_evaluation", records=assess_rows(settings, refs, mc, bars),
        execution={"mc": {k:v for k,v in mc.items() if k != "records"},
                   "bar": {str(i): {k:v for k,v in row.items() if k != "records"} for i,row in bars.items()}},
        input_sha256=proof.hashes, input_targets=proof.targets, source_sha256=plan["source_sha256"], runtime=plan["runtime"],
        report_pbs_job_id=os.environ["PBS_JOBID"], complete_cohort_payloads_rehashed=True, incomplete_payloads_audited=False, native_probe_reexecuted=False,
        physical_states_redecoded=False, phase_time_apportioned=False, low_noise_independent_timing="unevaluated",
        warning=WARNING)
    try:
        require(inputs(config, proof)[3] == snapshots, "cohort state changed before publish")
        for cohort in [mc, *bars.values()]:
            if cohort["status"] not in COMPLETE:
                continue
            census = cohort["task_census"]
            root = Path(census["root"])
            require(task_census(root) == census, "task census changed before publish")
            require(sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
                    == cohort["accepted_file_census"], "accepted file census changed before publish")
        require(sources(proof) == plan["source_sha256"], "source closure changed before publish")
        proof.finish()
        require(runtime() == plan["runtime"], "runtime changed before publish")
    except Exception as exc:
        output_root.mkdir(parents=True, exist_ok=False)
        with (output_root / "validation_failure.json").open("xb") as stream:
            stream.write(c.canonical(dict(error=str(exc), success_report_published=False)) + b"\n")
        raise
    output_root.mkdir(parents=True, exist_ok=False)
    with (output_root / "report_ja.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(report_text(result))
    result["japanese_report_sha256"] = c.file_hash(output_root / "report_ja.md")
    with (output_root / "report.json").open("xb") as stream:
        stream.write(c.canonical(result) + b"\n")
    return result


def render(report_path, output_path, sha256):
    proof = Evidence()
    value = read_pin(dict(path=str(report_path), sha256=sha256), proof)
    require(value["purpose"] == "main_independent_timing_evaluation", "wrong report")
    text = report_text(value)
    proof.finish()
    with Path(output_path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p = sub.add_parser("render")
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.config, args.output)
    elif args.command == "run":
        run(args.plan, args.output_root)
    else:
        render(args.report, args.output, args.sha256)


if __name__ == "__main__":
    main()
