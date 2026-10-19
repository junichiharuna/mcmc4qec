"""Paired decoder-prior effects from all completed pilot comparisons."""
import argparse
import json
import math
from pathlib import Path

import calibration as c
import summarize_tile_pilot as compact
import tile_weight_stratified as w


WARNING="Paired pilot effects at fixed physical noise and the recorded Linux decoder environment. Familywise intervals assume iid physical-error draws and fixed decoder decisions; comparisons need not be independent. This is not a BAR bias estimate, a universal determinism proof or an interval-coverage calibration. Zero observed disagreement does not establish equal failure support."


def paired_table(row):
    keys=("samples","baseline_failures","failures","failure_disagreements","logical_disagreements")
    if any(type(row[key]) is not int for key in keys):
        raise ValueError("integer observed paired counts required")
    n,a,b,d,logical=(row[key] for key in keys)
    if n<1 or any(not 0<=value<=n for value in (a,b,d,logical)) or logical<d:
        raise ValueError("invalid observed counts or logical/failure mismatch order")
    doubled=(2*n-a-b-d,d+b-a,d+a-b,a+b-d)
    if any(value<0 or value%2 for value in doubled):
        raise ValueError("incompatible paired margins")
    cells=[value//2 for value in doubled]
    if sum(cells)!=n:
        raise ValueError("paired table does not conserve sample count")
    difference=b-a
    se=None if n==1 else math.sqrt(max(0.,(d-difference*difference/n)/(n*(n-1))))
    return dict(table=dict(zip(("both_success","baseline_success_alternative_failure","baseline_failure_alternative_success","both_failure"),cells)),
                failure_rate_difference=difference/n,failure_boundary_mass=d/n,paired_difference_standard_error=se)


def assess_rows(rows,alpha=.05):
    if not rows or not math.isfinite(alpha) or not 0<alpha<1:
        raise ValueError("nonempty fixed family and valid alpha required")
    keys=[(r["n"],r["noise"],r["physical_p"],r["baseline_physical_prior"],r["alternative_physical_prior"]) for r in rows]
    if len(keys)!=len(set(keys)):
        raise ValueError("duplicate prior comparison")
    marginal_alpha=alpha/(3*len(rows))
    records=[]
    for row in rows:
        result=paired_table(row)
        table=result["table"]
        new=w.clopper_pearson(table["baseline_success_alternative_failure"],row["samples"],marginal_alpha)
        recovered=w.clopper_pearson(table["baseline_failure_alternative_success"],row["samples"],marginal_alpha)
        boundary=w.clopper_pearson(row["failure_disagreements"],row["samples"],marginal_alpha)
        records.append(dict(row,**result,new_failure_interval=list(new),recovered_interval=list(recovered),
                            failure_boundary_interval=list(boundary),
                            failure_rate_difference_interval=[max(-1.,new[0]-recovered[1]),min(1.,new[1]-recovered[0])]))
    return dict(comparisons=len(rows),family_alpha=alpha,marginal_intervals=3*len(rows),marginal_alpha=marginal_alpha,
                method="Clopper-Pearson marginal intervals with Bonferroni over all comparisons and three counts per comparison",
                records=records,warning=WARNING)


def derive(manifest_path,summary_path,counts_path,alpha=.05):
    paths={"manifest":Path(manifest_path),"summary":Path(summary_path),"counts":Path(counts_path)}
    hashes={key:c.file_hash(path) for key,path in paths.items()}
    plan,data,counts=[json.loads(paths[key].read_text()) for key in ("manifest","summary","counts")]
    if counts["input_sha256"]!=hashes["summary"] or counts["source_sha256"]!=c.file_hash(compact.__file__):
        raise ValueError("pilot counts input or producer source hash mismatch")
    expected=compact.summarize(plan,data)
    if any(c.canonical(counts.get(key))!=c.canonical(value) for key,value in expected.items()):
        raise ValueError("compact counts differ from all fixed raw pilot tasks")
    result=assess_rows(expected["prior_comparisons"],alpha)
    if hashes!={key:c.file_hash(path) for key,path in paths.items()}:
        raise ValueError("pilot input changed during derivation")
    return dict(result,input_sha256=hashes,source_sha256=c.file_hash(__file__),
                confidence_source_sha256=c.file_hash(w.__file__),producer_source_sha256=c.file_hash(compact.__file__),
                pilot_tasks=expected["tasks"],distinct_probe_draws=expected["probe_samples"],
                reproducibility_checks=expected["checks"])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--summary",type=Path,required=True)
    parser.add_argument("--counts",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("derived output exists; preserve previous evidence")
    result=derive(args.manifest,args.summary,args.counts)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as stream:stream.write(c.canonical(result)+b"\n")
    print(json.dumps({key:value for key,value in result.items() if key!="records"}))


if __name__=="__main__":
    main()
