"""Bind saved final calibration reports to the unchanged timing candidate policy."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import shlex

import calibration as c
import tile_select_timing as selector

PHASE_SOURCES = dict(audited="tile_audited_results.py", comparisons="tile_comparisons.py",
                     precision="tile_precision_assessment.py", weight="tile_weight_comparison.py",
                     strata="tile_initialization_strata.py")
WARNING = ("Selection reuses externally pinned recovered final reports and the unchanged candidate policy. "
           "The external recovery hash must come from accepted independent collection, not this reader. "
           "No raw-row reanalysis, bootstrap rerun, fresh native probe, full-state decoding, historical consumed-input proof, "
           "population precision, nominal coverage, fastest-setting or recommendation guarantee is added.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_case(item, guards):
    case = item["case"]
    require(type(case) is int and case in range(4), "invalid case")
    root = Path(item["recovered_root"]).resolve()
    pin = item["recovery_sha256"]
    require(isinstance(pin, str) and re.fullmatch(r"[0-9a-f]{64}", pin), "external recovery hash required")
    proof_path = root / "recovery.json"
    require(c.file_hash(proof_path) == pin, "recovery differs from external pin")
    guards[proof_path] = pin
    proof = json.loads(proof_path.read_text())
    require(proof["problems"] == [], "recovery reported problems")
    members, originals = {}, {}
    for original, record in proof["files"].items():
        member = record["member"]
        relative = PurePosixPath(member)
        path = root / member
        require(not relative.is_absolute() and ".." not in relative.parts and "\\" not in member
                and path.resolve().is_relative_to(root) and member not in members,
                "unsafe or duplicate recovery member")
        require(PurePosixPath(original).is_absolute(), "original path must be absolute")
        actual = c.file_hash(path)
        require(actual == record["sha256"] and record.get("expected_sha256", actual) == actual,
                "recovered payload hash differs")
        guards[path] = actual
        members[member] = (original, path, actual)
        originals[original] = (member, path, actual)
    require({path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
            == set(members) | {"recovery.json"}, "unexpected or missing recovery files")
    def read(member):
        require(member in members, "missing recovered member: " + member)
        return json.loads(members[member][1].read_text())
    def sha(member):
        require(member in members, "missing recovered member: " + member)
        return members[member][2]
    plan, summary = read("run/manifest.json"), read("run/summary.json")
    state = plan["snapshot"]
    production = state["production"]
    expected_phases = ["audited", "comparisons", "precision", "weight"] + (["strata"] if case > 1 else [])
    require(plan["schema"] == 1 and plan["purpose"] == "final_calibration_reaggregation"
            and plan["case"] == case and plan["replicates"] == 192 and plan["groups"] == 768
            and plan["phases"] == expected_phases, "fixed final manifest differs")
    current = selector.b.make_plan()
    require(c.canonical({k:v for k,v in production.items() if k != "runtime"})
            == c.canonical({k:v for k,v in current.items() if k != "runtime"}), "fixed production grid differs")
    require(c.digest(production) == state["sampling_manifest"], "sampling manifest differs")
    for original, digest in state["input_sha256"].items():
        require(original in originals and originals[original][2] == digest, "saved input binding differs")
    production_root = PurePosixPath(plan["production_root"])
    def saved_input(name):
        original = str(production_root / name)
        require(original in originals, "missing production input")
        return json.loads(originals[original][1].read_text())
    require(c.canonical(saved_input("manifest.json")) == c.canonical(production), "production input differs")
    context = saved_input("analysis_manifest.json")
    require(c.digest(context) == state["analysis_context"] and context["sampling_manifest"] == state["sampling_manifest"]
            and context["reference_summary_sha256"] == state["input_sha256"][str(production_root / "reference_summary.json")],
            "analysis/reference input differs")
    for name, digest in state["source_sha256"].items():
        require(PurePosixPath(name).name == name and "\\" not in name, "unsafe source name")
        require(sha("sources/" + name) == digest, "saved source binding differs")
        source = Path(__file__).parent / name
        require(c.file_hash(source) == digest, "current source differs: " + name)
        guards[source] = digest
    source_names = {*PHASE_SOURCES.values(), "tile_summary.py", "tile_final_reaggregation.py"}
    require(source_names <= set(state["source_sha256"]), "source closure missing required modules")
    manifest = c.digest(plan)
    job = proof["job_id"]
    require(re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?", job), "invalid job identity")
    ledger, intent = read("run/submission.json"), read("run/submission-intent.json")
    script_original = members["run/reaggregate.sh"][0]
    require(ledger["job_id"] == job and ledger["manifest"] == manifest
            and {key:value for key,value in ledger.items() if key != "job_id"} == intent
            and ledger["command"] == ["qsub", script_original]
            and ledger["script_sha256"] == sha("run/reaggregate.sh"), "submission binding differs")
    pbs = proof["pbs"]
    require(proof["manifest"] == manifest and pbs["job_state"] == "F" and pbs["Exit_status"] == 0
            and shlex.split(pbs["Submit_arguments"]) == [script_original], "successful PBS/script binding required")
    execution = read("run/execution-intent.json")
    require(execution["manifest"] == manifest and execution["pbs_job_id"] == job
            and summary["execution_intent_sha256"] == sha("run/execution-intent.json"), "execution binding differs")
    require(summary["case"] == case and summary["replicates"] == 192 and summary["groups"] == 768
            and summary["manifest"] == manifest and summary["pbs_job_id"] == job
            and summary["complete"] is True and summary["terminal_binding_valid"] is True
            and summary["phase_failure"] is None and summary["terminal_failure"] is None
            and summary["input_snapshot"] == c.digest(state)
            and [row["phase"] for row in summary["records"]] == expected_phases, "complete final summary required")
    reports = {}
    for phase, outcome in zip(expected_phases, summary["records"]):
        stem = "run/phases/" + phase
        report, measurement = read(stem + ".json"), read(stem + ".measurement.json")
        require(outcome == read(stem + ".outcome.json") and outcome["status"] == "ok" and outcome["returncode"] == 0
                and outcome["output_sha256"] == sha(stem + ".json")
                and outcome["measurement_sha256"] == sha(stem + ".measurement.json")
                and outcome["measurement"] == measurement, "phase outcome binding differs")
        require(measurement["phase"] == phase and measurement["status"] == "ok"
                and measurement["manifest"] == manifest and measurement["pbs_job_id"] == job
                and measurement["output_sha256"] == sha(stem + ".json")
                and read(stem + ".request.json") == dict(phase=phase,manifest=manifest,pbs_job_id=job),
                "phase request/measurement binding differs")
        if phase != "audited":
            require(measurement["adapter_sha256"] == sha("run/phases/audited.json"), "phase audit differs")
        require(report["case"] == case and report["source_sha256"] == sha("sources/" + PHASE_SOURCES[phase]),
                "phase case/source differs")
        reports[phase] = report
    audited, precision = reports["audited"], reports["precision"]
    require(audited["purpose"] == "audited_calibration_results" and audited["schema"] == 1
            and audited["replicates"] == 192 and audited["groups"] == 768 and audited["conditions"] == 352
            and audited["sampling_manifest"] == state["sampling_manifest"]
            and audited["analysis_context"] == state["analysis_context"]
            and audited["trace_audit_manifest"] == state["trace_audit_manifest"]
            and audited["current_archived_inputs_match_audited_inputs"] is True
            and audited["terminal_payload_stat_checked"] is True, "full audited report required")
    require(all(audited[name] is False for name in ("historical_consumed_input_hashes_recorded", "bar_bootstrap_recomputed",
                                                   "all_physical_states_redecoded")), "audit scope differs")
    require(precision["schema"] == 1 and precision["purpose"] == "empirical_relative_precision_assessment"
            and precision["replicates"] == 192 and precision["conditions"] == 352
            and precision["summary_source_sha256"] == sha("sources/tile_summary.py"), "full precision report required")
    for label, name in dict(sampling="manifest.json", analysis="analysis_manifest.json", reference="reference_summary.json",
                            summary=f"summary-{case}.json").items():
        require(precision["input_sha256"][label] == state["input_sha256"][str(production_root/name)],
                "precision input binding differs")
    require(precision["input_sha256"]["rows"] == state["rows_sha256"], "precision raw-row hash differs")
    metrics = {tuple(row[key] for key in selector.s.CONDITION): {k:v for k,v in row.items() if k not in selector.s.CONDITION}
               for row in audited["records"]}
    require(len(metrics) == len(audited["records"]) == len(precision["records"]) == 352, "missing or duplicate audited conditions")
    seen = set()
    for row in precision["records"]:
        key = tuple(row["condition"][name] for name in selector.s.CONDITION)
        require(key not in seen and key in metrics and c.canonical(metrics[key]) == c.canonical(row["assessment"]["metrics"]),
                "precision metrics differ from audited condition")
        seen.add(key)
    evidence = dict(case=case, recovery_sha256=pin, final_manifest_sha256=sha("run/manifest.json"),
                    final_summary_sha256=sha("run/summary.json"), audited_sha256=sha("run/phases/audited.json"),
                    precision_sha256=sha("run/phases/precision.json"), pbs_job_id=job,
                    analysis_context=state["analysis_context"], reference_sha256=precision["input_sha256"]["reference"])
    return production, precision, evidence


def run(cases, output):
    output = Path(output)
    require(not output.exists(), "selection output exists")
    require(len(cases) == 4 and sorted(item["case"] for item in cases) == list(range(4)), "all four distinct cases required")
    guards = {Path(__file__): c.file_hash(__file__), Path(selector.__file__): c.file_hash(selector.__file__)}
    loaded = [read_case(item, guards) for item in sorted(cases, key=lambda item:item["case"])]
    production = loaded[0][0]
    require(all(c.canonical(row[0]) == c.canonical(production) for row in loaded), "production differs across cases")
    evidence = [row[2] for row in loaded]
    require(len({row["analysis_context"] for row in evidence}) == len({row["reference_sha256"] for row in evidence}) == 1,
            "analysis/reference differs across cases")
    result = selector.choose(production, [row[1] for row in loaded])
    extra = {value for row in evidence for key,value in row.items() if key.endswith("sha256")}
    extra.add(c.file_hash(__file__))
    result["selection_evidence_sha256"] = sorted(set(result["selection_evidence_sha256"]) | extra)
    result.update(final_audit_evidence=evidence, final_selection_adapter_sha256=c.file_hash(__file__),
                  raw_rows_recomputed=False, fresh_native_probe_executed=False, historical_consumed_input_hashes_recorded=False,
                  final_evidence_scope=WARNING)
    require(all(c.file_hash(path) == digest for path,digest in guards.items()), "inputs/source changed during selection")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(c.canonical(result) + b"\n")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(json.loads(args.config.read_text()),args.output)
    print(json.dumps(dict(outcomes=[{k:row[k] for k in ("case","epsilon","status","eligible_conditions")} for row in result["records"]],warning=WARNING)))


if __name__ == "__main__":
    main()
