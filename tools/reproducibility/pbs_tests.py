"""Run only small archive fixtures under a pinned PBS request."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def check(ok, message):
    if not ok:
        raise ValueError(message)


def pinned(pin):
    raw = Path(pin["path"]).read_bytes()
    check(hashlib.sha256(raw).hexdigest() == pin["sha256"], "Acceptance source pin differs")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    check(os.environ.get("PBS_JOBID"), "Fixture acceptance must run through qsub")
    request = json.loads(pinned(dict(path=args.request, sha256=args.sha256)))
    check(request["purpose"] == "reproduction_archive_fixture_acceptance", "Fixture request required")
    sources = request["sources"]
    check(set(sources) == {"archive.py", "test_archive.py", "pbs_tests.py"}, "Exact fixture source census required")
    source_root = Path(__file__).resolve().parent
    for name, pin in sources.items():
        check(Path(pin["path"]) == source_root / name, "Fixture source location differs")
        pinned(pin)
    result = Path(args.result)
    check(not result.exists(), "Acceptance result must be fresh")
    response = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(source_root),
                               "-p", "test_archive.py", "-v"], capture_output=True, text=True,
                              cwd=result.parent, timeout=120)
    for suffix, text in (("stdout", response.stdout), ("stderr", response.stderr)):
        with result.with_suffix("." + suffix).open("x", encoding="utf8") as stream:
            stream.write(text)
    check(response.returncode == 0 and re.search(r"Ran 23 tests in .*\n\nOK\s*$", response.stderr), "Archive fixture acceptance failed")
    for pin in sources.values():
        pinned(pin)
    receipt = dict(schema=1, purpose=request["purpose"], sources=sources, tests_passed=23,
                   request=dict(path=args.request, sha256=args.sha256), pbs_job_id=os.environ["PBS_JOBID"],
                   production_files_read=False, scientific_reproduction_verified=False,
                   actual_archive_collected=False)
    with result.open("x", encoding="utf8") as stream:
        json.dump(receipt, stream, indent=2)


if __name__ == "__main__":
    main()
