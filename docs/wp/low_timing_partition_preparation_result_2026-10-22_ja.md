# 分割worker入力準備の受入結果

[小仕様](low_timing_partition_preparation_spec_2026-10-22_ja.md)、受入テスト、実装の順で、全12条件からworker入力を構築・保存する処理を追加した。
既存controllerへの接続、実metadata全12件による準備、qsub投入は行っていない。

Windows Python 3.11で16 testが3.29秒、保存sourceからの再実行が4.76秒で成功した。
全12条件の人工metadataから3workerを構築し、元entryの科学的な内容を保持したまま、isolated readerの環境・parent・directoryを対応するworkerへ結び付けることを確認した。
全体manifest、資源計画、候補、prepared、scriptのhash関係と、workerごとの重複しない出力rootを検査した。
単一ジョブで収まる場合は既存経路を維持し、新たな成果物を作らない。
条件不足・重複・順序違い・reference違い・環境不足・helper pin不一致・出力重複と、事前検査の失敗を拒否した。
保存途中で入力が変わった場合には途中成果物を保持し、準備完了receiptを作らず再実行を拒否した。

準備処理のテストではnative bootstrap、isolated template検査、実費用検査を明示したdoubleに置き換えた。
それらを実cluster入力で通したという意味ではなく、資源計画器・script生成・file hashと保存の境界を接続した受入である。
実装は実保存前に元のbootstrapとtemplate検査、共通reference audit、runnerの実費用検査を呼び、保存後にも入力とsourceを再確認する。
qsub・sampling・raw trace readerは呼ばず、投入intentや台帳を作らない。
worker入力を準備しても全体の `execution_ready` はfalseのままである。

[受入資料](data_tile_validation_2026-10-17/low_timing_partition_preparation_acceptance_v1/accepted.json)にsource、依存source、テスト、実装前の失敗log、保存版成功log、Python版を保存した。
受入記録のSHA256は `9d6f1f9c81d72920e56c8ea42557700180fdd34d440c41ad05f2e93df836167f` である。
repository rootから次のコマンドで再実行できる。

```powershell
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" -B -m pytest docs/wp/data_tile_validation_2026-10-17/low_timing_partition_preparation_acceptance_v1/test_preparation.py -q -p no:cacheprovider
```

18:17 JSTの既存inventoryの実読込ではmetadataは9/12条件で、C3T0・C3T1・C3T2がpendingだった。
部分集合や推測費用で本番入力は作成していない。
全条件の資源判定、実入力作成、共有lock下の投入、結合ジョブと後続censusへの接続は未完了であり、低ノイズの正式完了数は9/12条件のままである。
