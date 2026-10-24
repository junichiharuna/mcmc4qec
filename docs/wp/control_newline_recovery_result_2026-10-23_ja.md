# 制御仕様書の改行差分からの復旧結果

2026年10月23日08:56 JSTまでに、C3T1とC3T2の停止した制御経路を再接続した。
数値sampling、native reference、PC解析の再投入は行っていない。
検証範囲は制御経路の復旧であり、数値計算全体の完了や科学的妥当性の認定ではない。

## 原因と影響

future_pc_export_wait_spec_2026-10-22_ja.mdは、LF版のSHA256が7e3eeac824f01601763a972af8eb85409753144ece93b3b087f030a4d91227df、CRLF版がfa3b29f52ff10ae33808e9602f25ea539d8a53b12c0f3e09e729b210157e3b0fだった。
CRLFをLFへ置換したバイト列が、前者と完全一致することを確認した。
C3T1 laboのserialは正常終了したが、親の終了後検証がLF版を要求して停止し、索引・転送・最終集約とC3T2 supervisorにも停止が伝播した。
元のLF版への復元後、後からCRLF版を固定していたC3T2監査と最終集約の待受4件も停止した。
この追加停止は復旧時の依存先確認の順序が不十分だったことによるものであり、その停止記録も保持した。
C3T2のsampling、native待受、DGX・labo待受とC3T1のDGX serialには入力不一致がないことを実ファイルで確認した。

## 復旧方法

[変換前のバイト列と復元記録](data_tile_validation_2026-10-17/control_newline_restoration_v1/restored.json) を保存した。
未知のhashは受け入れず、保存したCRLF版と復元したLF版の完全一致を検証する明示的な変換だけを許可した。
元のintent、停止記録、観測履歴、実行済みの成果物を削除・上書きせず、新しいcontrol_newline_recovery_v1配下へ接続した。
稼働中のPython sourceは変更していない。
C3T1 laboは全5バッチ・120群・10,560行のserial完了と割当、transfer記録、archive本体のhash・sizeを検証し、数値再実行なしで親の完了を復旧した。
C3T1の共有入力回収と保存済みreplayは、元の受理条件と固定入力を検証して再利用した。
索引の768群・67,584行の全分母検証、最終集約の元の算術検証、科学的な適用限界を保持している。
C3T2監査はcollector・audit操作がまだ試行されていないことを確認し、同じsampling jobの終了観測へ再接続した。
C3T2の3子プロセスはPID・コマンド・生成時刻を照合し、Windowsのprocess handleを取得して実終了codeを監視する。
子プロセスを再起動する経路は追加していない。
クラスタ操作は既存のqsub制御と共有slot制約を使用し、最大2要求nodeを維持する。

## 検証と実稼働

[受入記録](data_tile_validation_2026-10-17/control_newline_recovery_acceptance_v1/accepted.json) にsource 14ファイルと試験ログを保存した。
Windowsで20件の制御試験が成功し、実時間は3.59秒だった。
対象は既知の改行変換、未知の入力変更の拒否、完了範囲、元の科学設定・出力先の保持、PID再利用の拒否、停止前の操作未試行である。
数値科学コードは変更しておらず、この復旧用に新しい科学benchmarkは実施していない。
[実稼働とhashの観測](data_tile_validation_2026-10-17/control_newline_recovery_observation_v1.json) では、指定した24プロセス全てのPIDとコマンドを確認し、復旧intentが参照する848ファイルに不一致はなかった。
別途、元のC3T2転送待受PID42560と索引PID44396も実稼働し、停止記録がないことを確認した。

| 復旧した処理 | PID |
|---|---:|
| C3T1索引 | 35252 |
| C3T1転送待受 | 16348 |
| C3T1最終準備 | 45160 |
| C3T1最終実行待受 | 26316 |
| C3T1算術検証・候補作成待受 | 3756 |
| C3T2既存子プロセス監視 | 29984 |
| C3T2回収・監査待受 | 28788 |
| C3T2最終準備 | 40796 |
| C3T2最終実行待受 | 47492 |
| C3T2算術検証・候補作成待受 | 41160 |

## 継続状態と再現

08:56頃のクラスタjob265462はR・1要求node・経過6時間53分である。
C3T1 DGXは24/33バッチを回収済みで、24番目のremote PID1775720の正常なterminalと終了を確認した。
次batchへの進行は既存serial PID45416が担当する。
全低ノイズ条件の検証作業は依然10/12であり、残り2条件・全条件比較・独立計時・最終報告は未完了である。
sourceはoutput/control_newline_recovery_v1にあり、受入記録のsourcesにも同一バイト列を保存した。
制御試験はPython 3.11で `python -m pytest output/control_newline_recovery_v1 -q` により再実行できる。
復旧driverは一回限りの実行記録を保護するため、既存の出力先を指定して再実行しない。
今後の停止は実PID・job状態と成果物を調べてから扱い、観測timeoutだけを根拠に再投入しない。
この作業ではcommit・push・公開操作は行っていない。

## 09:03 JSTのcheckout変換防止

対象仕様書にはtext・eol属性がなく、ローカルのcore.autocrlfはtrueだった。
既存の.gitattributesはsourceと検証データをバイト単位で保護していたが、この仕様書は対象に含まれていなかった。
対象1ファイルにtext eol=lfを追加し、今後のGit checkoutによるCRLF変換を防止した。
[隔離したGit作業領域での検証](data_tile_validation_2026-10-17/line_ending_checkout_validation_v1/accepted.json) では、修正前のcheckoutが今回の不一致と同じCRLF版のhashとなり、修正後は元のLF版のhashを保持した。
この再現はGit変換経路が原因になり得ることを示すが、最初に変換を起こした具体的な操作は特定していない。
本作業領域の稼働中入力のバイト列は変更しておらず、隔離環境でもcommitは作成していない。
属性変更は未コミットである。
