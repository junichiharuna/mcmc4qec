"""Public type coverage and the optional static type-check gate."""

from importlib.util import find_spec
import inspect
import os
from pathlib import Path
import subprocess
import sys

import mcmc4qec
from mcmc4qec.kernels import Proposal
from mcmc4qec.stim_dem import StimDemModel, StimDemNoise
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
    public_values = [getattr(mcmc4qec, name) for name in mcmc4qec.__all__]
    # These classes are returned by exported factories or proposal methods.
    public_values.extend((Proposal, StimDemModel, StimDemNoise))
    for value in public_values:
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


def test_mypy_consumer_contract(tmp_path):
    """Nested-list matrices, callback output, and Noise fit together for clients."""
    if find_spec("mypy") is None:
        pytest.skip("mypy is not installed")
    root = Path(__file__).resolve().parents[1]
    source = root / "src"
    env = {**os.environ, "MYPYPATH": str(source)}
    valid = tmp_path / "typing_client.py"
    valid.write_text(
        "from typing import Any\n"
        "import numpy as np\n"
        "from numpy.typing import ArrayLike\n"
        "from mcmc4qec import CSSCode, CallableDecoder, IndependentBitFlip, Problem, Result, exact, direct_mc, sample_faulty, diagnose, evaluate_convergence\n"
        "from mcmc4qec import BinaryLinearModel, minimum_weight_coset_representative\n"
        "code = CSSCode([[0,0,0]], [[1,1,0],[0,1,1]], [[1,1,1]], [[1,0,0]])\n"
        "decoder = CallableDecoder(lambda s: [int(tuple(s)==(1,0))], identifier='example')\n"
        "noise = IndependentBitFlip(3, scales=[1.0, 1.0, 1.0])\n"
        "problem = Problem(code.bit_flip_model(), noise, decoder)\n"
        "result = exact(problem, 0.25)\n"
        "model = BinaryLinearModel([[1, 0]], [[0, 1]])\n"
        "representative = minimum_weight_coset_representative([1, 0], [[0, 1]])\n"
        "class CustomModel:\n"
        "    n = 1\n"
        "    def validate_state(self, state: np.ndarray) -> list[int]: return [int(state[0])]\n"
        "    def syndrome(self, state: np.ndarray) -> list[int]: return [int(state[0])]\n"
        "    def observables(self, state: np.ndarray) -> list[int]: return [int(state[0])]\n"
        "    def metadata(self) -> dict[str, Any]: return {'identifier': 'custom-model'}\n"
        "class CustomNoise:\n"
        "    n = 1\n"
        "    def sample(self, p: tuple[float, int], rng: np.random.Generator) -> list[int]: return [0]\n"
        "    def log_prob(self, state: np.ndarray, p: tuple[float, int]) -> float: return 0.0\n"
        "    def metadata(self) -> dict[str, Any]: return {'identifier': 'custom-noise'}\n"
        "class CustomDecoder:\n"
        "    def predict(self, syndrome: ArrayLike) -> list[int]: return [0]\n"
        "    def metadata(self) -> dict[str, Any]: return {'identifier': 'custom-decoder'}\n"
        "custom = Problem(CustomModel(), CustomNoise(), CustomDecoder())\n"
        "exact(custom, (0.25, 1))\n"
        "direct_mc(custom, (0.25, 1), trials=4)\n"
        "sample_faulty(custom, (0.25, 1), initial_state=[1])\n"
        "run = Result('sample_faulty', {}, 0.0, states=np.zeros((1, 8, 1), dtype=np.uint8))\n"
        "diagnose((run, run))\n"
        "evaluate_convergence(np.zeros((2, 8)), other_initialization=np.ones((2, 8)))\n"
        "evaluate_convergence((run, run), other_initialization=(run, run))\n",
        encoding="utf-8",
    )
    command = [sys.executable, "-m", "mypy", "--ignore-missing-imports"]
    completed = subprocess.run(command + [str(valid)], cwd=root, env=env,
                               capture_output=True, text=True, timeout=50, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr

    invalid = tmp_path / "typing_invalid.py"
    invalid.write_text(
        "from mcmc4qec import BinaryLinearModel, CallableDecoder, IndependentBitFlip, Problem, exact, direct_mc, sample_faulty\n"
        "noise = IndependentBitFlip(1)\n"
        "noise.probabilities('wrong')\n"
        "problem = Problem(BinaryLinearModel([[1]], [[1]]), noise, "
        "CallableDecoder(lambda s: [0], identifier='decoder'))\n"
        "problem.log_prob([0], 'wrong')\n"
        "exact(problem, 'wrong')\n"
        "direct_mc(problem, 'wrong', trials=4)\n"
        "sample_faulty(problem, 'wrong', initial_state=[1])\n",
        encoding="utf-8",
    )
    completed = subprocess.run(command + [str(invalid)], cwd=root, env=env,
                               capture_output=True, text=True, timeout=50, check=False)
    assert completed.returncode != 0, completed.stdout + completed.stderr
    assert completed.stdout.count('incompatible type "str"') == 2, completed.stdout
    for function in ("exact", "direct_mc", "sample_faulty"):
        assert f'Cannot infer value of type parameter "_P" of "{function}"' in completed.stdout
