# 独立計時の資源・並列性監査（2026-10-25）

ユーザー指定の上限は同時に最大2物理ノード、各96コアであり、2ジョブという指定ではない。
前段と同じノードを継続使用する指定もなく、前段完了後に別の2ノードを使用しても適合する。
現行の独立計時では各ジョブのCPUまたは予約メモリが1ノード分を必要とするため、結果として同時最大2ジョブとなる。
このため、現在のtailの並列数制限は変更しないと判断した。

| 工程 | PBS要求CPU | 実行worker数 | 予約メモリ | 根拠 |
|---|---:|---:|---:|---|
| capacity | 2 | 2 | 340 GiB | 2つのfull estimatorによる事前計測、walltime上限24時間 |
| benchmark | 96 | 1〜96 | 32〜340 GiB | capacityで観測したRSSと時間からworker数・partitionを決定 |

capacity同士は340 GiBずつの予約により同一ノードへ収まらず、benchmark同士は96 CPUずつの要求により同居できない。
capacityとbenchmarkの組合せも98 CPU・最低372 GiBとなり、同一ノードへ配置できない。
capacity段階のCPU利用が少ないのは、2 estimatorという計測契約と保守的なメモリ予約によるもので、ジョブ数ゲートだけを緩めても解消しない。
benchmarkのCPU要求は常に96だが、実worker数はメモリ制約やpartitionのtask数により96未満になり得る。

固定の候補一覧は48行だが、実行対象数、capacity後のpartition数、実worker数はまだ未確定である。
監査時点では新しい独立計時の入力ディレクトリも未作成であり、未実測のworker数や利用率を推定値で確定していない。
実行は `calibration.parallel_map` のprocess poolで行い、各workerの数値ライブラリのthread数は1に固定する。

制限はschedulerの `running < 2`、共通の `can_submit`、remoteの要求ノード数集計、実submitterの投入直前検査に存在する。
根拠は `output/low_partition_independent_execution_v1/engine.py:91`、同 `remote.py:61`、`output/low_timing_selection_execution_v1/execution.py:16`、`cluster_scripts/submit_tile_low_noise_timing_execution.py:87` にある。
資源決定は `cluster_scripts/tile_low_noise_timing_execution.py:57` と同ファイルの `resource_plan` にある。

予約メモリを減らす、要求CPUをworker数まで減らす、複数条件を同一ノードへ詰め込む変更は、単なる上限の読み替えではなく新しい資源・計時方式となる。
同居処理による競合やI/O負荷はtask wall、CPU時間、capacityからのpartition予測に影響するため、元の計時結果と無条件に統合できない。
現在のreport実装はCPU model、frequency、affinity、NUMA、concurrent loadをunknownとし、`hardware_equivalence_certified=False` を記録する。
2点のcapacityから96 workerへの資源外挿も未検証であり、計時や診断から精度・被覆・高速化を保証しない。
現submitterはvnodeを固定しないが、各ジョブが単一ノードで同時最大2件であるため、ユーザーの同時2物理ノード上限に適合する。

実行予定のtail設定からparent environmentとimport元を読み、次の実ファイルのSHA-256を照合した。
パスはクラスタの `$HOME` 相対で示す。

| 証跡 | パス | SHA-256 |
|---|---|---|
| tail設定 | `$HOME/workspace/mcmc4qec/20261025-low-parallel-tail-v2/tail-config-v5.json` | `171e40877853b59393153028599b5269dbccffb2bbc4ddbdec4027624aefe6ad` |
| parent environment | `$HOME/workspace/mcmc4qec/20261024-low-parallel-parent-environment-v1/parent-environment.json` | `8e069c1137ccad9415edf3b5d296184e326722cc2a514d0b67ce76b52abd7a6f` |
| 実runner | `$HOME/workspace/mcmc4qec/20261018-tile-low-timing-stage3-v2/cluster_scripts/tile_low_noise_timing_execution.py` | `d32c910b25058cc76f3d4d540c3b40801febd810f66b7e156b2b554be8ddc7cc` |
| 実submitter | `$HOME/workspace/mcmc4qec/20261018-tile-low-timing-stage3-v2/cluster_scripts/submit_tile_low_noise_timing_execution.py` | `e008f847fdf5b3074de944dcb9f55f2eb998868f0a9c0c2410781d9329ccd485` |

本監査は読み取りだけで行い、source・構成・実行中のflow・固定済み入力の変更、計算の実行、ジョブ投入は行っていない。
この文書の追加だけを行った。
