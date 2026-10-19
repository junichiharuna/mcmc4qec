"""Describe complete low-noise BAR cohorts without inventing a reference."""
import argparse
from collections import defaultdict
import itertools
import json
import math
from pathlib import Path
from statistics import fmean

import calibration as c
import tile_low_noise_analysis as analysis
import tile_comparisons as comparisons
import tile_summary as original
import tile_weight_reference_comparison as bounded

CONDITION = original.CONDITION
WARNING = "No independent reference is supplied: bias, RMSE and coverage are not assessed. Setting agreement, interval overlap and diagnostics do not certify convergence or accuracy. Paired contrasts are descriptive, not simultaneous inference or a recommendation. Missing outcomes remain in the planned denominator."


def expected_conditions(plan):
    for kernel, initial in itertools.product(plan["kernels"], plan["initializations"]):
        for chains, burn, samples, _, label, _, block in analysis.analysis_settings(plan):
            yield (plan["case"], kernel, initial, chains, burn, samples, label,
                   "cross_chain" if block is None else "block", block)


def paired_agreement(left, right, replicates):
    left = comparisons.validate_cohort(left, replicates)
    right = comparisons.validate_cohort(right, replicates)
    pairs = [(a["estimate"], b["estimate"]) for a, b in zip(left, right)
             if a["estimate"] is not None and b["estimate"] is not None]
    positive = [(a, b) for a, b in pairs if a > 0 and b > 0]
    difference, difference_se = comparisons.moments([b-a for a, b in pairs])
    log_ratio, log_se = comparisons.moments([math.log(b)-math.log(a) for a, b in positive])
    available = dict(mean_estimate_difference=difference, estimate_difference_standard_error=difference_se,
                     mean_log_ratio=log_ratio, log_ratio_standard_error=log_se)
    intervals = [(a["interval"], b["interval"]) for a, b in zip(left, right)
                 if a["interval"] is not None and b["interval"] is not None]
    disjoint = sum(a[1] < b[0] or b[1] < a[0] for a, b in intervals)
    result = {key: value if (len(positive) if "log_ratio" in key else len(pairs)) == replicates else None
              for key, value in available.items()}
    return dict(result, replicates=replicates, point_pairs=len(pairs), positive_point_pairs=len(positive),
                difference_direction="right-minus-left", log_ratio_direction="log(right)-log(left)",
                interval_pairs=len(intervals), disjoint_intervals=disjoint,
                unavailable_interval_pairs=replicates-len(intervals), available_only=available,
                intervals_unavailable=dict(left=sum(row["interval"] is None for row in left),
                                           right=sum(row["interval"] is None for row in right)))


def summarize_rows(plan, rows):
    """Numerical summary only; caller must validate persisted input evidence."""
    expected = list(expected_conditions(plan))
    if len(set(expected)) != len(expected):
        raise ValueError("duplicate planned condition")
    expected_set = set(expected)
    cohorts = defaultdict(list)
    spec = plan["condition"]
    kernels, initializations = list(plan["kernels"]), plan["initializations"]
    for row in rows:
        key = tuple(row[name] for name in CONDITION)
        if key not in expected_set:
            raise ValueError("unexpected analysis condition")
        rep = row["replicate"]
        group = [plan["case"], plan["target_index"], kernels.index(row["kernel"]),
                 initializations.index(row["init"]), rep]
        if (type(rep) is not int or row["group"] != group
                or row["target_p"] != spec["target"] or row["noise"] != spec["noise"]
                or row["n"] != 2*spec["size"]**2 or row["reference"] is not None
                or row["reference_available"] is not False):
            raise ValueError("row identity or reference differs")
        if any(type(row[name]) is not bool for name in ("available", "flagged", "undefined", "high_rhat", "low_ess")):
            raise ValueError("explicit boolean availability and diagnostic flags required")
        if isinstance(row["estimate"], bool):
            raise ValueError("probability must not be boolean")
        cohorts[key].append({field: row[field] for field in comparisons.FIELDS})
    if set(cohorts) != expected_set:
        raise ValueError("missing planned condition")
    conditions = []
    replicates = plan["replicates"]
    for key in expected:
        cohort = comparisons.validate_cohort(cohorts[key], replicates)
        values = [row["estimate"] for row in cohort if row["estimate"] is not None]
        mean = fmean(values) if values else None
        assessment = bounded.assess_bounds(cohort, replicates, None)
        conditions.append(dict(zip(CONDITION, key)) | dict(
            metrics=assessment["metrics"], point_mean=mean if len(values) == replicates else None,
            available_only_point_mean=mean))
    paired = [dict(pair, **paired_agreement(cohorts[tuple(pair["left"])], cohorts[tuple(pair["right"])], replicates))
              for pair in comparisons.condition_pairs(expected)]
    return dict(schema=1, case=plan["case"], target_index=plan["target_index"], target_p=spec["target"],
                replicates=replicates, rows=len(expected)*replicates, conditions=conditions,
                paired_comparisons=paired, reference_available=False,
                population_rmse_certified=False, nominal_coverage_certified=False,
                raw_artifacts_audited=False, full_trace_redecoded=False, warning=WARNING)


def run(root, output):
    import tile_low_noise_analysis_partitions as partitions
    root, output = Path(root), Path(output)
    if output.exists():
        raise ValueError("summary output exists; preserve prior result")
    plan, rows, collection = partitions.read_collection(root)
    # Exhaust the iterator: its final checks are part of the input audit.
    result = summarize_rows(plan, rows)
    if result["rows"] != collection["rows"]:
        raise ValueError("collection row count differs")
    result.update(manifest=c.digest(plan), collection=c.digest(collection),
                  source_sha256=c.file_hash(__file__), collected_artifacts_validated=True,
                  raw_artifacts_audited=False, full_trace_redecoded=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(c.canonical(result)+b"\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.output)
    print(json.dumps(dict(rows=result["rows"], conditions=len(result["conditions"]),
                         paired_comparisons=len(result["paired_comparisons"]), reference_available=False)))


if __name__ == "__main__":
    main()
