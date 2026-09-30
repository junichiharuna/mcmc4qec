# dev3 実行例整備の統合記録

## Phase 0

開始時 main と origin/main は `8cbc0b1c4eef64519cc6320b3ddd5565876d168e` で一致し、作業ツリーは clean だった。
更新済み AGENTS.md と依頼書 `docs/dev_request_2026-09-30_examples.md` が同commitに含まれることを確認した。
着手前の指定文書、既存6例、CI、wheel検証helperを読んだ。
指定 Python 3.11 による全 suite は 268 passed / 4 skipped、46.08秒で、ファイル別合計最大は11.00秒だった。
研究リポジトリは `69efcfcc86af3bf24ca977a098dab0f348601aff`、status cleanであり、読み取り専用とする。

## 統合方針

作業枝は wp/f〜wp/j、統合順は H → F → G → I → J とする。
verify_wheel.pyはexamples以下を再帰的に列挙し、マニフェストの依存分類を使い、各例を `--quick --seed ... --out <一時ディレクトリ>` で実行する。
READMEのPythonブロックは英語版だけを実行し、日本語版はコードの完全一致試験で保証する。
notebookはinstalled wheelを使うカーネルでquick実行し、既定出力の再生成とは分けて記録する。

## マニフェストの依存修正の判断

make_toric_codeは既存実装でldpcとbposdをimportし、matching extraだけでは動かない。
ライブラリ本体やmatching extraの意味を変えず、toricを使うFの2例、Gの3例、Iの最初の3notebookの必要extrasにcodesを追加する。
ファイル名とSUMMARYキーは変更しない。
この不足は依頼書のマニフェストとdev2公開契約の不整合であり、メイン判断として依頼書の該当extrasとWP-Jの一覧に同じ修正を適用する。

## 既存6例のSUMMARYキー

依頼書に指定のない既存6例については、Fの提案をメインが承認し次の集合を使う。

| script | keys |
| --- | --- |
| bit_flip.py | exact, pl, pl_interval, ew_exact, ew_chain |
| three_noise.py | cases |
| bar_ladder.py | ladder, bar, intervals, exact |
| toric_pymatching.py | code, p, pl, pl_interval, ew_direct, ew_chain |
| stim_dem.py | mechanisms, exact, pl, pl_interval |
| circuit_baseline.py | locations, detectors, pl, pl_interval |

## version更新の確認対象

pyprojectの配布版番号はPhase 2で0.1.0.dev3へ更新する。
実行時 `mcmc4qec.__version__` は現在 src/mcmc4qec/results.py の `VERSION = "0.1.0.dev2"` に固定されている。
実行時番号も揃える最小差分はこの1行を `VERSION = "0.1.0.dev3"` にすることであり、アルゴリズムや公開APIは変わらない。
当初はsrc変更禁止との整合を確認したが、依頼書全体の再実行指示を受けて第1節のメイン向け最小修正の例外と第7.2節のdev3指定を再確認し、この1行を同範囲として更新する。
配布設定と実行時versionの一致テストを先に追加し、dev2対dev3で失敗することを確認してから修正した。
