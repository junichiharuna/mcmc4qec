# 利用者が取得できる再現資料と不足の監査

GitHubは2026-10-25 03:05:31 JSTの読取りAPIで確認し、private保存は265617の受入receipt、共有候補は265624の生成・265627の全候補検査と独立レビューまで追記した。
確認対象は小さい既存文書・metadata、限定したファイルの所在・サイズである。
生データやnative binaryを読み込まず、数値計算・ローカルテスト・新規公開・commitは行っていない。
GitHubの確認対象とasset名・数・宣言hashは[読取り証拠](reproduction_public_access_observation_2026-10-25.json)に保存した。
この文書は全raw入力の完成した配布索引ではなく、実在する取得起点と未確認事項を分けた監査である。

## 公開済み資料の取得

[公開main](https://github.com/junichiharuna/mcmc4qec/tree/837a96b8836ba8c81043fcba15b065eb1a8b5296)は確認時点で `837a96b8836ba8c81043fcba15b065eb1a8b5296`、Releaseのtag `v0.1.0.dev5` は `c27ca896a1025c74975bc45322798eea2e0409b0` を指す。
mainとtagは異なるため、同じcommitとして扱わない。
repositoryはpublic、[Release](https://github.com/junichiharuna/mcmc4qec/releases/tag/v0.1.0.dev5)はdraftではないprereleaseで、添付物は次の5件だった。

| 配布物 | bytes | 取得先 |
|---|---:|---|
| source ZIP | 33,750,089 | [mcmc4qec-0.1.0.dev5-source.zip](https://github.com/junichiharuna/mcmc4qec/releases/download/v0.1.0.dev5/mcmc4qec-0.1.0.dev5-source.zip) |
| wheel | 93,199 | [mcmc4qec-0.1.0.dev5-py3-none-any.whl](https://github.com/junichiharuna/mcmc4qec/releases/download/v0.1.0.dev5/mcmc4qec-0.1.0.dev5-py3-none-any.whl) |
| 配布manifest | 854 | [manifest.json](https://github.com/junichiharuna/mcmc4qec/releases/download/v0.1.0.dev5/manifest.json) |
| Release本文 | 4,734 | [release_body.md](https://github.com/junichiharuna/mcmc4qec/releases/download/v0.1.0.dev5/release_body.md) |
| SHA-256一覧 | 366 | [SHA256SUMS.txt](https://github.com/junichiharuna/mcmc4qec/releases/download/v0.1.0.dev5/SHA256SUMS.txt) |

source ZIPの宣言SHA-256は `ea6b535789f584d138391f209bc8d17ae97d0d84929e1e93e0fd170f53407487`、wheelは `98a70792c8e9a51a131c0ff6117180d7b28eccd7f00ef5f144566f6ca7c093ed` である。
今回の監査はAPIのasset metadata確認であり、配布物本体の再download・再hashは行っていない。
以前の公開時のdownload確認範囲は[公開結果](publication_result_2026-10-24_ja.md)に記録されている。

公開treeに、tile factoryとBP-OSD・BP-LSD・BeliefFind・Union-Findの実装、次の利用例、API、tutorialが存在することを確認した。

| 利用者の目的 | 公開済みファイル | 現在の範囲 |
|---|---|---|
| tile72の導入例 | [tile_bposd.py](https://github.com/junichiharuna/mcmc4qec/blob/837a96b8836ba8c81043fcba15b065eb1a8b5296/examples/tile_bposd.py) | bit-flipの短い直接MC・条件付きMCMC例。主校正のorder10とは異なる。 |
| tile72/288の固定prior BAR | [tile_capacity_fixed_prior.py](https://github.com/junichiharuna/mcmc4qec/blob/837a96b8836ba8c81043fcba15b065eb1a8b5296/examples/workflows/tile_capacity_fixed_prior.py) | bit/depolarizingを選べるが、目標pはサイズ別の固定値で、正式低ノイズselectionを再生するCLIではない。 |
| 基本decoder比較 | [decoder_comparison.py](https://github.com/junichiharuna/mcmc4qec/blob/837a96b8836ba8c81043fcba15b065eb1a8b5296/examples/decoder_comparison.py) | Steane・toric・tile72のbit-flip例。追加decoderのBAR校正を再現するものではない。 |
| 自分の問題への接続 | [API](https://github.com/junichiharuna/mcmc4qec/blob/837a96b8836ba8c81043fcba15b065eb1a8b5296/docs/api_en.md)、[tutorial](https://github.com/junichiharuna/mcmc4qec/blob/837a96b8836ba8c81043fcba15b065eb1a8b5296/docs/tutorial_en.md) | 公開libraryの契約と使い方。cluster固有の校正環境の複製ではない。 |

取得したsourceを使う導入手順はRelease本文の `python -m pip install '.[bposd,codes]' 'ldpc==2.4.1'` とquick例にある。
この監査では実行しておらず、利用例の成功を本研究の混合・精度・被覆の再現とは扱わない。
例の詳しい制限は[符号・decoder・利用例監査](code_decoder_examples_audit_2026-10-25_ja.md)を参照する。
公開確認後にlocalのtile workflowへ `--ladder` を追加し、[PBS受入](tile_example_target_cli_acceptance_2026-10-25_ja.md)で任意目標の結線を確認したが、上表の公開commitやv8共有候補へ反映済みとは扱わない。
公開treeには `reference_summary.json`・`reference_audit.json` 等の選択された集計もあるが、Release本文は完全なraw trace・WSS datasetを含まないことを明記している。

## private source snapshotと現行再現手順

クラスタworkspaceを `$HOME/workspace/mcmc4qec` とし、以下はその下の相対パスで示す。
クラスタへの既存アクセス権を持つ担当者向けの所在であり、第三者がdownloadできるURLではない。

| 資料 | 実在する取得起点・量・既存hash | 取得できる範囲と不足 |
|---|---|---|
| v5 source snapshot | [receipt](reproduction_snapshot_v2_acceptance_2026-10-25.json)の `original_evidence_root`、その下の `snapshot/private-source.zip`。4,794,453 bytes、SHA-256 `95a725674f9c6fbd17e520fd8aea42b7d1aa953fa06a7d88adaa7528044cc76c`。 | source1031参照のprivate保存。公開ZIP未作成。利用者の直接取得経路・利用条件・保存期限は未確認。 |
| v5 metadata snapshot | 同じrootの `snapshot/private-metadata.zip`。772,213 bytes、SHA-256 `9a4d1c4b5e1ce482875295215104aee5846da6fde65c2d8114941574f87f439b`。 | 明示した75文書のprivate保存。過去の全metadata、最終proof、raw/native bytesを含む完全閉包ではない。 |
| v5の外部入力索引 | 同じrootの `snapshot/external-index.json`。9,871,229 bytes、SHA-256 `e78ecc15de438d6f15fc7d66fced8bafd01d94610be5d0780577ab0cea0d5ce4`。 | 14,420 external recordsを記録。今回はreceiptだけを読み、index本体・raw/nativeの内容は読んでいない。宣言hashとstatだけでは取得成功や永久保存を保証しない。 |
| v5の参照関係 | 同じrootの `snapshot/one-hop-edges.json`。17,766,549 bytes、SHA-256 `bcd3896c8a6fa4339170d465c7fdc9be196d11a293edfdce53af310be92992f8`。 | 19,692 edges。明示scope外の参照もあり、完全な依存閉包・科学的再現は未達。 |
| v8時点の有限snapshot | [保存結果](reproduction_snapshot_v8_acceptance_2026-10-25_ja.md)と[受入receipt](reproduction_snapshot_v8_acceptance_2026-10-25.json)。265617はF/0・run_count 1・walltime6秒でsource1252参照、metadata112件、envelope1223参照、edge31512件、external20518件、原本文字23,371,439 bytesをprivate保存した。 | 先行265616の改行hash差による失敗を残し、別stageの正常終了証拠を確認した。この原本に固定した共有候補を265624で生成し、265627の全候補検査と独立レビューを完了したが、未公開・未配布である。後続control差分・最終proofは含まない。 |
| 現行のクラスタ再開手順 | [常駐処理確認](cluster_resident_resume_2026-10-25_ja.md)と[成果物監査](final_deliverable_audit_2026-10-24_ja.md)。 | 既存クラスタのconfig・journalを読む具体的手順。公開mainにはこの再開文書も `tools/reproducibility/README.md` も存在しないことを確認した。 |

v5の元rootは `20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-snapshot-v2-actual-v2` である。
v8の元rootは `20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v8-finite-snapshot-v2` である。
v8の `snapshot/private-source.zip` は5,265,785 bytes・SHA-256 `4236249124a9ae60da31e3809500d047a28a061d5e66ac6defdfc6900193ca11`、`snapshot/private-metadata.zip` は1,241,260 bytes・SHA-256 `e607c91a19d5569673320eed04a3045ac89ed3b00c0c23722006ec7623ce12e1` である。
v8の `snapshot/external-index.json` は14,033,364 bytes・SHA-256 `0939be693821d291d14ecbdc98ef61073e5cd84b125975f771eddcde7440e5ff` で、他のmember/indexのサイズとhashも受入receiptにある。
これらは原本hashであり、公開用の小証跡自体のbytesのhashではない。
v8で保存した参照には歴史的な検証sourceや非担当slotも含まれ、source1252参照全てが現行12workerで実行されたとは扱わない。
raw/nativeの再hash、全依存閉包、最終proof、科学的完全再現は未達である。
権限を持つ担当者は、receiptの原本hashと `snapshot/source-members.json`・`metadata-members.json` を起点に該当ZIPを特定できる。
今回その転送は実行しておらず、private ZIPをそのまま第三者へ渡せるとは判定していない。
共有用コピーには識別子処理と原本hash／共有後hashの対応、参照先へのアクセス案内が必要である。
[tool README](../../tools/reproducibility/README.md)の `archive.py build`・`verify` は別形式のv1 inventory用であり、現在のv2 snapshotへそのまま適用できる処理ではない。
v2 snapshot用の専用exporter revision2は29fixtureを受入済みで、265624で実共有候補の生成・内部verifyを完了した。
[生成記録](share_snapshot_v2_acceptance_2026-10-25_ja.md)と[独立レビュー](share_snapshot_v8_candidate_review_2026-10-25_ja.md)は、候補保存・確認範囲と公開配布・科学的完全再現を区別している。
同READMEは `execution_ready=false`・`scientific_reproduction_verified=false` とし、自動再配置・再pin runnerは未実装と明記している。
これらのファイルはローカルにはあるが今回の公開mainにはなく、利用者が通常cloneで取得できる再現手順としては未提供である。

共有候補の保存先はworkspace相対 `20261024-c3t2-index-relocation-v1/pipeline-submissions/share-snapshot-v8-candidate-v2/shareable/` であり、既存クラスタ権限を持つ担当者が以下のファイルとmanifestを取得できる。
以下のSHA-256は候補の共有用bytesを指し、上記private原本のhashとは異なる。
候補manifest内でも元hashと共有後hashを分離し、埋め込まれた元pinを共有後bytesへ偽装更新していない。

| 保存済み共有候補 | bytes | SHA-256 |
|---|---:|---|
| finite-v8-sharing-candidate.zip | 9,137,857 | `aa2369d5d9bd106bc5568936cb6265ad709ebf82142ca97f01e9d52d2708bff8` |
| builder-source.zip | 22,184 | `c25db96bb8e8e07397366300a54162c406149acba44bc9b270396f49a1ebba41` |
| candidate-summary.json | — | `bea6d50b5a7475dfeb687a5aaf28304a22ba2ff9253c16771c4e630664d710e2` |
| builder-source-manifest.json | — | `0a164ca6c3f60fd05e58d620db50c267ed3ea550d49a7e8084c6b88c4cc35398` |

265627では候補全1,372 memberの既知private literal残留0件と、sidecar7sourceの固定bytes一致を確認した。
独立レビューはgeneric文字列・synthetic fixtureの一致を実識別子と区別し、source読取り・PBS全候補検査・限定sampleの範囲でblockingな指摘を見つけなかった。
この結果は未知秘密の不存在や署名付きの出所証明ではなく、`publicly_distributable=false`・`execution_ready=false`・`scientific_reproduction_verified=false` を維持する。
候補は265617のv8時点に固定され、後続control差分、全12条件の最終受理、独立計時、最終reportの完了proofを追加済みとは扱わない。
別保存の `operational-source-supplement.zip` はworkspace相対 `20261024-c3t2-index-relocation-v1/pipeline-submissions/share-snapshot-v8-identifier-audit-v1/` にあり、SHA-256は `102a4a9a3a943d0aadcedc7c2f6385dabea9b9ea6a3eb4285f02713bb6ce2b13` である。
この補助7sourceは静的読取り・pin照合の対象であり、元候補と同じ全policy literal検査を実施したとは扱わない。
共有候補と補助物はいずれもprivate所在で、第三者向けdownload URLは未提供である。

後続のfinite flow v9は、[専用保存結果](finite_flow_v9_snapshot_acceptance_2026-10-25_ja.md)と[原本の小receipt](finite_flow_v9_snapshot_receipt_2026-10-25.json)に別保存した。
265646のF/0でsource1336参照・metadata179件、private source ZIP 5,527,469 bytes・metadata ZIP 1,984,549 bytesを保存し、既存v8共有候補は変更していない。
source参照数を実行sourceの全数とせず、v9はprivateな追加保存であり、公開配布や全raw保存へ読み替えない。
さらにv11復旧差分をqsub 265662のF/0で追加保存し、8 fixtureと実採取が成功した。
[保存結果](finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md)と[小receipt](finite_flow_v11_delta_snapshot_receipt_2026-10-25.json)にsource参照474件・metadata109件、private source ZIP 1,615,118 bytes・metadata ZIP 140,336 bytesを記録した。
稼働中のunbound mergeを既存gateの偽familyで通さず、終端後の後続ジョブを含むfresh shared gateが受理してから投入した。
v9 ZIPを再読せず、別private差分として参照で結び、v8共有候補も変更していない。
v11差分には科学resultや全rawを含まず、科学的完了・完全な依存閉包・第三者向け公開配布を保証しない。

さらにv12のnamespace/observer/tail/flow復旧差分をqsub 265676のF/0で保存した。
[保存結果](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)と[小receipt](finite_flow_v12_delta_snapshot_receipt_2026-10-25.json)にsource参照94件・metadata109件、private source ZIP 286,778 bytes・metadata ZIP 151,658 bytesを記録する。
元merge/acceptanceの完了を示す小原本と失敗試験3件も収録したが、巨大result/selection・raw/nativeや過去ZIPは開いていない。
v11以前の保存を不変の参照基準としたprivate差分であり、tail計時や全科学検証の完了を意味しない。

## v13と後続の完了成果物（2026-10-25追補）

以下は上記v8共有候補・v12差分の後に保存した資料であり、公開mainやReleaseへ追加済みとは扱わない。
各リンク先の保存範囲と原本hashを引き継ぎ、この索引の更新ではarchiveや科学payloadを読み直していない。

| 資料 | 保存先・取得起点 | 範囲と残作業 |
|---|---|---|
| v13復旧source・control差分 | [保存結果](finite_flow_v13_delta_snapshot_acceptance_2026-10-25_ja.md)と[receipt](finite_flow_v13_delta_snapshot_receipt_2026-10-25.json)。クラスタworkspace相対 `20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v13-control-delta-v1/` の `snapshot/private-source.zip`・`snapshot/private-metadata.zip`。 | qsub265701のF/0でsource92参照・metadata217件を保存済み。265700の10:19:22 JSTのR観測までの有限差分であり、後続のcensus完了・独立計時・最終報告は含まない。 |
| 全件seed照合と正式受理 | [原本resultと保存説明](data_tile_validation_2026-10-17/low_timing_full_census_v13_20261025/README_ja.md)。同説明にcluster原本root・descriptor・journal completed/manifestの所在とhashを記載。 | 4,208,002件の検査と265703・265707・265708のF/0、回収原本の一致を確認済み。小resultはworking treeに保存したが、private原本への第三者アクセスや独立計時の完了は含まない。 |
| 設定選択の24行表と再現source | [保存directoryの案内](data_tile_validation_2026-10-17/accepted_selection_projection_v1_20261025/README_ja.md)と[原本・共有後hash対応](data_tile_validation_2026-10-17/accepted_selection_projection_v1_20261025/copy-manifest.json)。 | 265705の18 fixtureと265706の実抽出がF/0。22小ファイルに表・元field対応・受入・投入・source・fixtureを保存済み。識別子置換済みrequestは参照用で、そのまま実行できず、private元selection等が別途必要。 |

24行表の12選択行は全て診断flag192/192、残り12行はreference区間幅により非選択であり、推奨設定や独立校正の成果物として配布説明しない。
これらの完了証拠を含む最終差分保存と、独立計時・最終報告の成果物への取得起点の追加は未完了である。
既存の公開資料、working treeの小成果物、クラスタ権限が必要なprivate原本を分けたまま最終引渡し表へ統合する。

## 生データと集計の具体的な取得起点

下表のhashは既存証拠が示す原本hashであり、今回再計算した値ではない。
ローカルにある大容量archiveは名前とサイズだけ確認し、内容を開いていない。
全体の保存期限・第三者提供の利用条件は、下表のどのprivate datasetでも未確認である。

| 対象 | 実ファイル・形式・量・既存hash | 現在の取得方法と欠落 |
|---|---|---|
| 主4条件の直接MC | [reference_audit.json](data_tile_validation_2026-10-17/reference_audit.json)とlocal `reference_archive_verification.json`。1,248 artifacts・3,750 filesで、後者はchunksのJSON・NPZ・done JSONごとのhashを持つ。archive SHA-256 `58a83c8958fada5887e5ccb37ce4a6f0ac554023f20e73efeac1bd062bb39933`。追加の限定stat確認でrepository相対 `output/tile_validation_recovery/reference-artifacts.tar.gz` の存在と7,814,608 bytesを確認した。 | 公開mainからsummary/auditを取得できるが、archive verificationと対応するraw archiveの公開取得先は確認できない。今回のstat確認はarchive内容の再hashではなく、現在のbytesが既存hashと一致することを再検証していない。 |
| 主4条件のsampling・analysis | [raw保存監査](raw_preservation_audit_2026-10-25_ja.md)にsampling4件・analysis4件の現local archive相対パス、stat容量、既存回収hashを整理した。全8 archiveの存在と容量を明示パスのstatで確認し、analysis各caseは既存receiptで768 group・2,315 files。 | 私有PC上の保存物への取得起点があるが、公開download、別媒体backup、提供条件・保存期限は未確認。samplingと派生analysis、存在確認と内容照合、現在のpayloadと過去のconsumed hashを区別する。 |
| 固定16条件のWSS | local `docs/wp/data_tile_validation_2026-10-17/weight_reference_recovered_v1/evidence.tar.gz` の存在と608,476,985 bytesを確認。gzip level1、23,954 artifacts・71,904 files、raw chunks23,938。SHA-256 `5650c33310cabfaea17a91c6185007631bbfede70a7fb613e2670828de4da476`。 | [回収終端記録](data_tile_validation_2026-10-17/weight_reference_recovery_terminal_validation_v1.json)と同directoryの `export.json`・`recovery.json`・`input_sha256.json` が原本との対応を示す。archiveも回収終端記録も公開mainにない。私有保存物から共有版を取得する方法は未提供。 |
| 低ノイズcase2/target0のsampling・anchor | local `low_sampling_export_case2_target0_inputs_v1/accepted-input-sha256.json`、indexの既存SHA-256 `b78ff0af9a251118d9070c206f3fed672aed68606ac0070b3c8680fb90669b24`。[抽出記録](data_tile_validation_2026-10-17/low_sampling_export_case2_target0_inputs_v1/extraction.json)は61,440 sampling tasks＋192 anchors、184,897 filesを記録。 | 元実行先はworkspace相対 `20261018-tile-low-analysis-v11/runs/staged-production-2-0-v1` と記録されている。indexは原本file hashの抽出で、payload回収証拠ではない。公開mainにはindex・抽出記録がなく、archiveの現有無・配布先はこの監査では未確認。 |
| 同条件の派生集計 | [collection_verification.json](data_tile_validation_2026-10-17/low_collection_case2_target0_evidence_v1/collection_verification.json)は `20261018-tile-low-staging-control-v2/runs/collection-2-0-v1/rows.jsonl` 185,144,123 bytesと `evidence.json` 84,672,940 bytesを記録。rows SHA-256 `0fae2028ada19a8727bbfebb1d02d8de7be8d5216e1e281bee53007147f6912d`。 | 公開mainにverificationはあるが、そこに記載したprivate pathはdownload URLではない。`all_trace_payloads_recovered=false` であり、rows回収を全trace回収としない。 |
| 現行全12条件の入力 | [統一JSON索引](low_twelve_raw_access_inventory_2026-10-25.json)はfront v6の各実prepared世代から12条件のproduction/audit/reference root、36 control pin、portable ZIP 273件の既存pinと取得起点を抽出した。[追記説明](raw_access_followup_2026-10-25_ja.md)に形式と転送部分集合の記録容量を示す。 | 全raw総容量と公開downloadは未確定。小controlの原本hashは確認したが、raw現在bytesの全件再照合は未実施。既存の回収検証を否定せず、3条件の量やportable転送容量を全12条件のraw容量へ広げない。 |
| 主ノイズ独立計時MC/BAR | [計時JSON索引](main_timing_raw_access_inventory_2026-10-25.json)と[追記説明](raw_access_followup_2026-10-25_ja.md)にMC1件・BAR4件の現archive、指定stat容量、既存回収hash、原run、task JSON/NPZ/doneとfile indexを記録した。 | 私有保存物への起点がある。既存回収時の照合証拠を引き継ぎ、今回raw再照合・第三者転送はしていない。主計時の索引にJSONL memberはなく、低ノイズrows.jsonlや後続48行とは別scope。 |

WSS回収物は `input_bytes.json`・`input_sha256.json`・`expected.json` で範囲と既存hashを指定できるため、単に「データあり」という記録より具体的な取得起点になっている。
主4条件・直接MC・WSSの追加stat確認と既存receiptの対応は[raw保存監査](raw_preservation_audit_2026-10-25_ja.md)に保存した。
WSS archiveも同監査で608,476,985 bytesの存在を再確認したが、raw本体を開かず、既存hashを再計算した値へ読み替えていない。
ただし、そのarchiveの保存成功は第三者のアクセス許可や再配布条件の確定ではない。
低ノイズexportの既存仕様は[archive仕様](tile_low_noise_archive_spec_2026-10-19_ja.md)にあり、manifest・全予定task・失敗taskを含む3ファイル組をgzip archiveへ出す契約がある。
この仕様とscriptの存在だけで、各条件のexportや公開downloadが完了したとは扱わない。
今回、保存済みraw原本が実際に失われたと判明した具体例はない。
archiveの現存確認と過去の回収照合、保存先・indexがあるが現bytesを全件再照合していないものを区別し、後者を消失や未保存と判定しない。
完全な物理誤り履歴や過去analysisのconsumed hashが元から記録されていない制約は別に残る。
今回の監査完了に全raw再hashや大転送を新たに要求せず、既存receiptの観測時点と検証範囲を引き継ぐ。

## 利用者への引渡しで実際に不足する項目

1. 保存・内部verify・独立レビュー済みのv8共有候補を、利用者が実際に取得できる配布先と取得手順。
   専用exporterの受入、共有archive・外側hash・manifestは上記のとおり保存済みだが、未公開・未配布であり、後続control差分と最終proofの追加も未完了である。
2. source archiveから除いたraw/nativeごとの取得先、形式、byte数、原本hash、公開／個別提供／取得不可の区別をまとめた対応表。
3. 各private datasetの提供条件・保管担当・保存期限・問い合わせ方法。
   これらは未確認であり、MITのsource公開やprivate pathの存在から推測しない。
4. 元環境のPython/native記録と、新しい利用者環境の構築・import origin・新pinを対応付ける実行可能な再現手順。
   [手動の再配置手順](../../tools/reproducibility/README.md#relocation-to-another-local-or-cluster-workspace)には、外部入力取得、記録版の環境構築、path対応、新environment・source pinからmanifest・config・scriptを作る順序、新環境の受入、qsub投入までを記載済みである。
   別環境で校正実験全体を自動再実行する再配置・再pin runnerは未実装であり、上記の手動手順の記載や保存物の検証だけで実行可能性・科学的完全再現を保証しない。
   現行のクラスタ再開手順は、既存環境の実行を読む手順として別に保持する。
5. 全12条件・selection24行・独立計時48行・最終reportの実完了証拠と、基礎入力811,008行を含む原本への対応。
   現行のsnapshotや公開Releaseには、その後の未完成結果が保存済みだとは主張できない。

既存の `external_access` はformat・custodian・availability・retrieval・retentionを求めるが、現状では未確認値を正直に残す必要がある。
必要なsourceやrawを取得できない項目をblockerとして列挙し、snapshot保存・公開取得可能性・科学的完全再現を別々に判定する。
この監査では新規公開や追加の科学的検証を行っていない。
