# Raw 保存要件の限定監査

2026-10-25に、[最終成果物監査](final_deliverable_audit_2026-10-24_ja.md)、[取得可能性の索引](reproduction_access_inventory_2026-10-25_ja.md)、既存の小さいreceiptと文書、および明示されたarchiveのstatを確認した。
raw本体の読込・hash再計算・展開、directory全走査、科学計算、ジョブ投入は行っていない。
下表の容量は指定ファイルの今回のstat、SHA-256は過去の回収記録による値であり、現在のbytesとの再照合を意味しない。
公開済み資料の状態は取得可能性の索引の観測時点に依存し、本監査では外部サービスを再確認していない。

## 主4条件：現在の保存起点を具体化できたもの

以下のパスはこのrepositoryからの相対パスである。
`R` は `output/tile_validation_recovery` とする。
sampling archiveはcompact traceと保存initial/checkpoint、anchor等のJSON・NPZ・done記録を含む回収物であり、全物理状態や完全な乱数軌道を保存したものとはしない。
analysis archiveは各case768 group・2,315 filesの保存行と診断等の回収物であり、raw samplingとは別に残す。

| 保存物 | 現在の相対パス | bytes | 既存SHA-256 |
|---|---|---:|---|
| sampling case0 | `R/20261018-v2-tile-case0-recovery/production-sampling-0.tar.gz` | 7,866,545,400 | `c1cec6049d9641fcdc3fa34e762df63bc047a255898bf4c2d4715eb455fdfce3` |
| sampling case1 | `R/production-sampling-1.tar.gz` | 1,084,152,515 | `d55c89d6f31f549784ef91d2910acb96d4e09b61dbb047e32af2cb1c060e4c05` |
| sampling case2 | `R/20261018-v2-tile-case2-recovery/production-sampling-2.tar.gz` | 1,119,120,228 | `1b455a949d31106c34d0184f05c1def9e4d414c5bfea78be5734476f925489d1` |
| sampling case3 | `R/production-sampling-3.tar.gz` | 842,505,751 | `d9da46720bd4571ca2f6c8e45b5e00930f78df3d0be29e48eb66c80190cb95b8` |
| analysis case0 | `R/20261018-v2-tile-case0-analysis-recovery/production-analysis-0.tar.gz` | 4,439,599,537 | `fa8ac44f692be5520a2cdb47b3214e50204278ced71af856e1c98ce2d18f294b` |
| analysis case1 | `R/20261018-v2-tile-case1-analysis-recovery/production-analysis-1.tar.gz` | 1,943,166,818 | `19ccf9223b94a8e1178bafbb460ca21d94c1256be77ad5b6fa9f49084f944b2f` |
| analysis case2 | `R/20261018-v2-tile-case2-analysis-recovery/production-analysis-2.tar.gz` | 4,477,986,977 | `3431a5a84aa13ca0773ed8ebd92dab34feb3840b357496a7e614264183707410` |
| analysis case3 | `R/20261018-v2-tile-case3-analysis-recovery/production-analysis-3.tar.gz` | 3,087,175,636 | `d213d22dbbf34c52790b3955c9731ffc75901f5727edc857e124a728ca0089e1` |
| 直接MC reference | `R/reference-artifacts.tar.gz` | 7,814,608 | `58a83c8958fada5887e5ccb37ce4a6f0ac554023f20e73efeac1bd062bb39933` |

sampling case0/2は各 `sampling_case{0,2}_collection_stage_binding_v1.json`、case1/3は各 `production_sampling_archive_verification-{1,3}.json` の先頭記録を根拠とした。
analysisは各 `production_analysis_recovery_caseN_20261018-v2-tile-caseN-analysis-recovery.json` の保存先・容量・hashを確認し、その指定archiveの存在とサイズを照合した。
直接MCは [reference_audit.json](data_tile_validation_2026-10-17/reference_audit.json) と `reference_archive_verification.json` に1,248 artifacts・3,750 files・81,788,928試行の回収検証が記録されている。
取得可能性の索引で未確定だった直接MC archiveの現保存先とbyte数は、この限定stat確認で補足できた。
各元receipt・archive検査の起点と形式は[データREADME](data_tile_validation_2026-10-17/README.md)にも記録されている。

これらの存在は別媒体へのbackup、第三者の取得、保存期限の保証ではない。
取得にはこのPCの保管物へのアクセスが必要で、通常cloneや公開Releaseからraw archiveを取得できるとは確認していない。
コピー後の検証は既存 `artifact_archive.py` と外部固定manifest・archive/hash indexを使う範囲を引き継ぎ、大容量の照合はqsub内で行う。
この監査はその取得・再照合を実行していない。

## WSS・低ノイズ・独立計時の証拠と不足

| 対象 | 確認できた保存・索引の根拠 | 未確認・残る事項 |
|---|---|---|
| 固定16条件WSS | `data_tile_validation_2026-10-17/weight_reference_recovered_v1/evidence.tar.gz` は今回statで608,476,985 bytes。既存hash `5650c33310cabfaea17a91c6185007631bbfede70a7fb613e2670828de4da476`。同directoryのexport/recoveryと[終端検証](data_tile_validation_2026-10-17/weight_reference_recovery_terminal_validation_v1.json)はgzip level1、23,954 artifacts・71,904 files・raw chunks23,938、input hash/size index、回収検証を記録する。 | rawはprivate。取得窓口、提供条件、保管担当、保存期限、別媒体backupは未確認。今回archiveを再hashしたとはしない。 |
| 低ノイズ全12条件 | [成果物監査](final_deliverable_audit_2026-10-24_ja.md)のfront v6から、保持された各worker自身のprepared・manifest・environment・元入力pinへたどる起点がある。12×352設定×192 seedの基礎811,008行と、selection24行は別scopeである。 | 全12条件のraw所在・形式・容量・既存hashを一対一にした統一索引と、全条件のarchive回収証拠は本監査では未取得。worker終端やsource snapshotをrawの永続保存へ読み替えない。 |
| 低ノイズC2T0の具体例 | [抽出記録](data_tile_validation_2026-10-17/low_sampling_export_case2_target0_inputs_v1/extraction.json)は61,440 sampling tasks＋192 anchors、184,897 files、元run `20261018-tile-low-analysis-v11/runs/staged-production-2-0-v1` とhash index `b78ff0af9a251118d9070c206f3fed672aed68606ac0070b3c8680fb90669b24` を記録する。クラスタworkspaceからの相対パスである。 | `current_remote_raw_scan=false` の索引抽出で、payloadの回収ではない。[派生集計の検証](data_tile_validation_2026-10-17/low_collection_case2_target0_evidence_v1/collection_verification.json)も `all_trace_payloads_recovered=false`。rows.jsonlやevidence.jsonを全rawと数えない。 |
| 低ノイズC3T2 | [算術回収receipt](data_tile_validation_2026-10-17/c3t2_arithmetic_recovery_20261024_v1/receipt.json)には小さいresult・request・review・CSV等の元hashと識別子処理後hashが別々に記録されている。 | これはraw sampling archiveではない。11条件や3条件の量から全12条件の総容量を推定して確定値にしない。 |
| 主ノイズの独立計時 | [正式reportの回収検証](data_tile_validation_2026-10-17/main_timing_report_result_evidence_v1/collection_verification.json)、[科学レビュー](data_tile_validation_2026-10-17/main_timing_scientific_review_v1/report_ja.md)、MCの `local_verification.json` とBARのcase別 `independent_payload_verification.json` がある。MCは4,620 filesの照合とarchive hash `f28b3aa507a0d043d06a7d921e29b7f11b15bdf65482316a6cfc84e5c3d9b136`、BAR各caseは384 tasksと保存chain metadataの検証を記録する。 | 主8条件の結果保存と全raw計時archiveの取得表は別である。各MC/BAR原task・JSONL・NPZの現保存場所、容量、取得用archiveとの対応をこの監査では確定していない。 |
| 低ノイズの独立計時 | 最終成果物監査に正式selection24行、48行のMC/BAR評価、各192分母、対象なし理由を保存する契約がある。 | 当該scopeの実完了とraw保存のreceiptは本監査では未取得。主ノイズの独立計時やfixture受入で代替しない。未実行・非選択・対象なしを区別して最終索引へ追加する。 |

## 完了前に残す最小の追記

1. 主4条件と直接MC・WSSのarchive保存先・容量を[取得索引](reproduction_access_inventory_2026-10-25_ja.md)へ反映済みで、元hashと今回statを区別した。
2. 低ノイズ12条件は[統一索引](low_twelve_raw_access_inventory_2026-10-25.json)へ実prepared・保管先・既存control/receipt/ZIP pin・形式・未集計容量・取得条件を対応付けた。
3. 主独立計時のMC/BAR5archive、原task形式・現保存先・既存回収receiptは[追記](raw_access_followup_2026-10-25_ja.md)と[計時索引](main_timing_raw_access_inventory_2026-10-25.json)へ保存した。
   低ノイズの後続selection・計時・最終reportは、その実完了証拠が得られた段階で別scopeとして保存する。
4. 全private datasetについて保管担当、提供条件、保存期限または未確定、削除・移動の判断窓口、別媒体backupの有無を記録する。
   現在読んだ資料から保存期限を確定できず、永久保存や「公開後何年」といった期限は作らない。

上表の全12条件・主計時の「本監査では未取得／未確定」は初回監査時点の不足であり、そのうち所在・既存pinの対応は上記追記で補った。
今回、原本の消失を確認した具体例はない。
現bytesを全件再照合していないものを未保存・消失と扱わず、既存回収時の検証を観測時点付きで引き継ぐ。
全raw再hashや大転送は今回の追加完了要件にしていない。

source/metadata snapshotの保存、rawの所在確認、rawの回収検証、公開取得可能性、独立な科学的再現は別の判定である。
主校正の過去analysis artifactは消費時点のtrace・anchor hashを記録しておらず、後日の保存payload監査から当時のconsumed hashを証明し直せない。
anchorには全物理誤りと完全な乱数metadataがないため、保存原本が揃っても生試行の完全再復号を保証しない。
これらの制約と有限reference・乱数stream独立性の限界を[検証報告](tile_validation_report_2026-10-18_ja.md)から引き継ぎ、保存の改善を独立性や名目被覆の証明へ拡張しない。
