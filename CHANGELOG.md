# Changelog

## Unreleased

- Rename the package and repository from the provisional `rimc` to `mcmc4qec`
  (import name `mcmc4qec`). No API change.

## 0.1.0.dev3 — development

- Add real-code examples, research workflows, editable component templates,
  and four self-contained executed Jupyter tutorials.
- Standardize example CLIs with quick runs, explicit seeds and output paths,
  and machine-readable summaries.
- Expand the English README and add a matching Japanese README and an
  example catalog with measured run times and scientific limitations.
- Add plotting and notebook extras, recursive installed-wheel verification,
  and CI coverage for quick examples and notebook execution.

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
