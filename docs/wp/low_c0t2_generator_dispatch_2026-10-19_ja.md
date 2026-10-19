# C0T2のanchor計算

次の固定条件C0T2はtile72・bit-flip・目標p=0.001であり、192 seed、target priorに固定したBP-OSD、16 chain、66000 stepを使う。
事前に保存したmanifestとpartitionを変更せず、既存の一回限りsubmitterでanchor phaseのpreflightとexecuteを各一度実行した。
source・script・runtime・native binary・旧controller終了・共有lock・待機を含む最大2要求nodeの検査を通してqsubした。

anchor jobは265337.node-PRISMで、投入応答はreturncode 0・ambiguous falseだった。
実PBSの脚本と要求資源1 node・96 CPU・32 GiB・上限1時間を照合した。
jobはF・exit 0・run_count 1、walltime 29秒で終了した。
この観測は正常終端と固定入力の確認であり、192 anchor成果物の最終集約・数値検証を完了したという意味ではない。

投入後確認の[観測スクリプト](data_tile_validation_2026-10-17/observe_c0t2_anchor_dispatch_v1.py)と[結果](data_tile_validation_2026-10-17/c0t2_anchor_dispatch_v1.json)を保存した。
localのpreflight・submission証拠は`data_tile_validation_2026-10-17/low_partition_0_2_anchors_0_*_once_v1_*`である。
同時にC0T1のBAR解析265334はR・run_count 1で継続していた。

## sampling partition 0の投入

anchor終了後、固定sampling partition 0についてpreflightの空き枠を確認し、executeを一度だけ実行した。
qsub応答はjob 265338.node-PRISM・returncode 0・ambiguous falseだった。
投入後に実PBS脚本と要求資源1 node・96 CPU・32 GiB・上限17時間30分を照合し、R・run_count 1を確認した。
このwalltimeは資源上限であり、完了予測ではない。
観測時の所有者active jobは265334と265338で、合計2要求nodeだった。

[観測スクリプト](data_tile_validation_2026-10-17/observe_c0t2_sample0_dispatch_v1.py)と[観測結果](data_tile_validation_2026-10-17/c0t2_sample0_dispatch_v1.json)を保存した。
localのpreflight・submission証拠は`data_tile_validation_2026-10-17/low_partition_0_2_sample_0_*_once_v1_*`である。
C0T2全体は192 anchor task・184320 sampling taskの計画であり、今回の投入だけで全partitionの完了を表すものではない。
sampling集約、BAR解析、trace監査、独立referenceとの正式比較は後続工程として残る。
