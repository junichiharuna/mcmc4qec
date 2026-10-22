"""The GitHub Release body must not keep links that only resolve inside docs/."""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_RELATIVE = re.compile(r"\]\((?![a-z]+://|#)[^)\s]+\)")


def load():
    path = ROOT / ".github" / "scripts" / "release_body.py"
    spec = importlib.util.spec_from_file_location("release_body", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_relative_links_become_blob_urls():
    module = load()
    text = "[a](api_en.md) [b](../examples/README.md#x) [c](#frag) [d](https://zenodo.org/)"
    out = module.absolutize(text, "v9.9")
    assert out == (
        "[a](https://github.com/junichiharuna/mcmc4qec/blob/v9.9/docs/api_en.md) "
        "[b](https://github.com/junichiharuna/mcmc4qec/blob/v9.9/examples/README.md#x) "
        "[c](#frag) [d](https://zenodo.org/)"
    )


def test_release_notes_body_has_no_relative_links():
    module = load()
    notes = module.NOTES.read_text(encoding="utf-8")
    assert _RELATIVE.search(notes), "the notes are expected to use relative links in the repository"
    body = module.absolutize(notes, "v0.1.0.dev5")
    assert not _RELATIVE.search(body)
    for target in re.findall(r"\]\((https://github\.com/junichiharuna/mcmc4qec/blob/v0\.1\.0\.dev5/[^)#]+)", body):
        relative = target.split("/blob/v0.1.0.dev5/", 1)[1]
        assert (ROOT / relative).is_file(), relative
