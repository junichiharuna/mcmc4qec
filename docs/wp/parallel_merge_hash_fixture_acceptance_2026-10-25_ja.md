# Merge hash並列化のfixture受入

2026-10-25に、hash検査を省略せずsnapshot処理だけを並列化する独立候補を実装した。
小仕様、受入テスト、実装の順で作成し、実行中のflow、既存worker、科学engine、row計算、selectorは変更していない。
独立レビューは `parallel_merge_hash_review_2026-10-25_ja.md` にある。

## 実行結果

共有physical-node gateからqsubしたPBS job `265606` は、run_count=1、Exit_status=0、walltime=2秒で終了した。
要求は1ノード・8 CPU・4 GiB・15分で、fixtureのみを実行し、科学raw payloadは読んでいない。
旧fixture evidenceに対する18テストは0.750秒、実workerで使用した旧evidenceに対する同じ18テストは0.733秒で成功した。
36種類の独立テストという意味ではない。
これらは小fixtureの処理時間であり、全mergeの速度や所要時間の予測には使用しない。

確認範囲は、元worker validator bodyのsnapshotとconsumed-bytes SHAの実呼出数、同一pathの重複hash、登録順、phase barrier、最大8 threads・最大16未回収task、変更と誤pinの拒否、例外と待機interrupt後のdrainである。
新validatorのsourceロードなど、追加の運用hashは元入力集合のpath×phaseの回数とは別に扱う。
旧workerが記録したevidence source pinと、新validator自身のsource pinを分離した。

## 再現証跡

原本stageは `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/parallel-merge-hash-tests-v1/` である。
`accepted.json` のSHA-256は `a693966ee443b9aed22c80a2489d9ca11ca843ca3e94d8f99a6accf9a71377b4` である。
同stageの `request.json`、`submission.json`、`actual-terminal.json`、`fixture.stderr`、`actual_worker.stderr` に固定source、qsub記録、terminal状態、18件ずつの実行結果を保存した。
受入wrapperは終了コードを検査し、今回の18件ずつという件数は保存ログで確認した。
上記SHAは識別子を置換していない非公開原本を指す。

候補sourceは `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/output/parallel_merge_hash_candidate_v1/` に固定した。

| ファイル | SHA-256 |
|---|---|
| bounded_hash.py | `923476abcb04ed1093a07332ede4cf1360e390c729d74c96931c3406df0a6dd7` |
| worker_validator.py | `49f2d6bf101ce364f28b5171e40ae43d064d0be22fd8f82ea80823755913f067` |
| execution_adapter.py | `dbcb40d6d060f9727c3b690ac0523c218952809967d28dd18890ee6ecc2c14e2` |

## 残る統合受入

全merge経路の旧版との24行一致、元raw入力集合について主要loopが発生させる4*S+Uのpath×phase実count、実PBSの8 CPU検査成功前にparallel hashを開始しないことは未検証である。
ここでSはworkerごとのraw入力bytesを足した値、Uはそのpathの和集合のbytesであり、同内容でも別pathなら別入力として数える。
metadataの読込と追加運用sourceのhashは、このraw入力の式とは別に数える。
8 CPU execution adapterは新contractと新runnerの候補を生成するが、この記録は実mergeやcontrollerの移行を行った証拠ではない。
32 GiBでの全mergeのメモリ十分性と、実科学ファイルでの速度改善は未検証である。
