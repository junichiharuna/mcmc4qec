# C3T1 collectorの投入前node gate停止からの再接続

sampling265438は実PBSでF・exit 0・run_count 1を確認し、実walltimeは8時間00分20秒だった。
後続collectorはlocalの空き確認後、remoteの共有lock下の2node gateで停止した。
保存応答のreturncodeは1、stderrは `two-node budget exceeded including queued jobs` であり、qsub応答やjob IDは返っていない。
21:24以降の実照会ではC3T2 sampling265448がRで、ownerの非終端jobは1件だった。

実remoteのcollector保存先にはdry-runとscriptだけがあり、submission intent・台帳・worker開始・完了・terminal・collection出力は存在しないことを確認した。
観測timeoutから再投入を判断したものではなく、投入前のgate拒否と未実行状態の照合に基づく。
旧local controllerのerror・intent・応答は残し、元のsource・符号・seed・prior・sampling入力は変更しない。

新しい保存先で同じ固定collector・監査configを使い、既存の収集・capacity監査・full監査の順序と共有lock・最大2nodeを維持する。
新controllerは開始直前にremoteの未投入状態を再照会し、過去のerror種類・単発投入失敗応答・後続未実行を検証する。
それ以外のerror、投入台帳、部分出力があれば実行せず、正常な再試行とみなさない。
元の失敗を監査完了へ置き換えず、完了後の結果を下流へ接続する処理は別に行う。

受入では投入前node gate以外の失敗、remote台帳・出力、後続実行記録を拒否する。
実qsub投入と新しいjobの稼働確認は実行後に記録する。

## 21:35 JSTの投入・稼働確認

guardの6 testは2.33秒で成功し、保存sourceからの再実行も6 passed・15.46秒だった。
[受入資料](data_tile_validation_2026-10-17/c3t1_collection_slot_resume_acceptance_v1/)のmanifest SHA256は `381ac62f74efb7cb5cb164fd75d9a57f20bff9d3c9d2a766e3124d6c6692d81d` である。
元のaudit controllerが実稼働していないことを確認し、新controller PID39268をhiddenで起動した。
開始時にremoteの未投入状態を再照合し、旧sourceと失敗記録を保持した。
既存の固定worker経由でqsubを実行し、collector job `265457` のR・run_count 1を確認した。
要求は1 CPU・32 GB・1node・8時間枠であり、この枠は実測完了時間の保証ではない。
C3T2 sampling265448もRで、要求node合計は2だった。
[投入と実稼働の記録](data_tile_validation_2026-10-17/c3t1_collection_slot_actual_start_20261022_v1.json)を保存し、local投入receiptのSHA256は `5c6f9b7b4682d7b67ce4b1dcd239c966c19e7e5cdc46b9c3d86ed3cb1598ab2d` である。
新controllerはcollector正常終了後にcapacity監査・full監査へ進むが、これらはまだ完了していない。
C3T1 native経路とC3T2 generatorは旧auditの停止信号で停止しており、新auditへの下流再接続が残っている。
C3T2 sampling265448自体は引き続き実行中であり、generatorの停止をsamplingジョブの終了とみなさない。

## 21:43〜21:44 JSTの訂正

上記の「C3T1 native経路が停止している」という記載は誤りだった。
native job265455は正常終了し、21:11:08にreference_ready=trueの完了記録とaccepted.jsonを回収済みである。
DGXとlaboも既存経路からC3T1 batch0を開始し、実PID1010955・7540の稼働を確認した。
nativeとPC計算の再起動は不要であり、停止したC3T2 generatorと監査後の集約経路を再接続する。
collector265457とsampling265448は引き続きRで、合計2要求nodeを維持している。
