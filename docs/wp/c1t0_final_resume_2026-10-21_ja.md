# C1T0最終設定・投入の再接続

## 小仕様

旧preparation waiterと旧final driverは、先行監査の失敗を伝播して、それぞれprepare前とpreflight前に停止した。
旧source・旧記録・native preparer・final wrapperは保持し、新しい待機記録と実行記録を用いる。
旧停止理由と未操作を確認し、元のbindingsで既存受入証拠を検査した上で、修正済み監査driverとそのintentを追加固定する。
元waiterのcompletion検査に、新しいfull監査の受理記録を渡す。
全PC回収・転送とfull監査の両方が完了した後に、元のnative preparerを一度だけ呼ぶ。
preparerが成功した後に限り、元final driverのpreflight・最大2要求ノード確認・qsub・実際の正常終了検査・13ファイル回収を順に行う。
制御用remote Pythonには生成時と同じthread環境を起動前に渡す。
観測timeoutや投入結果不明を正常終了や再投入許可として扱わない。
この再接続は数値計算・科学的受入条件を変更しない。

## 受入条件

予期した停止理由以外、prepare/preflight/submitのintentが存在する場合、完了済みの場合は再開を拒否する。
修正済み監査intentのsource hashと環境指定を検査する。
元の受入テストに加え、環境付与・別interpreter拒否・既存操作拒否を検査する。
新記録と旧記録の保存先を分離し、source変更は実行中の検査で拒否する。

## 実施結果

Windows Python 3.11で新規テストと元preparer・waiter・final driverのテストを実行し、59 passed・0.80秒だった。
PID47776で起動し、実際の固定済み受入証拠と再接続先intentの照合に成功した。
00:18時点ではfull監査受理済み、PC全回収・転送待ちであり、prepareと最終qsubは未実施である。
sourceとログは [保存manifest](data_tile_validation_2026-10-17/orchestration_thread_resume_20261021_v1/manifest.json) に固定した。
