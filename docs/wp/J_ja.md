# WP-J 完了メモ

作成日：2026-09-30。
担当は `README.md`、`README_ja.md`、`examples/README.md`、`tests/test_docs_manifest.py` である。
既存の英語 README の冒頭 3 行、二つの quickstart Python ブロック、対応表、制約の記述を保持し、install と extras、目的別の入口、例の一覧への導線を追加した。
日本語 README は同じ構成と主張を持ち、冒頭で英語版を一次版と明記した。
英日二つの Python ブロックは文字列として一致する。
`examples/README.md` は依頼書の新規 16 本、既存 6 本、`notebooks/regenerate.py` を含む 23 ファイルを一覧にした。
toric ファクトリの現行依存に合わせ、該当する例と notebook に `codes` extra を記載した。
独立レビューの指摘を受け、英日 README の後半でも toric、surface、asymmetric toric を含む現行の `codes` 依存を明示した。
実行時間の列は統合後の実測待ちで `not measured` とした。

## 科学的な確認

条件付き chain の状態頻度を絶対 `P_L` と読まない説明を README と実行例一覧に置いた。
standard BAR ladder の固定デコーダー、p 依存の BP-OSD と回路 `decoder_p`、明示的な近似 mode の bias を説明した。
exact または失敗を観測した MC anchor と、隣接 rung の overlap 不足による `OverlapError` を説明した。
ESS、split R-hat、`evaluate_convergence` が証明ではなく、完全な判定には独立の直接 MC による条件付き分散が必要と記載した。
論文は in preparation とだけ扱い、図表の再現を主張していない。
物理回路の baseline には単一 fault の `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)` を明示した。
著者名 `junichi haruna` を保持し、所属、DOI、ライセンス、公開は未確定とした。

## 実行した検証

`%USERPROFILE%/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_docs_manifest.py::test_japanese_python_blocks_match_english_exactly -q` は 1 passed だった。
`%USERPROFILE%/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_docs_manifest.py -q` は最終実行で 1 passed、2 failed だった。
二つの失敗は F/G/H/I の 17 ファイルがこの worktree にまだ存在しないことによる。
失敗を skip したり、存在検査を緩めたりはしていない。
`git diff --check` は通過した。
installed wheel での README ブロック実行、全例の既定・quick 実行時間、統合後の全テストと CI は未実施である。

## main への引き継ぎ

F/G/H/I の成果物を統合後、`tests/test_docs_manifest.py` の全件を実行し、実際のファイル名、extras、出力の意味との整合を再確認する。
`examples/README.md` の既定・quick 時間を各 WP の実測値で埋める。
`pyproject.toml` に `plot` と `notebooks` を追加し、`codes` の現行依存を含む optional wheel 環境を準備する。
`docs/wp/verify_wheel.py` では `examples/**/*.py` と `notebooks/regenerate.py` をマニフェストに沿って分類し、実行例は `--quick --seed --out` を一時ディレクトリとともに渡す。
README の Python ブロックは英語版だけを wheel で実行し、日本語版との同一性は文書テストで確認する。
既存の `docs/tutorial_en.md` の Python ブロック検証も保持する。
