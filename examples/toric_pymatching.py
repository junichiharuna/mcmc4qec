"""Small toric-code PyMatching direct MC and conditional MCMC example."""

import numpy as np

from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig, direct_mc, sample_faulty
from mcmc4qec.adapters import matching_from_check_matrix
from mcmc4qec.codes import make_toric_code


def main():
    code = make_toric_code(5)
    decoder = matching_from_check_matrix(
        code.hz, logical_map=code.lz, identifier="toric-d5-mwpm"
    )
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
    p = 0.1
    mc = direct_mc(problem, p, trials=2_000, seed=11)
    chain = sample_faulty(problem, p, config=SamplingConfig(samples=100, burn_in=20), seed=12)
    print(f"Toric d=5, p={p}: direct MC P_L={mc.estimate:.4f}, interval={mc.interval}")
    print(f"Direct MC E[weight | faulty]={mc.conditional_weight:.3f}")
    print(f"Conditional MCMC E[weight | faulty]={np.count_nonzero(chain.states, axis=-1).mean():.3f}")
    print("Kernels:", chain.metadata["config"]["expanded_move_probabilities"])


if __name__ == "__main__":
    main()
