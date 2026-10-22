# tile72 bit-flip p=0.003の低ノイズ比較

C0T1の最終比較265341.node-PRISMはF・exit 0・run_count 1、walltime 51分11秒で終了した。
親側の終端受入と転送前後の同一性確認を通し、reportと実行記録13点をローカルへ回収した。
352設定×事前固定192 seedの67,584行を保持し、全設定で点推定192件、区間未取得0件、記録された失敗0件だった。
一方、全352設定で189–192 seedに診断flagがあり、長い設定にも混合上の懸念が残った。

参照は重み層別samplingによる有限の99.9%区間 `[0.00015190300429955927, 0.00015190804002956739]` であり、厳密な真値ではない。
各MC層のClopper–Pearson区間、Bonferroni調整、未計算重みの確率上限を含む。
以下は事前計画の長い設定（16 chain・burn-in 6,000・保存60,000・fine ladder）を記述的に抜き出したもので、結果を見て選んだ推奨設定ではない。
相対biasと相対RMSEの幅は参照区間内での範囲であり、母集団RMSEの信頼区間ではない。

| kernel | 初期化 | 相対bias範囲 (%) | 相対RMSE範囲 (%) | block1024 被覆件数 | cross-chain 被覆件数 |
|---|---|---:|---:|---:|---:|
| ZH | logical_basis | −0.0309–−0.0276 | 1.1612–1.1613 | 180/192 | 182/192 |
| ZH | logical_combination | −0.0538–−0.0505 | 1.1673–1.1674 | 179/192 | 182/192 |
| ZHS | logical_basis | −0.0742–−0.0708 | 1.2036–1.2038 | 182/192 | 182/192 |
| ZHS | logical_combination | 0.0036–0.0069 | 1.2200–1.2201 | 182/192 | 181/192 |

この8設定では、参照区間全体を含む件数と参照区間に交差する件数が一致しており、表はその件数を全192 seedを分母として示す。
8設定すべてでflaggedとlow ESSが192/192、high R-hatは144–156/192、診断未定義は0/192だった。
診断flagのあるseedを除外せずにbias・RMSE・被覆件数を計算している。
この有限cohortの誤差や被覆件数から収束、支持の連結性、名目95%被覆、母集団RMSEを保証しない。
全352設定ではhigh R-hatが144–192、low ESSが186–192、診断未定義が0–192であり、長い設定の未定義0件を全設定へ一般化しない。
誤差法とnested trace長は軌道を共有しており、独立の追加cohortとして数えない。
この条件からZHSの一律の優位性や低ノイズ全域の精度を主張しない。

trace監査は768群・192 anchor・159,744 planned sampling taskを対応付け、10,702,848の保存checkpointを再復号した。
失敗samplingは0件で、最終比較で現存trace payloadのhashと監査記録の対応を照合した。
全MCMC状態の独立再復号やanchor MCの再実行をしたわけではない。
referenceの生artifact hash、物理誤りの乱数再生成、集計の再現を確認し、復号labelの検査は5,813,747件中24,175件であり、全labelの再復号ではない。
時間切れとなった元BAR解析265334の検証済み629群を再利用し、欠けていた139群を回復job 265340で再計算した履歴をreportに保持している。

reportのcompletion SHA-256は `296349b1910bfce5c05cc55bb0fec44caa2945dbd49514e4a8533848dafa91cf`、report SHA-256は `db0fbd9ea104bf55c5f5a84d29f5cf291e4312a47061f567fa4de156d537bcb2` である。
[集約JSON](data_tile_validation_2026-10-17/low_c0t1_recovered_summary_v1.json)と[再現スクリプト](data_tile_validation_2026-10-17/summarize_low_c0t1_recovered_v1.py)を保存した。
集約JSONのSHA-256は `a2051966bcd97d003c9a859d0e606e995866e3565c60b5f39b150e44f3141a78` である。
再現スクリプトは検証済みC0T0集約処理のreport hash・保存先・条件座標・物理誤り率だけを変更したもので、変更記録は `data_tile_validation_2026-10-17/low_c0t1_summary_derivation_v1.json` に保存した。
元reportと実行記録は `data_tile_validation_2026-10-17/low_bar_recovery_report_c0t1_collection_v1/artifacts/` にあり、454,663,531 byteのreportを固定済み公開候補へ追加していない。
同じ精度までの計算時間の比較と、残る条件の検証は未完了である。
