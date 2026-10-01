# WP-M 独立レビュー

## 判定

`8e221a4` と `81a5591` の WP-M 差分に統合を妨げる問題は見つからなかった。
修正後の保存数比較は block 長 8 を固定しており、旧計測で生じた保存数と自動 block 長の交絡を解消している。
研究精度の 95% 被覆、長い chain での収束、原因の一意な特定は今回の結果からは主張できず、文書もそのように限定している。

## 科学的・コード上の照合

benchmark は `make_toric_code(3)` の X bit-flip モデル、`IndependentBitFlip`、固定の `mwpm_decoder(code)` を一つの `Problem` に束ね、`exact`、BAR、direct MC に共用する。
`examples/workflows/pl_curve.py` の d=3 既定と ladder、chain 数、保存数、burn-in、anchor と確認 MC の試行数、bootstrap 回数が一致する。
`exact` は 18 bit の全 262144 状態を列挙し、同じ failure 判定で p=0.22 の真値 0.6026625647015839 を出す。
seed 2026 の BAR 区間 [0.5055163266489403, 0.5650849390034506] は真値を外し、独立 MC 区間 [0.5711650330352703, 0.6265354185118538] は真値を含み、両区間は交差しない。
保存済み CSV の基準 20 seed は BAR 13/20、独立 MC 20/20、区間非交差 2/20 で、表の値と一致する。
各 seed で `spawn_seeds` により anchor、BAR、確認 MC の乱数列を分離し、感度表は基準と同じ先頭 8 seed を使う。
修正版 CSV の保存 200 と 1200 は両方 block 8 であり、基準先頭 8 seed の block 8 と比較できる。
旧自動 block 6/11 の CSV と修正版 CSV を seed ごとに照合し、BAR 点推定、MC 点推定、最大 chain IAT は全行一致し、bootstrap 区間のみ変わることを確認した。
修正版の保存 200/600/1200 の BAR 被覆はそれぞれ 6/8、4/8、7/8 で、旧自動 block 11 の 8/8 を保存数単独の効果と解釈していない。
block 3/27/107 の比較は同じ軌道の bootstrap だけを変え、平均区間幅は 0.04817/0.07616/0.08562 へ増えるが、seed 2026 の真値外れは残る。
anchor exact、ladder の粗密、burn-in、低 p、初期状態の各仮説 (a)〜(e) について数値と限定的な判断が記録されている。
今回の固定 p の独立 bit-flip では log-density difference が重みの一次関数であるため重み IAT を参照できるが、BAR score と一般ノイズにまで同じ IAT を仮定していない。
20 seed の Wilson 区間 [0.433, 0.819] と各 8 seed の広い区間を示し、設定間の小さな被覆差を優劣や名目被覆の証拠としていない。
`--truth-file` は target p だけを機械的に照合し、同じ符号・decoder・failure 定義かの確認は `--trust-truth-file` を指定する利用者の責任であると明示されている。

## 残る制限と最小の改善案

toric d=3 では `minimum_weight_initial_state` と `maximum_weight_initial_state` が同じ重み 3 の配列を返し、対応する 8 seed の結果も同一なので、この二行から異なる初期重みへの感度は評価できない。
異なる初期重みの影響を調べる次の研究計測では、開始状態が実際に異なる符号または支持内の失敗状態を選び、配列と重みを CSV に記録するとよい。
低 p 比較は対象 p と ladder 全体を同時に変えるため、高 p 仮説の因果的な分離ではなく分布の記述的比較に留まる。
保存 1200・block 8 の 7/8 は pilot の出発点としては使えるが、観測 IAT より短い block と広い Wilson 区間のため、推奨値の確証にはならない。
`tests/test_bar_coverage.py` は 2 bit の非自明な nuisance 座標を含む exact 問題で 10 seed を走らせる緩い被覆回帰検査であり、benchmark の 20 seed 結果や名目 95% 被覆を保証するテストではない。
別の連続した seed 群 10〜19 と 20〜29 でも被覆は 10/10 と 9/10 で、5/10 の閾値に近い seed 調整の兆候は見なかった。

## 実行した確認

`%USERPROFILE%/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_bar_coverage.py tests/test_estimation.py -q` は 12 passed、14.24 秒だった。
最終 script の `samples_short --seeds 1 --truth-file <baseline_summary.csv> --trust-truth-file` は 5.02 秒で終了し、block 8 と既存 CSV と同じ seed 2026 の区間幅 0.06468969173676575 を出した。
元の baseline 20 seed や全 suite はこのレビューでは再実行しておらず、既存 CSV と WP 完了メモを照合した。
