# 分割workerの実行runner：受入と環境確認

[小仕様](low_timing_partition_runner_spec_2026-10-22_ja.md)、受入テスト、実装の順で `run-worker` と `capture-terminal` を追加した。
runner自身にqsub投入機能はなく、既存の稼働sourceやcontrollerは変更していない。

## ローカル受入

Windows Python 3.11で制御15件・費用確認13件の計28 testが3.60秒、保存版からの再実行が4.68秒で成功した。
制御テストはnative bootstrapとraw readerを明示したdoubleに置き換え、人工PBS記録を使った。
開始、完了、R状態での待機結果、F状態の保存、先に実装した保存証跡検証関数までを接続した。
実行前・実行中の入力やnative fileの変更、PBS割当変更、reader失敗、費用検証失敗で完了記録を作らず、例外記録を保持して再実行を拒否した。
既存出力の上書きを拒否し、終了コード非ゼロのPBS記録を保存して受理済みdescriptorを作らないことも確認した。
費用確認テストではisolated最終reader、collection内包、独立collection、staged copyを含む既定式と、費用・pin・scopeの不一致を検査した。
isolated metadata readerとPBS費用readerはこの単体テストではdoubleであり、実最終reportを再検証した結果ではない。

[受入資料](data_tile_validation_2026-10-17/low_timing_partition_runner_acceptance_v1/accepted.json)にrunner、テスト、証跡検証依存source、実装前の失敗log、保存版成功log、Python版を保存した。
受入記録のSHA256は `cec46d2511415310d3c1205b51ef3ef28f0171e05e02eec207144fb282468055` である。
repository rootから次のコマンドで再実行できる。

```powershell
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" -B -m pytest docs/wp/data_tile_validation_2026-10-17/low_timing_partition_runner_acceptance_v1/test_runner.py docs/wp/data_tile_validation_2026-10-17/low_timing_partition_runner_acceptance_v1/test_resource.py -q -p no:cacheprovider
```

## クラスタの固定環境確認

未使用directory `/home/user/workspace/mcmc4qec/20261022-low-partition-runner-bootstrap-v1` にrunner・証跡検証module・値処理moduleを配置した。
固定parent環境v4を読み、元のbootstrapとscience関数によるPython・source closure・native binding・runtimeの整合性確認、および値処理moduleのimportを実行した。
既存selectorのsource 53本を認識し、3.240秒で成功した。
[実確認結果](data_tile_validation_2026-10-17/low_timing_partition_runner_bootstrap_v1/stdout.json)のSHA256は `2527429af1272c67bcbc3f44d2116f6f270fa58248d11373d6dfae2ff8f7a4e2` である。
runner sourceのSHA256は `447cb602658980834ecff964b8c8d1367b5c64991d2d3684b91e57ea7283ee84` である。
同階層に送信program、実行結果、stderrを保存した。
これは軽いimportとfile整合性確認であり、sampling・trace reader・新しいnative probe・qsubは実行していない。

## 未完了

実metadata全12件からの分割入力作成、共有lock下の投入と最大2node制御、実PBS内のworker実行、結合ジョブの資源算定と実行、後続censusへの接続は未完了である。
`capture-terminal` はmetadataのdescriptor作成までで、trace payloadの再照合は実行枠を確保した結合ジョブに残す。
この段階で全条件選択の完了や科学的な混合・被覆・速度を認定せず、低ノイズの正式完了数は9/12条件のままである。
