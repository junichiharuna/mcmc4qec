# Bring your own code, noise, and decoder

All components share a finite state space and a deterministic failure definition. The examples below use a three-qubit CSS code so you can run each in seconds. Install the checkout with `python -m pip install -e .` first.

## Your CSS matrices

Supply binary `hx`, `hz`, `lx`, and `lz` with the same number of columns. By default the logical rows must be complete paired bases: `hx @ hz.T = 0`, stabilizer/logical commutators vanish, and `lx @ lz.T` is the identity over GF(2). If you deliberately use independently ordered logical bases, pass `logical_basis="independent"`; their cross-pairing must be invertible, and the input rows are not rebased. `CSSCode` validates these conditions and raises `ValueError` on a mismatch. In the bit-flip model, `hz` measures X errors and `lz` maps them to logical observables.

```python
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, IndependentBitFlip, Problem, exact

code = CSSCode(hx=np.zeros((0, 3), dtype=int),
               hz=[[1, 1, 0], [0, 1, 1]],
               lx=[[1, 1, 1]], lz=[[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="my-repetition3-logical-decoder-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
print(exact(problem, 0.25).estimate)  # 0.15625
```

`CallableDecoder` returns predicted **logical observables**, not physical corrections. Keep the same decoder and failure predicate for standard BAR ladders.

## BAR with default settings

For the same three-qubit code, supply a ladder starting at a noise rate where failures are reasonably common:

```python
import numpy as np
from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip,
                      Problem, estimate_logical_error)

code = CSSCode(hx=np.zeros((0, 3), dtype=int),
               hz=[[1, 1, 0], [0, 1, 1]],
               lx=[[1, 1, 1]], lz=[[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="my-repetition3-logical-decoder-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
ladder = [0.4, 0.25, 0.1]
result = estimate_logical_error(problem, ladder, seed=73)
for p, estimate, interval in zip(ladder, result.estimates, result.intervals):
    print(f"p={p}: P_L={estimate:.6g}, interval={interval}")
```

No `config` or `anchor` is required. The default `SamplingConfig()` retains 1,000 samples after 100 burn-in steps per rung, with one chain, thinning 1, Z/H weights 0.7/0.3, `cluster_k=2`, and lazy probability 0.05. Pass a `SamplingConfig` to tune the run; these defaults do not establish research accuracy, and physical circuit models still require appropriate kernel settings.

The first rung's anchor is computed by exact enumeration if the product of coordinate alphabet sizes is at most 4,096, and otherwise by 10,000 fixed direct-MC trials. For example, `estimate_logical_error(problem, ladder, anchor_max_states=0, anchor_trials=20000, seed=73)` forces a 20,000-trial MC anchor. Its independent RNG and uncertainty are recorded and propagated into the result. You can instead provide `anchor=exact(problem, ladder[0])` or a compatible independent `direct_mc` result.

An MC anchor with zero failures or all trials failing raises `ValueError`; increase the trial budget, change the first noise rate, or supply a valid anchor. The automatic calculation does not extend its trial count until failures appear. Inspect warnings and `result.metadata["anchor"]`, and check mixing and sensitivity before interpreting intervals. See [automatic-anchor settings](api_en.md#automatic-bar-anchor) for validation and provenance details.

## Static CSS phase flips

For binary Z-error support, `code.phase_flip_model()` measures syndrome with X checks (`hx`), reads logical observables with `lx`, and uses Z stabilizer rows (`hz`). The same `IndependentBitFlip(code.n)` represents the Bernoulli product distribution on Z-error support. For example, this three-qubit CSS code protects X errors but has no X checks to detect Z errors:

```python
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, IndependentBitFlip, Problem, exact

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
z_decoder = CallableDecoder(lambda syndrome: [0], identifier="zero-z-v1")
problem = Problem(code.phase_flip_model(), IndependentBitFlip(code.n), z_decoder)
print(exact(problem, 0.25).estimate)  # 0.4375
```

With optional PyMatching, `mwpm_decoder(code, errors="Z")` builds from `hx` and maps its physical correction through `lx`; `bposd_decoder(code, p, errors="Z", **kw)` does the same with a fixed BP-OSD prior. Both default to `errors="X"`, preserving the existing `hz`/`lz` decoder. A rectangular toric geometry alone does not establish unequal aggregate X/Z failure rates: compare them with exact enumeration when feasible or report Monte Carlo uncertainty. For bounded repeated measurements, `PhenomenologicalModel(..., data_noise="phase_flip")` uses binary Z data faults and noisy X checks. Its `PhenomenologicalNoise` still needs explicit `{"data": ..., "measurement": ...}` probabilities for the complete experiment.

## Your normalized noise

A custom noise object has `n`, matching `alphabets`, `sample(p, rng)`, `log_prob(state, p)`, and JSON-compatible `metadata()`. Its `log_prob` is the normalized log probability of the **full** state under parameter `p`. Return negative infinity for zero support. The sampler must draw from that same distribution. This example uses three different per-qubit rates while retaining a scalar ladder parameter:

```python
import math
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, Problem, exact

class UnequalBitFlip:
    n = 3
    alphabets = (2, 2, 2)
    scales = np.array([0.5, 1.0, 1.5])

    def sample(self, p, rng):
        rates = p * self.scales
        if np.any((rates < 0) | (rates > 1)):
            raise ValueError("rates must be in [0, 1]")
        return (rng.random(self.n) < rates).astype(np.uint8)

    def log_prob(self, state, p):
        rates = p * self.scales
        if np.any((rates < 0) | (rates > 1)):
            raise ValueError("rates must be in [0, 1]")
        state = np.asarray(state)
        if state.shape != (self.n,) or np.any((state != 0) & (state != 1)):
            raise ValueError("invalid state")
        probabilities = np.where(state, rates, 1 - rates)
        return float(np.log(probabilities).sum()) if np.all(probabilities > 0) else -math.inf

    def metadata(self):
        return {"identifier": "unequal-bit-flip-v1", "scales": self.scales.tolist()}

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="my-repetition3-logical-decoder-v1")
print(exact(Problem(code.bit_flip_model(), UnequalBitFlip(), decoder), 0.25).estimate)
```

For correlated noise, compute the true joint state probability. Replacing it with independent marginals changes both the target distribution and BAR ratios. Check normalization by enumeration on a small instance before sampling.

## Your physical-correction decoder

An existing object's `decode(syndrome)` may return a physical correction instead of logical observables. Declare `output_kind="correction"` and supply `logical_map` (`L`) explicitly. The adapter multiplies `L @ correction % 2`. The following deterministic table is a stand-in for an external decoder and can be replaced by a configured BP-OSD object:

```python
import numpy as np
from mcmc4qec import CSSCode, IndependentBitFlip, Problem, exact
from mcmc4qec.adapters import DecoderAdapter

class CorrectionDecoder:
    corrections = {(0, 0): (0, 0, 0), (1, 0): (1, 0, 0),
                   (1, 1): (0, 1, 0), (0, 1): (0, 0, 1)}

    def decode(self, syndrome):
        return self.corrections[tuple(syndrome)]

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
adapter = DecoderAdapter(CorrectionDecoder(), output_kind="correction",
                         logical_map=code.lz, identifier="my-correction-decoder-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), adapter)
print(exact(problem, 0.25).estimate)  # 0.15625
```

For a decoder returning logical predictions directly, use `output_kind="observable"` and omit `logical_map`. `settings` records configuration for provenance but does not configure the wrapped decoder. Pin its behavior during a run. A decoder for repeated measurements must accept the full selected syndrome history or difference representation. A custom failure predicate receives `(state, predicted, truth)` and must return a Boolean; the same predicate is used by exact enumeration, direct MC, and conditional MCMC. Do not assume it stays unchanged under stabilizer flips.

## Built-in codes and decoders

Install `python -m pip install -e ".[codes,matching]"` for the HGP-based factories and PyMatching. The same `Problem` contract applies to these codes:

```python
from mcmc4qec import IndependentBitFlip, Problem, direct_mc
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import mwpm_decoder

code = make_toric_code(3)
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
print(direct_mc(problem, 0.1, trials=100, seed=3).estimate)
```

Other factories include toric, surface, asymmetric toric, Hamming HGP, BB72/108/144, and concatenated Steane. Some preserve independently ordered logical rows through `logical_basis="independent"`; treat the rows as the supplied basis rather than assuming `lx[i]` flips only observable `i`. `bposd_decoder(code, p, **kw)` fixes its channel prior at construction. The depolarising sector constructors return both logical sectors in model order, while `DepolarizingNoise` continues to sample correlated X/Z components through joint I/X/Y/Z labels.

## Initialization, cache, and diagnostics

Statistical errors accompany numerical results by default. A conditional MCMC run returns its weight mean and IAT-based Monte Carlo standard error. Use `diagnostics=True` for additional numerical ACF, blocking and bootstrap results, or provide `DiagnosticsConfig` to bound their cost:

```python
from mcmc4qec import (BinaryLinearModel, CallableDecoder, DiagnosticsConfig,
                      IndependentBitFlip, KernelConfig, Problem, SamplingConfig,
                      diagnostic_report, sample_faulty)

# Failure is x[0] == 1; x[1] remains a variable conditional observable.
problem = Problem(BinaryLinearModel([[1, 1]], [[1, 0]]), IndependentBitFlip(2),
                  CallableDecoder(lambda syndrome: [0], identifier="zero-v1"))
run = sample_faulty(problem, 0.3, seed=41,
    config=SamplingConfig(samples=128, burn_in=32, chains=4,
                          kernels=KernelConfig(cluster_k=1)),
    diagnostics=DiagnosticsConfig(max_lag=32, block_sizes=(1, 4, 16, 32),
                                  bootstrap_replicates=100, seed=7))
print("Conditional mean and MCSE:", run.conditional_weight,
      run.conditional_weight_standard_error)
report = run.diagnostics["trace_analysis"]
print("Classical split R-hat:", report["rhat"])
print("Chain IAT / ESS:", report["chain_iat"], report["chain_ess"])
print("ACF:", report["acf"])
print("Batch-mean SE scan:", report["blocking"])
print("Bootstrap mean intervals:", report["bootstrap"]["blocks"])

# Alternative observables can be analyzed afterwards without resampling.
last_bit = diagnostic_report(run, observable=lambda state: float(state[-1]),
    observable_name="last bit", config=DiagnosticsConfig(bootstrap_replicates=0))
print("Last-bit mean and MCSE:", last_bit["mean"], last_bit["iat_mcse"])
```

Omit `diagnostics` to skip extra analysis while still returning the default mean MCSE. In BAR, the same keyword adds per-rung reports to `result.diagnostics[i]["trace_analysis"]`. These are conditional observable errors; the logical-probability errors remain in `result.intervals` and `result.log_standard_errors`. The detailed analysis has its own RNG and does not affect sampled states or BAR uncertainty. `None` means unavailable, not zero error. Inspect block-length sensitivity, short/constant chains, and warnings before interpreting intervals. See the [API formulas and fields](api_en.md#default-statistical-errors-and-optional-detailed-diagnostics).

`minimum_weight_initial_state(code)` and `maximum_weight_initial_state(code)` choose among minimum representatives of the code's logical-basis cosets. `observable_sector_initial_state(code, bits)` requests a particular nonzero observable sector even when logical bases are independent, and `random_logical_sector_initial_state(code, seed=...)` chooses a nonzero sector. These are candidates: verify that the state lies in the noise support and fails under your actual decoder and predicate before passing it as `initial_state` to `sample_faulty`. Large stabilizer ranks use SciPy MILP and require proven optimality within `time_limit`.

For repeated decoding, `SamplingConfig(cache_cap=1000, cache_policy="lru")` applies a strict LRU cache; `"freeze"` stops adding entries at the cap, while `"research_clear"` checks the soft cap every ten steps. `KernelConfig(zanella_fastpath=True)` accelerates supported product noises without changing their target distribution. `diagnose` can summarize multiple chains, but an apparently healthy weight series is insufficient evidence of mixing. `evaluate_convergence` screens chain scaling, late stationarity, different starting populations, and IAT versus an independently estimated direct-MC **conditional observable variance**. Without that variance or a second initialization population, the corresponding checks remain unresolved.

## Physical circuit faults

`stim_noise_locations(circuit)` lists supported single- and two-qubit Pauli noise target groups. A `CircuitFaultModel` assigns each selected location one exclusive category: no fault or one fault label. `CircuitFaultNoise` uses explicit location probabilities; `uniform_fault_noise(model)` is a convenience choice. The circuit's native noise probabilities are ignored by the physical likelihood and need not equal the supplied fault probabilities. `surface_logical_idle_problem(distance=3, decoder_p=0.01, basis="Z")` constructs a 2d-round rotated-surface midpoint-observable baseline with a PyMatching decoder. The DEM is used to construct that decoder; sampled states remain physical location choices. See `examples/circuit_baseline.py` for a runnable direct-MC example.

Conditional circuit MCMC supports physical single-fault moves with `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)` and Z+OBF with `KernelConfig(zanella=0.7, single=0.3, cluster=0, stabilizer=0)`, including mixtures of these moves. H requires explicit `circuit_groups`, and circuit stabilizer moves remain unavailable. The circuit builder supports specified Pauli noise instructions on deterministic Clifford detector circuits; it does not handle non-Pauli faults or correlations between locations. See [the kernel comparison](../examples/circuit_zanella.py) for conditional weights, acceptance rates, and IAT; these conditional samples do not estimate absolute `P_L`.

Each `circuit_groups` entry is a nonempty group of location indices from `model.locations`. Groups must be disjoint, and every location within a group must have the same channel and ordered fault alphabet; equal alphabet size alone is insufficient. If locations 1 and 2 meet that contract, `KernelConfig(single=.2, zanella=.4, circuit_single=.2, cluster=.2, cluster_k=1, circuit_groups=((1, 2),))` mixes all four moves. Omitted locations are unchanged by H. Groups are selected uniformly independently of the state; unavailable relocation branches remain self-loops, with no mixture renormalization. H preserves occupancy within each group and is generally reducible alone; mixing with other moves does not by itself prove connectivity of an arbitrary failure set. The proposal is also available as `PhysicalClusterExchange` from `mcmc4qec.circuit`.

With `zanella_fastpath=True`, exact built-in circuit model/noise pairs with the standard failure predicate reuse physical detector/observable effect tables and update only changed locations. Custom subclasses or failure predicates retain the general path. `python benchmarks/bench_circuit_step.py --steps 100 --compare-delta` compares the dedicated and general paths from a common faulty state and checks retained trajectories and acceptance counts.
