# tile288 depolarizing p=0.01の低ノイズ校正結果

C3T0の最終解析job265459は2026-10-23 03:33:43 JSTにexit status 0で終了し、実walltimeは2時間30分28秒だった。
回収と保存BAR行の独立再集計が完了し、全768群・67,584行・352設定を含む。
これにより低ノイズ条件の検証作業は10/12条件が完了した。
精度・混合・名目95%被覆の認定ではない。

## 固定条件と結果

[sampling計画](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/sampling.json)に符号、ノイズ、decoder、ladder、seedと生成環境を保存した。
BP-OSDはbp_method=min_sum、max_iter=100、ms_scaling_factor=1.0、osd_method=osd_cs、osd_order=10、schedule=parallelである。
fine ladderは0.1、0.085、0.07、0.06、0.05、0.04、0.03、0.02、0.015、0.01である。
ZHはZ 0.7・H 0.3、ZHSはZ 0.6・H 0.3・stabilizer 0.1で、cluster_k=2・lazy=0.05である。
生成環境はPython 3.11.9、ldpc 2.4.1、bposd 2.1、NumPy 2.4.6で、sourceとnative profile・fixtureのhashを保持する。

事前固定した長い16設定は8 chain・burn-in 6,000・保存12,000・fine ladderである。
ZH/ZHS、logical_basis/logical_combination、block 32・128・1024/cross_chainを比較した。
全16設定で点推定と区間を192件取得したが、診断flag・high R-hat・low ESS・診断未定義も各192/192だった。
全seedを分母に残し、除外数は0である。

| 誤差法 | 設定数 | reference区間全体の包含 /192 | reference区間との重なり /192 | 診断flag /192 | 診断未定義 /192 |
|---|---:|---:|---:|---:|---:|
| block 32 | 4 | 0 | 192 | 192 | 192 |
| block 128 | 4 | 0 | 192 | 192 | 192 |
| block 1024 | 4 | 0 | 192 | 192 | 192 |
| cross_chain | 4 | 0 | 192 | 192 | 192 |

重み層別MCのreferenceは、各層のClopper–Pearson区間をBonferroniで合成し、省略質量上界を加えた99.9%区間[5.4522233011243575e-09, 2.0050098251715794e-05]である。
partial estimateは6.126214978763684e-07、plugin MCSEは3.8224032381066513e-07、省略質量上界は5.02494809277051e-15で、full_point_estimateはnullである。
reference区間が広く、192/192の重なりを真値の95%被覆と扱わず、全体包含0件も真値の被覆0件とは扱わない。
長い16設定の相対RMSE範囲の下端は26.19〜29.14%、上端は1,527.01〜1,571.02%である。
有限reference区間に基づく範囲であり、真の相対RMSEの点推定ではない。
全16設定で20%・10%の経験的精度gateを通らず、校正済み推奨設定や直接MCに対する速度優位を主張しない。
公開既定は変更しない。

## 再集計と再現資料

[独立再集計](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/review.json)は元reportの11,968値を照合し、最大絶対差は5.551115123125783e-17だった。
Windows Python 3.11.9での所要時間は78.819秒だった。
保存行の算術確認であり、sampling、decoder、raw trace、ACF、WSS、BAR、bootstrapの再実行ではない。
[全352設定CSV](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/all_settings.csv)、[長い16設定CSV](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/fixed_long_slice.csv)、[保存行](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/rows.jsonl)を保持する。
[再現source](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/reproduction/review.py)と[実行command](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/reproduction/command.json)も保存し、再実行時は未使用の出力directoryを指定する。

[最終report](data_tile_validation_2026-10-17/c3t0_recovery8h_final_collected_v1/artifacts/final-report.json)のSHA256は `a7d0afdeac6c457eacd72fd167f9eb217464e3a4fda1820ca0c1d7d907cd7bec` である。
[回収receipt](data_tile_validation_2026-10-17/c3t0_recovery8h_final_collected_v1/receipt.json)のSHA256は `167c329b8b80cfddff6bb5a1ad7ddec53683e96122e34e859ad26eb64ae6833e` で、acceptedとremote_snapshot_unchangedはtrueである。
reviewのSHA256は `c204874742c609c9c864fc9f4137446f722e52c873b2e62e6df34496f8e5b5bf`、manifestは `434039a7012b4c9a5b0960812ad86c56e022d9adf02adc4182f710d9dde46463` である。
29ファイルのhash・サイズと長い16設定CSVの全セルを[追加照合](data_tile_validation_2026-10-17/c3t0_final_review_observation_20261023_v1.json)した。
追加照合のSHA256は `12285ea9e87f7fbf11df3ecc4e0389f0b12bec5337f6c856051f24b2c499e0b3` であり、[照合source](data_tile_validation_2026-10-17/c3t0_final_review_observation_20261023_v1.py)を保存した。

tile288 depolarizingのp=0.003・p=0.001、全12条件の設定選択と独立計時、最終報告は未完了である。
