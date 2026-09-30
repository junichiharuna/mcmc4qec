"""Check the installed wheel, examples and documentation in an isolated venv.

Run with that venv's Python: python -I docs/wp/verify_wheel.py core|optional.
Pytest is run separately, with --override-ini pythonpath=.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import time

import mcmc4qec


def main():
    mode = sys.argv[1]
    if mode not in {"core", "optional"}:
        raise ValueError("expected core or optional")
    root = Path(__file__).resolve().parents[2]
    installed = Path(mcmc4qec.__file__).resolve().parent
    source = root / "src" / "mcmc4qec"
    assert installed != source
    assert Path(sys.prefix).resolve() in installed.parents
    assert mcmc4qec.__version__ == importlib.metadata.version("mcmc4qec") == "0.1.0.dev2"
    source_files = {p.relative_to(source): p.read_bytes() for p in source.rglob("*.py")}
    wheel_files = {p.relative_to(installed): p.read_bytes() for p in installed.rglob("*.py")}
    assert source_files == wheel_files, "wheel/source Python files differ"
    for name in ("pymatching", "ldpc", "bposd", "stim"):
        assert (importlib.util.find_spec(name) is not None) == (mode == "optional"), name
    print(f"{mode}: {installed}; {len(source_files)} Python files match source", flush=True)

    def run(label, args):
        start = time.perf_counter()
        result = subprocess.run([sys.executable, "-I", *args], cwd=root,
                                text=True, capture_output=True, timeout=60)
        print(f"{label}: exit={result.returncode}, {time.perf_counter()-start:.2f}s", flush=True)
        print(result.stdout, end="", flush=True)
        if result.returncode:
            print(result.stderr, flush=True)
            result.check_returncode()

    core_examples = {"bit_flip.py", "three_noise.py", "bar_ladder.py"}
    for path in sorted((root / "examples").glob("*.py")):
        if mode == "optional" or path.name in core_examples:
            run(str(path.relative_to(root)), [str(path)])
        else:
            print(f"{path.name}: skipped in core (requires optional dependencies)", flush=True)
    for relative in ("README.md", "docs/tutorial_en.md"):
        blocks = re.findall(r"```python\s*\n(.*?)```", (root / relative).read_text(encoding="utf-8"), re.S)
        assert blocks, relative
        for index, block in enumerate(blocks, 1):
            needs_optional = "make_toric_code" in block
            if mode == "core" and needs_optional:
                print(f"{relative} block {index}: skipped in core (optional)", flush=True)
            else:
                run(f"{relative} block {index}", ["-c", block])


if __name__ == "__main__":
    main()
