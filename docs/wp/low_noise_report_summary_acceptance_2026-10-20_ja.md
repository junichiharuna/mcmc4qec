# 低ノイズ比較report要約の受入結果

[小仕様](low_noise_report_summary_spec_2026-10-20_ja.md)に従い、保存済みreportから値を抽出する要約入口を追加した。
既存C0T1用の一回限りの要約sourceと、その結果は変更していない。
新入口では、選択した8設定の点推定がすべて取得できることを前提にせず、欠測とfailureを残したまま192 seedの分母を維持する。
全352設定を保存し、独立referenceなしの被覆件数・bias/RMSE範囲はnullのまま扱う。
BARやMCMC、referenceの値を新たに計算する処理ではない。

受入テストを先に追加し、未実装によるimport失敗を確認した後に実装した。
12テストが0.79秒で成功し、欠測・interval未取得・referenceなし・分母不一致・重複設定・選択設定不足・範囲外件数・不完全cohortのRMSE・誤ったhash・既存出力保護を確認した。
実データ確認では、固定hashのC0T1 report 454,663,531 bytesを読み、67,584行・352設定の保存集計から約4.01秒で要約を作った。
[新しい要約](data_tile_validation_2026-10-17/low_c0t1_summary_extractor_check_v1.json)のSHA-256は `e7e4b532b99805f88ee7e662d3937e976d9baa7c00fd96d7f2d554a530c14873` である。
[従来要約との照合](data_tile_validation_2026-10-17/low_c0t1_summary_extractor_comparison_v1.json)では、選択8設定、全設定の範囲、reference、failure件数、audit項目など15項目が一致した。
照合記録SHA-256は `eafd791191dbb75c56a89703d4f14b8d7370b82c9f3d4107af50c92de2592b57` である。
この一致を新しい科学検証やraw payloadの独立再監査とは扱わない。

source・テスト・初回失敗と成功のログ・実データ照合を [11ファイルの保存manifest](data_tile_validation_2026-10-17/low_noise_report_summary_sources_v1/manifest.json)にまとめた。
manifest SHA-256は `a8c3458662788926f174ff2651ebe7368445f51e4b3fb98b4d6d79a6781ebe03` である。
再現時はmanifestの相対pathどおりrepositoryへ復元し、external_inputsのhashを確認する。
テストは `python -m pytest output/test_summarize_low_noise_report_v1.py -q` で実行する。

最終readerの正常終端と回収で得た実reportのpath・SHA-256を指定し、未使用の出力pathへ次のように要約する。
未取得のreport hashを仮値で埋めたり、途中indexを最終reportとして渡したりしない。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B output/summarize_low_noise_report_v1.py --report $reportPath --report-sha256 $reportPin --case 0 --target-index 2 --output $newSummaryPath
```

C0T2の最終reportはまだ得られておらず、この入口による同条件の最終要約は未実施である。
抽出する長い設定は以前から固定した記述用の断面であり、推奨設定、収束、名目95%被覆や母RMSEの保証ではない。
