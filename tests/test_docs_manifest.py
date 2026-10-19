"""Keep the public documentation index in sync with runnable files."""

from pathlib import Path
import ast
import importlib.util
import re
from types import SimpleNamespace
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
    public_docs = [ROOT / "docs" / name for name in
                   ("index.md", "index_ja.md", "guide_en.md", "guide_ja.md", "api_en.md")]
    public_docs.extend((ROOT / "docs" / "reference").glob("*.md"))
    for page in (EN, JA, INDEX, TUTORIAL_EN, TUTORIAL_JA, *public_docs):
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


def test_generated_reference_covers_every_top_level_export_once():
    module = ast.parse((ROOT / "src" / "mcmc4qec" / "__init__.py").read_text(encoding="utf-8"))
    exports = next(ast.literal_eval(node.value) for node in module.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "__all__"
                           for target in node.targets))
    documented = []
    for page in (ROOT / "docs" / "reference").glob("*.md"):
        documented.extend(re.findall(r"^::: mcmc4qec\.(\w+)$",
                                      page.read_text(encoding="utf-8"), re.MULTILINE))
    assert len(documented) == len(set(documented))
    assert set(documented) == set(exports)


def test_site_links_preserve_pages_and_code_and_resolve_repository_files():
    spec = importlib.util.spec_from_file_location("site_links", ROOT / "docs" / "_site_links.py")
    assert spec is not None and spec.loader is not None
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    page = SimpleNamespace(file=SimpleNamespace(abs_src_path=str(TUTORIAL_EN)))
    config = {"docs_dir": str(ROOT / "docs"),
              "repo_url": "https://github.com/junichiharuna/mcmc4qec",
              "nav": [{"Tutorials": [{"English": "tutorial_en.md"},
                                      {"Japanese": "tutorial_ja.md"}]}]}
    text = ('[Japanese](tutorial_ja.md#自分の-css-行列を使う)\n'
            '[README](../README.md#usage-notes)\n'
            '[Records](wp/)\n'
            '[Section](#local)\n'
            '```python\ntext = "[example](not-a-file.md)"\n```\n')
    converted = hook.on_page_markdown(text, page=page, config=config)
    assert '[Japanese](tutorial_ja.md#自分の-css-行列を使う)' in converted
    assert '[README](https://github.com/junichiharuna/mcmc4qec/blob/main/README.md#usage-notes)' in converted
    assert '[Records](https://github.com/junichiharuna/mcmc4qec/tree/main/docs/wp)' in converted
    assert '[Section](#local)' in converted
    assert 'text = "[example](not-a-file.md)"' in converted
    with pytest.raises(ValueError, match="missing link target"):
        hook.on_page_markdown('[Missing](not-a-file.md)', page=page, config=config)
