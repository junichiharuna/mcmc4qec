"""Small exact-reference coverage smoke test for anchored BAR intervals."""

import numpy as np

from mcmc4qec import (BinaryLinearModel, CallableDecoder, IndependentBitFlip,
                      KernelConfig, Problem, SamplingConfig, exact)
from mcmc4qec.estimation import estimate_logical_error


def test_small_problem_bar_intervals_cover_exact_across_seeds():
    # Failure is the first bit; the second bit remains a nontrivial nuisance
    # coordinate. Exact P(F)=p at both rungs, independent of MCMC.
    problem = Problem(BinaryLinearModel([[1, 1]], [[1, 0]]),
                      IndependentBitFlip(2),
                      CallableDecoder(lambda syndrome: [0], identifier="zero"))
    ladder = [0.4, 0.2]
    truth = exact(problem, ladder[-1]).estimate
    anchor = exact(problem, ladder[0])
    config = SamplingConfig(samples=120, burn_in=30, chains=2,
                            kernels=KernelConfig(cluster_k=1))
    covered = 0
    widths = []
    for seed in range(10):
        result = estimate_logical_error(problem, ladder, anchor=anchor,
                                        config=config, seed=seed,
                                        bootstrap_replicates=24,
                                        bootstrap_block_length=8)
        assert result.interval is not None
        covered += result.interval[0] <= truth <= result.interval[1]
        widths.append(result.interval[1] - result.interval[0])
    # A loose gross-regression screen, not a binomial proof of nominal coverage.
    assert covered >= 5
    assert all(np.isfinite(width) and width > 0 for width in widths)
