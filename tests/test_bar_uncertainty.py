"""Cross-chain BAR uncertainty contracts on independent conditional chains."""

import math

import numpy as np
import pytest

from mcmc4qec import (BinaryLinearModel, CallableDecoder, IndependentBitFlip,
                      KernelConfig, Problem, SamplingConfig, direct_mc, exact)
from mcmc4qec.estimation import EstimationResult, _cross_chain_covariance, estimate_logical_error
from mcmc4qec.diagnostics import paper_burn_in_cut


def _problem():
    return Problem(BinaryLinearModel([[1, 1]], [[1, 0]]),
                   IndependentBitFlip(2),
                   CallableDecoder(lambda syndrome: [0], identifier="zero"))


def test_independent_chain_standard_error_and_shared_rung_covariance():
    # Constant traces give one BAR ratio per chain without within-chain noise.
    # The two edges share the middle chain, so their covariance is retained.
    edge1 = (np.array([[0.0], [1.0], [2.0]]),
             np.array([[0.0], [0.0], [0.0]]))
    edge2 = (np.array([[0.0], [0.0], [0.0]]),
             np.array([[2.0], [1.0], [0.0]]))
    covariance = _cross_chain_covariance([edge1, edge2])
    chain_ratios = np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]])
    assert np.allclose(covariance, np.cov(chain_ratios, rowvar=False, ddof=1) / 3)
    assert math.sqrt(covariance[0, 0]) == pytest.approx(0.5 / math.sqrt(3))


def test_same_pooled_point_estimate_and_metadata():
    problem = _problem()
    kwargs = dict(anchor=exact(problem, .4), config=SamplingConfig(
        samples=80, burn_in=20, chains=3, kernels=KernelConfig(cluster_k=1)),
        seed=25, bootstrap_replicates=8, bootstrap_block_length=4)
    block = estimate_logical_error(problem, [.4, .25, .1], **kwargs)
    cross = estimate_logical_error(problem, [.4, .25, .1], uncertainty="cross_chain", **kwargs)
    assert cross.log_estimates == block.log_estimates
    assert cross.adjacent_log_ratios == block.adjacent_log_ratios
    assert cross.metadata["uncertainty_method"].startswith("cross-chain")
    assert block.metadata["uncertainty_method"].startswith("shared-rung circular")
    assert cross.metadata["config"]["bootstrap_successes"] == 0
    assert cross.bootstrap_log_ratio_covariance is None
    restored = EstimationResult.from_json(cross.to_json())
    assert restored.metadata == cross.metadata
    assert restored.intervals == cross.intervals


def test_mc_anchor_variance_is_independent_of_shared_rung_covariance():
    problem = _problem()
    anchor = direct_mc(problem, .4, trials=1000, seed=12)
    result = estimate_logical_error(problem, [.4, .25, .1], anchor=anchor,
        config=SamplingConfig(samples=80, burn_in=20, chains=4,
                              kernels=KernelConfig(cluster_k=1)),
        seed=25, uncertainty="cross_chain")
    covariance = np.asarray(result.metadata["cross_chain_log_ratio_covariance"])
    anchor_var = (1-anchor.estimate)/(anchor.trials*anchor.estimate)
    assert result.log_standard_errors[0]**2 == pytest.approx(anchor_var)
    assert result.log_standard_errors[-1]**2 == pytest.approx(anchor_var+covariance.sum())


def test_invalid_method_and_single_chain_rejected():
    problem = _problem()
    anchor = exact(problem, .4)
    with pytest.raises(ValueError, match="uncertainty"):
        estimate_logical_error(problem, [.4, .2], anchor=anchor, uncertainty="wrong")
    with pytest.raises(ValueError, match="two"):
        estimate_logical_error(problem, [.4, .2], anchor=anchor,
                               uncertainty="cross_chain", config=SamplingConfig(chains=1))


def test_small_exact_reference_coverage_smoke():
    problem = _problem()
    truth = exact(problem, .2).estimate
    anchor = exact(problem, .4)
    config = SamplingConfig(samples=120, burn_in=30, chains=4,
                            kernels=KernelConfig(cluster_k=1))
    covered = 0
    for seed in range(10):
        result = estimate_logical_error(problem, [.4, .2], anchor=anchor,
            config=config, seed=seed, uncertainty="cross_chain")
        assert result.interval is not None
        covered += result.interval[0] <= truth <= result.interval[1]
    assert covered >= 5


def test_research_style_iterated_geyer_cut():
    # The first value was checked against the read-only RIMC postprocess.burn_in.
    trace = np.random.default_rng(71).integers(0, 3, 250).astype(float)
    assert paper_burn_in_cut(trace) == (6, False)
    assert paper_burn_in_cut(np.ones(40)) == (20, True)
    with pytest.raises(ValueError, match="one chain"):
        paper_burn_in_cut(np.ones((2, 40)))
