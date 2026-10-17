"""Finite acceptance of the completion audit, including deliberate corruption."""
from pathlib import Path
import sys

import numpy as np
import pytest

for module in ("pymatching", "ldpc", "bposd"):
    pytest.importorskip(module)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import audit_calibration as a


def test_inventory_rejects_missing_extra_and_incomplete(tmp_path):
    c.save_artifact(tmp_path/"0", {"id": 0}, {}, {"status": "ok"})
    a.check_inventory(tmp_path, ["0"])
    with pytest.raises(ValueError, match="inventory"):
        a.check_inventory(tmp_path, ["0", "1"])
    (tmp_path/"unexpected.tmp").write_text("incomplete")
    with pytest.raises(ValueError, match="inventory"):
        a.check_inventory(tmp_path, ["0"])


def test_marker_must_certify_both_payloads(tmp_path):
    c.save_artifact(tmp_path/"0", {"id": 0}, {}, {"status": "ok"})
    p = tmp_path/"0.done.json"
    import json
    marker = json.loads(p.read_text())
    del marker["sha256"][".npz"]
    c.atomic_json(p, marker)
    with pytest.raises(ValueError, match="both"):
        a.checked_artifact(tmp_path/"0", {"id": 0})


def test_structural_constants_are_distinct_from_stuck_chains():
    diag = dict(rhat=None, chain_ess=[None]*4, chain_iat=[None]*4)
    assert a.screen_diagnostic(diag, 0)["structural_constant"]
    assert not a.screen_diagnostic(diag, 0)["flagged"]
    assert a.screen_diagnostic(diag, 1)["undefined"]
    assert a.screen_diagnostic(diag, 1)["flagged"]
    good = dict(rhat=1.001, chain_ess=[1000]*4, chain_iat=[10]*4)
    assert not a.screen_diagnostic(good, 1)["flagged"]
    assert a.screen_diagnostic(dict(good, rhat=1.2), 1)["flagged"]


def test_row_algebra_rejects_wrong_coverage_and_covariance():
    ws = [np.random.default_rng(i).integers(1, 4, (4, 32)) for i in range(4)]
    ladder = [.1, .07, .05, .03]
    record = c.estimate_window(ws, 7, ladder, .13, block=None, replicates=8, rng=np.random.default_rng(1))
    truth = record["estimate"]
    row = dict(record, truth=truth, available=True, covered=True)
    a.verify_row(row, ws, 7, ladder, .13, truth)
    with pytest.raises(ValueError, match="covered"):
        a.verify_row(dict(row, covered=False), ws, 7, ladder, .13, truth)
    with pytest.raises(ValueError, match="covariance"):
        a.verify_row(dict(row, covariance=-np.eye(3)), ws, 7, ladder, .13, truth)


def test_independent_cohort_summary_keeps_unavailable_in_denominator():
    rows = [dict(estimate=1., truth=1., available=True, covered=True, interval=[.8,1.2], log_se=.2),
            dict(estimate=2., truth=1., available=True, covered=False, interval=[1.8,2.2], log_se=.1),
            dict(estimate=None, truth=1., available=False, covered=False, interval=None)]
    result = a.cohort_summary(rows)
    assert result["denominator"] == 3
    assert result["coverage"] == 1/3
    assert result["conditional_coverage"] == 1/2
    assert result["bias"] == .5
    assert result["rmse"] == pytest.approx(np.sqrt(.5))


def test_complete_small_group_and_exact_constant_classification(tmp_path):
    plan = c.make_plan(smoke=True)
    plan.update(steps=48, windows=[32], burns=[8], blocks=[8], bootstrap_replicates=4)
    bank = c.enumerate_bank(2)
    c.save_artifact(tmp_path/"truth"/"2", dict(manifest=c.digest(plan), code=2, code_identity=c.code_identity(2)), bank, {"status": "ok"})
    group = (2, 0, 0, 0)
    for rung, chain in __import__("itertools").product(range(4), range(4)):
        assert c.sample_task((str(tmp_path), plan, (*group, rung, chain)))["status"] == "ok"
    c.analyze_group((str(tmp_path), plan, group))
    result = a.audit_group((str(tmp_path), plan, group))
    assert len(result["rows"]) == 2 and not result["trace_failures"]
    assert len(result["inventory"]) == 51
    assert all(d["structural_constant"] and not d["flagged"] for d in result["diagnostics"] if d["observable"] == "logical_bit_0")
    import summarize_calibration as summary
    report = tmp_path/"report"
    report.mkdir()
    c.atomic_json(report/"audit.json", dict(status="verified", manifest=c.digest(plan)))
    a.write_gzip_jsonl(report/"rows.jsonl.gz", result["rows"])
    a.write_gzip_jsonl(report/"diagnostics.jsonl.gz", result["diagnostics"])
    cohorts = []
    for row in result["rows"]:
        cohort = a.cohort_summary([row])
        cohort.update(condition=[row[k] for k in ("code", "ladder", "init", "burn", "samples", "method", "block")],
                      truth=row["truth"], target_p=.03, relative_bias=cohort["bias"]/row["truth"], relative_rmse=cohort["rmse"]/row["truth"])
        cohorts.append(cohort)
    c.atomic_json(report/"cohorts.json", dict(summaries=cohorts))
    summarized = summary.summarize(report, tmp_path/"tables")
    assert len(summarized) == 2
    assert all(r["denominator"] == 1 for r in summarized)
