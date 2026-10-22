# tile288 bit-flip p=0.003の低ノイズ校正結果

C1T1の最終集計job265420は2026-10-22 02:57:27 JSTにexit status 0で終了し、実測walltimeは2時間24分9秒だった。
03:09に回収、03:10に保存BAR行の独立算術確認を完了した。
全768群・67,584行・352設定を含み、低ノイズ条件の検証作業は8/12条件が完了した。
これは精度・混合・95%被覆の認定ではない。

## 計算条件

[保存sampling計画](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/c1t1/review/sampling.json)を再現条件の一次資料とする。
BP-OSDはbp_method=min_sum、max_iter=100、ms_scaling_factor=1.0、osd_method=osd_cs、osd_order=10、schedule=parallelで、目標prior 0.003をladder全体とanchorで固定する。
fine ladderは0.1、0.085、0.07、0.06、0.05、0.04、0.03、0.02、0.015、0.01、0.007、0.005、0.003である。
ZHはZ 0.7・H 0.3、ZHSはZ 0.6・H 0.3・stabilizer 0.1で、cluster_k=2・lazy=0.05である。
生成環境はPython 3.11.9、ldpc 2.4.1、bposd 2.1、NumPy 2.4.6で、OMP・OpenBLAS・MKL・NumExprのthread数は1である。
source、native profile・fixtureのhashを保持し、版番号の一致だけでは環境間のfailure集合の一致と扱わない。

## 事前固定した長い16設定

8 chain・burn-in 6,000・保存12,000・fine ladderで、ZH/ZHS、logical_basis/logical_combination、block 32・128・1024/cross_chainを比較した。
すべての設定で点推定と区間は192件取得したが、診断flag・high R-hat・low ESSは各192/192だった。
診断未定義はZH・logical_combinationで191/192、それ以外で192/192であり、全件を分母に残した。

| 誤差法 | 設定数 | reference区間全体の包含 /192 | reference区間との重なり /192 | 診断flag /192 | 診断未定義 /192 |
|---|---:|---:|---:|---:|---:|
| block 32 | 4 | 0 | 192 | 192 | 191–192 |
| block 128 | 4 | 0 | 192 | 192 | 191–192 |
| block 1024 | 4 | 0 | 192 | 192 | 191–192 |
| cross_chain | 4 | 0 | 192 | 192 | 191–192 |

重み層別MCのreferenceは、各層のClopper–Pearson区間をBonferroniで合成し、省略質量上界を加えた99.9%区間[2.2322340171710182e-13, 1.2594912218352896e-07]である。
partial estimateは5.264352469032883e-09、plugin MCSEは3.7222724383363155e-09、省略質量上界は1.398797676910072e-15であり、full_point_estimateはnullである。
reference区間が広く、全192件との重なりは真値の95%被覆を示さず、全体包含0件も真値の被覆0件を意味しない。
長い設定の相対RMSE範囲の下端は26.20〜31.01%、上端は121,950〜129,325%である。
上端の大きさにはreference下端が極めて小さいことが影響しており、これを真の相対RMSEの点推定と解釈しない。
全16設定で20%・10%の経験的精度gateを通らず、校正済み推奨設定や直接MCに対する速度優位は主張しない。
公開既定は変更しない。

## 独立算術確認と再現資料

[独立再集計](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/c1t1/review/review.json)は各設定192 seedを除外せず集計し、元reportの11,968値との最大絶対差は5.551115123125783e-17だった。
既存の相対許容差1e-10・絶対許容差0を満たし、Windows Python 3.11での所要時間は51.275秒だった。
これは保存行の算術確認であり、sampling、decoder、raw trace、ACF、WSS、BAR、bootstrapの再実行ではない。
[全352設定CSV](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/c1t1/review/all_settings.csv)、[長い16設定CSV](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/c1t1/review/fixed_long_slice.csv)、[保存行](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/c1t1/review/rows.jsonl)を保持した。
[再現source](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/c1t1/review/reproduction/review.py)と[実行command](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/c1t1/review/reproduction/command.json)を保存し、再実行では未使用の出力directoryを指定する。
元archive・転送plan・入力hashはrequestとreviewに記録しており、この文書だけで全archiveを配布したという意味ではない。

[最終report](data_tile_validation_2026-10-17/planned_final_c1t1_collected_v1/artifacts/final-report.json)のSHA256は `1de516b3facd031855b9c33aa9aaf1f8f229a451eeab3b0868d442ae38819ffb` である。
[回収receipt](data_tile_validation_2026-10-17/planned_final_c1t1_collected_v1/receipt.json)のSHA256は `08156bdb194cde0baa55c1995e837edd2bd01b2964ffac34a0f1a593db78e489` で、acceptedとremote_snapshot_unchangedはtrueである。
reviewのSHA256は `5146270353ce6770a99db0263d5af5cb15f93f886cc3f7c147b55e995d64d4b6`、manifestは `948ad2672535e5aac45bd2dd06f324fd8670bc0011ad62320501c323f9158e99` である。
元reportはraw reference監査と現在のtrace payload再hashを記録しているが、全状態・全reference labelの再復号、anchor MCの再実行、native decoderの再検証は行っていない。
名目被覆・母RMSEの認定flagはfalseである。

最初の投入前失敗と復旧v1の失敗記録は保存し、[復旧仕様](c1t1_final_capacity_recovery_2026-10-22_ja.md)に従う別版driverで回収した。
旧watcherが記録したC1T1失敗は書き換えず、今回の[後続処理完了記録](data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/completed.json)を独立算術確認とcandidate作成の証跡とする。
低ノイズ全12条件の設定選択、独立計時、最終報告は未完了である。
