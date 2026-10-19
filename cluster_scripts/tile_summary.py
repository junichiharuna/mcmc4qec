"""Complete-cohort BAR statistics; finite reference uncertainty stays explicit."""
import argparse
from collections import Counter, defaultdict
import itertools
import json
import math
import os
from pathlib import Path
from statistics import fmean

import calibration as c
from tile_reference import wilson


CONDITION = ("case", "kernel", "init", "chains", "burn", "samples", "ladder", "method", "block")


def summarize_condition(rows, replicates, reference):
    keys = [r["replicate"] for r in rows]
    if len(keys) != replicates or set(keys) != set(range(replicates)):
        raise ValueError("missing or duplicate replicate in fixed cohort")
    estimates = [r["estimate"] for r in rows if r["estimate"] is not None]
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in estimates):
        raise ValueError("invalid point estimate")
    target = reference["estimate"]
    lower, upper = reference["interval_999"]
    out = dict(replicates=replicates, point_estimates=len(estimates),
               reference=target, reference_standard_error=reference["standard_error"],
               reference_interval_999=[lower, upper],
               unavailable_intervals=0,
               failures=dict(Counter(r["failure"] for r in rows if r["failure"])),
               **{key:sum(bool(r[key]) for r in rows) for key in ("flagged","undefined","high_rhat","low_ess")})
    covered = dict(point=0, entire=0, possible=0)
    widths = []
    for row in rows:
        interval = row["interval"]
        if row["available"] != (interval is not None):
            raise ValueError("availability and interval disagree")
        if interval is None:
            out["unavailable_intervals"] += 1
            continue
        lo, hi = interval
        if not (math.isfinite(lo) and math.isfinite(hi) and 0 <= lo <= hi <= 1):
            raise ValueError("invalid interval")
        covered["point"] += lo <= target <= hi
        covered["entire"] += lo <= lower and upper <= hi
        covered["possible"] += lo <= upper and lower <= hi
        widths.append(hi-lo)
    for key, count in covered.items():
        out[f"covered_reference_{key}"] = count
        out[f"coverage_reference_{key}"] = count/replicates
        out[f"coverage_reference_{key}_wilson95"] = wilson(count,replicates,.95)
    out["available_only_mean_interval_width"] = fmean(widths) if widths else None
    bias = fmean(estimates)-target if estimates else None
    rmse = math.sqrt(fmean((x-target)**2 for x in estimates)) if estimates else None
    complete = len(estimates) == replicates
    out.update(bias=bias if complete else None, rmse=rmse if complete else None,
               available_only_bias=bias, available_only_rmse=rmse,
               bias_reference_range=None, rmse_reference_range=None)
    if complete:
        mean = fmean(estimates)
        closest = max(lower,min(upper,mean))
        mse = lambda value: fmean((x-value)**2 for x in estimates)
        out.update(bias_reference_range=[mean-upper,mean-lower],
                   rmse_reference_range=[math.sqrt(mse(closest)), math.sqrt(max(mse(lower),mse(upper)))])
    return out


def expected_conditions(plan, case, kernel, initial):
    spec=plan["cases"][case]
    for chains,burn,samples,ladder in itertools.product(sorted(set([4,spec["chains"]])),plan["burns"],spec["windows"],("coarse","fine")):
        for block in [b for b in plan["blocks"] if b<=samples and (b!=1024 or samples>=6000)]+[None]:
            yield case,kernel,initial,chains,burn,samples,ladder,"cross_chain" if block is None else "block",block


def summarize(root, case):
    root=Path(root)
    plan=json.loads((root/"manifest.json").read_text())
    context=json.loads((root/"analysis_manifest.json").read_text())
    if context["sampling_manifest"] != c.digest(plan):
        raise ValueError("analysis uses a different sampling manifest")
    if c.file_hash(root/"reference_summary.json") != context["reference_summary_sha256"]:
        raise ValueError("independent reference hash mismatch")
    reference=next(r for r in context["references"] if r["case"]==case)
    summaries=[]
    raw_path=root/f"rows-{case}.jsonl"
    temporary=raw_path.with_suffix(f".{os.getpid()}.tmp")
    with temporary.open("wb") as stream:
        for kernel_index,kernel in enumerate(plan["kernels"]):
            for init_index,initial in enumerate(plan["initializations"]):
                cohorts=defaultdict(list)
                expected=set(expected_conditions(plan,case,kernel,initial))
                for rep in range(plan["replicates"]):
                    group=(case,kernel_index,init_index,rep)
                    artifact=c.load_artifact(root/"analysis"/c.task_id(group),dict(analysis=c.digest(context),group=list(group)))
                    if artifact is None:
                        raise ValueError(f"missing analysis {group}")
                    record=artifact[1]
                    if record["group"]!=list(group) or record["status"]!="ok":
                        raise ValueError("invalid analysis record")
                    seen=set()
                    for row in record["rows"]:
                        key=tuple(row[k] for k in CONDITION)
                        if key in seen or key not in expected or row["replicate"]!=rep or row["group"]!=list(group):
                            raise ValueError("duplicate or unexpected condition in analysis")
                        seen.add(key)
                        cohorts[key].append(row)
                        stream.write(c.canonical(row)+b"\n")
                    if seen!=expected:
                        raise ValueError("analysis omitted expected conditions")
                for key,rows in cohorts.items():
                    summaries.append(dict(zip(CONDITION,key),**summarize_condition(rows,plan["replicates"],reference)))
    os.replace(temporary,raw_path)
    result=dict(case=case,analysis=c.digest(context),summary_source_sha256=c.file_hash(__file__),
                raw_rows_sha256=c.file_hash(raw_path),conditions=len(summaries),records=summaries,
                warning="All fixed replicates retained. Reference bounds and Wilson intervals are not simultaneous guarantees; diagnostics do not prove convergence.")
    c.atomic_json(root/f"summary-{case}.json",result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=range(4),required=True)
    args=parser.parse_args()
    result=summarize(args.root,args.case)
    print(json.dumps({k:v for k,v in result.items() if k!="records"}))


if __name__=="__main__":
    main()
