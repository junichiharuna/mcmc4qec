"""Recompute recovered MC counts and check every seed and target decoder."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import fmean, variance
import tarfile

import calibration as c
import tile_study as t
import tile_reference as r


def conditional_weight_reference(records):
    trials={x["trials"] for x in records}
    if len(trials)!=1 or len(records)<2:
        raise ValueError("at least two equal-budget independent chunks required")
    counts=[x["failures"] for x in records]
    total=sum(counts)
    if not total:
        return dict(mean=None,chunk_delta_standard_error=None,chunks=len(records))
    sums=[x["failures"]*(x["conditional_weight"] or 0.) for x in records]
    mean=sum(sums)/total
    residuals=[v-mean*k for v,k in zip(sums,counts)]
    se=math.sqrt(variance(residuals)/len(records))/fmean(counts)
    return dict(mean=mean,chunk_delta_standard_error=se,chunks=len(records))


def audit(archive,plan,summary,verification):
    if verification["archive_sha256"]!=c.file_hash(archive):
        raise ValueError("archive changed after transfer audit")
    if summary["manifest"]!=c.digest(plan):
        raise ValueError("reference summary manifest differs")
    expected_models={case:c.digest(t.build_problem(size,noise,plan["targets"][case])[1].metadata())
                     for case,(size,noise) in enumerate(plan["cases"])}
    records=[]
    package_hashes=set()
    with tarfile.open(archive,"r|gz") as tar:
        for member in tar:
            if not member.name.startswith("chunks/") or not member.name.endswith(".json") or member.name.endswith(".done.json"):
                continue
            payload=tar.extractfile(member).read()
            if hashlib.sha256(payload).hexdigest()!=verification["payload_sha256"][member.name]:
                raise ValueError("metadata differs from verified archive")
            record=json.loads(payload)
            task=record["task"]
            if record["status"]!="ok" or record["seed"]!=r.chunk_seed(task):
                raise ValueError("chunk failure or wrong seed")
            if member.name!=f"chunks/{c.task_id(task)}.json":
                raise ValueError("task/filename mismatch")
            metadata=record.pop("metadata")
            if c.digest({key:metadata[key] for key in ("model","noise","decoder","failure")})!=expected_models[task[0]]:
                raise ValueError("model, noise, failure or target-prior decoder mismatch")
            if metadata["sampling_p"]!=plan["targets"][task[0]] or metadata["rng"]["entropy"]!=record["seed"]:
                raise ValueError("sampling parameter or actual RNG mismatch")
            package_hashes.add(metadata["package_source_sha256"])
            records.append(record)
    records.sort(key=lambda row:row["task"])
    regenerated=r.aggregate(plan,records)
    if c.canonical(regenerated)!=c.canonical(summary["records"]) or summary["chunks"]!=len(records):
        raise ValueError("recomputed complete-cohort summary differs")
    if len({x["seed"] for x in records})!=len(records) or len(package_hashes)!=1:
        raise ValueError("seed collision or mixed package sources")
    return dict(chunks=len(records),total_trials=sum(x["trials"] for x in records),
                summary_reproduced=True,all_seeds_verified=True,all_problem_metadata_verified=True,
                package_source_sha256=sorted(package_hashes),model_hashes=expected_models,
                conditional_weight=[dict(case=case,**conditional_weight_reference([x for x in records if x["task"][0]==case])) for case in range(4)],
                warning="Conditional-weight SE uses an independent-chunk delta approximation. Seed/config/count audit is not a second decoder implementation.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("archive","manifest","summary","verification","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.archive,json.loads(args.manifest.read_text()),json.loads(args.summary.read_text()),json.loads(args.verification.read_text()))
    result.update(archive_sha256=c.file_hash(args.archive),summary_sha256=c.file_hash(args.summary),source_sha256=c.file_hash(__file__))
    c.atomic_json(args.output,result)
    print(json.dumps(result))


if __name__=="__main__":
    main()
