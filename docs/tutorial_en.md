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

## Your normalized noise

A custom noise object has `n`, matching `alphabets`, `sample(p, rng)`, `log_prob(state, p)`, and JSON-compatible `metadata()`. Its `log_prob` is the normalized log probability of the **full** state under parameter `p`. Return negative infinity for zero support. The sampler must draw from that same distribution. This example uses two different per-qubit rates while retaining a scalar ladder parameter:

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

`minimum_weight_initial_state(code)` and `maximum_weight_initial_state(code)` choose among minimum representatives of the code's logical-basis cosets. `observable_sector_initial_state(code, bits)` requests a particular nonzero observable sector even when logical bases are independent, and `random_logical_sector_initial_state(code, seed=...)` chooses a nonzero sector. These are candidates: verify that the state lies in the noise support and fails under your actual decoder and predicate before passing it as `initial_state` to `sample_faulty`. Large stabilizer ranks use SciPy MILP and require proven optimality within `time_limit`.

For repeated decoding, `SamplingConfig(cache_cap=1000, cache_policy="lru")` applies a strict LRU cache; `"freeze"` stops adding entries at the cap, while `"research_clear"` checks the soft cap every ten steps. `KernelConfig(zanella_fastpath=True)` accelerates supported product noises without changing their target distribution. `diagnose` can summarize multiple chains, but an apparently healthy weight series is insufficient evidence of mixing. `evaluate_convergence` screens chain scaling, late stationarity, different starting populations, and IAT versus an independently estimated direct-MC **conditional observable variance**. Without that variance or a second initialization population, the corresponding checks remain unresolved.

## Physical circuit faults

`stim_noise_locations(circuit)` lists supported single- and two-qubit Pauli noise target groups. A `CircuitFaultModel` assigns each selected location one exclusive category: no fault or one fault label. `CircuitFaultNoise` uses explicit location probabilities; `uniform_fault_noise(model)` is a convenience choice. The circuit's native noise probabilities are ignored by the physical likelihood and need not equal the supplied fault probabilities. `surface_logical_idle_problem(distance=3, decoder_p=0.01, basis="Z")` constructs a 2d-round rotated-surface midpoint-observable baseline with a PyMatching decoder. The DEM is used to construct that decoder; sampled states remain physical location choices. See `examples/circuit_baseline.py` for a runnable direct-MC example.

Conditional circuit MCMC requires an explicit physical kernel: `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)`. The default Z+H mixture and stabilizer flip do not apply to this state space. The circuit builder supports specified Pauli noise instructions on deterministic Clifford detector circuits; it does not handle non-Pauli faults or correlations between locations.
