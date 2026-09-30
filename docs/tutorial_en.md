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
