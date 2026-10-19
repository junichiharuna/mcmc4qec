# C0T1復旧後の完了受理の準備

[復旧準備](low_c0t1_recovery_preparation_2026-10-19_ja.md)に続き、復旧jobが実際に必要になった場合の完了受理と、その保存記録を読み戻す入口を準備した。
元のv2 transportからimport先・control hash・対象root・証拠保存prefixだけを変更し、逆置換で元sourceに一致することを確認した。
数値処理、完了scope、元の復旧helperは変更していない。

完了受理は`output/complete_low_bar_recovery_c0t1_once_v1.py`、読み戻しは`output/low_bar_recovery_completion_record_c0t1_v1.py`である。
実際のprepareとexecuteの受理記録、job ID、script、input hash、実PBS終端を照合する経路を維持した。
mock SSHでの受入18件は2.43秒で通過した。
未実行・変更された入力・過剰な完了scope・曖昧なSSH応答を拒否し、既存証拠への再実行を拒否することを確認した。

実worktreeの記録を使った確認でも、まだ存在しないC0T1復旧prepareを検出し、SSH呼出し0・新しいcompletion成果物0で拒否した。
この確認で復旧jobを投入したり、実行中の元jobを完了扱いにしたりしていない。
265334と265338は引き続きR・run_count 1だった。

復旧が必要となるかは未確定であり、正常終了時は通常経路を使う。
復旧後の最終比較・report transportは、将来の実prepare/submission/completionとC0T1 trace・referenceに結び付ける必要があり、まだ未作成である。
完了受理が証明するのはjob終端・group marker等の指定scopeまでであり、全raw traceやreferenceの監査完了を意味しない。
