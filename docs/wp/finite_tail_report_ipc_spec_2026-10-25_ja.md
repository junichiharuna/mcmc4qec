# 有限PBS actionのreport内部IPC overlay

## 対象と境界

対象は固定report SHA-256 `affd3ccef29614ac4f79652f5dbb8fc7bac75667c69c099a82f3a8c5d2ce0750` の `partition_check` だけとする。
元source、既存environment、v8、科学設定を変更せず、新規source bytesを純粋変換で導出する。
元reportそのもの、または既存 `bridge_overlay.py` と同じbridge二箇所・runner2 hashだけの変更を元reportに逆変換できるsourceだけを受理する。
後者はbridge実bytesの逆変換SHAとrunner実bytesの固定SHAも検査する。
派生reportとenvironmentの新規pin・外部受理は呼出し側の責任とし、元environmentへ上書きしない。

## 保存する契約

`bridge.verify`、`proof.finish`、五つの結果項目、完全な `proof.files`、元Pythonのpin検査、bridge/runnerのpin検査を保存する。
子processのexecutable・stdin・env・cwd・thread設定を保存し、元の隔離されたmerge import contextを使う。
stderrの空白以外を拒否する条件、environment/filesの検査、戻り値、後段の各file再検査を保存する。
子processのstdoutに渡す完全JSONだけを、PBS scratch配下の呼出しごとの新規directoryの `proof.json` に移す。
子processは排他作成・flush・fsync後にpath/SHA-256/sizeの小receiptだけをstdoutへ出す。
親はPBS内でreceiptの上限・完全なkey集合・期待path・size・SHA-256を検査し、完全JSONを読んで元の戻り値を復元する。
proofを縮小・省略・科学的成功receiptへ置換しない。
artifactは呼出し終了後もscratch内に残し、失敗時も証跡を消さない。
scratchの保管期間はPBS環境に従い、恒久保存またはouter側の回収が済んだことを意味しない。
outerへ返すのは別のaction receiptだけとし、この完全戻り値をouter stdoutへ出してはならない。

## 有限時間と前提

`derive_report(base_pin, base_bytes, *, timeout_seconds, bridge_pin=None, bridge_bytes=None, runner_pin=None, runner_bytes=None)` はsource bytesだけを返す。
外部helper moduleやhelper importは加えず、sourceに固定した有限整数timeoutを使う。
timeoutは1秒以上86400秒以下とし、boolやfloatを受け入れない。
運用側はPBS walltimeと後処理余裕を考慮した値を明示的に選び、無制限待受へ変更しない。
実行時は `PBS_JOBID` を必須とし、`TMPDIR` があればそれを、なければ `tempfile.gettempdir()` の既定scratchを使う。
scratchは絶対・正規化済み・実在directoryであることを検査し、呼出しごとの新規directoryを作成する。
PBS allocationの真正性とwalltimeは共通worker側の責務であり、環境変数だけをallocationの証明とは扱わない。
120秒という固定値を除く科学検査を変更せず、実測前に十分な資源・時間とは主張しない。

## 受入と未実施事項

受入testは固定実sourceからの狭い変換、元検査・child program保存、改変source拒否、helper pin拒否、finite timeout、PBS必須・scratch fallback、完全proofの同値復元、artifact残存、receipt/path/size/hash改変拒否、元stderrとenvironment/files拒否条件を対象とする。
testは科学moduleをimportせず、抽出した実 `partition_check` と子process fixtureを使う。
testの実行と実metadataの時間・RSS計測は有限PBS actionで別途行う。
この変更の作成時点では、ローカルcode/test/science実行・qsub・remote変更は未実施である。
