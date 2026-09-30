# Public API

The top-level names below match `mcmc4qec.__all__` in this revision. Import code factories from `mcmc4qec.codes`. The contracts require deterministic decoding and normalized noise probabilities on the entire stated state space. A probability is for the complete experiment represented by the model; a phenomenological result is not a per-round rate.

| Names | Purpose and main constraints |
| --- | --- |
| `Model`, `Noise`, `Decoder` | Protocols for state validation, normalized `log_prob`, sampling, logical prediction, and JSON-compatible metadata. |
| `BinaryLinearModel`, `CSSCode` | Binary syndrome/observable model and validated CSS matrices. `logical_basis="paired"` requires identity cross-pairing; explicit `"independent"` accepts invertible cross-pairing without rebasing rows. Invalid dimensions, nonbinary matrices, or CSS commutation raise `ValueError`. |
| `CallableDecoder`, `CallableFailure`, `Problem` | Bind deterministic logical predictions and one failure definition across exact, MC, and MCMC. Identifiers and settings remain caller-maintained provenance. |
| `IndependentBitFlip`, `DepolarizingNoise`, `PhenomenologicalNoise` | Independent binary, joint I/X/Y/Z categorical, and bounded spacetime noise. Zero support has log probability `-inf`. |
| `DepolarizingModel`, `PhenomenologicalModel` | Full Pauli observables and explicit repeated-measurement boundaries; `PhenomenologicalModel` requires rounds, boundary choices, representation, and data-noise type. |
| `KernelConfig`, `SamplingConfig` | Kernel weights sum to one without implicit normalization; separate lazy probability, burn-in, thinning, chain count, and finite initialization budget. |
| `exact`, `direct_mc`, `sample_faulty` | Exact finite enumeration (limited by `max_states`), fixed-trial MC with a 95% Wilson interval, and failure-conditioned MCMC. They return `Result`; `sample_faulty` may raise `InitializationError`. |
| `spawn_seeds` | Deterministic independent child integer seeds for caller-managed workers. |
| `diagnose` | Weight-trace IAT, ESS, and split R-hat when meaningful; diagnostics do not establish convergence or ergodicity. |
| `Result`, `__version__` | JSON-serializable result and package version. A zero observed MC count retains an upper bound and does not establish zero true mass. |
| `DecoderAdapter`, `PyMatchingAdapter`, `matching_from_check_matrix` | Wrap a decoder with explicit `output_kind`; physical corrections require `logical_map`. The check-matrix helper rejects columns of degree above two. PyMatching correlation choice must be explicit. |
| `SectorDecoder`, `HistoryDecoder` | Compose sector predictions or transform an explicit syndrome history for a decoder. They do not change the joint noise distribution. |
| `from_stim_dem`, `from_stim_circuit`, `matching_from_dem` | Build latent DEM model/noise, convert a Stim circuit with explicit approximation options, and make a graphlike DEM decoder. These require optional Stim/PyMatching as applicable. |
| `estimate_logical_error`, `EstimationResult`, `bennett_log_ratio`, `OverlapError` | Anchored BAR ladder, its result, an adjacent log-ratio primitive, and the insufficient-overlap error. A standard ladder keeps one failure set; the explicit decoder-dependent mode is approximate. |

Additional code factories in `mcmc4qec.codes` currently include `make_toric_code(d)` and `make_surface_code(d)`. They require optional `ldpc` and `bposd`, return `CSSCode`, and reject invalid distances. See [the tutorial](tutorial_en.md) for custom components and [the README](../README.md) for a quickstart.

`exact(problem, p, max_states=...)` returns an absolute logical failure probability and, when failure mass is positive, a failure-conditioned nonzero-coordinate count. `direct_mc(problem, p, trials=..., seed=...)` uses a fixed trial count. `sample_faulty(problem, p, config=..., seed=..., initial_state=...)` returns states shaped `(chains, samples, n)`; it does not return absolute `P_L`. `estimate_logical_error(problem, ladder, anchor=..., config=..., ...)` returns per-rung absolute estimates, log estimates, intervals where available, warnings, and diagnostics. Its exact or positive fixed-trial MC anchor must match the first rung's model, noise, decoder, failure definition, and probability. `OverlapError` means the sampled adjacent ensembles had no observed bidirectional support overlap.

The default Z/H mixture uses weights 0.7/0.3, `cluster_k=2`, one chain, and a separate 0.05 lazy probability. Rejections and lazy moves remain chain steps. A custom `Noise.log_prob(state, p)` must return the normalized log probability on the same state space used by `sample`; invalid values and mismatched state dimensions are rejected. `p` may be a scalar or, for models requiring it, an explicit parameter dictionary. For phenomenological models, `p={"data": ..., "measurement": ...}` describes the entire bounded experiment. Optional decoders must return a deterministic prediction of logical observables; adapters never infer whether output is a correction from its shape.
