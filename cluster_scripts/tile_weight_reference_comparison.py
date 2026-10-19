"""Compare fixed BAR cohorts to bounded references without inventing a point.

This module checks summary arithmetic. The caller must separately bind and
audit raw artifacts, the fixed decoder prior and the native runtime evidence.
"""
import math

import tile_precision_assessment as precision
import tile_study as study
import tile_weight_stratified as weight


WARNING = (
    "Interval-reference comparison only. Partial weight sums are not full point "
    "references. Omitted mass is a bound, not a statistical standard error. "
    "Empirical cohort ranges are not population-RMSE confidence intervals; "
    "reference coverage is uncertain and not simultaneous across conditions. "
    "Diagnostics and agreement do not certify convergence or nominal coverage."
)


def assess_bounds(rows, replicates, interval, thresholds=(.2, .1)):
    """Retain every replicate and return ranges over an uncertain reference.

    A temporary midpoint lets the existing validated cohort implementation
    compute interval-only quantities. All midpoint-dependent outputs are
    discarded; the midpoint is never a reported estimate of the truth.
    """
    bounds = [0., 1.] if interval is None else list(interval)
    if (len(bounds) != 2 or not all(math.isfinite(x) for x in bounds)
            or not 0 <= bounds[0] <= bounds[1] <= 1):
        raise ValueError("finite ordered reference bounds required")
    lower, upper = bounds
    internal = dict(estimate=lower + (upper-lower)/2,
                    interval_999=bounds, standard_error=None)
    assessed = precision.assess_condition(rows, replicates, internal, thresholds)
    keep = ("replicates", "point_estimates", "unavailable_intervals", "failures",
            "flagged", "undefined", "high_rhat", "low_ess",
            "available_only_mean_interval_width", "bias_reference_range",
            "rmse_reference_range")
    metrics = {key: assessed["metrics"][key] for key in keep}
    for kind in ("entire", "possible"):
        for key in (f"covered_reference_{kind}", f"coverage_reference_{kind}",
                    f"coverage_reference_{kind}_wilson95"):
            metrics[key] = assessed["metrics"][key] if interval is not None else None
    # hypot avoids underflow when squaring very small logical probabilities.
    if metrics["point_estimates"] == replicates and interval is not None:
        values = [row["estimate"] for row in rows]
        mean = math.fsum(values)/replicates
        closest = max(lower, min(upper, mean))
        rmse = lambda p: math.hypot(*(x-p for x in values))/math.sqrt(replicates)
        metrics["rmse_reference_range"] = [rmse(closest), max(rmse(lower), rmse(upper))]
    result = {key: assessed[key] for key in (
        "relative_bias_reference_range", "relative_rmse_reference_range",
        "relative_rmse_minimizer", "precision")}
    if interval is None:
        metrics.update(bias_reference_range=None, rmse_reference_range=None)
        result.update(relative_bias_reference_range=None, relative_rmse_reference_range=None,
                      relative_rmse_minimizer=None,
                      precision=[dict(epsilon=x, classification="reference_unavailable")
                                 for x in thresholds])
    return dict(result, metrics=metrics, reference_point=None,
                reference_interval=None if interval is None else bounds,
                population_rmse_certified=False, nominal_coverage_certified=False,
                warning=WARNING)


def _same_synthesis(actual, expected):
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and actual.keys() == expected.keys()
                and all(_same_synthesis(actual[k], v) for k, v in expected.items()))
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(actual) == len(expected)
                and all(_same_synthesis(a, b) for a, b in zip(actual, expected)))
    if isinstance(expected, float):
        return (isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=0.))
    return type(actual) is type(expected) and actual == expected


def compare_condition(rows, replicates, condition, *, case, target_prior, thresholds=(.2, .1)):
    """Check a weight-reference summary and assess one fixed-prior BAR cohort."""
    if (type(case) is not int or case not in range(len(study.CASES))
            or not math.isfinite(target_prior) or not 0 < target_prior < 1
            or condition["case"] != case or condition["physical_decoder_prior"] != target_prior):
        raise ValueError("reference case/prior identity differs")
    planned, available = condition["planned_trials"], condition["available_trials"]
    if (type(planned) is not int or type(available) is not int
            or not 0 <= available <= planned or planned < 1):
        raise ValueError("invalid reference trial counts")
    obtained = condition["available"]
    if type(obtained) is not bool or obtained != (not condition["failed_chunks"]):
        raise ValueError("reference availability and failed chunks disagree")
    reference = condition["reference"]
    if obtained != (reference is not None):
        raise ValueError("reference availability and synthesis disagree")
    description = None
    if obtained:
        if available != planned:
            raise ValueError("complete reference trial budget required")
        confidence = reference["confidence_level"]
        if not math.isfinite(confidence) or not 0 < confidence < 1:
            raise ValueError("invalid reference confidence level")
        strata = [{key: layer[key] for key in ("w", "mode", "trials", "failures")}
                  for layer in reference["strata"]]
        if sum(layer["trials"] for layer in strata) != planned:
            raise ValueError("stratum and condition trial counts differ")
        size, noise = study.CASES[case]
        expected = weight.synthesize(2*size*size, noise, target_prior, strata, 1-confidence)
        if not _same_synthesis(reference, expected):
            raise ValueError("saved reference synthesis disagrees with stratum counts")
        description = {key: reference[key] for key in (
            "partial_estimate", "omitted_mass_upper", "mc_standard_error_plugin",
            "interval", "confidence_level", "interval_method")}
        description["full_point_estimate"] = None
    assessment = assess_bounds(rows, replicates,
                               reference["interval"] if obtained else None, thresholds)
    return dict(case=case, physical_decoder_prior=target_prior,
                reference_available=obtained, reference=description, assessment=assessment,
                raw_artifacts_audited=False, native_decoder_revalidated=False, warning=WARNING)
