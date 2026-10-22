# C3T2の生成後処理

## 小仕様

受入済みC3T1処理を、対象C3T2・先行C3T1の組合せへ束縛する。
生成receiptのregistry受理後にnative referenceを起動する。
PC計算は各hostの先行条件の正常回収と今回のreference受理を待つ。
collectorとcapacity/full監査は実PBS終端と固定済み設定を照合する。
元の一度限りの操作、共有lock、最大2要求ノード、1 thread環境を維持する。
元sourceは変更せず、導出元hash・置換・結果hashを記録する。

## 受入条件

実設定・開始記録、異なる条件の拒否、registry待機、childのhandleと終端、重複開始の拒否を確認する。
導出が指定した変更に限られることと、既存の異常fixtureが引き続き異常であることを確認する。
全件indexと転送は既存の全5条件対応driverを使う。
本番の科学的受理は最終成果物の検証まで未完了とする。

## 実施結果

Windowsの元受入と導出検査の計41件が成功した。
sourceと結果は `data_tile_validation_2026-10-17/c3t2_downstream_acceptance_v1/` に保存した。
launcherはPID42644・session50292、collector監査はPID32224・session67040で生成registry待ちを開始した。
全件indexはPID44396・session60935、全件転送はPID42560・session22843で待機を開始した。
02:08のsession pollで4処理の生存を確認した。
本番childの開始、全件index・転送完了、この接続からの新規qsubは未実施である。
