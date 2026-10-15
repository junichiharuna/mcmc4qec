"""A block-length sensitivity changes uncertainty, not the sampled experiment."""

from mcmc4qec import (BinaryLinearModel, CallableDecoder, IndependentBitFlip,
                      KernelConfig, Problem, SamplingConfig, exact)
from mcmc4qec.estimation import estimate_logical_error


def test_block_length_preserves_sampling_and_point_estimate():
    problem = Problem(BinaryLinearModel([[1, 1]], [[1, 0]]),
                      IndependentBitFlip(2),
                      CallableDecoder(lambda syndrome: [0], identifier="zero"))
    kwargs = dict(anchor=exact(problem, .4), seed=6100,
                  config=SamplingConfig(samples=80, burn_in=20, chains=4,
                                        kernels=KernelConfig(cluster_k=1)),
                  bootstrap_replicates=12)
    results = [estimate_logical_error(problem, [.4, .25, .1],
               bootstrap_block_length=length, **kwargs) for length in (2, 8, 32)]
    for result in results[1:]:
        assert result.log_estimates == results[0].log_estimates
        assert result.adjacent_log_ratios == results[0].adjacent_log_ratios
        assert result.diagnostics == results[0].diagnostics
        assert result.metadata["rungs"] == results[0].metadata["rungs"]
        assert result.interval is not None
