# report回収を有限PBS actionへ移すsource overlay

## 固定対象

元driver SHA-256は `1d3b5a7ab35e5deafdc6a2f3d9ee9908027695883a9d036e6ad6c1c5d2f6fcbd` とする。
元driverと既存実行環境は変更せず、このbytesからだけ新規driverとcollection sourceを導出する。
固定sourceの `main()` のtry本体で、`stable();sealed=call("seal",ctx)` に続く `artifacts=files(sealed)` から最後のprintまでを抽出する。
`files()` の固定sourceも抽出し、moduleに同名の別関数があってもその固定定義を実行する。
抽出対象はASTで構造を確認し、元sourceの文字列区間を切り出す。
科学的な行の削除や別実装への書換えは行わない。

## APIと実行境界

`extract_collection(source_pin, source_bytes)` は `files()` と回収suffixを結合した実際のcompile対象bytesを返す。
`derive_driver(source_pin, source_bytes)` は回収suffixだけを `call("collect",dict(ctx,ledger=ledger,sealed=sealed))` へ置換した新規bytesを返す。
直前の `stable()` と `call("seal",ctx)`、元の例外記録は保存する。
`verify_derivation(source_pin, source_bytes, derived_pin, derived_bytes)` は新規path・pin・完全な派生bytes一致を検査し、元driver・派生driver・実compile対象のSHA-256を返す。
`collect(module, ctx, ledger, sealed, stable, *, source_pin, source_bytes)` は固定抽出sourceをmoduleのglobalsのコピーと明示contextでcompile・execする。
元 `files()` の許容status・output名・evidence名・全path検査、全artifact転送とhash一致、descriptorとsubmissionの完全同値、`stable()`、completed保存、全fileのmanifest hash、最後の小printを保存する。
戻り値は元mainと同じ `None` とし、失敗は例外として上流へ伝える。
completedとmanifestの小pinが必要な場合は、元回収処理の完了後に共通workerが別途保存する。
実行時は `PBS_JOBID` を必須とし、実allocationの真正性と有限walltimeは共通workerで検証する。
この関数自体がqsubやremote actionをdispatchすることはない。
有限PBS workerへの `collect` routing、親terminal確認、transport、moduleの固定helper読込、DEST/JOB設定、実効 `stable()` の供給は共通coordinatorの責務とする。
workerは元のscp呼出しを実行するか、その完全commandだけを同一pin/pathのcopyへ写す検証済みtransportを供給する。
単なる無処理 `stable()` や未確認sourceのmoduleを実運用に使ってはならない。
既存stdoutのstatus/job_id/collection_verifiedは小receiptであり、report本文・seal全体・manifest全体をouter stdoutへ出さない。

## 受入

固定実driverのASTと抽出した全statement・`files()` ASTの同値を検査する。
派生driverの回収suffix以外のbytes保存、元source改変拒否、派生source改変拒否、新規originとpinの一致を検査する。
小さいfixtureで全file列挙・転送・hash・descriptor/submission比較・completed/manifest保存を通し、各失敗の拒否を検査する。
実運用の回収完了や出力hash一致はPBSで実行確認するまで主張しない。
作成時点のローカルcode/test/science実行、qsub、remote変更、commit/pushは未実施である。
