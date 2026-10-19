# Portable BARのcohort分母と途中結果の照合

最終集約の小仕様に基づき、検証済みbatchを全768 groupの予定集合へ対応付けるindexを追加した。
これは最終trace監査・reference結合の前段であり、正式なbias・RMSE・被覆の集約readerはまだ未実装である。

元のhost割当、production manifest、source、hostごとのruntimeを照合する。
未知group、group重複、archive重複、host変更、runtime/sourceの違い、行数・失敗数の不整合を拒否する。
未到着groupはpendingとして残し、infrastructure failureのgroupも88設定分の予定行を分母に残す。
未取得の推定値や診断値は作らない。
全groupが終端した場合でも、このindexだけで`final_scientific_validation=True`にはしない。
欠落がある場合に全group完了を要求する呼出しは失敗する。

実装前の受入テストの失敗を保存し、実装後はarchive検証を含む21テストが0.91秒で通った。
その後、実回収済みDGX batch 0/1のarchive member、parent binding、source、runtime、全group集合を再照合してindexを作成した。
batch 1は実execution intentとの結び付けも再照合した。
読み取り前後のarchiveと関連入力のhashを確認した。

| 項目 | 件数 |
| --- | ---: |
| 全予定group | 768 |
| 回収済みgroup | 40 |
| 未回収group | 728 |
| 全予定設定行 | 67584 |
| 取得済み設定行 | 3520 |
| 未回収の設定行 | 64064 |
| 取得済み行の区間未取得 | 0 |
| 取得済み行の診断flag | 3520 |
| 取得済み行の未定義診断 | 2132 |

未回収728 groupの診断が良好であるという意味ではなく、未回収と診断済みを分けて記録している。
取得済み行の診断flag・未定義診断を理由に分母から除外していない。
この部分集合から全cohortのbias・RMSE・被覆を推定していない。

結果は`data_portable_bar_2026-10-19/first40-cohort-inventory-v1.json`に保存した。
source・受入log・再現用スクリプトは同directoryの`cohort_index_sources_v1/`にあり、依存する回収helperの記録は既存の`collection_sources_v1/`等にある。
元samplingの全partition終端、元環境でのtrace監査、独立referenceとの結合と、実行中の全設定移植比較は引き続き未完了である。
