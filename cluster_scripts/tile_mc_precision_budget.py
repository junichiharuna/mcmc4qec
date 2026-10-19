"""Plan fixed direct-MC relative-RMSE budgets from an independent reference.

This does not execute a benchmark or infer walltime from a required trial count.
"""
import argparse
import json
import math
from pathlib import Path

import calibration as c
import tile_study as t


def required_trials(probability,epsilon):
    if not math.isfinite(probability) or not 0<probability<=1 or not math.isfinite(epsilon) or epsilon<=0:
        raise ValueError("positive probability and relative-RMSE target required")
    return max(1,math.ceil((1-probability)/(probability*epsilon**2)))


def relative_rmse(trials,probability):
    if not isinstance(trials,int) or trials<1 or not math.isfinite(probability) or not 0<probability<=1:
        raise ValueError("positive fixed trials and probability required")
    return math.sqrt((1-probability)/(trials*probability))


def budget_row(reference,epsilon):
    point=reference["estimate"]
    lower,upper=reference["interval_999"]
    if not 0<lower<=point<=upper<=1:
        raise ValueError("a positive finite reference interval is required")
    optimistic,conservative=required_trials(upper,epsilon),required_trials(lower,epsilon)
    planned=64*((conservative+63)//64)
    return dict(case=reference["case"],target_p=reference["target_p"],physical_decoder_prior=reference["target_p"],
                metric="relative_RMSE",epsilon=epsilon,reference_point=point,reference_interval_999=[lower,upper],
                required_trials_reference_point=required_trials(point,epsilon),
                required_trials_reference_range=[optimistic,conservative],planned_trials=planned,
                relative_rmse_at_reference_point=relative_rmse(planned,point),
                relative_rmse_reference_range=[relative_rmse(planned,upper),relative_rmse(planned,lower)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("budget plan exists; preserve prior plan")
    reference=json.loads(args.reference.read_text())
    rows=reference["records"]
    if len(rows)!=4 or {row["case"] for row in rows}!=set(range(4)):
        raise ValueError("all four independent reference cases required")
    budgets=[budget_row(row,epsilon) for row in sorted(rows,key=lambda row:row["case"]) for epsilon in (.2,.1)]
    result=dict(stage="direct_mc_time_to_accuracy_budget_v1",replicates=192,master_seed=t.MASTER,seed_stage=121,
                cases=t.CASES,decoder=t.SETTINGS,source_sha256=c.file_hash(__file__),reference_sha256=c.file_hash(args.reference),
                records=budgets,total_planned_trials=192*sum(row["planned_trials"] for row in budgets),executed=False,
                warning="Planning only. Relative RMSE is not a 95% interval half-width. Bernoulli MC is unbiased at fixed N, but the probability used here is a finite reference. Chosen budgets use its lower bound, rounded to 64; this is conditional on the true probability lying within the reference interval. No measured runtime or achieved benchmark accuracy is claimed.")
    c.atomic_json(args.output,result)
    print(json.dumps(dict(total_planned_trials=result["total_planned_trials"],records=budgets)))


if __name__=="__main__":
    main()
