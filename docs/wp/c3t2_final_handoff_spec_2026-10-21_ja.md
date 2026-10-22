# C3T2の最終準備・集計への接続

## 小仕様

C3T2の全PC回収後の転送、full監査、native reference受理を照合し、既存の条件別preparerへ渡す。
受入済みC3T1用adapterの条件・監査source・待機sourceのbindingだけを変更する。
最終設定作成後は元のpreflight・最大2要求ノードの空き確認・共有lock下のqsub・実PBS終端確認・13成果物回収を維持する。
前段未完了は待機とし、失敗や曖昧な投入結果を自動再試行しない。
12時間の最終集計設定は資源上限であり、所要時間の保証ではない。

## 受入条件

実監査・転送待機・元sourceのbinding、前段3種類の完了条件、別条件・hash・jobの拒否を確認する。
最終driverはcase 3・target 2をcollectorへ渡し、他条件の設定を拒否する。
元操作の回帰テストと1 thread環境を維持する。
本番の全件準備とreport完了は実証跡の回収まで未実施とする。

## 実施結果

Windowsの準備側22件・実行側31件が成功した。
sourceと結果は `data_tile_validation_2026-10-17/c3t2_final_handoff_acceptance_v1/` と `c3t2_final_execution_acceptance_v1/` に保存した。
準備はPID24796・session46844、実行はPID3716・session74361で待機を開始し、02:08のsession pollで生存を確認した。
本番の設定作成、最終qsub、13成果物回収は未実施である。
