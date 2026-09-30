"""Anchored BAR ladder on a small, exactly enumerable CSS problem."""

import numpy as np

from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip, KernelConfig,
                      Problem, SamplingConfig, estimate_logical_error, exact)


def main():
    code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
                   [[1, 1, 1]], [[1, 0, 0]])
    decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                              identifier="repetition3-minimum-weight-v1")
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
    ladder = [0.4, 0.25, 0.1]
    result = estimate_logical_error(
        problem, ladder, anchor=exact(problem, ladder[0]),
        config=SamplingConfig(samples=200, burn_in=30,
                              kernels=KernelConfig(cluster_k=1)),
        seed=73, bootstrap_replicates=30,
    )
    for p, estimate, interval in zip(ladder, result.estimates, result.intervals):
        print(f"p={p}: BAR P_L={estimate:.5f}, interval={interval}")
    print("Exact final P_L:", exact(problem, ladder[-1]).estimate)


if __name__ == "__main__":
    main()
