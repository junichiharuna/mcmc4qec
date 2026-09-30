# mcmc4qec
Estimate logical error probabilities for CSS quantum codes with exact enumeration, direct Monte Carlo, and anchored BAR splitting.
Sample failure-conditioned errors with configurable OBF, Zanella (Z), cluster exchange (H), and stabilizer kernels.
Bring your own code, normalized noise distribution, deterministic decoder, and failure predicate.

This pre-alpha package is under active validation. Install from a local checkout with `python -m pip install -e ".[matching]"` for the following example:

```python
import numpy as np
from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig, direct_mc, sample_faulty
from mcmc4qec.adapters import matching_from_check_matrix
from mcmc4qec.codes import make_toric_code

code = make_toric_code(5)
decoder = matching_from_check_matrix(code.hz, logical_map=code.lz,
                                     identifier="toric-d5-mwpm")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
p = 0.1
mc = direct_mc(problem, p, trials=2_000, seed=11)
chain = sample_faulty(problem, p, config=SamplingConfig(samples=100, burn_in=20), seed=12)
print("Direct MC P_L and 95% Wilson interval:", mc.estimate, mc.interval)
print("Z+H E[weight | faulty]:", np.count_nonzero(chain.states, axis=-1).mean())
```

The conditional chain measures properties **within** the failure set; its state frequency does not estimate absolute `P_L`. The default has Z weight 0.7, H weight 0.3, `cluster_k=2`, one chain, and a separate lazy probability of 0.05. Rejected and lazy steps remain in the trace. Run the full example with `python examples/toric_pymatching.py`.

An anchored BAR ladder estimates `P_L(p)` across probabilities. This compact example uses a small enumerable code so its first rung can be anchored exactly:

```python
from mcmc4qec import SamplingConfig, estimate_logical_error, exact

# problem is a fixed-decoder Problem; see examples/bar_ladder.py.
ladder = [0.4, 0.25, 0.1]
result = estimate_logical_error(problem, ladder, anchor=exact(problem, ladder[0]),
                                config=SamplingConfig(samples=200, burn_in=30), seed=73)
print(result.estimates, result.intervals)
```

The complete runnable ladder, including its three-bit `Problem`, is in [examples/bar_ladder.py](examples/bar_ladder.py). Keep the same decoder and failure definition across a standard ladder. An MC anchor must observe positive failure mass. Missing observed support overlap raises `OverlapError`.

| Noise and state | OBF / Z / H | Stabilizer flip | Decoder connection |
| --- | --- | --- | --- |
| Static CSS bit-flip | Supported | Optional | PyMatching or deterministic user decoder; BP-OSD through `DecoderAdapter` |
| Static CSS depolarising | Supported with joint I/X/Y/Z labels | Optional | Full logical prediction; sector composition is a decoder choice |
| Phenomenological data and measurement faults | Supported | Unavailable | Decoder must consume the selected syndrome history or difference representation |
| Stim detector error model | Supported on latent mechanism bits | Unavailable | Matching from a graphlike DEM, or a user decoder |

`exact` enumerates small categorical state spaces; `direct_mc` uses a fixed trial count; `sample_faulty` samples normalized noise conditioned on failure; `estimate_logical_error` uses adjacent BAR ratios and an anchor. See the [API reference](docs/api_en.md) and [bring-your-own-components tutorial](docs/tutorial_en.md). Optional connections use `pip install ".[matching]"`, `".[bposd]"`, or `".[stim]"`.

Diagnostics such as ESS and split R-hat do not prove convergence, ergodicity, or correctness. A chain can remain trapped even when its weight trace looks healthy. The `p_dependent_decoder_approx` BAR mode explicitly ignores changes in failure sets and its interval omits that bias. Model support and initialization limits, observed overlap, finite samples, and block length also limit estimates. DEM sampling does not establish equivalence to every physical circuit noise model. The circuit baseline and research-code comparisons are documented separately as their validation becomes available.

The associated paper is in preparation. The software citation names junichi haruna as instructed by the project owner; DOI, release date, license, and public release details remain pending. See [CITATION.cff](CITATION.cff) and [CONTRIBUTING.md](CONTRIBUTING.md). No license has been selected and this repository has not been published as a public package.
