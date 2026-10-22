# C3T0の4時間collectorが時間切れになった場合の復旧仕様

2026-10-22 03:50時点でcollector265419は稼働中であり、失敗は確定していない。
この仕様は条件付きの準備であり、現在のjob・source・出力先・実行上限を変更するものではない。

## 起動条件と保持する範囲

復旧対象はcase 3・target_index 0だけとする。
実qstatが元jobのF・Exit_status -29・run_count 1、元script、1ノード・1 CPU・32 GB・4時間の要求を示した場合だけ復旧を検討する。
R・Q・観察不明・他の終了理由・成功終了では投入しない。
元の `sampling-collection-budget4h-v1` と `sampling-collection-submission-budget4h-v1` をその場で保持し、確定終端後に全ファイルの一覧とhashを固定する。
旧summaryが存在する場合は別の状況として停止し、本仕様の無summary時間切れとして扱わない。
旧途中行を成功した全collectionへ昇格せず、samplingとanchorを再生成せずに同じ全taskを新collectorで再検査する。

## 別出力先と検査

新出力先は `sampling-collection-retry8h-v1`、submission先は `sampling-collection-submission-retry8h-v1` とする。
要求は1ノード・1 CPU・32 GB・8時間を上限とし、所要時間の保証とは扱わない。
既存の2時間失敗からの復旧実装を基に、旧出力先、旧上限の検査、新出力先、新上限、対象条件の制約だけを別版にする。
元sampling source・plan・seed・task・分母・metadata検査・payload照合・二度目の全hash照合・native照合は維持する。
旧成果物は新worker実行の前後にも同一であることを確認する。
qsubは既存の共有lockと待機jobを含む最大2要求ノードの制御を通し、曖昧な投入応答や既存intentがあれば自動再試行しない。

## 受入と後続への接続

小さいfixtureで旧4時間終端の同一性、旧成果物の追加・削除・改変の拒否、R/Q/成功/別resourceの拒否、元関数の不変、新旧receipt混入の拒否、全768群・192 anchorの保持を検査する。
case 3・target 0以外、条件値の型違い、既存の復旧出力・曖昧な投入・共有lock競合・2ノード上限も受入対象とする。
Windowsでの受入後、Linuxで同じ受入を行い、固定source・config・確定した旧PBS終端・保存hashを結び付けてから実投入する。
全trace監査、portable解析、最終report、独立算術確認、計時candidate、次条件driverへの接続は、新しいcollectionを明示する別版で検証する。
旧失敗を正常終了に読み替えるfallbackや、既存driverへの出力偽装は行わない。
この後続接続と実PBS終端受理が終わるまでは復旧完了としない。

現時点では実jobの失敗確定、復旧context作成、native受入、復旧qsub、後続接続はいずれも未実施である。

## 条件付きcontrolsの受入

`output/collection_4h_timeout_recovery_v1/` に既存復旧実装とは別のcontrolsを用意した。
先に4時間終端と8時間の新枠を要求する受入を作り、旧実装に対する18件の失敗と、対象条件制約に対する10件の失敗を保存した。
変更後はWindowsで51 passed・16.72秒、Linuxで51 passed・8.83秒だった。
元sampling関数の不変、出力先のみのAST変更、新しい資源枠、旧成果物の保持、全768群と192 anchorの分母、新旧receipt混入の拒否、監査への明示的backend選択を合成fixtureで検査した。
qsubを置き換えたfixtureでは、共有lock・controller・要求ノード数・曖昧な応答・既存intentの制御を検査した。
case 3・target 0以外、boolや文字列の条件値、R/Q/成功終了・異なるresourceは拒否する。
Linux受入は既存bundleのPythonを使った合成fixtureの確認であり、実265419の失敗証跡を受理した実preflightではない。
この段階で実jobの失敗確定、復旧context、実preflight・qsub、後続controllerの接続は未実施である。
現jobと既存driverは変更していない。
