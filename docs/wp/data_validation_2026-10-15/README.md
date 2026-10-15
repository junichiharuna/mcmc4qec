# Integration validation, 2026-10-15

`source.log` records the full source suite with the read-only research checkout
enabled. `core.log` and `optional.log` record the installed-wheel suites with
source import paths and research environment variables removed.
`verify_core.log` and `verify_optional.log` record installed/source byte checks,
examples, documentation snippets, and (for optional) quick notebooks.
`summary.json` records counts, elapsed times, maximum per-file test time,
package/wheel fingerprints, and the unchanged kernel defaults.

The wheel was built with `python -m build --wheel --outdir output/dev6/dist`
and installed with `--no-deps --force-reinstall` into the existing isolated
`.venv-dev5-core` and `.venv-dev5-optional` environments. This reused their
dependencies; these were not newly created environments.

All Python interpreters derive from the specified Windows Python 3.11.
The source run used `.venv-dev5-source`. Package and consumer type checks use
`mypy --strict`. Remote CI was not run because no commit or push was requested.
