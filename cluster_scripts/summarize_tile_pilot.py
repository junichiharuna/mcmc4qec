"""Compact paired decoder-prior counts from the completed pilot, not BAR bias."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import calibration as c
import tile_study as t


def summarize(plan,data):
    expected=set(t.pilot_tasks(plan))
    keys=[tuple(r["task"]) for r in data["records"]]
    if data["manifest"]!=c.digest(plan) or len(keys)!=len(expected) or set(keys)!=expected:
        raise ValueError("incomplete or mismatched pilot")
    mismatch_fields=("repeat_mismatches","reverse_mismatches","fresh_mismatches","syndrome_violations","failure_definition_mismatches")
    checks=dict.fromkeys(mismatch_fields,0)
    grouped=defaultdict(list)
    for r in data["records"]:
        if r["status"]!="ok":
            raise ValueError("failed pilot task")
        probe=r["decoder_probe"]
        for key in checks:
            checks[key]+=probe[key]
        for comparison in probe["prior_comparisons"]:
            grouped[r["n"],r["noise"],r["p"],comparison["physical_target_prior"]].append(dict(comparison,samples=probe["samples"]))
    rows=[]
    for (n,noise,p,prior),records in sorted(grouped.items()):
        rows.append(dict(n=n,noise=noise,physical_p=p,baseline_physical_prior=p,alternative_physical_prior=prior,
                         alternative_sector_prior=records[0]["sector_prior"],tasks=len(records),
                         **{key:sum(r[key] for r in records) for key in
                            ("samples","logical_disagreements","failure_disagreements","failures","baseline_failures")}))
    return dict(tasks=len(keys),probe_samples=sum(r["decoder_probe"]["samples"] for r in data["records"]),
                checks=checks,prior_comparisons=rows,
                warning="Paired outcome counts on a small pilot sample; not a BAR bias measurement or proof of universal determinism.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--summary",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=summarize(json.loads(args.manifest.read_text()),json.loads(args.summary.read_text()))
    result.update(input_sha256=c.file_hash(args.summary),source_sha256=c.file_hash(__file__))
    c.atomic_json(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k!="prior_comparisons"}))


if __name__=="__main__":
    main()
