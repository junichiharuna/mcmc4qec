"""Finite acceptance for the separate tile code-capacity study driver."""
from pathlib import Path
import sys
import itertools

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_study as t


def test_complete_tile72_logical_quotient_failure_definition():
    code, problem = t.build_problem(6, "bit", .03)
    coefficients = np.array(list(itertools.product((0, 1), repeat=8)), dtype=np.uint8)
    states = coefficients @ code.lx % 2
    compact = t.compact(problem, states)
    assert np.array_equal(compact["sector"] != 0, np.any(coefficients, axis=1))
    assert [problem.is_faulty(s) for s in states] == list(np.any(coefficients, axis=1))
    assert np.all(compact["syndrome_weight"] == 0)


@pytest.mark.parametrize("noise", ["bit", "depolarizing"])
def test_correction_equation_failure_and_reproducibility(noise):
    code, problem = t.build_problem(6, noise, .03)
    rng = np.random.default_rng(8721)
    states = np.array([problem.noise.sample(.03, rng) for _ in range(12)])
    record = t.decoder_probe(6, noise, .03, states, priors=[.03, .001])
    assert record["repeat_mismatches"] == record["reverse_mismatches"] == record["fresh_mismatches"] == 0
    assert record["syndrome_violations"] == 0
    assert record["failure_definition_mismatches"] == 0
    compact = t.compact(problem, states)
    assert np.array_equal(compact["sector"] != 0, [problem.is_faulty(s) for s in states])


@pytest.mark.parametrize("noise", ["bit", "depolarizing"])
def test_initialization_and_seed_identity(noise):
    code, problem = t.build_problem(6, noise, .1)
    for i in range(2*len(code.lx)):
        state, attempts = t.initial_state(code, problem, .1, noise, "logical", i, np.random.default_rng(i), 5)
        assert problem.is_faulty(state) and np.isfinite(problem.log_prob(state, .1))
        assert attempts == 0
    state, attempts = t.initial_state(code, problem, .1, noise, "rejection", 0, np.random.default_rng(3), 1000)
    assert attempts > 0 and problem.is_faulty(state)
    assert t.seed((0, 1, 2), 3) == t.seed((0, 1, 2), 3)
    assert t.seed((0, 1, 2), 3) != t.seed((0, 1, 3), 3)


def test_pilot_artifact_resume_and_corruption(tmp_path):
    plan = t.make_plan()
    plan.update(mc_trials=12, steps=16, probe_samples=4, max_initial_attempts=1000)
    task = (0, 0, 0)
    result = t.pilot_task((str(tmp_path), plan, task))
    assert result["status"] == "ok"
    assert len(result["chains"]) == 4
    assert t.pilot_task((str(tmp_path), plan, task))["resumed"]
    path = tmp_path/"pilot"/"0-0-0.npz"
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        t.pilot_task((str(tmp_path), plan, task))
