"""Summarize audited fixed cohorts, retaining unavailable and flagged replicates.

Only compact postprocessing is performed here; no new sampling or bootstrap.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import json
import math
from pathlib import Path
import statistics


def records(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite_quantiles(values):
    values = sorted(v for v in values if v is not None and math.isfinite(v))
    if not values:
        return None, None, None
    # Explicit nearest-rank quantiles, no hidden interpolation convention.
    return tuple(values[max(0, math.ceil(len(values)*q)-1)] for q in (.5, .9, .99))


def summarize(root, output):
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    audit = json.loads((root/"audit.json").read_text())
    if audit["status"] != "verified":
        raise ValueError("completed audit required")
    grouped_diag, windows = {}, {}
    for d in records(root/"diagnostics.jsonl.gz"):
        key = tuple(d[k] for k in ("code", "ladder", "init", "burn", "samples", "rung", "p", "observable"))
        grouped_diag.setdefault(key, []).append(d)
        window = (*d["group"], d["burn"], d["samples"])
        flags = windows.setdefault(window, dict(flagged=False, undefined=False, high_rhat=False, low_ess=False))
        for flag in flags:
            flags[flag] |= d[flag]
    diagnostics = []
    for key, rows in sorted(grouped_diag.items()):
        result = dict(zip(("code", "ladder", "init", "burn", "samples", "rung", "p", "observable"), key))
        result.update(replicates=len(rows), structural_constant=sum(r["structural_constant"] for r in rows),
                      flagged=sum(r["flagged"] for r in rows), undefined=sum(r["undefined"] for r in rows),
                      rhat_gt_1_01=sum(r["high_rhat"] for r in rows),
                      rhat_gt_1_1=sum(r["rhat"] is not None and r["rhat"] > 1.1 and not r["structural_constant"] for r in rows),
                      min_ess_lt_100=sum(r["low_ess"] for r in rows))
        for metric in ("rhat", "min_chain_ess", "max_chain_iat"):
            for label, value in zip(("median", "q90", "q99"), finite_quantiles(r[metric] for r in rows if not r["structural_constant"])):
                result[metric+"_"+label] = value
        errors = [r["mean_error"] for r in rows if r["mean_error"] is not None]
        result.update(exact_mean=rows[0]["exact_mean"], mean_bias=statistics.mean(errors) if errors else None,
                      mean_rmse=math.sqrt(statistics.mean(e*e for e in errors)) if errors else None,
                      mean_bias_se=statistics.stdev(errors)/math.sqrt(len(errors)) if len(errors)>1 else None)
        diagnostics.append(result)
    write_csv(output/"mixing_summary.csv", diagnostics)
    grouped = {}
    for r in records(root/"rows.jsonl.gz"):
        key = tuple(r[k] for k in ("code", "ladder", "init", "burn", "samples", "method", "block"))
        r["screen"] = windows.get((*r["group"], r["burn"], r["samples"]), dict(flagged=True, undefined=True, high_rhat=False, low_ess=False))
        grouped.setdefault(key, []).append(r)
    initial = json.loads((root/"cohorts.json").read_text())["summaries"]
    coverage = []
    for old in initial:
        key = tuple(old["condition"])
        rows = grouped[key]
        result = dict(zip(("code", "ladder", "init", "burn", "samples", "method", "block"), key))
        result.update({k: v for k, v in old.items() if k not in ("condition", "wilson")})
        result.update(wilson_low=old["wilson"][0], wilson_high=old["wilson"][1])
        errors = [r["estimate"]-r["truth"] for r in rows if r["estimate"] is not None]
        logs = [r["log_estimate"] for r in rows if r.get("log_estimate") is not None]
        se = [r["log_se"] for r in rows if r["available"]]
        result.update(bias_se=statistics.stdev(errors)/math.sqrt(len(errors)) if len(errors)>1 else None,
                      empirical_log_sd=statistics.stdev(logs) if len(logs)>1 else None,
                      rms_log_se=math.sqrt(statistics.mean(x*x for x in se)) if se else None,
                      zero_log_se=sum(r.get("log_se") == 0 for r in rows))
        result["se_to_empirical_sd"] = (result["rms_log_se"]/result["empirical_log_sd"]
                                        if result["rms_log_se"] is not None and result["empirical_log_sd"] else None)
        for flag in ("flagged", "undefined", "high_rhat", "low_ess"):
            result[flag+"_replicates"] = sum(r["screen"][flag] for r in rows)
        for label, flagged in (("screen_flagged", True), ("screen_unflagged", False)):
            subset = [r for r in rows if r["screen"]["flagged"] == flagged]
            result[label+"_count"] = len(subset)
            result[label+"_coverage"] = sum(r["covered"] for r in subset)/len(subset) if subset else None
        coverage.append(result)
    write_csv(output/"coverage_summary.csv", coverage)
    # Paired comparisons for windows/methods share saved traces; initialization
    # cohorts use distinct RNG streams, so their pairing is only by replicate ID.
    contrasts = []
    for key, rows in grouped.items():
        code, ladder, init, burn, samples, method, block = key
        comparisons = []
        if method == "block":
            comparisons.append(("method_vs_cross_chain", (code, ladder, init, burn, samples, "cross_chain", None)))
        if burn == 6000:
            comparisons.append(("burn_6000_minus_600", (code, ladder, init, 600, samples, method, block)))
        if samples != 600:
            base_samples = 600 if samples == 6000 else 6000
            target = (code, ladder, init, burn, base_samples, method, block)
            if target in grouped:
                comparisons.append((f"length_{samples}_minus_{base_samples}", target))
        if init == "dispersed":
            comparisons.append(("dispersed_minus_stationary_independent_streams", (code, ladder, "stationary", burn, samples, method, block)))
        for label, baseline in comparisons:
            base = {r["replicate"]: r for r in grouped[baseline]}
            differences = [int(r["covered"])-int(base[r["replicate"]]["covered"]) for r in rows]
            points = [(r["estimate"]-base[r["replicate"]]["estimate"])/r["truth"] for r in rows
                      if r["estimate"] is not None and base[r["replicate"]]["estimate"] is not None]
            entry = dict(zip(("code", "ladder", "init", "burn", "samples", "method", "block"), key))
            entry.update(contrast=label, denominator=len(differences), coverage_difference=statistics.mean(differences),
                         coverage_difference_se=statistics.stdev(differences)/math.sqrt(len(differences)) if len(differences)>1 else None,
                         relative_point_difference=statistics.mean(points) if points else None,
                         relative_point_difference_se=statistics.stdev(points)/math.sqrt(len(points)) if len(points)>1 else None)
            contrasts.append(entry)
    write_csv(output/"paired_comparisons.csv", contrasts)
    metadata = dict(manifest=audit["manifest"], coverage_conditions=len(coverage), mixing_conditions=len(diagnostics),
                    contrasts=len(contrasts), thresholds=dict(rhat=1.01, minimum_chain_ess=100),
                    note="Post-hoc descriptive screens; no replicate removed from primary coverage; no multiplicity-adjusted guarantees.")
    (output/"summary_metadata.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    return coverage


def figures(coverage, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    settings = [("block", 8), ("block", 32), ("block", 128), ("block", 1024), ("cross_chain", None)]
    for init in ("stationary", "dispersed"):
        fig, axes = plt.subplots(3, 2, figsize=(10, 10), sharex=True, sharey=True)
        for i, code in enumerate(("toric3", "surface3", "steane")):
            for ladder in range(2):
                ax = axes[i, ladder]
                for method, block in settings:
                    points = sorted([r for r in coverage if r["code"] == code and r["ladder"] == ladder and
                                     r["init"] == init and r["burn"] == 600 and r["method"] == method and r["block"] == block], key=lambda r: r["samples"])
                    ax.plot([r["samples"] for r in points], [r["coverage"] for r in points], marker="o",
                            label=f"block {block}" if block else "cross-chain")
                ax.axhline(.95, color="black", linestyle="--", linewidth=.8)
                ax.set_xscale("log")
                ax.set_ylim(0, 1.01)
                ax.set_title(f"{code}, target p={'.03' if ladder == 0 else '.0001'}")
                ax.grid(alpha=.2)
                if ladder == 0:
                    ax.set_ylabel("Coverage (192 replicates)")
                if i == 2:
                    ax.set_xlabel("Retained transitions per chain")
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=5)
        fig.suptitle(f"{init} initialization; burn-in 600; four chains")
        fig.tight_layout(rect=(0, .045, 1, .97))
        fig.savefig(Path(output)/f"coverage_{init}.png", dpi=160)
        fig.savefig(Path(output)/f"coverage_{init}.pdf")
        plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--figures", action="store_true")
    args = parser.parse_args()
    coverage = summarize(args.root, args.out)
    if args.figures:
        figures(coverage, args.out)
