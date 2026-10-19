"""Build a new immutable tile-study deployment bundle from reviewed local files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    files=[*sorted((root/"cluster_scripts").glob("*.py")),root/"cluster_scripts/requirements.txt",
           *sorted((root/"tests").glob("test_tile*.py")),*sorted((root/"tests").glob("test_submit_tile*.py")),
           root/"tests/test_artifact_archive.py",root/"tests/test_steane_components.py",
           root/"dist/mcmc4qec-0.1.0.dev5-py3-none-any.whl",
           root/"docs/wp/tile_validation_plan_2026-10-17_ja.md",
           root/"docs/wp/tile_weight_stratified_spec_2026-10-17_ja.md",
           root/"docs/wp/tile_weight_reference_comparison_spec_2026-10-18_ja.md",
           root/"docs/wp/tile_low_noise_plan_2026-10-18_ja.md",
           root/"docs/wp/tile_kernel_support_2026-10-17_ja.md",
           root/"docs/wp/tile_time_to_accuracy_plan_2026-10-17_ja.md",
           root/"docs/wp/tile_decoder_platform_2026-10-17_ja.md",
           root/"docs/wp/tile_trace_audit_execution_2026-10-18_ja.md",
           root/"docs/wp/tile_decoder_prior_effect_2026-10-18_ja.md",
           root/"docs/wp/tile_validation_report_2026-10-18_ja.md",
           root/"docs/wp/data_tile_validation_2026-10-17/reference_audit.json",
           root/"docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json",
           root/"docs/wp/data_tile_validation_2026-10-17/decoder_platform_fixture.json",
           root/"docs/wp/data_tile_validation_2026-10-17/decoder_platform_linux.json"]
    provenance=dict(base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
                    files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output/"bundle.json").write_text(json.dumps(provenance,indent=2)+"\n",encoding="utf-8")
    archive=output/"bundle.tar.gz"
    with tarfile.open(archive,"w:gz") as tar:
        for path in files:
            tar.add(path,arcname=path.relative_to(root).as_posix())
        tar.add(output/"bundle.json",arcname="bundle.json")
    provenance["archive_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/"bundle.json").write_text(json.dumps(provenance,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(output=str(output),archive_sha256=provenance["archive_sha256"])))


if __name__=="__main__":
    main()
