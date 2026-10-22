# Tile288へ保存配列後処理を広げる前の確認

稼働中のC0T2用portable処理は変更しない。
`portable_bar_arrays_v1.py` の中核はsize 6/12、bit/depolarizing、logical_count 8を明示的に扱う一方、full driverはC0T2、full parity入口はC0T0の事前固定群だけを受理する。
再割当てrunnerもC0T2とtile72 geometryを固定しており、条件guardの削除だけで別条件へ流用しない。

今回の確認は、既存の凍結済み解析関数とdecoder構築を除いた変換関数について、tile72/288 × bit-flip/depolarizing × 低ノイズ3点の縮小配列上の一致を試す範囲である。
成功、保存sampling失敗、zero anchorを含め、数値・ACF・離散flag・未定義位置を既存の比較器で照合する。
変換後はdecoder factoryを例外に置き換え、呼出しがないことを要求する。
元関数のsource hash検査と明示geometryの検査を維持する。
このfixtureは実seed、実失敗集合、元環境のraw trace監査、PC上の本番parity、処理速度の検証ではない。

本番拡張には新しい条件の元環境データとmetadata、全設定の事前固定parity群、実host/runtime/sourceへのbinding、重複のない768群の割当て、専用driver・回収・最終readerの接続が必要である。
現在のC0T2の実行・割当て・回収を新条件へ読み替えず、元decoderのfailure labelを保存配列から引き継ぐ。
native decoder環境をまたいだlabelの混合を行わない。

## 縮小配列の実施結果

2026-10-20にWindowsのoptional環境で36 passed・13.49秒を確認した。
4種類の符号・noiseと低ノイズ3点それぞれで、通常結果、sampling失敗を含む結果、zero anchorを試した。
縮小配列は2 rung・4 chain・10保存点を用い、元関数と変換関数の数値・ACF・離散flag・未定義位置を既存比較器で照合した。
変換関数の実行時にはdecoder factoryを例外に置き換えており、呼出しがあれば失敗する。
元解析sourceのSHA-256 `4b2e4fa26ab54180dbdf4bc9cdfadd2cbe0781087037c84ac343def481080f7e` は変換ごとに検査された。
1テストファイルの実測時間は60秒以内であり、samplingや新しいqsubは行っていない。

[保存manifest](data_tile_validation_2026-10-17/portable_bar_tile288_readiness_v1/manifest.json)はsource・ログ・receiptの12ファイルを束ね、SHA-256は `f125036b5316a068291d6647796da7c85d738651b19aff3f65f6c8899b00507b` である。
[receipt](data_tile_validation_2026-10-17/portable_bar_tile288_readiness_v1/receipt.json)にはコマンド、条件範囲、元source hash、実行後の環境観測を保存した。
sourceのアーカイブはテスト後に作成したもので、実行中の全依存closureの封印やPC上での実parityを認定するものではない。
再現時は `sources/` 以下をrepository rootに対する相対配置として参照し、稼働中の固定sourceを上書きせず別checkoutで用いる。
実行コマンドは `python -m pytest output/portable_bar_tile288_readiness_v1/test_condition_arrays.py -q --durations=3` で、optional依存を備えたPythonを使用する。
Linux上でのこの追加fixture実行、tile288の実入力export、全設定parity、新driver・割当て・回収・最終readerへの接続は未実施である。

## 条件を明示する新しいparity入口

新しい入口は別directoryに置き、既存のC0T0 parity入口や稼働中のC0T2 driverを変更しない。
呼出し側はcase、target index、元production manifestのSHA-256、元sampling root、export archiveとexport manifestのSHA-256をすべて明示する。
各条件の照合群は事前に `(case, target_index, 0, 0, 0)` と固定し、実結果を見て別seed・kernel・初期化へ置き換えない。
production目的・192 seed・analysis stage 153、caseごとのsize/noise、3種類の物理p、元root、単独のreference付きexportを照合する。
固定した元sourceの全88設定を再計算し、referenceの全row・診断・ACF、flag・未定義位置を比較する。
群、方法、長いwindow、診断配列の欠落や重複を拒否する。
同梱sourceのimport先とbyte hash、既存変換helperとarchive readerの固定hash、single-thread設定を確認し、decoder factoryを禁止する。
成功・失敗とも一回の実行先へ保存し、既存出力を上書きしない。
この入口はparity専用であり、768群のdriver、科学cohortの受理、raw trace監査、referenceとの最終結合を代替しない。

## 条件入口の実装と受入

隔離した `output/portable_bar_condition_parity_v1/condition_parity.py` を実装した。
条件・元root・hashの取り違え、群と全設定の欠落・重複、未定義とsampling失敗の保持、CLIでの改変helper拒否・失敗記録保持・既存出力拒否を試した。
booleanや浮動小数点を整数のcondition identityと同一視するケースと、二重先頭slashのrootを失敗する受入で確認して修正した。
Windowsは49 passed・1.47秒、Linuxは49 passed・0.68秒で、Linux配置の4sourceはテスト前後にhashを照合した。
Linuxの軽量受入は新規の `/home/user/workspace/mcmc4qec/20261020-portable-condition-parity-v1` で実行し、既存bundleを変更していない。
CLIのhelpと拒否経路は実プロセスで確認したが、実入力を用いた成功経路の全設定parityは未実施である。
先の36ケースはWindowsでの縮小数値比較であり、この49件の入口検査と検証範囲を混同しない。

[保存manifest](data_tile_validation_2026-10-17/portable_bar_condition_parity_v1/manifest.json)は17ファイルを束ね、SHA-256は `cd3aea416bf28dd35ab57d68b2c8938484d7f8e7f2797857de31ff3b004116a4` である。
新しい入口sourceのSHA-256は `e182c6bb9b33243229ad3a374a8d53bbe1db542e09f3797eda556667e34b4bd9` で、既存の変換helperとarchive readerは元の固定hashのままである。
実施範囲は[receipt](data_tile_validation_2026-10-17/portable_bar_condition_parity_v1/receipt.json)に保存した。

次の候補C1T0は[事前固定identity](data_tile_validation_2026-10-17/portable_bar_condition_parity_v1/prospective_case1_target0.json)として群 `(1,0,0,0,0)` とproduction manifest `d2e3be26cc75202f15dc4bb1874fb0e210f906451d2cbb0522d4222e8441a06a` を元の生成準備へ照合した。
元rootは `/home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/runs/partitioned-full-1-0-v1` である。
元環境の全設定referenceとexport archiveはまだ用意しておらず、未取得hashを仮値で埋めた実行configは作成していない。
この候補を使う場合も、元環境でのreference作成と元入力の照合、新しいarchiveのpin、各hostでの成功parityを経てから、専用の全群driver・割当て・回収・最終readerへ接続する。
