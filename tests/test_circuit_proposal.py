import itertools

import numpy as np
import pytest

pytest.importorskip("stim")

from mcmc4qec.circuit import CircuitFaultModel, CircuitFaultNoise, PhysicalFaultProposal
from mcmc4qec.core import CallableDecoder, Problem
from test_circuit_model import small_circuit


def test_proposal_normalization_support_and_detailed_balance():
    model = CircuitFaultModel.from_stim_circuit(small_circuit())
    noise = CircuitFaultNoise(model, {"X_ERROR": [1], "DEPOLARIZE1": [.2, .3, .5]})
    problem = Problem(model, noise, CallableDecoder(lambda s: np.zeros(1, dtype=np.uint8), identifier="zero"))
    kernel = PhysicalFaultProposal()
    states = [np.array(s, dtype=np.uint8) for s in itertools.product(range(2), range(4))]
    for a in states:
        assert sum(kernel.probability(a, b, problem, .25) for b in states) == pytest.approx(1)
        for b in states:
            qab = kernel.probability(a, b, problem, .25)
            qba = kernel.probability(b, a, problem, .25)
            assert qab == pytest.approx(qba)
            if not qab:
                continue
            alpha_ab = min(1, np.exp(problem.log_prob(b, .25) - problem.log_prob(a, .25)) * qba / qab)
            alpha_ba = min(1, np.exp(problem.log_prob(a, .25) - problem.log_prob(b, .25)) * qab / qba)
            lhs = np.exp(problem.log_prob(a, .25)) * qab * alpha_ab * problem.is_faulty(b)
            rhs = np.exp(problem.log_prob(b, .25)) * qba * alpha_ba * problem.is_faulty(a)
            if problem.is_faulty(a) and problem.is_faulty(b):
                assert lhs == pytest.approx(rhs)


def test_add_delete_replace_proposals():
    model = CircuitFaultModel.from_stim_circuit(small_circuit())
    noise = CircuitFaultNoise(model, {"X_ERROR": [1], "DEPOLARIZE1": [1 / 3] * 3})
    problem = Problem(model, noise, CallableDecoder(lambda s: np.zeros(1, dtype=np.uint8), identifier="zero"))
    kernel = PhysicalFaultProposal()
    assert kernel.probability([0, 0], [0, 1], problem, .1) == pytest.approx(1 / 6)
    assert kernel.probability([0, 1], [0, 0], problem, .1) == pytest.approx(1 / 6)
    assert kernel.probability([0, 1], [0, 2], problem, .1) == pytest.approx(1 / 6)


def test_distinct_location_distributions_obey_detailed_balance():
    import stim

    circuit = stim.Circuit("""
        R 0 1
        DEPOLARIZE1(0.1) 0 1
        M 0 1
        DETECTOR rec[-2]
        OBSERVABLE_INCLUDE(0) rec[-1]
    """)
    model = CircuitFaultModel.from_stim_circuit(circuit)
    noise = CircuitFaultNoise(model, [[.2, .3, .5], [.5, .3, .2]])
    problem = Problem(model, noise,
        CallableDecoder(lambda s: np.zeros(1, dtype=np.uint8), identifier="zero"))
    p = {"location_rates": [.1, .3]}
    kernel = PhysicalFaultProposal()
    states = [np.array(s) for s in itertools.product(range(4), repeat=2)]
    for a in states:
        for b in states:
            qab = kernel.probability(a, b, problem, p)
            qba = kernel.probability(b, a, problem, p)
            if not qab or not problem.is_faulty(a) or not problem.is_faulty(b):
                continue
            pi_a, pi_b = np.exp(problem.log_prob(a, p)), np.exp(problem.log_prob(b, p))
            flow_ab = pi_a * qab * min(1, pi_b * qba / (pi_a * qab))
            flow_ba = pi_b * qba * min(1, pi_a * qab / (pi_b * qba))
            assert flow_ab == pytest.approx(flow_ba)
