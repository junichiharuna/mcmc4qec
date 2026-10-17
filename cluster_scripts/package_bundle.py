"""Archive the wheel, drivers, acceptance tests, and exact source provenance.

Run locally after building the wheel. This does not connect to or submit jobs
on the cluster. Deployment uses scp followed by sha256sum verification.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"output"/"cluster_deploy_20261017"
OUT.mkdir(parents=True, exist_ok=True)
files = [*sorted((ROOT/"cluster_scripts").glob("*.py")), ROOT/"cluster_scripts/requirements.txt",
         ROOT/"dist/mcmc4qec-0.1.0.dev5-py3-none-any.whl", ROOT/"tests/test_tile_codes.py",
         ROOT/"tests/test_cluster_calibration.py", ROOT/"examples/tile_bposd.py",
         ROOT/"docs/wp/tile_cluster_spec_2026-10-17_ja.md",
         ROOT/"docs/wp/calibration_cluster_design_2026-10-17_ja.md"]
provenance = dict(base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  files={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(OUT/"bundle.json").write_text(json.dumps(provenance, indent=2)+"\n", encoding="utf-8")
(OUT/"source.patch").write_bytes(subprocess.check_output(["git", "diff", "--binary", "--", "src", "README.md", "README_ja.md"], cwd=ROOT))
archive = OUT/"bundle.tar.gz"
with tarfile.open(archive, "w:gz") as tar:
    for path in files:
        tar.add(path, arcname=path.relative_to(ROOT).as_posix())
    for name in ("bundle.json", "source.patch"):
        tar.add(OUT/name, arcname=name)
print(json.dumps(dict(path=str(archive), sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
