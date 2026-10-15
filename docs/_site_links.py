"""Keep repository-relative Markdown links useful in the curated docs site."""

from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^\s)]+)\)")


def _pages(items):
    for item in items:
        if isinstance(item, str):
            yield item
        elif isinstance(item, dict):
            for value in item.values():
                yield from _pages(value if isinstance(value, list) else [value])


def on_page_markdown(markdown, *, page, config, **kwargs):
    """Link non-site repository files to GitHub without editing Markdown sources."""
    docs = Path(config["docs_dir"])
    included = {(docs / path).resolve() for path in _pages(config["nav"])}
    source = Path(page.file.abs_src_path)

    def replace(match):
        raw = match.group(1)
        uri = urlsplit(raw)
        if uri.scheme or uri.netloc or not uri.path:
            return match.group(0)
        target = (source.parent / unquote(uri.path)).resolve()
        if not target.exists():
            raise ValueError(f"{source.name}: missing link target {raw}")
        if target in included:
            return match.group(0)
        relative = target.relative_to(ROOT).as_posix()
        kind = "tree" if target.is_dir() else "blob"
        url = f"{config['repo_url']}/{kind}/main/{quote(relative)}"
        if uri.query:
            url += "?" + uri.query
        if uri.fragment:
            url += "#" + uri.fragment
        return match.group(0).replace(f"({raw})", f"({url})")

    # Do not rewrite example code that happens to contain Markdown links.
    parts = re.split(r"(^```[^\n]*\n.*?^```[ \t]*$)", markdown,
                     flags=re.MULTILINE | re.DOTALL)
    return "".join(part if i % 2 else LINK.sub(replace, part)
                   for i, part in enumerate(parts))
