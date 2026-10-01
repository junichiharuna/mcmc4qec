# Contributing

This package is a pre-alpha development prototype released under the MIT
License (see `LICENSE`). The public repository and release process have not
been finalized.

## Local checks

Use Python 3.11 or newer. From the package directory:

```console
python -m pip install -e ".[test]"
python -m pytest tests/ -q
python examples/bit_flip.py
python examples/bar_ladder.py
```

For packaging validation, build a wheel, install it in a separate environment,
then disable the source-path override when testing:

```console
python -m pip install build
python -m build --wheel
# In a separate environment, install the wheel path and pytest.
python -m pytest --override-ini pythonpath= tests/ -q
python examples/bit_flip.py
python examples/bar_ladder.py
```

Run core checks without optional decoders, then run decoder integration checks
with the corresponding optional dependencies installed. Keep local tests small;
large rare-event sweeps and benchmark campaigns belong in separately planned
compute jobs.

With `pymatching`, `ldpc`, and `bposd` installed, run
`python examples/toric_pymatching.py`. With Stim installed, run
`python examples/stim_dem.py` and `python examples/circuit_baseline.py`. The CI workflow installs the built wheel and
tests Python 3.11 and 3.12 with and without optional dependencies. A defined
workflow is not evidence of a successful remote run; check its actual status
after an authorized push.

## Scientific changes

Start with a small specification and acceptance test. For changes to proposals,
densities, or state representations, use enumerable examples to check
normalization, support, forward/reverse proposal probabilities, detailed
balance, and the shared failure definition. Check communicating classes and
periodicity separately from detailed balance.

Keep every rejection in a Markov chain. Do not silently renormalize kernel
weights, reinterpret decoder output, assume custom predicate invariance, or
replace a correlated noise model with independent sectors. Record intentional
approximations and expanded settings in the result.

Diagnostic quality does not prove correctness. Report the validation actually
run, including limitations and missing checks; do not describe unrun CI or
planned experiments as successful.

## Before public release

- Confirm the final distribution destination and inspect the completed
  three-noise acceptance evidence, including Y correlations and time boundaries.
- Review third-party rights and dependency compatibility with the MIT License
  (pymatching and stim are Apache-2.0, ldpc is MIT).
- Review `CITATION.cff`, whose author was supplied by the project owner and
  whose DOI and release metadata remain unconfirmed.
- Review package contents, documentation, optional dependency versions, and
  installed-wheel checks in supported Python environments.
- Record actual verification in the changelog and obtain authorization for
  publishing, pushing, or changing repository visibility.

These are release preparation items, not claims that a public release exists.
