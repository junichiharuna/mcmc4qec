# 次条件へのPC初回parity引継ぎ

各hostの条件順はC1T0 → C1T1 → C1T2 → C3T0 → C3T1 → C3T2とする。
新条件のnative reference受理記録と、前条件の当該hostの最終batch回収記録を外部hash付きregistryで指定する。
前条件のassignmentは事前固定manifestで認証し、そのhostの最終batchとの一致、正常な回収、archive全member、parentと実行終端の対応を確認する。
途中batch、別host、別条件、未完了・context失敗・基盤失敗の回収は引継ぎに使わない。
新条件のnative referenceと最初の入力batchが同じ条件・元manifestに属することを確認する。
PC上では元のexecution lock・runtime・前ジョブの実終端・稼働中process検査を保持し、既存の全88設定parityを一度だけ実行する。
同じhost上で保存結果を再検査して受理し、固定workerへの入力を返す。
parityは同じ保存traceに対する実装・環境間の整合性検査であり、混合・被覆・全cohortの精度保証ではない。
受入では5条件×2hostの前後関係と最終batch、別host・途中batch・異常回収・native条件の取り違えを検査し、remote parity処理の変更がないことを確認する。

## 実施結果と入力

`output/planned_pc_parity_v1/parity.py` と `handoff.py` に実装し、元C1T0用transportからの置換を `derive.py`・`derivation.json` に保存した。
Windows25件・1.08秒、Linux25件・0.50秒の受入とCLI起動確認を通過した。
registry結合試験はarchive readerを合成データで置き換えており、本番前条件のarchive検査や実parity計算を行った証拠ではない。
remoteのparity実行と保存結果の再検査の本文が元版と一致することも確認した。
[31ファイルのsource・固定割当て・ログ](data_tile_validation_2026-10-17/planned_pc_parity_acceptance_v1/manifest.json)のmanifest SHA-256は `32330ccfd68b72ebc72c7bdd18e6d57c3175a840b1ef802609cf51e0448b1613` である。

registryは次のfieldを持つJSONとし、nativeは新条件のcollectorが保存した `accepted.json` を指定する。
transfer・parent・archiveは前条件の当該hostの最終batchに属する `transfer-verification.json`・`parent.json`・`outputs.zip` を指定する。
各file entryは絶対pathと実測SHA-256の対 `{ "path": "...", "sha256": "..." }` とする。
このregistry自体にも外部SHA-256を付ける。

```json
{
  "schema": 1,
  "condition": "c1t1",
  "host": "dgx",
  "native": {"path": "ABSOLUTE_NATIVE_ACCEPTED_JSON", "sha256": "ACTUAL_SHA256"},
  "transfer": {"path": "ABSOLUTE_PREVIOUS_TRANSFER_JSON", "sha256": "ACTUAL_SHA256"},
  "parent": {"path": "ABSOLUTE_PREVIOUS_PARENT_JSON", "sha256": "ACTUAL_SHA256"},
  "archive": {"path": "ABSOLUTE_PREVIOUS_OUTPUT_ZIP", "sha256": "ACTUAL_SHA256"}
}
```

実入力が揃った後に `parity.py HOST --condition CONDITION --registry REGISTRY_JSON --registry-sha256 REGISTRY_SHA256` を一度だけ実行する。
現在のC1T0ではDGX batch31・Labo batch5の正常回収を待ち、途中batchの結果で代替しない。
当該5条件の本番registry作成・初回parityは未実施である。
