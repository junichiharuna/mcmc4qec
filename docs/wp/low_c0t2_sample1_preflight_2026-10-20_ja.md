# C0T2 sampling後半分割の事前確認

既存の固定実行手順を使い、C0T2のsample partition 1のpreflightを実施した。
対象はreplicate 96～191の92160 taskであり、実行中のpartition 0（replicate 0～95）とは重複しない。
元のseed、192 anchor、kernel、ladder、trace長は変更していない。

要求は1 node・96 CPU／worker・32 GiB・walltime 17時間30分で、最大2ノードの制限を維持する。
元production manifestは `8093838b22f74cad6ed113b5af8c185034b2585cfc4d0d7b374f150d9654b396` である。
固定PBS scriptのSHA-256は `bd52d95b8b4d8088231b4616cda2985f41ad4ba526d6f78527c99710193ac115` である。

事前確認はreturncode 0・ambiguous falseで終了し、source・Python binary・native binary・platform probe・未使用の出力先を確認した。
観測時は2ノード使用中で `slot_available=false`、`qsub_executed=false` だった。
preflight成功は将来の空き枠の保証ではなく、execute時にも共有lockと実PBSの要求ノード数を再確認する。
receiptのSHA-256は `38f4c5951ad0cafa56dc2c154307be8c2c4c57319eb8778422273c67cf4efe9b` である。
記録は [preflight receipt](data_tile_validation_2026-10-17/low_partition_0_2_sample_1_preflight_once_v1_receipt.json) と同名のintent・script・stdout・stderrに保存した。

実施済みの入口は次の通りであり、同じpreflightを再実行しない。

```powershell
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' output/submit_low_partition_once.py --case 0 --target-index 2 --phase sample --index 1 --preflight
```

空き枠と他の完了処理・回復処理の順序を確認した後の投入入口は次の通りであり、まだ実施していない。

```powershell
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' output/submit_low_partition_once.py --case 0 --target-index 2 --phase sample --index 1 --execute
```

この入口はqsubを一度だけ呼び、待機中jobも含めた要求ノード数が2を超える場合は拒否する。
既存intent・ledgerがある場合や応答が曖昧な場合は再投入せず、実PBS状態と保存証拠を確認する。
