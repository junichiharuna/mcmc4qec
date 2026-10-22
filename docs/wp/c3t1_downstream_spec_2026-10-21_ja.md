# C3T1の生成後処理

## 小仕様

受入済みC3T0処理を、対象C3T1・先行C3T0の組合せへ明示的に束縛する。
生成receiptのregistry受理後にnative referenceを起動し、各PCは先行条件の正常回収と今回のreference受理を待って計算へ進む。
collectorとcapacity/full監査は実PBSの正常終端を要求し、既存の共有lockと最大2要求ノードの制限を維持する。
元sourceは変更せず、導出元hashと置換箇所数を記録する。
各操作は一度だけ実行し、観測期限の満了をジョブ終了とは扱わない。

## 受入条件

実設定・開始記録の照合、異なる条件の拒否、registry待機、childの実handle保持と異常終了、既存実行の再起動拒否を確認する。
元テストの条件を書き換える際は、異常fixtureが正常値と一致しないことを確認する。
全件indexと転送には既存の全5条件対応driverを使用する。
接続・テストの完了を本番の科学的条件完了として扱わない。

## 実施結果

Windowsの元受入と導出検査の計41件が成功した。
sourceと結果は `data_tile_validation_2026-10-17/c3t1_downstream_acceptance_v1/` に保存した。
launcherはPID42248・session62654、collector監査はPID43488・session16456で生成registry待ちを開始した。
全件indexはPID25248・session3855、全件転送はPID33688・session38810で待機を開始した。
02:08のsession pollで4処理の生存を確認した。
本番childの開始、全件index・転送完了、この接続からの新規qsubは未実施である。
