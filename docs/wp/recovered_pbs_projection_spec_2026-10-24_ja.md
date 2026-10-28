# recovered readerのPBS照合形式修正

保存側の`low_bar_recovery_parent.observe`はPBS照会を8項目へ正規化する一方、利用側のrecovered readerは照会結果全体を返していた。
この形式差を解消するため、recovered readerの`observe`だけを保存側の`dependencies().parent.parent.observe`へ委譲する。
保存済みterminal、job ID、終了状態、終了コード、run count、実行script、要求資源、使用資源、error path、実行hostの検査を削除・緩和しない。
qstat全体のwrapperや稼働中環境の上書きは行わない。
新readerは別ディレクトリへ配置し、利用側環境のreader source hash・resolved path・import origin・PYTHONPATHだけを明示的に更新する。
Python実行ファイル、native binding、core、他の科学計算ソース、計算設定は変更しない。
旧reader・旧環境・旧manifestを保持し、稼働中workerの証跡を変更しない。

## 受入条件

元の保存側`observe`と元のsnapshot実装を使い、追加のqstat属性・timestampを含む照会結果でも保存済み8項目が同じ場合はsnapshotを受理する。
8項目の値の変更・欠損、別job・複数job・不正job ID、照会失敗、読取り中のterminal変更、封印済みファイルの改変は拒否する。
元readerでは正常系テストが失敗し、新readerでは成功することをPBS内で確認する。
AST照合により`observe`以外のreader構成が元ソースと一致することを確認する。
環境複製のテストでは変更箇所を限定し、native binding・core・他モジュールのpin・入力辞書が保存されることを確認する。
テストはローカルPCで実行せず、親driverがqsubで投入する。
この受入はPBS形式の整合性に限り、科学的精度・混合・被覆や全12条件の完了を保証しない。
