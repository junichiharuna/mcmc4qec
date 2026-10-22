# C3T1/C3T2最終集約の依存先再接続

旧最終集約の準備・実行・後処理は、先行auditの停止を検出し、各工程の実操作前に停止した。
条件ごとの旧保存先と失敗種別を照合し、準備request・qsub intent・回収・算術集計などの記録が追加されていれば再接続を拒否する。
旧記録は保持し、新しいlocal保存先から再接続したauditの完了を待つ。
native reference、PC計算、distribution、科学設定、remoteの準備・集約root、configの検証、qsubと最大2要求nodeの制約を維持する。
変更はlocal保存先と監視する先行経路、および再接続の出典記録に限定する。
準備はdistribution・audit・nativeの完了証跡が揃った後だけ実行し、実行driverはその準備結果を既存の検証関数で受理してから投入する。
投入応答が不明な場合は停止し、同じ操作を自動で再実行しない。

受入では条件・工程の限定、旧工程の未着手状態、既存のremote rootと検証sourceの保持、新local保存先間の参照整合を確認する。
本接続の受入を集約結果や科学的精度の受入とは扱わない。

## 22:07 JSTの接続・実稼働確認

旧保存先の全6工程を照合し、準備はintentとerrorだけ、実行・後処理はそれらと待機観測だけだった。
新たな準備・実行・後処理の接続を `output/final_slot_resume_v1/` に実装し、固定scope・未着手状態・経路整合の14 testが1.25秒、記録付き実行では1.00秒で成功した。
sourceと受入記録は [final_slot_resume_acceptance_v1](data_tile_validation_2026-10-17/final_slot_resume_acceptance_v1/) に保存した。
accepted.jsonのSHA256は `5f7ed302097cca92109dcf4b97889249459921f3f530e924de5d3665508bee89` である。
試験は元workspaceのsourceに対して実行し、同じbyteのsourceを受入資料に保存した。

C3T1の準備・実行・後処理はPID42028・30080・36268、C3T2はPID15892・49348・46316で起動した。
実processとcommandを照会し、全6工程にintentがあり、errorとcompletedがないことを確認した。
実行driverの入力照合はC3T1が314件、C3T2が423件の固定入力で成功した。
新記録は `data_tile_validation_2026-10-17/slot_reconnected_final_v1/` に保存する。
この時点では先行するdistributionとauditの完了を待っており、新しい集約jobのqsubは未実施である。
クラスタの265457と265448は実照会でともにRで、合計2要求nodeを維持している。
