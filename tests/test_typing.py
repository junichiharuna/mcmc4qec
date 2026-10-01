"""Public type coverage and the optional static type-check gate."""

from importlib.util import find_spec
import inspect
from pathlib import Path
import subprocess
import sys

import mcmc4qec
import pytest


def _assert_complete_signature(value):
    signature = inspect.signature(value)
    for parameter in signature.parameters.values():
        if parameter.name in ("self", "cls"):
            continue
        assert parameter.annotation is not inspect.Parameter.empty, (value, parameter.name)
    assert signature.return_annotation is not inspect.Signature.empty, value


def test_public_signatures_are_annotated():
    """Check every exported callable and methods reachable on exported classes."""
    for name in mcmc4qec.__all__:
        value = getattr(mcmc4qec, name)
        if inspect.isfunction(value):
            _assert_complete_signature(value)
        elif inspect.isclass(value):
            if issubclass(value, BaseException):
                continue
            if "__init__" in value.__dict__ and not getattr(value, "_is_protocol", False):
                _assert_complete_signature(value)
            for method_name, method in inspect.getmembers(value):
                if method_name.startswith("_"):
                    continue
                if isinstance(method, property):
                    _assert_complete_signature(method.fget)
                elif inspect.isfunction(method) or inspect.ismethod(method):
                    _assert_complete_signature(method)


def test_mypy_package():
    if find_spec("mypy") is None:
        pytest.skip("mypy is not installed")
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "-m", "mypy", "--ignore-missing-imports", "src/mcmc4qec"],
        cwd=root, capture_output=True, text=True, timeout=50, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
