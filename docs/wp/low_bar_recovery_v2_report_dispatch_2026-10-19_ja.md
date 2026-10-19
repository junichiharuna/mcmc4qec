# BAR再開の完了受理と最終比較の投入

2026-10-19に再開job 265331.node-PRISMのF・Exit_status 0・run_count 1を確認した。
実walltimeは01:15:33、最大RSSは125969580kbである。
v2の完了入口と保存記録のreadbackを通し、全768群・67584行、再利用672群・再計算96群の終了metadataを受理した。
完了記録のSHA256は `7a4304d1054be8a7ce698fd6ad4cbd19235ff60c1a5985de795fd3ad3accf33f` である。
実PBS・投入記録・群markerの再hashを確認した受理であり、親側で群payload・結合済み行・raw traceを全再hashした意味ではない。
trace監査との結合とreferenceの全検証は後続のPBS処理で行う。

再開完了、既存のtrace監査265326、reference producer 265221とaudit 265227の記録を結び付け、最終比較のprepare・preflight・executeを各一度実施した。
prepared SHA256は `f3de3baccd8d80c0c5bdb9e9008e1db77f83e77d5edd0e992dd9b7b9585427fc` である。
実測のRSSと検証済みの資源規則から、1 CPU・1 worker・241GB・1ノード、walltime上限24時間が選ばれた。
24時間は要求上限であり、終了予定ではない。
job 265333.node-PRISMをqsubで投入し、実R・run_count 1と資源の一致を確認した。
同時にC0T1の集約265332がRであり、合計2ノードで稼働している。
投入後の観測とローカル入力210件の照合を [low_bar_report_dispatch_265333_v1.json](data_tile_validation_2026-10-17/low_bar_report_dispatch_265333_v1.json) に保存した。
観測JSONのSHA256は `56d33f16f00c1cbc78f399c683c5298060a90f2bb2df1a83b6c9ac4b1daa5f31` であり、公開候補915ファイルが不変であることも確認した。
最終比較の完了受理・回収は未実施で、低ノイズの正式比較完了数は3/12のままである。

投入前後のローカル記録は `data_tile_validation_2026-10-17/low_bar_recovery_report_control_{prepare,preflight,execute}_v2_*` に保存し、再実行しない。
再開完了の記録は同ディレクトリの `low_bar_recovery_completion_once_v2_*` にある。
次は265333のF・Exit_status 0・run_count 1を確認後、[v2手順](low_bar_recovery_v2_runbook_2026-10-19_ja.md)の報告完了受理と回収へ進む。
集約265332は独立に終了を確認し、[C0T1の手順](low_sampling_c0t1_collection_2026-10-19_ja.md)で受理する。
