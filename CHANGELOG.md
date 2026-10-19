# Changelog

## Unreleased

- Add checked BP-LSD (order 0), BeliefFind, and Union-Find factories, including
  depolarizing sector adapters, small-code tests, and comparison examples.
  Reject unsupported native options and invalid corrections explicitly.
  These interface checks do not calibrate logical error rates or BAR coverage.
- Link current tile code-capacity results and unfinished low-noise validation
  from the English and Japanese README and documentation overview.

- Add `make_tile_code(l, m)` for the open-boundary weight-six tile family,
  paired CSS logical bases, BP-OSD integration tests and a runnable example.
  Published distance labels are not independently certified by the factory.
- Add a fixed-cohort PBS calibration driver with checked exact banks, compact
  traces, shared-rung BAR covariance, checksum-verified resume, and a two-node
  submission limit. Complete and audit 46,080 traces and 64,512 analysis rows;
  preserve coverage, bias, mixing diagnostics, and reproduction records.
- Document disconnected failure-state components for the default Z/H mixture
  in the fixed-decoder Steane calibration. Public defaults remain unchanged;
  neither longer traces nor wide intervals establish correct mixing.

- Allow BAR calls with both `config` and `anchor` omitted, retaining existing
  sampling defaults. Automatically enumerate up to 4,096 states or use 10,000
  fixed direct-MC trials, with configurable budgets, independent RNG, anchor
  uncertainty propagation, and recorded provenance. Reject zero-failure and
  all-failure MC anchors rather than extending the trial budget adaptively.

- Return conditional-weight mean and IAT-based Monte Carlo standard error by
  default, with unavailable errors represented as None.
- Add optional numerical ACF, batch-mean error scans, and per-chain circular
  bootstrap intervals alongside sampling and BAR results via diagnostics.
  Expose DiagnosticsConfig, diagnostic_report and analyze_traces for post-hoc
  custom observables; keep sampling and BAR uncertainty RNGs unchanged.

- Reduce per-step overhead while preserving seeded trajectories; defer reverse
  Zanella normalization for candidates outside the failure set.
- Add physical-circuit effect delta updates and opt-in cluster exchange with
  explicit compatible location groups; retain public sampling defaults.
- Enable strict mypy checking for package helpers and consumer contracts, with
  optional backend exceptions scoped to their namespaces.
- Add a fixed-seed, one-factor block-length calibration with exact anchors and
  recorded mixing diagnostics; finite experiments do not certify coverage.

- Rename the package and repository from the provisional `rimc` to `mcmc4qec`
  (import name `mcmc4qec`). No API change.

## 0.1.0.dev5 — development

- Add optional cross-chain BAR uncertainty with paired adjacent-rung covariance
  and independent anchor variance; retain pooled point estimates and the default
  block-bootstrap behavior. Document finite-chain bias and coverage assumptions.
- Add fixed-seed BAR protocol and length-comparison benchmarks, per-chain
  iterated burn cuts, checked exact-truth caching, and explicit distinctions
  between paper observable-mean experiments and BAR uncertainty estimates.
- Archive all 60 length-comparison runs and 240 protocol/anchor runs, with
  paired comparisons, Wilson intervals, finite-chain limitations, and an
  independently reviewed correction to unresolved diagnostic counts on CSV reload.
- Reuse Zanella proposal distributions across steps and avoid duplicate decoder
  validation on cache hits, preserving reference trajectories and RNG use.
- Publish two-run performance measurements for toric d=5/d=7 and BB72, including
  the remaining toric gap, and refresh affected example timings.

## 0.1.0.dev4 — development

- Add static CSS phase-flip models, Z-sector MWPM/BP-OSD construction,
  phenomenological phase-flip data, and a rectangular-toric X/Z example.
- Support OBF, Zanella, and physical single-fault mixtures on exclusive
  circuit locations, with variable alphabets and enumerated transition checks.
  Circuit cluster and stabilizer moves remain unavailable.
- Add a dedicated product-noise sampling path with the same proposal,
  acceptance, random-number consumption, and saved trajectories as reference
  sampling; record remaining research-runner performance gaps.
- Investigate toric BAR interval coverage against exact truth over repeated
  seeds, document controlled sensitivity checks, and update workflow guidance.
  Short runs and diagnostic checks do not guarantee research precision.
- Annotate public APIs and returned public methods, ship a PEP 561 marker,
  and check both package and consumer typing in CI.
- Extend installed-wheel checks to the two new examples and the type marker.

## 0.1.0.dev3 — development

- Add real-code examples, research workflows, editable component templates,
  and four self-contained executed Jupyter tutorials.
- Standardize example CLIs with quick runs, explicit seeds and output paths,
  and machine-readable summaries.
- Expand the English README and add a matching Japanese README and an
  example catalog with measured run times and scientific limitations.
- Add plotting and notebook extras, recursive installed-wheel verification,
  and CI coverage for quick examples and notebook execution.
- Reuse ideal circuit segments while constructing physical fault effects,
  preserving fault order and detector/observable columns.

## 0.1.0.dev2 — development

- Add real CSS code factories and MWPM/BP-OSD decoder constructors, with
  reproducible matrix, decoder, exact, Monte Carlo, and BAR research comparisons.
- Accept explicitly requested independent logical bases without changing the
  default paired-basis contract or the supplied observable ordering.
- Accelerate product-noise Zanella proposals and add configurable decoder
  caching and syndrome updates, with enumerated transition-equivalence tests.
  Research-runner speed parity remains unmet; profiling records the next steps.
- Add multiple-chain diagnostics, four convergence consistency checks, and
  exact coset-based initialization. Diagnostics do not prove convergence.
- Add physical circuit-fault configurations, exclusive location alphabets,
  single-fault MH proposals, and a midpoint surface-code baseline. Physical
  circuit Z/H/stabilizer proposals remain unsupported.
- Expand the README, API/tutorial, examples, optional-dependency packaging,
  citation metadata, and installed-wheel CI on Python 3.11 and 3.12.
- Include nested package sources in provenance fingerprints.

This is a private development version, not a published release.

## 0.1.0.dev0 — unreleased

- Establish an independent `src/mcmc4qec` package for finite binary states and
  deterministic decoders, without importing the research checkout.
- Add CSS bit-flip models, configurable failure predicates, exact enumeration,
  fixed-trial direct Monte Carlo, and failure-conditioned MCMC.
- Provide OBF, Zanella, cluster exchange, and stabilizer proposals with explicit
  mixture settings and retained rejection/lazy steps.
- Add serializable results, provenance, and weight-series diagnostics.
- Wrap existing decoder objects with explicit output semantics, including
  PyMatching correlation settings and BP-OSD physical-correction mapping.
- Supply a small repetition-code example, staged design documentation, and
  installed-wheel CI definitions.

This development stage does not complete the initial three-noise specification.
Depolarising and phenomenological models, splitting/BAR, Stim integration,
circuit faults, and research-runner compatibility remain subsequent work.
# 0.1.0.dev1 (local prototype)

- Categorical Pauli states and depolarizing noise with joint X/Z components.
- Explicit phenomenological time boundaries, data/measurement rates and histories.
- General-density BAR, explicit changing-decoder approximation, shared-rung block bootstrap.
- Stim DEM mechanism preservation and validated families; sector/history decoder composition.
- Bounded proposal workspace, categorical JSON, source fingerprints and move rates.
