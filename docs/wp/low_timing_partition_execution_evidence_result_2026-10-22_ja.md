# 分割workerのPBS証跡：検証関数の受入結果

[小仕様](low_timing_partition_execution_evidence_spec_2026-10-22_ja.md)、受入テスト、実装の順で保存済みworker証跡を読む検証関数を追加した。
本番runnerや既存controllerには接続せず、実ジョブの証跡受入や新規投入は行っていない。

人工証跡による30 testがWindows Python 3.11で4.02秒、保存sourceからの再実行が4.98秒で成功した。
全12条件manifestと資源計画、担当worker、外部prepared・環境pin、qsub intentと台帳、script全内容、開始・終了直前・終了後のPBS記録、開始と完了の記録、値ファイルを結合した。
同じPBS job ID・run_count 1・host・要求資源・scriptを要求し、終了後の状態はFと整数exit 0を必要とする。
終了コードのbool値、重複したselect指定、要求資源やhostの変更、曖昧なjob ID、未終了、script変更を拒否した。
外側の値ファイルhashを更新しても、worker indexやresolved pathの不一致を拒否することを確認した。
担当外を含む全体割当の欠落、native bindingの変更、相対証跡path、検証終了時の入力変更も拒否した。

[受入資料](data_tile_validation_2026-10-17/low_timing_partition_execution_evidence_acceptance_v1/accepted.json)にsource、テスト、実装前の失敗log、成功log、Python版を保存した。
受入記録のSHA256は `aaf3c5e49c05239eafee823c1569db0381a4dbdca854593eb4a8b4f6118e57eb` である。
[保存版の再実行記録](data_tile_validation_2026-10-17/low_timing_partition_execution_evidence_acceptance_v1/saved_source_replay.json)のSHA256は `f492207fb0b163353a0aef4adf606f4ae6d31a50b0512493ff3fc3759044f851` である。
repository rootから次のコマンドで再実行できる。

```powershell
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" -B -m pytest docs/wp/data_tile_validation_2026-10-17/low_timing_partition_execution_evidence_acceptance_v1/test_evidence.py -q -p no:cacheprovider
```

これらのtestでは保存した人工PBS記録を使い、実schedulerへの照会、実Python実行環境の起動、native probe、科学的な再計算を行っていない。
検証関数自体にもnetwork接続・ファイル書込・qsub呼出しはない。
`worker_envelope_accepted` は渡された保存証跡の結合結果であり、単独では行の算術・全体結合・後続censusを認定しない。
`production_selection_validated=False` と `fresh_native_probe_claimed=False` を維持する。

本番runnerの事前検査と実PBS照会、入力作成、投入lockと最大2node制御、結合ジョブ資源の算定、後続censusとの接続は未完了である。
実metadata全12件による本番経路の実行も未実施であり、低ノイズの正式完了数は9/12条件のままである。
