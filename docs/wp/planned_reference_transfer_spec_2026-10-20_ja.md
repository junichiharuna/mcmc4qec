# 次条件のnative reference回収

対象はC1T1/C1T2/C3T0/C3T1/C3T2のprepare済みnative referenceとする。
固定済みprepare receiptのconfig・script・resourceと、外部hash付きの実qsub応答を照合する。
実qsub応答は既存reference controllerのsubmit戻り値そのものを保存し、preflightやcapacity_unavailableを投入成功として扱わない。
条件、保存root、config、script、資源、job IDのいずれかが違う場合は回収しない。
実qstatでF・exit 0・run_count 1とscript・資源・ownerを確認してから、既存controllerのcompleteを一度だけ実行する。
5つの成果物を転送し、archive全memberと元metadata・選択群・task markerを既存readerで検査する。
転送後に元ファイルのhashを再取得し、転送中の変更を拒否する。
既存C1T0のcollectorとその受理記録は変更しない。
referenceの受理は全cohortの科学検証やPC parityの受理ではない。
受入は5条件の正しい投入binding、条件・script・資源の取り違え、未投入応答、再実行・異常終端を含む。

## 実施結果

`output/planned_reference_transfer_v1/collect.py` を既存C1T0用collectorから派生し、条件選択と外部pin付きの実submit応答を受け取る入口にした。
既存controllerの実byte hashを確認してからcompleteを呼び、archive検査・転送後の再hash・一度限りの保存先を維持する。
派生元のhashと置換記録は同directoryの `derive.py`・`derivation.json` に保存した。
Windows31件・0.66秒、Linux31件・0.13秒で受入が成功し、CLIのimportと `--help` 起動も両環境で確認した。
結合試験は5条件の実prepare済みconfigを読み、合成PBS・転送・archive readerを使用している。
本番のarchive payload検査や本番completeの成功を示す試験ではない。
本番のreference投入・complete・回収は未実施であり、初回PC parityの新条件接続も未完了である。
[source・固定config・ログを含む24ファイルのmanifest](data_tile_validation_2026-10-17/planned_reference_transfer_acceptance_v1/manifest.json)のSHA-256は `1ff80c18429202c4452b5161311b64033a0171e86b97dd0f46ef678ae75e8168` である。

## 実行入口

既存reference controllerの `submit --execute` による実際の戻り値をJSONとして保存し、そのSHA-256を指定する。
予約状態やpreflightの結果を実投入の代わりに指定しない。
controllerは共有lockとQを含む最大2ノードを検査してqsubするため、並行driverの使用枠を確認してから投入する。
以下の `SUBMISSION_JSON` と `SUBMISSION_SHA256` は実投入後に得た値で置換する。

```powershell
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_reference_transfer_v1/collect.py --condition c1t1 --submission SUBMISSION_JSON --submission-sha256 SUBMISSION_SHA256
```

Q/R等の正常な非終端状態では `completion_attempted=false` を返し、保存先を予約しない。
completeを開始した後の失敗ではintentと応答を保持し、同じ操作を自動再試行しない。
