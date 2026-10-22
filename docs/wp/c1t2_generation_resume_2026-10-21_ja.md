# C1T2生成待機の再接続

## 小仕様

C1T2の旧待機処理は、C1T1監査待機の失敗を検出して、anchor投入前に停止した。
同じ事前固定済みgenerator・3件のpreflight・seed・resourceを用い、新しい実行記録から待機を再開する。
先行監査の参照先だけを `planned_c1t1_thread_resume_v1` に変更し、sourceとintentのhashを固定する。
旧停止理由の一致と、旧待機内のanchor/sample操作が未実施であることを確認する。
全体のsubmission receiptが存在する場合は、元の検査により再投入を拒否する。
元driverの実PBS正常終了・native reference受理・Qを含む最大2要求ノード・anchor終了後のsample投入・receipt registry検査を継承する。

## 受入条件

旧停止理由が違う場合と、いずれかの生成操作intentが存在する場合は起動を拒否する。
再接続先のsource hashと生成時のthread環境指定を検査する。
元driverの順序と実投入receiptの受入テストを併せて実施する。

## 実施結果

Windows Python 3.11で新規テストと元driverのテストを実行し、21 passed・0.77秒だった。
PID6248で起動し、実際の事前固定済みpreflight・未投入・sourceの照合に成功した。
00:18時点でC1T1 full監査の受理待ちであり、C1T2の生成qsubは未実施である。
sourceとログは [保存manifest](data_tile_validation_2026-10-17/orchestration_thread_resume_20261021_v1/manifest.json) に固定した。
