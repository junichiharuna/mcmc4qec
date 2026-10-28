# v8 実行資料の private 保存結果

qsub 265617 が F / exit 0 / run_count 1 / walltime 6 秒で終了し、現行 v8 の有限 source・metadata snapshot を保存した。
固定された flow v8、front v6 の実12worker、並列 merge v6、tail v3 / config v8、新 report 環境、実 controller entrypoint と immutable launch 記録を対象にした。
旧 v5 snapshot は不変更で保持する。

保存した source は 1252 宣言 path、metadata は 112 文書、元 envelope は全1223参照、one-hop edge は31512件、external index は20518件である。
原本文字データは 23,371,439 bytes、private source ZIP は 5,265,785 bytes、private metadata ZIP は 1,241,260 bytes である。
元 v5 の1031 sourceを歴史的基準として保持し、221 pathを追加した。
現行 authority 文書が参照する source は543件で、保持した元 manifest の非担当 slot と歴史的検証用 source も含む。
543件すべてが実12workerで実行されたという意味ではない。
worker / prepared / 実job IDの対応を別に保存している。

受入済み snapshot_v2.py 原本を使用し、明示sourceの全件hash、metadata hash、同pathのpin矛盾、source aliasのtargetとbytesを前後検証した。
raw/native はcontentを開かず、再hashもしていない。
mutable な observations.jsonl は保存対象にせず、採取時点のPBS観測を新しいimmutable JSONへ保存した。
その観測は6件F・6件Rであり、後日の状態や最終科学結果を証明しない。

先行する qsub 265616 は production-ready のbyte pin照合で F / exit 1 となり、失敗記録を保持する。
ローカルの再直列化コピーはCRLFと末尾改行を含み、remote原本とJSON内容が同じでもbytesとhashが違った。
remote原本を変更せず、そのhashを使う新collectorと新stageへ切り替えた。
原本の来歴として265608の正常終端・受入source manifest・helper pin、265609の正常終端・native受入・request・実scriptを再照合し、deploymentとnative受入fieldsからproduction-readyを完全再導出して一致を確認した。
JSON同値を理由に旧pin検査を通す処理にはしていない。

保存先は `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v8-finite-snapshot-v2/` である。
`accepted.json`、`private-request.json`、`private-authority.json`、`snapshot/receipt.json`、二つのprivate ZIPと各indexを保存した。
各artifactの原本hashとサイズは[公開用の小証跡](reproduction_snapshot_v8_acceptance_2026-10-25.json)に記録する。
この小証跡のhash欄はクラスタ原本を指し、識別子を除いた公開版bytesのhashとは区別する。

公開用archiveはまだ作成しておらず、private ZIPをそのまま公開可能とは扱わない。
full_dependency_closure_complete、final_proofs_complete、scientific_reproduction_verified はすべてfalseである。
全12条件のmerge・独立計時・最終報告の完了証拠は、取得後に別の追加保存として扱う。
