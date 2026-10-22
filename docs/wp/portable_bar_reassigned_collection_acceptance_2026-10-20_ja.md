# 再割当て結果の回収と旧新混合集計の受入記録

## 実装範囲

[固定分担plan](portable_bar_remaining_assignment_acceptance_2026-10-20_ja.md)と[runner](portable_bar_reassigned_runner_acceptance_2026-10-20_ja.md)に続き、再割当て結果の回収と旧新経路の群数集計を実装した。
新しいcollectorは既存collectorから明示した置換だけで導出し、元のファイルは変更していない。
固定ownerによる担当検査を、独立したplan・baseline・config・実行intent・実際の担当の照合へ置き換えた。
数値行・診断・ACF・終端記録・snapshotの検査関数は、既存版とASTが同一であることを確認した。
回収archiveにはplan・baseline・config・parity検査の証明記録と、新collectorおよび照合helperのsourceを含める。
archive内のcollector名を新しい版の名前にし、旧collectorの名前で新しいsourceを示さない。

旧新混合集計は既存の全群数集計から導出し、固定planの実行先と各batchの割当てを検査する。
実行先を `host`、元の担当を `original_host` として記録し、移動した264群についてLaboで実行したことにしない。
既存18 DGX batch・6 Labo batchと新規14 batchの合成記録で、全768群・192 seed・67584行を保持することを確認した。
失敗・未回収・区間未取得・診断未定義を除外せず、完了した群数と数値行の取得状況を区別する。
全群が揃っていても `final_scientific_validation` はfalseのままとする。

## 実行した確認

collectorと混合集計の受入テストを先に作り、未実装によるimport失敗を保存した後に実装した。
collectorの初回検査は新規検査26件と既存の数値・診断検査23件の計49件が11.90秒で成功した。
configのschema・runtime・入力名の検査を追加した後、新規検査29件が5.79秒で成功した。
新旧archive転送検査15件は0.77秒で成功した。
新旧群数集計31件は44.11秒で成功し、導出sourceの一致を検査する追加1件も0.43秒で成功した。
導出元のSHA-256、置換手順、導出後のsource hash、RED/GREENログを保存した。
既存の小さい数値fixtureを使う行・診断検査以外は合成した割当て・終端記録・archiveの検査であり、新経路で本番結果を回収した検証ではない。

## 保存と再現

[sourceと検証ログ](data_portable_bar_2026-10-19/remaining_assignment_collection_sources_v1/)には39ファイルを保存し、コピー前後のSHA-256を照合した。
[manifest](data_portable_bar_2026-10-19/remaining_assignment_collection_sources_v1/manifest.json)のSHA-256は `57a9c81740431160357bfd601236c687b3e61631004e616624ebfac9aceb5b2c` である。
manifestには各ファイルの元の相対位置と、基になるリポジトリのcommitを記録した。
再現にはそのcheckoutの `src/` と `cluster_scripts/` を使い、保存したhelperを記録された `output/` の位置へ復元する。
テストの実行例は次のとおりである。

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -B -m pytest output/test_portable_bar_reassigned_collection_v1.py output/test_portable_bar_reassigned_collection_regression_v1.py output/test_portable_bar_reassigned_archive_v1.py output/test_portable_bar_archive_v1.py output/test_portable_bar_mixed_cohort_v1.py output/test_portable_bar_cohort_v1.py -q
```

上記は個別に実行したテスト群をまとめた再現用コマンドであり、この組合せでの一括実行時間は未測定である。
archive作成・source導出の各スクリプトは実行済みであり、既存の出力を上書きするために再実行しない。

## 残る作業

再割当て結果を読むpayload reader・最終provider・転送用contextの対応、および本番config生成・入力配置・起動と回収の自動制御は未完了である。
ここまでの検査は元環境での全sampling・trace監査・独立reference照合を代替しない。
再割当て264群の本計算は未開始であり、公開候補のsourceと配布物も変更していない。
