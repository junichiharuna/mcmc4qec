"""Empirical full-cohort relative precision with finite-reference uncertainty."""
import argparse
from collections import defaultdict
import itertools
import json
import math
from pathlib import Path

import calibration as c
import tile_summary as s


WARNING="Empirical fixed-cohort relative RMSE over a finite reference interval. Reference coverage is not certain; replicate sampling uncertainty is not a population-RMSE confidence interval. Missing points never qualify through available-only statistics. Precision, diagnostics and interval coverage remain separate. No recommendation or nominal coverage certification."


def assess_condition(rows,replicates,reference,thresholds=(.2,.1)):
    point=reference["estimate"]
    lower,upper=reference["interval_999"]
    if not all(math.isfinite(v) for v in (point,lower,upper)) or not 0<=lower<=point<=upper<=1:
        raise ValueError("finite ordered reference probability interval required")
    if (not isinstance(replicates,int) or isinstance(replicates,bool) or replicates<1 or not thresholds
        or any(not math.isfinite(v) or v<=0 for v in thresholds) or len(set(thresholds))!=len(thresholds)):
        raise ValueError("positive fixed cohort and distinct finite positive thresholds required")
    metrics=s.summarize_condition(rows,replicates,reference)
    result=dict(metrics=metrics,relative_bias_reference_point=None,relative_bias_reference_range=None,
                relative_rmse_reference_point=None,relative_rmse_reference_range=None,relative_rmse_minimizer=None,
                population_rmse_certified=False,nominal_coverage_certified=False,warning=WARNING)
    status=None
    values=[row["estimate"] for row in rows if row["estimate"] is not None]
    if len(values)!=replicates:
        status="incomplete_points"
    else:
        rmse=lambda p:math.hypot(*(x/p-1 for x in values))/math.sqrt(replicates)
        bias=lambda p:math.fsum(x/p-1 for x in values)/replicates
        if point>0:
            r,bias_at_point=rmse(point),bias(point)
            if math.isfinite(r) and math.isfinite(bias_at_point):
                result.update(relative_rmse_reference_point=r,relative_bias_reference_point=bias_at_point)
        if lower==0:
            status="reference_zero_boundary"
        else:
            scale=max(values)
            if scale:
                scaled=[x/scale for x in values]
                stationary=scale*math.fsum(x*x for x in scaled)/math.fsum(scaled)
                minimizer=max(lower,min(upper,stationary))
            else:
                minimizer=lower
            bounds=[rmse(minimizer),max(rmse(lower),rmse(upper))]
            bias_bounds=[bias(upper),bias(lower)]
            if all(math.isfinite(v) for v in (*bounds,*bias_bounds)):
                result.update(relative_rmse_reference_range=bounds,relative_rmse_minimizer=minimizer,
                              relative_bias_reference_range=bias_bounds)
            else:
                status="numerical_range"
    assessments=[]
    for epsilon in thresholds:
        if status is not None:
            classification=status
        elif result["relative_rmse_reference_range"][1]<=epsilon:
            classification="empirical_within_target"
        elif result["relative_rmse_reference_range"][0]>epsilon:
            classification="empirical_above_target"
        else:
            classification="reference_sensitive"
        assessments.append(dict(epsilon=epsilon,classification=classification))
    result["precision"]=assessments
    return result


def assess_calibration(root,case):
    root=Path(root)
    paths={"sampling":root/"manifest.json","analysis":root/"analysis_manifest.json",
           "reference":root/"reference_summary.json","summary":root/f"summary-{case}.json","rows":root/f"rows-{case}.jsonl"}
    hashes={key:c.file_hash(path) for key,path in paths.items()}
    plan,context,reference_file,summary=[json.loads(paths[key].read_text()) for key in ("sampling","analysis","reference","summary")]
    if (context["sampling_manifest"]!=c.digest(plan) or context["reference_summary_sha256"]!=hashes["reference"]
        or summary["analysis"]!=c.digest(context) or summary["case"]!=case or summary["raw_rows_sha256"]!=hashes["rows"]):
        raise ValueError("calibration manifest/reference/raw-row hash binding differs")
    references=[record for record in context["references"] if record["case"]==case]
    raw_references=[record for record in reference_file["records"] if record["case"]==case]
    if len(references)!=1 or c.canonical(references)!=c.canonical(raw_references) or references[0]["target_p"]!=plan["cases"][case]["target"]:
        raise ValueError("reference identity or target differs")
    expected={key for kernel,initial in itertools.product(plan["kernels"],plan["initializations"])
              for key in s.expected_conditions(plan,case,kernel,initial)}
    cohorts=defaultdict(list)
    keep=("replicate","estimate","interval","available","flagged","undefined","high_rhat","low_ess","failure")
    with paths["rows"].open(encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line)
            key=tuple(row[name] for name in s.CONDITION)
            if key not in expected:
                raise ValueError("unexpected calibration condition")
            cohorts[key].append({name:row[name] for name in keep})
    stored={tuple(row[name] for name in s.CONDITION):row for row in summary["records"]}
    if (set(cohorts)!=expected or set(stored)!=expected or len(stored)!=len(summary["records"])
        or summary["conditions"]!=len(expected)):
        raise ValueError("missing or duplicate calibration conditions")
    records=[]
    for key in sorted(expected,key=c.canonical):
        assessment=assess_condition(cohorts[key],plan["replicates"],references[0])
        old_metrics={name:value for name,value in stored[key].items() if name not in s.CONDITION}
        if c.canonical(old_metrics)!=c.canonical(assessment["metrics"]):
            raise ValueError("saved summary disagrees with complete raw cohort")
        records.append(dict(condition=dict(zip(s.CONDITION,key)),assessment=assessment))
    if hashes!={key:c.file_hash(path) for key,path in paths.items()}:
        raise ValueError("input hash changed during assessment")
    return dict(schema=1,purpose="empirical_relative_precision_assessment",case=case,replicates=plan["replicates"],
                conditions=len(records),records=records,input_sha256=hashes,source_sha256=c.file_hash(__file__),
                summary_source_sha256=c.file_hash(s.__file__),warning=WARNING)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("assessment already exists; preserve previous evidence")
    result=assess_calibration(args.root,args.case)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(c.canonical(result)+b"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="records"}))


if __name__=="__main__":
    main()
