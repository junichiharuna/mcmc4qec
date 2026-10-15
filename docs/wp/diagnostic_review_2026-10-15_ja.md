# 観測量平均の診断・誤差解析の独立レビュー（2026-10-15）

## 対象と判定範囲

`trace_stats.analyze_traces` の観測量平均、古典的 split R-hat、IAT に基づく標準誤差、非重複 batch means、円環 moving-block bootstrap を実装担当とは別に検討する。
`sample_faulty` と `estimate_logical_error` の同時診断は保存済み軌道を読む後処理であり、提案・受理・sampling RNG・BAR の点推定と区間推定を変更しない設計とする。
追加の利用者指定により、既存 IAT を使う条件付き重み平均の標準誤差は既定で返し、ACF・block scan・bootstrap の詳細解析のみ選択可能にする。
この追加解析の区間は指定した観測量の平均に対する区間であり、論理誤り率や BAR の区間ではない。
本レビューは有限の数値チェックであり、混合、エルゴード性、名目被覆、研究精度を保証しない。

## 方法上の確認点

独立な K chain が同じ長さ n を持つとき、平均の IAT 標準誤差は `sqrt(sum(s_j**2 * tau_j / n)) / K` とする。
`sum(chain_ess)` は従来の chain 別 ESS の合計という表示を維持してもよいが、異なる自己相関を持つ chain の単純 pooled mean に対応する ESS とは一般に一致しない。
R-hat は生の観測量を分割した古典的な分散比であり、順位正規化と folded R-hat を使う現行 Stan の指標とは区別する。
奇数長の中央一標本を R-hat 計算から除く場合は使用数と除外数を返し、平均・IAT・bootstrap まで同じ標本を捨てない。
非重複 batch means は各 chain 内で作り、chain 間の平均差を batch の分散へ混ぜない。
batch 数を B とすると標準誤差は `sqrt(sum(var(batch_means_j, ddof=1) / B)) / K` である。
block 長で割り切れない末尾を捨てたときは、使用数、除外数、その部分列の平均、全標本平均との差を返す。
円環 moving-block bootstrap は chain ごとに独立な始点を抽出し、末尾から先頭への折返しを許し、連結後の最初の n 標本を使う。
block 長で割り切れない最後の部分 block も独立な始点から作る。
定数 trace や不足標本から得るゼロの誤差を精度保証として表示しない。
block 長を変える感度表は、適切な block 長や plateau の自動認定ではない。
chain 独立性と定常性を仮定する誤差評価であり、同じ初期 basin に閉じ込められた chain 群を診断値だけで救済できない。

## 独立受入チェック

実装前に `tests/test_trace_stats_review.py` を追加した。
古典的 split R-hat の手計算、奇数長の中央除外、chain 別 batch 分散の集約と末尾除外、円環 bootstrap の厳密な条件付き分散、定常 AR(1) の既知の漸近分散、affine 変換に対する整合性を検証する。
bootstrap の独立参照では全円環始点について block 和の母分散を列挙し、完全 block と最後の部分 block の分散を加算する。
この参照は実装の乱数列を再実行する方式ではない。
AR(1) は `phi=0.8`、独立 4 chain、各 8192 標本で、理論 IAT は 9 である。
Python `A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe` で独立テストを実行し、最終確認は 6 passed、0.57 秒だった。
最も長い独立テストは 6000 反復の円環 bootstrap 分散確認で、0.14 秒だった。
AR(1) の chain 別 IAT は 8.4657、8.9904、8.0473、9.0509 となり、平均の推定 MCSE は 0.0268320、理論漸近値は 0.0276214 だった。
これらは固定 seed の軽い公式検証であり、QEC rare-event 推定の被覆実験ではない。

## 発見事項と修正確認

初回実装では `[[0.1]*3, [1.0]*3]` の定数 trace に対し、平均を引く丸め誤差が残り、第一 chain の ACF が `[1, 2/3, 1/3]` と返った。
実装担当に再現例を送り、定数値の範囲を直接検査する修正後、両 chain の ACF が `None` となる独立回帰テストを確認した。
同じ注意を split segment の分散と batch means の退化判定にも反映した実装を確認した。
ESS の説明を、分散が異なる場合だけでなく自己相関が異なる場合にも pooled mean の ESS と一致しない表現へ修正した。
独立に検証した範囲で、batch 集約、円環 bootstrap の完全 block と部分 block、R-hat の中央除外に未解決の公式上の問題は見つからなかった。
sampling と BAR の統合テストおよび全 suite の結果は統合担当の記録を参照し、本レビューの独立 6 テストの実績と区別する。

## 統合後の追加レビュー

既定MCSE追加後、定数chainと非定数chainの混在、短い非定数trace、旧JSON、異なるthin、custom observableのscalar・vector・complex・infを追加確認した。
custom callbackの複素数値がfloat変換時に虚部を失う問題を発見し、`analyze_traces` の実数検証まで複素数型を保つ修正後に再検証した。
独立テストの最終実行は13 passed、0.67秒、warningなしだった。
既定MCSEの公式、診断設定の事前検証、samplingとBARからの乱数隔離に未解決のブロッカーは見つからなかった。

## 一次資料

古典的な分散比と順位正規化・folding の区別は [Vehtari et al., Rank-normalization, folding, and localization](https://sites.stat.columbia.edu/gelman/research/published/Vehtari_etal_2020_rhat_ess.pdf) を参照した。
batch means の漸近分散推定と適用条件は [Flegal and Jones, Batch means and spectral variance estimators in Markov chain Monte Carlo](https://arxiv.org/abs/0811.1729) を参照した。
固定長の円環 block と最後の n 標本への切詰めは [Politis and White, Automatic Block-Length Selection for the Dependent Bootstrap](https://www.math.ucsd.edu/~politis/SBblock-revER.pdf) を参照した。
これらの理論的条件を本リポジトリの任意の符号・noise・decoder が満たすとは主張しない。
