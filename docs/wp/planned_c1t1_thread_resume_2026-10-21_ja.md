# C1T1後続処理の環境設定を伴う再接続

## 小仕様

旧C1T1 driverは先行監査のerrorを検出し、collectorのpreflight後、submit前に停止した。
旧実行記録と固定workerは変更せず、別の実行記録から同じcollector・capacity監査・full監査を再開する。
先行監査の参照先を `recovery_full_thread_resume_v1` に変更し、実際のPBS正常終了と受理済みterminalの確認は既存実装を継承する。
すべてのworker呼び出しで、元のnative decoder環境の4種類のthread数を1、PYTHONHASHSEEDを0にPython起動前に設定する。
旧driverの停止理由が一致し、いずれのsubmit intentも存在しないことを再開条件とする。
元driver・修正済み先行driver・先行intent・旧停止記録と元の受理済み入力をhashで固定する。
qsub直前の要求ノード確認、共有lock、実際のPBS結果の検査、曖昧な投入の自動再試行禁止は元の実装を維持する。
新しい出力先も一度だけ作成し、失敗時にはerrorを保存して停止する。

## 受入条件

全worker actionで環境変数が元interpreterより前に付与され、workerとconfig引数が保持されることを確認する。
別interpreterや別SSH接続の要求は実行前に拒否する。
旧停止理由の相違、既存submit intent、旧completedの存在は再開を拒否する。
既存driverの順序・PBS正常終了・最大2要求ノード・一度だけの操作に関するテストを併せて実施する。
この修正は実行制御のみを対象とし、新しい数値結果の正しさや混合を保証するものではない。

## 実施結果

Windows Python 3.11で新規テストと元driverのテストを実行し、38 passed・0.76秒だった。
PID28916で起動し、先行full監査265369の実PBS正常終了とterminal受理を確認した。
collector265370をqsubで投入し、00:18時点で実行中である。
以後のcapacity/full監査は未完了である。
sourceとログは [保存manifest](data_tile_validation_2026-10-17/orchestration_thread_resume_20261021_v1/manifest.json) に固定した。
