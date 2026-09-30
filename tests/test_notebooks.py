"""Run each tutorial notebook quickly against the active installed package."""

import json
import os
from pathlib import Path
import sys
import time

import pytest


nbformat = pytest.importorskip("nbformat")
nbclient = pytest.importorskip("nbclient")
pytest.importorskip("ipykernel")

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = (
    "01_quickstart.ipynb",
    "02_pl_curve_with_bar.ipynb",
    "03_conditional_sampling_and_diagnostics.ipynb",
    "04_bring_your_own.ipynb",
)


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebook_executes_quickly(name, tmp_path, monkeypatch):
    if name != "04_bring_your_own.ipynb":
        pytest.importorskip("pymatching")
        pytest.importorskip("ldpc")
        pytest.importorskip("bposd")
    pytest.importorskip("matplotlib")
    import mcmc4qec
    if Path(mcmc4qec.__file__).resolve() == ROOT / "src" / "mcmc4qec" / "__init__.py":
        previous_pythonpath = os.environ.get("PYTHONPATH")
        monkeypatch.setenv("PYTHONPATH", str(ROOT / "src") + (
            os.pathsep + previous_pythonpath if previous_pythonpath else ""))
    kernel = tmp_path / "kernels" / "mcmc4qec-test"
    kernel.mkdir(parents=True)
    (kernel / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "mcmc4qec test", "language": "python",
    }), encoding="utf-8")
    old_path = os.environ.get("JUPYTER_PATH")
    monkeypatch.setenv("JUPYTER_PATH", str(tmp_path) + (os.pathsep + old_path if old_path else ""))
    monkeypatch.setenv("MCMC4QEC_QUICK", "1")
    notebook = nbformat.read(ROOT / "notebooks" / name, as_version=4)
    start = time.perf_counter()
    executed = nbclient.NotebookClient(
        notebook, timeout=25, kernel_name="mcmc4qec-test",
        resources={"metadata": {"path": str(ROOT / "notebooks")}},
    ).execute()
    assert time.perf_counter() - start < 60
    assert all(cell.outputs for cell in executed.cells if cell.cell_type == "code")
    assert any("image/png" in output.get("data", {})
               for cell in executed.cells if cell.cell_type == "code"
               for output in cell.outputs)
