# WP-J 独立レビュー

対象は WP-J の `a0bc4d0` であり、`README.md`、`README_ja.md`、`examples/README.md`、`tests/test_docs_manifest.py`、`docs/wp/J_ja.md` を確認した。
依頼書 `docs/dev_request_2026-09-30_examples.md` と `AGENTS.md` を受入基準とした。

## 判定

重大な阻害事項は見つからなかった。
英語 README の既存冒頭、二つの quickstart Python ブロック、ノイズとカーネルの対応表、科学的制約の記述は保持されている。
日本語 README は英語版を一次版と明記し、同じ章構成と主張を持ち、二つの Python ブロックは文字列として一致した。
`examples/README.md` は既存 6 例、新規 12 例、notebook 4 本、`notebooks/regenerate.py` の計 23 ファイルを列挙し、各表に目的、extras、時間、出力の読み方、科学的注意の列がある。
toric 系ファクトリが現状で `ldpc` と `bposd` を使うため、依頼書の原表から追加した `codes` extra は妥当である。
実行時間の `not measured` はメインの統合後実測待ちと明記され、測定値として扱われていない。

## 指摘と依頼

英日 README の後半の符号ファクトリ段落は `codes` extra を HGP 系にだけ結び付けるため、同じ文書の冒頭にある toric ファクトリの依存説明と離れて読むと誤解を招き得る。
担当者には、英日両方で toric、surface、asymmetric toric の現行依存も分かる表現に揃えるよう依頼した。

## 科学的注意

条件付き chain の頻度を絶対 `P_L` として扱わず、exact、直接 MC、anchor 付き BAR との役割を分けている。
standard ladder のデコーダー固定、p 依存の BP-OSD と `decoder_p`、明示的な近似 mode で区間に含まれない bias を説明している。
exact または失敗を観測した MC anchor、overlap 不足時の `OverlapError`、独立直接 MC の条件付き分散を要する収束判定を説明している。
診断を収束や正しさの証明とせず、論文を in preparation と扱い、物理回路では単一 fault カーネルを明示している。

## 検証と残件

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_docs_manifest.py -q` は 1 passed、2 failed だった。
二つの失敗は他 WP の未統合ファイル 17 個がこの worktree に存在しないためで、存在確認を緩めていないことを確認した。
`git diff --check main...HEAD` は成功した。
`test_docs_manifest.py` は実在ファイルとの双方向の一覧照合、相対リンク、英日 Python ブロックの一致を検査しており、依頼書の指定に沿う。
統合後の全リンクと一覧、実例の出力と説明の整合、英語 README ブロックの installed wheel 実行、時間の実測はこのレビュー時点では未実施である。
