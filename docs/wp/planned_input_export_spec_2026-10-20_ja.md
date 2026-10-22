# 残る5条件の入力export

C1T1/C1T2/C3T0/C3T1/C3T2の固定割当てを入力とし、既存のraw exporterとarchive readerを変更せず使う。
各条件の事前固定したpartition preparation、native reference config、割当てのhashを照合する。
実投入receiptはpathと外部SHA-256を明示したregistryで受け取り、anchor 0・sample 0・sample 1の3件が揃うことを要求する。
receiptの条件・partition・qsub script・資源・script hash・partition manifestを事前準備と照合し、重複job、未投入preflight、曖昧応答は拒否する。
元クラスタで3件の実qstatを取得し、owner・script・資源・F・exit 0・run_count 1を確認する。
実scriptとpartition manifestのbyte hashをexport前後に照合する。
1件でも実行中、失敗、欠落、整合性不明ならexportを実行しない。
全terminalの証跡をexportと一緒に保存する。
元source・metadata・選択群のartifactとmarker・archive全memberの既存検査を維持し、未選択群を混入させない。
操作は新規保存先への一度限りとし、自動再試行・qsub・数値worker起動は行わない。
受入では正常な3件、欠落・重複・条件違い・preflight・script/hash/resource違い・実行中・異常終端・再実行を検査する。
合成受入と実metadata preflightは本番入力export・数値parityとは区別する。

## 実施結果と再現

既存C1T0用adapterから、対象config・割当ての選択と3件の終端検査を変更した別adapterを作成した。
raw exporterとarchive検査は維持し、派生scriptの置換箇所と回数を `output/planned_input_export_v1/derive.py` に明記した。
実際のremote処理を合成PBS・小さいexporterで実行する試験を含め、Windows38件・0.62秒、Linux38件・0.12秒で成功した。
[受入ログ](data_tile_validation_2026-10-17/planned_input_export_acceptance_v1/accepted.json)は本番入力・本番terminalの検査成功を意味しない。
C1T1の実3投入receiptは[外部hash付きregistry](data_tile_validation_2026-10-17/planned_input_export_c1t1_registry_v1/registry.json)へ固定し、元preparation・partition manifest・config・割当てとのローカル照合を通過した。
registry SHA-256は `c733894d2b686050e9b48ba2ea085f951f7aba28be279865f33486beb454d81f` である。
本番exportは未実施であり、sample 1の正常終了後に以下を一度ずつ実行する。
preflightも実3ジョブの正常終端を要求し、未完了時に先行実行して自動再試行する用途には使わない。

```powershell
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_input_export_v1/export.py dgx 0 --condition c1t1 --registry 'A:/dev/mcmc4qec/docs/wp/data_tile_validation_2026-10-17/planned_input_export_c1t1_registry_v1/registry.json' --registry-sha256 c733894d2b686050e9b48ba2ea085f951f7aba28be279865f33486beb454d81f --preflight
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_input_export_v1/export.py dgx 0 --condition c1t1 --registry 'A:/dev/mcmc4qec/docs/wp/data_tile_validation_2026-10-17/planned_input_export_c1t1_registry_v1/registry.json' --registry-sha256 c733894d2b686050e9b48ba2ea085f951f7aba28be279865f33486beb454d81f
```

Laboおよび後続batchは固定割当てのhost・sequenceを明示し、他4条件は実qsub後のreceiptを同じ形式で外部pinする。
native reference計算、各PCへの配置とparity、worker起動は別途必要であり、このexport adapterが自動で実施する範囲には含まれない。
