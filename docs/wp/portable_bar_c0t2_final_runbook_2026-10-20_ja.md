# C0T2 portable BARの最終評価手順

対象はtile72・bit-flip・target_index 2の固定production `8093838b22f74cad6ed113b5af8c185034b2585cfc4d0d7b374f150d9654b396` である。
この条件は保存配列をLaboとDGXで後処理しているため、通常のcluster BAR partition・BAR collectorを作る経路とは区別する。
sampling完了、元クラスタ環境の全trace監査、旧新混在768群の回収、両hostの完全parity、独立WSS referenceを最終評価で結び付ける。
部分回収や個別parityの成功を、全群の精度・混合・名目95%被覆の保証とは扱わない。

## 18:27 JSTまでの実行状況

full trace監査265348は正常終了し、completion readerも使用済みである。
DGX再割当てbatch13までとLabo最終batch5の回収を完了し、[snapshot v20](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v20.json) で768群・67,584行・未回収0を照合した。
Labo batch5のprepare・collectは使用済みであり、再実行しない。
全行に診断flagがあり、診断未定義は41,424行、区間未取得と基盤失敗は0だった。
最終reportはまだ未作成であり、回収完了を科学検証完了とは扱わない。
最終転送contextの作成先は `output/portable_mixed_c0t2_distribution_v1` とする。
初回にdata directoryを出力先へ指定した呼出しは、output配下を要求する事前検査で拒否され、出力作成前に終了した。
指定を修正したcontext生成は成功し、同じ出力先へ重複実行しない。
context SHA-256は `79f3aab5862d5bb4f36370140dde73a47317e640c82678414b9d6d204817a557`、転送対象は130ファイルである。
17:50 JSTに転送helperを起動し、配置先を `/home/user/workspace/mcmc4qec/20261020-portable-mixed-c0t2-inputs-v1`、local記録先を `data_portable_bar_2026-10-19/mixed-c0t2-final-transfer-v1` とした。
転送は130ファイル・9,532,490,259 bytesで完了し、[receipt](data_portable_bar_2026-10-19/mixed-c0t2-final-transfer-v1/receipt.json) に転送後の全hash照合を保存した。
同じ配置先・記録先へ再実行しない。
最終wrapperには元venvの入口と実prefix・binaryを明示的に固定する [別wrapper](portable_mixed_venv_binding_spec_2026-10-20_ja.md) を使用する。
実配置先は `/home/user/workspace/mcmc4qec/20261020-portable-mixed-venv-controls-v2/portable_mixed_venv_qsub_v1.py` である。
最終configは [実prepare/preflight記録](data_portable_bar_2026-10-19/mixed-c0t2-final-config-v2/accepted.json) に保存し、156 source・136 metadataを照合した。
job rootは `/home/user/workspace/mcmc4qec/20261020-portable-mixed-c0t2-final-v1`、config SHA-256は `4aa2210aafc1d0f25c987da488516f57f110bfe16413a2bf9a980999fbacf8b9` である。
prepareとdry-runは使用済みで、script SHA-256は `76f04966f311e52fdc4b6403069d63c2dc2bda30a1af00c0334aa250d0bfa81e` である。
投入監視はlocal PID30804で起動しており、復旧collectorのqsub受理後に待機中を含む2ノード制約を検査する。
監視の実行中に同じjobを手動投入せず、`mixed-c0t2-final-slot-handoff-v1/` のintent・実qstat・submitted/errorの有無を先に確認する。
実終端F・exit 0・run_count 1の後は、上記新wrapperのcompleteを元venv入口で一度だけ実行する。
回収には `output/portable_mixed_venv_final_collection_v1.py` を用い、実config SHAとcompleteが作成したterminal.jsonの実SHAを外部指定する。
旧 `portable_mixed_final_collection_v1.py` は旧wrapperへ固定されているので、このjobへは使わない。
新回収入口はWindows26 passed・24.32秒、Linux26 passed・14.26秒と、実prepared configの読取を通過した。
最初のWindows試験は生成sourceのCRLFと自己転送時のLFの差を検出したため、元bytesを保持してLFへ統一し、再試験した。
本番reportの完成・complete・回収は未実施である。
以下の古い段階説明は使用済み状況をこの節で上書きして参照し、一括実行しない。

## 使用済みの実行と現在の所有者

samplingはanchor 265337、sample0 265338、sample1 265339の正常終端を確認済みである。
sampling collector 265345は正常終了・受理済みであり、prepare・preflight・execute・completeを再実行しない。
collector prepared SHA-256は `2219cd0e4fd652955510c03019566ac548abf8ea0392e685d0e34467d9d5d76c` である。
trace capacity 265346も正常終了し、prepare・preflight・executeは使用済みである。
capacity prepared SHA-256は `5ba3212b940a40843e738852a54b5214a8c6ffba7d28a2847034e931716bf2c5` である。
capacity completeの初回SSH接続失敗と、失敗記録を保持した一回の受理回復は [回復記録](trace_capacity_transport_recovery_2026-10-20_ja.md) に従い、以下のcompleteを重複実行しない。
full監査のprepareも使用済みであり、prepared SHA-256は `20d8d409972a29b037ee11f33c6200b6516c21a7093526fce8aea8a1b6de12be` である。
full preflightの通信失敗、別記録による読み取り専用の再観測成功、keepalive付きexecuteの開始は [投入記録](low_c0t2_trace_full_dispatch_2026-10-20_ja.md) を参照し、以下のpreflight・executeを新たに重複実行しない。
full監査のexecuteはjob 265348として正常に受け付け済みであり、現在はその終端を待つ段階である。
DGXの再割当てdriver `portable_bar_reassigned_pipeline_v1.py --first 0 --last 13` は起動済みで、既存DGX batch 17の回収準備・回収と、新14 batchの配置・起動・回収を担当する。
2026-10-20 12:32 JST時点でDGX batch 17と再割当てbatch 0〜4の正常終端・回収照合は完了し、再割当てbatch 5が実PID 1380616で稼働している。
同じbatchに対して別のprepare・collect・起動を並行実行しない。
Laboはbatch 3まで回収済みであり、batch 4が実PID 6360で稼働し、既存の `portable_bar_later_handoff_v1.py labo 5` がbatch 4の終端を待っている。
この引継ぎはbatch 4の回収・受理、batch 5の起動、起動したSSHの終端待ちを担当するが、batch 5自身の回収は行わない。
Labo batch 6以降を旧規則で新規予約しない。
台帳・現在の実PID・実qstatを確認し、既存記録のある操作は繰り返さない。

## sampling collectorと元環境trace監査

以下は各段階が未使用の場合に限る手順であり、文書を上から一括実行しない。
collectorの実qstatでF・Exit_status 0・run_count 1を確認してから、次を一度だけ行う。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
$collectorPin = '2219cd0e4fd652955510c03019566ac548abf8ea0392e685d0e34467d9d5d76c'
& $taskPython output/complete_low_partition_collection_once.py --case 0 --target-index 2 --prepared-sha256 $collectorPin
& $taskPython output/prepare_low_partition_trace_once.py --case 0 --target-index 2 --collector-prepared-sha256 $collectorPin
```

後者の成功receipt `low_partition_trace_capacity_0_2_prepare_once_v1_receipt.json` の `response.prepared_sha256` がtrace capacityの実prepared SHAである。
receiptのacceptedと実stdout・source hashを確認してその値を `$traceCapacityPin` に設定し、次を順に行う。
未取得のSHAを仮値で補わない。

```powershell
& $taskPython output/submit_low_partition_trace_once.py --case 0 --target-index 2 --collector-prepared-sha256 $collectorPin --prepared-sha256 $traceCapacityPin --action preflight
```

待機中を含む全既存要求に1ノードを追加しても合計2以下であることと、preflight成功を確認した後にだけexecuteする。
入口自身も共有lockと投入直前のnode数を再検査する。

```powershell
& $taskPython output/submit_low_partition_trace_once.py --case 0 --target-index 2 --collector-prepared-sha256 $collectorPin --prepared-sha256 $traceCapacityPin --action execute
```

実jobの正常終端を確認してから次のcompleteとfull監査prepareを行う。

```powershell
& $taskPython output/complete_low_partition_trace_once.py --case 0 --target-index 2 --collector-prepared-sha256 $collectorPin --prepared-sha256 $traceCapacityPin
& $taskPython output/prepare_low_partition_trace_full_once.py --case 0 --target-index 2 --collector-prepared-sha256 $collectorPin --capacity-prepared-sha256 $traceCapacityPin
```

full prepareの成功receipt `low_partition_trace_full_0_2_prepare_once_v1_receipt.json` から実prepared SHAを `$traceFullPin` に取得する。
`submit_low_partition_trace_full_once.py` に同じcase・target・collector・capacity引数と `--prepared-sha256 $traceFullPin` を渡し、preflight、実node空き確認、executeの順に行う。
正常終端後は同じ引数で `complete_low_partition_trace_full_once.py` を一度だけ実行する。
full監査rootは `/home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/runs/partitioned-trace-full-0-2-v1` である。
completeはmetadataの終端受理であり、最終readerが行う現在の全payload検査を省略しない。

## 全群の回収と転送

### Laboの最終batch 5

batch 4の回収とbatch 5の起動は既存引継ぎに任せ、別のcontrollerを起動しない。
batch 5の実起動後、`labo-batch5-start-intent-v1.json`、`labo-batch5-handle-v1.json` とremoteの `result/execution-intent.json` が揃ったことを確認する。
次のprepareは未使用の場合に一度だけ実行し、実起動の環境・source・group censusへ回収を結ぶ。
使用済みのparent・preparationがある場合は再実行せず、その内容と実remoteを照合する。

```powershell
& $taskPython -B output/prepare_portable_bar_later_collection_v1.py labo 5
```

保存先は `docs/wp/data_portable_bar_2026-10-19/labo-batch5-collection-preparation-v1.json` である。
実processと `completion.json` を観測し、観測timeoutを正常終端や再起動の根拠にしない。
terminalがある場合はexecution intentとの結合と成功内容を確認し、未回収の場合に次を一度だけ実行する。

```powershell
& $taskPython -B output/collect_portable_bar_later_once_v1.py labo 5
```

既存のcollection execution intentがありtransfer verificationがない場合は、同じcollectを再実行せず、保存ログと実remote archiveから回復可能性を確認する。
成功時は `labo-batch5-collection-v1/transfer-verification.json` の `transfer_verified`・`batch_accepted`、予定24群、infrastructure failure 0、実行intentとarchiveのbindingを照合する。
この成功後もDGX側の残群と元環境trace監査が完了するまでは最終評価に進まない。
Labo batch 6への引継ぎを作成しない。
この節のprepare・collectは2026-10-20 12:34 JST時点では未実施である。

### 混在全768群

混在形式用の `index_portable_mixed_collected_v1.py --snapshot-name new_snapshot_name.json` で未使用名のsnapshotを作る。
snapshot作成は全回収の宣言ではなく、`all_groups_terminal=true`、terminal_groups=768、pending_groups=0、planned_rows=67584を確認する。
infrastructure failure、未定義診断、flag、区間未取得を予定行数の分母から除外しない。
両hostのparityと全archiveを含むsnapshotの固定SHAを渡し、新しいoutput directoryへ転送contextを作る。

```powershell
& $taskPython output/portable_bar_mixed_distribution_v1.py --inventory $inventoryPath --inventory-sha256 $inventoryPin --output $newContextDirectory
```

この入口は未回収が残れば出力先を作らず拒否する。
contextの出力先は未使用の `output/` 配下directoryでなければならない。
成功したtransfer-plan.jsonの実SHAを固定し、未使用のクラスタ直下directoryとlocal記録directoryを指定して転送する。

```powershell
& $taskPython output/portable_bar_mixed_transfer_v1.py --plan $transferPlanPath --plan-sha256 $transferPlanPin --destination $newClusterDirectory --record-dir $newTransferRecordDirectory --execute
```

転送receipt、全file census、source/assignment/context hash、remoteのtransfer-complete.jsonを照合する。
失敗時は部分配置とintentを保持し、同じ配置先・record directoryへ自動再実行しない。

## 最終qsub

最終readerと制御sourceの配置先は `/home/user/workspace/mcmc4qec/20261020-portable-mixed-controls-v1/output` である。
配置済みsource manifestは `3c92eede73d4a65a5d59f0081a72590ee05b713a8f1aef3972d69f626e1d6e86` であり、実使用前にsourceと外部依存のhashを再確認する。
本番configはまだ作成しておらず、全入力の実資料が揃ってから次の項目を固定する。

| config項目 | 必要な実資料 |
|---|---|
| inputs | sampling root、上記full audit root、転送済みportable root、既存WSS reference root |
| source_roots / source_sha256 | helper・cluster_scripts・mcmc4qecの実source rootと全Python file census/hash |
| metadata_sha256 | context・transfer完了、plan/baseline、全38 parent、監査summary、sampling/audit/reference manifestを含む実metadata |
| wrapper / python | `portable_bar_mixed_qsub_v1.py` と元クラスタPythonの実path/hash |
| resource / resource_reason / resource_evidence | 1 CPU、実測を根拠に選ぶmemoryとwalltime、根拠ファイルのhash |

資源は [別記録](portable_bar_mixed_final_resource_2026-10-20_ja.md) により1 CPU・32 GB・4時間を選び、根拠を `/home/user/workspace/mcmc4qec/20261020-portable-mixed-resource-v1` へ配置済みである。
科学比較用のWSS reference rootは `/home/user/workspace/mcmc4qec/20261018-tile-weight-reference-v4/runs/reference` であり、既存reference bindingが記録したこの実pathを、最終readerで改めて検査する。

configのpurposeは `portable_bar_mixed_final_pbs`、portable contextのschemaは2である。
portable側のreference archiveはparity用であり、inputs.referenceの科学比較用WSS rootと混同しない。
wrapperのprepareは全38 batch・全768群・固定plan・成功した元環境監査を検査するが、最終科学検査の代替ではない。
クラスタ上でconfigを固定し、新規job rootに対してwrapperのprepare、submitのdry run、実node空き確認、submit --executeの順に進める。
submit --executeはqsubを使い、待機中を含む上限2ノードと共有lockを適用する。
実jobのF・Exit_status 0・run_count 1、script・resource・job IDの一致を確認してからwrapperのcompleteを行う。
曖昧なqsub応答時は再投入せず、保存intentと実qstatを照合する。
完了reportはterminalが固定したSHAで回収し、全67,584行と失敗・未定義・未取得を含む集計、独立reference照合、provenanceを確認して日本語報告に反映する。
この回収には [検証済みの最終report回収helper](portable_mixed_final_collection_acceptance_2026-10-20_ja.md) を用い、実configとterminalのhashを外部指定して転送前後・localのbytesを照合する。
回収済みreportからの記述用抽出には [欠測を保持する要約入口](low_noise_report_summary_acceptance_2026-10-20_ja.md) を使い、正常終端・回収で確認した実report hashを渡す。
本番全群context、最終config、最終qsubとreport回収はこの文書作成時点では未実施である。
