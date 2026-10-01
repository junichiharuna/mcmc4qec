"""Audit and describe all predeclared twenty-seed BAR protocol cohorts."""

import csv
import json
import math
from pathlib import Path

import numpy as np


BASE = Path(__file__).resolve().parent
CACHE = json.loads((BASE / "truth_cache.json").read_text(encoding="utf-8"))
SEEDS = list(range(2026, 2046))
REGIONS = {"dev4": (0.30, 0.26, 0.22),
           "paper": (0.10, 0.07, 0.05, 0.03)}
PROTOCOLS = ("default_block", "default_cross", "paper16", "paper50")


def exact(p):
    n = CACHE["n"]
    return math.fsum(count * p**w * (1-p)**(n-w)
                     for w, count in enumerate(CACHE["failure_weight_counts"]))


def read(region, protocol, anchor):
    path = BASE / "protocol" / "raw" / f"{region}_{protocol}_{anchor}_2026_20_runs.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rows.sort(key=lambda row: int(row["seed"]))
    assert [int(row["seed"]) for row in rows] == SEEDS, path
    assert {row["truth_cache_source_sha256"] for row in rows} == {
        CACHE["package_source_sha256"]}, path
    assert {row["problem_sha256"] for row in rows} == {
        CACHE["problem_sha256"]}, path
    assert {row["truth_source"] for row in rows} == {"checked_weight_cache"}, path
    assert {row["bootstrap_replicates"] for row in rows} == {"30"}, path
    assert {row["block"] for row in rows} == {"8"}, path
    assert {row["anchor_trials"] for row in rows} == {"1500"}, path
    assert {row["auxiliary_start"] for row in rows} == {"True"}, path
    assert all(math.isclose(float(row["exact"]), exact(REGIONS[region][-1]),
                            abs_tol=1e-12) for row in rows), path
    expected_chains = 4 if protocol.startswith("default") else int(protocol[5:])
    expected_samples = 600 if protocol.startswith("default") else 250
    expected_lazy = .05 if protocol.startswith("default") else 0
    assert {row["chains"] for row in rows} == {str(expected_chains)}, path
    assert {row["samples"] for row in rows} == {str(expected_samples)}, path
    assert {float(row["lazy"]) for row in rows} == {expected_lazy}, path
    return rows


def stats(values):
    return {"mean": float(np.mean(values)),
            "sd": float(np.std(values, ddof=1)),
            "se": float(np.std(values, ddof=1) / math.sqrt(len(values)))}


def cuts(rows):
    all_cuts = [int(cut) for row in rows for rung in row["cuts"].split("/")
                for cut in rung.split(",")]
    retained = [250 - cut for cut in all_cuts]
    return {"chain_rung_count": len(all_cuts),
            "cut_min": min(all_cuts), "cut_median": float(np.median(all_cuts)),
            "cut_max": max(all_cuts),
            "retained_min": min(retained),
            "retained_median": float(np.median(retained)),
            "retained_max": max(retained),
            "half_trace_cap_chains": sum(cut == 125 for cut in all_cuts),
            "half_trace_cap_chain_fraction": sum(cut == 125 for cut in all_cuts) / len(all_cuts),
            "seeds_with_any_cap": sum(row["burn_capped"] == "True" for row in rows)}


def main():
    cohorts = {(region, protocol, anchor): read(region, protocol, anchor)
               for region in REGIONS for protocol in PROTOCOLS
               for anchor in (("mc",) if region == "dev4" else ("mc", "exact"))}
    assert len(cohorts) == 12
    for region in REGIONS:
        block = cohorts[(region, "default_block", "mc")]
        cross = cohorts[(region, "default_cross", "mc")]
        for a, b in zip(block, cross):
            for field in ("estimate", "ratios", "cuts", "scaling", "drift",
                          "multistart", "dispersion", "auxiliary_four_rule_pass"):
                assert a[field] == b[field], (region, field, a["seed"])
        for protocol in PROTOCOLS:
            if region == "dev4":
                continue
            mc = cohorts[(region, protocol, "mc")]
            anchored = cohorts[(region, protocol, "exact")]
            for a, b in zip(mc, anchored):
                for field in ("ratios", "cuts", "scaling", "drift", "multistart",
                              "dispersion", "auxiliary_four_rule_pass",
                              "paper_vacuous_pass", "four_rule_pass", "burn_capped"):
                    assert a[field] == b[field], (region, protocol, field, a["seed"])
        short = cohorts[(region, "paper16", "mc")]
        long = cohorts[(region, "paper50", "mc")]
        for a, b in zip(short, long):
            for short_rung, long_rung in zip(a["cuts"].split("/"), b["cuts"].split("/")):
                assert short_rung.split(",") == long_rung.split(",")[:16], (region, a["seed"])
    result = {"source_commit": "05c70056e3cac6e9a92592daa6b186d86ceed773",
              "package_source_sha256": CACHE["package_source_sha256"],
              "n_cohorts": len(cohorts), "n_seed_rows": 20 * len(cohorts),
              "exact_truth": {region: exact(ladder[-1]) for region, ladder in REGIONS.items()},
              "cohorts": {}}
    for (region, protocol, anchor), rows in cohorts.items():
        values = np.array([float(row["estimate"]) for row in rows])
        truth = exact(REGIONS[region][-1])
        entry = {"estimate": stats(values), "bias": stats(values-truth),
                 "coverage": sum(row["covered"] == "True" for row in rows),
                 "valid_intervals": sum(row["low"] != "" for row in rows),
                 "mean_width": float(np.mean([float(row["high"])-float(row["low"])
                                         for row in rows if row["low"] != ""])),
                 "formal_four_rule_pass": sum(row["four_rule_pass"] == "True" for row in rows),
                 "formal_four_rule_unresolved": sum(row["four_rule_pass"] in ("", "None") for row in rows),
                 "vacuous_three_rule_pass": sum(row["paper_vacuous_pass"] == "True" for row in rows),
                 "auxiliary_four_rule_pass": sum(row["auxiliary_four_rule_pass"] == "True" for row in rows),
                 "seed2026_estimate": float(values[0])}
        if protocol.startswith("paper"):
            entry["burn"] = cuts(rows)
        result["cohorts"][f"{region}/{protocol}/{anchor}"] = entry
    target = BASE / "protocol" / "protocol_derived.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
