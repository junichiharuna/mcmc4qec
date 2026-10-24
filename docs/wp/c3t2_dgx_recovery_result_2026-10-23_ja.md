# C3T2 DGXと後続待受の復旧結果

2026-10-23 13:09 JSTにDGX batch0の転送後hash確認が90秒でタイムアウトし、serialと親待受、依存する5段階の待受が停止した。
13:16の読み取り専用確認で、転送先14ファイルすべてが元のhashと一致し、入力archiveは69,562,906 byte、該当するDGX数値プロセスは存在しなかった。
元の入力・制御265件のpin、全33バッチの割当、旧プロセスの不存在を確認して、未作成のpreposition受理記録を追加した。
旧停止記録と科学helperは保持し、export・prepositionを再利用して別のserial記録からparity以降を継続した。

復旧制御の受入は12 passed・3.55秒、後続経路の受入は9 passed・4.36秒だった。
後続経路はindex・distribution・最終準備・最終実行・最終回収の5段階を新しい記録へ接続し、完了済みのlabo共通入力回収を再利用する。
最終実行のCOLLECTIONと算術検証のdistribution_doneも復旧先へ結び、canonicalな候補出力先と元のqsub・最大2要求nodeの共有制御は維持する。
実行待受の事前確認を最終準備のintent作成直前に行った際のFileNotFoundErrorは、準備PIDの生存とintent作成を確認した後に読み取り専用確認を再実施し、成功した。
その事前確認は実行待受やqsubを起動しておらず、重複投入はない。

13:23 JSTの[実稼働観測](data_tile_validation_2026-10-17/c3t2_recovery_runtime_observation_20261023_v1.json)で、DGXのparity PID2127569、laboのbatch0 PID23488、復旧serialと後続5待受、C3T1 index、C3T2 collector待受の実プロセスを確認した。
DGX parityとlabo batch0はいずれも数値処理中で、terminalは未取得だった。
全体の数値検証は未完了であり、今回の復旧を精度・被覆・混合の認定とは扱わない。

主な証拠は以下に保存した。

- [入力確認・復旧受入・serial記録](data_tile_validation_2026-10-17/c3t2_dgx_preposition_recovery_v1/accepted.json)
- [元の入力と停止記録の照合](data_tile_validation_2026-10-17/c3t2_dgx_preposition_recovery_v1/reconciliation.json)
- [後続制御の受入](data_tile_validation_2026-10-17/c3t2_dgx_followup_recovery_v1/accepted.json)
- [入力確認の小仕様](c3t2_dgx_preposition_recovery_spec_2026-10-23_ja.md)
- [後続接続の小仕様](c3t2_followup_recovery_spec_2026-10-23_ja.md)

復旧serialのPIDは5212、indexは45712、distributionは49400、最終準備は48012、最終実行待受は23748、最終回収待受は41396である。
旧の監視PID29984は依存失敗で停止した記録を保持しており、新serialが自身の完了と親handoffの完了を記録するため、旧監視を再起動していない。
