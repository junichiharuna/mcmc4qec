# tile72 bit-flip p=0.001の低ノイズ比較

最終集計265366.node-PRISMは2026-10-20 21:54:56 JSTにF・exit 0・run_count 1で終了し、walltimeは33分55秒だった。
終端受入と転送前後の同一性確認を通し、最終reportと実行記録13点を回収した。
352設定×事前固定192 seedの67,584行を保持し、全設定で点推定192件、区間未取得0件、記録された失敗0件だった。
全352設定の全192 seedに診断flag・high R-hat・low ESSがあり、計算完了を混合の良好さとは扱わない。

重み層別samplingの有限99.9%参照区間は `[1.4294542619067877e-05, 1.4294564407788293e-05]` であり、厳密な真値ではない。
各MC層のClopper–Pearson区間、Bonferroni調整、未計算重みの確率上限を含む。
以下は他条件と同じ事前計画の長い設定（16 chain・burn-in 6,000・保存60,000・fine ladder）の記述的比較であり、結果から選んだ推奨設定ではない。
相対biasと相対RMSEの幅は参照区間に対応する範囲であり、母集団RMSEの信頼区間ではない。

| kernel | 初期化 | 相対bias範囲 (%) | 相対RMSE範囲 (%) | block1024 被覆件数 | cross-chain 被覆件数 |
|---|---|---:|---:|---:|---:|
| ZH | logical_basis | 0.06418–0.06433 | 1.46345–1.46346 | 175/192 | 177/192 |
| ZH | logical_combination | 0.03092–0.03107 | 1.34856–1.34857 | 180/192 | 180/192 |
| ZHS | logical_basis | 0.10965–0.10980 | 1.45197–1.45198 | 176/192 | 175/192 |
| ZHS | logical_combination | 0.05745–0.05761 | 1.46657–1.46658 | 174/192 | 178/192 |

この8設定では参照区間全体を含む件数と交差する件数が一致し、表は全192 seedを分母として示す。
8設定とも診断未定義は0件だったが、全352設定では0〜192件であり、短い設定の未定義を除外していない。
診断flagのあるseedもbias・RMSE・被覆件数に含める。
有限cohortでの参照との整合性から、収束、支持の連結性、名目95%被覆、母集団RMSEを保証しない。
誤差法とnested trace長は軌道を共有しており、独立の追加cohortとして数えない。

trace監査は768群・192 anchor・184,320 planned sampling taskを対応付け、12,349,440の保存checkpointを再復号した。
失敗samplingは0件であり、最終集計は現存trace payloadと監査のhash対応を照合した。
全MCMC状態の再復号、anchor MCの再実行、全reference labelの再復号を行ったという主張ではない。
PCでの後処理・回収とクラスタでの最終監査を経た結果であり、転送成功だけを科学検証の根拠にしていない。

report SHA-256は `111a82133aa6ebdb1f03c4ea32237ca783686b584eaa63912608bf910c53cea5` である。
[集約JSON](data_tile_validation_2026-10-17/low_c0t2_recovered_summary_v1.json)、[再現script](data_tile_validation_2026-10-17/summarize_low_c0t2_recovered_v1.py)、[元集約処理からの変更記録](data_tile_validation_2026-10-17/low_c0t2_summary_derivation_v1.json)、[回収receipt](data_portable_bar_2026-10-19/mixed-c0t2-final-collected-v1/receipt.json)を保存した。
集約JSONのSHA-256は `afece9018da64a10dff9a591304da4fccce4897905ad8cdc845dfbae4ca53605` である。
元reportと実行記録は `data_portable_bar_2026-10-19/mixed-c0t2-final-collected-v1/artifacts/` に保持する。
同じ精度までの計算時間比較とtile288の低ノイズ6条件は未完了である。
