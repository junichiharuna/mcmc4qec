# 低ノイズ解析と全 trace 監査の接続仕様

`read_audited_collection(sampling_root, audit_root)` は既存 collection iterator を完全消費し、同一 production plan の full trace audit と結合して `(plan, rows, evidence)` を返す。
capacity は拒否し、192 replicate、768 group、各 group の全 rung/chain を要求する。
既存 plan reader、artifact reader、native probe を再利用し、PBS execution と qsub submission ledger、script、native evidence、summary、measurement、audit artifact の identity と hash を検査する。
audit failure、欠損、入力変更、context error は拒否する。
記録済み sampling failure は除外せず、task status、件数、解析 failed_tasks と照合する。
成功 task は全保存長、既定 checkpoint 数、初期状態と seed の確認記録を要求する。
解析 input marker と監査保存 input marker を全件照合し、現在の marker、JSON、NPZ を再 hash する。
anchor は解析が消費した marker と現在 payload の整合性を検査し、MC 再実行や全状態再復号とは扱わない。
読み込む全証拠と入力の hash を保存し、返却前に再照合して読込中の変更を拒否する。
lexical path と解決先を別々に記録し、内容が同じでも symlink の解決先変更を拒否し、各入力が所属する sampling/audit root の外への参照を拒否する。
既存 frozen source を変更せず、新 adapter の source hash を evidence に記録する。
全物理状態再復号、独立 decoder 正しさ、混合、精度、被覆の保証は行わない。
reference 監査はこの API に含めず、既存 comparison に渡すための collection evidence のみ提供する。
本番は全 trace I/O と native probe を伴うためクラスタで実行し、この実装作業では remote 操作と qsub は行わない。

受入は実保存 artifact による group 接続、payload 改変、marker 不一致、sampling failure の保存、task 欠落、全数条件と iterator 終端検査、読込中変更の拒否を含める。
native/PBS 環境と小さい計測時計は fixture とし、実本番完了の証拠とは扱わない。
768 group の制御フロー受入では I/O、group 検証、native 環境を明示的な fixture に置き換え、実保存 group の検証と既存 collection reader の全数終端検証を別の受入で行う。
この分解受入を全 768 group の実 artifact による本番通し検証とは扱わない。
