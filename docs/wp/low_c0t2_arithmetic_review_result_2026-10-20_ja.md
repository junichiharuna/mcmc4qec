# C0T2：保存BAR行の独立算術レビュー

tile72 bit-flip p=.001について、保存済み38 archive・768 groupの全67,584行を読み、352設定×192 seedの集計を独立に再計算した。
最終reportとの照合11,968値は、最大絶対差0で一致した。
診断flag・未定義・区間未取得・数値推定失敗による分母からの除外は0である。
この結果により、先行する[6条件比較](low_long_six_comparison_result_2026-10-20_ja.md)で未追加だったC0T2の保存BAR行の独立算術確認を完了した。

## 確認した範囲

受理済みreport、転送plan、contextを固定hashで読み、各archiveのhashを3つの保存記録へ結び付けた。
38 archiveの合計9,490,191,365 byteについて、読取前後のSHA-256一致を確認した。
読み出すanalysis JSONはarchive manifestのbyte数・hashと照合し、ZIP member・group・設定・seedの欠落や重複を拒否した。
元sampling manifestは保存exportから読み、report中の元remote pathのbyte hashとproduction digestを照合した。
元の入力export全体、raw trace、ACF、復号label、WSS labelの再監査を行ったわけではない。

独立算術は[既存レビュー](low_recovered_arithmetic_review_result_2026-10-20_ja.md)と同一byteの標準library実装を使用した。
新しいsampling、decoder、BAR、bootstrap、WSS推定は実行していない。
整数・bool・件数を厳密照合し、浮動小数点の受理条件は既存レビューと同じ相対許容差1e-10・絶対許容差0とした。
今回実測された最大差は0である。
確認した指標はbias・RMSE・relative bias/RMSE、reference区間との重なりと全体包含、そのWilson区間、取得できた区間の平均幅、診断件数、失敗件数などである。

| 項目 | 結果 |
|---|---:|
| 読み出したgroup | 768/768 |
| 保存BAR行 | 67,584 |
| 設定数 | 352 |
| 各設定のseed数 | 192 |
| reportとの照合値 | 11,968 |
| reportとの最大絶対差 | 0 |
| 分母からの除外 | 0 |
| archive読取・算術レビュー実測 | 161.312秒 |

この時間は保存データ読取と集計の時間であり、samplingやBAR推定の計算時間ではない。
環境はWindows・Python 3.11.9で、追加読取の受入は10 passed・0.58秒だった。
この追加読取経路・実データレビューのLinux実行は未実施である。

## 修正と失敗記録

[小仕様](low_c0t2_arithmetic_review_spec_2026-10-20_ja.md)と受入を用意して実装した。
初回の実データ読取はkernel欄を配列として参照し、実際は名前をキーにした辞書だったため最初のgroupでKeyErrorとなった。
この時点では数値集計を開始しておらず、未完了の出力を成功結果として扱っていない。
名前順を明示的に検査する受入を追加し、既存算術sourceを変更せず読取側を修正した。
初回source・ログと出力directory `low_c0t2_portable_arithmetic_v1` を保持し、修正後は新しい `low_c0t2_portable_arithmetic_v2` へ実行した。

## 長い設定の既存図表との照合

fine ladder・16 chain・burn-in 6,000・保存60,000の16設定について、既存の6条件比較CSVとも432値を照合し、最大絶対差0だった。
したがって、既存図のC0T2の16点や診断件数を訂正する必要はなかった。
block32のreference重なり143–154/192、block1024の174–180/192、cross_chainの175–180/192という結果は維持される。
長い全16設定で診断flagは192/192であり、算術一致を混合改善とは扱わない。
referenceは有限標本の99.9%区間と省略質量上界を含む参照であり、厳密な真値ではない。
このレビューによって、母RMSE・名目95%被覆・低ノイズ全域の精度が保証されたわけではない。

## 保存物と再現

- [独立レビューJSON](data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/review.json)：設定・全archiveのpath/hash・環境・照合数・最大差。
- [全352設定CSV](data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/all_settings.csv)と[長い16設定CSV](data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/fixed_long_slice.csv)。
- [抽出した保存BAR行](data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/rows.jsonl)：計算に使用した行の設定・推定値・区間・flag・failureを保持する。
- [既存図表との照合](data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/verification.json)と[実行ログ](data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/actual_execution.log)。
- [最終manifest](data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/run_manifest.json)：source・失敗ログ・受入・数値結果など21ファイルを束ねる。

最終manifestのSHA-256は `877cbea76492cbe78a3bb526c56440cd1e1760dff643a7f177b32adc315fe26b` である。
元のarchiveと転送planを保持したrepositoryを指定し、未使用の出力directoryへ次のように再現する。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B docs/wp/data_tile_validation_2026-10-17/low_c0t2_portable_arithmetic_v2/reproduction/review.py --repository A:/dev/mcmc4qec --output output/low_c0t2_arithmetic_replay_new
```

sourceの配置先と実行時刻によりprovenanceの絶対path・実測時間は変わる。
この追加確認によって正式比較の完了条件数を増やさず、低ノイズは6/12条件のままである。
