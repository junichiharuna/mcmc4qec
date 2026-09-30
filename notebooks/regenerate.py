"""Execute and save the four tutorial notebooks with the active Python kernel.

Run ``python notebooks/regenerate.py`` from an environment with the notebook
extra and the installed mcmc4qec package. ``--clear`` removes saved outputs
for a reproducibility check; a subsequent default run restores them. CI can
use ``--quick --out DIR`` to save shortened runs outside the source tree.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

import nbformat
from nbclient import NotebookClient


NOTEBOOKS = (
    "01_quickstart.ipynb",
    "02_pl_curve_with_bar.ipynb",
    "03_conditional_sampling_and_diagnostics.ipynb",
    "04_bring_your_own.ipynb",
)


def kernel_directory(root: Path) -> Path:
    directory = root / "kernels" / "mcmc4qec-local"
    directory.mkdir(parents=True)
    (directory / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "mcmc4qec local Python",
        "language": "python",
    }), encoding="utf-8")
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clear", action="store_true", help="Remove saved outputs only")
    parser.add_argument("--quick", action="store_true", help="Execute shortened notebook runs")
    parser.add_argument("--out", type=Path, help="Save executed notebooks in this directory")
    args = parser.parse_args()
    if args.clear and (args.quick or args.out):
        parser.error("--clear cannot be combined with --quick or --out")
    directory = Path(__file__).resolve().parent
    output_directory = args.out.resolve() if args.out else directory
    research_roots = (Path("C:/dev/RIMC").resolve(), Path("A:/dev/RIMC").resolve())
    if any(output_directory == root or output_directory.is_relative_to(root)
           for root in research_roots):
        parser.error("output directory must not be inside the read-only research repository")
    if args.out:
        output_directory.mkdir(parents=True, exist_ok=True)
    if not args.clear:
        import mcmc4qec
        print(f"Installed package: {Path(mcmc4qec.__file__).resolve()}", flush=True)
    with tempfile.TemporaryDirectory(prefix="mcmc4qec-kernel-") as temporary:
        previous = os.environ.get("JUPYTER_PATH")
        os.environ["JUPYTER_PATH"] = str(kernel_directory(Path(temporary))) + (
            os.pathsep + previous if previous else ""
        )
        previous_quick = os.environ.pop("MCMC4QEC_QUICK", None)
        if args.quick:
            os.environ["MCMC4QEC_QUICK"] = "1"
        try:
            for name in NOTEBOOKS:
                path = directory / name
                output_path = output_directory / name
                notebook = nbformat.read(path, as_version=4)
                start = time.perf_counter()
                if args.clear:
                    for cell in notebook.cells:
                        if cell.cell_type == "code":
                            cell.outputs = []
                            cell.execution_count = None
                else:
                    notebook = NotebookClient(
                        notebook, timeout=180, kernel_name="mcmc4qec-local",
                        resources={"metadata": {"path": str(directory)}},
                    ).execute()
                nbformat.write(notebook, output_path)
                print(f"{name}: status=ok; {time.perf_counter() - start:.2f}s; "
                      f"{output_path.stat().st_size} bytes; {output_path}", flush=True)
        finally:
            if previous is None:
                os.environ.pop("JUPYTER_PATH", None)
            else:
                os.environ["JUPYTER_PATH"] = previous
            if previous_quick is not None:
                os.environ["MCMC4QEC_QUICK"] = previous_quick


if __name__ == "__main__":
    main()
