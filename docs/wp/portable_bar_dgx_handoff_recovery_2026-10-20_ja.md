# DGX再割当てbatch 8後の引継ぎ復旧

既存pipelineはbatch 8起動後の回収準備で状態応答のJSON読取りに失敗した。
保存された例外は `JSONDecodeError` のchar 8192であり、当該応答のraw byteは保存されていないため、切断や切詰めの原因までは確定していない。
既存controllerは例外後も数値SSHの終了を待ってから停止した。
旧controller PID 4108が存在しないことを確認した。
再観測ではbatch 8の実PID 1496265が終了し、accepted=true・20群のcompletionが存在した。
38,198 byteの完全な状態応答を `data_portable_bar_2026-10-19/dgx-reassigned-8-recovery-observation-v1.json` へ保存した。

## 復旧手順

初回の回収準備は状態応答の読取り中に失敗し、local collection parentとpreparationは未作成だった。
両方が存在しないことを確認してから、既存の準備関数で実intentに基づくbatch 8の回収準備を実施した。
既存collectorによるbatch 8の回収・検証を行い、正常受理後にbatch 9〜13の既存割当てを継続する。
batch 9の入力準備は既存のexportと配置処理で行い、数値起動とは分ける。
batch 8の数値計算を再実行せず、失われたSSH終了codeを推測して記録しない。

## 再開adapterの契約

旧controllerのsource hashと実processの終了、batch 8の正常回収を確認してから再開する。
旧controller・error・completionの保存先は保持し、再開controllerの3記録だけに新しい名前を使う。
既存の割当て・数値worker・launch・collector・終端検証のsourceは変更しない。
read-only状態観測のJSON読取り・SSH失敗に限り、raw応答と例外を保存して最大3回再観測する。
部分応答を受理せず、全試行で失敗した場合は停止し、数値job・転送・回収を自動再実行しない。
batch 9以降の実行intentやhandleが既に存在する場合も、新規起動せず証跡を調査する。
新adapterのsourceも実行中のhash検査へ加え、旧controllerのpinは書き換えない。

## 実施結果

部分JSONの保存と再観測、3回失敗時の停止、timeoutの扱い、不正schemaの拒否、3つのcontroller記録だけの保存先変更について、5 passed・0.39秒だった。
batch 8の20群は既存collectorでtransfer_verified=true・batch_accepted=true・infrastructure failure=0として回収した。
batch 9の元archiveは279,116,989 byte・14,577 member・20群で、元クラスタからの転送とDGX上のhash確認を完了した。
再開controller PID 45340は旧sourceのpin一致と旧controller processの不在、batch 8の正常回収を確認してbatch 9〜13を開始した。
batch 9の実PID 1547853がlive・terminal=falseであることを観測し、`dgx-reassigned-9-resume-live-v1.json` へ保存した。
この観測はbatch 9の終了や後続batchの成功を示すものではない。
新controllerは `output/portable_bar_reassigned_resume9_run_v1.log` に進捗を記録し、実数値processのSSH handleを保持する。
旧controllerを再起動せず、新controllerや回収処理の一度限りの操作も重複実行しない。

source・受入ログ・旧失敗記録・回収と再開の証跡を[50ファイルのmanifest](data_tile_validation_2026-10-17/portable_dgx_resume9_v1/manifest.json)へ保存した。
manifest SHA-256は `f49424897e960eb59fbe150650ef2fcd1467c436f863d82249c138fe2bbfdeee` である。
実行中の可変logはこの保存物に含めず、再開時点の観測と後続の進捗を区別する。
