"""Complete-cohort one-factor paired contrasts of the frozen tile BAR study."""
import argparse
from collections import Counter,defaultdict
import itertools
import json
import math
from pathlib import Path
from statistics import fmean,variance

import calibration as c
import tile_summary as s


FACTORS=dict(kernel=(1,),initialization=(2,),chains=(3,),burn=(4,),samples=(5,),
             ladder=(6,),uncertainty=(7,8))
FIELDS=("replicate","estimate","interval","available","flagged","undefined","high_rhat","low_ess","failure")


def condition_pairs(keys):
    """Every unordered pair differing in exactly one controlled factor."""
    keys=list(keys)
    if len(set(keys))!=len(keys):
        raise ValueError("duplicate conditions")
    for factor,positions in FACTORS.items():
        groups=defaultdict(list)
        for key in keys:
            groups[tuple(value for i,value in enumerate(key) if i not in positions)].append(key)
        for fixed in sorted(groups,key=c.canonical):
            for left,right in itertools.combinations(sorted(groups[fixed],key=c.canonical),2):
                yield dict(factor=factor,left=left,right=right)


def moments(values):
    return (fmean(values) if values else None,
            math.sqrt(variance(values)/len(values)) if len(values)>1 else None)


def validate_cohort(rows,replicates):
    if replicates<1 or len(rows)!=replicates or {row["replicate"] for row in rows}!=set(range(replicates)):
        raise ValueError("missing or duplicate replicate")
    for row in rows:
        estimate=row["estimate"]
        if estimate is not None and (not math.isfinite(estimate) or not 0<=estimate<=1):
            raise ValueError("invalid estimate")
        interval=row["interval"]
        if row["available"]!=(interval is not None):
            raise ValueError("interval availability mismatch")
        if interval is not None:
            lo,hi=interval
            if not (math.isfinite(lo) and math.isfinite(hi) and 0<=lo<=hi<=1):
                raise ValueError("invalid interval")
    return sorted(rows,key=lambda row:row["replicate"])


def compare(left,right,replicates,reference):
    left,right=validate_cohort(left,replicates),validate_cohort(right,replicates)
    target=reference["estimate"]
    lower,upper=reference["interval_999"]
    if not all(math.isfinite(x) for x in (target,lower,upper)) or not 0<=lower<=target<=upper<=1:
        raise ValueError("invalid reference")
    estimates=[(a["estimate"],b["estimate"]) for a,b in zip(left,right) if a["estimate"] is not None and b["estimate"] is not None]
    positive=[(a,b) for a,b in estimates if a>0 and b>0]
    difference,difference_se=moments([b-a for a,b in estimates])
    mse,mse_se=moments([(b-target)**2-(a-target)**2 for a,b in estimates])
    log_ratio,log_se=moments([math.log(b)-math.log(a) for a,b in positive])
    ref_range=sorted(fmean((b-ref)**2-(a-ref)**2 for a,b in estimates) for ref in (lower,upper)) if estimates else None
    available=dict(mean_estimate_difference=difference,estimate_difference_standard_error=difference_se,
                   mean_squared_error_difference=mse,squared_error_difference_standard_error=mse_se,
                   squared_error_difference_reference_range=ref_range,
                   mean_log_ratio=log_ratio,mean_log_ratio_standard_error=log_se)
    full={key:value if (len(positive) if "log_ratio" in key else len(estimates))==replicates else None for key,value in available.items()}
    out=dict(replicates=replicates,point_pairs=len(estimates),positive_point_pairs=len(positive),
             reference=reference,available_only=available,**full,
             intervals_unavailable=dict(left=sum(x["interval"] is None for x in left),right=sum(x["interval"] is None for x in right)),
             failures=dict(left=dict(Counter(x["failure"] for x in left if x["failure"])),
                           right=dict(Counter(x["failure"] for x in right if x["failure"]))),
             diagnostics={key:dict(left=sum(bool(x[key]) for x in left),right=sum(bool(x[key]) for x in right),
                                  difference=sum(int(bool(b[key]))-int(bool(a[key])) for a,b in zip(left,right))/replicates)
                          for key in ("flagged","undefined","high_rhat","low_ess")})
    criteria=dict(point=lambda lo,hi:lo<=target<=hi,
                  entire=lambda lo,hi:lo<=lower and upper<=hi,
                  possible=lambda lo,hi:lo<=upper and lower<=hi)
    for name,criterion in criteria.items():
        pairs=[(False if a["interval"] is None else criterion(*a["interval"]),
                False if b["interval"] is None else criterion(*b["interval"])) for a,b in zip(left,right)]
        count=Counter(pairs)
        mean,se=moments([int(b)-int(a) for a,b in pairs])
        out[f"coverage_reference_{name}"]=dict(both=count[True,True],left_only=count[True,False],
                                               right_only=count[False,True],neither=count[False,False],
                                               difference=mean,standard_error=se)
    return out


def run(root,case,output):
    root,output=Path(root),Path(output)
    if output.exists():
        raise ValueError("comparison output already exists; preserve prior report")
    plan=json.loads((root/"manifest.json").read_text())
    context=json.loads((root/"analysis_manifest.json").read_text())
    summary=json.loads((root/f"summary-{case}.json").read_text())
    raw=root/f"rows-{case}.jsonl"
    if context["sampling_manifest"]!=c.digest(plan) or summary["analysis"]!=c.digest(context) or summary["case"]!=case:
        raise ValueError("analysis/summary identity differs")
    if c.file_hash(root/"reference_summary.json")!=context["reference_summary_sha256"] or c.file_hash(raw)!=summary["raw_rows_sha256"]:
        raise ValueError("reference or raw rows changed")
    expected={key for kernel,initial in itertools.product(plan["kernels"],plan["initializations"])
              for key in s.expected_conditions(plan,case,kernel,initial)}
    cohorts=defaultdict(list)
    with raw.open() as stream:
        for line in stream:
            row=json.loads(line)
            key=tuple(row[k] for k in s.CONDITION)
            if key not in expected:
                raise ValueError("unexpected comparison condition")
            cohorts[key].append({field:row[field] for field in FIELDS})
    if set(cohorts)!=expected:
        raise ValueError("omitted comparison condition")
    for rows in cohorts.values():
        validate_cohort(rows,plan["replicates"])
    reference=next(r for r in context["references"] if r["case"]==case)
    contrasts=[]
    for pair in condition_pairs(cohorts):
        contrasts.append(dict(factor=pair["factor"],
                              left=dict(zip(s.CONDITION,pair["left"])),right=dict(zip(s.CONDITION,pair["right"])),
                              **compare(cohorts[pair["left"]],cohorts[pair["right"]],plan["replicates"],reference)))
    result=dict(case=case,analysis=c.digest(context),source_sha256=c.file_hash(__file__),
                rows_sha256=summary["raw_rows_sha256"],summary_sha256=c.file_hash(root/f"summary-{case}.json"),
                conditions=len(cohorts),contrasts=len(contrasts),records=contrasts,direction="right minus left; log(right/left)",
                warning="All planned replicate pairs retained. Shared anchors and traces stay paired; kernel/initialization streams themselves are independent. Standard errors describe replicate variation, not simultaneous tests or convergence. Reference-range MSE differences retain finite reference uncertainty. Entire/possible coverage differences are not confidence bounds on the true coverage difference. No time-to-accuracy claim is made here.")
    c.atomic_json(output,result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.root,args.case,args.output)
    print(json.dumps({key:result[key] for key in ("case","conditions","contrasts","rows_sha256")}))


if __name__=="__main__":
    main()
