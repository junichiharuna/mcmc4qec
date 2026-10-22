# 分割した低ノイズ設定選択：読み込み・結合中核の受入結果

[小仕様](low_timing_partition_values_spec_2026-10-22_ja.md)、受入テスト、実装の順で、条件単位の既存reader呼出しと全24行への結合処理を追加した。
公開パッケージ、稼働中controller、既存selector、固定実験入力は変更していない。
中核は `output/low_timing_partition_values_v1/values.py` にあり、保存版も下記の受入資料に含める。

## 検証した範囲

Windows Python 3.11で33 passed・16.35秒、保存版からの再実行で33 passed・17.31秒だった。
全12条件・各352設定の人工metadataについて、既存の実 `choose` 関数と実reference幅・精度評価を用いた。
固定192件の人工推定値に対して算出した評価値を各設定へ割り当て、計画済み設定の全数と順位を保持した。
実traceを読む `load_complete` とsource closure探索はテスト用doubleに置き換え、file hashとresolved pathの照合は実ファイルで行った。
単一selector経路と分割・結合経路で、24行と12件のbindingの全値一致を確認した。
referenceなし、reference幅不適格、選択成功、精度未達を含み、診断未定義と区間未取得の記録を保持した。
担当外の条件を読まず、読込異常を不適格な結果へ変換せず停止することを確認した。
条件・worker・設定の欠落や重複、分母違い、parent設定違い、source変更、入力変更、resolved path変更、結合終了時の入力変更を拒否した。
同じPBS job IDを複数workerへ割り当てた結果、PBS環境なし、single-thread環境違いも拒否した。

## 保存と再現

[受入資料](data_tile_validation_2026-10-17/low_timing_partition_values_acceptance_v1/accepted.json)に中核source、テスト、実装前の失敗log、依存source 53本、platform profileとfixture、依存版、core source hashを保存した。
受入記録のSHA256は `4dcb6673ef5e0f75c1ee0df9d1a8a06daed10e9f240d3bda13f4d61945f44490` である。
保存版の初回実行では相対位置から読むplatform fixtureが不足し、その失敗logを保持したまま必要な2ファイルを追加した。
追加後の成功logは `saved_source_tests_with_platform.txt` である。
repository rootから次のコマンドで保存版を再実行できる。

```powershell
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" -B -m pytest docs/wp/data_tile_validation_2026-10-17/low_timing_partition_values_acceptance_v1/test_values.py -q -p no:cacheprovider
```

## 未完了の接続

実PBS台帳・正常終了・script・native環境をまとめて検証する新しいenvelope、worker入力作成、結合ジョブの資源見積り、qsub投入、後続censusへの接続は未完了である。
今回の中核はPBS_JOBIDの形式とthread環境を検査するが、実schedulerに照会して実行を認定するものではない。
実データ全12条件による再読込と設定選択も未実施である。
結合結果は既存の正式selector結果と別のpurposeを使い、`production_selection_validated=False` と `worker_execution_evidence_validated=False` を返す。
この中間結果を既存の正式結果へ読み替えず、PBS証跡を検証する接続を完成させてから後続へ渡す。
今回の受入は科学的な混合・被覆・速度の追加認定ではなく、低ノイズの正式完了数は9/12条件のままである。
