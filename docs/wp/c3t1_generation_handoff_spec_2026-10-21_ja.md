# C3T1生成への順次引継ぎ

## 小仕様

C3T1の固定済みanchor 0・sample 0・sample 1だけを対象とし、既存preflightと未使用executeを照合する。
先行C3T0のfull監査とnative referenceの正常完了後に、元のqsub wrapperでanchorを投入する。
anchorの正常終端を確認してからsample 0・1を空き枠へ投入し、実receiptを同条件registryへまとめる。
現在まだ存在しないC3T0 native開始記録を待ち、元source・condition・referenceのbindingを確認してから先行完了の検査へ進む。
元の共有lock、最大2要求ノード、実PBS検査、曖昧性を残した停止を維持する。
元C1T2生成driverの実行順序と操作を再利用し、稼働中sourceを変更しない。
registry完成をsamplingの正常終了や科学的受理とは扱わない。

## 受入条件

実3 preflight・未使用execute・C3T0監査開始記録を操作なしで照合する。
native開始記録がない間は先行完了検査やqsubへ進まず、別条件や別sourceを拒否する。
samplingより先にanchorの正常終端を要求し、失敗時は同一executeを再試行しない。
条件別receiptとregistryのpathがC3T1に限定されることを確認する。

## 実施結果

Windowsの追加11件と元生成driverの回帰14件が成功した。
実3 preflight・未使用execute・先行監査の開始記録を照合した。
実PBS正常終端のfixture検査は行ったが、本番先行ジョブの正常終端受理と新規qsubは未実施である。
sourceとテスト結果は `data_tile_validation_2026-10-17/c3t1_generation_handoff_acceptance_v1/` に保存した。
PID17876・session2387で待機を開始し、02:08のsession pollで生存を確認した。
