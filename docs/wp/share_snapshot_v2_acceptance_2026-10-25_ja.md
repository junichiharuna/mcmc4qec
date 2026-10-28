# 有限private snapshotの共有候補exporter受入

新形式のexporterを、仕様、専用fixture、実装の順に追加した。
対象はsnapshot_v2の保存済みsource・metadata・5 indexであり、外部raw/nativeの取得や完全な再配置ではない。
既存archive.pyの23 fixture成功は、この新形式の受入として数えていない。
コードと手順は `tools/reproducibility/` に保存し、公開uploadとcommitは行っていない。

## Fixtureと実入力を区別した結果

| PBS job | 対象 | 結果 |
|---|---|---|
| 265618 | 初版exporterの専用fixture | F0、run_count 1、26件成功、0.097秒、PBS walltime 1秒。 |
| 265619 | その時点で保存されたv8 private snapshotの共有候補生成 | F1、21秒。3 policy fixture成功後、source残留検査で停止し、共有ZIPは未作成。 |
| 265620 | 失敗したpolicyと保存source ZIPだけの限定診断 | F0、9秒。drive検出器の誤判定8件を確認。 |
| 265622 | revision2 exporterの専用fixture | F0、run_count 1、29件成功、0.101秒、PBS walltime 1秒。 |
| 265624 | 同じv8 private snapshotの共有候補再生成 | F0、run_count 1、PBS walltime 2分19秒。3 policy fixture、実build、公開bytes verifyが成功。 |
| 265627 | 全候補の識別子検査と限定review sample | F0、run_count 1、PBS walltime 38秒。既知policyの残留を全member名・本文で検査。 |

265620が確認した8件は、scpのhost:path、POSIX PYTHONPATHの区切り、source文字列のescaped newlineの末尾をWindows driveとみなした誤判定である。
初版の受入済みsourceを残し、revision2の差分をdrive検出の単語途中を除外する1行に限定した。
29件には、URL・scp指定・POSIX path list・escaped newlineの保持、未匿名Windows絶対pathの拒否、URL内のprivate literalの拒否を加えた。
この診断やfixture成功は、実候補全体の匿名化や科学的再現の成功を意味しない。

元receiptの外部SHA、固定7 artifactの元SHA、ZIP各memberの元SHA・bytesを検証する。
source・metadata・edge・external・envelope・receiptでは元hashと公開hashを分離し、埋め込まれた元pinを公開bytesへ偽装更新しない。
専用fixtureは、危険ZIP、重複member/key、size上限、原本hash不一致、redaction後key衝突、外部pathのopen/stat禁止、false scopeを含む。
テストと圧縮はすべて共有physical-node gate経由のqsub上で実行し、このPCでは実行していない。

## 固定した証跡

以下のstageは `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/` の下にある。
記載SHAは識別子を置換していないprivate原本を指す。

| stage / ファイル | SHA-256 |
|---|---|
| share-snapshot-v2-fixtures-v1/accepted.json | `f858ba3f0debc391af9e39c63a5937fd0571b95d0543e366b4076608827f4b29` |
| share-snapshot-v2-fixtures-v2/accepted.json | `c250c77af6313fb8728cf3a5cc2f3339e97473e9fc688849abd22d9cca78ecae` |
| 初版share_snapshot_v2.py | `59ef9288381fbe786f6f1147b85a6d87bf5da6d0c87e86d03b657544fd5ffa29` |
| share_snapshot_v2_revision2.py | `031b3cb08282c4ce383ad6284e0899733b92ca5dc55ddf33bcbdc27be82d7842` |
| test_share_snapshot_v2_revision2.py | `3fad16693a5b64c4fef604b957128c8224bc313931cadb26bd63125d24385824` |

失敗stage `share-snapshot-v8-candidate-v1` と限定診断stage `share-snapshot-v8-policy-diagnostic-v1` を上書きせず残した。
実候補の元snapshotは265617で保存したv8時点の有限scopeに固定し、後続controllerの差分に差替えていない。
未知・難読化された識別子やgeneric source sidecarの内容は、別の独立した識別子レビューを要する。
共有候補を生成しても `execution_ready=false`、`scientific_reproduction_verified=false`、`full_dependency_closure_complete=false`、`publicly_distributable=false` を維持する。

## 実共有候補

265624はsource1252参照、metadata112件、5 index、元receiptから1370 artifactsを共有候補へ保存した。
保存先は上記基準root下の `share-snapshot-v8-candidate-v2/shareable/` であり、公開download先ではない。
原本artifactを変更せず、外部raw/nativeを読み込まず、公開uploadも行っていない。
ここでのverify成功は公開bytesとmanifestの整合性であり、科学的再現や第三者環境での実行成功ではない。

| ファイル | bytes | SHA-256 |
|---|---:|---|
| finite-v8-sharing-candidate.zip | 9,137,857 | `aa2369d5d9bd106bc5568936cb6265ad709ebf82142ca97f01e9d52d2708bff8` |
| builder-source.zip | 22,184 | `c25db96bb8e8e07397366300a54162c406149acba44bc9b270396f49a1ebba41` |
| candidate-summary.json | — | `bea6d50b5a7475dfeb687a5aaf28304a22ba2ff9253c16771c4e630664d710e2` |

privateの `share-snapshot-v8-candidate-v2/accepted.json` は `9cf9a16e1c617ae67dc0710032fa1fd83bb4c97bb4651664e76b54ea7644e695` である。
policyの元本文と実job scriptはprivate記録へ保持し、共有候補ではpolicyとscriptのhashだけを記録した。
snapshot採取後に作った7 sourceはgeneric builder-source sidecarに元bytesで保存した。
sidecar内の架空fixture識別子と実識別子の区別を含め、独立した識別子レビューは生成時点では未完了である。

## 全候補検査と補助source保存

265627では1370 artifactsにmanifestとREADMEを加えた1372 memberを検査し、policyに宣言したprivate literalとescape表現のcase-insensitive残留は0件だった。
7 source sidecarは固定sourceとのbytes一致と余分memberがないことを確認した。
sidecarのgeneric文字列・fixtureの一致箇所は別に列挙し、実識別子との分類を独立レビューへ渡した。
保存source1252参照の既存64桁hash出現数、metadata112件の数値・bool・元hashの多重集合が一致した。
この比較は値とhashのcensusであり、位置ごとの科学的意味や完全再現の保証ではない。
各最大2000 bytesのredacted source、metadata、edge、external、envelope、README sampleをprivate audit stageへ保存した。

識別子そのものを含まない小reportを [share_snapshot_v8_candidate_audit_2026-10-25.json](share_snapshot_v8_candidate_audit_2026-10-25.json) に保存した。
原本reportのSHAは `478b066f33456b393d4b9d803cf4450c12865fe35fdbea8f0b6de1ef88dac3c2` である。
限定sampleやpolicyの実値は、この追跡reportへ転記していない。

後から作ったfixture受入wrapper、限定診断、全候補audit、初版exporter/test、手順READMEを7 memberの `operational-source-supplement.zip` に別途固定した。
保存先は上記基準root下の `share-snapshot-v8-identifier-audit-v1/` で、SHAは `102a4a9a3a943d0aadcedc7c2f6385dabea9b9ea6a3eb4285f02713bb6ce2b13` である。
memberごとの原SHAとbytesは小reportの `supplemental_source_manifest` にある。
補助ZIPは元候補や元sidecarを変更せず、private policy本文を含めていない。
補助sourceについてはsource読取りとpin照合の範囲を、元候補・sidecarの全走査と区別する。

その後、[独立レビュー](share_snapshot_v8_candidate_review_2026-10-25_ja.md)でsource読取り、PBS全候補検査、限定sampleの範囲を確認し、元候補と7 source sidecarにblockingな指摘は見つからなかった。
generic文字列とsynthetic fixtureの一致箇所を実アカウント・実ホストの混入と区別したが、未知秘密の不存在は保証せず、元candidateの未公開・非実行・非再現flagsを変更していない。
