# v12復旧差分のprivate追加保存

qsub 265676で10 fixtureとv12復旧差分の実snapshot採取に成功した。
実qstatはF/0・run_count=1・walltime 1秒・CPU time 1秒で、fixtureは0.077秒で成功した。
既存shared physical gateがfresh censusを受理してから1 CPU・2 GiB・10分の保存ジョブを投入し、本番source・資源・profile・controllerは変更していない。
本番処理の再実行やcontroller再起動も行っていない。

| 最終保存内容 | 件数・サイズ |
|---|---:|
| source参照 | 94 |
| metadata document | 109 |
| one-hop edge | 1,509 |
| external record | 1,052 |
| 元source/metadata text | 1,374,712 bytes |
| private-source.zip | 286,778 bytes |
| private-metadata.zip | 151,658 bytes |
| one-hop-edges.json | 1,367,612 bytes |
| external-index.json | 742,537 bytes |

最終inventoryはmetadata106件・明示source22件・全宣言を検査するsource map6件である。
snapshotのmetadata109件には採取request・inventory・fixture受入の3件が加わる。
source参照には受入fixtureやalias・歴史資料も含まれ、実科学workerで実行した全sourceの数ではない。
6 mapのsource宣言数は順に4・4・16・17・3・4件であり、flowのmapだけ明示test-root相対baseを使い、残りはstage内の絶対pinを使う。
これらは全source宣言のscope包含とSHAを確認した一方、その他configのsource pinは有限prefixの対象だけを収集し、古い参照はexternalとして保持した。

対象はnamespace helper/authority/witness、observer source/authority/fixture/native、tail binding/dispatchの導出sourceと実config、flow source v11とactual config v12・migration・immutable launchである。
observer readyの原本SHAは `e498798f93748a0a9e07b04c520b04daba4b8c1b78f84b4e91e5f59cfdad5d21`、tail readyは `9db38edad846a9f1321a4a4f102d7b402662856716611e7505f26e9eb56c54b6`、v12 configは `083a22ca37fe46eb31f2f1034554f76aeffa77e77c273e33627e14e67318838e` に固定した。
265663–265674の投入・受入・terminal小原本を保存し、265663・265668・265669のF1も成功と区別して保持した。
この12件は全件run_count=1で、それ以外の9件はF0だった。
元merge265660・acceptance265661のcompletion/canonical accepted/terminal・claim・native preflight・submission・PBS start/end・job.shも小原本として保存した。
巨大merge-result・selectionの内容は開かず、その宣言hashと境界だけを残した。
以後のtail計時・科学検証の完了はこの保存の範囲外である。

独立レビュー対象の初版inventoryは105 metadata・SHA `1ad823efb546609e0798e0b2ef5ba4417d8b3837465126be45a15d4ffa6d054b` であり、その原本を保持した。
レビューで元acceptanceのPBS開始記録も補足する提案を受け、別v2のprepare.pyの固定一覧に1件追加した。
他のcollector・fixture・stagerのbytesはレビュー対象から変更していない。
最終inventoryは60,074 bytes・106 metadata・SHA `a26d02cf472943692f2453baf0f36ce7544995b120b5c5641329650019528741` で、このv2だけを本採取へ投入した。
追加原本は `$HOME/workspace/mcmc4qec/20261025-low-merge-terminal-acceptance-v1/actual-pbs-start.json`、2,316 bytes、SHA `c21b6aac2e086746126e5756223afc829a2b8118651327934fad0b23ab2bc6e1` である。
4 MiB＋1 byteのbounded readで実原本bytesとpinの一致を確認し、snapshot内でも既存libraryによる原本検証を行った。
初版105件の独立レビューと、最終106件のPBS受入・追加1件の照合を区別する。
追加1件は親agentも独立SSHで2,316 bytesと同じSHAを確認し、単一job 265661・保存時R/run_count=1・select 1 CPU/96 GiBのproducer記録との結合を確認した。
この独立確認でも巨大result/selectionは再読していない。
各file 4 MiB・差分合計16 MiBの上限は変更していない。

取得起点は `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v12-control-delta-v1/` である。
以下のSHA-256はprivate原本bytesを指し、この識別子除去済み文書のbytesを指さない。

| 原本 | SHA-256 |
|---|---|
| accepted.json | `73ee8a6534178fb2a5508490ebb8a6c3c4f3029863be5022b5d1ee05376dc4ec` |
| terminal.json | `4a0d137d07bea01f6032d03ee8f17eddcd74811ff7a079a5a63dc22be2a11b8f` |
| fixture-accepted.json | `5b3bc1f0529521c04e252eae12ba1780f2bd44d16ebd1cff96f4142f0f6d3121` |
| ready.json | `edf97b7835b9c518a4e31ab74e947d459f5f09a85610f04f124227f3f33d5c31` |
| snapshot/receipt.json | `f90afa5c73419cb10fc753b7cb7c8137a7114c2f5cd0e30243145524a271da10` |
| snapshot/private-source.zip | `cd03a1e8a0f4f812036c1c9321d9e95cb44cacd6935e502991855ce32e0fc244` |
| snapshot/private-metadata.zip | `917b4e77d7a5756cfdb6008edbdbcd4123000cf7c5599db677c58df102054ff4` |

識別子を含まないsnapshot/receipt.jsonの原本bytesを[小receipt](finite_flow_v12_delta_snapshot_receipt_2026-10-25.json)へ保存し、上表と同じhashを維持した。
原本archiveと索引はクラスタに保持し、小receipt・terminal・fixture log・request・ready・submissionだけローカル回収した。
v8/v9/v11の保存原本と既存共有候補は変更せず、過去ZIPの内容を再読・再圧縮していない。

使用したsourceの同一bytesを `tools/reproducibility/prepare_tile_v12_delta_snapshot.py`、`collect_tile_v12_delta_snapshot.py`、`test_tile_v12_delta_scope.py`、`stage_tile_v12_delta_snapshot.py` に保存した。
元staging名は順にprepare.py・collect.py・test_collect.py・stage.pyである。
原本hashは順に `25aea1eb82bdf3956a4deba948ee29fe70ef30481e12bcc07595014b50daad1a`、`dc4ebb4778ab75f39a3d015558d61a5e17d766766b82ea3a18a762462351f26c`、`bc44c6203c506f5ba7fd693180b915be867aafc96ac63317c49ef0205986a226`、`5c07983e33f8726a1a3a704acce86bbf302f6b2bca1b15a3e8fd2c6b5324b860` である。
既存Scope/libraryを再利用した新wrapperの10 fixtureであり、旧v11の8 fixtureやlibraryの受入件数を新版全体へ拡大した主張ではない。

raw/nativeを再hashせず、科学値や既存原本pinを変更していない。
full_dependency_closure_complete・final_proofs_complete・scientific_reproduction_verified・execution_ready・publicly_distributableはfalseのままである。
新たな共有候補、公開upload、commitは未実施である。
