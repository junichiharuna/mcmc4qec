# 低ノイズ計時前処理：分割資源計画器の受入結果

[小仕様](low_timing_partition_plan_spec_2026-10-22_ja.md)、受入テスト、実装の順に、全12条件のmetadataから資源割当を作る計画器を追加した。
実行中のcontroller、既存assembly、固定入力は変更していない。
これは[分割方針案](low_timing_partition_contingency_2026-10-22_ja.md)の資源計画部分であり、worker・結合・後続計時の実行経路は未実装である。

Windows Python 3.11の受入テストは27 passed・0.82秒だった。
保存sourceからの再実行も27 passed・2.81秒だった。
単一ジョブで収まる例では、費用明細・hash allowance・collectionの扱い・資源・説明文を含む判定全体が既存assemblyと一致した。
単一ジョブの上限を超える固定例では、全12条件を順序を保つ3ジョブへ4条件ずつ割り当て、各要求時間16時間50分、memory 32 GBとなった。
これは小さい人工入力に基づく動作確認であり、実データの資源判定や所要時間予測ではない。
一条件だけで24時間・340 GBの境界に一致する例を受理し、時間が境界を超える例を拒否した。
12ジョブを必要とする例も全条件を保持し、同時要求node上限2の指定を維持した。
欠落、重複、順序違い、pin不一致、不正費用、単一条件の資源超過は拒否した。

source、既存assemblyのコピー、既存fixtureのコピー、テスト、実装前の失敗log、成功logを[受入資料](data_tile_validation_2026-10-17/low_timing_partition_plan_acceptance_v1/accepted.json)に保存した。
受入記録のSHA256は `0bfab0fa71e54fd2576361de7b04af01b3494a29b8f781b49bc597df765bb403` である。
repository rootから次のコマンドで保存sourceの受入テストを再実行できる。

```powershell
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" -B -m pytest docs/wp/data_tile_validation_2026-10-17/low_timing_partition_plan_acceptance_v1/test_partition.py -q -p no:cacheprovider
```

全12条件の実metadataはまだ揃っておらず、本番計画の作成・qsub投入・raw reader実行・設定選択は未実施である。
結合時の全入力再照合費用、実PBSとsourceの結合、全24出力の検証、後続censusとの接続も未完了である。
出力には `execution_ready=False` と未評価の結合資源を明記し、計画器の受入を分割実行全体の受入として扱わない。
