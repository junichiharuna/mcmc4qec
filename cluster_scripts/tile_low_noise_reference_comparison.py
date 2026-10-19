"""Compare a complete low-noise BAR cohort to an audited bounded reference."""
from collections import defaultdict
import argparse
import json
import os
from pathlib import Path
import socket

import calibration as c
import tile_low_noise_summary as description
import tile_weight_reference_comparison as bounded

WARNING = "The weight reference is an interval with omitted-mass bounds, not a full point reference. All planned replicates remain in the denominator. Empirical bias/RMSE ranges and reference-interval coverage do not certify population precision or nominal coverage. Reference label checkpoints and MCMC saved checkpoints are not full independent re-decoding."


def compatible_condition(plan, context):
    reference = context["reference"]
    profile = plan["native_input_digests"]["platform_profile"]
    if (context["purpose"] != "weight_reference_production"
            or c.canonical(reference["runtime"]) != c.canonical(plan["runtime"])
            or c.canonical(reference["decoder"]) != c.canonical(plan["decoder"])
            or reference["platform_profile_digest"] != profile
            or context["input_digests"]["platform_profile"] != profile):
        raise ValueError("fixed decoder/runtime/native profile differs")
    matches = [index for index, row in enumerate(reference["conditions"])
               if row["case"] == plan["case"] and row["physical_decoder_prior"] == plan["condition"]["target"]]
    if len(matches) != 1:
        raise ValueError("exactly one matching reference case/prior required")
    return matches[0]


def compare_rows(plan, rows, condition):
    """Numerical comparison only; persisted evidence is a caller responsibility."""
    rows = list(rows)
    validated = description.summarize_rows(plan, rows)
    cohorts = defaultdict(list)
    for row in rows:
        cohorts[tuple(row[name] for name in description.CONDITION)].append(row)
    keys = list(description.expected_conditions(plan))
    # Validate the reference synthesis once, before sharing it across settings.
    reference = bounded.compare_condition(cohorts[keys[0]], plan["replicates"], condition,
                                          case=plan["case"], target_prior=plan["condition"]["target"])
    interval = reference["assessment"]["reference_interval"]
    conditions = [dict(zip(description.CONDITION, key)) | dict(
        assessment=bounded.assess_bounds(cohorts[key], plan["replicates"], interval)) for key in keys]
    return dict(schema=1, case=plan["case"], target_index=plan["target_index"],
                target_p=plan["condition"]["target"], replicates=plan["replicates"], rows=validated["rows"],
                reference_available=reference["reference_available"], reference=reference["reference"],
                conditions=conditions, raw_reference_audited=False, native_decoder_revalidated=False,
                all_reference_labels_redecoded=False, all_mcmc_states_redecoded=False,
                nominal_coverage_certified=False, population_rmse_certified=False, warning=WARNING)


def source_hashes():
    import audit_tile_weight_reference as audit
    import tile_low_noise_analysis_partitions as partitions
    import tile_low_noise_study as low
    import tile_reference as reference
    modules = (c, description, description.analysis, description.comparisons, description.original,
               bounded, bounded.precision, bounded.study, bounded.weight, partitions, audit, low, reference)
    result = {Path(module.__file__).name: c.file_hash(module.__file__) for module in modules}
    result[Path(__file__).name] = c.file_hash(__file__)
    return result


def run(root, reference_root, output):
    import audit_tile_weight_reference as audit
    import tile_low_noise_analysis_partitions as partitions
    import tile_low_noise_study as low
    if (not os.environ.get("PBS_JOBID")
            or any(os.environ.get(key) != value for key, value in low.native.THREADS.items())):
        raise ValueError("PBS job and fixed single-thread environment required")
    root, reference_root, output = Path(root), Path(reference_root), Path(output)
    if output.exists():
        raise ValueError("comparison output exists; preserve prior result")
    sources = source_hashes()
    plan, rows, collection = partitions.read_collection(root)
    # Its final consistency checks run only when this iterator is exhausted.
    rows = list(rows)
    manifest = reference_root/"manifest.json"
    manifest_hash = c.file_hash(manifest)
    context = json.loads(manifest.read_bytes())
    index = compatible_condition(plan, context)
    report = audit.audit_saved_condition(reference_root, index)
    if (c.canonical(report["context"]) != c.canonical(context)
            or report["context_digest"] != c.digest(context)
            or report["reference_plan_digest"] != c.digest(context["reference"])
            or report["native_profile_digest"] != plan["native_input_digests"]["platform_profile"]
            or report["native_platform_verified"] is not True
            or report["raw_reference_audited"] is not True
            or report["all_labels_redecoded"] is not False
            or report["condition"]["condition"] != index
            or c.file_hash(manifest) != manifest_hash):
        raise ValueError("reference audit does not bind the requested fixed condition")
    result = compare_rows(plan, rows, report["condition"])
    if result["rows"] != collection["rows"]:
        raise ValueError("collection row count differs")
    if source_hashes() != sources:
        raise ValueError("comparison source changed during audit")
    result.update(manifest=c.digest(plan), collection=c.digest(collection), reference_audit=report,
                  source_sha256=sources,
                  comparison_source_sha256=c.file_hash(__file__),
                  pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname(),
                  collected_artifacts_validated=True, raw_reference_audited=True,
                  native_decoder_revalidated=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(c.canonical(result)+b"\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.reference_root, args.output)
    print(json.dumps(dict(rows=result["rows"], conditions=len(result["conditions"]),
                         reference_available=result["reference_available"])))


if __name__ == "__main__":
    main()
