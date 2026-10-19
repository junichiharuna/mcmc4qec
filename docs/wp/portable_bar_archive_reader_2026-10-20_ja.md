# Portable BAR archive readerの実装・検証

[小仕様](portable_bar_archive_reader_spec_2026-10-20_ja.md)に従い、全cohort providerの構成要素として `output/portable_bar_payload_v1.py` を追加した。
親のreceipt・source・runtime、execution intentと終端summary、各groupのmarker・JSON・NPZを相互に照合する。
元samplingのrecordとanchorを渡し、既存の`validate_group`で設定行・診断・ACFと失敗状態を再検証する。
infrastructure failureの部分出力は推定値として読まない。
公開候補および実行中driverは変更していない。

## 受入テスト

成功、sampling failure、anchor failure、infrastructure failureの実producerによる小fixtureを使った。
source、runtime、profile、変換規則、intent、marker、設定行、診断、ACF、計数、未知groupの不整合を拒否した。
外側のarchive hashを更新しても内部不整合を検出する改変テストを含む。
新readerの21件と既存archive検証の6件を合わせ、27 passed / 2.99秒を確認した。
実装前のimport失敗、初回テスト、修正後のテストログを保持した。

## 実データでの照合

DGX batch 2の入力archiveと回収archiveを親の固定hashに照合し、20群・1760行を読み取った。
各群について15 rung × 16 chainのsampling record、共有anchor、入力marker集合を元exportと照合した。
元の全設定行、診断とACFを既存validatorへ再度渡し、collection reportの計数と一致することを確認した。
結果は [batch 2のpayload検証](data_portable_bar_2026-10-19/dgx-batch2-payload-validation-v1.json) に保存した。
初回の実データ読取りでは、profileファイルのSHA-256をcanonical JSONのdigestと比較して拒否した。
両者は異なる表現のhashであるため、生ファイルをexecution intentへ、JSON内容のdigestをplanへ個別に照合するよう修正し、再実行が成功した。
初回失敗ログも保存し、入力や既存の計算結果は変更していない。

## 適用限界と残作業

この読取りは保存済みmetadataと出力payloadの検証であり、推定計算やdecoderを再実行していない。
現在の元sampling payloadのnative trace監査と独立reference結合は引き続き必要である。
全768群の集合、固定host割当、hostごとの全設定移植照合を一つに結ぶproviderは未完成である。
20群の読取り成功を全cohortのbias・被覆の校正完了とは扱わない。

## 再現資料

実行は `.venv-experimental-optional/Scripts/python.exe -m pytest output/test_portable_bar_payload_v1.py output/test_portable_bar_archive_v1.py -q` と `output/verify_portable_payload_batch2_v1.py` を用いた。
reader・受入テスト・実データ読取りscript・ログは `data_portable_bar_2026-10-19/payload_reader_sources_v1/` にhash付きで保存した。
実データ読取りscriptは排他的出力を使うため、保存済みの出力へ再実行しない。
