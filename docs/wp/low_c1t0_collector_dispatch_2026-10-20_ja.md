# tile288 bit-flip p=.01のsampling終端とcollector投入

sampling job `265343.node-PRISM` は2026-10-20 14:46:54 JSTにF・exit 0・run_count 1で終了した。
実walltimeは7時間52分17秒、CPU timeは622時間31分55秒、保存された使用memoryは10,974,072 KBだった。
前段anchor job 265342とsample job 265343の正常終端を既存readerで確認し、collectorのprepare・preflight・executeを一度ずつ行った。
sample partitionは0のみであり、存在しないsample 1は投入していない。

collector prepared SHA-256は `9ec6795d7b5dd3e7dd0920649ac0aefa2f2d18d128bb2cb0fc1b68e0f1e3c1f8` である。
要求資源は1ノード・1 CPU・32 GB・walltime上限2時間で、実測所要時間の予測とは扱わない。
preflightで要求中1ノードと空き枠を確認し、共有lockと直前の上限検査を通してqsubを実行した。
投入commandは `qsub /home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/runs/partitioned-full-1-0-v1/sampling-collection-submission/partition.sh` である。
返されたjob IDは `265356.node-PRISM` で、実qstatでもR・要求1 CPUを確認した。
この時点でC0T2 full trace監査265348もRであり、要求最大2ノードを維持した。

prepare・preflight・executeの全intent、script、stdout、stderr、receiptは `data_tile_validation_2026-10-17/low_partition_collection_1_0_*_once_v1_*` に保存した。
[実qstatと投入証跡](data_tile_validation_2026-10-17/low_c1t0_collector_dispatch_20261020_v1.json)のSHA-256は `6e2a21ccdae3ae1e91117c2ff2f1de1fd906baa88b2d114fdb42ea613c870f8d` である。
`output/record_low_c1t0_collector_dispatch_v1.py` は実PBS情報からこの記録を保存した読み取り用sourceである。
上記の一度限りの操作は使用済みであり、同じprepare・preflight・executeを再実行しない。

## 後続処理

collector265356は16:53 JSTまでにF・Exit_status -29となり、walltime 2時間00分33秒で設定上限2時間を超過した。
stderrにもPBSのwalltime超過によるkillが記録されている。
`sampling-collection/summary.json` はなく、`tasks.jsonl` は17,822,826 bytesで、最後の保存taskは `[1,0,1,1,137,0,4]` だった。
途中成果物は元の場所へ保持し、正常completionや全群回収として扱わない。
実qstatと途中ファイルのhash・stderrを [時間切れ記録](data_tile_validation_2026-10-17/c1t0_collector_timeout_20261020_v1.json) に保存し、SHA-256は `9b92e24702bddac9fd44a04269dc9d0cf52e33754384ec264fcf0b6e6514a371` である。
自動引継ぎは異常終端を拒否して停止し、completionもreference qsubも実行しなかった。
既存の `complete_low_partition_collection_once.py` をこの失敗jobへ呼び出さず、失敗記録を保持した別の復旧計画を作る。
collectorの受理後にも元環境のtrace監査、実reference生成、各PCのparity、全群BAR、独立referenceとの結合と計時が残る。
samplingの終了とcollectorの投入を科学検証完了とは扱わず、低ノイズ正式比較は5/12条件のままとする。

1群のnative parity referenceは元の専用契約でsamplingから独立して作成できるため、正常終了済みのanchor265342/sample265343と元入力を再確認し、別の操作で [reference265360を投入](portable_bar_native_reference_spec_2026-10-20_ja.md) した。
これは全群collectorの成功を代替せず、全群の最終科学評価には復旧したcollectorとtrace監査を引き続き必須とする。
