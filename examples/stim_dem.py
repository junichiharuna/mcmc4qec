"""Three hand-written DEM mechanisms, not a physical-circuit reproduction.

Requires the optional Stim dependency. The ^ fragments share one latent fault.
"""
from itertools import product

import numpy as np
import stim

from mcmc4qec import CallableDecoder, Problem, from_stim_dem, exact, direct_mc


def main():
    dem = stim.DetectorErrorModel("""
        error(0.10) D0 L0 ^ D1
        error(0.05) D0
        error(0.02) D1
    """)
    model, noise = from_stim_dem(dem, identifier="three-mechanism-demo")
    assert model.n == 3
    latent = np.array(list(product((0, 1), repeat=model.n)), dtype=bool)
    detectors, observables, replayed = dem.compile_sampler(seed=41).sample(
        shots=len(latent), return_errors=True, recorded_errors_to_replay=latent,
    )
    assert np.array_equal(replayed, latent)
    assert np.array_equal(detectors, latent @ model.H.T % 2)
    assert np.array_equal(observables, latent @ model.L.T % 2)
    decoder = CallableDecoder(
        lambda syndrome: [int(np.all(syndrome))],
        identifier="predict-correlated-mechanism-on-two-clicks-v1",
    )
    problem = Problem(model, noise, decoder)
    reference = exact(problem, None)
    mc = direct_mc(problem, None, trials=2_000, seed=42)
    print("Three latent mechanisms retained; ^ does not introduce an independent fault.")
    print("Stim replay agrees with H/L for all eight latent configurations.")
    print(f"Fixed DEM (p=None): exact P_L={reference.estimate:.6f}, direct MC={mc.estimate:.6f}")
    print(f"Direct MC Wilson95 interval: {mc.interval}")
    print("This example samples independent DEM mechanisms; physical fault equivalence is not inferred.")


if __name__ == "__main__":
    main()
