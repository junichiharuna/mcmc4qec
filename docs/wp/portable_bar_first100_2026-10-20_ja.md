# Portable BARの100群回収時点

2026年10月20日01:04 JST時点の途中記録である。
DGXのbatch 0～4について、保存済みarchive・実行元・回収記録の検証を既存index処理で実施し、[100群のindex](data_portable_bar_2026-10-19/first100-cohort-inventory-v1.json)に保存した。
全768群のうち100群を回収済みで、668群は未回収として分母に保持している。
観測済みは8800行、未回収分は58784行で、全計画は67584行である。
回収済みのinfra failureと区間未取得は0だが、診断flagは8800行すべてにあり、診断未定義は5348行ある。
これらを除外して被覆や精度を主張せず、全sampling・元traceの監査・独立referenceとの最終比較は未完了として扱う。

DGX batch 5は開始済みで、実際のexecution intentに結び付けた回収準備を完了した。
batch 6の入力配置処理は進行中であり、この時点では本計算を開始していない。
Labo PCの本計算parent PID 15892と一致検証PID 15784は実プロセス照会で存在を確認した。
一致検証PIDの累積CPU時間は4960.65625秒であり、前回の2628.86秒から増加している。
クラスタの265334と265338はともにPBS状態R・run_count 1であり、新規qsubは行っていない。

再現には既存の `output/index_portable_collected_v1.py --snapshot-name <新しいファイル名>.json` を用いる。
今回のログは `output/portable_bar_first100_inventory_v1.log` に保存した。
公開候補のコード・配布物は変更していない。

## 次バッチの準備完了

その後、batch 6の入力配置が終了コード0で完了した。
入力は20群・14577 member・278721846 byteで、archive SHA256は `ff5355f3cc1a4e94913818ca47b784e491c64730513587001d1f4af882f6e6f0`、manifest SHA256は `cbf94b0043ebfb8e7dbb07943bc807f423a191587b7cf3113aca50460efc6b9a` である。
既定の固定ownerと元の順序で選択し、batch 5の完了確認・回収検証後にbatch 6へ引き継ぐcontrollerを起動した。
controllerは `output/portable_bar_later_handoff_v1.py dgx 6` で、記録は [controller](data_portable_bar_2026-10-19/dgx-batch6-handoff-controller-v1.json) と [観測ログ](data_portable_bar_2026-10-19/dgx-batch6-handoff-observations-v1.jsonl) に保存する。
batch 6本計算の開始とは区別する。
