# 復旧full監査の起動環境修正

capacity監査265367は正常終了・受理済みだが、続くfull-planはnative環境照合で停止した。
read-only診断で、生成時との差はthread_environmentだけであり、元の1 thread設定をPython起動前に与えた別processでは全比較項目が一致した。
両方の診断でfull監査rootが未作成であることを確認した。
診断は `data_tile_validation_2026-10-17/recovery_full_native_diagnosis_v1/diagnosis.json` に保存した。

既存worker、監査config、source、native判定、resource計算、qsub protocolは変更しない。
各リモートworker操作のPython起動前に `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0` を明示する。
既存capacity計算を再実行せず、未作成のfull planから別の実行記録directoryへ進む。
plan・preflight・qsub・正常終端確認・completeを既存workerで一度ずつ実施し、曖昧応答は再投入しない。
qsubでは既存の共有lock・最大2要求ノードを維持する。

元の失敗した引継ぎと後続driverのerrorを削除・上書きしない。
full監査が受理された後、停止したC1T1収集・C1T2生成・C1T0最終設定・最終集計の依存先を、記録を残して新しい受理結果へ接続し直す。
環境修正はdecoder検査の緩和でも、科学的な混合・被覆の受理でもない。

## 再開の証跡

追加する起動commandと前提検査の受入はWindowsで5 passed・0.54秒だった。
生成時と同じthread設定を明示した実クラスタprocessでも、既存native fixture検査の全項目が一致した。
`output/recovery_full_thread_resume_v1/resume.py` をlocal PID46920で起動し、00:04 JSTにfull planの正常作成を確認した。
sourceのSHA-256は `86045281499b6ce2996c81bcbf3e38cf150ab7618816dc8ea542aa05927cc9d0` で、稼働中に変更しない。
新しい実行記録は `data_tile_validation_2026-10-17/recovery_full_thread_resume_v1/` に保存する。
作成されたfull manifestは `296ba3e0ac11356099043c72f38eee8227dad5eee21f623bd1bbfdcebbfd7181` である。
capacity実測から選ばれた要求は96 workers・96 CPU・62 GB・1 node・1時間30分である。
この時点ではpreflightを実行中で、full監査のqsub・正常終端・受理は未完了である。

## 00:20 JSTの追記

full監査265369をqsubで投入し、00:06:50開始・00:11:21終了、F・Exit_status=0・run_count=1、実walltime4分30秒を確認した。
受理済みterminalのSHA-256は `0ddb824ccb0c23f1b5904871b265317c071508d84aa557eb50b5b8b5f6c0da28` である。
旧失敗記録を保持したまま、停止した後続4処理を3本の新driverへ再接続した。
詳細は [最新状態](PROJECT_STATUS_2026-10-21_ja.md)、[C1T1再開](planned_c1t1_thread_resume_2026-10-21_ja.md)、[C1T0最終処理](c1t0_final_resume_2026-10-21_ja.md)、[C1T2生成](c1t2_generation_resume_2026-10-21_ja.md)を参照する。
