"""Contracts for choosing a physical target without changing the failure event."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]


def example():
    spec = importlib.util.spec_from_file_location(
        "tile_fixed_prior_example", ROOT / "examples/workflows/tile_capacity_fixed_prior.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("size,target,ladder", [
    (6, .03, [.1, .07, .05, .03]),
    (12, .05, [.1, .085, .07, .06, .05]),
])
def test_omitted_options_keep_original_ladder(size, target, ladder):
    assert example()._target_ladder(size, None) == (target, ladder)


@pytest.mark.parametrize("ladder,target,expected", [
    (".1,.07,.05,.03,.01", .01, [.1, .07, .05, .03, .01]),
    (".1,.07,.05", .05, [.1, .07, .05]),
    (".1,.08", .08, [.1, .08]),
])
def test_explicit_ladder_sets_target_to_endpoint(ladder, target, expected):
    assert example()._target_ladder(6, ladder) == (target, expected)


@pytest.mark.parametrize("ladder", [
    "", ".1", ".1,.01,.01", ".1,.005,.01", "nan,.01",
    "inf,.01", "1,.01", "0,.01", ".1,0", ".1,-.01", ".1,,.01", "x,.01",
])
def test_invalid_ladder_rejected(ladder):
    with pytest.raises(ValueError):
        example()._target_ladder(6, ladder)


def test_explicit_ladder_allows_high_target():
    assert example()._target_ladder(6, ".4,.3,.2") == (.2, [.4, .3, .2])


@pytest.mark.parametrize("noise", ["bit", "depolarizing"])
@pytest.mark.parametrize("size", [6, 12])
def test_target_prior_and_problem_shared_by_anchor_check_and_bar(noise, size, tmp_path, monkeypatch):
    module = example()
    decoder = object()
    bit_model, joint_model, bit_noise, joint_noise = (object() for _ in range(4))
    code = SimpleNamespace(n=2 * size * size, lx=np.zeros((4, 2), dtype=np.uint8),
                           lz=np.zeros((4, 2), dtype=np.uint8), bit_flip_model=lambda: bit_model)
    factories = []
    mc_calls = []
    bar_calls = []

    def factory(kind, code_arg, prior, **settings):
        factories.append((kind, code_arg, prior, settings))
        return decoder

    outcome = SimpleNamespace(to_json=lambda: "{}", estimate=.01, interval=[.001, .02],
                              trials=512, failures=5, estimates=[.1, .01], intervals=[[0, 1], [0, 1]])

    def direct_mc(problem, p, **kwargs):
        mc_calls.append((problem, p, kwargs))
        return outcome

    def bar(problem, ladder, **kwargs):
        bar_calls.append((problem, ladder, kwargs))
        return outcome

    monkeypatch.setattr(module.qec, "make_tile_code", lambda *args: code)
    monkeypatch.setattr(module.qec, "bposd_decoder", lambda *a, **kw: factory("bit", *a, **kw))
    monkeypatch.setattr(module.qec, "depolarizing_bposd_decoder", lambda *a, **kw: factory("depolarizing", *a, **kw))
    monkeypatch.setattr(module.qec, "DepolarizingModel", lambda c: joint_model)
    monkeypatch.setattr(module.qec, "IndependentBitFlip", lambda n: bit_noise)
    monkeypatch.setattr(module.qec, "DepolarizingNoise", lambda n: joint_noise)
    monkeypatch.setattr(module.qec, "Problem", lambda m, n, d: SimpleNamespace(model=m, noise=n, decoder=d))
    monkeypatch.setattr(module.qec, "direct_mc", direct_mc)
    monkeypatch.setattr(module.qec, "estimate_logical_error", bar)
    monkeypatch.setattr(sys, "argv", ["example", "--quick", "--size", str(size), "--noise", noise,
                                     "--ladder", ".1,.03,.01",
                                     "--initialization", "logical", "--out", str(tmp_path)])
    module.main()
    assert len(factories) == 1
    assert factories[0][:2] == (noise, code)
    assert factories[0][2] == (.01 if noise == "bit" else 2 * .01 / 3)
    assert factories[0][3]["osd_order"] == 10
    problem, ladder, options = bar_calls[0]
    assert ladder == [.1, .03, .01]
    assert all(call[0] is problem for call in mc_calls)
    assert [call[1] for call in mc_calls] == [.1, .01]
    assert problem.decoder is decoder
    assert problem.model is (bit_model if noise == "bit" else joint_model)
    assert problem.noise is (bit_noise if noise == "bit" else joint_noise)
    assert options["mode"] == "fixed_failure"
    assert len(options["initial_states"]) == len(ladder)
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["target_p"] == .01
    assert summary["sector_decoder_prior"] == factories[0][2]


def test_invalid_cli_has_no_output_side_effect(tmp_path, monkeypatch):
    module = example()
    out = tmp_path / "not-created"
    monkeypatch.setattr(sys, "argv", ["example", "--ladder", "nan,.01", "--out", str(out)])
    with pytest.raises(SystemExit) as error:
        module.main()
    assert error.value.code == 2
    assert not out.exists()
