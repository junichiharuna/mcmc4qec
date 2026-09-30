# WP-A 第1回独立レビュー（2026-09-30）

対象は `f8f5469` と `81aece0` の差分、および `docs/wp/A_ja.md` と `docs/crossval_research_ja.md` である。
研究リポジトリ `C:/dev/RIMC` の参照 commit は `69efcfcc86af3bf24ca977a098dab0f348601aff` であり、読み取り専用で確認した。
研究側の `git status --porcelain=v1` は出力なしだった。

## 判定

実装の重大な反例は見つからなかった。
受入条件のうち、研究 decoder 関数との直接比較と数値表の機械的再現性には証拠の不足が残る。
大きい符号の距離は研究と同一の行列および論理代表による上界を確認したものであり、独立した最小距離の下界証明ではないと文書が区別しているため、この扱いは妥当である。

## 指摘

| 重大度 | 箇所 | 観察と受入への影響 | 求める対応 |
| --- | --- | --- | --- |
| 中 | `tests/test_decoders.py:25`, `:38`, `:53`, `:71`、`docs/crossval_research_ja.md:29` | コミットされた全 syndrome テストは研究側の `make_mwpm_decoder` などを import せず、同じ `pymatching` / `ldpc` の recipe を別に構築して期待値にしている。研究関数を直接呼んだという文書の実行報告は否定されないが、差分から再実行可能な直接照合は確認できない。 | 研究リポジトリを読み取り専用 import する検証スクリプト、または研究出力の固定 fixture と生成手順を残す。少なくともコミット済みテストの検証対象を recipe 比較と明記する。 |
| 中 | `docs/crossval_research_ja.md:42`, `:48`, `:61` | exact、direct MC、Z+H の値と seed、主要パラメータは記録されているが、`Problem` と decoder prior の構築、`Result` からの区間集計を実行するコマンドまたはスクリプトは残っていない。数値一致の第三者再実行は表だけでは一意にできない。 | 軽量な再現スクリプトか実行コマンド、使用した decoder prior、参考区間の計算式を記録する。既存の実測結果を新たな検証実行として扱わない。 |
| 低 | `src/mcmc4qec/codes.py:26`, `:68`, `:183`, `:193`, `:203`, `:271` | 公開 docstring は `[[n,k,d]]` と断定形だが、大きい符号の `d` はこの WP で独立に下界を示していない。`docs/crossval_research_ja.md:13` 以下では正しく区別されている。 | 公開 docstring でも研究側のパラメータ表示であることと、距離はこの実装のテストで独立認証していないことを短く示す。 |

## 確認できた範囲

`tests/test_codes.py` は対象ファクトリの `n`、`k`、`hx @ hz.T=0`、完全な論理基底を検査し、小符号のみ低重みを全列挙している。
`tests/test_crossval_research.py` は12構成の `hx/hz/lx/lz` の shape と raw bytes の SHA-256 を固定し、研究 `int8` とライブラリ `uint8` のバイナリ要素 bytes の一致を検査する。
`core.CSSCode` は論理交差行列の GF(2) 可逆性を検査し、非単位の研究基底では明示した `logical_basis="independent"` が行順を保持する。
`Problem.is_faulty` の論理予測と真値の不一致は、研究 decoder の残差に対する論理検査と同値であり、Pauli の X/Z sector 順序も一致する。
`bposd_decoder` は有限実数の prior と非負整数の OSD order を検査し、order が検査行列の nullity を超えると native constructor の前に拒否する。
optional 依存なしの対象テストは担当実測で `40 passed, 26 skipped` であり、core import に optional decoder を要求しない。
研究テスト八ファイルの102関数は表で意味論ごとに分類され、新規52 parameterized case と既存テストの対応、未移植理由を記録している。
同じ合成 weight trace の BAR 値は固定期待値としてテストされているが、研究関数の実行自体はそのテストには含まれない。
対象15公開関数について AST で docstring の存在を確認し、15件すべてに英語 docstring がある。

## このレビューでの実行

Python は `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` を使い、AST による docstring 存在検査のみ実行した結果は `15 15 []` だった。
全 suite と約40秒の担当テストは並列実行枠を避けるためこのレビューでは再実行しておらず、担当の `66 passed, 39.65 秒` および `40 passed, 26 skipped` を独立実測とは扱わない。
