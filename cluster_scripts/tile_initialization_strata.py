"""Supplemental parity strata for fixed depolarizing X/Z logical starts."""
import argparse
from collections import defaultdict
import itertools
import json
from pathlib import Path

import calibration as c
import tile_bar_study as b
import tile_study as t
import tile_summary as s


FIELDS=("replicate","estimate","interval","available","flagged","undefined","high_rhat","low_ess","failure")


def basis_indices(replicate,chains):
    if replicate<0 or chains not in (4,8):
        raise ValueError("fixed depolarizing design requires four or eight selected chains")
    return [(replicate*8+chain)%16 for chain in range(chains)]


def summarize_strata(rows,replicates,reference,initialization,chains):
    if replicates<2 or replicates%2 or initialization not in ("logical","rejection"):
        raise ValueError("equal fixed parity strata and a known initialization required")
    primary=s.summarize_condition(rows,replicates,reference)
    indexed={row["replicate"]:row for row in rows}
    strata=[]
    for parity in (0,1):
        ids=list(range(parity,replicates,2))
        # Relabel only the reporting index; original physical seeds stay intact.
        subset=[dict(indexed[rep],replicate=local) for local,rep in enumerate(ids)]
        indices=basis_indices(parity,chains)
        if any(basis_indices(rep,chains)!=indices for rep in ids):
            raise ValueError("initialization pattern varies within stratum")
        label=("logical_X_basis" if parity==0 else "logical_Z_basis") if initialization=="logical" else ("rejection_even" if parity==0 else "rejection_odd")
        strata.append(dict(label=label,parity=parity,original_replicate_ids=ids,
                           basis_indices=indices if initialization=="logical" else None,
                           statistics=s.summarize_condition(subset,len(ids),reference)))
    return dict(primary=primary,strata=strata)


def run(root,case,output):
    root,output=Path(root),Path(output)
    if output.exists():
        raise ValueError("stratum report already exists; preserve prior output")
    plan=json.loads((root/"manifest.json").read_text())
    if case not in (2,3):
        raise ValueError("this supplement covers only the depolarizing cases")
    spec=plan["cases"][case]
    if spec["noise"]!="depolarizing" or spec["size"] not in (6,12) or spec["chains"]!=8:
        raise ValueError("not the fixed eight-chain depolarizing design")
    for key,module in (("tile_driver_sha256",t),("bar_sampler_sha256",b)):
        if plan["runtime"][key]!=c.file_hash(module.__file__):
            raise ValueError("initialization source differs from pinned study")
    context=json.loads((root/"analysis_manifest.json").read_text())
    primary=json.loads((root/f"summary-{case}.json").read_text())
    raw=root/f"rows-{case}.jsonl"
    if context["sampling_manifest"]!=c.digest(plan) or primary["analysis"]!=c.digest(context) or primary["case"]!=case:
        raise ValueError("analysis identity differs")
    if c.file_hash(root/"reference_summary.json")!=context["reference_summary_sha256"] or c.file_hash(raw)!=primary["raw_rows_sha256"]:
        raise ValueError("reference or raw rows changed")
    expected={key for kernel,initial in itertools.product(plan["kernels"],plan["initializations"])
              for key in s.expected_conditions(plan,case,kernel,initial)}
    stored={tuple(row[key] for key in s.CONDITION):row for row in primary["records"]}
    if set(stored)!=expected or len(stored)!=len(primary["records"]):
        raise ValueError("incomplete or duplicate primary summary condition")
    cohorts=defaultdict(list)
    with raw.open() as stream:
        for line in stream:
            row=json.loads(line)
            key=tuple(row[field] for field in s.CONDITION)
            if key not in expected:
                raise ValueError("unexpected stratum condition")
            cohorts[key].append({field:row[field] for field in FIELDS})
    if set(cohorts)!=expected:
        raise ValueError("omitted stratum condition")
    reference=next(row for row in context["references"] if row["case"]==case)
    records=[]
    for key in sorted(cohorts,key=c.canonical):
        condition=dict(zip(s.CONDITION,key))
        report=summarize_strata(cohorts[key],plan["replicates"],reference,condition["init"],condition["chains"])
        if c.canonical(dict(condition,**report["primary"]))!=c.canonical(stored[key]):
            raise ValueError("primary summary cannot be reproduced")
        records.append(dict(condition,**report))
    result=dict(case=case,analysis=c.digest(context),source_sha256=c.file_hash(__file__),
                primary_summary_sha256=c.file_hash(root/f"summary-{case}.json"),raw_rows_sha256=primary["raw_rows_sha256"],
                primary_summaries_reproduced=True,conditions=len(records),records=records,
                warning="Supplemental fixed parity strata; the complete 192-replicate cohort remains primary. Failed/undefined/unavailable rows remain in their original strata. Rejection parity controls do not imply X/Z initial states. Source and index rules are checked; a complete raw initial-state audit is separate. Wilson intervals are descriptive, not simultaneous coverage guarantees. This report does not change seeds, budgets or sampling.")
    c.atomic_json(output,result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--case",type=int,choices=(2,3),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.root,args.case,args.output)
    print(json.dumps({key:result[key] for key in ("case","conditions","primary_summaries_reproduced")}))


if __name__=="__main__":
    main()
