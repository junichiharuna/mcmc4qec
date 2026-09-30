"""Small bit-flip example; run against an installed mcmc4qec package."""

import numpy as np

from mcmc4qec import (
    CSSCode,
    CallableDecoder,
    IndependentBitFlip,
    KernelConfig,
    Problem,
    Result,
    SamplingConfig,
    diagnose,
    direct_mc,
    exact,
    sample_faulty,
)


def main():
    code = CSSCode(
        hx=np.zeros((0, 3), dtype=int),
        hz=[[1, 1, 0], [0, 1, 1]],
        lx=[[1, 1, 1]],
        lz=[[1, 0, 0]],
    )
    # The minimum-weight correction acts on qubit 0 only for syndrome 10.
    # lz = [1, 0, 0] maps that correction to its logical observable.
    decoder = CallableDecoder(
        lambda syndrome: [int(tuple(syndrome) == (1, 0))],
        identifier="repetition3-minimum-weight-v1",
    )
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
    p = 0.25
    reference = exact(problem, p)
    mc = direct_mc(problem, p, trials=10_000, seed=18)
    samples = sample_faulty(
        problem,
        p,
        config=SamplingConfig(
            samples=2_000,
            burn_in=100,
            chains=2,
            # Two occupied/empty pairs cannot be exchanged in this tiny code.
            kernels=KernelConfig(cluster_k=1),
        ),
        seed=31,
    )
    restored = Result.from_json(samples.to_json())
    assert np.array_equal(restored.states, samples.states)
    assert np.isclose(reference.estimate, 3 * p**2 - 2 * p**3)
    print(f"Exact P_L: {reference.estimate:.6f}")
    print(f"Direct MC P_L: {mc.estimate:.6f}; 95% Wilson interval: {mc.interval}")
    print(f"Exact E[weight | faulty]: {reference.conditional_weight:.6f}")
    print(f"MCMC E[weight | faulty]: {samples.states.sum(axis=-1).mean():.6f}")
    print("Diagnostics (do not establish convergence):", diagnose(samples))
    print("Result JSON round trip: preserved retained states")


if __name__ == "__main__":
    main()
