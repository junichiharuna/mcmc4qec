"""Descriptive costs for complete independent cohorts that meet empirical precision.

Call only after artifact, provenance and independent-reference validation.
This module performs statistical postprocessing, not artifact or trace auditing.
"""
from collections import Counter
import math
from statistics import fmean

import tile_precision_assessment as precision


BAR_PHASES=("construction","anchor","initialization","sampling","compact","analysis")
WARNING=("Full fixed cohorts, including failed tasks. Ratios are MC mean cost / BAR mean cost; "
         "values above one favor BAR for that clock only. Both empirical precision targets must pass "
         "over the finite reference interval. No population-RMSE, population-time-ratio or nominal "
         "coverage certification. BAR timing does not collect mixing diagnostics. Task clocks exclude "
         "artifact writes; job phase clocks cannot be apportioned to conditions. Inputs still require "
         "artifact, native-environment, selection and independent-reference audits.")


def cost_summary(values):
    present=[value for value in values if value is not None]
    if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<0 for v in present):
        raise ValueError("cost must be finite nonnegative seconds or missing")
    complete=len(present)==len(values)
    mean=fmean(present) if present else None
    total=math.fsum(present) if present else None
    return dict(records=len(values),missing=len(values)-len(present),sum=total if complete else None,
                mean=mean if complete else None,available_only_mean=mean,
                available_only_min=min(present) if present else None,
                available_only_max=max(present) if present else None)


def assess(method,records,replicates,reference,epsilon):
    if method not in ("mc","bar"):
        raise ValueError("method must be mc or bar")
    allowed={"ok","failed"} if method=="mc" else {"ok","failed","unavailable"}
    if any(row["status"] not in allowed for row in records):
        raise ValueError("unknown task status")
    rows=[]
    for record in records:
        failed=record["status"]=="failed"
        interval=None if failed else record.get("interval")
        if method=="bar" and not failed and record["available"]!=(interval is not None):
            raise ValueError("BAR interval availability differs")
        rows.append(dict(replicate=record["replicate"],estimate=None if failed else record.get("estimate"),
                         interval=interval,available=interval is not None,
                         flagged=method=="bar",undefined=method=="bar",high_rhat=False,low_ess=False,
                         failure=record.get("failure") or (record.get("error","task failed") if failed else None)))
    assessment=precision.assess_condition(rows,replicates,reference,(epsilon,))
    costs={key:cost_summary([row.get(key) for row in records]) for key in ("task_wall_seconds","cpu_seconds")}
    if method=="mc":
        for key in ("construction_wall_seconds","direct_mc_elapsed_seconds"):
            costs[key]=cost_summary([row.get(key) for row in records])
    else:
        for phase in BAR_PHASES:
            for clock in ("wall_seconds","cpu_seconds"):
                costs[phase+"_"+clock]=cost_summary([row.get("timing",{}).get(phase,{}).get(clock) for row in records])
    return dict(method=method,replicates=replicates,status_counts=dict(Counter(row["status"] for row in records)),
                precision=assessment,costs=costs,diagnostics_status="not_applicable" if method=="mc" else "not_collected",
                raw_records_audited_here=False,warning=WARNING)


def compare(mc_records,bar_records,replicates,reference,epsilon):
    mc=assess("mc",mc_records,replicates,reference,epsilon)
    bar=assess("bar",bar_records,replicates,reference,epsilon)
    qualified=all(result["precision"]["precision"][0]["classification"]=="empirical_within_target" for result in (mc,bar))
    ratios={}
    for key in ("task_wall_seconds","cpu_seconds"):
        numerator,denominator=mc["costs"][key]["mean"],bar["costs"][key]["mean"]
        value=None
        if not qualified:
            reason="precision_not_confirmed"
        elif numerator is None or denominator is None:
            reason="incomplete_costs"
        elif denominator==0:
            reason="zero_bar_cost"
        elif not math.isfinite(numerator/denominator):
            reason="numerical_range"
        else:
            reason=None
            value=numerator/denominator
        ratios[key]=dict(value=value,reason=reason)
    return dict(epsilon=epsilon,mc=mc,bar=bar,ratios_mc_over_bar=ratios,
                phase_time_apportioned=False,nominal_coverage_certified=False,
                population_precision_certified=False,warning=WARNING)
