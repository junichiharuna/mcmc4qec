# tile288 bit-flip p=.003の生成開始

C0T2 full trace監査job265348は14:55:16 JSTにF・exit 0・run_count 1で終了し、walltimeは8分20秒だった。
空き枠と既存の生成順を確認して、case 1・target 1のanchor partition 0をqsubで投入した。
job265357は15:03:05 JSTに開始し、15:04:42 JSTにF・exit 0・run_count 1、walltime1分36秒で終了した。
[anchor投入と実PBS記録](data_tile_validation_2026-10-17/low_c1t1_anchor_dispatch_20261020_v1.json)のSHA-256は `ea3186a283b0d588610dc04c8d7433d3b5ca6c6fa39b24b7ffaaaa35daf134f8` である。

anchorの正常終端後、sample partition 0の未使用preflightで空き枠を確認し、executeを一度だけ実行した。
返されたjob IDは `265358.node-PRISM` で、15:07 JSTの実qstatでRを確認した。
投入commandは `qsub /home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/runs/partitioned-full-1-1-v1/sampling-submissions/sample/0/partition.sh` である。
要求は1ノード・96 CPU・32 GB・walltime上限12時間30分で、この上限を予想所要時間とは扱わない。
同時にC1T0のcollector265356がRであり、待機中を含む要求最大2ノードを維持した。
[sampling投入と実PBS記録](data_tile_validation_2026-10-17/low_c1t1_sampling_dispatch_20261020_v1.json)のSHA-256は `95c554878173c587383d689bca21c6de4f65b1762da00e373291518dde3f6339` である。

事前固定planのSHA-256は `68c74f4da10db79e11bcf21cea888c75d6553422cc736d090c3b7e6f9ce06775` を維持した。
全preflight・submissionのintent、実script、stdout、stderr、receiptは `data_tile_validation_2026-10-17/low_partition_1_1_anchors_0_*` と `low_partition_1_1_sample_0_*` に保存した。
これらは使用済み操作であり、同じpreflight・executeを繰り返さない。
sample partition 1はplanに存在するが、本書作成時点では未投入である。
collector、元環境trace監査、BAR、独立referenceとの結合と計時はまだ残っている。
この生成開始を科学的な精度や被覆の受理とは扱わない。

## sample partition 1の投入

native reference265360の正常終端・回収後、17:16 JSTの未使用preflightで既存要求1ノードと入力・sourceの一致を確認した。
sample partition 1のexecuteを一度だけ行い、`265361.node-PRISM` としてqsubに受け付けられた。
commandは `qsub /home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/runs/partitioned-full-1-1-v1/sampling-submissions/sample/1/partition.sh` である。
要求は1ノード・96 CPU・32 GB・上限12時間30分であり、所要時間の予測ではない。
17:18 JSTの実qstatではsample 0の265358がR、sample 1の265361がQで、待機分を含む最大2ノードを維持した。
[実投入とPBS記録](data_tile_validation_2026-10-17/low_c1t1_sampling1_dispatch_20261020_v1.json) のSHA-256は `edafec960a568327fe975ac099bd979229d9981622afc32a9901f17bb12ca424` である。
`low_partition_1_1_sample_1_preflight_once_v1_*` と `low_partition_1_1_sample_1_submission_once_v1_*` は使用済みであり、同じ操作を繰り返さない。
C1T0 collectorの復旧とC0T2の最終collectorは別の未完了処理で、実行可能になってから次の空き枠へ投入する。
