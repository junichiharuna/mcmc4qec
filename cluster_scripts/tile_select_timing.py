"""Select reproducible independent-timing candidates from full calibration cohorts."""
import argparse
from collections import Counter
import itertools
import json
import math
from pathlib import Path

import calibration as c
import tile_bar_study as b
import tile_precision_assessment as p
import tile_summary as s


POLICY=dict(schema=1,thresholds=[.2,.1],replicates=192,
    eligibility="all points present and empirical relative RMSE upper bound over reference interval <= epsilon",
    ranking=["total_proposed_steps","cross_chain_before_block","smaller_block","ZH_before_ZHS","logical_before_rejection","canonical_condition"],
    diagnostic_filter=False,interval_availability_filter=False)
WARNING="Calibration candidate for an independent check, not a recommended or fastest setting. Step count is not measured time. Full trace/anchor/reference audits and initialization comparisons remain required before submission. Diagnostic failures and unavailable intervals are retained. Independent accuracy and nominal coverage are not certified."


def step_count(plan,condition):
    spec=plan["cases"][condition["case"]]
    rungs=spec["coarse"] if condition["ladder"]=="coarse" else spec["rungs"]
    return len(rungs)*condition["chains"]*(condition["burn"]+condition["samples"])


def rank(plan,condition):
    return (step_count(plan,condition),condition["method"]!="cross_chain",condition["block"] or 0,
            condition["kernel"]!="ZH",condition["init"]!="logical",c.canonical(condition))


def classification(assessment,epsilon):
    metrics=assessment["metrics"]
    if metrics["replicates"]!=192 or not 0<=metrics["point_estimates"]<=192:
        raise ValueError("fixed full-cohort accounting required")
    bounds=assessment["relative_rmse_reference_range"]
    if bounds is not None and (len(bounds)!=2 or not all(math.isfinite(v) for v in bounds) or not 0<=bounds[0]<=bounds[1]):
        raise ValueError("invalid relative precision bounds")
    if metrics["point_estimates"]!=192:
        return "incomplete_points"
    if bounds is None:
        classifications={row["epsilon"]:row["classification"] for row in assessment["precision"]}
        result=classifications[epsilon]
        if result not in ("reference_zero_boundary","numerical_range"):
            raise ValueError("missing precision bounds without an explicit undefined reason")
        return result
    if bounds[1]<=epsilon:return "empirical_within_target"
    if bounds[0]>epsilon:return "empirical_above_target"
    return "reference_sensitive"


def choose(plan,reports):
    """Choose from freshly recomputed assessments; run() provides raw-file validation."""
    if plan["replicates"]!=192 or len(reports)!=4 or sorted(r["case"] for r in reports)!=list(range(4)):
        raise ValueError("all four fixed 192-replicate cohorts required")
    records=[]
    evidence=[]
    for report in sorted(reports,key=lambda r:r["case"]):
        case=report["case"]
        expected={key for kernel,initial in itertools.product(plan["kernels"],plan["initializations"])
                  for key in s.expected_conditions(plan,case,kernel,initial)}
        observed=[tuple(row["condition"][key] for key in s.CONDITION) for row in report["records"]]
        if report["replicates"]!=192 or report["conditions"]!=len(expected) or len(observed)!=len(expected) or set(observed)!=expected:
            raise ValueError("missing, duplicate or unexpected calibration condition")
        evidence.append(dict(case=case,assessment_digest=c.digest(report),input_sha256=report["input_sha256"]))
        for epsilon in POLICY["thresholds"]:
            classes=[classification(row["assessment"],epsilon) for row in report["records"]]
            eligible=[row for row,kind in zip(report["records"],classes) if kind=="empirical_within_target"]
            out=dict(case=case,epsilon=epsilon,eligible_conditions=len(eligible),classification_counts=dict(sorted(Counter(classes).items())),
                     precision_independently_confirmed=False,recommended=False)
            if eligible:
                selected=min(eligible,key=lambda row:rank(plan,row["condition"]))
                out.update(status="selected",condition=selected["condition"],
                           total_proposed_steps=step_count(plan,selected["condition"]),calibration_assessment=selected["assessment"])
            else:
                out.update(status="unmet",reason="No complete calibration condition met the empirical precision target over the reference interval.")
            records.append(out)
    source={"selector":c.file_hash(__file__),"precision":c.file_hash(p.__file__),"summary":c.file_hash(s.__file__)}
    hashes=sorted({*(v for row in evidence for v in row["input_sha256"].values()),
                   *(row["assessment_digest"] for row in evidence),*source.values(),c.digest(POLICY)})
    return dict(schema=1,purpose="standalone_bar_settings",sampling_manifest=c.digest(plan),
                selection_evidence_sha256=hashes,assessment_evidence=evidence,policy=POLICY,
                source_sha256=source,records=records,warning=WARNING)


def run(root,output):
    root,output=Path(root),Path(output)
    if output.exists():
        raise ValueError("selection exists; preserve prior evidence")
    plan=json.loads((root/"manifest.json").read_text())
    if c.canonical(plan)!=c.canonical(b.make_plan()):
        raise ValueError("fixed production sampling manifest and runtime required")
    reports=[p.assess_calibration(root,case) for case in range(4)]
    # Recheck all inputs after every case has been assessed, before publishing a selection.
    paths=dict(sampling="manifest.json",analysis="analysis_manifest.json",reference="reference_summary.json")
    for report in reports:
        case=report["case"]
        for name,sha in report["input_sha256"].items():
            filename=paths.get(name) or (f"summary-{case}.json" if name=="summary" else f"rows-{case}.jsonl")
            if c.file_hash(root/filename)!=sha:
                raise ValueError("calibration input changed during candidate selection")
    result=choose(plan,reports)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("xb") as stream:stream.write(c.canonical(result)+b"\n")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.root,args.output)
    print(json.dumps(dict(output=str(args.output),outcomes=[{k:row[k] for k in ("case","epsilon","status","eligible_conditions")} for row in result["records"]],warning=WARNING)))


if __name__=="__main__":
    main()
