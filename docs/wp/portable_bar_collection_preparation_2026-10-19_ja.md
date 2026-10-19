# 移植BARの回収準備と検証

2026-10-19 22:14 JST時点で、両PCの本処理は継続中であり、回収対象のbatch completionはまだ存在しない。
DGXは親PID 468606・20 group、laboは親PID 15892・24 groupで、完了groupはそれぞれ0だった。
この時点の結果を空の成功batchとして回収していない。

[回収仕様](portable_bar_collection_spec_2026-10-19_ja.md)に沿って、親側の投入記録・parity受入・固定group割当から独立したbindingを作り、両PCへ読取専用collectorを配置した。
collectorは元のsampling archive、export manifest、source、全raw payload、task metadata、結果marker、全設定と診断・ACFの対応を検証する。
sourceを固定した元loaderを使い、decoderは再構築しない。
検証中のfile変更も拒否する。
数値推定やACF自体を再計算する処理ではなく、保存結果の構造・完全性・provenanceを確認する処理である。

infrastructure失敗を含むbatchも、全予定groupと予定行数を残して回収できる設計とした。
失敗のあるbatchを成功batchと表示せず、部分artifactも保存する。
sampling失敗、利用不能区間、未定義診断は元の結果に残す。
転送後は親側でarchiveの全member hash・集合・親binding・reader hash・group censusを再照合する。
これは元samplingの最終監査や独立referenceとの科学集約を代替しない。

関連5ファイルの受入は44 passed・3.30秒だった。
既存producerの小さな出力を使い、正常・sampling失敗・anchor 0、設定欠落・重複、group変更、診断/ACF欠落、metadata/payload改変、runtime/source変更、未完了batch、危険なarchive path、転送改変を検証した。
通信timeoutを模した試験では、最初の実行intentを残して二度目のcollector実行を拒否した。
実C0T0のparity結果についても、6行・診断128件・ACF128配列の構造検証を実行し、全6行のflagged/undefinedを保持した。
検証用の短いwindowを収束済みの証拠として扱わない。

両PCに対して実際に終端確認のgateを呼び、どちらも `terminal=false, collector_executed=false` で戻った。
したがって、collector本体による完了batchの回収、結果archiveの作成と転送は未実施である。
実際の全window結果が出てから、構造検証を実データに適用する必要がある。

## 保存先と再現手順

証跡は [data_portable_bar_2026-10-19](data_portable_bar_2026-10-19/) に保存した。
`dgx-collection-parent-v1.json` と `labo-collection-parent-v1.json` が親側の固定bindingであり、`*-collection-preparation-v1.json` に配置したsource hashと未実行のcollector呼出しを保存した。
`collection_sources_v1/manifest.json` は小仕様・reader・transport・受入テスト・ログの保存時hashを記録する。
生入力archiveと実行先は [投入報告](portable_bar_postprocessing_result_2026-10-19_ja.md) を参照する。

本処理の観測には `output/observe_portable_bar_batch0_v2.py` を使う。
終端後の回収には `output/collect_portable_bar_batch0_once_v1.py dgx` または同じscriptの `labo` を使う。
未完了なら終端確認だけで戻り、collector実行intentを作らない。
終端確認後は新規のintentを作ってから一度だけcollectorを呼び、remoteの `collection-batch0-v1/outputs.zip` を親側へ転送する。
SSH応答が不明になった場合は、同じremoteのcollector出力とreceiptを確認してから回収を継続し、scriptの再実行でcollectorを重複起動しない。
検証済みの回収記録は `*-collection-v1/transfer-verification.json` に保存する設計であり、現時点ではそのfileは未作成である。

sourceの受入は、リポジトリrootでPython 3.11から次を実行する。

```powershell
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -m pytest output/test_portable_bar_transport_v1.py output/test_portable_bar_archive_v1.py output/test_portable_bar_collection_v1.py output/test_portable_bar_arrays_v1.py output/test_portable_bar_full_v1.py -q
```

実入力を使うテストは `output/portable_bar_parity_local_v2/export` を参照するため、別環境ではまず固定parity archiveと `portable_bar_runner_v2.py` から同じdirectoryを作る。
一般公開用のstandalone runnerや公開APIへの統合は、この回収helperの受入とは別の作業である。
公開候補を変更せず、正式な低ノイズ比較は引き続き4/12条件として扱う。
