# flow v9 / finite outer のprivate追加保存

切替後のflow v9とfinite outerについて、qsub 265646でprivate snapshotを追加保存した。
F0・run_count=1・walltime 7秒・CPU time 6秒で、先行する9件のscope fixtureは0.044秒で成功した。
既存v8 private snapshotとv8共有候補は変更していない。
科学計算の完了、全依存の取得、別環境での実行、公開共有候補の生成は、この保存の成功とは別である。

| 保存内容 | 件数・サイズ |
|---|---:|
| source宣言 | 1,336 |
| metadata document | 179 |
| 元sealed envelope宣言 | 1,223 |
| one-hop edge | 48,890 |
| external record | 22,890 |
| 元source/metadata text | 30,484,980 bytes |
| private-source.zip | 5,527,469 bytes |
| private-metadata.zip | 1,984,549 bytes |
| 説明用private-authority.json | 778,239 bytes |

source数には旧v8の1,252宣言と追加84宣言が含まれ、alias・historical・validation sourceを保持する。
全sourceが実際の科学workerで実行されたという意味ではない。
metadataは旧112件を保持し、現行設定・受入・起動・切替・qsub等の67件を追加した。
新flow config、finite outerの7実sourceとdirect source_pins、family runtime、dynamic gate、新PBS wrapper、report環境、実native/assembly受入、旧controller停止と新launchを明示的に保存した。
worker/prepared対応は旧v8と同一であることを照合し、十二workerのqstatは採取時点の観測として別に保存した。
増加中のログ、raw/nativeの内容、巨大なmerge-resultや科学valuesは読み込まず、宣言済みhashと境界だけを外部referenceに残した。

初回qsub 265645は7 fixtureに成功しsnapshot本体を生成したが、最後の説明用authorityが4,433,802 bytesとなり4 MiB上限を超えてF1だった。
そのstage・source・中間snapshot・F1 terminalを保持し、受入済み実採取とは扱わない。
別source/version/stageで、source理由をpathとdocument roleの組ごとにまとめた。
詳細なJSON pointerは既存libraryのone-hop indexにすべて保持し、原本source/metadata pinや科学値は変更していない。
PBS wrapperにも4 MiB＋1 byteのbounded readを加え、2件の回帰fixtureを追加した。
独立source reviewでは具体的なblockerは報告されず、新版9 fixtureと実採取が265646で成功した。
4 MiB/fileと32 MiB/totalの上限は緩めていない。

保存先は `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v9-finite-snapshot-v2/` である。
以下のSHA-256は、識別子を含むprivate原本bytesを指し、識別子除去済みの本文のhashではない。

| 原本 | SHA-256 |
|---|---|
| accepted.json | `7c2bd3750529032d7e3d57429bfe379985129cd8741730ea6267ec3d2b74c45a` |
| terminal.json | `c3d422990374ca992793e86ead2be0641a04ee04a54b86cbef4b754763040dd3` |
| snapshot/receipt.json | `efe1892730e2c2e75d9d97e9798418dcae7f35ed89101ec12f79d80b43809aa5` |
| private-request.json | `3270907c42daab4eed411a806290555f9921c9b4dfa856ecb67ef7fc464510ad` |
| private-authority.json | `79d6a6275c58c38739ce93abdfecd897492cd1added9b52c1f31bf864585af3a` |
| snapshot/private-source.zip | `9116a517743217ee681da212c30500c0efd92ed4dfb15260a79f4312e44ae669` |
| snapshot/private-metadata.zip | `531ae8d8d6752751b8daea9b56531b931d76b90f59e530a2d4969d167207c47c` |
| scope-fixture-accepted.json | `488e377a09bf94e13baf6b46e6c5ee66b9c09e0664c7a80b7445f1712cb3d826` |

元のsnapshot library SHA `053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a` は変更していない。
新9 fixtureは薄いrequest builderとwrapperの受入であり、既存libraryの25 fixtureやv1 archiveの23 fixtureを新版全体へ拡大した主張ではない。
生成後のarchiveと大容量索引はクラスタに保持し、ローカルへは小receipt・terminal・fixture log・staging authority・時点観測だけを回収した。
one-hop indexは41,629,335 bytes、external indexは15,657,140 bytesで、ローカルで内容検索・解凍・再hashしていない。

実際に使用した4 sourceの同一bytesを `tools/reproducibility/collect_tile_v9_snapshot.py`、`test_tile_v9_snapshot_scope.py`、`pbs_tile_v9_snapshot.py`、`deploy_tile_v9_snapshot.py` に保存した。
元のstaging名は順にcollect.py・test_collect.py・run.py・deploy.pyであり、固定された原本の実行時importもこの名称を使う。
collector SHAは `4c2f1d728feb635e3efe9eb76ccfe4e2793211d28040d3b050c3eab80655cd68`、fixtureは `a0df7bd1d5e72012387059cb096805da9412040b243a443267649c8b76d50e28`、PBS wrapperは `72ce0b8f3842281b7732c6a23d380ad9fa28fdeeafc4e91aed88bfd35316d115`、deployerは `b131605fe60d014bb7ab81efcee35c93ef9ede14652f0e6ae0b8e0b4c5f5fdc2` である。
これらは固定private runの採取手順を保存するもので、既存stageを再利用して実行するためのportable CLIではない。

full_dependency_closure_complete・final_proofs_complete・scientific_reproduction_verified・publicly_distributableはfalseのままである。
v9の共有候補生成と識別子レビュー、公開upload、commitは未実施である。
識別子を含まない小receiptの原本bytesは `docs/wp/finite_flow_v9_snapshot_receipt_2026-10-25.json` に保存し、そのSHAは上記snapshot/receipt.jsonと同一である。
