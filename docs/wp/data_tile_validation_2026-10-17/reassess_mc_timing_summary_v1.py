"""Reassess the fixed recovered MC summary; no payload scan or simulation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT/"src"), str(ROOT/"cluster_scripts")]
import calibration as c
import tile_timing_metrics as metrics
import tile_precision_assessment as precision
import tile_summary as summary_module
import tile_reference as reference_module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output = DATA/"timing_mc_achieved_precision_v1.json"
    report = DATA/"timing_mc_achieved_precision_v1_ja.md"
    if output.exists() or report.exists(): raise ValueError("preserve existing reassessment")
    cohort = DATA/"mc_timing_main_evidence_v1"
    paths = dict(summary=cohort/"mc-benchmark/summary.json", manifest=cohort/"mc-benchmark/manifest.json",
        budget=cohort/"mc-benchmark/budget.json", reference=DATA/"reference_summary.json",
        reference_audit=DATA/"reference_audit.json", local_verification=cohort/"local_verification.json",
        benchmark_verification=cohort/"benchmark_verification.json", terminal=cohort/"terminal.json",
        preflight=cohort/"mc-benchmark/native_preflight.json", selection=DATA/"bar_timing_selected_settings_v1.json")
    sources = {str(Path(module.__file__).resolve()): sha(module.__file__) for module in
               (c, metrics, precision, summary_module, reference_module)}
    sources[str(Path(__file__).resolve())] = sha(__file__)
    hashes = {key: sha(path) for key, path in paths.items()}
    loaded = {key: json.loads(path.read_bytes()) for key, path in paths.items()}
    plan, saved, budget = loaded["manifest"], loaded["summary"], loaded["budget"]
    local, verified = loaded["local_verification"], loaded["benchmark_verification"]
    if (local["all_files_sha256_match"] is not True or local["summary_sha256"] != hashes["summary"]
            or local["benchmark_verification_sha256"] != hashes["benchmark_verification"]
            or local["terminal_sha256"] != hashes["terminal"]
            or local["native_preflight_sha256"] != hashes["preflight"]
            or verified["full_task_artifacts_metadata_verified"] is not True
            or verified["main_manifest"] != c.digest(plan) or saved["manifest"] != c.digest(plan)
            or plan["purpose"] != "mc_precision_benchmark" or plan["seed_stage"] != 121 or plan["replicates"] != 192
            or saved["tasks"] != 1536 or len(saved["records"]) != 1536
            or budget["reference_sha256"] != hashes["reference"]):
        raise ValueError("fixed recovered MC evidence/reference binding differs")
    audit, terminal = loaded["reference_audit"], loaded["terminal"]
    if (audit["summary_sha256"] != hashes["reference"] or not all(audit.get(key) for key in
        ("all_seeds_verified", "all_problem_metadata_verified", "summary_reproduced"))
            or terminal["job"]["job_state"] != "F" or terminal["job"]["Exit_status"] != 0
            or terminal["job_id"] != verified["job_id"] or terminal["job_id"] != loaded["preflight"]["pbs_job_id"]):
        raise ValueError("saved reference audit or MC terminal differs")
    expected = [(case, epsilon) for case in range(4) for epsilon in (.2, .1)]
    if [(row["case"], row["epsilon"]) for row in plan["conditions"]] != expected:
        raise ValueError("fixed eight conditions required")
    records = []
    for case, epsilon in expected:
        refs = [row for row in loaded["reference"]["records"] if row["case"] == case]
        if len(refs) != 1: raise ValueError("one independent reference per case required")
        ref = refs[0]
        cond = next(row for row in plan["conditions"] if (row["case"], row["epsilon"]) == (case, epsilon))
        if (cond["reference_point"] != ref["estimate"] or cond["reference_interval_999"] != ref["interval_999"]
                or cond["target_p"] != ref["target_p"]): raise ValueError("reference/budget condition differs")
        rows = [row for row in saved["records"] if (row["case"], row["epsilon"]) == (case, epsilon)]
        assessment = metrics.assess("mc", rows, 192, ref, epsilon)
        label = assessment["precision"]["precision"][0]["classification"]
        records.append(dict(case=case, epsilon=epsilon, planned_trials=cond["planned_trials"],
            mc_assessment=assessment, mc_precision_gate=label,
            ratio_eligible_if_future_bar_passes=label == "empirical_within_target",
            current_mc_over_bar_ratio=None, current_ratio_reason="bar_main_evaluation_not_available",
            future_ratio_block_reason=None if label == "empirical_within_target" else "precision_not_confirmed"))
    for key, path in paths.items():
        if sha(path) != hashes[key]: raise ValueError("input changed during reassessment")
    for name, digest in sources.items():
        if sha(name) != digest: raise ValueError("numerical source changed during reassessment")
    result = dict(schema=1, purpose="saved_mc_timing_summary_precision_reassessment", records=records,
        generated_utc=datetime.now(timezone.utc).isoformat(), input_sha256={str(paths[k]): v for k, v in hashes.items()},
        numerical_source_sha256=sources, environment=dict(python=sys.version, executable=sys.executable, platform=platform.platform()),
        mc_execution=dict(job_id=terminal["job_id"], hostname=loaded["preflight"]["hostname"],
            job_phase_wall_seconds=saved["phase_wall_seconds"], sum_task_cpu_seconds=saved["sum_task_cpu_seconds"],
            pbs_resources=terminal["job"]["Resource_List"], pbs_resources_used=terminal["job"]["resources_used"]),
        predeclared_gate="Both complete empirical relative-RMSE upper bounds over the finite reference interval <= epsilon.",
        source_of_precision="Saved 1536-row MC summary; numerical helpers only.",
        raw_payloads_rehashed_here=False, mc_reexecuted=False, native_probe_reexecuted=False,
        bar_main_evaluation_available=False, new_thresholds=False, new_seeds=False, cohort_rows_removed=False,
        population_precision_certified=False, nominal_coverage_certified=False,
        warning="The shared finite 99.9% Wilson reference interval is not a certain truth interval or simultaneous eight-condition guarantee. Empirical cohort RMSE is not population RMSE. Existing accepted artifact audits are cited, not repeated here. No BAR speedup is available.")
    lines = ["# 保存 MC 計時 summary の達成精度確認", "",
        "固定 1536 行だけを既存の精度 helper で再集計し、raw payload の全再読込・MC 再実行・native probe は行っていない。",
        "各条件の予定 192 replicate は全件成功し、区間欠損も 0 件だった。",
        "予定 epsilon と実測相対 RMSE を区別し、閾値変更・seed 追加・cohort 削除は行わない。", "",
        "|case|epsilon|実測相対 RMSE の reference 範囲|既存判定|", "|---|---:|---:|---|"]
    for row in records:
        lo, hi = row["mc_assessment"]["precision"]["relative_rmse_reference_range"]
        lines.append(f"|{row['case']}|{row['epsilon']}|{lo:.9f}–{hi:.9f}|{row['mc_precision_gate']}|")
    lines += ["", "within は 4 条件、above は 2 条件、reference_sensitive は 2 条件である。",
        "BAR main が未評価のため、現段階の全 8 条件の時間比は未取得である。",
        "MC の gate を通らない 4 条件は、今後 BAR が通過しても固定規則上の同精度時間比を null とする。",
        "20%・10%予算の計画式は、有限 reference 範囲を仮定した母 RMSE の式であり、この独立 192 標本の経験的 RMSE 通過を保証しない。",
        "bias・RMSE・参考区間被覆・失敗分母と wall/CPU 費用の全 8 行は timing_mc_achieved_precision_v1.json に保存した。",
        "MC は node011・96 workers、全 8 条件を一つの pool で実行し、phase wall は約 226.898 秒だった。",
        "条件別 task wall/CPU の平均と、全 job の phase wall・PBS wall を混同せず、phase 時間を条件へ按分しない。",
        "有限 reference の不確実性と有限 192 replicate の不確実性を残し、母精度・名目被覆・BAR の速度優位を保証しない。",
        "元 summary、reference、audit、環境、数値 source と実行 script の hash を JSON に記録した。", ""]
    with output.open("xb") as stream: stream.write(c.canonical(result)+b"\n")
    with report.open("x", encoding="utf-8", newline="\n") as stream: stream.write("\n".join(lines))
    print(json.dumps(dict(output=str(output), report=str(report), classifications=[r["mc_precision_gate"] for r in records])))


if __name__ == "__main__": main()
