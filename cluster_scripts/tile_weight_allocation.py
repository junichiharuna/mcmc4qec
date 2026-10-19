"""Freeze independent weight-reference budgets from an audited allocation pilot."""
import argparse
import json
import math
from pathlib import Path

import calibration as c
import tile_weight_reference_driver as d
import tile_weight_stratified as w


POLICY=dict(tail_tolerance=1e-14,enumeration_limit=4000000,
            mc_design_worker_seconds=3600.,min_mc_trials=4096,
            max_mc_trials=4194304,trial_quantum=4096,chunk_size=4096)


def tail_cut(n,p,tolerance):
    if not 0<tolerance<1:
        raise ValueError("positive tail tolerance below one required")
    masses=[w.binomial_mass(n,index,p) for index in range(n+1)]
    for end in range(n+1):
        tail=math.fsum(masses[end+1:])
        if tail<=tolerance:
            return end,masses,tail
    raise AssertionError("full weight grid must have zero tail")


def ideal_mc_trials(masses,variances,costs,work_seconds):
    if not (len(masses)==len(variances)==len(costs)) or not math.isfinite(work_seconds) or work_seconds<=0:
        raise ValueError("matching allocation vectors and positive work budget required")
    if not masses:
        return []
    if any(not math.isfinite(x) or x<0 for x in masses) or any(not 0<x<=.25 for x in variances) or any(not math.isfinite(x) or x<=0 for x in costs):
        raise ValueError("finite mass, positive design variance and cost required")
    denominator=math.fsum(b*math.sqrt(v*cost) for b,v,cost in zip(masses,variances,costs))
    if denominator<=0:
        raise ValueError("positive mass required for MC allocation")
    return [work_seconds*b*math.sqrt(v/cost)/denominator for b,v,cost in zip(masses,variances,costs)]


def round_trials(value,minimum,maximum,quantum):
    if not math.isfinite(value) or value<0 or not 0<minimum<=maximum or quantum<1 or minimum%quantum or maximum%quantum:
        raise ValueError("finite nonnegative allocation and compatible bounds required")
    return min(maximum,max(minimum,quantum*math.ceil(min(value,maximum)/quantum)))


def layer_design(rows,weight,pilot_samples):
    exact=[row for row in rows if row["w"]==weight]
    candidates=exact or [row for row in rows if row["w"]>0]
    cost=max(row["task_wall_seconds_max"]/(1 if row["w"]==0 else pilot_samples) for row in candidates)
    if not exact:
        return cost,.25,False
    row=exact[0]
    smooth=(row["failures_available"]+.5)/(row["trials_available"]+1)
    return cost,smooth*(1-smooth),True


def make_allocation(pilot,audit,profile):
    d.validate_pilot(pilot,audit)
    if not profile.get("native_ldpc_sha256") or not profile.get("fixture"):
        raise ValueError("pinned native profile required; compute-node preflight remains mandatory")
    conditions,reports=[],[]
    for case,(size,noise) in enumerate(pilot["cases"]):
        n=2*size*size
        for prior_index,prior in enumerate(pilot["priors"][case]):
            rows=[row for row in audit["strata"] if row["case"]==case and row["prior_index"]==prior_index]
            end,masses,tail=tail_cut(n,prior,POLICY["tail_tolerance"])
            designs=[layer_design(rows,weight,pilot["samples"]) for weight in range(end+1)]
            sizes=[w.class_size(n,weight,noise) for weight in range(end+1)]
            mc=[weight for weight,count in enumerate(sizes) if count>POLICY["enumeration_limit"]]
            raw=ideal_mc_trials([masses[weight] for weight in mc],
                [designs[weight][1] for weight in mc],[designs[weight][0] for weight in mc],POLICY["mc_design_worker_seconds"])
            budgets={weight:round_trials(value,POLICY["min_mc_trials"],POLICY["max_mc_trials"],POLICY["trial_quantum"])
                     for weight,value in zip(mc,raw)}
            layers=[dict(w=weight,mode="mc" if weight in budgets else "enum",trials=budgets.get(weight,count))
                    for weight,count in enumerate(sizes)]
            seconds=0.
            for layer in layers:
                weight,trials=layer["w"],layer["trials"]
                unit=1 if weight==0 else pilot["samples"]
                seconds+=designs[weight][0]*sum(max(unit,min(POLICY["chunk_size"],trials-start))
                                               for start in range(0,trials,POLICY["chunk_size"]))
            conditions.append(dict(case=case,physical_decoder_prior=prior,layers=layers))
            reports.append(dict(case=case,physical_decoder_prior=prior,w_max=end,omitted_mass_upper=tail,
                unmeasured_weights=[weight for weight,design in enumerate(designs) if not design[2]],
                planned_trials=sum(layer["trials"] for layer in layers),
                enum_trials=sum(layer["trials"] for layer in layers if layer["mode"]=="enum"),
                mc_trials=sum(budgets.values()),planned_worker_seconds=seconds,
                pilot_observed_partial_sum=math.fsum(masses[row["w"]]*row["failure_rate"] for row in rows if row["w"]<=end),
                mc_design_standard_error=math.sqrt(math.fsum(masses[weight]**2*designs[weight][1]/budgets[weight] for weight in mc)),
                layer_design=[dict(w=weight,cost_seconds_per_trial=design[0],variance=design[1],pilot_measured=design[2])
                              for weight,design in enumerate(designs)]))
    return dict(schema=1,purpose="pilot_only_fixed_weight_allocation",conditions=conditions,
                chunk_size=POLICY["chunk_size"],pilot_audit_digest=c.digest(audit),
                platform_profile_digest=c.digest(profile),pilot_manifest_digest=c.digest(pilot),
                policy=dict(POLICY),policy_digest=c.digest(POLICY),planner_sha256=c.file_hash(__file__),
                allocation_report=reports,
                warning="Pilot-only allocation; pilot samples and pseudo-counts never enter the independent reference. Missing weights use maximum design variance; zero pilot failures do not imply exact zero. Design SE and work are planning quantities, not achieved uncertainty or measured runtime. Bounds, rounding and enumeration change the design work budget. The absolute tail tolerance does not guarantee relative accuracy at low noise. Actual per-condition CP/Bonferroni intervals retain the tail and failed chunks remain unavailable.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-manifest",type=Path,required=True)
    parser.add_argument("--pilot-audit",type=Path,required=True)
    parser.add_argument("--platform-profile",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    values=[json.loads(path.read_text()) for path in (args.pilot_manifest,args.pilot_audit,args.platform_profile)]
    result=make_allocation(*values)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(c.canonical(result)+b"\n")
    print(json.dumps(dict(allocation=c.digest(result),conditions=len(result["conditions"]),
                         planned_trials=sum(row["planned_trials"] for row in result["allocation_report"]))))


if __name__=="__main__":
    main()
