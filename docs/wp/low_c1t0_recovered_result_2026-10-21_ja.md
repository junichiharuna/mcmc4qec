# tile288 bit-flip p=0.01の低ノイズ校正結果

C1T0の最終検証job265383は2026-10-21 07:54:06 JSTにexit status 0で終了し、実測walltimeは1時間35分11秒だった。
全768群・67,584行・352設定を含むreportを回収し、回収receiptのacceptedとremote_snapshot_unchangedを確認した。
これにより低ノイズ検証の正式完了はtile72の6条件と合わせ7/12条件となる。
完了は検証作業の完了を指し、設定の精度・混合・95%被覆を認定したことを意味しない。

## 計算条件

[保存したsampling計画](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t0/review/sampling.json)を再現条件の一次資料とする。
decoderはBP-OSDで、bp_method=min_sum、max_iter=100、ms_scaling_factor=1.0、osd_method=osd_cs、osd_order=10、schedule=parallelである。
条件付きsamplingの各rungとanchorで目標prior 0.01を固定する実装を用い、rungごとの物理誤り率とは区別する。
fine ladderは0.1、0.085、0.07、0.06、0.05、0.04、0.03、0.02、0.015、0.01である。
ZHはZ 0.7・H 0.3、ZHSはZ 0.6・H 0.3・stabilizer 0.1で、両者ともcluster_k=2・lazy=0.05である。
生成時の保存runtimeはPython 3.11.9、ldpc 2.4.1、bposd 2.1、NumPy 2.4.6で、OMP・OpenBLAS・MKL・NumExprのthread数を1に固定している。
sourceとnative profile・fixtureのhashもsampling計画に保持しており、package版だけで異なる環境のfailure集合が同一だとは扱わない。

## 独立算術確認

回収した保存BAR行から、各設定192 seedを除外なしで再集計した。
元reportの11,968値との最大絶対差は1.1102230246251565e-16で、既存の相対許容差1e-10・絶対許容差0を満たした。
実行はWindows Python 3.11で51.460秒だった。
readerの実入力接続で見つかったexport hashとkernel mappingの取り違えは、[小仕様・失敗受入・修正・実入力確認](planned_arithmetic_reference_fix_spec_2026-10-21_ja.md)の順に別版で修正した。
算術式、seed、全件分母、元の科学計算と回収成果物は変更していない。
本確認はsampling、decoder、BAR、bootstrap、WSSの再計算ではない。

## 事前固定した長い16設定

8 chain・burn-in 6,000・保存12,000・fine ladderで、ZH/ZHSとlogical_basis/logical_combinationの4組を比較した。
誤差法はblock 32・128・1024とcross_chainの4種類で、計16設定である。
どの設定も点推定と区間を192件取得したが、診断flag・high R-hat・low ESSはいずれも192/192だった。
診断未定義はkernelと初期化の組により54〜68/192で、集計から除外していない。

| 誤差法 | 設定数 | reference区間全体の包含 /192 | reference区間との重なり /192 | 診断flag /192 | 診断未定義 /192 |
|---|---:|---:|---:|---:|---:|
| block 32 | 4 | 0 | 192 | 192 | 54–68 |
| block 128 | 4 | 0 | 192 | 192 | 54–68 |
| block 1024 | 4 | 0 | 192 | 192 | 54–68 |
| cross_chain | 4 | 0 | 192 | 192 | 54–68 |

referenceは層別MCのClopper–Pearson区間をBonferroniで合成し、省略質量上界を加えた99.9%区間で、[3.3419944370269276e-08, 1.038163335890121e-05]である。
partial estimateは6.4268873375551e-07だが、完全な真値としては扱わず、reportのfull_point_estimateはnullである。
この広いreference区間と全192件で重なったことは、真値の95%被覆を示さない。
全体包含0件も真値の被覆0件という意味ではなく、有限referenceに由来する評価の幅を区別する。
長い設定の相対RMSE範囲の下端は20.43〜22.30%、上端は1187.37〜1223.36%となり、referenceの不確かさを含む評価でも20%・10%の経験的精度gateを通らなかった。
この結果から校正済み推奨設定や直接MCに対する速度優位を主張せず、公開既定も変更しない。

## 証拠と再現

[最終report](data_tile_validation_2026-10-17/recovery_c1t0_final_collected_v1/artifacts/final-report.json)のSHA256は `c7715a02ff0ebec682359a3366137136dfb3e5dca7905f04e155f667d6f82189` である。
[回収receipt](data_tile_validation_2026-10-17/recovery_c1t0_final_collected_v1/receipt.json)のSHA256は `245fa7f9a7bbba1109de1cbcf7af77b3a790e4732d4bfac4e071678bae304320` である。
[独立再集計](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t0/review/review.json)には入力hash、実行環境、全数照合結果、計算時間と適用範囲を保存した。
[全352設定CSV](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t0/review/all_settings.csv)、[長い16設定CSV](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t0/review/fixed_long_slice.csv)、[保存行](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t0/review/rows.jsonl)も保存した。
[再現source](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t0/review/reproduction/review.py)と[実行command](data_tile_validation_2026-10-17/planned_arithmetic_handoff_v2/c1t0/review/reproduction/command.json)を保持し、再実行では未使用の出力directoryを指定する。
元archiveと転送planの配置はrequestとinput_sha256に記録しており、この報告だけで全archiveを配布したという意味ではない。
review manifestのSHA256は `9ba883a7c18b60b4abcfb193856d067dc79dabf2df29eb59ff1a3b0907b41045` である。
元reportはraw referenceの監査と現在のtrace payloadの再hashを記録しているが、全MCMC状態・全reference labelの再復号、anchor MCの再実行、native decoderの再検証は行っていない。
名目被覆と母RMSEの認定flagはいずれもfalseである。
