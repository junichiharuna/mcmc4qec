# 観測量 trace の統計診断と平均の不確かさ（実装前仕様）

対象は独立に初期化・乱数化した K 本、各 n 個の定常区間の実数観測量であり、棄却後の重複値も残す。
入力は有限で空でない長方形配列 `[chain, sample]` とし、1 次元は 1 chain と解釈する。
入力の burn-in 除去、thinning、定常性の判定は行わない。
出力は JSON 化可能な辞書とし、未定義値は `None`、定数 chain の不確かさを確実性を意味する 0 に置き換えない。

## 推定量

- 平均は全 chain を等重みで集約する。
- chain 別 FFT ACF は `sum_t (x_t-mean)(x_(t+l)-mean) / sum_t (x_t-mean)^2` とし、分母を lag ごとに補正しない。
- IAT は既存 `diagnostics._iat` の Geyer initial positive / monotone pairs と一致させ、n < 8、定数、非正推定は未定義とする。
- ESS は n/IAT、互換集約 IAT は chain IAT の算術平均、互換集約 ESS は chain ESS の和とし、全 chain で定義できる場合だけ返す。
- chain ESS の和は一般に集約平均に対応する ESS ではなく、chain 間の分散と自己相関時間の相違に依存するため、集約平均用には IAT MCSE を別に返す。
- 平均の IAT MCSE は `sqrt(sum_j(s_j^2*tau_j/n))/K` とし、不偏標本分散を使う。
- cross-chain SE は chain 平均の不偏標準偏差を `sqrt(K)` で割り、K < 2 または定数 chain を含む場合は未定義とする。
- R-hat は生観測量の classical split R-hat と明記し、rank-normalized R-hat や bulk/tail ESS と呼ばない。
- R-hat は既存診断と同じく K >= 2、n >= 8 で計算し、奇数長では中央の 1 値を除いて前半・後半を使い、within 分散 0 は未定義とする。

## Blocking と bootstrap

block 長 b ごとに chain 内で先頭から a=floor(n/b) 個の非重複 block を作る。
block 平均の chain 別不偏分散を v_j として、切り詰めた平均の SE を `sqrt(sum_j(v_j/a))/K` とする。
残余 n-ab は chain ごとに捨て、使用数・破棄数・切り詰めた平均・元の平均との差を出力する。
a < 2、定数 chain、または block 平均に変動がない chain を含む場合は SE を未定義とする。
既定 block 長は 1 および 4 block 以上を確保できる 2 の累乗とし、短い trace では 1 のみ返す。
指定 block 長は 1..n の異なる整数とし、昇順で表示する。
bootstrap は chain ごとに独立に circular moving block を復元抽出し、ceil(n/b) block から先頭 n 個を採用して chain 平均を等重み集約する。
chain 境界を越えた block は作らないが、各 chain 自身の末尾から先頭への循環は許す。
同一 seed は同一 bootstrap 結果を返し、sampling やグローバル乱数の状態には触れない。
seed を省略した場合は生成した entropy の整数を結果に記録し、その seed による再現を可能にする。
bootstrap 反復の不偏標準偏差と線形補間 percentile 95% 区間を block 長ごとに返す。
反復 0 は無効化、1 は拒否、定数 chain、n < 2、b=n、または bootstrap 反復が全て同じ値の場合は SE と区間を未定義とする。

## 限界と受入確認

有限長の診断は収束・既約性・エルゴード性・正しさを証明せず、各不確かさには定常性と chain 独立性の仮定がある。
block 長による感度と短い実行の不安定性を warnings に明示し、既定 block 長を自動最適化や被覆保証と扱わない。
ここでの区間は指定観測量平均の区間であり、BAR 推定や論理誤り率の区間ではない。
小配列の ACF・R-hat・block 分散の手計算、IAT との互換、固定 seed の正負相関 AR 系列、chain 境界保持、再現性、定数・短い trace、不正入力、JSON 化、入力非破壊を受入テストで確認する。
実装前時点で上記受入テストは未実施である。

式の参照は [Stan Reference Manual 2.40, Posterior Analysis](https://mc-stan.org/docs/2_40/reference-manual/analysis.html) および [Geyer, Stat 3701 MCMC lecture notes](https://www.stat.umn.edu/geyer/3701/notes/mcmc-bayes.pdf) とする。
Stan の現行 rank-normalized 診断全体を実装するものではなく、生観測量の従来式と区別する。

## 実装後の受入確認（2026-10-15）

上記仕様、受入テスト、実装の順に追加し、実装前テストでは対象 module 不在による収集失敗を確認した。
`tests/test_trace_stats.py` の 41 tests と独立レビュー側 `tests/test_trace_stats_review.py` の 6 tests は合計 47 passed、0.62 秒で成功した。
`src/mcmc4qec/trace_stats.py` の mypy strict は成功した。
独立レビューが指摘した小数の定数 chain の平均丸めによる偽 ACF を、値域 0 の明示判定で修正した。
同種の定数 split 分散と block 平均分散の丸めも未定義判定に反映した。
これらは小規模受入検証であり、実符号上の名目被覆校正や性能 benchmark はこの担当範囲では未実施である。
