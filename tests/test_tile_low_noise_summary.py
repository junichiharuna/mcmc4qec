"""Full-cohort low-noise agreement is not accuracy or coverage."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_low_noise_study as low
import tile_low_noise_summary as summary


def fixture_rows():
    plan = low.make_plan(0, 2, capacity=False)
    plan.update(replicates=2, burns=[0], blocks=[2])
    plan["condition"].update(chains=4, steps=8, windows=[8], rungs=[.1, .001], coarse=[.1, .001])
    rows = []
    for key in summary.expected_conditions(plan):
        for rep in range(2):
            row = dict(zip(summary.CONDITION, key))
            row.update(group=[0, 2, list(plan["kernels"]).index(row["kernel"]),
                              plan["initializations"].index(row["init"]), rep],
                       replicate=rep, target_p=.001, noise="bit", n=72,
                       estimate=.01*(rep+1), interval=[.001, .04], available=True,
                       flagged=False, undefined=False, high_rhat=False, low_ess=False,
                       failure=None, reference=None, reference_available=False)
            rows.append(row)
    return plan, rows


def test_all_conditions_and_pairs_have_full_denominator_without_reference():
    plan, rows = fixture_rows()
    result = summary.summarize_rows(plan, rows)
    assert result["rows"] == 32 and len(result["conditions"]) == 16
    assert result["reference_available"] is False
    assert result["nominal_coverage_certified"] is False
    assert len(result["paired_comparisons"]) > 0
    for condition in result["conditions"]:
        assert condition["metrics"]["replicates"] == 2
        assert condition["metrics"]["bias_reference_range"] is None
        assert condition["metrics"]["coverage_reference_entire"] is None
        assert condition["point_mean"] == pytest.approx(.015)
    for pair in result["paired_comparisons"]:
        assert pair["replicates"] == pair["point_pairs"] == pair["interval_pairs"] == 2
        assert pair["mean_estimate_difference"] == 0


@pytest.mark.parametrize("change", ["missing", "duplicate", "group", "target", "noise", "n", "setting", "reference"])
def test_missing_or_misidentified_row_is_not_an_estimation_failure(change):
    plan, rows = fixture_rows()
    if change == "missing": rows.pop()
    elif change == "duplicate": rows[-1] = deepcopy(rows[0])
    elif change == "group": rows[0]["group"][1] = 1
    elif change == "target": rows[0]["target_p"] = .003
    elif change == "noise": rows[0]["noise"] = "depolarizing"
    elif change == "n": rows[0]["n"] = 288
    elif change == "setting": rows[0]["burn"] = 123
    else: rows[0]["reference"] = .01
    with pytest.raises(ValueError): summary.summarize_rows(plan, rows)


def test_failed_or_undefined_rows_remain_in_counts_and_pairs():
    plan, rows = fixture_rows()
    rows[0].update(estimate=None, interval=None, available=False, failure="sampling_failed",
                   flagged=True, undefined=True)
    result = summary.summarize_rows(plan, rows)
    first = result["conditions"][0]
    assert first["metrics"]["replicates"] == 2
    assert first["metrics"]["unavailable_intervals"] == first["metrics"]["undefined"] == 1
    assert first["point_mean"] is None
    assert first["available_only_point_mean"] == .02
    incomplete = [p for p in result["paired_comparisons"] if p["point_pairs"] == 1]
    assert incomplete and all(p["mean_estimate_difference"] is None for p in incomplete)
    assert all(p["replicates"] == 2 for p in incomplete)


def test_zero_points_and_disjoint_intervals_have_explicit_pair_denominators():
    _, rows = fixture_rows()
    left, right = deepcopy(rows[:2]), deepcopy(rows[:2])
    left[0].update(estimate=0., interval=[0., .001])
    right[0].update(estimate=.1, interval=[.09, .11])
    out = summary.paired_agreement(left, right, 2)
    assert out["point_pairs"] == 2 and out["positive_point_pairs"] == 1
    assert out["mean_log_ratio"] is None
    assert out["disjoint_intervals"] == 1 and out["interval_pairs"] == 2
    assert out["mean_estimate_difference"] == pytest.approx(.05)


def test_paired_difference_is_signed_right_minus_left():
    _, rows = fixture_rows()
    left, right = deepcopy(rows[:2]), deepcopy(rows[:2])
    for row in right: row["estimate"] *= 2
    out = summary.paired_agreement(left, right, 2)
    assert out["mean_estimate_difference"] == pytest.approx(.015)
    assert out["difference_direction"] == "right-minus-left"
    assert out["log_ratio_direction"] == "log(right)-log(left)"
    assert out["estimate_difference_standard_error"] == pytest.approx(.005)
    import math
    assert out["mean_log_ratio"] == pytest.approx(math.log(2))


def test_summary_cli_consumes_validated_collection_and_binds_evidence(tmp_path, monkeypatch):
    import types
    import json
    import calibration as c
    plan, rows = fixture_rows()
    collection = dict(rows=len(rows), analysis="mock-context", rows_sha256="mock-row-hash")
    fake = types.SimpleNamespace(read_collection=lambda root: (plan, iter(rows), collection))
    monkeypatch.setitem(sys.modules, "tile_low_noise_analysis_partitions", fake)
    output = tmp_path/"summary.json"
    result = summary.run(tmp_path, output)
    assert json.loads(output.read_text())["collection"] == c.digest(collection)
    assert result["collected_artifacts_validated"] is True
    assert result["full_trace_redecoded"] is False
    with pytest.raises(ValueError, match="output exists"):
        summary.run(tmp_path, output)


@pytest.mark.parametrize("change", ["final_iterator_check", "count"])
def test_cli_does_not_publish_before_collection_validation_finishes(tmp_path, monkeypatch, change):
    import types
    plan, rows = fixture_rows()
    def read():
        yield from rows
        if change == "final_iterator_check":
            raise ValueError("final collection check failed")
    collection = dict(rows=len(rows)+(1 if change == "count" else 0))
    monkeypatch.setitem(sys.modules, "tile_low_noise_analysis_partitions",
                        types.SimpleNamespace(read_collection=lambda root: (plan, read(), collection)))
    output = tmp_path/"summary.json"
    with pytest.raises(ValueError): summary.run(tmp_path, output)
    assert not output.exists()


def test_actual_collection_reader_and_summary_keep_all_192_replicates(tmp_path, monkeypatch):
    """Mock execution evidence upstream; exercise real collect/read/summary APIs."""
    import tile_low_noise_analysis_partitions as partitions
    import tile_low_noise_analysis as analysis
    plan, templates = fixture_rows()
    plan["replicates"] = 192
    groups = list(analysis.groups(plan))
    wrapper = dict(production=plan, analysis_context={"mock": True},
                   resources=dict(partitions=[dict(index=0, groups=[list(g) for g in groups])]))
    monkeypatch.setattr(partitions, "read_plan", lambda root: wrapper)
    monkeypatch.setattr(partitions, "partition_evidence", lambda *args: ({}, "mock-proof"))
    def records(*args):
        for group in groups:
            rows = []
            for original in templates:
                if original["group"][2:5] == [group[2], group[3], 0]:
                    row = deepcopy(original)
                    row.update(group=list(group), replicate=group[4])
                    rows.append(row)
            yield dict(rows=rows, failed_tasks=[]), 0, "mock-proof"
    monkeypatch.setattr(partitions, "validated_groups", records)
    collected = partitions.collect(tmp_path)
    output = summary.run(tmp_path, tmp_path/"descriptive.json")
    assert collected["groups"] == 768
    assert output["rows"] == 3072
    assert all(condition["metrics"]["replicates"] == 192 for condition in output["conditions"])
