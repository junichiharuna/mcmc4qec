# 並列workerの実行時import解決とruntime移設

2026-10-25時点の復旧仕様と検証記録である。
数値計算の完了記録ではない。

## 原因と変更範囲

第2版の12 workerは、実行用runnerと同じディレクトリに配置されたisolatedモジュールが、環境で指定した同名モジュールを隠したため、import元の照合で停止した。
Pythonはスクリプトの所在を`sys.path[0]`に置くため、別の準備スクリプトからrunnerを読み込むnative検証だけでは、この差を検出できなかった。
第3版では、既に受入済みの`runner.py`・`evidence.py`・`values.py`だけを新しい専用runtimeディレクトリへ同一bytesで移す。
環境、科学ソース、decoder、推定手順、既存の入力hashは変更しない。
isolatedモジュールは、環境が指定する`cluster_scripts`内の配置を維持する。
旧workerの失敗記録は保存し、第3版は新しいmanifest・prepared・実行ディレクトリを使用する。

移設前後の3ファイルについてbytesとSHA-256の一致を確認する。
新manifest・prepared・変換規則のafter pinは、実際に使う新runtimeのパスを指す。
変換規則のbefore pinは、初めの受入済みソースを維持する。
変換規則の厳密照合と環境のimport元照合を緩めない。

## 実スクリプトのimport環境を使うprobe

両計算ノードで、固定したPythonから実際のrunnerファイルを`-i --help`で起動する。
help終了後の同じインタープリターで、Pythonが設定した`sys.path[0]`を変更せず、実ファイルの関数とnative bootstrapを検証する。
実ファイルは`bootstrap.__code__.co_filename`で識別する。
旧配置でimport元の不一致が再現することと、新配置で全import元、native bootstrap、engineのmanifest検証が成功することを別々に記録する。
科学関数の差替え、import元の偽装、`sys.path`の手動変更は行わない。

これは対話検査モードのprobeであり、通常の`run-worker`全体を実行した証拠ではない。
第3版の準備receiptでも、通常workerの起動受入は未確認と明示する。
最初のproduction canaryで、実際のPBS実行状態、bootstrap後に保存されるexecution証跡、readerの起動、および起動エラーがないことを確認してから、残り11 workerへ展開する。
canaryの起動受入と、全12 workerの正常終了・値の受理は別の判定とする。

## 検証結果

| 検証 | 結果 | 範囲 |
|---|---|---|
| 最初のprobe 265547・265548 | F/1、各1秒 | 対話モードが`__file__`を除くことによるprobe自身の失敗で、bootstrap未到達 |
| 修正版probe 265549・265550 | F/0、5秒・6秒 | 両ノードで旧配置の不一致を再現し、新配置のnative bootstrapとmanifest検証に成功 |
| 第3版native準備 265551 | F/0、45秒 | 移設証明、両probeの終端証拠、新しい12 workerのresource・template・scriptを検証 |

原本のrequest、PBS終端情報、標準出力、標準エラー、receiptは非公開の実行証跡ディレクトリに保存する。
この表の成功を、production readerの完走、数値結果の正しさ、混合、bias、被覆の保証として扱わない。

## 子readerの入口も含めた第4版の検証

第3版のcanary 265553はmain側のbootstrapを通過してexecution証跡を保存したが、17秒でF/1となった。
子readerのCLIが置かれた元ディレクトリにも旧recoveredモジュールがあり、変更後の環境が指定するモジュールを隠していた。
main側の起動受入と子reader側の起動受入を分け、後者まで確認する必要がある。

全isolated reader 9環境について実CLIの所在を先頭にしたimport解決を列挙し、変更したrecovered 2環境だけに不一致があることを確認した。
残る7環境のimport元は一致した。
第4版向けには、既存の修正済みrecoveredモジュールとCLIを同一bytesで新しい2ファイル専用ディレクトリへ移す。
対象2環境のsource・resolved path・import元・Python検索パスを、実際に使用する配置へ更新する。
元環境からの変更はこの2モジュールの参照と、共通の新ディレクトリを一度だけ先頭に加える操作に限定する。
既に承認されたrecoveredモジュールの観測処理以外に、科学ソースを変更しない。

実CLIのprobeは、両ノードで旧2環境の不一致再現と新しい全9環境のnative bootstrapを行う。
子CLIのbootstrapが自身の`__file__`を検査するため、対話モードで除かれた属性だけを、起動済み関数の実ファイル名との一致確認後に復元する。
この復元と対話モードの使用を結果に明記し、`sys.path`、import元、科学関数は変更しない。
親PBS・親プロセスとの結合確認や数値readerの実行は、このprobeの検証範囲に含めない。
通常canaryではmainのexecution証跡だけでなく、子readerのbootstrap通過と読取り開始も確認する。

probe 265559はF/0・19秒となり、旧2環境の不一致を再現して、新しい全9環境のnative bootstrapが成功した。
もう一方の指定ノードは別所有者の96 CPUジョブで占有されたため、265560を待機状態のまま取り消し、未実行であることと前後のPBS状態を保存した。
空いている別ノードへ切り替えた265561はF/0・24秒となり、mainの2検査と子readerの11検査が成功した。
最初のノードの成功結果は再実行せず再利用し、新しいproduction対象の2ノードについてmainと全isolated readerの入口を検証した。
第4版の準備、通常canary、全12条件の完了は、それぞれ対応する実行証跡で別に判定する。
