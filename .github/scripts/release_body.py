"""Convert the release notes into a GitHub Release body with absolute links.

The notes in ``docs/experimental_release_notes_en.md`` use links relative to
``docs/`` so that they work in the repository and in the MkDocs site.
The GitHub Releases page does not resolve relative links, so this script
rewrites every relative link target to a ``blob/<tag>`` URL on GitHub.

Usage::

    python .github/scripts/release_body.py v0.1.0.dev5 > output/release_body.md
"""
from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "docs" / "experimental_release_notes_en.md"
REPO_URL = "https://github.com/junichiharuna/mcmc4qec"
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def absolutize(text: str, tag: str, *, base_dir: str = "docs") -> str:
    """Return ``text`` with relative Markdown link targets made absolute.

    Targets that already have a URL scheme or that are pure fragments are
    left unchanged.
    Relative targets are resolved against ``base_dir`` within the repository
    and pointed at ``REPO_URL/blob/<tag>/<path>``.
    """

    def replace(match: re.Match[str]) -> str:
        target = match.group(1)
        if "://" in target or target.startswith(("#", "mailto:")):
            return match.group(0)
        path, sep, fragment = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(base_dir, path))
        if resolved.startswith(".."):
            raise ValueError(f"link escapes the repository: {target}")
        return f"]({REPO_URL}/blob/{tag}/{resolved}{sep}{fragment})"

    return _LINK.sub(replace, text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tag", help="git tag the links should point at, e.g. v0.1.0.dev5")
    parser.add_argument("--notes", type=Path, default=NOTES, help="Markdown source (default: the English release notes)")
    args = parser.parse_args(argv)
    text = args.notes.read_text(encoding="utf-8")
    sys.stdout.write(absolutize(text, args.tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
