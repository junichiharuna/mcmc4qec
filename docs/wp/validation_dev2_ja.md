# dev2 統合・installed wheel 検証

2026-09-30、Windows、指定 Python 3.11 で実行した。
機能コードは全 WP 統合後の `4330c3f`、最終公開 docstring を含む package ソースは `5d2e793` である。
全 suite は同時実行せず、各実行には295秒の外側タイムアウトを設けた。
各ファイルの時間は JUnit の testcase time をファイル単位で合計して確認した。

## ソース統合

各段階で `python -m pytest tests -q --durations=10 --junitxml=output/<stage>.xml` を実行した。
Python の絶対パスは `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` である。

| 統合段階 | 対象 | 結果 | 秒 | 最長ファイル合計秒 |
| --- | --- | --- | ---: | ---: |
| A | f3eec34 | 218 passed / 4 skipped | 68.77 | 15.68 |
| B | 6f38eda | 231 passed / 4 skipped | 39.15 | 8.07 |
| E | 6b0b885 | 247 passed / 4 skipped | 39.23 | 7.48 |
| D | 9b52061 | 247 passed / 4 skipped | 47.43 | 10.76 |
| C と公開 API 65名 | 4330c3f | 268 passed / 4 skipped | 76.01 | 21.33 |

4 skip は `RIMC_RESEARCH_ROOT` の明示指定時にだけ実行する研究 decoder 直接比較である。
WP-A の最終独立レビューではこの環境変数を指定し、同ファイル19件成功、研究decoder4種の各256症候群で不一致0を確認した。
大符号の距離下界の独立証明や研究論文の全数値再現を意味しない。

## wheel と環境

`C:/dev/mcmc4qec-wt/d/.venv-cff/Scripts/python.exe -m build --wheel` で最終 artifact を構築した。
ファイルは `dist/mcmc4qec-0.1.0.dev2-py3-none-any.whl` で、SHA256 は `e4d443a860a182786d3377cc068f713428771630fde9615cf7efbdb493581664` である。
この wheel を新設した `.venv-dev2-core` と `.venv-dev2-optional` にそれぞれ `-m pip install --no-deps --force-reinstall` で導入した。
core は NumPy と pytest を持ち、PyMatching、ldpc、bposd、Stim は不在である。
optional は PyMatching 2.4.0、ldpc 2.4.1、bposd 2.1、Stim 1.16.0 とそれらの依存を持つ。
両環境は NumPy 2.4.6 と pytest 9.1.1 を使用した。
`-I -m pytest --override-ini pythonpath= tests -q` で作業木の `src` を検索対象から外し、installed wheel を試験した。
最終 core wheel の結果は 208 passed / 43 skipped、41.23秒、最長ファイル合計11.37秒だった。
optional の最終 wheel は 268 passed / 4 skipped、81.52秒、最長ファイル合計20.65秒だった。

初回 core 検証では SciPy の必要な MILP 試験2件の skip 漏れを検出し、該当試験にだけ `pytest.importorskip("scipy.optimize")` を追加した。
SciPy 不在時に最適化が ImportError を返すライブラリ契約は変更していない。
optional ではこの2件も実行し、全列挙との最適値比較を維持する。
core の43 skip は optional 接続、MILP、および研究 checkout 直接比較を含み、モジュール単位の skip があるため optional の収集件数との差とは一致しない。

## 実行例・文書・公開 API

再現コマンドは各 venv の `python.exe -I docs/wp/verify_wheel.py core` または `optional` である。
この helper は import 先が venv の site-packages 配下であること、version、再帰的な Python 23ファイルと source の byte 一致、optional 依存の有無を検証する。
各 example と各文書ブロックを別の `python -I` プロセスで実行し、1件60秒の上限を設ける。
core では `bar_ladder.py`、`bit_flip.py`、`three_noise.py` の全3例、README の core 例1個、tutorial の独自コード・ノイズ・decoder の3例が exit 0 だった。
optional ではさらに `circuit_baseline.py`、`stim_dem.py`、`toric_pymatching.py` を含む全6例、README の2例、tutorial の4例が exit 0 だった。
toric の表示は direct MC の条件付き平均7.068817と Z+H の6.73、回路例は500試行で45失敗、P_L=0.09、Wilson区間 `[0.0679425, 0.1183094]` だった。
短い例の一致精度や混合を証明する試験ではなく、実行契約を検証する smoke test である。
`test_public_api.py` は65個の公開名が import 可能で API 文書に掲載され、callable に docstring があることを検証した。
独立レビューは各 docstring の引数・返値・例外・単位も確認し、指摘を補完した。
`C:/dev/mcmc4qec-wt/d/.venv-cff/Scripts/cffconvert.exe --validate` は schema 1.2.0 の検証に成功した。
著者はユーザー指定の junichi haruna であり、version は pyproject、実行時定数、CFF のすべてで `0.1.0.dev2` とした。

## remote CI

最終検証後に main を push し、Python 3.11 / 3.12 の core / optional 計4jobの結果を追記する。
