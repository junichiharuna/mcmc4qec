# tile288 bit-flip p=0.001の低ノイズ校正結果

C1T2の最終解析job265435は2026-10-22 15:24:48 JSTにexit status 0で終了し、実walltimeは2時間44分04秒だった。
15:37に回収と転送前後の照合、15:38に保存BAR行の独立再集計を完了した。
全768群・67,584行・352設定を含み、低ノイズ条件の検証作業は9/12条件が完了した。
これは精度・混合・名目95%被覆の認定ではない。

## 固定した計算条件

[保存sampling計画](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t2/review/sampling.json)を再現条件の一次資料とする。
BP-OSDはbp_method=min_sum、max_iter=100、ms_scaling_factor=1.0、osd_method=osd_cs、osd_order=10、schedule=parallelで、目標prior 0.001をladder全体とanchorで固定する。
fine ladderは0.1、0.085、0.07、0.06、0.05、0.04、0.03、0.02、0.015、0.01、0.007、0.005、0.003、0.002、0.001である。
ZHはZ 0.7・H 0.3、ZHSはZ 0.6・H 0.3・stabilizer 0.1で、cluster_k=2・lazy=0.05である。
生成環境はPython 3.11.9、ldpc 2.4.1、bposd 2.1、NumPy 2.4.6で、OMP・OpenBLAS・MKL・NumExprのthread数は1である。
sourceとnative profile・fixtureのhashを保持し、版番号の一致を環境間のfailure集合の一致とは扱わない。

## 事前固定した長い16設定

8 chain・burn-in 6,000・保存12,000・fine ladderで、ZH/ZHS、logical_basis/logical_combination、block 32・128・1024/cross_chainを比較した。
全16設定で点推定と区間を192件取得したが、診断flag・high R-hat・low ESS・診断未定義も各192/192だった。
全seedを分母に残し、未定義項目を含む結果を除外していない。

| 誤差法 | 設定数 | reference区間全体の包含 /192 | reference区間との重なり /192 | 診断flag /192 | 診断未定義 /192 |
|---|---:|---:|---:|---:|---:|
| block 32 | 4 | 0 | 192 | 192 | 192 |
| block 128 | 4 | 0 | 192 | 192 | 192 |
| block 1024 | 4 | 0 | 192 | 192 | 192 |
| cross_chain | 4 | 0 | 192 | 192 | 192 |

重み層別MCのreferenceは、各層のClopper–Pearson区間をBonferroniで合成し、省略質量上界を加えた99.9%区間[6.309944586015671e-15, 1.7406849390070254e-09]である。
partial estimateは1.0094180142318528e-10、plugin MCSEは7.137666997316734e-11、省略質量上界は4.177187461534978e-16で、full_point_estimateはnullである。
reference区間が広く、192/192の重なりは真値の95%被覆を示さず、全体包含0件も真値の被覆0件を意味しない。
長い16設定の相対RMSE範囲の下端は31.20〜34.74%、上端は5,746.54〜6,823.92%である。
これは有限reference区間に基づく範囲で、真の相対RMSEの点推定ではない。
全16設定で20%・10%の経験的精度gateを通らず、校正済み推奨設定や直接MCに対する速度優位は主張しない。
公開既定は変更しない。

## 独立再集計と再現資料

[独立再集計](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t2/review/review.json)は各設定192 seedを除外せず集計し、元reportの11,968値との最大絶対差は5.551115123125783e-17だった。
Windows Python 3.11.9での所要時間は57.771秒だった。
これは保存行の算術確認で、sampling、decoder、raw trace、ACF、WSS、BAR、bootstrapの再実行ではない。
[全352設定CSV](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t2/review/all_settings.csv)、[長い16設定CSV](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t2/review/fixed_long_slice.csv)、[保存行](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t2/review/rows.jsonl)を保存した。
[再現source](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t2/review/reproduction/review.py)と[実行command](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t2/review/reproduction/command.json)を保存し、再実行では未使用の出力directoryを指定する。
元archive・転送plan・入力hashはrequestとreviewに記録しており、この文書だけで全archiveを配布したという意味ではない。

[最終report](data_tile_validation_2026-10-17/planned_final_c1t2_collected_v1/artifacts/final-report.json)のSHA256は `f620a244ce380d0530f26d8bf4c880daec8fdaba4c3bf0484029f6309661e3d6` である。
[回収receipt](data_tile_validation_2026-10-17/planned_final_c1t2_collected_v1/receipt.json)のSHA256は `3dba42e680523f4e34952aebc07875726c5aa7ff5db7c0d1fa7f3a8b26dd7fb9` で、acceptedとremote_snapshot_unchangedはtrueである。
reviewのSHA256は `8b4c1e1301d429ee6b0c3f965e266d75722b5426e0f37348b96d13a218bf92e8`、manifestは `422709e9a4e3ce2e38215400a96d468f7f597c272eca8ff97efebfcb518f1218` である。
回収artifactと再集計出力の計29ファイル、長い16設定のCSVとreviewの全セル一致、条件と分母を[追加照合](data_tile_validation_2026-10-17/c1t2_final_review_observation_20261022_v1.json)で確認した。
そのSHA256は `7b138ab68adf08049a2cb24c5baf8cfbd308eec0652e1bcaa0ef6f5cd981bdea` で、照合sourceも同名の `.py` に保存した。
元reportはraw reference監査と現在のtrace payload再hashを記録しているが、全状態・全reference labelの再復号、anchor MCの再実行、native decoderの再検証は行っていない。
名目被覆・母RMSEの認定flagはfalseである。

残るtile288 depolarizingの低ノイズ3条件、全12条件の設定選択と独立計時、最終報告は未完了である。
