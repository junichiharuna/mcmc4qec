"""Keep the published top-level API and reference documentation in sync."""
import inspect
from pathlib import Path
import re

import mcmc4qec


def test_public_exports_are_documented_and_importable():
    reference = (Path(__file__).resolve().parents[1] / "docs" / "api_en.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"`([A-Za-z_][A-Za-z_0-9]*)`", reference))
    exports = mcmc4qec.__all__
    assert len(exports) == len(set(exports))
    assert not (set(exports) - documented)
    for name in exports:
        value = getattr(mcmc4qec, name)
        if callable(value):
            assert inspect.getdoc(value), name
