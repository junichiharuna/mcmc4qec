"""Check the final report against recovered rows; do not rerun sampling."""
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parent
RESULTS = DATA / "results"
RECOVERED = ROOT / "output/cluster_results/20261017-calibration"
REPORT = ROOT / "docs/wp/calibration_results_2026-10-17_ja.md"


def sha(path):
    return hashlib.file_digest(Path(path).open("rb"), "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    audit, recovery = read(RESULTS/"audit.json"), read(RESULTS/"recovery.json")
    assert audit["status"] == recovery["status"] == "verified"
    assert audit["traces"] == 46080 and audit["rows"] == 64512
    assert audit["groups"] == 2304 and not audit["trace_failures"]
    assert audit["unavailable_intervals"] == 0
    assert recovery["payloads"] == audit["inventory_files"] == 145449
    assert sha(RESULTS/"audit.json") == recovery["remote_audit_sha256"]
    for name, expected in audit["outputs"].items():
        assert sha(RECOVERED/name) == expected, name
    for name in ("audit.json", "recovery.json", "archives.json", "inventory.jsonl.gz"):
        assert sha(RESULTS/name) == sha(RECOVERED/name), name
    archive_records = read(RESULTS/"archives.json")
    assert len(archive_records) == 97
    assert sum(r["bytes"] for r in archive_records) == 1636106601
    for r in archive_records:
        assert (RECOVERED/"archives"/r["path"]).stat().st_size == r["bytes"]
    payload = gzip.decompress((RESULTS/"coverage_rows.csv.gz").read_bytes())
    assert hashlib.sha256(payload).hexdigest() == audit["outputs"]["coverage_rows.csv"]
    rows = list(csv.DictReader(io.StringIO(payload.decode())))
    assert len(rows) == 64512
    fields = ("code", "ladder", "init", "burn", "samples", "method", "block")
    grouped = {}
    for r in rows:
        assert r["available"] == "True" and not r["failure"]
        grouped.setdefault(tuple(r[k] for k in fields), []).append(r)
    summaries = list(csv.DictReader((RESULTS/"coverage_summary.csv").open(encoding="utf-8")))
    assert len(summaries) == len(grouped) == 336
    for s in summaries:
        members = grouped[tuple(s[k] for k in fields)]
        assert len(members) == 192 == int(s["denominator"])
        assert {int(r["replicate"]) for r in members} == set(range(192))
        assert sum(r["covered"] == "True" for r in members) == int(s["covered"])
        errors = [float(r["estimate"])-float(r["truth"]) for r in members]
        for key, value in (("bias", sum(errors)/192), ("rmse", math.sqrt(sum(e*e for e in errors)/192))):
            assert math.isclose(float(s[key]), value, rel_tol=1e-9, abs_tol=1e-18), (key, s)
    def select(code, ladder, init, burn, samples, method="block", block="128"):
        return next(s for s in summaries if tuple(s[k] for k in fields) ==
                    (code, str(ladder), init, str(burn), str(samples), method, block))
    long = ["| 符号 | target p | 初期化 | 相対bias% | 相対RMSE% | block128被覆 | cross-chain被覆 | screen/192 |",
            "|---|---:|---|---:|---:|---:|---:|---:|"]
    lengths = ["| 符号 | target p | 保存600 | 保存6,000 | 保存60,000 |", "|---|---:|---|---|---|"]
    for code in ("toric3", "surface3", "steane"):
        for ladder in (0, 1):
            for init in ("stationary", "dispersed"):
                s = select(code, ladder, init, 6000, 60000)
                x = select(code, ladder, init, 6000, 60000, "cross_chain", "")
                long.append(f'| {code} | {s["target_p"]} | {init} | {100*float(s["relative_bias"]):.6f} | '
                            f'{100*float(s["relative_rmse"]):.6f} | {s["covered"]}/192 | {x["covered"]}/192 | {s["flagged_replicates"]} |')
            cells = []
            for n in (600, 6000, 60000):
                s = select(code, ladder, "stationary", 600, n)
                cells.append(f'{s["covered"]}/192；{100*float(s["relative_rmse"]):.4f}%')
            lengths.append(f'| {code} | {s["target_p"]} | '+" | ".join(cells)+" |")
    report = REPORT.read_text(encoding="utf-8")
    for marker, table in (("LONG_TABLE", long), ("LENGTH_TABLE", lengths)):
        text = "\n".join(table)
        # First finalization fills placeholders; subsequent runs only verify.
        if f"<!-- {marker} -->" in report:
            report = report.replace(f"<!-- {marker} -->", text)
        assert text in report, f"report table changed: {marker}"
    REPORT.write_text(report, encoding="utf-8")
    assert "16 passed in 13.02s" in (DATA/"completion_tests.log").read_text(encoding="utf-8-sig")
    status = (DATA/"cluster_completion_status.txt").read_text(encoding="utf-8-sig")
    assert status.count("job_state = F") == status.count("Exit_status = 0") == 8
    bundle = read(DATA/"cluster_bundle.json")
    for name in ("cluster_scripts/calibration.py", "dist/mcmc4qec-0.1.0.dev5-py3-none-any.whl"):
        assert sha(ROOT/name) == bundle["files"][name]
        assert bundle["files"][name] in status
    git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", bundle["base_commit"], "HEAD"], cwd=ROOT, check=True)
    assert not git("diff", bundle["base_commit"], "--", "src/mcmc4qec/sampling.py", "src/mcmc4qec/kernels.py", "src/mcmc4qec/estimation.py")
    assert not git("-C", "A:/dev/RIMC", "status", "--short")
    handoff = ROOT/"docs/handoff/IMPLEMENTATION_STATUS.md"
    old = subprocess.check_output(["git", "show", bundle["base_commit"]+":docs/handoff/IMPLEMENTATION_STATUS.md"], cwd=ROOT).decode()
    assert handoff.read_text(encoding="utf-8").startswith(old.replace("\r\n", "\n"))
    pages = [REPORT, DATA/"README.md", ROOT/"docs/api_en.md", ROOT/"docs/wp/tile_cluster_report_2026-10-17_ja.md",
             ROOT/"docs/wp/calibration_cluster_design_2026-10-17_ja.md"]
    validation_path = DATA/"completion_validation.json"
    for page in pages:
        for target in re.findall(r"\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                path = (page.parent/target.split("#")[0]).resolve()
                assert path == validation_path or path.exists(), (page, target)
    source_files = [ROOT/p for p in ("cluster_scripts/audit_calibration.py", "cluster_scripts/verify_recovery.py",
                    "cluster_scripts/summarize_calibration.py", "cluster_scripts/steane_components.py",
                    "tests/test_calibration_audit.py", "tests/test_calibration_recovery.py", "tests/test_steane_components.py")]
    files = [*RESULTS.iterdir(), *pages, handoff, *source_files, Path(__file__), DATA/"completion_tests.log", DATA/"cluster_completion_status.txt"]
    evidence = dict(status="verified", checked_at=datetime.now(timezone.utc).isoformat(),
                    base_commit=bundle["base_commit"], manifest=audit["manifest"],
                    traces=audit["traces"], rows=len(rows), coverage_conditions=len(summaries),
                    unavailable_intervals=0, trace_failures=0, terminal_successful_jobs=8,
                    focused_tests=dict(passed=16, seconds=13.02),
                    recovery=recovery, rimc_status="clean; read-only", public_defaults="unchanged",
                    archive_check="Full payload checksum verification recorded in recovery.json; this final check reconfirms archive sizes and all audit-output hashes.",
                    hashes={p.relative_to(ROOT).as_posix(): sha(p) for p in files if p.is_file()})
    validation_path.write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items() if k not in ("hashes", "recovery")}))


if __name__ == "__main__":
    main()
