"""Synthetic full-dimensional low-noise BAR resource profiles, never estimates."""
import argparse
from copy import deepcopy
import itertools
import json
import math
import os
from pathlib import Path
import socket
import time
import traceback

import numpy as np
import calibration as c
import tile_study as t
import tile_low_noise_study as low
import tile_low_noise_analysis as analysis

WARNING = "ARTIFICIAL compact arrays for resource sizing only; no physical sampling, mixing, reference, coverage or time-to-accuracy interpretation. All planned groups retained."


def make_plan(case, target_index):
    production = low.make_plan(case, target_index, capacity=False)
    return dict(schema=1, purpose="low_noise_synthetic_analysis_capacity", synthetic=True,
                production=production, replicates=2, workers=8, seed_stage=155,
                native_input_digests=production["native_input_digests"],
                required_threads=production["required_threads"],
                sources=dict(capacity=c.file_hash(__file__), analysis=c.file_hash(analysis.__file__)),
                warning=WARNING)


def groups(plan):
    base = plan["production"]
    return ((base["case"], base["target_index"], kernel, init, rep)
            for kernel, init, rep in itertools.product(range(2), range(2), range(plan["replicates"])))


def production_groups(plan):
    return analysis.groups(plan["production"])


def compute_plan(plan):
    if plan["purpose"] != "low_noise_synthetic_analysis_capacity" or plan["synthetic"] is not True:
        raise ValueError("explicit synthetic capacity plan required")
    result = deepcopy(plan["production"])
    result["stages"]["analysis"] = plan["seed_stage"]
    return result


def synthetic_seed(plan, group, rung, chain):
    return t.seed((plan["seed_stage"], *group, rung, chain), 2)


def profile(args):
    root, plan, group = args
    if tuple(group) not in set(groups(plan)):
        raise ValueError("profile group outside fixed cohort")
    computational = compute_plan(plan)
    identity = dict(manifest=c.digest(plan), group=list(group), synthetic=True)
    path = Path(root)/"profiles"/c.task_id(group)
    cached = c.load_artifact(path, identity)
    if cached is not None:
        return cached[1]
    started, cpu = time.perf_counter(), time.process_time()
    record = dict(group=list(group), synthetic=True, status="ok")
    try:
        spec = computational["condition"]
        code, problem = t.build_problem(spec["size"], spec["noise"], spec["target"])
        bits = len(code.lx)*(2 if spec["noise"] == "depolarizing" else 1)
        check_count = len(problem.model.syndrome(np.zeros(code.n, dtype=np.uint8)))
        loaded, records = {}, {}
        for rung, chain in itertools.product(range(len(spec["rungs"])), range(spec["chains"])):
            rng = np.random.default_rng(synthetic_seed(plan, group, rung, chain))
            loaded[rung, chain] = dict(
                weight=np.maximum(1, rng.binomial(code.n, spec["rungs"][rung], spec["steps"])).astype(np.uint16),
                syndrome_weight=rng.binomial(check_count, .2, spec["steps"]).astype(np.uint16),
                sector=rng.integers(1, 2**bits, size=spec["steps"], dtype=np.uint32))
            records[rung, chain] = dict(status="ok", synthetic=True)
        anchor = dict(status="ok", synthetic=True, estimate=.5, failures=8192, trials=16384)
        result, _ = analysis.analyze_arrays(computational, group, loaded, records, anchor)
        record.update(rows=len(result["rows"]), diagnostic_count=result["diagnostic_count"],
                      analysis_seconds=result["wall_seconds"],
                      estimation_unavailable=sum(not row["available"] for row in result["rows"]))
        if record["estimation_unavailable"]:
            raise ValueError("synthetic profile did not exercise all planned estimators")
    except Exception as error:
        record.update(status="failed", error=repr(error), traceback=traceback.format_exc())
    record.update(wall_seconds=time.perf_counter()-started, cpu_seconds=time.process_time()-cpu,
                  peak_rss_mb=c.peak_rss_mb(), warning=WARNING)
    c.save_artifact(path, identity, {}, record)
    return record


def resource_plan(plan, summary):
    compute_plan(plan)
    expected = list(groups(plan))
    rows = summary["records"]
    keys = [tuple(row["group"]) for row in rows]
    if (summary["manifest"] != c.digest(plan) or summary["synthetic"] is not True or summary["failed"] != 0
            or summary["tasks"] != len(expected) or len(keys) != len(expected) or set(keys) != set(expected)):
        raise ValueError("complete bound synthetic capacity cohort required")
    for row in rows:
        if row["status"] != "ok" or row["synthetic"] is not True:
            raise ValueError("unsuccessful synthetic profile")
        if any(isinstance(row[key], bool) or not isinstance(row[key], (int, float))
               or not math.isfinite(row[key]) or row[key] <= 0 for key in ("wall_seconds", "peak_rss_mb")):
            raise ValueError("positive finite resource measurements required")
    seconds = max(row["wall_seconds"] for row in rows)
    rss = max(row["peak_rss_mb"] for row in rows)
    workers = min(96, math.floor((340-8)*1024/(1.5*rss)))
    waves = math.floor((86400-600)/(2*seconds))
    if workers < 1 or waves < 1:
        raise ValueError("one analysis group exceeds resources; further decomposition required")
    all_groups = list(production_groups(plan))
    per_job = workers*waves
    partitions = []
    for start in range(0, len(all_groups), per_job):
        selected = all_groups[start:start+per_job]
        wall = 1800*math.ceil((2*seconds*math.ceil(len(selected)/workers)+600)/1800)
        if wall > 86400:
            raise ValueError("rounded walltime exceeds node limit")
        partitions.append(dict(index=len(partitions), groups=[list(g) for g in selected],
                               wall_seconds=wall, walltime=f"{wall//3600:02d}:{wall%3600//60:02d}:00"))
    return dict(manifest=c.digest(plan), measurement=c.digest(summary), synthetic=True,
                production_manifest=c.digest(plan["production"]), groups=len(all_groups), workers=workers,
                cpus=96, memory_gb=max(32, math.ceil(1.5*rss*workers/1024+8)), max_nodes=2,
                max_group_wall_seconds=seconds, max_worker_rss_mb=rss, partitions=partitions, warning=WARNING)


def measured_profile(root, plan):
    """Bind resource calculations to complete native compute-node artifacts."""
    root = Path(root)
    base = plan["production"]
    if (c.canonical(plan) != c.canonical(make_plan(base["case"], base["target_index"]))
            or c.canonical(json.loads((root/"manifest.json").read_text())) != c.canonical(plan)):
        raise ValueError("profile source/runtime or saved manifest differs")
    for key, digest in plan["native_input_digests"].items():
        if c.digest(json.loads((root/(key+".json")).read_text())) != digest:
            raise ValueError("native platform inputs changed")
    summary = json.loads((root/"summary.json").read_text())
    result = resource_plan(plan, summary)
    proof = root/"preflight-analysis-capacity"/"native_preflight.json"
    if c.file_hash(proof) != summary["native_preflight_sha256"]:
        raise ValueError("native preflight evidence changed")
    evidence = json.loads(proof.read_text())
    intent = json.loads((root/"execution-intent.json").read_text())
    if (evidence["manifest"] != c.digest(plan) or not evidence["pbs_job_id"] or not evidence["hostname"]
            or any(intent[key] != evidence[key] for key in ("manifest", "pbs_job_id", "hostname"))
            or intent["synthetic"] is not True or intent["workers"] != plan["workers"]
            or summary["workers"] != plan["workers"]):
        raise ValueError("compute execution binding differs")
    low.native.trace_audit.validate_platform(json.loads((root/"platform_profile.json").read_text()), evidence["profile"])
    expected_rows = len(list(analysis.analysis_settings(base)))
    for row in summary["records"]:
        path = root/"profiles"/c.task_id(row["group"])
        marker = path.with_suffix(".done.json")
        if not marker.exists() or set(json.loads(marker.read_text())["sha256"]) != {".json", ".npz"}:
            raise ValueError("complete profile artifact marker required")
        arrays, raw = c.load_artifact(path, dict(manifest=c.digest(plan), group=row["group"], synthetic=True))
        if arrays or c.canonical(raw) != c.canonical(row):
            raise ValueError("profile raw artifact and summary differ")
        if (row["rows"] != expected_rows or row["diagnostic_count"] <= 0
                or row["estimation_unavailable"] != 0 or not math.isfinite(row["analysis_seconds"])
                or row["analysis_seconds"] <= 0):
            raise ValueError("all planned estimators must have been exercised")
    result.update(native_preflight_sha256=c.file_hash(proof),
                  execution_intent_sha256=c.file_hash(root/"execution-intent.json"))
    return result


def run_phase(root, plan):
    root = Path(root)
    base = plan["production"]
    if c.canonical(plan) != c.canonical(make_plan(base["case"], base["target_index"])):
        raise ValueError("profile source/runtime or fixed configuration changed")
    if not os.environ.get("PBS_JOBID") or any(os.environ.get(k) != v for k, v in plan["required_threads"].items()):
        raise ValueError("qsub and pinned single-thread environment required")
    if (root/"profiles").exists() or (root/"summary.json").exists():
        raise ValueError("existing capacity artifacts; automatic rerun forbidden")
    intent = dict(manifest=c.digest(plan), synthetic=True, workers=plan["workers"],
                  pbs_job_id=os.environ["PBS_JOBID"], hostname=socket.gethostname())
    with (root/"execution-intent.json").open("xb") as stream:
        stream.write(c.canonical(intent)+b"\n")
    native_hash = low.preflight(root, plan, "analysis-capacity")
    expected = list(groups(plan))
    started = time.perf_counter()
    rows = c.parallel_map(profile, [(str(root), plan, group) for group in expected], plan["workers"])
    rows.sort(key=lambda row: row["group"])
    if [tuple(row["group"]) for row in rows] != sorted(expected):
        raise ValueError("missing or duplicate completed capacity group")
    summary = dict(manifest=c.digest(plan), synthetic=True, tasks=len(rows), records=rows,
                   failed=sum(row["status"] != "ok" for row in rows), workers=plan["workers"],
                   native_preflight_sha256=native_hash, phase_wall_seconds=time.perf_counter()-started,
                   warning=WARNING)
    c.atomic_json(root/"summary.json", summary)
    if summary["failed"]:
        raise RuntimeError("failed profiles retained; automatic retry forbidden")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "run", "resources"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--case", type=int, choices=range(4))
    parser.add_argument("--target-index", type=int, choices=range(3))
    args = parser.parse_args()
    if args.command == "plan":
        if args.root.exists() and any(args.root.iterdir()):
            raise ValueError("new empty output root required")
        plan = make_plan(args.case, args.target_index)
        args.root.mkdir(parents=True, exist_ok=True)
        c.atomic_json(args.root/"manifest.json", plan)
        for key, value in low.native.platform_inputs().items():
            c.atomic_json(args.root/(key+".json"), value)
        low.preflight(args.root, plan, "plan")
        print(json.dumps(dict(manifest=c.digest(plan), groups=len(list(groups(plan))), synthetic=True)))
        return
    plan = json.loads((args.root/"manifest.json").read_text())
    base = plan["production"]
    if c.canonical(plan) != c.canonical(make_plan(base["case"], base["target_index"])):
        raise ValueError("profile source/runtime changed")
    if args.command == "run":
        result = run_phase(args.root, plan)
        print(json.dumps({k: v for k, v in result.items() if k != "records"}))
    else:
        print(json.dumps(measured_profile(args.root, plan)))


if __name__ == "__main__":
    main()
