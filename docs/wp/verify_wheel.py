"""Check the installed wheel, examples and documentation in an isolated venv.

Run with that venv's Python: python -I docs/wp/verify_wheel.py core|optional.
Pytest is run separately, with --override-ini pythonpath=.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import tomllib

import mcmc4qec


# A missing/extra entry is an integration error, not an implicit optional skip.
EXAMPLES = {
    "bit_flip.py": (False, "exact pl pl_interval ew_exact ew_chain"),
    "three_noise.py": (False, "cases"),
    "bar_ladder.py": (False, "ladder bar intervals exact"),
    "toric_pymatching.py": (True, "code p pl pl_interval ew_direct ew_chain"),
    "stim_dem.py": (True, "mechanisms exact pl pl_interval"),
    "circuit_baseline.py": (True, "locations detectors pl pl_interval"),
    "bb72_bposd.py": (True, "code p pl pl_interval ew_direct ew_chain"),
    "toric_depolarizing.py": (True, "code p pl pl_interval ew_direct ew_chain"),
    "phenomenological_toric.py": (True, "code rounds p pl pl_interval"),
    "steane_exact.py": (False, "code ladder exact bar bar_intervals"),
    "workflows/pl_curve.py": (True, "codes ladder estimates intervals checks"),
    "workflows/conditional_weight.py": (True, "code ps ew_direct ew_chain"),
    "workflows/convergence_check.py": (True, "code p checks verdict warnings"),
    "workflows/p_dependent_decoder.py": (True, "code ladder fixed approx"),
    "templates/byo_css_bitflip.py": (False, "n k checks_passed pl"),
    "templates/byo_noise.py": (False, "n normalization pl"),
    "templates/byo_decoder.py": (False, "n output_kind checks_passed pl"),
    "templates/byo_stim_dem.py": (True, "detectors mechanisms pl"),
}


def reject_nonfinite(value):
    raise ValueError(f"nonfinite JSON value: {value}")


def main():
    mode = sys.argv[1]
    if mode not in {"core", "optional"}:
        raise ValueError("expected core or optional")
    root = Path(__file__).resolve().parents[2]
    installed = Path(mcmc4qec.__file__).resolve().parent
    source = root / "src" / "mcmc4qec"
    assert installed != source
    assert Path(sys.prefix).resolve() in installed.parents
    release = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert mcmc4qec.__version__ == importlib.metadata.version("mcmc4qec") == release
    description = importlib.metadata.metadata("mcmc4qec").get_payload()
    assert description.replace("\r\n", "\n").strip() == (root / "README.md").read_text(encoding="utf-8").strip(), "wheel README differs"
    source_files = {p.relative_to(source): p.read_bytes() for p in source.rglob("*.py")}
    wheel_files = {p.relative_to(installed): p.read_bytes() for p in installed.rglob("*.py")}
    assert source_files == wheel_files, "wheel/source Python files differ"
    for name in ("pymatching", "ldpc", "bposd", "stim", "matplotlib", "nbclient", "nbformat", "ipykernel"):
        assert (importlib.util.find_spec(name) is not None) == (mode == "optional"), name
    print(f"{mode}: {installed}; {len(source_files)} Python files match source", flush=True)

    def run(label, args, *, timeout=60, keys=None):
        start = time.perf_counter()
        # Notebook kernels are grandchildren; keep source paths out of their
        # environment as well as isolating this immediate Python subprocess.
        environment = {key: value for key, value in os.environ.items()
                       if key.upper() not in {"PYTHONPATH", "PYTHONHOME"}}
        result = subprocess.run([sys.executable, "-I", *args], cwd=root,
                                text=True, capture_output=True, timeout=timeout,
                                env=environment)
        print(f"{label}: exit={result.returncode}, {time.perf_counter()-start:.2f}s", flush=True)
        print(result.stdout, end="", flush=True)
        if result.returncode:
            print(result.stderr, flush=True)
            result.check_returncode()
        if keys is not None:
            final = result.stdout.strip().splitlines()[-1]
            assert final.startswith("SUMMARY "), label
            payload = json.loads(final[len("SUMMARY "):], parse_constant=reject_nonfinite)
            assert set(payload) == set(keys.split()), label

    discovered = {path.relative_to(root / "examples").as_posix()
                  for path in (root / "examples").rglob("*.py")}
    assert discovered == set(EXAMPLES), (discovered - set(EXAMPLES), set(EXAMPLES) - discovered)
    with tempfile.TemporaryDirectory(prefix="mcmc4qec-wheel-") as output:
        for relative, (optional, keys) in sorted(EXAMPLES.items()):
            if mode == "core" and optional:
                print(f"{relative}: skipped in core (requires optional dependencies)", flush=True)
                continue
            path = root / "examples" / relative
            target = Path(output) / Path(relative).with_suffix("")
            run(str(path.relative_to(root)), [str(path), "--quick", "--seed", "20260930",
                                            "--out", str(target)], timeout=10, keys=keys)
        if mode == "optional":
            run("notebooks (quick)", [str(root / "notebooks" / "regenerate.py"), "--quick",
                                      "--out", str(Path(output) / "notebooks")], timeout=240)
        else:
            print("notebooks: skipped in core (requires notebooks extra)", flush=True)
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
