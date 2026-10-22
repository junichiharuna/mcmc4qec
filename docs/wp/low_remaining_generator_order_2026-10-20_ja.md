# 未完了のtile288低ノイズ生成順

固定生成planは `data_tile_validation_2026-10-17/low_sampling_partition_preparation_v1.json`、SHA-256 `68c74f4da10db79e11bcf21cea888c75d6553422cc736d090c3b7e6f9ce06775` を一次資料とする。
10月20日朝に稼働中のcase 1・target 0の生成partitionはsample 0だけであり、sample 1はplanに存在しない。
この点をlocalのselection readerでも確認し、存在しないsample 1はremote接続・投入前に拒否された。
sample 0 job 265343の正常終端後は、生成partitionを追加せずcollectorの準備へ進む。
265343は10月20日14:46:54 JSTに正常終了し、[collector265356をqsubで投入](low_c1t0_collector_dispatch_2026-10-20_ja.md)してRを確認した。
collectorの正常終端受理は未実施である。

case 1・target 1/2とcase 3・target 0/1/2は、それぞれanchor 0とsample 0/1を持つ。
同じroot・phase・indexへの使用済み投入を繰り返さず、実qstatと保存intentを照合する。
待機中も含めて最大2ノードを維持する。

直近の空き枠はC0T2のfull trace監査を優先する。
その正常終端後、実空き枠が得られた段階でcase 1・target 1のanchor 0を次候補とする。
localの固定selection照合は成功し、rootは `/home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/runs/partitioned-full-1-1-v1`、1ノード・96 CPU・32 GB・walltime上限2時間である。
このlocal照合ではremote接続もqsubも行っておらず、上限2時間は実測所要時間ではない。

次候補を使用する場合は未使用のpreflightを実行して、正常応答・入力一致・空き枠を確認し、その後にexecuteする。
既存記録があれば操作を繰り返さない。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B output/submit_low_partition_once.py --case 1 --target-index 1 --phase anchors --index 0 --preflight
# 上記の成功と実node空きの確認後に限る。
& $taskPython -B output/submit_low_partition_once.py --case 1 --target-index 1 --phase anchors --index 0 --execute
```

上のanchor preflight・executeは10月20日に使用済みとなり、job265357は正常終了した。
続くsample partition 0のpreflight・executeも実施し、job265358のRを確認した。
実記録と使用済み操作は[生成開始記録](low_c1t1_generation_dispatch_2026-10-20_ja.md)を参照し、同じコマンドを再実行しない。
sample partition 1も17:17 JSTまでにqsubへ投入し、job265361のQを確認した。
当該preflight・executeも使用済みであり、実記録は [追加投入記録](low_c1t1_generation_dispatch_2026-10-20_ja.md) に保存した。
各samplingの後にはcollector、元環境trace監査、BARの比較、独立referenceとの結合、計時が残るため、生成の終端を全検証完了と扱わない。

## 20:29 JST：次条件の実クラスタ事前検査

case 1・target 2、tile288 bit-flip p=.001のanchor 0について、固定生成planから既存helperのpreflightを一度だけ実施した。
元クラスタのsource・native binary・runtime・plan・scriptと旧controllerの終端を照合し、returncode 0・ambiguous=falseで終了した。
実応答はslot_available=false・qsub_executed=falseであり、実投入は行っていない。
[preflight receipt](data_tile_validation_2026-10-17/low_partition_1_2_anchors_0_preflight_once_v1_receipt.json)のSHA-256は `ba68782130ea11622ceb010840dbdd659c3ae78fe141e3ee0429194830f55738` である。
`low_partition_1_2_anchors_0_preflight_once_v1_*` は使用済みであり、同じpreflightを再実行しない。
次のexecuteは未使用であり、C0T2最終投入と復旧capacity/full監査の既存監視を優先し、実空き枠と共有lockを確認してから行う。
execute自身も元source・runtime・native・planと待機中を含む最大2ノードをqsub直前に再検査する。
このpreflightをanchorの投入・正常終端・sampling開始の証拠とは扱わない。

## 21:35 JST前後：C1T2のsampling事前検査

case 1・target 2のsample 0とsample 1について、未使用のpreflightをそれぞれ一度だけ並列に実行した。
両方ともreturncode 0・ambiguous=false・qsub_executed=falseで、元source・native binary・runtime・plan・scriptと旧controllerの終端を照合した。
両応答ともslot_available=falseであり、新しいqsubは行っていない。
sample 0の [receipt](data_tile_validation_2026-10-17/low_partition_1_2_sample_0_preflight_once_v1_receipt.json) はSHA-256 `98d8570f3d974b6925e0d90477ef77b81864fb73214d9909f136b3b0bc96deb7`、sample 1の [receipt](data_tile_validation_2026-10-17/low_partition_1_2_sample_1_preflight_once_v1_receipt.json) は `958cc4fecd18644f4adb70ecced405510f6b62d8971719accf49b85ca6cb6429` である。
これでC1T2のanchor 0・sample 0・sample 1のpreflightは全て使用済みとなったため、同じpreflightを再実行しない。
3ジョブのexecuteはいずれも未使用である。

次の生成は、既存C0T2 finalとC1T0復旧capacity/full監査の引継ぎを優先し、その後の実空き枠でC1T2 anchor 0から進める。
C1T1生成が既に終わっている場合は、[担当driver](planned_c1t1_handoff_spec_2026-10-20_ja.md)のcollector・監査を優先し、同時の手動投入を競合させない。
sample 0/1の実投入時にも固定helperのexecuteが元source・runtime・native・planと最大2要求ノードをqsub直前に再検査する。
prepare/preflight済みであることだけを、新しい投入許可や空き枠の証拠とは扱わない。

## 22:49 JST：次生成の担当driver

C1T2の[生成引継ぎdriver](planned_c1t2_generation_handoff_spec_2026-10-20_ja.md)をlocal PID44160で起動した。
先行C1T1 full監査とnative referenceの正常完了後、anchor 0の投入・正常終端確認、sample 0/1の空き枠への投入を担当する。
当該3 executeを手動で重複実行しない。
Windows/Linux各14件の受入と実3preflightの照合を通過したが、起動時点で新しいqsubは行っていない。
共有lockと待機中を含む最大2ノード検査を維持し、sample 0/1は空き枠があれば並行実行する。

## 23:15 JST：残るdepolarizing 3条件の事前検査

case 3・target 0/1/2のanchor 0・sample 0/1、計9件の未使用preflightを、条件ごとに3件ずつ並列で実行した。
全件がreturncode 0・ambiguous=false・qsub_executed=falseで終了し、元source・native binary・runtime・plan・PBS scriptと旧controllerの終端を照合した。
全件でslot_available=falseであり、新しいqsubは実施していない。
9件のpreflightは使用済みとなったため、同じpreflightを再実行しない。
9件のexecuteは未使用で、C3向け自動投入driverも未起動である。
既存C1T2生成引継ぎと先行監査の順序を維持し、後続の実投入は共有lock・最大2要求ノードをqsub直前に再検査する。

| 条件 | anchorの要求walltime | 各sample分割の要求walltime |
|---|---:|---:|
| C3T0 | 3時間 | 21時間30分 |
| C3T1 | 3時間 | 21時間30分 |
| C3T2 | 3時間 | 22時間30分 |

全ジョブの要求は1ノード・96 CPU・32 GBで、walltimeは上限であり実測所要時間やETAではない。
固定plan・helper・実応答・receipt・使用済み/未使用区分を[52ファイルのmanifest](data_tile_validation_2026-10-17/c3_generator_preflights_v1/manifest.json)へ保存した。
事前検査の成功をsampling・混合・被覆の検証完了とは扱わない。
