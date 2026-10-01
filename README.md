# mcmc4qec
Estimate logical error probabilities for CSS quantum codes with exact enumeration, direct Monte Carlo, and anchored BAR splitting.
Sample failure-conditioned errors with configurable OBF, Zanella (Z), cluster exchange (H), and stabilizer kernels.

Public APIs include type annotations and a `py.typed` marker for IDEs and type checkers. See the [API contracts](docs/api_en.md) for supported inputs and custom components.
Bring your own code, normalized noise distribution, deterministic decoder, and failure predicate.

This pre-alpha package is under active validation. [日本語版](README_ja.md).

## Install and first run

Install a local checkout with `python -m pip install -e .` for core examples. The following toric example needs `python -m pip install -e ".[codes,matching]"`: `make_toric_code` currently needs the `codes` extra.

| Extra | Use |
| --- | --- |
| `codes` | Toric, surface, asymmetric toric, Hamming HGP, and BB code factories |
| `matching` | PyMatching decoders |
| `bposd` | BP-OSD decoder dependency |
| `stim` | Stim DEM and circuit examples |
| `plot` | Optional PNG plots in workflow scripts; CSV remains available without it |
| `notebooks` | Jupyter notebook execution and plotting |

Install several at once with `python -m pip install -e ".[codes,matching,bposd,stim,plot,notebooks]"`. See the [full example index](examples/README.md) for the dependencies of each file.

PyMatching 2.4 requires matplotlib itself. Workflow CSV fallback covers an unavailable pyplot drawing layer; it does not remove the decoder dependency.

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
print("Direct MC E[weight | faulty]:", mc.conditional_weight)
print("Z+H E[weight | faulty]:", np.count_nonzero(chain.states, axis=-1).mean())
```

The conditional chain measures properties **within** the failure set; its state frequency does not estimate absolute `P_L`. The default has Z weight 0.7, H weight 0.3, `cluster_k=2`, one chain, and a separate lazy probability of 0.05. Rejected and lazy steps remain in the trace. Run the full example with `python examples/toric_pymatching.py`.

An anchored BAR ladder estimates `P_L(p)` across probabilities. This compact example uses a small enumerable code so its first rung can be anchored exactly:

```python
import numpy as np
from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip, KernelConfig,
                      Problem, SamplingConfig, estimate_logical_error, exact)

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="repetition3-minimum-weight-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
ladder = [0.4, 0.25, 0.1]
result = estimate_logical_error(problem, ladder, anchor=exact(problem, ladder[0]),
                                config=SamplingConfig(samples=200, burn_in=30,
                                    kernels=KernelConfig(cluster_k=1)), seed=73)
print(result.estimates, result.intervals)
```

The complete runnable ladder, including its three-bit `Problem`, is in [examples/bar_ladder.py](examples/bar_ladder.py). Keep the same decoder and failure definition across a standard ladder. An MC anchor must observe positive failure mass. Missing observed support overlap raises `OverlapError`.

## Choose a starting point

| Goal | Start here |
| --- | --- |
| Estimate absolute `P_L` | [Steane exact/MC/BAR comparison](examples/steane_exact.py), [toric BAR curve](examples/workflows/pl_curve.py), or [BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| Explore a failure-conditioned distribution | [Conditional weight comparison](examples/workflows/conditional_weight.py), [multiple-chain checks](examples/workflows/convergence_check.py), or [diagnostics notebook](notebooks/03_conditional_sampling_and_diagnostics.ipynb) |
| Bring your own code, noise, or decoder | [CSS template](examples/templates/byo_css_bitflip.py), [noise template](examples/templates/byo_noise.py), [decoder template](examples/templates/byo_decoder.py), or [component notebook](notebooks/04_bring_your_own.ipynb) |
| Work with detector or physical circuit faults | [Stim DEM template](examples/templates/byo_stim_dem.py), [DEM example](examples/stim_dem.py), or [physical circuit baseline](examples/circuit_baseline.py) |

For a guided first run, open [the quickstart notebook](notebooks/01_quickstart.ipynb). The [example index](examples/README.md) lists every script and notebook, its required extras, and how to read its output. For component contracts, use the [API reference](docs/api_en.md) and [bring-your-own-components tutorial](docs/tutorial_en.md).

| Noise and state | OBF / Z / H | Stabilizer flip | Decoder connection |
| --- | --- | --- | --- |
| Static CSS bit-flip | Supported | Optional | PyMatching or deterministic user decoder; BP-OSD through `DecoderAdapter` |
| Static CSS phase-flip | Supported | Optional | PyMatching or BP-OSD with `errors="Z"`, using `hx`/`lx` |
| Static CSS depolarising | Supported with joint I/X/Y/Z labels | Optional | Full logical prediction; sector composition is a decoder choice |
| Phenomenological data and measurement faults | Supported | Unavailable | Decoder must consume the selected syndrome history or difference representation |
| Stim detector error model | Supported on latent mechanism bits | Unavailable | Matching from a graphlike DEM, or a user decoder |
| Physical Stim circuit locations | OBF, Z, and physical single-fault moves; H unavailable | Unavailable | Midpoint surface logical-idle baseline with PyMatching |

`exact` enumerates small categorical state spaces; `direct_mc` uses a fixed trial count; `sample_faulty` samples normalized noise conditioned on failure; `estimate_logical_error` uses adjacent BAR ratios and an anchor.

Code factories include toric and surface codes, asymmetric toric, Hamming HGP, BB72/108/144, Steane, and concatenated Steane; the current toric, surface, asymmetric toric, Hamming HGP, and BB factories need `".[codes]"`. Decoder constructors cover MWPM and BP-OSD for bit-flip and phase-flip (`errors="Z"`), plus explicit sector decoding for depolarising noise. `SamplingConfig(cache_cap=..., cache_policy=...)` bounds deterministic decode caching, and `KernelConfig(zanella_fastpath=True)` uses the verified product-noise path when available. Diagnostics now include multiple-chain summaries, exact CSS coset initialization helpers, and a four-check `evaluate_convergence` screen that requires an independent direct-MC conditional variance for a complete verdict. These checks cannot prove mixing or correctness.

The physical circuit baseline samples mutually exclusive fault labels at supported Stim noise locations. Choose physical single-fault moves with `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)`, or Z+OBF with `KernelConfig(zanella=0.7, single=0.3, cluster=0, stabilizer=0)`. Mixtures of these three moves are supported; H and stabilizer moves remain unavailable, so the default Z+H setting is unsupported. The surface logical-idle example evaluates a midpoint observable after the first d of 2d noisy rounds; its DEM is used for decoder construction, while sampling stays on physical locations. See the [physical baseline](examples/circuit_baseline.py) and [kernel comparison](examples/circuit_zanella.py).

Diagnostics such as ESS and split R-hat do not prove convergence, ergodicity, or correctness. A chain can remain trapped even when its weight trace looks healthy. The `p_dependent_decoder_approx` BAR mode explicitly ignores changes in failure sets and its interval omits that bias. Model support and initialization limits, observed overlap, finite samples, and block length also limit estimates. DEM sampling does not establish equivalence to every physical circuit noise model. The circuit baseline does not establish reproduction of published figures.

The associated paper is in preparation. The software citation names junichi haruna as instructed by the project owner; affiliation, DOI, release date, license, and public release details remain pending. See [CITATION.cff](CITATION.cff) and [CONTRIBUTING.md](CONTRIBUTING.md). No license has been selected and this repository has not been published as a public package.
