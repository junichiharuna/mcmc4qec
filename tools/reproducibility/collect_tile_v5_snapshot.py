"""Build the actual finite declaration census and snapshot it only in PBS."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

FLOW_SHA = "7c467ff93159574d9a98dd276df8431f2787b6577e83c2a3c9d6c15613ab86b1"
ENVELOPE_SHA = "25e2464484c67f9842fb9a68861bf70f85203e6db87e537491f13d20251c3b6a"
INITIAL_REQUEST_SHA = "b88a1e7391b5d3f8110696cbed9c2c191d6a77366c6b49de19b1105a13b3be7a"
INITIAL_ROLES_SHA = "b159a0c922a8ce53537e674f3369dab588fb4ced097083380cea5ab7885deff5"
FIXTURE_SHA = "2d9d10f6b3e6b27d927e3ce3a8f7afa2d1b55806517334f47f30bf2c7462852b"
LIBRARY_SHA = "053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a"
FLOW_SOURCE_SHA = "a202803df8ab82687697c16ae3f44d56d79a388842e863ca0caed9aed794e4ad"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bounded(path, limit=2097152):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "Metadata/bootstrap file exceeds explicit byte bound")
    return raw


def pin(path):
    return dict(path=str(path), sha256=hashlib.sha256(bounded(path)).hexdigest())


def read(pin):
    raw = bounded(pin["path"])
    require(hashlib.sha256(raw).hexdigest() == pin["sha256"], "Pinned metadata authority differs")
    return json.loads(raw)


def actual_request(work, stage, scan_references):
    remote = work / "20261024-c3t2-index-relocation-v1"
    initial = remote / "pipeline-submissions/reproduction-source-inventory-v1"
    initial_request_pin = dict(path=str(initial / "private-request.json"), sha256=INITIAL_REQUEST_SHA)
    initial_roles_pin = dict(path=str(initial / "private-explicit-roles.json"), sha256=INITIAL_ROLES_SHA)
    initial_request, roles = read(initial_request_pin), read(initial_roles_pin)
    declared = {}
    for seed in initial_request["seeds"]:
        require(seed["path"] not in declared or declared[seed["path"]] == seed["sha256"], "Initial request has conflicting source pins")
        declared[seed["path"]] = seed["sha256"]
    current = {path: declared[path] for path, rows in roles.items()
               if any(row["category"] == "current_runtime_source" for row in rows)}
    require(len(current) == 318, "Original current source declaration census differs")
    flow_pin = dict(path=str(work / "20261025-low-parallel-controller-v5/flow-config.json"), sha256=FLOW_SHA)
    flow = read(flow_pin)
    preparation = read(flow["worker_preparation"])
    manifest = read(preparation["manifest"])
    tail = read(flow["tail"]["config"])
    envelope_pin = dict(path=str(remote / "output/cluster_postprocess_pipeline_v1/controller-envelope.json"), sha256=ENVELOPE_SHA)
    envelope_doc = read(envelope_pin)
    require(len(envelope_doc["sources"]) == 1223, "Original frozen envelope denominator differs")
    envelope = []
    for relative, checksum in envelope_doc["sources"].items():
        path = remote / relative
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts, "Canonical relative envelope key required")
        envelope.append(dict(path=str(path), sha256=checksum,
                             category="source" if path.suffix == ".py" else "sealed_upstream_non_source"))
    sealed = {row["path"]: row["sha256"] for row in envelope if row["category"] == "source"}
    require(len(sealed) == 729 and len(set(current) & set(sealed)) == 31, "Source envelope/current overlap differs")
    sources = dict(current)
    for path, checksum in sealed.items():
        require(path not in sources or sources[path] == checksum, "Current/envelope original source pins conflict")
        sources[path] = checksum
    require(len(sources) == 1016, "Baseline exact source union differs")
    metadata = {}

    def add_metadata(p, category, relative_base=None):
        require(p["path"] not in metadata or metadata[p["path"]]["sha256"] == p["sha256"], "Current metadata authority conflict")
        value = read(p)
        metadata[p["path"]] = dict(p, category=category, relative_base=relative_base)
        return value

    for seed in initial_request["seeds"]:
        if Path(seed["path"]).suffix == ".json":
            add_metadata(dict(path=seed["path"], sha256=seed["sha256"]), "explicit_current_configuration_or_acceptance")
    add_metadata(initial_request_pin, "initial_current_source_scope_authority")
    add_metadata(initial_roles_pin, "initial_current_source_role_authority")
    add_metadata(envelope_pin, "original_sealed_envelope", str(remote))
    add_metadata(flow_pin, "actual_controller_configuration")
    add_metadata(flow["dispatch_policy"], "actual_dispatch_policy")
    # Include actual controller origin; flow-config itself does not pin its caller.
    native = remote / "pipeline-submissions/parallel-flow-native-v5"
    native_acceptance = add_metadata(pin(native / "accepted.json"), "actual_controller_native_acceptance_observed")
    launch = remote / "pipeline-state/parallel-flow-v5-launch"
    started = add_metadata(pin(launch / "started.json"), "actual_controller_launch_observed")
    require(native_acceptance["config"] == started["config"] == flow_pin
            and native_acceptance["flow"] == started["controller"]
            and native_acceptance["flow"]["sha256"] == FLOW_SOURCE_SHA,
            "Actual controller identity is not bound to this flow")
    supplements = []
    def add_source(p, reason):
        require(p["path"] not in sources or sources[p["path"]] == p["sha256"], "Supplemental current source pin conflict")
        if p["path"] not in sources:
            supplements.append(dict(p, reason=reason))
        sources[p["path"]] = p["sha256"]

    controller = native_acceptance["flow"]
    add_source(controller, "Actual controller entrypoint absent from flow-config helper map")
    for group in ("helpers", "worker_sources"):
        for key, descriptor in preparation[group].items():
            add_source(descriptor, "Actual preparation." + group + "." + key)
    policy = read(flow["dispatch_policy"])
    add_source(policy["capacity"], "Actual dispatch policy capacity verifier")
    # These fields are inputs to the currently selected merge validators, including
    # old/new source bytes needed to prove permitted operational transformations.
    for edge in scan_references(flow["merge_inputs"]):
        target = edge.get("target")
        if edge["kind"] == "pin" and isinstance(target, str) and Path(target).suffix in (".py", ".sh", ".pbs"):
            require(Path(target).is_absolute(), "Current merge source declaration must be absolute")
            add_source(dict(path=target, sha256=edge["sha256"]), "Current merge validation input " + edge["pointer"])
    for name in ("intent.json", "process.json"):
        add_metadata(pin(launch / name), "actual_controller_launch_observed")
    environments = []
    for p in (preparation["environment"], tail["parent_environment"], tail["report_environment"]):
        environments.append(add_metadata(p, "current_runtime_environment"))
    environments.extend(condition["reader_process"]["environment"] for condition in manifest["conditions"] if "reader_process" in condition)
    for rule in preparation.get("environment_rules", []):
        if "after" in rule:
            value = read(rule["after"])
            if any(value == environment for environment in environments):
                add_metadata(rule["after"], "current_reader_environment")
    external, resolved, bindings = {}, {}, []

    def add_external(path, checksum, category):
        require(path not in external or external[path]["sha256"] == checksum, "Current native declaration conflicts")
        external[path] = dict(path=path, sha256=checksum, category=category,
                              reason="Current runtime pin; content is not read or rehashed by preservation")

    for environment in environments:
        for path, checksum in environment["source_sha256"].items():
            require(sources.get(path) == checksum, "Environment source absent from exact current-plus-envelope scope")
        for path, target in environment["resolved_sources"].items():
            require(path not in resolved or resolved[path] == target, "Environment source alias authorities conflict")
            resolved[path] = target
        for path, checksum in environment["native_binding"].items():
            add_external(path, checksum, "native_binary")
        add_external(environment["python_path"], environment["python_sha256"], "python_executable")
        for module, origin in environment["import_origins"].items():
            if origin in environment["source_sha256"]:
                checksum = environment["source_sha256"][origin]
                target = environment["resolved_sources"][origin]
            else:
                require(origin in environment["native_binding"], "Unaccounted imported origin")
                checksum = environment["native_binding"][origin]
                target = str(Path(origin).resolve(strict=False))
            bindings.append(dict(module=module, origin=origin, resolved=target, sha256=checksum))
    worker_jobs = []
    for worker in preparation["workers"]:
        prepared = add_metadata(worker["prepared"], "actual_worker_prepared")
        for key in ("manifest", "resource_plan", "environment"):
            actual_value = add_metadata(prepared[key], "actual_worker_" + key)
            if key == "manifest":
                add_source(actual_value["engine_source"], "Actual worker manifest.engine_source")
        for key in ("runner", "evidence_reader"):
            add_source(prepared[key], "Actual worker prepared." + key)
        require(sources.get(worker["script"]["path"]) == worker["script"]["sha256"], "Actual worker script not in source scope")
        directory = Path(worker["script"]["path"]).parent
        ledger = add_metadata(pin(directory / "submission.json"), "actual_worker_submission_observed")
        add_metadata(pin(directory / "submission-intent.json"), "actual_worker_submission_intent_observed")
        add_metadata(pin(directory / "qsub-response.json"), "actual_worker_submission_response_observed")
        require(ledger["command"] == ["qsub", worker["script"]["path"]]
                and ledger["script_sha256"] == worker["script"]["sha256"], "Actual submission is not bound to original script")
        worker_jobs.append(dict(index=worker["index"], job_id=ledger["job_id"], prepared=worker["prepared"]))
    require([row["index"] for row in worker_jobs] == list(range(12)) and len({row["job_id"] for row in worker_jobs}) == 12,
            "Full twelve actual worker identities required")
    source_rows = [dict(path=path, sha256=checksum, resolved_path=resolved.get(path, path)) for path, checksum in sorted(sources.items())]
    request = dict(schema=2, roots=dict(workspace=str(work)), sources=source_rows,
                   metadata=sorted(metadata.values(), key=lambda row: row["path"]),
                   external=sorted(external.values(), key=lambda row: row["path"]), bindings=bindings,
                   envelope=envelope, expected_source_count=len(sources), expected_envelope_count=1223,
                   limits=dict(file_bytes=4194304, total_bytes=33554432), final_proofs_complete=False)
    authority = dict(schema=1, purpose="finite_snapshot_actual_scope_authority", flow=flow_pin, envelope=envelope_pin,
                     initial_request=initial_request_pin, initial_roles=initial_roles_pin,
                     current_sources=318, sealed_python_sources=729, overlapping_declaration_paths=31,
                     baseline_source_references=1016, supplemental_sources=supplements,
                     actual_source_references=len(sources), actual_worker_bindings=worker_jobs,
                     metadata_scope="Explicit listed current metadata only; all one-hop references indexed without recursion",
                     historical_closure_complete=False, scientific_reproduction_verified=False)
    return request, authority


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--self-sha256", required=True)
    args = parser.parse_args()
    require(os.environ.get("PBS_JOBID") and pin(Path(__file__))["sha256"] == args.self_sha256,
            "Pinned actual collection must run in PBS")
    work = Path.home() / "workspace/mcmc4qec"
    fixture = work / "20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-snapshot-v2-tests-v2"
    accepted = read(dict(path=str(fixture / "accepted.json"), sha256=FIXTURE_SHA))
    require(accepted["tests_passed"] == 25 and accepted["sources"]["snapshot_v2.py"]["sha256"] == LIBRARY_SHA,
            "Accepted finite snapshot library required")
    observed = json.loads(subprocess.run(["qstat", "-xf", "-F", "json", accepted["pbs_job_id"]],
                                        check=True, capture_output=True).stdout)["Jobs"][accepted["pbs_job_id"]]
    require(observed["job_state"] == "F" and observed["Exit_status"] == 0 and observed["run_count"] == 1,
            "Successful fixture terminal evidence required")
    library = accepted["sources"]["snapshot_v2.py"]
    source = bounded(library["path"])
    require(hashlib.sha256(source).hexdigest() == LIBRARY_SHA, "Accepted finite library changed")
    spec = importlib.util.spec_from_file_location("accepted_finite_snapshot", library["path"])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(source, library["path"], "exec"), module.__dict__)
    stage = Path(args.stage)
    request, authority = actual_request(work, stage, module.scan_references)
    module.save_new(stage / "private-request.json", module.encode(request))
    module.save_new(stage / "private-authority.json", module.encode(authority))
    receipt = module.snapshot(request, stage / "snapshot")
    result = dict(schema=1, purpose="actual_finite_snapshot_collection", pbs_job_id=os.environ["PBS_JOBID"],
                  collector=dict(path=str(Path(__file__).resolve()), sha256=args.self_sha256), library=library,
                  fixture=dict(path=str(fixture / "accepted.json"), sha256=FIXTURE_SHA),
                  request=pin(stage / "private-request.json"), authority=pin(stage / "private-authority.json"),
                  snapshot_receipt=pin(stage / "snapshot/receipt.json"), counts={key:receipt[key] for key in
                    ("source_references", "metadata_documents", "envelope_references", "one_hop_edges", "external_records", "original_text_bytes")},
                  public_archive_created=False, full_dependency_closure_complete=False, scientific_reproduction_verified=False)
    module.save_new(stage / "accepted.json", module.encode(result))
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
