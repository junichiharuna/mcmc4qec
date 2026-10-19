"""Run editable templates as users run them, including invalid input guards."""

import json
import os
from pathlib import Path
import subprocess
import sys

import mcmc4qec
import pytest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "examples" / "templates"
KEYS = {
    "byo_css_bitflip": {"n", "k", "checks_passed", "pl"},
    "byo_noise": {"n", "normalization", "pl"},
    "byo_decoder": {"n", "output_kind", "checks_passed", "pl"},
    "byo_stim_dem": {"detectors", "mechanisms", "pl"},
}


def run_template(name, out, extra_env=None):
    env = os.environ.copy()
    # Use the same imported package in source and isolated installed-wheel runs.
    package_parent = str(Path(mcmc4qec.__file__).resolve().parents[1])
    env["PYTHONPATH"] = package_parent + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("MCMC4QEC_TEMPLATE_MATRICES", None)
    env.pop("MCMC4QEC_TEMPLATE_LOG_OFFSET", None)
    env.pop("MCMC4QEC_TEMPLATE_APPEND_BITS", None)
    env.pop("MCMC4QEC_TEMPLATE_SAMPLE_EXTRA_BITS", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(TEMPLATES / f"{name}.py"), "--quick", "--seed", "13", "--out", str(out)],
        capture_output=True, text=True, env=env, timeout=10,
    )


@pytest.mark.parametrize("name", KEYS)
def test_default_quick_run(name, tmp_path):
    if name == "byo_stim_dem":
        pytest.importorskip("stim")
        pytest.importorskip("pymatching")
    out = tmp_path / name
    result = run_template(name, out)
    assert result.returncode == 0, result.stdout + result.stderr
    summary = [line for line in result.stdout.splitlines() if line.startswith("SUMMARY ")]
    assert len(summary) == 1
    assert set(json.loads(summary[0][8:])) == KEYS[name]
    assert (out / "result.json").is_file()


@pytest.mark.parametrize("name,inject,expected", [
    ("byo_css_bitflip", {"MCMC4QEC_TEMPLATE_MATRICES": json.dumps({"hx": [[1, 0, 0]]})}, "commute"),
    ("byo_noise", {"MCMC4QEC_TEMPLATE_LOG_OFFSET": "0.1"}, "normalized"),
    ("byo_noise", {"MCMC4QEC_TEMPLATE_SAMPLE_EXTRA_BITS": "1"}, "state"),
    ("byo_decoder", {"MCMC4QEC_TEMPLATE_APPEND_BITS": "1"}, "correction output"),
])
def test_invalid_input_stops_before_sampling(name, inject, expected, tmp_path):
    out = tmp_path / name
    result = run_template(name, out, inject)
    assert result.returncode != 0
    assert result.stdout == ""
    assert len(result.stderr.strip().splitlines()) == 1
    assert result.stderr.startswith("CHECK FAILED: ")
    assert expected in result.stderr
    assert not out.exists()


@pytest.mark.parametrize("name", KEYS)
def test_research_output_is_rejected(name, tmp_path):
    if name == "byo_stim_dem":
        pytest.importorskip("stim")
        pytest.importorskip("pymatching")
    research = tmp_path / "read-only-research"
    research.mkdir()
    result = run_template(name, research / "template-output",
                          {"RESEARCH_ROOT": str(research)})
    assert result.returncode != 0
    assert "read-only research repository" in result.stderr
    assert "SUMMARY " not in result.stdout


def test_environment_research_root_is_rejected(tmp_path):
    research = tmp_path / "read-only-research"
    research.mkdir()
    result = run_template("byo_css_bitflip", research / "output",
                          {"RIMC_RESEARCH_ROOT": str(research)})
    assert result.returncode != 0
    assert "read-only research repository" in result.stderr
    assert not (research / "output").exists()
