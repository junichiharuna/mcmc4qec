"""Audit a completed fixed anchor cohort without replacing replicate anchors."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import tarfile

import calibration as c
import tile_bar_study as b
import tile_study as t
from tile_reference import wilson


def audit_records(plan,case,records,problem_hash):
    keys=[row["replicate"] for row in records]
    if len(keys)!=plan["replicates"] or set(keys)!=set(range(plan["replicates"])):
        raise ValueError("missing or duplicate fixed anchor replicate")
    success=[]
    failed=[]
    zero=[]
    log_se=[]
    seeds=[]
    for row in records:
        rep=row["replicate"]
        expected_seed=t.seed((32,case,rep),0)
        if row["case"]!=case or row["seed"]!=expected_seed:
            raise ValueError("wrong case or recorded anchor seed")
        seeds.append(row["seed"])
        if row["status"]=="failed":
            failed.append(rep)
            continue
        if row["status"]!="ok" or row["problem_hash"]!=problem_hash or row["trials"]!=plan["anchor_trials"]:
            raise ValueError("wrong anchor status, fixed decoder or trial budget")
        k,n=row["failures"],row["trials"]
        if not isinstance(k,int) or not 0<=k<=n or row["estimate"]!=k/n:
            raise ValueError("anchor counts do not reproduce estimate")
        expected_interval=wilson(k,n,.95)
        if len(row["interval"])!=2 or any(not math.isclose(x,y,rel_tol=0,abs_tol=1e-14) for x,y in zip(row["interval"],expected_interval)):
            raise ValueError("anchor counts do not reproduce Wilson interval")
        if not math.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"]<0:
            raise ValueError("invalid direct-MC elapsed time")
        if k==0:
            zero.append(rep)
        else:
            log_se.append(math.sqrt((1-k/n)/k))
        success.append(row)
    if len(set(seeds))!=len(seeds):
        raise ValueError("anchor seed collision")
    trials=sum(row["trials"] for row in success)
    failures=sum(row["failures"] for row in success)
    estimate=failures/trials if trials else None
    return dict(case=case,replicates=plan["replicates"],successful_replicates=len(success),failed_replicates=sorted(failed),
                zero_failure_replicates=sorted(zero),trials_available=trials,failures_available=failures,
                pooled_anchor_estimate_for_audit_only=estimate if not failed else None,
                pooled_anchor_wilson95_for_audit_only=wilson(failures,trials,.95) if not failed else None,
                available_only_pooled_estimate=estimate,
                failures_per_successful_replicate_range=[min(row["failures"] for row in success),max(row["failures"] for row in success)] if success else None,
                anchor_log_standard_error_range_positive_counts=[min(log_se),max(log_se)] if log_se else None,
                sum_direct_mc_elapsed_seconds=sum(row["elapsed_seconds"] for row in success),
                physical_sampling_p_from_pinned_source=plan["cases"][case]["rungs"][0],
                physical_decoder_prior=plan["cases"][case]["target"],all_recorded_seeds_verified=True,
                warning="Audit aggregation only; each replicate keeps its own independent anchor. Log SE is the binomial delta term used by the fixed BAR analysis, not a coverage guarantee. Raw physical errors and full direct_mc RNG metadata were not saved in these anchor artifacts; sampling p and RNG calls are checked through pinned source/manifest, not independent raw-trial recounting. Elapsed time is not CPU time.")


def audit(archive,plan,summary,verification):
    case=summary["case"]
    if verification.get("stage")!="production-anchors" or verification.get("case")!=case or c.file_hash(archive)!=verification["archive_sha256"]:
        raise ValueError("anchor archive differs from transfer audit")
    if summary["manifest"]!=c.digest(plan) or summary["command"]!="anchors":
        raise ValueError("wrong anchor phase summary")
    for key,module in (("bar_sampler_sha256",b),("tile_driver_sha256",t)):
        if plan["runtime"][key]!=c.file_hash(module.__file__):
            raise ValueError("pinned source differs")
    spec=plan["cases"][case]
    problem_hash=c.digest(t.build_problem(spec["size"],spec["noise"],spec["target"])[1].metadata())
    records=[]
    with tarfile.open(archive,"r|gz") as tar:
        for member in tar:
            if not member.name.startswith("anchors/") or not member.name.endswith(".json") or member.name.endswith(".done.json"):
                continue
            payload=tar.extractfile(member).read()
            if hashlib.sha256(payload).hexdigest()!=verification["payload_sha256"][member.name]:
                raise ValueError("anchor metadata differs from checked archive")
            row=json.loads(payload)
            if member.name!=f"anchors/{case}-{row['replicate']}.json":
                raise ValueError("anchor filename differs from metadata")
            records.append(row)
    ordered=lambda values:sorted(values,key=lambda row:row["replicate"])
    if c.canonical(ordered(records))!=c.canonical(ordered(summary["records"])) or summary["tasks"]!=len(records):
        raise ValueError("phase summary differs from raw anchor records")
    if summary["failed"]!=sum(row["status"]=="failed" for row in records):
        raise ValueError("phase failure accounting differs")
    result=audit_records(plan,case,records,problem_hash)
    result.update(phase_summary_reproduced=True,problem_hash=problem_hash,anchor_phase_wall_seconds=summary["elapsed_seconds"])
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("archive","manifest","summary","verification","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("audit output exists; preserve prior record")
    result=audit(args.archive,json.loads(args.manifest.read_text()),json.loads(args.summary.read_text()),json.loads(args.verification.read_text()))
    result.update(archive_sha256=c.file_hash(args.archive),summary_sha256=c.file_hash(args.summary),source_sha256=c.file_hash(__file__))
    c.atomic_json(args.output,result)
    print(json.dumps(result))


if __name__=="__main__":
    main()
