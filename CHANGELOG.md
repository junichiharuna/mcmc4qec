# Changelog

## 0.1.0.dev0 — unreleased

- Establish an independent `src/rimc` package for finite binary states and
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
