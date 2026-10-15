"""Validate fixed cohorts and recompute summaries without sampling or extras."""

import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent
SEEDS = list(range(6100, 6120))
BLOCKS = (8, 32, 128)


def main():
    cache = json.loads((ROOT / "truth_cache.json").read_text(encoding="utf-8"))
    counts = cache["failure_weight_counts"]
    truth = math.fsum(count * .22**w * .78**(18-w)
                      for w, count in enumerate(counts))
    weight_truth = math.fsum(w * count * .22**w * .78**(18-w)
                             for w, count in enumerate(counts)) / truth
    anchor_truth = math.fsum(count * .3**w * .7**(18-w)
                             for w, count in enumerate(counts))
    assert sum(counts) == 196608 and len(counts) == 19
    assert hashlib.sha256(b"".join(c.to_bytes(8, "little", signed=True)
                                  for c in counts)).hexdigest() == cache["counts_sha256"]
    groups, summaries = {}, []
    for block in BLOCKS:
        with (ROOT / f"block{block}_runs.csv").open(newline="", encoding="utf-8") as stream:
            rows = sorted(csv.DictReader(stream), key=lambda row: int(row["seed"]))
        assert [int(row["seed"]) for row in rows] == SEEDS
        groups[block] = rows
        for row in rows:
            expected = dict(scenario="anchor_exact", uncertainty="block_bootstrap",
                            samples="600", burn_in="180", chains="4",
                            block_length=str(block), bootstrap_replicates="100",
                            ladder="0.3/0.26/0.22", anchor_kind="exact",
                            truth_source="checked_weight_cache", bootstrap_successes="100")
            assert all(row[key] == value for key, value in expected.items())
            assert row["problem_sha256"] == cache["problem_sha256"]
            assert row["truth_cache_source_sha256"] == cache["package_source_sha256"]
            assert math.isclose(float(row["exact_estimate"]), truth, rel_tol=0, abs_tol=1e-14)
            assert math.isclose(float(row["exact_conditional_weight"]), weight_truth, rel_tol=0, abs_tol=1e-13)
            assert math.isclose(float(row["anchor_estimate"]), anchor_truth, rel_tol=0, abs_tol=1e-14)
            assert all(math.isfinite(float(row[key])) for key in
                       ("bar_low", "bar_high", "bar_estimate", "bar_width", "max_chain_iat",
                        "target_rhat", "target_ess", "target_chain_weight"))
            assert float(row["bar_low"]) <= float(row["bar_high"])
            covered = float(row["bar_low"]) <= truth <= float(row["bar_high"])
            assert row["bar_covers_exact"] == str(covered)
            assert math.isclose(float(row["bar_width"]),
                                float(row["bar_high"])-float(row["bar_low"]), abs_tol=1e-15)
        values = [float(row["bar_estimate"]) for row in rows]
        widths = [float(row["bar_width"]) for row in rows]
        covered = sum(row["bar_covers_exact"] == "True" for row in rows)
        z, n = 1.959963984540054, len(rows)
        center = (covered/n+z*z/(2*n))/(1+z*z/n)
        half = z*math.sqrt((covered/n)*(1-covered/n)/n+z*z/(4*n*n))/(1+z*z/n)
        summaries.append(dict(block=block, n=n, covered=covered,
                              wilson_low=center-half, wilson_high=center+half,
                              exact=truth, mean=statistics.mean(values),
                              bias=statistics.mean(values)-truth,
                              sd=statistics.stdev(values), se=statistics.stdev(values)/math.sqrt(n),
                              mean_width=statistics.mean(widths),
                              median_max_iat=statistics.median(float(r["max_chain_iat"]) for r in rows),
                              median_target_ess=statistics.median(float(r["target_ess"]) for r in rows),
                              min_target_ess=min(float(r["target_ess"]) for r in rows),
                              max_target_rhat=max(float(r["target_rhat"]) for r in rows),
                              exact_conditional_weight=weight_truth,
                              mean_weight_bias=statistics.mean(float(r["target_chain_weight"]) for r in rows)-weight_truth,
                              min_block_over_max_iat=min(float(r["block_over_max_iat"]) for r in rows)))
    invariant = ("bar_estimate", "target_chain_weight", "target_chain_weight_range",
                 "max_chain_iat", "target_rhat", "target_ess", "mc_estimate", "anchor_estimate")
    for block in BLOCKS[1:]:
        assert all(all(a[key] == b[key] for key in invariant)
                   for a, b in zip(groups[8], groups[block]))
    pairs = []
    for left, right in ((8, 32), (8, 128), (32, 128)):
        diffs = [float(b["bar_width"])-float(a["bar_width"])
                 for a, b in zip(groups[left], groups[right])]
        pairs.append(dict(left=left, right=right, mean_width_difference=statistics.mean(diffs),
                          se_width_difference=statistics.stdev(diffs)/math.sqrt(len(diffs)),
                          gained=sum(a["bar_covers_exact"] == "False" and b["bar_covers_exact"] == "True"
                                     for a, b in zip(groups[left], groups[right])),
                          lost=sum(a["bar_covers_exact"] == "True" and b["bar_covers_exact"] == "False"
                                   for a, b in zip(groups[left], groups[right]))))
    for name, rows in (("summary.csv", summaries), ("paired.csv", pairs)):
        with (ROOT / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps(dict(summary=summaries, paired=pairs), indent=2))


if __name__ == "__main__":
    main()
