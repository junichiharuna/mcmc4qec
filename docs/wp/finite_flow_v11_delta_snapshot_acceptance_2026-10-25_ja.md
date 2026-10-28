# v11復旧差分のprivate追加保存

qsub 265662で8件のfixtureとv11運用差分の実snapshot採取に成功した。
実qstatはF/0・run_count=1・walltime 2秒・CPU time 1秒で、fixtureは0.065秒で成功した。
元ready SHA `c5fa82913f2a9b1dc4360761c5cafbbcbe0037749b4707539b050ed8378f827f` と固定source・資源を変更せず、merge 265660の終端後に後続ジョブを含むfresh shared gateが受理してから投入した。
要求資源は1 CPU・2 GiB・10分であり、保存専用の新submission adapterや偽のfamilyを追加していない。

| 差分保存内容 | 件数・サイズ |
|---|---:|
| source参照 | 474 |
| metadata document | 109 |
| one-hop edge | 1,506 |
| external record | 716 |
| 元source/metadata text | 5,075,914 bytes |
| private-source.zip | 1,615,118 bytes |
| private-metadata.zip | 140,336 bytes |
| one-hop-edges.json | 1,201,762 bytes |
| external-index.json | 469,616 bytes |

明示inventoryのmetadata106件・entrypoint23件を起点とし、指定prefixのsource参照と採取用metadataを追加した結果である。
source参照数はalias・受入fixture・歴史資料を含み、実科学workerで実行された全sourceの数ではない。
source版v10とactual config世代v11を区別し、alias修正、flow/config/migration、tail移設、265647–265659の受入・失敗・投入証拠、immutable起動証拠と265660の投入原本を保存した。
265660の科学的なresult、後続の科学証拠、可変journalは対象外である。
旧v9 snapshotを読み直して再構成せず、旧receiptとarchive宣言hashを参照で結ぶ別deltaとして保存した。
既存v8 private snapshot・v8共有候補・v9保存原本は変更していない。

独立レビューで指摘された265647・265652の相対source mapを各stage/test-rootへ明示し、203件・217件の展開先・SHA・scope包含をPBSで照合した。
相対base保持・不一致拒否、未指定baseの非推測、source改変と過大metadata拒否などを8 fixtureで確認した。
受入済みsnapshot libraryとv9 Scope helperを再利用し、各file 4 MiB・差分合計16 MiBの上限を維持した。
旧libraryの受入件数をこの新版全体の受入件数へ拡大していない。

取得起点は `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v11-control-delta-v1/` である。
以下のSHA-256はprivate原本bytesを指し、この識別子除去済み文書のbytesを指さない。

| 原本 | SHA-256 |
|---|---|
| accepted.json | `7b98b1637628e22759f9f83e1f4038cbbd4f019d5574c14501cdfe724d86edfb` |
| terminal.json | `9307633265d93281d17bb65f9bb2ab419479117a3e45aa83f809d78826bb6b46` |
| fixture-accepted.json | `1598d7510f838348a6992f67f662bbacdb20732408c5ecdcce0270219c796c9d` |
| snapshot/receipt.json | `d98ccffa2ae84897a8f009fcf668f5f0808c159d6505db4a4290f99298ade681` |
| request.json | `57bfeac17ee57ce5258a21ede2b8c6fb135be440c35d74e4c8edfc596c50cc6a` |
| snapshot/private-source.zip | `390e9f4ec026f9bc59c39ff950e9363e9b34862e1c97f9b075eb9baf4e815648` |
| snapshot/private-metadata.zip | `f335c7f761a8e1be09af5c797333b5e3072d180642c56979e0c0f1f208cf9ed9` |

identifierを含まないsnapshot/receipt.jsonの原本bytesを[小receipt](finite_flow_v11_delta_snapshot_receipt_2026-10-25.json)へ保存し、上表と同じhashを維持した。
archiveや索引の内容をローカルへ転送・解凍・再hashせず、小receipt・terminal・fixture log・request・ready・submissionだけ回収した。
新しい共有候補や公開URLは作成していない。

実使用した4 sourceの同一bytesを `tools/reproducibility/prepare_tile_v11_delta_snapshot.py`、`collect_tile_v11_delta_snapshot.py`、`test_tile_v11_delta_scope.py`、`stage_tile_v11_delta_snapshot.py` に保存した。
原staging名は順にprepare.py・collect.py・test_collect.py・stage.pyであり、固定sourceをそのまま保存した歴史的手順である。
source原本hashは順に `f7557db7e21d90241ebc370bcd4534825e6a73ef003fadc1157117043b3c5b46`、`8494c4d8e25d1645e0bc03fdb0401a5211f230c8374804de43c94a08cb736dc6`、`34b604edbf871f6a84ef592b181723faf825b37e140bd3ea43ef4d3c2a74fb66`、`d8b4cc10f9f60bd2fce18f875811055d99396d9fd4a6cad60a4de99377f80e6b` である。
元のsnapshot library・本番controller・固定source・worker・結果・資源配置を変更せず、controllerを再起動していない。

raw/native内容の読込・再hashは行っていない。
full_dependency_closure_complete・final_proofs_complete・scientific_reproduction_verified・execution_ready・publicly_distributableはfalseのままである。
この保存成功やmergeのF0を、比較・計時・全科学検証の完了とは扱わない。
