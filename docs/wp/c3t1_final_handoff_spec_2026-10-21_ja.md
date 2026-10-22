# C3T1の最終準備・集計への接続

## 小仕様

C3T1の全PC回収後の転送、full監査、native reference受理を照合して、既存の条件別preparerへ接続する。
受入済みC3T0用adapterの条件・監査source・待機sourceのbindingだけを変更し、稼働中sourceは変更しない。
設定作成後は元のpreflight・最大2要求ノードの空き確認・共有lock下のqsub・実PBS終端確認・13成果物回収を使用する。
前段が未完了の間は待機し、操作失敗や曖昧な投入結果を自動再試行しない。
最終集計の12時間設定は資源上限であり、予想所要時間ではない。

## 受入条件

実監査・転送待機・元sourceのbinding、前段3種類の完了条件、別条件・別hash・別jobの拒否を確認する。
最終driverはcase 3・target 1をcollectorへ渡し、他条件の設定を拒否する。
元操作の回帰テストと1 thread環境の維持を確認する。
本番の全件準備とreport完了は、その実証跡の回収まで未実施とする。

## 実施結果

Windowsの準備側22件・実行側31件が成功した。
sourceと結果は `data_tile_validation_2026-10-17/c3t1_final_handoff_acceptance_v1/` と `c3t1_final_execution_acceptance_v1/` に保存した。
準備はPID3052・session13885、実行はPID26748・session56191で待機を開始し、02:08のsession pollで生存を確認した。
本番の設定作成、最終qsub、13成果物回収は未実施である。
