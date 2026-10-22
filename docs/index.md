# mcmc4qec documentation

[日本語](index_ja.md)

mcmc4qec estimates logical error probabilities for quantum error-correcting codes.
Define a code, a noise distribution, and a decoder, then use exact enumeration, direct Monte Carlo, or failure-conditioned MCMC with Bennett acceptance ratio (BAR) splitting.
The package is pre-alpha; its interfaces and numerical validation are still evolving.

## Start with a complete calculation

The [tutorial](tutorial_en.md) starts with a distance-3 toric code and an MWPM decoder.
It explains the noise ladder and anchor, how to choose a sampling budget, what the returned errors mean, and how to replace the built-in components.
You need Python 3.11 or newer and a local checkout.

```sh
python -m pip install -e ".[codes,matching]"
```

For core-only examples, install with `python -m pip install -e .` and start with the tutorial's [small CSS model](tutorial_en.md#your-css-matrices).
The [README](../README.md) gives a shorter overview and runnable example.

## Find the right document

| You want to… | Read |
| --- | --- |
| Understand a first estimate from beginning to end | [Tutorial](tutorial_en.md) |
| Choose a method, check uncertainty, or use another noise model | [Workflow guide](guide_en.md) |
| Check assumptions, defaults, or statistical conventions | [API contracts](api_en.md) |
| Look up arguments, return types, and class methods | [Sampling API](reference/sampling.md), [results API](reference/results.md) |
| Run a complete script or notebook | [Examples and notebooks](../examples/README.md) |
| Review evidence behind the numerical claims | [Release notes and validation records](experimental_release_notes_en.md) |
| Check current tile results and unfinished validation | [Tile validation report](wp/tile_validation_report_2026-10-18_ja.md), [study status](wp/tile_validation_status_2026-10-17_ja.md) (Japanese) |

API pages are generated from the current source signatures and docstrings.
Use them alongside the API contracts: a signature alone does not explain the assumptions behind an estimator.
Historical development reports and measurements remain in the repository and are linked where needed.

## Read and build locally

The Markdown documents can be read directly in the repository.
For the searchable site, run these commands from its root:

```sh
python -m pip install -e ".[docs]"
python -m mkdocs serve
```

Open the local address printed by MkDocs, usually `http://127.0.0.1:8000`.
To build static HTML and check links, use `python -m mkdocs build --strict`; the output is in `output/docs-site/`.
See [Contributing](../CONTRIBUTING.md#documentation) for the build conventions.

The package uses the [MIT license](../LICENSE).
Citation metadata is in [CITATION.cff](../CITATION.cff).
