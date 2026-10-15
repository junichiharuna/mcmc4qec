"""Keep the public documentation index in sync with runnable files."""

from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "README.md"
JA = ROOT / "README_ja.md"
INDEX = ROOT / "examples" / "README.md"
TUTORIAL_EN = ROOT / "docs" / "tutorial_en.md"
TUTORIAL_JA = ROOT / "docs" / "tutorial_ja.md"
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PYTHON_BLOCK = re.compile(r"^\x60{3}python[ \t]*\n(.*?)^\x60{3}[ \t]*$", re.MULTILINE | re.DOTALL)


def _local_target(page: Path, raw: str) -> Path | None:
    uri = urlsplit(raw)
    if uri.scheme or uri.netloc or raw.startswith("#"):
        return None
    return (page.parent / unquote(uri.path)).resolve()


def _indexed_files() -> set[Path]:
    paths = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ["):
            continue
        first_cell = line.split("|", 2)[1]
        match = LINK.search(first_cell)
        if match is None:
            continue
        target = _local_target(INDEX, match.group(1))
        if target is not None and target.suffix in {".py", ".ipynb"}:
            paths.add(target)
    return paths


def test_example_index_matches_every_python_file_and_notebook():
    expected = set((ROOT / "examples").rglob("*.py"))
    expected.update((ROOT / "notebooks").rglob("*.py"))
    expected.update((ROOT / "notebooks").rglob("*.ipynb"))
    indexed = _indexed_files()
    assert indexed == expected, (
        f"missing from examples/README.md: {sorted(map(str, expected - indexed))}; "
        f"listed but absent: {sorted(map(str, indexed - expected))}"
    )
    assert all(path.is_file() for path in indexed)


def test_relative_readme_links_resolve():
    for page in (EN, JA, INDEX, TUTORIAL_EN, TUTORIAL_JA):
        text = page.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            raw = match.group(1)
            target = _local_target(page, raw)
            if target is not None:
                assert target.exists(), f"{page.relative_to(ROOT)}: {raw}"


@pytest.mark.parametrize("english_page,japanese_page", [(EN, JA), (TUTORIAL_EN, TUTORIAL_JA)])
def test_japanese_python_blocks_match_english_exactly(english_page, japanese_page):
    english = PYTHON_BLOCK.findall(english_page.read_text(encoding="utf-8"))
    japanese = PYTHON_BLOCK.findall(japanese_page.read_text(encoding="utf-8"))
    assert english
    assert japanese == english
