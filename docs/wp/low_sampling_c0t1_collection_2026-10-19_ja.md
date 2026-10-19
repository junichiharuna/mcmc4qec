# C0T1のサンプリング終了と集約投入

2026-10-19にC0T1のsample partition 1、job 265327.node-PRISMのF・Exit_status 0・run_count 1を確認した。
実walltimeは05:00:08である。
anchor 265317とsample partition 0の265319は先に正常終了しており、これでC0T1の3 generatorが終了した。
固定された全入力・投入記録・元PBSのscriptと資源・native環境を既存のcollector入口で照合し、prepare・preflight・executeを各一回実施した。
prepared SHA256は `a8de133844236c4a79c942d3b6f6e818789729bf028ddf73b066c79723b21ec6` である。
集約job 265332.node-PRISMをqsubで投入し、実R・run_count 1・scriptと資源の一致を確認した。
資源は1 CPU・1 worker・32GB・1ノード、walltime上限2時間である。
この2時間は初期の資源上限で、実測に基づく終了予定ではない。
同時に稼働するBAR再開265331と合わせ、待機中を含む要求ノード数が2であることを確認した。
公開候補915ファイルが不変であることも再確認した。

投入と観測は [low_partition_collection_dispatch_265332_v1.json](data_tile_validation_2026-10-17/low_partition_collection_dispatch_265332_v1.json) に保存した。
観測JSONのSHA256は `aaf77b987a951bf7ad93019aacd70a4f3644832b92187164e45cb0fa23f87b2b` である。
同じdataディレクトリの `low_partition_collection_0_1_{prepare,preflight,execute}_once_v1_*` に各intent・receipt・送信script・stdout・stderrがあり、再実行しない。
サンプリングのPBS成功終了はraw artifactの全監査やBARの最終比較完了とは別である。
低ノイズの正式比較完了数は3/12のままである。

次はjob 265332のF・Exit_status 0・run_count 1を確認した後、Python 3.11の絶対パスで `output/complete_low_partition_collection_once.py --case 0 --target-index 1 --prepared-sha256 a8de133844236c4a79c942d3b6f6e818789729bf028ddf73b066c79723b21ec6` を一度だけ実行する。
完了受理前にanalysisやtrace監査を成功扱いせず、実行済みのcapacity 265318との結び付きを確認してから本解析を準備する。
BAR再開265331についても完了summaryと成功終了の受理は未実施であり、[v2実行後手順](low_bar_recovery_v2_runbook_2026-10-19_ja.md)へ進む条件を満たした時点で処理する。
