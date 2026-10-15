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

## Documentation

Install the documentation tools and preview from the repository root:

```console
python -m pip install -e ".[docs]"
python -m mkdocs serve
python -m mkdocs build --strict
python docs/check_site.py
```

The static build is written to `output/docs-site/`. Building and previewing do
not publish the site. The CI documentation job builds it without deploying.
The HTML check also verifies generated anchor links and theme asset paths.
MkDocs configuration and its explicit page list live in `mkdocs.yml`.
When adding a page, update both `nav` and the `exclude_docs` allowlist.
Keep the English and Japanese tutorials' Python blocks identical and runnable
independently. Check them with the optional dependencies their examples need.

API signatures and docstrings are generated from `src/mcmc4qec` using
mkdocstrings; optional scientific backends are not needed for the docs build.
The handwritten [API contracts](docs/api_en.md) explain assumptions that are
not captured by signatures. New top-level exports belong in one of the pages
under `docs/reference/`.

Source Markdown retains repository-relative links. The small
`docs/_site_links.py` hook converts links to files outside the curated site
into repository URLs when building; historical records and raw measurements
are not copied into the site. Keep links to site pages relative so MkDocs can
check their targets and heading anchors.

The [MkDocs configuration reference](https://www.mkdocs.org/user-guide/configuration/)
describes navigation, exclusions, link validation, and hooks. See also the
[Material navigation guide](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/)
and [mkdocstrings signature options](https://mkdocstrings.github.io/python/usage/configuration/signatures/).

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
