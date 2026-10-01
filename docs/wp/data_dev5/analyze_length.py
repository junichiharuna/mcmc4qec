"""Audit the predeclared twenty-seed length cohort without resampling."""

import csv
import json
import math
from pathlib import Path

import numpy as np


BASE = Path(__file__).resolve().parent
TRUTH = json.loads((BASE / "truth_cache.json").read_text(encoding="utf-8"))
COUNTS = TRUTH["failure_weight_counts"]
N = TRUTH["n"]
SEEDS = list(range(2026, 2046))


def truth(p):
    return math.fsum(count * p**w * (1-p)**(N-w)
                     for w, count in enumerate(COUNTS))


def read_length(length):
    rows = []
    for path in sorted((BASE / "length" / "raw").glob(
            f"baseline_{length}_*_runs.csv")):
        with path.open(newline="", encoding="utf-8") as stream:
            rows.extend(csv.DictReader(stream))
    rows.sort(key=lambda row: int(row["seed"]))
    assert [int(row["seed"]) for row in rows] == SEEDS, length
    assert {row["truth_cache_source_sha256"] for row in rows} == {
        TRUTH["package_source_sha256"]}, length
    assert {row["bootstrap_replicates"] for row in rows} == {"30"}, length
    assert {row["block_length"] for row in rows} == {"8"}, length
    assert {row["burn_in"] for row in rows} == {"180"}, length
    assert {row["chains"] for row in rows} == {"4"}, length
    exact = truth(.22)
    assert all(math.isclose(float(row["exact_estimate"]), exact,
                            abs_tol=1e-12) for row in rows), length
    return rows


def measures(rows):
    estimate = np.array([float(row["bar_estimate"]) for row in rows])
    anchor = np.array([float(row["anchor_estimate"]) for row in rows])
    log_ratio = np.log(estimate / anchor)
    exact_reanchored = truth(.30) * np.exp(log_ratio)
    return estimate, anchor, log_ratio, exact_reanchored


def stats(values):
    return {"mean": float(np.mean(values)),
            "sd": float(np.std(values, ddof=1)),
            "se": float(np.std(values, ddof=1) / math.sqrt(len(values)))}


def main():
    data = {length: read_length(length) for length in (600, 2400, 9600)}
    metrics = {length: measures(rows) for length, rows in data.items()}
    for index in range(20):
        assert len({metrics[length][1][index] for length in metrics}) == 1
    summary = {"source_commit": "05c70056e3cac6e9a92592daa6b186d86ceed773",
               "package_source_sha256": TRUTH["package_source_sha256"],
               "n_seeds": 20, "seed_min": 2026, "seed_max": 2045,
               "exact_target": truth(.22), "exact_anchor": truth(.30),
               "lengths": {}, "paired_differences": {}}
    for length, (estimate, anchor, log_ratio, reanchored) in metrics.items():
        rows = data[length]
        ratio = np.exp(log_ratio)
        anchor_contribution = (anchor - truth(.30)) * ratio
        summary["lengths"][str(length)] = {
            "mc_estimate": stats(estimate),
            "mc_bias": stats(estimate - truth(.22)),
            "exact_reanchored_estimate": stats(reanchored),
            "exact_reanchored_bias": stats(reanchored - truth(.22)),
            "log_ratio": stats(log_ratio),
            "anchor": stats(anchor),
            "anchor_ratio_sample_covariance": float(np.cov(anchor, ratio, ddof=1)[0, 1]),
            "anchor_ratio_sample_correlation": float(np.corrcoef(anchor, ratio)[0, 1]),
            "anchor_contribution": stats(anchor_contribution),
            "sample_variance_components": {
                "exact_reanchored": float(np.var(reanchored, ddof=1)),
                "anchor_contribution": float(np.var(anchor_contribution, ddof=1)),
                "twice_covariance": float(2 * np.cov(reanchored, anchor_contribution, ddof=1)[0, 1]),
                "mc_point_total": float(np.var(estimate, ddof=1)),
            },
            "bar_covered": sum(row["bar_covers_exact"] == "True" for row in rows),
            "seed2026_mc_estimate": float(estimate[0]),
            "seed2026_exact_reanchored": float(reanchored[0]),
        }
    for earlier, later in ((600, 2400), (600, 9600), (2400, 9600)):
        old, new = metrics[earlier], metrics[later]
        summary["paired_differences"][f"{later}-{earlier}"] = {
            "mc_estimate": stats(new[0] - old[0]),
            "exact_reanchored_estimate": stats(new[3] - old[3]),
            "log_ratio": stats(new[2] - old[2]),
        }
    target = BASE / "length" / "length_derived.json"
    target.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
