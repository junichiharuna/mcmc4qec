# v13復旧source・controlのprivate差分保存

qsub 265701はF/0・run_count=1・walltime1秒・CPU時間1秒で終了し、10 fixtureとv13復旧差分のsnapshot保存を完了した。
fixtureの実測時間は0.080秒で、圧縮と原本照合を含む処理は全てPBS内で実行した。
既存shared gateの2回のfresh照合は、実行中265700の1 CPU・96 GiBと保存jobの1 CPU・2 GiBを、同じ1物理node内の合計2 CPU・98 GiBとして受理した。
最大2物理node・各96 CPUの制約と既存lockを維持し、本番job・科学設定・公開済み版を変更していない。

| 保存内容 | 件数・サイズ |
|---|---:|
| source参照 | 92 |
| metadata document | 217 |
| one-hop edge | 2,714 |
| external record | 1,718 |
| 元source・metadata text | 3,541,702 bytes |
| private-source.zip | 244,679 bytes |
| private-metadata.zip | 455,725 bytes |

保存対象は計測265677・265678、旧停止265675、初期fixture265679・265680、今回の最終157 fixture、旧readiness 14 fixture、専用環境・node・outer・recoveryの実組立、265699のnative検証、login readiness、v13設定・immutable launchである。
最終157 fixtureは7組の28・23・19・27・18・27・15件であり、nativeの13 constructorと今回のsnapshot用10 fixtureは別に数える。
nativeの13 caseについて、まとめのacceptedだけでなく各caseのaccepted原本も保存した。
source参照数には過去fixture・制御helper・複製sourceを含み、実科学workerで実行したsourceの数とは扱わない。

親agentが確認した初版inventoryはmetadata213件・明示source26件・metadata原文2,716,631 bytesだった。
8つのsource mapにある32宣言を全てscope内で解決し、件数は順に4・3・4・5・3・6・3・4件だった。
相対pathの1 mapは明示されたtest-rootだけを基準にし、その他は絶対pinを使用した。
この検査は新sourceの有限範囲の完全性であり、旧科学依存の全閉包を検証したものではない。

初版inventoryと旧observer copyを保持した上で、更新されたobserver sourceを別private pathへ追加した。
追加は1 sourceとその1 control記録に限定し、最終inventoryはmetadata214件・明示source27件となった。
snapshotのmetadata217件は、この214件に採取request・inventory・snapshot用fixture受入を加えたものである。
旧inventoryのSHA-256は `b42674bb175aec9c44e04f0c79ddd3c72a010918f9ba18ed0da744a07a8b7f46`、最終inventoryは `edba78b05e330eb59947cd9b526c0aa1eee2dfe471df7b930085752f27ea7cf5` である。
最新observer sourceは `379cd9094d1df40c2f82cf6e0c46a1df38f6ac70db6d390acf19bf22ad974f89` に固定し、元のcopyを上書きしていない。
ローカルのstart・observe・readiness deploymentの3 sourceも、repository相対の由来とともにprivate保存した。

265700については、最初のprepare actionのimmutable payload・PBS投入台帳・開始記録と、2026-10-25 10:19:22 JSTのqstat観測だけを保存した。
この観測時点ではRであり、以後の進行・終了・全件censusの完了を表す記録ではない。
capture原本のSHA-256は `c2ce8f4970fca4c79491ed177ac2739a8314636591432bc5511b8a2e193285b7` である。
変更中journalやlog、後から生成された本番manifestは今回のsnapshotに追加していない。

v12 snapshotのacceptedと小receiptを起点に、過去ZIPは宣言hashだけを外部参照として保持した。
過去ZIPの内容、科学bundle、raw/nativeデータ、result、selection、catalogは読取り・再hash・再圧縮していない。
明示pathだけを扱い、1 file 4 MiB・差分合計16 MiBの上限を維持した。
既存v12 collector、v9 Scope、snapshot_v2 libraryを再利用し、新しい汎用保存frameworkは追加していない。

取得起点は `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v13-control-delta-v1/` である。
以下のSHA-256は識別子を含む場合のあるprivate原本bytesを指し、この識別子除去済み文書のbytesとは異なる。

| 原本 | SHA-256 |
|---|---|
| accepted.json | `83de0c1400dcb695c386a7a7ec3cc8568cab140bfafd7b8bbd6d8fa3b4eb95b6` |
| terminal.json | `f3e3e546d9a092e27385e5c5d7e1ef606b7d83b89ee22c81b7045d7b91f08a59` |
| fixture-accepted.json | `9774d81e70e64190c0e8acbbdc62b4177c698ac59e59c99a981c060cf7d00467` |
| ready.json | `fb2c4728f1b96b4dbe2228c14814f20085b3c8b487a6ee7eaa5828406ad699ed` |
| snapshot/receipt.json | `919769a61d337cbe4adf56b16595915b89dfd3aa4d0ac994da646945b1e5449f` |
| snapshot/private-source.zip | `fa88a8ebf86d90ddaca7a4c3e53cec10103f9d14157d919164199e753126a9ae` |
| snapshot/private-metadata.zip | `940140b1bfd7a4ec27fa028011959b71bddcde008e44e80a6b3b5cf00c6033d5` |

識別子を含まないreceiptは[小receipt](finite_flow_v13_delta_snapshot_receipt_2026-10-25.json)へ原本bytesのまま保存した。
原本archiveはクラスタに保持し、小receipt・terminal・request・accepted・fixture logだけをローカル回収した。
実行sourceはクラスタの `output/reproduction_snapshot_v13_delta_v1/` とprivate-source.zip内にあり、ローカル作業原本も同名のoutputディレクトリに保持した。
source・control・baseline参照を復元するための有限snapshotであり、そのまま科学計算を再実行できるという保証ではない。
`scientific_reproduction_verified`・`full_dependency_closure_complete`・`final_proofs_complete`・`final_scientific_proofs_complete`・`execution_ready`・`publicly_distributable`はfalseのままである。
最終科学proofと今後の計時・報告結果の保存は未完了で、新規公開・公開用アップロード・commitは実施していない。
