"""Check local HTML links and theme assets after `mkdocs build --strict`."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.links.append(values[attribute])


def main():
    site = Path(__file__).resolve().parents[1] / "output" / "docs-site"
    pages = {}
    for path in site.rglob("*.html"):
        parser = References()
        parser.feed(path.read_text(encoding="utf-8"))
        pages[path.resolve()] = parser
    if not pages:
        raise SystemExit("No HTML pages found; run python -m mkdocs build --strict first")
    failures = []
    count = 0
    for page, parser in pages.items():
        # MkDocs' generic 404 page uses host-root links without a configured site_url.
        if page.name == "404.html":
            continue
        for link in parser.links:
            uri = urlsplit(link)
            if uri.scheme or uri.netloc:
                continue
            count += 1
            target = ((site / uri.path.lstrip("/")) if uri.path.startswith("/") else
                      (page.parent / unquote(uri.path)) if uri.path else page).resolve()
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                failures.append(f"{page.relative_to(site)}: missing {link}")
            elif uri.fragment and target in pages and unquote(uri.fragment) not in pages[target].ids:
                failures.append(f"{page.relative_to(site)}: missing anchor {link}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Checked {len(pages) - 1} content pages and {count} local links/assets")


if __name__ == "__main__":
    main()
