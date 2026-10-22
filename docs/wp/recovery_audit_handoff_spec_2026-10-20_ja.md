# 復旧collectorからtrace監査への一度限りの引継ぎ

復旧collector265362の実qstatで、固定script・resource・run_count 1・F・exit 0を確認してから既存completeを一度だけ実行する。
観測timeoutや一時的SSH失敗は未確定として同じjobを観測し、終了や再投入の根拠にしない。
正常終了以外のterminalは停止し、同じ計算を再投入しない。

完了検査後、準備済み復旧audit workerでcapacityのplan・preflightを作る。
C0T2最終reportの既存監視による投入記録を確認し、実要求ノードが2未満になってから既存schedulerでcapacityをqsubする。
共有lock、Qを含む最大2ノード、直前の再検査は既存schedulerが実行する。
capacityの実正常終端とcompleteを受理してから、実測資源によるfull plan・preflight・qsub・completeへ進む。
元worker・scheduler・稼働中controllerは変更しない。

各変更操作は先に排他的なintentを保存し、応答・検査結果を別途保存する。
変更操作のtimeout・曖昧応答・エラーは自動再試行せず、状態確認を要求する失敗記録を残して停止する。
共有slotの観測は30秒間隔とし、新規ジョブを要求しない間はqsubしない。
全full監査までの引継ぎ完了は科学cohortの最終受理とは区別する。
各監査のcomplete応答は、直前に投入・観測したjob IDとterminal hashの形式を照合する。
collectorのcomplete応答でも、固定config・実job ID・科学cohort未受理・full監査未完了を要求する。

2026-10-20のWindows受入は30 passed・2.23秒だった。
試験はPBS状態・resource・完了応答の不一致、同一操作の再実行禁止、通信観測の再試行と処理順を検査し、クラスタの実計算は実行しない。
実配置済みcontrolの全hash、未作成のcapacity/full root、未封印のcollector terminalをread-onlyで照合した。
20:21 JST前後にlocal PID47332で引継ぎを起動し、実job265362のRを観測して待機している。
この起動時点で監査plan・qsub・実監査・completeは未実施であり、科学的な正式完了数は増えていない。
実行入口は `python -B output/recovery_trace_audit_v1/handoff.py` だが、この起動は使用済みであり再実行しない。
記録先は `data_tile_validation_2026-10-17/recovery_trace_audit_handoff_v1`、事前照合は同階層の `recovery_trace_audit_handoff_preflight_v1.json` に保存した。
両引継ぎのsource・受入結果・起動証跡・実機観測は [49ファイルのmanifest](data_tile_validation_2026-10-17/automatic_handoffs_progress_20261020_v1/manifest.json) に保存し、SHA-256は `52eb9cd2617bd702374ea44ac554dbb649b7df03e71473362f9125c38cf5d7ab` である。
