"""Fixed-budget independent direct-MC references for the tile study."""
import argparse
import itertools
import json
import math
from pathlib import Path
from statistics import NormalDist
import time
import traceback

import mcmc4qec as qec
import calibration as c
import tile_study as t


def runtime():
    return dict(**t.runtime(), reference_driver_sha256=c.file_hash(__file__))


def make_plan():
    return dict(schema=1, stage="independent-reference-v1", master_seed=t.MASTER,
                cases=t.CASES, targets=[.03, .05, .03, .05], chunks=[96, 96, 96, 960],
                trials_per_chunk=65536, decoder=t.SETTINGS, runtime=runtime(),
                warning="Finite Monte Carlo reference, not exact truth; fixed trial budgets, no optional stopping.")


def tasks(plan):
    return ((case, chunk) for case in range(len(plan["cases"])) for chunk in range(plan["chunks"][case]))


def chunk_seed(task):
    return t.seed((21, *task), 0)


def wilson(failures, trials, level):
    z = NormalDist().inv_cdf((1+level)/2)
    p = failures/trials
    denominator = 1+z*z/trials
    center = (p+z*z/(2*trials))/denominator
    half = z*math.sqrt(p*(1-p)/trials+z*z/(4*trials*trials))/denominator
    return [max(0., center-half), min(1., center+half)]


def reference_task(args):
    root, plan, task = args
    identity = dict(manifest=c.digest(plan), task=list(task))
    path = Path(root)/"chunks"/c.task_id(task)
    cached = c.load_artifact(path, identity)
    if cached is not None:
        return cached[1]
    started = time.perf_counter()
    try:
        case, _ = task
        size, noise = plan["cases"][case]
        _, problem = t.build_problem(size, noise, plan["targets"][case])
        result = qec.direct_mc(problem, plan["targets"][case], trials=plan["trials_per_chunk"], seed=chunk_seed(task))
        record = dict(task=list(task), status="ok", seed=chunk_seed(task), failures=result.failures, trials=result.trials,
                      estimate=result.estimate, interval=result.interval, conditional_weight=result.conditional_weight,
                      elapsed_seconds=result.elapsed_seconds, metadata=result.metadata, warnings=result.warnings)
    except Exception as error:
        record = dict(task=list(task), status="failed", error=repr(error), traceback=traceback.format_exc())
    record.update(total_seconds=time.perf_counter()-started, peak_rss_mb=c.peak_rss_mb())
    c.save_artifact(path, identity, {}, record)
    return record


def aggregate(plan, records):
    expected = set(tasks(plan))
    keys = [tuple(r["task"]) for r in records]
    if set(keys) != expected or len(keys) != len(expected) or any(r["status"] != "ok" for r in records):
        raise ValueError("complete successful fixed cohort required")
    output = []
    for case in range(len(plan["cases"])):
        subset = [r for r in records if r["task"][0] == case]
        if any(r["trials"] != plan["trials_per_chunk"] for r in subset):
            raise ValueError("fixed trial budget changed")
        trials = sum(r["trials"] for r in subset)
        failures = sum(r["failures"] for r in subset)
        estimate = failures/trials
        output.append(dict(case=case, size=plan["cases"][case][0], noise=plan["cases"][case][1],
            target_p=plan["targets"][case], chunks=len(subset), trials=trials, failures=failures, estimate=estimate,
            standard_error=math.sqrt(estimate*(1-estimate)/trials),
            interval_95=wilson(failures,trials,.95), interval_999=wilson(failures,trials,.999),
            conditional_weight=sum(r["failures"]*(r["conditional_weight"] or 0) for r in subset)/failures if failures else None,
            worker_seconds=sum(r["elapsed_seconds"] for r in subset)))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "run"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=96)
    args = parser.parse_args()
    if args.command == "plan":
        if (args.root/"manifest.json").exists():
            raise ValueError("manifest already exists")
        c.atomic_json(args.root/"manifest.json", make_plan())
        return
    plan = json.loads((args.root/"manifest.json").read_text())
    if plan != json.loads(c.canonical(make_plan())):
        raise ValueError("reference plan or runtime differs")
    started = time.perf_counter()
    # Longest-first: the much larger depolarizing case starts before short tails.
    jobs = sorted(tasks(plan), key=lambda job: (-job[0], job[1]))
    records = c.parallel_map(reference_task, [(str(args.root), plan, job) for job in jobs], args.workers)
    records.sort(key=lambda r:r["task"])
    summary = aggregate(plan, records)
    c.atomic_json(args.root/"summary.json", dict(manifest=c.digest(plan), records=summary,
                    chunks=len(records), elapsed_seconds=time.perf_counter()-started))
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
