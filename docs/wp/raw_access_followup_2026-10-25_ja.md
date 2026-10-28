# Raw保存先の追記：低ノイズ12条件と主独立計時

2026-10-25に、[raw保存監査](raw_preservation_audit_2026-10-25_ja.md)の残作業1〜3について、既存の小さいmanifest・receiptと明示archiveのstatだけから索引を補足した。
科学計算、raw本体の読込・展開・再hash、directory全走査、巨大indexの展開、新規ジョブ投入は行っていない。
以下のクラスタ相対パスの起点は `$HOME/workspace/mcmc4qec` であり、公開download URLではない。
公開用索引では絶対パスの識別子を置換したが、掲載SHA-256は置換前の原本を指し、索引JSON自身のhashではない。

## 低ノイズ12条件の統一索引

[機械可読索引](low_twelve_raw_access_inventory_2026-10-25.json)に全12条件の符号・noise・p、実prepared、実manifest、登録production root、audit/reference root、既存controlのpin、report pin、形式、取得条件を保存した。
起点は `20261025-low-parallel-front-v6/prepared-receipt.json`、原本SHA-256は `22eedcbfb42b9ef6ce3d286b539630491efeb80fd0317287fb31fc6ca8c3e058` である。
index0はfront v6、index1/6/7/8は保持されたfront v4、残り7条件はfront v5の実preparedを記録し、一律v6として付け替えていない。
これは入力の保存先索引であり、workerの終了・最終受理を新たに認定するものではない。

下表のrootは `20261018-tile-low-analysis-v11/runs/` 以下の登録production rootである。
audit rootのretry/budget差分、portable rootの正確な日付と名前、全pinはJSON索引を参照する。

| index | 符号・noise | p | 登録production root | 入力経路 | portable転送記録bytes |
|---:|---|---:|---|---|---:|
| 0 | tile72 bit | 0.01 | `partitioned-full-0-0-v1` | recovered | 未集計 |
| 1 | tile72 bit | 0.003 | `partitioned-full-0-1-v1` | recovered | 未集計 |
| 2 | tile72 bit | 0.001 | `partitioned-full-0-2-v1` | portable mixed | 9,532,490,259 |
| 3 | tile288 bit | 0.01 | `partitioned-full-1-0-v1` | portable condition | 3,968,906,245 |
| 4 | tile288 bit | 0.003 | `partitioned-full-1-1-v1` | portable condition | 5,029,753,220 |
| 5 | tile288 bit | 0.001 | `partitioned-full-1-2-v1` | portable condition | 5,602,897,252 |
| 6 | tile72 depolarizing | 0.01 | `staged-production-2-0-v1` | staged | 未集計 |
| 7 | tile72 depolarizing | 0.003 | `staged-production-2-1-v1` | staged | 未集計 |
| 8 | tile72 depolarizing | 0.001 | `staged-production-2-2-v1` | staged | 未集計 |
| 9 | tile288 depolarizing | 0.01 | `partitioned-full-3-0-v1` | portable condition | 5,491,434,941 |
| 10 | tile288 depolarizing | 0.003 | `partitioned-full-3-1-v1` | portable condition | 6,535,632,313 |
| 11 | tile288 depolarizing | 0.001 | `partitioned-full-3-2-v1` | portable condition | 7,107,503,228 |

全36 control fileは明示pinから限定して読み、原本hashと照合した最大124,354 bytesのJSONである。
全rawの総容量は12条件とも未集計であり、表の数値は既存 `transfer-complete.json` が記録するcontrol込みの転送部分集合で、現在のstatや全raw容量ではない。
portable7条件は各 `context.json` の既存 `input_sha256` から計273件のZIP位置とhashを抽出し、archive本体は開いていない。
ZIPはbatch outputsとreference inputsであり、全sampling生データを内包すると認定していない。
recovered/staged5条件は `analysis_manifest.json` と `partition_analysis_manifest.json` の既存completed-phase記録、および各実manifestの `condition.input_sha256` が詳細入力索引への起点となる。
記録されたcollection manifestのidentity digestは、対象ファイルのbyte SHA-256と断定せず別fieldに保存した。
task保存形式はJSON metadata・done markerとNPZ compact trace/checkpoint、派生analysisはJSON/JSONLであり、全物理誤り履歴とは異なる。
個々のrawファイルが今も全件取得可能かの走査、全条件archive回収、公開取得経路の確認は未実施である。

既存アクセス権を持つ担当者は、索引の実preparedと実manifestを取り出し、原本pinを確認した後、条件内のcontrol/indexから必要なtaskまたはarchiveを選べる。
コピー・展開・rawの全hash照合が必要な場合は、既存のqsubと2物理ノード制約の下で行う。
今回の限定監査で追加のqsubや巨大index読込は必要なかった。
第三者への権限付与・転送・公開は実行していない。

### 19:12 JST追記：指定273 ZIPの現存と容量

2026-10-25 19:12:06 JSTに、上記索引に明示されたportable7条件の273 ZIPだけをクラスタでlstatした。
全273件が指定場所に通常file・非symlinkとして存在し、欠落・未観測・通常file以外はいずれも0件だった。
親directoryも指定パスに沿って非symlinkを確認し、代替パス探索やdirectory全走査は行っていない。

| 条件index | 指定ZIP数・確認数 | 観測したZIP合計bytes |
|---:|---:|---:|
| 2 | 39/39 | 9,511,945,333 |
| 3 | 39/39 | 3,923,378,015 |
| 4 | 39/39 | 4,973,244,306 |
| 5 | 39/39 | 5,539,215,612 |
| 9 | 39/39 | 5,434,066,377 |
| 10 | 39/39 | 6,467,046,815 |
| 11 | 39/39 | 7,031,369,917 |
| 合計 | 273/273 | 42,880,266,375 |

[観測原本](portable_zip_stat_observation_2026-10-25.json)は170,904 bytes、SHA-256は `9b2f385d8150c5f80eb948336f64a30f25c929d93e49841bb34592fa64194869` であり、原本と同じbytesを保存した。
各ZIPの `recorded_original_sha256` は過去の索引からの複写であり、今回の内容再照合の結果ではない。
合計は指定ZIP自体の現在のstat容量で、上表のcontrol込み過去転送bytesや全12条件の全raw容量と区別する。
ZIP本体の読取り・展開・再hash・member検査・科学計算・追加qsubは行っておらず、archiveの完全性、全sampling生データの収録、backup、保存期限、第三者取得可能性はこの観測から保証しない。
recovered/stagedの他5条件は今回の対象外である。
実施sourceとrequestはlocal `output/portable_zip_stat_2026-10-25_v1/` に保存した。

## 主ノイズ独立計時の原taskとarchive

[主計時の機械可読索引](main_timing_raw_access_inventory_2026-10-25.json)に原run、実job番号、task形式、展開先、archive、現stat容量、既存hashと照合receiptを保存した。
下表の相対パスの起点はrepository内 `docs/wp/data_tile_validation_2026-10-17/` である。
容量は今回の指定ファイルstat、hashは過去の回収記録であり、今回の内容再照合を意味しない。

| 対象・実job | archive | bytes | 既存SHA-256 |
|---|---|---:|---|
| MC全4case・265237 | `mc_timing_main_evidence_v1/mc-benchmark.tar.gz` | 5,800,713 | `f28b3aa507a0d043d06a7d921e29b7f11b15bdf65482316a6cfc84e5c3d9b136` |
| BAR case0・265263 | `bar_main_case0_evidence_v1/recovered.tar.gz` | 12,089,902 | `341554f3aaf92de72327ccd5d249df7ebef03989067295a59712faa59604fc17` |
| BAR case1・265266 | `bar_main_case1_evidence_v1/recovered.tar.gz` | 97,886,759 | `c52b45c75d80e51ebccd532a5031c76e61efdfacd483091d394f4b07ba56a3a6` |
| BAR case2・265267 | `bar_main_case2_evidence_v1/recovered.tar.gz` | 23,989,162 | `3b00fc9170371f70f65b7210c2a1c80235256bc88640342a5966a180c60df464` |
| BAR case3・265268 | `bar_main_case3_evidence_v1/recovered.tar.gz` | 132,884,981 | `f055219ea30f7a7fa02d0e681f6ced340b28faaa22941350240fa37c06a50ea5` |

MCの原runは `20261018-tile-mc-timing-v3/runs/mc-benchmark`、BARは `20261018-tile-bar-seed-audit-v1/runs/benchmark-{0,1,2,3}` である。
MCは1,536 tasks・4,620 files、BAR各caseは384 tasks・1,167 filesの回収を既存receiptが記録する。
それぞれ `tasks/<task-id>.json`・`.npz`・`.done.json` の3ファイル組と `summary.json` を保存している。
限定して読んだ既存MC `benchmark_verification.json` とBAR `verification.json` のfile indexには、独立した `.jsonl` memberはない。
したがって、この主計時の保存物をJSONLとして案内せず、別scopeの低ノイズ `rows.jsonl` とも混同しない。
実taskの展開先はMC `mc_timing_main_evidence_v1/mc-benchmark/tasks`、BAR各 `bar_main_caseN_evidence_v1/recovered/benchmark-N/tasks` であり、今回task本体は開いていない。
主計時の正式reportは `20261018-tile-timing-report-v2/runs/formal-all-cases-v1/results/report.json` と `report_ja.md` で、[回収検証](data_tile_validation_2026-10-17/main_timing_report_result_evidence_v1/collection_verification.json)にjob265277・15成果物の対応がある。
reportの回収や保存chain検査は、全状態再復号・乱数列の統計的独立性・母RMSE・名目被覆の保証ではない。
後続の低ノイズ独立計時48行とそのraw保存完了は、この主計時の5archiveで代替しない。

## 最終的に残る保存上の不足

主4条件・直接MC・WSS・主計時の現archive所在と容量、および低12条件の条件別取得起点は具体化した。
低ノイズportable7条件では指定273 ZIPの現存とstat容量まで19:12 JSTに確認したが、ZIP内容と全rawの検証は追加していない。
全12条件のraw全件の現存・総byte数・完全な回収archive・第三者downloadと、未完成の低ノイズ独立計時や最終reportの保存証拠は未確定である。
全private datasetの保管担当、提供条件、保存期限、問い合わせ・削除判断窓口、別媒体backupは未確認のまま記録し、永久保存や新しい義務を設定しない。
今回の限定監査で、保存済みraw原本が実際に失われたと判明した具体例はない。
既存の回収hash照合がある保存物と、所在・indexはあるが現在のbytesを全件再照合していない保存物を区別し、後者を消失・未保存とは判定しない。
観測時点付きの既存回収証拠を引き継ぎ、今回の完了要件へ全raw再hashや大転送を追加しない。
主校正の過去analysisについて当時のconsumed trace/anchor hashが不明な制約は残り、今回の所在索引や現在のpayload監査から過去の消費内容を証明し直せない。
