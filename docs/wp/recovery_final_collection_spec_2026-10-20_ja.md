# 復旧条件の最終report回収

既存の最終report collectorを別ファイルへ派生し、元collectorは変更しない。
対象をC1T0、復旧用qsub wrapperの固定hash、元venv入口へ明示的に変更する。
snapshot開始時は外部pin付きconfigのsource全体を照合してからwrapperをimportする。
reportについて既存のPBS・実行host・行数・条件数・hashに加え、復旧authority・入力証跡・reader sourceをwrapperの既存検査関数で照合する。
転送前後のsnapshot一致、失敗記録の保持、同じ保存先への再実行拒否は既存処理を維持する。
collectorからqsub、BAR、復号、raw trace監査を新規に実行しない。
実最終configと正常終端・sealed terminalが揃うまで本番回収は行わない。

受入ではPBS・監査I/Oをfixtureに置き換え、改変・未完了・再実行・転送失敗を拒否する。
派生差分を固定文字列の置換と追加検査に限定し、元sourceと生成結果の対応を検査する。

## 実装と受入

`output/recovery_bar_final_v1/recovery_final_collection.py` に独立collectorを実装し、`derive_collection.py` で元collectorとの派生差分を再現できる。
sourceはimport前に全pyファイルのcensus・canonical path・hashを確認する。
元collectorは変更せず、復旧qsub wrapperの `validate_report` と `recovery_state` をsnapshot内で使う。
Windows31 passed・8 skipped・3.01秒、Linux39 passed・1.57秒だった。
Linuxの追加8件はimport前の拒否と、実qsub wrapperによるprepare・fixture qsub・compute・completeからcollector snapshotまでの接続を含む。
PBS応答と監査I/O・数値reportはfixtureであり、本番の科学受理とは区別する。
sourceとログは [native受入](data_tile_validation_2026-10-17/recovery_final_collection_native_v1/accepted.json) に保存した。

## 本番制御ファイルの配置

`/home/user/workspace/mcmc4qec/20261020-recovery-c1t0-final-controls-v1` に制御ファイル22個を新規配置した。
元venvでimportし、元native referenceに含まれる113ソースとbyteを比較し、読み込まれた75 moduleの配置先とhashを確認した。
worker sourceは実batch0の固定recipeと一致し、collectorのwrapper path・hashとPython入口も一致した。
配置記録は [実native bootstrap](data_tile_validation_2026-10-17/recovery_c1t0_final_controls_native_v1/accepted.json) にある。
最終config作成・preflight・qsub・report実行・本番回収は未実施で、復旧collector完了後のauthorityを受理した結果ではない。
配置先は使用済みであり、同じstage操作を繰り返さない。

## 実行条件

本番回収には、当該wrapperによる正常終了確認とsealed `terminal.json`、外部で固定したconfig hash・terminal hashを必要とする。
入口は `recovery_final_collection.py --remote-root <最終job root> --config-sha256 <固定hash> --terminal-sha256 <固定hash> --destination <未使用local保存先>` である。
collectorは元venvからmetadataを読み、reportを別途scpで取得し、転送後に同じsnapshotを再確認する。
失敗時は保存記録を保持して原因を確認し、同じ保存先へ自動再試行しない。
