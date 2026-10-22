# C1T2生成後のnative referenceとPC処理への接続

## 小仕様

C1T2の生成再開driverが保存する正常完了recordと実generator registryを待ち、既存のnative reference driverを一度だけ起動する。
生成完了recordの意味は3件のqsub投入済みであり、samplingの正常終端とは区別する。
実sampling終端・qsub上限・reference回収の検査は、変更しない既存native driverが行う。
DGX・Laboについては、C1T1のserial driver intentとC1T2 native driver intentが存在した後、既存PC引継ぎdriverを各host一度だけ起動する。
PCの前条件全batch完了、referenceの受理、実process不在、parity、execution lockの検査は既存PC driverへ委譲する。
新しい親は子processのhandleを保持し、pollによる実終了と対応completed recordの両方を要求する。
観測の待ち時間を子の終了や再起動許可とは扱わない。
新親・元の受入済みsource・生成再開intent・実registryをhashで固定する。
起動intentは子の開始前に排他保存し、曖昧な起動や異常終了では同じ操作を自動再試行しない。
親が失敗した場合も、別の正常な子を暗黙に停止せず、起動済みPIDと終了状態をerror記録に残す。
この親はqsubや数値workerを直接呼ばず、科学的なcohort完了も宣言しない。
対象はC1T2だけとし、C3の実行順や既存の稼働中driverは変更しない。

## 受入条件

生成の未完了、異常終了、別registry path、hash不一致、scopeの違いを区別する。
nativeを先に起動し、各PCはnative intentと対応する前条件intentの両方を待つ。
子の起動intentが存在する場合、または既存子の保存先がある場合は二重起動しない。
子が実行中なら待機し、非zero終了は停止し、zero終了でもcompleted recordがなければ失敗とする。
zero終了とcompleted recordがそろった場合のみ役割ごとの完了を保存する。
source変更と生成完了record変更は実行前後の検査で拒否する。

## 実施結果

初版は合成テスト17件と接続先の回帰テスト20・19件に成功したが、実起動前のbindings検査で既存受入記録に存在しない `accepted` fieldを参照して停止した。
子process・qsub・数値workerは起動しておらず、実行directoryの作成前だった。
初版source・テスト・ログと `startup_failure.json` は `data_tile_validation_2026-10-17/c1t2_downstream_launch_acceptance_v1/` に保存した。

修正版v2は元の受入記録の `synthetic_only`・`real_driver_started` を検査し、外部固定されたWindows/Linuxログのhashと正常returncodeを照合する。
実在する両受入記録のschema、log変更・試験失敗・scope変更の拒否、実prelaunch bindingsの確認を追加した。
Windows Python 3.11で23 passed・0.83秒となり、実際の子processを起動してhandleと完了recordを照合する試験も成功した。
接続先の元native・PC driverの回帰は20 passed・0.77秒、19 passed・1.02秒だった。
新親自体のLinux試験は未実施で、Windowsで動く制御用親として実行する。
[v2 sourceと受入ログ](data_tile_validation_2026-10-17/c1t2_downstream_launch_acceptance_v2/manifest.json)のmanifest SHA-256は `16aaf92bf5bebe26de6b65e748ff0b243ae8644004af56682439b189d5406b01` である。
実行sourceのSHA-256は `767137e67d88fa6b27eb2930e67a7e0e0c4d95b3d555b41b07a25d20fb6813da` で、稼働中に変更しない。

local PID22720で起動し、00:34 JSTにsessionの継続をpollで確認した。
実行記録は `data_tile_validation_2026-10-17/c1t2_downstream_launch_v2/` に保存する。
この時点ではC1T2生成registryの完成待ちで、native/PCの子processはまだ起動していない。
この待機処理の開始をC1T2の計算開始・科学的検証完了とは扱わない。
