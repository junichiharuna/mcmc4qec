# WP-E 第1回敵対レビュー

対象は commit `506a74b`、`docs/wp/E_ja.md`、`docs/convergence_ja.md`、開発依頼書の WP-E 受入条件、研究側 `compare/convergence_flags.py` と論文 Setup である。
2026-09-30 に Python 3.11 で関連 12 テストを実行し、すべて成功した。
研究リポジトリは `PYTHONDONTWRITEBYTECODE=1` を設定して読み取り専用で参照した。

## 修正を要する所見

1. 高: `src/mcmc4qec/convergence.py:67`、`:77`、`:97` は判定式の分母がゼロで、差や最終散らばりが正の場合にも `ok=None` を返す。
研究側 `scaling_verdict`、`drift_verdict`、`multistart_verdict` は同じ状況を比率 `inf` の不合格とする。
`a=zeros((4,16))`、`b=ones((4,16))` の二群比較は `multistart=None` と全体 `converged=None` になり、`tile([0]*8+[1]*8,(4,1))` の後半ドリフトも `stationarity=None` になる。
`d=zeros((4,16)); d[0,4:]=1` では最初の四分の一の散らばりがゼロで最終散らばりは正なのに `scaling=None` になる。
各条件が観測可能な不一致を `False` と返すようにし、この境界例をテストする必要がある。

2. 中: `src/mcmc4qec/convergence.py:32` と `:107` は独立 direct MC 分散を省略すると chain 内分散を使い、四条件すべて `True` として `converged=True` を返し得る。
開発依頼書 WP-E の条件 (iv) は direct MC 分散との比較を指定する一方、論文 Setup の一次判定は chain 内分散を用いているため、二つの判定を API と記録上で区別する必要がある。
実際に独立正規乱数 32 chain × 2048 標本を二群に渡すと、分散未指定で `dispersion=True` と `converged=True` になった。

3. 中: `src/mcmc4qec/diagnostics.py:19` は IAT を 1 以上に切り上げるため、負の自己相関を持つ chain の IAT と ESS を誤って報告する。
AR(1) の係数 `-0.6` なら理論 IAT は `0.25` だが、32 chain × 2048 標本の実行では各 chain の報告 IAT が `1.0` になった。
研究側 `src/metrics.py:20` の推定にはこの切り上げがない。

4. 中: `tests/test_convergence.py:44` の二盆地テストは二つの AR(1) 群に固定オフセットを付けただけであり、依頼書が求める二盆地の玩具 Markov 問題での捕捉や移動を検査していない。
`tests/test_initial_states.py:61` の独立基底テストも `SimpleNamespace` であり、main の commit `e8a488b` で追加された `CSSCode(logical_basis="independent")` 実オブジェクトとの結合を受入テストにしていない。

## 確認できた点

`diagnose` の chain 平均の標本標準偏差を `sqrt(K)` で割る式と kernel 件数の集約は、検査した例では正しい。
研究側の四閾値 `1.5`、`3`、`3`、`3` と、最後の四分の一対半分のドリフト比較式は一致する。
rank 13 の MILP 経路をランダムな 16 座標の例で全 8192 組合せと比較し、最小重みは一致した。
main の `CSSCode(logical_basis="independent")` を動的に読み込んで WP-E の `observable_sector_initial_state` を試した一例では、指定観測セクターを保った。
これらの小例は全入力に対する証明ではない。
