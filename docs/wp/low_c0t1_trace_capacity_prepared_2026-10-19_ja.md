# C0T1 trace監査の資源計測準備

2026-10-19、受理済みC0T1 sampling集約を入力として、既存の`prepare_low_partition_trace_once.py`を一度実行した。
実collectorの終端、受理記録、sampling計画と入力hash、固定sourceとnative環境、生成脚本の構文を照合し、prepareを受理した。
prepared SHA256は`30a1d7cc2d53bb7ee042eb7f55bc322eb45cd923f7879604c6ef3c7a3dde02da`である。

監査用の独立rootは`/home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/runs/partitioned-trace-capacity-0-1-v1`である。
計画は2 replicate・8 workerの資源計測であり、後続の全seed監査ではない。
初期要求上限は1 node・96 CPU・340 GiB・24時間である。
この上限は実測使用量や完了予測ではなく、実資源計測後にfull auditの資源を決める。
prepareは全raw payloadの再hashを行っておらず、科学的精度や混合・被覆の検証完了を意味しない。

準備時点ではC0T0最終比較265333とC0T1 BAR解析265334が稼働中だった。
最大2要求nodeを維持するため、trace capacityのpreflightとqsubは未実施である。
空き枠ができたら同じprepared hashで`submit_low_partition_trace_once.py`のpreflightを行い、その結果と直前の実PBS状態を確認して一度だけexecuteする。
集約のprepared hashは`a8de133844236c4a79c942d3b6f6e818789729bf028ddf73b066c79723b21ec6`を使う。
資源計測の実終端を受理した後にfull auditを準備し、BARと監査の両方を受理してから正式比較へ進む。

実行記録は`data_tile_validation_2026-10-17/low_partition_trace_capacity_0_1_prepare_once_v1_`で始まるintent・script・stdout・stderr・receiptに保存した。
実行receiptはaccepted true・return code 0・qsub_executed falseである。
同じprepareを再実行せず、保存済み証拠とremoteの`parent-prepared.json`を以後の入口へ渡す。
今回、公開候補・科学設定・既存の実行コードは変更していない。
