# Portable BAR最終集計の投入ラッパー

`output/portable_bar_qsub_v1.py` にprepare・submit・compute・completeを実装した。
既存の `portable_bar_final_join_v1.py` と科学的なreader・推定式・予定分母は変更していない。
全768群と両hostのreplayを結ぶmetadata、元環境の監査summary、転送完了記録、source一覧とhashを照合し、実データの検証は既存readerがPBS内で再実行する。
prepareはqsubを呼ばず、submitの `--execute` だけが共有lock・controller不在・待機ジョブを含む最大2ノードの制約を検査してqsubを一度呼ぶ。
qsubのtimeoutや不明な応答ではintentとlockを残し、自動再投入しない。
computeは実PBS IDと投入receiptを照合し、失敗したreaderを成功扱いせず、completeは実qstatの正常終端と結果hashを確認する。

受入テストはWindows Python 3.11で27 passed・3.53秒、元クラスタのPython環境で27 passed・5.50秒だった。
試験は模擬入力・模擬qsubを使い、ノード上限、queued job、最後の確認時点の資源増加、二重投入、曖昧な応答、source変更、群の欠落・重複、reader失敗、PBS ID不一致、未終端・再実行jobを検査した。
最初の追加試験ではWindows fixtureのPBS引数がPOSIX shell用に引用されておらず1 failed・26 passedとなり、fixtureの引用を修正した。
その失敗ログと実装前のREDログも保存している。
実cohortの最終集計や科学的受入が終わったという意味ではない。

source SHA-256は `890ee2f042e7971c858fe396de0a79254fa0130c8ade8e41a27e93b9fac4d42f`、テストは `3708bf2e3fbbbac6fc51bf782f983531e3a23f96f45263793e5d71348a35e968` である。
固定snapshotとログは [qsub_sources_v1](data_portable_bar_2026-10-19/qsub_sources_v1/manifest.json) に保存した。
クラスタの `/home/user/workspace/mcmc4qec/20261020-portable-final-qsub-v1` に同じsourceとテストを配置し、元bundleや実行中ジョブのsourceは変更していない。

実行時は、全群の回収・転送完了と元環境のnative audit完了後、実path・hash・資源の判断根拠を記したconfigurationを独立に固定する。
sampling完了後のnative auditはPC解析の完了を待たずに進められる。
configurationには `inputs` のsampling/audit/portable/reference、`source_roots` のhelper/cluster/package、全Python sourceの `source_sha256`、wrapperと実Pythonのpath/hash、必須metadataの `metadata_sha256`、`resource`、`resource_reason`、測定証拠の `resource_evidence` を指定する。
実Pythonはsymlinkではなく解決済みの絶対pathを指定し、resourceは1 CPU・1ノードのメモリGBとwalltimeを記録する。
sourceの必要な一覧とmetadataの詳細は実装の `read_config` で検査する。
固定configurationのhashを全段階の `--config-sha256` に渡し、`prepare --config ...`、`submit --execute`、PBS内の `compute`、終端後の `complete` の順に実行する。
この時点では実configurationの作成、最終集計用のprepare・qsub・completeは未実施である。
