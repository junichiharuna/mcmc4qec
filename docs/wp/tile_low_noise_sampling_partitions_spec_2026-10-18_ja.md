# 低ノイズ sampling 分割実装仕様

独立レビュー済み [仕様案](tile_low_noise_sampling_partitions_proposal_2026-10-18_ja.md) を実装の受入基準とする。
新 module は `tile_low_noise_sampling_partitions.py` と `submit_tile_low_noise_sampling_partitions.py` とし、旧 module を変更しない。
後続の analysis / trace audit / 最終 collection は別担当の明示的な multi-PBS 入口へ接続する。

`prepare(root, capacity_root, capacity_receipt)` は全 192 replicate の元 production plan と別の `sampling_partition_manifest.json` を新 root に保存する。
capacity_receipt は必要 field のみを持つ Jobs mapping とし、元 capacity job の F/exit0、元 ledger/script と結ぶ。
`read_plan(root)` は partition wrapper、元 plan、capacity 入力 hash、source、runtime、routing reservation を再確認する。
`tasks_for_partition(wrapper, phase, index)` は元 7 座標を返し、seed の再定義をしない。
`run_partition(root, phase, index)` は現在の PBS、submission intent/ledger/script、native、資源を確認し、元の task worker を呼ぶ。
`collect(root)` は qsub 内で各 job の終端と全 artifact を検査し、全予定 outcome を保存する。
`completed_partition_evidence(root, plan)` は集計済み metadata の読み取り入口とし、raw payload の再走査を行わない。

collection は `sampling-collection/summary.json` と全 task の `tasks.jsonl` に保存する。
completed evidence の必須 key は `mode=partitioned_sampling`、sample、anchors、input_sha256、source_sha256、pbs_jobs である。
sample は tasks、failed、group_record_digests、anchors は tasks、failed、record_digests を持つ。
input_sha256 の key は production root からの相対パスで、partition manifest、routing reservation、collection、全 partition intent/native/summary、全 submission/terminal/script を含む。
source_sha256 は追加 reader/runner と凍結済依存の絶対パスから hash への mapping とする。
pbs_jobs は phase、index、job_id、exit_status、completion_class の list とし、成功だけに絞らない。
task failure が全件記録された partition は終了 code 2 と completion_class=recorded_task_failures を使い、未完了と区別する。
全件記録された collection は failed task を残して complete=True となり得るが、sampling の成功や科学的精度を意味しない。

`source_files(*root_paths)` は指定 module の local import を AST で追跡し、basename→Path を返す。
引数省略時は新 runner と submitter を起点とし、function-local import も含める。
`source_hashes()` はその source closure の絶対パス→SHA256 を返す。
collector の metadata を後続で読み直すことと、full audit / 最終 adapter による raw payload 再照合を区別する。
既存単一 job CLI へ戻らず、後続との統合受入前に production sampling を投入しない。

collector も同じ新 submitter の `--phase collect` から投入し、1 CPU・32 GiB・2 時間を未計測の初期上限として使う。
collector 実行時は自分の ledger/script/bundle/Python と実 PBS ID を結ぶ。
自身の終端は実行内で確定できないため、終了後に軽い `seal-collection` で現在の F/exit0 と資源/script を照合し、必要 fields のみの terminal receipt を排他保存する。
completed reader はこの receipt を必須とし、`collector_pbs_job={phase:collect, job_id, exit_status:0}` とその input hash を返す。
sample/anchors の `pbs_jobs` は collector と混同せず、後続 submitter は両者の終端を確認する。
pool の異常や終端証拠の変更で incomplete になっても、既に保存された検証可能な task outcome を summary へ残し、存在しない task を科学的失敗に置き換えない。

2026-10-18 の Windows 軽量受入は 3 file 合計 65 passed、34.14 秒であり、重い sampling と qsub は未実施である。
四 case・三 target の各 8 step witness は既存 worker と分割 routing worker を別 root で実行し、全 array、seed、初期化を一致確認した。
この 12 witness の task 座標は全 kernel/init と replicate 0/95/96/191、先頭/末尾 chain を含む。
全 192 replicate・768 group の metadata contract fixture は明示的な 1 rung/1 chain の synthetic データであり、本番計画の代用や数値的校正とは扱わない。
capacity の hash/PBS/native metadata 異常受入では数値 record 検証と platform probe 境界を stub し、本番入口は既存の実 record validator と native validator を呼ぶ。
collector の全失敗分母、pool crash の未完了、読取中の summary/tasks/terminal 改変、同 bytes の解決先変更を個別に拒否/保存確認した。
本番 artifact 全走査、Linux 実 native preflight、最大 2 node の実投入と後続の全 scientific pipeline 完了は、この local 受入では確認していない。
