# 再開v2の実行後手順

2026-10-19に、再開job 265331の終了確認・最終比較・回収をv2配置へ接続した。
実投入済みの再開jobは `265331.node-PRISM` であり、再投入しない。
新しい配置は `/home/user/workspace/mcmc4qec/20261019-tile-low-bar-recovery-v2` である。
その下の `partition0-v1`・`report_helpers_v1`・`report_completion_helpers_v1` は子ディレクトリ名であり、旧v1配置を指さない。
旧v1のhelper・receipt・失敗記録は保存したままである。

## 実施済み

終了確認・readback・投入記録への接続の20テストは2.42秒で成功した。
報告control・終了確認・回収transportの21テストは2.42秒で成功した。
これらのtransportテストはSSHと終了結果を模擬し、実データの数値完了を証明するものではない。
実投入記録に対するテストは、v2の配置・hash・job 265331・qsubコマンドの結び付きを読み取り専用で確認した。
報告用6 helperをv2配置へ転送し、既存helperと同じbytes、Linux import、bash構文を確認した。
報告deploymentのSHA256は `9ac84d83a5572af97791085aa550d0ec7e352706f472ec075f81542ddf433531` である。
実report controlのobserveも成功し、再開job Q、report未作成、待機中を含むrequested_nodes 2を確認した。
最終比較の完了数は3/12のままであり、この手順更新では増加していない。

## 実終了後に行う順序

以下の各コマンドはPython 3.11の絶対パスで実行する。
実行前にPBSの該当jobを照会し、F・Exit_status 0・run_count 1であることを確認する。
Q又はRなら終了確認へ進まず、同じjobの状態を後で再確認する。

1. 再開job 265331が成功終了した後に、`output/complete_low_bar_recovery_once_v2.py` を一度だけ実行する。
2. acceptedの終了記録を確認してから、`output/control_low_bar_recovery_report_v2.py prepare` を実行する。
3. 生成された資源と入力を確認し、同controlの `preflight` を実行する。
4. 待機中を含む最大2ノードを守れる場合に、同controlの `execute` でqsubを一度だけ実行する。
5. 返されたreport jobが成功終了した後に、`output/complete_low_bar_recovery_report_once_v2.py` を一度だけ実行する。
6. acceptedの報告終了記録を確認してから、`output/collect_low_bar_recovery_report_once_v2.py` を実行する。
7. 回収前後のsnapshotと全13 artifactのhashが一致したaccepted receiptを確認してから、日本語報告と正式比較件数を更新する。

観測だけを行う場合は `output/control_low_bar_recovery_report_v2.py observe` を使う。
各操作は既存receiptがある場合に再実行を拒否する。
SSH timeoutやエラーが起きた場合は保存記録とリモートの実状態を照合し、失敗と決め付けて再投入しない。
回収先は `docs/wp/data_tile_validation_2026-10-17/low_bar_recovery_report_collection_v2/` である。
報告のprepare・qsub・実終了・回収は、この文書を作成した時点では未実施である。
未収束・診断未定義・区間未取得を分母から除外せず、独立referenceがない領域の整合性を精度保証と扱わない。
公開候補のcommit・push・公開操作とは独立した手順である。
