"""Acceptance checks for the executable fixed-prior decoder example."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("decoder_comparison_example", ROOT / "examples/decoder_comparison.py")


def example():
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    return module


def test_exact_matches_physical_residual_enumeration():
    module = example()
    from mcmc4qec.codes import make_steane_code
    code = make_steane_code()
    result = module.run("steane", quick=True, seed=27)
    for row in result["decoders"]:
        decoder = module.make_decoders(code, "steane", .08)[row["name"]]
        raw = decoder.decoder
        probability = 0.
        for integer in range(128):
            error = np.array([(integer >> bit) & 1 for bit in range(7)], dtype=np.uint8)
            syndrome = code.hz @ error % 2
            correction = np.asarray(raw.decode(syndrome), dtype=np.uint8)
            assert np.array_equal(code.hz @ correction % 2, syndrome)
            if np.any(code.lz @ (error ^ correction) % 2):
                weight = int(error.sum())
                probability += .08**weight * .92**(7-weight)
        assert row["exact"]["estimate"] == pytest.approx(probability, abs=1e-14)
        assert row["direct_mc"]["trials"] == row["planned_trials"] == 64


def test_baseline_rejects_invalid_correction():
    module = example()
    from mcmc4qec.codes import make_steane_code
    code = make_steane_code()
    decoder = module.make_decoders(code, "steane", .08)["bp_osd_0"]
    class Broken:
        def decode(self, syndrome):
            return np.zeros(code.n, dtype=np.uint8)
    decoder.decoder = Broken()
    with pytest.raises(ValueError, match="syndrome"):
        decoder.predict(code.hz[:, 0])


@pytest.mark.parametrize("code", ["steane", "toric", "tile72"])
def test_quick_cli(code, tmp_path):
    if code == "toric":
        pytest.importorskip("bposd")
        from importlib.metadata import version
        if version("ldpc") != "2.4.1":
            pytest.skip("standalone UF is version scoped")
    import os
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    completed = subprocess.run([sys.executable, str(ROOT / "examples/decoder_comparison.py"),
                                "--code", code, "--quick", "--seed", "51", "--out", str(tmp_path)],
                               capture_output=True, text=True, env=env, timeout=15)
    assert completed.returncode == 0, completed.stderr
    last_line = completed.stdout.strip().splitlines()[-1]
    assert last_line.startswith("SUMMARY ")
    assert json.loads(last_line.removeprefix("SUMMARY "))["code"] == code
    report = json.loads((tmp_path / "summary.json").read_text())
    assert report["seed"] == 51
    assert report["decoder_prior"] == report["sampling_p"] == .08
    assert len(report["decoders"]) == (4 if code == "toric" else 3)
    for row in report["decoders"]:
        assert 0 <= row["direct_mc"]["failures"] <= 64
        assert row["direct_mc"]["trials"] == 64
        assert (row["exact"] is not None) == (code == "steane")
        assert row["direct_mc"]["metadata"]["rng"]["entropy"] == 51


def test_mwpm_requires_graphlike_code():
    with pytest.raises(ValueError, match="toric"):
        example().run("steane", quick=True, mwpm=True)


def test_optional_mwpm_baseline():
    pytest.importorskip("pymatching")
    pytest.importorskip("bposd")
    from importlib.metadata import version
    if version("ldpc") != "2.4.1":
        pytest.skip("standalone UF is version scoped")
    report = example().run("toric", quick=True, seed=51, mwpm=True)
    assert report["decoders"][-1]["name"] == "mwpm"
    assert report["decoders"][-1]["direct_mc"]["trials"] == 64


def test_read_only_research_output_guard(tmp_path, monkeypatch):
    root = tmp_path / "research"
    monkeypatch.setenv("RESEARCH_ROOT", str(root))
    with pytest.raises(ValueError, match="research repository"):
        example().output_dir(root / "generated")
    assert not root.exists()
