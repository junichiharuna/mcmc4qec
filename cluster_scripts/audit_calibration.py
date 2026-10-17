"""Read-only full-cohort audit and lossless recovery archives after PBS analysis.

Outputs go to a separate audit directory. Scientific rows are never filtered
by diagnostic screens. Screens are post-hoc descriptions, not convergence tests.
"""
from __future__ import annotations

import argparse
import csv
from functools import lru_cache
import gzip
import itertools
import json
import math
from pathlib import Path
import tarfile
import time

import numpy as np
import calibration as c


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b, message, *, atol=1e-11, rtol=1e-9):
    require(np.allclose(a, b, atol=atol, rtol=rtol), message)


def check_inventory(directory, names):
    expected = {name+ext for name in names for ext in (".npz", ".json", ".done.json")}
    actual = {p.name for p in Path(directory).iterdir()}
    require(actual == expected, f"inventory mismatch {directory}: missing={sorted(expected-actual)[:5]}, extra={sorted(actual-expected)[:5]}")


def checked_artifact(path, identity):
    path = Path(path)
    marker = json.loads(path.with_suffix(".done.json").read_text())
    require(set(marker["sha256"]) == {".npz", ".json"}, "marker must certify both payloads")
    result = c.load_artifact(path, identity)
    require(result is not None, f"missing artifact {path}")
    inventory = [{"path": str(path.with_suffix(ext)), "sha256": sha,
                  "bytes": path.with_suffix(ext).stat().st_size} for ext, sha in marker["sha256"].items()]
    done = path.with_suffix(".done.json")
    inventory.append(dict(path=str(done), sha256=c.file_hash(done), bytes=done.stat().st_size))
    return *result, inventory


def screen_diagnostic(diag, exact_variance):
    constant = exact_variance == 0
    undefined = not constant and (diag["rhat"] is None or any(x is None for x in diag["chain_ess"]))
    high = not constant and diag["rhat"] is not None and diag["rhat"] > 1.01
    low = not constant and any(x is not None and x < 100 for x in diag["chain_ess"])
    return dict(structural_constant=constant, undefined=undefined, high_rhat=high,
                low_ess=low, flagged=undefined or high or low)


def verify_row(row, weights, n, ladder, anchor, truth):
    close(row["truth"], truth, "truth mismatch", atol=0)
    if row["estimate"] is None:
        require(not row["available"] and not row["covered"], "unavailable row marked covered")
        return
    ratios = np.asarray(row["adjacent_log_ratios"])
    require(len(ratios) == len(ladder)-1, "edge count mismatch")
    for edge, (p, q) in enumerate(zip(ladder, ladder[1:])):
        # Verify the defining equation, independently of the bisection solver.
        h0 = np.bincount(weights[edge].ravel(), minlength=n+1)
        h1 = np.bincount(weights[edge+1].ravel(), minlength=n+1)
        delta = np.arange(n+1)*math.log(q/p)+(n-np.arange(n+1))*math.log((1-q)/(1-p))
        x = delta-ratios[edge]+math.log(h1.sum()/h0.sum())
        score = (h0*np.exp(-np.logaddexp(0., -x))-h1*np.exp(-np.logaddexp(0., x))).sum()/h0.sum()
        require(abs(score) < 1e-9, "BAR equation residual")
    logp = math.log(anchor)+sum(ratios)
    close(row["log_estimate"], logp, "log estimate mismatch")
    close(row["estimate"], math.exp(logp), "estimate mismatch", atol=0)
    covariance = np.asarray(row["covariance"])
    require(covariance.shape == (len(ratios), len(ratios)), "covariance shape")
    close(covariance, covariance.T, "covariance symmetry")
    require(np.linalg.eigvalsh(covariance).min() >= -1e-10, "covariance not positive semidefinite")
    se = math.sqrt(max(0., float(covariance.sum())))
    close(row["log_se"], se, "standard error mismatch")
    interval = [math.exp(logp-1.959963984540054*se), math.exp(min(0., logp+1.959963984540054*se))]
    if row["available"]:
        close(row["interval"], interval, "interval mismatch", atol=0)
        require(row["covered"] == (interval[0] <= truth <= interval[1]), "covered flag mismatch")
    else:
        require(row["interval"] is None and not row["covered"], "unavailable interval mismatch")


def cohort_summary(rows):
    total = len(rows)
    available = sum(r["available"] for r in rows)
    covered = sum(r["covered"] for r in rows)
    p, z = covered/total, 1.959963984540054
    center = (p+z*z/(2*total))/(1+z*z/total)
    half = z*math.sqrt(p*(1-p)/total+z*z/(4*total**2))/(1+z*z/total)
    errors = np.array([r["estimate"]-r["truth"] for r in rows if r["estimate"] is not None])
    return dict(denominator=total, available=available, covered=covered, coverage=p,
                conditional_coverage=covered/available if available else None, wilson=[center-half, center+half],
                bias=float(errors.mean()) if len(errors) else None,
                rmse=float(np.sqrt(np.mean(errors**2))) if len(errors) else None,
                empirical_sd=float(np.std(errors, ddof=1)) if len(errors)>1 else None,
                mean_log_se=float(np.mean([r["log_se"] for r in rows if r["available"]])) if available else None,
                mean_width=float(np.mean([r["interval"][1]-r["interval"][0] for r in rows if r["available"]])) if available else None)


@lru_cache(maxsize=3)
def bank_info(root, manifest, code):
    bank = c.load_bank(root, manifest, code)
    n = c.problem_for(code)[0].n
    codes = bank["weight"].astype(np.uint32)*65536+bank["syndrome_weight"].astype(np.uint32)*256+bank["sector"]
    return bank, n, np.unique(codes), c.dispersed_indices(bank, 4)


@lru_cache(maxsize=96)
def exact_observables(root, manifest, code, p):
    bank, n, _, _ = bank_info(root, manifest, code)
    mass = np.exp(bank["weight"]*math.log(p)+(n-bank["weight"].astype(int))*math.log1p(-p))
    mass /= mass.sum()
    observables = {k: bank[k] for k in ("weight", "syndrome_weight")}
    observables.update({f"logical_bit_{i}": (bank["sector"] >> i) & 1 for i in range(len(c.problem_for(code)[0].lz))})
    return {key: (float(np.dot(mass, values)),
                  0. if np.ptp(values) == 0 else float(np.dot(mass, (values-np.dot(mass, values))**2)))
            for key, values in observables.items()}


def verify_truth_chunk(args):
    root, plan, code, chunk = args
    manifest = c.digest(plan)
    path = Path(root)/"truth_parts"/f"{code}-{chunk}"
    bank, record, inventory = checked_artifact(path, dict(manifest=manifest, code=code, chunk=chunk, code_identity=c.code_identity(code)))
    _, problem = c.problem_for(code)
    start, stop = (2**problem.model.n * x//32 for x in (chunk, chunk+1))
    require((record["start"], record["stop"]) == (start, stop), "truth partition range")
    indices = np.arange(start, stop, dtype=np.uint32)
    states = c.unpack(indices, problem.model.n)
    actual = indices[[problem.is_faulty(s) for s in states]]
    require(np.array_equal(actual, bank["index"]), "public failure predicate differs from truth bank")
    return dict(code=code, chunk=chunk, states=stop-start, failures=len(actual), inventory=inventory)


def expected_row_keys(plan):
    return {(burn, samples, "cross_chain" if block is None else "block", block)
            for burn, samples in itertools.product(plan["burns"], plan["windows"])
            for block in [b for b in plan["blocks"] if b <= samples and (b != 1024 or samples >= 6000)] + [None]}


def audit_group(args):
    root, plan, group = args
    manifest = c.digest(plan)
    code, ladder_id, init, rep = group
    ladder = plan["ladders"][ladder_id]
    bank, n, valid_compact, starts = bank_info(root, manifest, code)
    matrix, problem = c.problem_for(code)
    traces, inventory, trace_failures = [], [], []
    for rung, p in enumerate(ladder):
        data = []
        for chain in range(plan["chains"]):
            task = (*group, rung, chain)
            arrays, record, inv = checked_artifact(Path(root)/"traces"/c.task_id(task), dict(manifest=manifest, task=list(task)))
            inventory.extend(inv)
            if record["status"] != "ok":
                trace_failures.append(dict(task=list(task), error=record.get("error")))
                data.append(None)
                continue
            require(set(arrays) == {"weight", "syndrome_weight", "sector"}, "trace columns")
            for key, dtype in (("weight", "uint16"), ("syndrome_weight", "uint16"), ("sector", "uint32")):
                require(arrays[key].shape == (plan["steps"],) and arrays[key].dtype == dtype, "trace shape/dtype")
            compact = arrays["weight"].astype(np.uint32)*65536+arrays["syndrome_weight"].astype(np.uint32)*256+arrays["sector"]
            require(np.all(arrays["weight"] <= n) and np.all(arrays["syndrome_weight"] <= len(matrix.hz)) and
                    np.all((arrays["sector"] > 0) & (arrays["sector"] < 2**len(matrix.lz))), "trace value range")
            require(np.isin(compact, valid_compact).all(), "compact trace outside exact support")
            require(record["init_seed"] == c.seed(task, 0) and record["sample_seed"] == c.seed(task, 1), "seed mismatch")
            initial = starts[chain] if init else c.initial_index(bank, n, p, init, chain, np.random.default_rng(c.seed(task, 0)))
            require(record["initial_index"] == initial, "initialization mismatch")
            md = record["metadata"]
            for key, value in problem.metadata().items():
                require(md[key] == value, f"problem metadata {key}")
            require(md["package_source_sha256"] == plan["runtime"]["package_sha256"] and md["sampling_p"] == p,
                    "source or probability mismatch")
            require(md["rng"]["entropy"] == c.seed(task, 1), "sampler entropy mismatch")
            cfg = md["config"]
            for key, value in dict(samples=plan["steps"], chains=1, burn_in=0, thin=1,
                                   kernels=plan["kernels"], cache_cap=plan["cache_cap"], cache_policy=plan["cache_policy"]).items():
                require(cfg[key] == value, f"sampling config {key}")
            require(cfg["initial_states"] == c.unpack([initial], n).tolist(), "metadata initial state")
            require(sum(x["proposed"] for x in record["acceptance_whole_trace"].values()) == plan["steps"], "transition count")
            data.append(arrays)
        traces.append(data)
    _, record, inv = checked_artifact(Path(root)/"analysis"/c.task_id(group), dict(manifest=manifest, group=list(group)))
    inventory.extend(inv)
    require(record["status"] == "ok" and record["group"] == list(group), "analysis identity")
    keys = [(r["burn"], r["samples"], r["method"], r["block"]) for r in record["rows"]]
    require(len(keys) == len(set(keys)) and set(keys) == expected_row_keys(plan), "analysis row key set")
    anchor, truth = (c.failure_mass(bank, n, p) for p in (ladder[0], ladder[-1]))
    for row in record["rows"]:
        require(row["group"] == list(group) and row["replicate"] == rep and row["code"] == c.CODES[code]
                and row["init"] == plan["init"][init] and row["ladder"] == ladder_id, "row condition identity")
        if trace_failures:
            require(not row["available"] and row["estimate"] is None and not row["covered"], "failed trace excluded from denominator")
        else:
            burn, samples = row["burn"], row["samples"]
            weights = [np.stack([t["weight"][burn:burn+samples] for t in rung]) for rung in traces]
            verify_row(row, weights, n, ladder, anchor, truth)
    # Check point estimates remain identical across all uncertainty methods.
    for burn, samples in itertools.product(plan["burns"], plan["windows"]):
        points = [r["log_estimate"] for r in record["rows"] if r["burn"] == burn and r["samples"] == samples and r.get("log_estimate") is not None]
        if points:
            close(points, points[0], "uncertainty method changed the pooled point")
    diagnostics = []
    if not trace_failures:
        expected = set(itertools.product(plan["burns"], plan["windows"], range(len(ladder))))
        found = [(d["burn"], d["samples"], d["rung"]) for d in record["diagnostics"]]
        require(len(found) == len(expected) and set(found) == expected, "diagnostic window/rung set")
        for diag in record["diagnostics"]:
            rung, burn, samples = diag["rung"], diag["burn"], diag["samples"]
            reference = exact_observables(root, manifest, code, ladder[rung])
            expected_obs = set(reference) | {f"bennett_edge_{i}" for i in (rung-1, rung) if 0 <= i < len(ladder)-1}
            require(set(diag["observables"]) == expected_obs, "diagnostic observable set")
            for name, obs in diag["observables"].items():
                require(obs["samples_per_chain"] == samples and obs["chains"] == plan["chains"], "diagnostic sample count")
                ref_mean, ref_var = reference.get(name, (None, None))
                if name in reference:
                    source = name if name in ("weight", "syndrome_weight") else "sector"
                    values = np.stack([t[source][burn:burn+samples] for t in traces[rung]])
                    if source == "sector":
                        values = (values >> int(name.split("_")[-1])) & 1
                    close(obs["chain_means"], values.mean(axis=1), "diagnostic chain means")
                    close(obs["mean"], values.mean(), "diagnostic mean")
                screen = screen_diagnostic(obs, ref_var)
                ess = [v for v in obs["chain_ess"] if v is not None]
                iat = [v for v in obs["chain_iat"] if v is not None]
                diagnostics.append(dict(group=list(group), code=c.CODES[code], ladder=ladder_id, init=plan["init"][init], replicate=rep,
                            rung=rung, p=ladder[rung], burn=burn, samples=samples, observable=name,
                            mean=obs["mean"], exact_mean=ref_mean, exact_variance=ref_var,
                            mean_error=None if ref_mean is None else obs["mean"]-ref_mean,
                            rhat=obs["rhat"], min_chain_ess=min(ess) if ess else None,
                            max_chain_iat=max(iat) if iat else None, iat_mcse=obs["iat_mcse"], **screen))
    return dict(group=list(group), rows=record["rows"], diagnostics=diagnostics, trace_failures=trace_failures, inventory=inventory)


def compare_summaries(rows, original, plan):
    grouped = {}
    for row in rows:
        key = tuple(row[k] for k in ("code", "ladder", "init", "burn", "samples", "method", "block"))
        grouped.setdefault(key, []).append(row)
    old = {tuple(s["condition"]): s for s in original["summary"]}
    require(len(old) == len(original["summary"]) and set(old) == set(grouped), "summary condition set")
    summaries = []
    for key, cohort in grouped.items():
        require(sorted(r["replicate"] for r in cohort) == list(range(plan["replicates"])), "cohort replicate set")
        summary = cohort_summary(cohort)
        for field, value in summary.items():
            if value is None:
                require(old[key][field] is None, f"summary {field}")
            else:
                close(value, old[key][field], f"summary {field}")
        summary.update(condition=list(key), relative_bias=summary["bias"]/cohort[0]["truth"] if summary["bias"] is not None else None,
                       relative_rmse=summary["rmse"]/cohort[0]["truth"] if summary["rmse"] is not None else None,
                       truth=cohort[0]["truth"], target_p=plan["ladders"][key[1]][-1])
        summaries.append(summary)
    pairs = {tuple(p["condition"]): p for p in original["paired"]}
    require(len(pairs) == len(original["paired"]) and set(pairs) == {k for k in grouped if k[-2] == "block"}, "paired condition set")
    for key, record in pairs.items():
        base = {r["replicate"]: r for r in grouped[(*key[:-2], "cross_chain", None)]}
        diffs = [int(r["covered"])-int(base[r["replicate"]]["covered"]) for r in grouped[key]]
        close(record["paired_coverage_difference"], np.mean(diffs), "paired difference")
        close(record["paired_se"], np.std(diffs, ddof=1)/math.sqrt(len(diffs)), "paired SE")
    return summaries


def verify_csv(path, rows):
    with Path(path).open(newline="") as stream:
        saved = list(csv.DictReader(stream))
    require(len(saved) == len(rows), "CSV row count")
    def key(r):
        return tuple(str(r[k]) if r[k] is not None else "" for k in ("code", "ladder", "init", "replicate", "burn", "samples", "method", "block"))
    wanted = {key(r): r for r in rows}
    require(len(wanted) == len(rows), "duplicate analysis row")
    seen = set()
    for row in saved:
        k = key(row)
        require(k in wanted and k not in seen, "CSV missing/duplicate condition")
        seen.add(k)
        expected = wanted[k]
        for field in row:
            value = expected.get(field)
            require(row[field] == ("" if value is None else str(value)), f"CSV value mismatch {field}")


def write_gzip_jsonl(path, records):
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        for record in records:
            stream.write(c.canonical(record).decode()+"\n")


def archive_part(args):
    root, output, plan, number = args
    selected = [g for i, g in enumerate(c.groups(plan)) if i % 96 == number]
    archive = Path(output)/"archives"/f"part-{number:02}.tar.gz"
    with tarfile.open(archive, "w:gz", compresslevel=1) as tar:
        for group in selected:
            paths = [Path(root)/"analysis"/c.task_id(group)]
            paths += [Path(root)/"traces"/c.task_id((*group, rung, chain)) for rung in range(len(plan["ladders"][group[1]])) for chain in range(4)]
            for path in paths:
                for ext in (".json", ".npz", ".done.json"):
                    source = path.with_suffix(ext)
                    tar.add(source, arcname="production/"+source.relative_to(root).as_posix())
    return dict(path=archive.name, sha256=c.file_hash(archive), bytes=archive.stat().st_size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=96)
    parser.add_argument("--expected-manifest", required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.out.resolve()
    require(root != output and root not in output.parents, "audit output must be outside production")
    require(not output.exists(), "use a new audit directory")
    output.mkdir(parents=True)
    (output/"archives").mkdir()
    started = time.perf_counter()
    plan = c.read_plan(root)
    require(c.digest(plan) == args.expected_manifest, "manifest differs from submission snapshot")
    require(plan == c.make_plan(), "production manifest differs from fixed scientific plan")
    check_inventory(root/"traces", [c.task_id(t) for t in c.tasks(plan)])
    check_inventory(root/"analysis", [c.task_id(g) for g in c.groups(plan)])
    check_inventory(root/"truth", [str(i) for i in range(3)])
    check_inventory(root/"truth_parts", [f"{i}-{j}" for i in range(3) for j in range(32)])
    truth = c.parallel_map(verify_truth_chunk, [(str(root), plan, i, j) for i in range(3) for j in range(32)], args.workers)
    inventory = [item for t in truth for item in t["inventory"]]
    for code in range(3):
        bank, metadata, inv = checked_artifact(root/"truth"/str(code), dict(manifest=c.digest(plan), code=code, code_identity=c.code_identity(code)))
        pieces = [c.load_artifact(root/"truth_parts"/f"{code}-{j}", dict(manifest=c.digest(plan), code=code, chunk=j, code_identity=c.code_identity(code)))[0] for j in range(32)]
        for key in bank:
            require(np.array_equal(bank[key], np.concatenate([p[key] for p in pieces])), "truth bank merge")
        inventory.extend(inv)
    records = c.parallel_map(audit_group, [(str(root), plan, g) for g in c.groups(plan)], args.workers)
    records.sort(key=lambda r: r["group"])
    rows = [r for record in records for r in record["rows"]]
    require(len(rows) == plan["expected_analysis_rows"], "total analysis count")
    diagnostics = [r for record in records for r in record["diagnostics"]]
    failures = [r for record in records for r in record["trace_failures"]]
    inventory.extend(item for record in records for item in record["inventory"])
    original = json.loads((root/"summary.json").read_text())
    require(original["manifest"] == c.digest(plan), "summary manifest")
    summaries = compare_summaries(rows, original, plan)
    verify_csv(root/"coverage_rows.csv", rows)
    for item in inventory:
        item["path"] = "production/"+Path(item["path"]).relative_to(root).as_posix()
    require(len({x["path"] for x in inventory}) == len(inventory), "duplicate inventory path")
    write_gzip_jsonl(output/"inventory.jsonl.gz", sorted(inventory, key=lambda x: x["path"]))
    write_gzip_jsonl(output/"diagnostics.jsonl.gz", diagnostics)
    write_gzip_jsonl(output/"rows.jsonl.gz", rows)
    c.atomic_json(output/"cohorts.json", dict(manifest=c.digest(plan), summaries=summaries))
    for name in ("manifest.json", "summary.json", "coverage_rows.csv"):
        (output/name).write_bytes((root/name).read_bytes())
    print(json.dumps(dict(phase="verified", traces=plan["expected_tasks"], groups=len(records), rows=len(rows), failures=len(failures))), flush=True)
    archives = c.parallel_map(archive_part, [(str(root), str(output), plan, i) for i in range(96)], args.workers)
    bundle = root.parent.parent
    extra = output/"archives"/"reproduction.tar.gz"
    with tarfile.open(extra, "w:gz", compresslevel=1) as tar:
        for folder in ("truth", "truth_parts", "pbs", "logs"):
            tar.add(root/folder, arcname="production/"+folder)
        for path in root.glob("*.json"):
            tar.add(path, arcname="production/"+path.name)
        tar.add(root/"coverage_rows.csv", arcname="production/coverage_rows.csv")
        for name in ("bundle.tar.gz", "environment.lock.txt", "bundle.json"):
            tar.add(bundle/name, arcname="deployment/"+name)
        tar.add(Path(__file__), arcname="audit_scripts/audit_calibration.py")
    archives.append(dict(path=extra.name, sha256=c.file_hash(extra), bytes=extra.stat().st_size))
    c.atomic_json(output/"archives.json", sorted(archives, key=lambda x: x["path"]))
    c.atomic_json(output/"audit.json", dict(status="verified", manifest=c.digest(plan), audit_script_sha256=c.file_hash(__file__),
        traces=plan["expected_tasks"], groups=len(records), rows=len(rows), inventory_files=len(inventory),
        full_steps=plan["expected_tasks"]*plan["steps"], trace_failures=failures,
        unavailable_intervals=sum(not r["available"] for r in rows),
        public_failure_states_checked=sum(t["states"] for t in truth), diagnostics=len(diagnostics),
        archives=len(archives), archive_bytes=sum(x["bytes"] for x in archives), elapsed_seconds=time.perf_counter()-started,
        warning="Post-hoc R-hat/ESS screens do not prove convergence. Compact traces do not retain full physical states.",
        outputs={p.name: c.file_hash(p) for p in output.iterdir() if p.is_file()}))
    print((output/"audit.json").read_text(), flush=True)


if __name__ == "__main__":
    main()
