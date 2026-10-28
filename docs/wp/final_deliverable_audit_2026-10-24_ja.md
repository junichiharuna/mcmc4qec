# 最終成果物の監査と残項目

## 最新の到達点（2026-10-26 08:41 JST）

`c0t1e1-mc-main0` の科学job265770はF/0・run_count=1・PBS wall56分07秒で終了し、[結果監査](../../output/census_active_node_migration_v1/mc-t1e1-main-result-audit-1792971680426190900/audit.json)で個別192recordの全件成功/取得、費用整合、summary/manifest/実PBS結合を確認した。
監査原本SHA-256は `430f3541b396600b607e94d297e80bff5752ea3b148832594d0411e7301ea40b`、[回収記録](../../output/census_active_node_migration_v1/mc-t1e1-main-result-audit-1792971680426190900/collection.json)は `e0b536d39c7fd834dc2aafe1f062251110312dc7c57ebeaf43d6bce344322b2f` である。
同記録のfull summaryは3,176,184 bytes・SHA-256 `ebf9ceaedf7bb675afe7b344f5a2a770bdff9eb2d92addcfb1334d7667fa568b`であり、この文書更新では小audit/collectionだけを読み、summaryやrawを読み直していない。
execution wall3365.589秒はpool1815.808秒とoutside pool1549.781秒に分かれるが、outside全体を検証処理へ帰属させない。
controller正式finishと精度gateは未確認で、正式受理済み本計時は6/24件のまま、BAR265772は稼働中である。
残る本計時・全48行の精度gate/費用比較・最終科学reader・報告・snapshot保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 08:33 JST）

`c0t1e1-bar-main0` の科学job265772のqsub投入・R（08:31:57開始）と、MC265770との別2物理ノード・各96 CPU/337 GiBの割当を[小原本](../../output/census_outer_operation_v1/bar-t1e1-main-allocation-1792971182972444900.json)で確認した。
原本SHA-256は `fc2a75ab687b46cf6944e837b73181cdcc8b67614b41fcdd40469c7ab889394d` で、親265771はF/0・run_count=1・PBS wall47分11秒で終了し解放済み、queued/unplacedはなかった。
BARのexecution-intent・actual-pbs-start・native_preflight・summary・failureはこの観測時点で未生成であり、Rだけから推定器task開始・結果を認定しない。
本計時の正式受理数は6/24件を維持し、残る本計時・最終科学reader・全48行の精度gate/費用比較・報告・snapshot保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 07:44 JST）

`c0t1e1-mc-main0` の科学job265770のqsub投入・Rと、BAR投入前helper265771との別2物理ノード・各96 CPU以内の割当を確認した。
割当監査原本SHA-256は `4a191fc53991ddcc5c3a8a4f7ca1e203fe0fcd917cd64cb752515764dc5f43cd` で、親265769はF/0・45分37秒で終了し解放済みだった。
開始marker・native・結果は監査時点で未生成で、本計時の正式受理数は6/24件のままとする。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 06:58 JST）

`c0t1e1` のBAR正式finish265768のF/0・41分37秒と、小原本19件の照合を完了した。
監査SHA-256は `fe71177afcecfbd3675e5afc105e6cf1d0513a9fc6e9f872a84074ad6945a94e` で、BAR本計時192反復・1 partition・21 workers・96 CPU・337 GiB・要求1時間の計画まで確認した。
先行MC本計画と合わせて準備を完了し、MC本計時はsubmittingへ進んだが科学job IDは未確定である。
本計時の正式受理数は6/24件を維持し、最終科学reader・報告・snapshot保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 06:12 JST）

`c0t1e1` のMC/BAR予備計時はともにF/0で、MC正式finish265766のF/0・41分18秒と[小原本照合](../../output/census_active_node_migration_v1/MC_T1E1_CAPACITY_FINISH_AUDIT_ja.md)を確認した。
監査SHA-256は `02ceb3a6f2dcf1d60e391843f6a81773be0a23681ad3a04b192bae902842bd72` で、本計時192反復・1 partition・21 workers・96 CPU・337 GiB・要求2時間の計画まで確認した。
本計時の実行・受理は未確認で、正式受理済み本計時は6/24件を維持する。
BAR終了確認helper265767はRで、残る独立計時・最終科学reader・報告・snapshot保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 04:56 JST）

BAR正式finish265760のF/0・22分58秒と[小原本の受入照合](../../output/census_active_node_migration_v1/BAR_T1E0_MAIN_FINISH_AUDIT_ja.md)により、正式受理済み本計時は6/24件となった。
監査SHA-256は `7b8f98aa70dc2badea3424c5e3e99a87c5571111eece1d331cff37e4fbac864f` で、summary / rawの再読や科学再計算は行っていない。
個別BAR結果・費用・精度gate・最終report / snapshotは引き続き未完了である。
次条件 `c0t1e1-mc-capacity` の投入前helper265761がRで、実科学job IDは未確定である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 04:23 JST）

MC本計時265753の正式finish265757はF/0・22分52秒で完了し、[小原本照合](../../output/census_active_node_migration_v1/MC_T1E0_MAIN_FINISH_AUDIT_ja.md)により正式受理済み本計時は5/24件となった。
監査SHA-256は `a7f92b67f4a388bdbfb3e2e6683cf32ff080cccfa8759671111c194b7ebbd76d` である。
BAR265755もF/0・33分11秒で終了し、[限定結果監査](../../output/census_active_node_migration_v1/BAR_T1E0_MAIN_RESULT_AUDIT_ja.md)で小要約192/192を確認したが、正式受理と159,972,736 bytesのsummary個別内容・費用は未確認である。
最終保存preparerはqsubのjob265759で37合成testsを1.071秒・skipなしで通過した。
fixture accepted原本SHA-256は `99e1d1ac945536545c63c96ba671a331f068cefe6aaa9425e558c892ff149bcf` で、本番の最終snapshot・最終科学reader・report完了は引き続き未達である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 03:48 JST）

次条件BAR本計時265755のqsub投入・Rと、MC終了確認helper265756との別2物理ノード・各96 CPU以内の割当を[限定監査](../../output/census_active_node_migration_v1/BAR_T1E0_MAIN_ALLOCATION_AUDIT_ja.md)で確認した。
監査原本SHA-256は `308bec17a230d03c1575f13a2bf7f1254eebf184b1219cf5a52d24cc85911238`、親265754はF/0・解放済みで、既知pin・計画・実PBSが一致した。
BARの推定器task開始・結果とMCの正式finishは未確認であり、正式受理済み本計時は4/24、最終科学評価・保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 03:35 JST）

次条件MC本計時265753のF/0・run_count=1・33分49秒を確認し、[限定結果監査](../../output/census_active_node_migration_v1/MC_T1E0_MAIN_RESULT_AUDIT_ja.md)で192反復の重複欠落なし・全成功・推定値取得と費用記録の整合を確認した。
監査JSONのSHA-256は `ff238aca6cfdba6a3a5a719d9eeb5a54aa09ba70dfe64604f9339fd44373c85f`、summary原本は `91ca37820a8c1d5c8ffc50631bab42c366babb48a6693200213ed3677e343556` である。
controller正式finishと精度gateは未確認であり、正式受理済み本計時は4/24、最終科学評価・報告保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 03:01 JST）

次条件MC本計時265753のqsub投入・Rと、BAR投入前helper265754との別2物理ノード・各96 CPU以内の割当を[限定監査](../../output/census_outer_operation_v1/MC_T1E0_MAIN_ALLOCATION_2026-10-26_ja.md)で確認した。
監査原本SHA-256は `848768f418bd2e675c60ab61aefe03f82c78b37444fd8d37ce12213794d5a2b0`、親265752はF/0・解放済みで、投入記録・script・manifest・実PBSが一致した。
開始marker・科学結果は監査時点で未生成であり、正式受理済み本計時は4/24、最終科学評価・報告保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 02:15 JST）

次条件BAR capacityの正式finish265751がF/0・40分51秒となり、[小原本監査](../../output/census_active_node_migration_v1/BAR_T1E0_CAPACITY_FINISH_AUDIT_ja.md)で受理から元capacity結果と192反復の本計時計画への対応を確認した。
監査JSONのSHA-256は `a941d791bf3e883626590b753769920a18d2131ed56f0ace0706540e3db3e8c9`、本計画は1 partition・21 workers・96 CPU・337 GiB・要求1時間で一致した。
次のMC本計時の投入前helper265752はRへ進んだが、科学本体のjob IDは未生成で、独立本計時正式受理済みは4/24のままである。
本計時実行・最終科学評価・再現用保存は未完了であり、以下は各観測時刻の履歴として保持する。

## 最新の到達点（2026-10-26 01:30 JST）

次条件MC capacityの正式finish265749がF/0・41分30秒となり、[小原本監査](../../output/census_active_node_migration_v1/MC_T1E0_CAPACITY_FINISH_AUDIT_ja.md)で受理から元capacity結果と192反復の本計時manifestへの対応を確認した。
監査JSONのSHA-256は `3742642c2387f954144a678ec985cf0bbe906a9a50cc83588bd415da079b6734` で、本計画は1 partition・21 workers・96 CPU・337 GiB・要求1時間で一致した。
本計時実行の記録は監査時点で未生成であり、独立本計時の正式受理済みは4/24、残り本計時・最終科学評価・再現用保存は未完了である。
以下は各観測時刻の履歴である。

公開状態は2026-10-26 01:07:44 JSTの[API確認記録](publication_state_check_2026-10-26.json)でもpublic・非archive・同main/tag・非draft prerelease・配布物5件を維持していた。
確認記録SHA-256は `fccd62e8b2ffa554d2691c35d86ef06ba5a377bd5e07f48e6e93a4b6dc834a08` であり、配布物bytes・CI・Zenodo・未コミット作業の公開は今回の確認範囲外である。

## 最新の到達点（2026-10-26 00:53 JST）

次条件BAR capacity265747のF/0・7分32秒と小要約2/2件・failed/unavailable各0を確認した。
根拠はlocal `output/finite_tail_resume_controller_v1/bar-c0t1e0-capacity-run-markers-1792943602475499600.json` と `independent-state-1792943602540503200.json` であり、正式回収と個別結果の検査は未了である。
MC capacity正式finish265749はRで、独立本計時正式受理済み4/24と最終科学検証未完了の扱いは変わらない。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 00:45 JST）

次条件BAR capacity265747のqsub投入・Rと、MC capacity終了確認helper265748のRを[限定割当監査](../../output/census_outer_operation_v1/C0T1E0_BAR_CAPACITY_ALLOCATION_2026-10-26_ja.md)で確認した。
監査原本SHA-256は `47a090165e161879fa0d16e52deb05e6ed764479236f2cdb8a78474622b44494`、実配置は別2物理ノード・各96 CPU以内であり、親265746はF/0・解放済みだった。
BARの開始marker・結果は監査時点で未生成で、独立本計時の正式受理済みは4/24、最終科学検証・報告・保存は未完了である。
以下は各観測時刻の履歴である。

## 最新の到達点（2026-10-26 00:32 JST）

BAR e1の正式finish265745はF/0・23分05秒となり、[限定監査](../../output/census_active_node_migration_v1/BAR_E1_MAIN_FINISH_AUDIT_ja.md)で受理・回収原本の一致と、元job265739・manifest/submissionへの対応を確認した。
監査JSONのSHA-256は `98acf701e009170d57c0dfe62bc22d99f9e60659cde59d739d1201cb6a528058`、独立本計時の正式受理済みは4/24である。
巨大BAR summaryの個別192件・費用・full bindingは後続PBS readerへ残し、receiptの `scientific_validation_complete=false` を保持する。
次MC capacity265743はF/0、次BAR capacityの投入前helper265746はRであり、残り20件の本計時、最終科学評価・報告・再現用保存は未完了である。
以下の到達点はその観測時刻の履歴である。

## 最新の到達点（2026-10-25 23:54 JST）

次条件 `c0t1e0-mc-capacity` 本体265743のqsub投入・Rと、前条件BAR終了確認helper265744のRを[限定割当監査](../../output/census_outer_operation_v1/C0T1E0_MC_CAPACITY_ALLOCATION_2026-10-25_ja.md)で確認した。
監査原本のSHA-256は `a6c12e1162e1481b6fcc52abe5f7fdc47ade35e86ba6bd312e2d709805f74625`、実配置は別2物理ノード・各96 CPU以内で、Q・未配置jobなしだった。
容量計測の開始marker・結果は監査時点で未生成であり、前条件BARの正式finishも未受理、本計時正式受理済みは3/24のままである。
以下の23:41以前の状態は履歴として保持する。

BAR本計時265739はF/0・37分31秒で終了し、[小原本限定監査](../../output/census_active_node_migration_v1/BAR_E1_MAIN_RESULT_AUDIT_ja.md)で投入・開始・実PBS終端の結合と、小要約の192/192・failed/unavailable各0を確認した。
監査JSONのSHA-256は `f4a14eba8d4b469211754c5b46a2cc407025a3dd060037b4e4c17f57dee3448a` であり、291,433,034 bytesのsummary本体は未読で、個別192件・費用・full summaryの結合は後続PBS readerへ残す。
当該BAR正式finish受理は未確認のため、本計時の正式受理済みは3/24のままである。
次capacityの投入前helper265742はRで、以下の23:38以前の稼働状態は履歴として保持する。

次精度条件MCの正式finish265741はF/0・22分50秒となり、[限定監査](../../output/census_active_node_migration_v1/MC_E1_MAIN_FINISH_AUDIT_ja.md)で受理・回収と既存192record監査への結合を確認した。
監査JSONのSHA-256は `200c143dab9175132ca63d7a3d090e82a7c303729732714db4f022c58dfb8657`、独立本計時の正式受理済みは3/24である。
receiptの `scientific_validation_complete=false` を保持し、BAR265739はR、次capacityの投入前helper265742がRで、全独立計時・最終科学評価・保存は未完了である。
以下の23:04以前の件数は時刻付き履歴として保持する。

BAR本計時265739のqsub投入・Rと、MC終端確認helper265740との別2物理ノード・各96 CPU以内の割当を[限定監査](../../output/census_outer_operation_v1/BAR_E1_MAIN_ALLOCATION_2026-10-25_ja.md)で確認した。
監査原本のSHA-256は `f761ebb468e44a6a5a2138025583f982b2935c6f7c25c5eefd5d85aab6879f7f` であり、開始markerは同時点で未生成、本計時の正式受理済みは2/24である。
以下の22:45以前の状態はその時刻の記録として保持する。

次精度条件MC本計時265737はF/0・run_count=1・28分13秒で終了した。
22:45:46 JSTの[限定独立監査](../../output/census_active_node_migration_v1/MC_E1_MAIN_RESULT_AUDIT_ja.md)で192反復の全件成功・重複欠落なし、manifest・投入記録・実PBS終端・summaryの結合と費用記録の整合を確認した。
監査JSONのSHA-256は `0ffd304cb4df2b907ac5e9e00971b934f4cdeb7c0efaeafb29ea3276bf3a59a7` であり、科学rawの再読や精度gateの評価は行っていない。
正式finish受理は未確認で、本計時の正式受理済み2/24とは別にこの1件の計算終了と個別結果監査を記録する。
BAR投入前helper265738は同時点でR、本体のsubmissionは未生成である。
以下の時刻付き到達点は履歴であり、最新の状態は上記および[状態文書](PROJECT_STATUS_2026-10-24_ja.md)を参照する。

[状態文書](PROJECT_STATUS_2026-10-24_ja.md)では初期capacity準備265709のF/0と、全48手法行を保持したinventoryのready24行・not_selected24行、capacity manifest24件を確認した。
これは実行対象24件の準備完了であり、全24件のcapacity実行完了ではない。
先頭C0T0・目標相対RMSE20%のMC265712とBAR265714はともにF/0となり、それぞれ予備計時2/2件を完了した。
MC finish265716もF/0・run_count=1で正式受理され、本計時192反復・1 partitionのmanifestとcapacity proofへの結合を[独立監査](../../output/census_active_node_migration_v1/MC_CAPACITY_FINISH_AUDIT_ja.md)で確認した。
本計時の要求は96 CPU・実worker上限21・337 GB・30分であり、資源計画を完了予測や192反復の実行結果とは扱わない。
監査原本`output/census_active_node_migration_v1/mc-capacity-finish-audit-1792911711939257400/audit.json`のSHA-256は`81ce9eb7f0b96dba9279df201b5472cedfc851f611e13871b8cfcd40f5c76c8a`で、小原本18件・正式finish・本計時manifestへの対応を保持する。
BAR finish265718はF/0・run_count=1・41分36秒で終了し、16:47:41 JSTの独立監査で正式受理から元capacity proofと192反復manifestへの結合を確認した。
小原本18件は `output/census_active_node_migration_v1/bar-capacity-finish-audit-1792914461448805900/` に保存し、元capacity時と本計画のsource pin60件・現在ファイルのhash一致も確認した。
同監査JSONのSHA-256は `5302ec536e54d202325d296e3c050dda842295d6b74b4d5d17198021227feff5` で、詳細は[BAR finish監査](../../output/census_active_node_migration_v1/BAR_CAPACITY_FINISH_AUDIT_ja.md)を参照する。
MC本計時265721はF/0・run_count=1・26分53秒で終了し、17:58:24 JSTの[独立結果監査](../../output/census_active_node_migration_v1/MC_MAIN_RESULT_AUDIT_ja.md)で192反復の全件成功・重複欠落なし、投入記録・結果・実PBS終端との結合を確認した。
同監査JSONのSHA-256は `4c10d1f4e7c0ef10f7226d7fe544248ab34268958e758ee967375755384d874b` で、原本は `output/census_active_node_migration_v1/mc-main-result-audit-1792918704434460000/` に保存した。
先頭MCの正式finish265725もF/0・22分51秒となり、18:56:40 JSTの[限定監査](../../output/census_active_node_migration_v1/MC_MAIN_FINISH_AUDIT_ja.md)でaccepted・completion・controls・collectedの一致と既存192record監査のpinへの結合を確認した。
同監査JSONのSHA-256は `145b7a25613031499b91066438e9a1d7d99dd219deb7726270743ff8fe56296f` であり、receiptの `scientific_validation_complete=false` を保持して最終科学検証とは区別する。
BAR本計時265723もF/0・run_count=1・29分52秒で終了し、小scientific-summaryは192/192・failed/unavailable各0を記録した。
18:48:13 JSTの[BAR小原本監査](../../output/census_active_node_migration_v1/BAR_MAIN_RESULT_AUDIT_ja.md)で実投入・manifest・script・実PBS終端の結合と小要約原本を確認し、監査JSONのSHA-256は `53f64e49a1be7ea8709d48dd8a75b9984cb8e55818848de62ec5d88a07008bb9` である。
BAR summary本体75,487,436 bytesは今回の小原本監査では読まず、個別192件の重複欠落・費用・full summaryとの結合は後続PBS readerで確認する。
BAR正式finish265727もF/0・23分02秒となり、19:27:29 JSTの[限定監査](../../output/census_active_node_migration_v1/BAR_MAIN_FINISH_AUDIT_ja.md)でaccepted・completion・controls・collectedの一致と先のmanifest・submission監査への結合を確認した。
同監査JSONのSHA-256は `b7a7dbc90b10d1100c0074433d514e010ab7471fa5d1ca69c329f89e7d8d4167` で、receiptは `scientific_validation_complete=false` を保持する。
先頭MC/BAR両本計時の正式finish受理は完了し、後続265728はF/0・14分47秒で終了、次の `c0t0e1-mc-capacity` 本体265729がRとなった。
同identityのBAR投入前helper265730もRで、19:43:09 JSTの[割当監査](../../output/census_outer_operation_v1/C0T0E1_CAPACITY_ALLOCATION_2026-10-25_ja.md)で投入記録との結合と別2物理ノード・各96 CPU以内を確認した。
MCの推定器開始記録は同監査時点で未生成であり、先頭組以外の独立本計時完了とは扱わない。
その後19:46 JSTには次MCの開始・native記録、19:49 JSTには実PBS F/0・7分15秒と小要約の2/2・failed/unavailable各0を確認した。
次MCの正式capacity finishと本計時192反復は未完了であり、個別recordの監査や全体の科学検証へ範囲を拡張しない。
19:57 JSTにはBAR投入前検証265730もF/0・14分45秒となり、BAR予備計時265731とMC終了確認265732がRへ進んだ。
19:58 JSTにこの2jobが別2物理ノード・各96 CPU以内であることを実PBSで確認し、詳しい記録を状態文書に追記した。
20:05 JSTには次BAR予備計時265731もF/0・7分49秒となり、小要約2/2・failed/unavailable各0を確認した。
MC終了確認265732はF/0・3分45秒となり、正式capacity finish265733がRへ進んだが、当該組の正式finish受理と本計時192反復は未完了である。
その後20:43:38 JSTの[限定監査](../../output/census_active_node_migration_v1/MC_E1_CAPACITY_FINISH_AUDIT_ja.md)で265733のF/0・41分24秒と正式capacity受理、本192反復計画への結合、反復0〜191の重複欠落なしを確認した。
同監査JSONのSHA-256は `8861209b44d20e4c456787db24a8ed88fda00a569f30e8b6313becefb5fd458b` であり、本計時のsubmission・execution-intent・summaryは同観測時点で未生成だった。
20:47 JSTには次BARの終了確認265734がF/0・3分45秒となり、正式capacity finish265735がRへ進んだ。
当該組のBAR正式capacity受理と両本計時は引き続き未完了である。
21:02 JSTには265735のRとBAR本計時の資源決定を確認し、反復0〜191の1 partition・21 workers・96 CPU・337 GB・要求1時間を記録した。
資源決定原本のSHA-256は `8b2fd379a27b08482fc0969ca89264a7100c000e57f919406f4a93c0ab5d5d43` で、同時点ではprepared-partitionとcompletedは未生成であり、本計時の開始・完了の証拠ではない。
その後21:29:44 JSTの[限定監査](../../output/census_active_node_migration_v1/BAR_E1_CAPACITY_FINISH_AUDIT_ja.md)で265735のF/0・41分52秒とBAR正式capacity受理、本192反復計画への結合を確認した。
監査JSONのSHA-256は `b34353c1e509983686baa7d21240b8c256ba2878922c9470c55733af1c9293c1` で、当該BAR本計時のsubmission・execution-intent・summaryは観測時点で未生成だった。
後続265736はRで、stateでは `c0t0e1-mc-main0` の投入前処理に進んだが、本計時job IDはまだ未記録だった。
独立本計時の正式受理済み件数は2/24であり、capacity4件を含むterminal6件とは区別する。
22:16:19 JSTの[実割当監査](../../output/census_outer_operation_v1/MC_E1_MAIN_ALLOCATION_2026-10-25_ja.md)では265736のF/0・解放と、次MC本計時265737のqsub投入・R・96 CPU・337 GiB・要求30分を確認した。
次BAR投入前helper265738もRで、両者は別2物理ノード・各96 CPU以内、配置未確定の所有jobなしだった。
監査原本のSHA-256は `db14fbe343dcb8a47e29986f91f2c3bb08ab39994f4c4908852f0787ebac7753` であり、MCの推定器開始記録は同時点で未生成、本計時の完了件数は増えていない。
MC個別192件の監査済み範囲とBAR小原本の監査範囲を区別し、先頭MC/BARの結果を独立計時48行・各192分母の完了と混同しない。
独立計時全体、最終科学評価・report、最終証拠の統合保存は未完了であり、以下の11:43以前の時刻付き記録は履歴として保持する。

## 完了確認と残要件（2026-10-25の文書監査）

下表は現行の草案・保存索引・状態文書を突き合わせた完了確認と残作業であり、本表の編集で数値を再計算していない。
11:43 JSTまでの[状態文書](PROJECT_STATUS_2026-10-24_ja.md)ではcensus265703・seal265707・collect265708のF/0と正式受理、独立計時準備265709の開始を確認しており、完了済み元14ジョブと受理済み比較は再計算しない。

| 作業・状態 | 具体的な次アクションと完了証拠 |
|---|---|
| 1. 完了：独立seedの全件照合 | [保存結果と正式受理](data_tile_validation_2026-10-17/low_timing_full_census_v13_20261025/README_ja.md)で全4,208,002件・予期しない衝突0、catalogの役割別件数、source/inputの前後記録、PBS終端、回収13原本とmanifest21項目の一致を確認した。統計的独立性の数学的証明や実sampling metadata全件の監査とは区別する。 |
| 2. 独立計時と効率評価 | 選択24組合せからMC/BAR計48行・各192分母を回収し、選択cohortと異なるseed、実行・非選択・未実行・失敗の理由、reference感度と各clockの費用を確認する。未収集診断を実測警告にせず、費用比較が成立しない条件も理由付きで残す。 |
| 3. 科学的結論と利用例の統合 | 受理済み全12条件の比較、上の独立計時、主4条件の既存結果を最終JSON・日本語報告へ対応づける。選択用cohortの24行射影は新しい独立校正ではなく、非選択行のnullだけでその条件の比較結果を代表しない。非選択条件もreference幅・分類数・保存済み診断の根拠へ結び、推奨・非推奨・未判定と固定prior・符号・noise・decoder・設定を利用例に対応させる。 |
| 4. 最終証拠と実行sourceの保存 | 完成したcensus・独立計時・report・controller終端と、その実source・環境・設定・seed・qsub/回収scriptを既存snapshotの差分として保存し、元hash・共有後hash・依存と外部入力の索引を更新する。v13 snapshotは265700の10:19:22 JSTのR観測までであり、これら最終証拠を含まない。 |
| 5. 再現手順と取得可能性の明示 | 公開版、未公開working tree、private archive、外部raw/nativeを分けた引渡し表を確定する。既存READMEの別workspace再構築順を実source・必要入力・実コマンドへの参照と結び、不明な取得条件・保持期限・過去consumed hashの限界を明記する。最終報告・状態文書・小receiptから同じ原本をたどれることを照合する。 |

既存[公開確認](publication_state_check_2026-10-25.json)はpublic main `837a96b8836ba8c81043fcba15b065eb1a8b5296` とexperimental Releaseの5 assetsを確認し、working_tree_changes_published=falseを記録している。
今回の限定したgit statusでも、固定prior workflowは変更中、最終報告・本監査・再現用READMEは未追跡であり、公開mainやReleaseに含まれる資料とは扱わない。
公開済み状態の維持と、後続成果物の保存・取得手順の完成を区別し、今回の文書監査から追加公開・commit・pushは行わない。

[raw取得索引](raw_access_followup_2026-10-25_ja.md)には低ノイズ12条件の実prepared世代と36 control pin、portable7条件の273 ZIP起点、主計時の5 archiveがある。
19:12:06 JSTの[指定ZIP限定stat](portable_zip_stat_observation_2026-10-25.json)で273/273件の通常file・非symlinkとしての現存、欠落・未観測各0、合計42,880,266,375 bytesを確認した。
この観測原本のSHA-256は `9b2f385d8150c5f80eb948336f64a30f25c929d93e49841bb34592fa64194869` であり、ZIPの内容再照合・全raw容量・第三者取得可能性の証明とは区別する。
これらの既存回収証拠・所在を引き継ぎ、全rawの現在bytes・総容量・第三者権限・提供条件・保持期限・backupが未確認の範囲を、消失や未保存と取り違えない。
保存原本の消失が判明した具体例はなく、全rawの再hash・無条件公開・別環境での全計算再実行を新たな完了条件にはしない。
ただしprivate pathやsnapshotだけで第三者による取得・実行可能性を宣言せず、[取得監査](reproduction_access_inventory_2026-10-25_ja.md)の不足を最終報告へ残す。

### 非選択条件を含む全12条件の科学評価をどう引き継ぐか

現行report source `20261025-finite-tail-report-environment-v1/cluster_scripts/tile_low_noise_timing_evaluation_report.py` のSHA-256 `c46a630e49c19d92c221c283dc43c7890fd5490cf37ebc151d4ac207e2c08c87` を静的に確認した。
inputsは受理済みselectionとscientific bundle内のselectionの完全一致を要求し、runはその全selectionを最終report.jsonのtop-level `selection` へ保存する。
したがって予定される `/selection/rows/<行>/candidates/<候補>/assessment` には、非選択条件を含む保存済みのbias・RMSE範囲、被覆・診断件数とその分母が残る。
`records[].selection` は縮約したplanning rowであり、このfieldだけを全校正評価の保存先と取り違えない。
現在のreport_ja.md生成は独立計時の結果が中心で、非選択条件の全校正bias・混合診断の説明表は出力しない。
これはsourceで確認した出力契約であり、未完成の実reportに値が既に保存されたという主張ではない。

追加の全候補抽出・候補再選択・再集計を作らず、最終日本語報告には次の既存の事前固定long sliceと原本を参照する対応表を加える。
固定long sliceは結果を見て選んだ最良候補ではなく、352設定全体の代替でもなく、符号・noise間で計算予算も異なることを保持する。

| 対象 | 再利用できる既存説明・小成果物 | 最終化時の対応 |
|---|---|---|
| tile72 bit、tile288 bit、tile72 depolarizingの各3確率 | [9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)と、そのmanifestに記録された144行のlong_settings.csv・reference情報 | 非選択理由・reference幅・診断の説明を既存の固定切り口に結び、全設定の値は最終JSONのcandidate assessmentを参照する。 |
| tile288 depolarizing p=0.01 | [C3T0個別報告](low_c3t0_result_2026-10-23_ja.md)とreviewのfixed_long_slice.csv | 既存の長い16設定の校正結果・有限reference幅・診断を保持し、独立計時の結果と分ける。 |
| tile288 depolarizing p=0.003 | [C3T1個別報告](low_c3t1_result_2026-10-23_ja.md)とreviewのfixed_long_slice.csv | 全352設定で保存された精度分類と診断の説明を再利用し、新しい校正や母精度の保証としない。 |
| tile288 depolarizing p=0.001 | [算術回収receipt](data_tile_validation_2026-10-17/c3t2_arithmetic_recovery_20261024_v1/receipt.json)、同reviewのmanifest・review.json・fixed_long_slice.csv | 元private hashと識別子置換後hashを区別し、広いreference区間と全192分母を説明する。16行CSVの原本hashは `5f3ce4dd0f6b833f0497161a12e7bfa3cdb59dea9a106c9ea3d1ba6cad47b592` である。 |

実report生成後に、top-level selectionの元pinへの対応、全24行の順序・identity、各条件の全候補件数、各assessmentの192分母と元fieldの値をPBS側で照合してから、この保存要件を完了とする。
日本語報告では非選択理由とreferenceの有無・幅を明示し、選択候補の24行射影、全候補の校正値、独立計時の48行を混同しない。
この対応確認と日本語への反映は未完了であり、既存sourceの読取りだけでは科学評価の最終報告完了としない。

## 現行の完了証拠を探す場所（v13、2026-10-25 10:25〜10:26 JST確認）

現行flow設定の固定pinからouter、effective設定をたどり、各4 MiB以下のJSONのSHA-256と出力先をSSHで読取り照合した。
flow設定は `20261025-low-parallel-controller-v13/flow-config.json`、SHA-256 `e68ac4d738c21c6d79ddf71a22f0dd8aa35456c4325507fccf48ca2cf547c0fa` である。
outerは `20261025-finite-tail-census-recovery-v13/config.json`、SHA-256 `a2c7b83d36b9c91b40af50214c78ad65afafb0506fa02da736741e3926da1a34` である。
effective設定は同階層の `effective-config.json`、SHA-256 `393c620fcca3c8b86e6dc3da8ec7a69eefd5f2099a2de97d8687d9b3a697c4d3` である。
以下のパスはクラスタ `$HOME/workspace/mcmc4qec` からの相対パスで、hashはprivate原本bytesを指す。

| 証拠・出力先 | 現行設定の実パス | 照合時の状態・今後の確認 |
|---|---|---|
| controller journal | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v13` | `resume-intent.json` と先行2roleのdirectoryが存在し、最終 `completed.json` は未作成。最終roleの結果と全要件を照合する。 |
| tail journal | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-tail-v13` | census準備・実行のdirectoryが存在。後続の `independent-execution`・`report-execution` の完了記録は未取得。 |
| 有限PBS action台帳 | `20261025-finite-tail-actions-v13` | roleごとの実submission・script・fresh qstat・completionを結合し、外側actionの成功と内側科学jobの完了を区別する。 |
| census構成／実job root | `20261025-low-parallel-census-config-v13` ／ `20261025-census-operational-bundle-v13/runs/all12-parallel-independent-timing-seed-census-v13` | 両rootが存在し、実job rootの直下は `catalog.json` と `manifest.json` のみ。全件照合の完了証拠ではない。 |
| 独立計時の入力／制御 | `20261025-low-parallel-independent-inputs-v9` ／ `20261025-low-parallel-independent-controls-v9` | 両rootとも未作成。生成後、実計時job・回収結果・全48行と各192分母へ結合する。 |
| 最終報告の入力／実job root | `20261025-low-parallel-report-inputs-v9` ／ `20261023-low-partition-report-job-v1/runs/report-all24-parallel-v9` | 両rootとも未作成。予定される `result/report.json`・`result/report_ja.md` とtail側の回収記録は未取得。 |
| 再利用するmerge／handoff | `20261025-low-parallel-front-v6/merge-parallel-v2` ／ `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v9/tail-handoff/completed.json` | 元受理済み原本を保持。旧名v9のhandoffと下流4rootは現effective設定が指す実pathであり、v13へ名前だけ置換しない。 |

10:24 JSTの[状態文書](PROJECT_STATUS_2026-10-24_ja.md)では準備265700のF/0と次の検証action265702のRを確認しており、この出力先照合ではjobを変更・停止・再投入していない。
既存directoryやstatus=readyを全件census、独立計時、最終報告の完了証拠とは扱わない。
古いv8・v9・v11の表は下に履歴として保持し、現行確認は本表と[再起動手順](cluster_resident_resume_2026-10-25_ja.md)から行う。

## 現行の到達点：2026-10-25 10:13 JST

実設定の組立265698と13通りの実constructor確認265699がF/0となり、loginのreadiness・起動previewを経て本番後処理を再開した。
後続専用v13 controllerは別SSHでPID1598334・start ticks770092111・command一致、生存とerrorなしを確認した。
初回census準備265700はR・run_count=1・walltime10秒であり、準備完了や全件census完了の証拠ではない。
元12worker・merge265660・acceptance265661の計14ジョブと受理済みcomparison・handoffを再利用し、再計算していない。
正式selection24行と独立計時48行・各192分母の対応、全件seed照合、最終reportと科学証拠・再現情報の保存は引き続き未完了である。
新source pinsと小原本は[接続受入記録](tail_census_resume_acceptance_2026-10-25_ja.md)、現行の起動記録と読取り確認先は[再起動手順](cluster_resident_resume_2026-10-25_ja.md)に保存する。
本稿の科学的な完了条件は変更せず、以下の停止・準備記録は履歴として保持する。

## 現行の到達点：2026-10-25の資源実測完了後

全12条件の元worker・merge265660・acceptance265661・comparison・handoffは受理済みであり、元計算の再実行は不要である。
[資源実測265678](census_measurement_submission_2026-10-25_ja.md)はF/0・run_count=1・walltime5分56秒で完了し、予定4,208,002件のうちpilot1,000件のunexpected collisionは0だった。
全件census・独立計時・最終reportの完了を示す結果ではない。
今回の元式の候補16 GiB・45分は旧メモリ上限のみを超えたが、元失敗265675の未保存値とは区別する。
本番後処理は停止中で、1 CPU・96 GiB・4時間の運用割当、専用環境と準備処理の接続、後続だけを再開する制御処理を修正・検証している。
予算枠をETAと扱わず、旧失敗rootと受理済み結果を保持する。

残る受入対象は、全件seed照合、正式selection24行と独立計時48行・各192分母の対応、未実行等の理由、最終report2ファイルと実PBS完了証拠、追加source・環境・原本の保存と再現手順である。
再開処理のfixture成功を科学工程の完了に読み替えず、最終成果物を本書の全要件と照合する。
以下の時刻付き到達点と保存記録は履歴として保持する。

## 現行の到達点：2026-10-25 09:29 JST

元12worker・merge265660・acceptance265661・comparison・handoffの受理は保持され、元計算の再実行はしていない。
後続census準備265675はF/1・run_count=1・walltime13分32秒・CPU時間13分24秒・PBS記録mem15,084,044KBで終了し、v12 controllerのPID1432966は不在である。
1,000件pilotのcollision=0を確認した後、計測値保存前に `measured census exceeds two-hour / four-GiB ceiling` で拒否され、個別の時間・メモリ超過と実predictionは未確定である。
先行bundle検証を含むpeak selfRSSが判定へ入った可能性を調査中で、PBS記録memと同じ値とは断定しない。
censusの `planning-failure.json` は `root_reusable:false`、catalog・manifest・prepare受理記録は未作成で、科学bundle1,757,600,835 bytesとconfigを保持する。
小証跡はlocal `output/low_parallel_flow_v11/census-failure-readonly.json` にあり、資源計測保存と新計画を準備中である。
独立計時48行・各192分母、後段reportとの正式selection24行の対応照合、最終科学証拠の統合保存は未完了、全体ETAは未定である。
[v12復旧差分保存](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)265676のF/0・10 fixture・source参照94件・metadata109件のprivate保存は完了済みであり、今回のcensus準備失敗や未完了の科学検証と区別する。
以下の旧到達点と保存記録は履歴として保持する。

## 2026-10-25 09:15 JSTの到達点

元の12worker・merge265660・acceptance265661を再実行せず採用するv12 controllerを起動し、別SSHでPID1432966・start ticks769736422・全command一致、生存・errors空を確認した。
native265673はF/0・18秒、tail265674はF/0・7秒で、実constructorとlogin namespace roundtripまでの[独立レビュー](cross_host_artifact_stat_review_2026-10-25_ja.md)を完了した。
現行configは `20261025-low-parallel-controller-v12/flow-config.json`、SHA-256 `083a22ca37fe46eb31f2f1034554f76aeffa77e77c273e33627e14e67318838e`、sourceは `20261024-c3t2-index-relocation-v1/output/low_parallel_flow_v11/flow.py`、SHA-256 `c08c21a859fccaaef227ed603f9aaf76a5403d0f7892e1a528dbaedaf27d088b` である。
tail設定は `20261025-finite-tail-cross-host-v2/config.json`、SHA-256 `873a2c5cbde9693e7007b17a5b40ceac028ceb9533f78b428446489e133a6d3b` で、元の科学設定・資源・未使用出力先を保持する。

`pipeline-state/parallel-flow-v12/comparison-completed.json` 本文で `all_twelve_processed=true` と元merge265660・acceptance265661への結合を確認した。
同comparisonのSHA-256は `53470c42aa0bc554c0401ccfadebd93866edf55eadd5a3b3eebd623d1b597db2` で、`independent_timing_performed=false`・`nominal_coverage_certified=false` を保持する。
継承した `pipeline-state/parallel-flow-v9/tail-handoff/completed.json` も `partition_started=true`・`flow_completed=true`・`cluster_controller=true` で、新v12 configに結合したSHA-256 `83bc44cf948494283a07b517a65e55f3a0b75e69929ae1d4ff39f7d583ce754b` を確認した。
これらのpipeline-state相対パスの基準は `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1` であり、config・tail設定の基準はworkspace直下とする。
selection24行の内容は元acceptanceの検証に依拠し、この小metadata確認で巨大selectionを読み直しておらず、後段reportとの対応照合は残る。
09:15:07 JSTの初回有限tail265675はR・walltime48秒・CPU時間46秒で、census準備へ進んだが、その完了や独立計時48行・各192分母・最終reportは未完了である。
小原本はlocal `output/low_parallel_flow_v11/first-tail.json` に保存し、現在の起動pinと読取り確認先は[再起動手順](cluster_resident_resume_2026-10-25_ja.md)を参照する。
旧stat失敗と元proofを保持し、全体ETAは未定である。
その後、265676のF/0・10 fixture成功と実採取により、[v12復旧差分](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)のsource参照94件・metadata109件のprivate保存を完了した。
初版inventoryの独立レビュー後に追加したPBS開始記録1件も原本hash・job結合を別SSHで照合したが、今後の独立計時・最終科学proofの保存は未完了である。
以下の08:49以前の停止・復旧準備は履歴として保持する。

## 2026-10-25 08:49 JST時点の到達点

本番merge265660とacceptance265661はF/0・run_count=1で、walltimeはそれぞれ1時間58分44秒・2分37秒、CPU時間は3時間19分30秒・2分31秒だった。
acceptance completionは `original_accept_terminal_executed=true` とPBS内のproduction selection生成を記録するが、controllerの統合受理・handoffは未完了である。
v11 controllerは `Previously PBS-verified artifact stat changed` を検出して停止し、PID1145733不在・`automatic_retry=false` を確認した。
独立した小metadata検査では4artifactの差はhost-localなdevice番号だけで、inode・size・mtime_ns・ctime_ns・modeとcanonicalな通常file・非symlinkの条件は一致していた。
元の重い計算・終端受理をやり直さず、元wrapper・proof・hash・sourceを保持するobserver移行を準備中で、本番再開は未完了である。
[v11差分保存](finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md)265662はF/0で8fixtureと実採取に成功し、source参照474件・metadata109件をprivate保存した。
このscopeはmergeの科学result・後続proof・可変journalを含まず、独立計時48行と各192分母・最終report・全科学証拠の統合保存は未完了、全体ETAは未定である。
以下の06:47までの稼働・保存準備の記録と実パスは履歴として保持する。

## 2026-10-25 06:47 JST時点の到達点

元12workerは全てF/0となり、v11 controllerが既存terminal12件を採用した。
新merge265660はR・run_count=1で、06:47 JSTのwalltime1分50秒・CPU時間3分25秒を確認したが、深い全12条件受理・selection24行・独立計時48行と各192分母・最終reportは未完了である。
controllerはPID1145733・start ticks768839164・journal v11で生存・errorなしと確認され、全体ETAは未定である。
現行の実パスと到達証拠は末尾の「追補：v11復旧後」に固定し、以下のv8・v9のパスと観測は履歴として保持する。
v9までの保存snapshotを、後続のv11制御source・設定・実merge証拠まで保存済みとは扱わず、新しい採取は準備中・未完了である。

## 初回監査時点の記録

2026-10-25 02:53:50 JSTの状態と、既存の小さい文書・固定config・実行コードの読取りに基づく。
新しい科学計算・ローカルテスト・ジョブ投入は行っていない。
この文書は成果物の完了条件を整理したものであり、[最終報告の草案](final_validation_report_draft_2026-10-24_ja.md)や受入試験の成功を科学検証の完了とは扱わない。
実ジョブの最新状態は[状態文書](PROJECT_STATUS_2026-10-24_ja.md)と[復旧結果](cluster_postprocess_recovery_result_2026-10-24_ja.md)の観測時刻で判断する。
この観測ではv8 controllerは起動識別情報が一致して生存し、error記録はなく、5件F/0のterminal回収と7件Rを確認した。
全12条件の深い結果受理、本番merge、独立計時、最終報告はまだ完了していない。
その後の[巨大metadata境界監査](tail_large_metadata_boundary_review_2026-10-25_ja.md)で、merge終端の受理とtail管理経路に非PBSでの大容量処理が残ることを確認した。
以下のv8実パスは初回監査時点と過去の証拠を探す起点として保持し、その後の切替・復旧は追補の時刻と実pinで区別する。

## 残る成果物と完了条件

| 項目 | 既存の根拠 | 残る成果物・確認 |
|---|---|---|
| 主4条件の校正 | [tile検証報告](tile_validation_report_2026-10-18_ja.md)、[主4条件の再集約](data_tile_validation_2026-10-17/final_reaggregation_four_case_scientific_summary_v1_ja.md) | 最終報告へ結果と限界を統合し、有限MC referenceを真値とせず、その不確実性と設定間のtrace共有を明記する。 |
| 低ノイズ全12条件の正式比較 | [途中利用案内](low_noise_interim_usage_2026-10-23_ja.md)、[最後の条件の算術照合receipt](data_tile_validation_2026-10-17/c3t2_arithmetic_recovery_20261024_v1/receipt.json) | 元PBS受理とv12 comparisonの全12条件受理を確認済み。12×352設定×192 seedの基礎811,008行を含む原本入力の保存・由来と、別成果物の正式selection24行を区別し、後段reportへ結合した保存・内容の対応を確認する。 |
| bias・RMSE・95%区間の被覆 | [検証計画](tile_validation_plan_2026-10-17_ja.md)、上記の主4条件報告と低ノイズ途中報告 | 全12条件の点推定・区間・reference感度を統合し、未収束・診断未定義・区間未取得を分母から除外しない。 |
| 混合とkernelの適用限界 | [支持の検討](tile_kernel_support_2026-10-17_ja.md)、[主4条件の混合比較](data_tile_validation_2026-10-17/mixing_comparison_four_case_v1/report_ja.md) | 全12条件の診断を設定・初期化・logical sectorに対応付け、diagnostic_not_collectedと実測された収束警告を区別する。未収集を警告の実測値へ読み替えない。 |
| 独立計時と計算効率 | [主ノイズの独立計時レビュー](data_tile_validation_2026-10-17/main_timing_scientific_review_v1/report_ja.md)、[分割集約から最終報告への接続](low_partition_report_result_2026-10-23_ja.md) | 正式selection24行に結合した独立seed census、計時入力、実ジョブ、回収結果を保存する。12条件×2精度目標×MC/BARの48行に各192分母を保持し、非選択・対象なし・未実行の理由を残す。 |
| decoder・符号・noise・failure定義 | [tile検証報告](tile_validation_report_2026-10-18_ja.md)、[prior感度](tile_decoder_prior_effect_2026-10-18_ja.md)、[platform差](tile_decoder_platform_2026-10-17_ja.md)、[追加decoder検証](basic_decoders_validation_2026-10-18_ja.md) | 最終設定表に固定prior、native版とbinary、反復数、OSD設定、joint noiseとsector近似の区別、再現性の適用範囲を明記する。 |
| 利用例・推奨設定・適用限界 | [decoder利用例](basic_decoders_usage_2026-10-18_ja.md)、[API](../api_en.md)、[tutorial](../tutorial_en.md)、[英語の検証状況](../tile_validation_interim_en.md) | 確定した推奨・非推奨・未判定を利用例と相互参照し、短い例や追加decoderの受入試験を科学的校正と混同しない。 |
| 日本語の最終報告と状態文書 | [草案](final_validation_report_draft_2026-10-24_ja.md)、[goal状態](goal_completion_status_2026-10-23_ja.md) | 本番merge・独立計時の受理済み証拠に結合したreport.jsonとreport_ja.mdを回収し、要件ごとの完了・否定結果・未取得を照合して正式報告へ反映する。 |
| source・metadataの保存 | [v5 snapshot](reproduction_snapshot_v2_spec_2026-10-25_ja.md)、[v8 snapshot](reproduction_snapshot_v8_spec_2026-10-25_ja.md)、[v9追加保存](finite_flow_v9_snapshot_acceptance_2026-10-25_ja.md)、[v11差分](finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md)、[v12差分](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)、[v13差分](finite_flow_v13_delta_snapshot_acceptance_2026-10-25_ja.md) | 既存原本を保持し、v11のsource参照474件・metadata109件に続き、v12の94件・109件をPBS265676、v13の92件・217件をPBS265701でprivate保存済み。v12はnamespace・observer等、v13は資源計測・専用環境・接続受入・設定・起動を含む有限差分である。v13の265700観測は10:19:22 JSTのRまでで、後の準備完了・全件census・独立計時・最終reportの証拠、科学payload・可変journalは未収録。これら最終科学証拠の統合保存は残る。 |
| 生データ・環境・再現手順 | 各結果のreceipt、manifest、environment、seedと設定、ジョブ台帳 | snapshotだけで科学的な完全再現を達成したとはしない。下記の保存監査を完了し、通常cloneまたは明示した配布archiveから再現に必要な実装と入力を取得できるようにする。 |

独立計時で対象が選ばれない場合は、事前規則・選択結果・対象なしの理由と全48行を保存する。
対象なしを独立計時の実施済み結果へ読み替えない。
CPU時間・wall時間・処理範囲・計算機差を記録し、PBSの待機時間やjob全体のwall時間をそのまま推定法の費用としない。
同精度に達した比較が成立しない条件の費用比は、理由付きの未判定として残す。
独立referenceがない、または不十分な領域では、設定間や広いWSS区間との整合を精度・被覆の保証としない。
支持の連結性、詳細釣合い、非周期性と実測診断を分け、診断良好を収束の証明としない。
精度未達や非推奨は記録可能な検証結果であり、処理未完了による証拠不足とは別である。

## 本番の完了証拠を探す場所（v8初回監査時点）

この初回監査時点ではcontroller設定v8、`output/low_parallel_flow_v6/flow.py`、front v6、`output/low_parallel_recovery_merge_v6/`、tail v3とtail設定v8を使っていた。
起動記録と読取り専用の確認手順は[クラスタ常駐処理の再開記録](cluster_resident_resume_2026-10-25_ja.md)にある。
以下のパスはクラスタの `$HOME/workspace/mcmc4qec` からの相対パスであり、Windows側の環境変数として展開しない。

| 記号・入力 | 実パスと照合対象 |
|---|---|
| flow設定 | `20261025-low-parallel-controller-v8/flow-config.json`、SHA-256 `6130af78e5924a299e044195e584b7419affedeecdda393f7842de1bb19c0e43` |
| F：flow journal | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v8` |
| front準備 | `20261025-low-parallel-front-v6/prepared-receipt.json`、SHA-256 `22eedcbfb42b9ef6ce3d286b539630491efeb80fd0317287fb31fc6ca8c3e058` |
| M：本番merge | `20261025-low-parallel-front-v6/merge-parallel-v1` |
| tail設定 | `20261025-low-parallel-tail-config-v8/tail-config.json`、SHA-256 `e91b41145b18198161bf8f877af176b9512f943ec9ac52d56dcfc08cf553bb5f` |
| T：tail journal | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-tail-v8` |
| R：報告job | `20261023-low-partition-report-job-v1/runs/report-all24-parallel-v8` |

front v6はindex 0だけを新worker265605に置き換え、index 1・6・7・8はfront v4、index 2・3・4・5・9・10・11はfront v5の実preparedを保持する。
各workerのmanifest・runner・submission ledger・実job IDをその実行時の記録へ照合し、全12件が新manifestで実行されたように読み替えない。
次の順で完了証拠を確認し、未作成のファイルは完了予定の出力であって取得済み証拠ではない。

1. `F/worker-<index>-finished.json` と各workerの元prepared・ledger・PBS終端を照合する。
   F/0とterminal回収だけでは、入力closureと科学的選択値の深い受理は完了していない。
2. `M/submission.json` と本番mergeのPBS正常終了、`M/accepted.json` の `production_selection_validated=true`・実job ID、`M/selection.json` のpinを照合する。
   全12条件の原本入力・基礎811,008行の保持と、selection24行の完全性を別々に確認する。
3. `F/comparison-completed.json` の `merge_accepted`・`selection`・12workerとmergeの実job ID、`all_twelve_processed=true` を確認する。
   この段階の `independent_timing_performed=false` と `nominal_coverage_certified=false` を維持し、独立計時完了や被覆保証へ拡張しない。
4. `F/tail-handoff/completed.json` をtail設定の `handoff_path` と照合し、`partition_started=true`・`flow_completed=true` と同じmerge・selectionのpinを確認する。
5. `T/census-preparation`、`T/census-execution`、`T/independent-preparation`、`T/independent-execution`、`T/report-preparation`、`T/report-execution` の順に各receipt・accepted・completedを読む。
   独立計時の48行・192分母、実行対象と非選択理由を照合し、対象なし経路の完了を計時実施済みとは数えない。
6. `T/report-execution/completed.json` で `status=report_completed`・`report_completed=true`・`collection_verified=true` を確認する。
   `outputs` は `report.json` と `report_ja.md` の2件で、元パスが `R/result/<名前>`、記録hashが `T/report-execution/collected/result/<名前>` のbytesと一致することを確認する。
7. `F/final-report/stdout.log` の検証結果と `F/completed.json` の `all_stages_completed=true`、`final_report`、`comparison` pinを照合する。
   controllerの終了や最終ファイルの存在だけで完了とは判定せず、回収済み日本語報告の内容を本監査表の全要件と照合する。

tail v3の `final-report` roleは固定source・環境・完了記録・報告2ファイルのhashを読む検証であり、現在は未実施である。
この経路をコードで読めることやfixture受入の成功は、本番が完了条件を満たした証拠ではない。

旧ローカル待受の `data_tile_validation_2026-10-17/low_partition_report_execution_v2/`、`low_partition_independent_execution_v1/`、`low_partition_independent_preparation_v1/`、`low_timing_partition_census_execution_v1/` は、この監査時点ではintentと待機観測のみだった。
それらのdirectoryの存在を本番完了と数えず、移行後のconfigが指すjournalと回収receiptを一次資料とする。

## 保存と再現可能性の監査

本goalの保存要件は、必要な原本・source・設定・環境・seed・scriptの保存、所在と取得可能性の索引、再現手順と限界の記録として監査する。
別環境で全科学計算を再実行して完全一致を証明することや、全rawを無条件で一般公開することを追加の必須要件とはしない。
ただし未取得・未保存の原本を保存済みと扱わず、private保存と第三者への提供可能性、科学的な再実行検証を分けて記録する。

`.gitignore` は `output/` と `docs/wp/data_*/` を除外しており、既存追跡ファイル以外は通常のgit addで保存されない。
今回の算術照合 `c3t2_arithmetic_recovery_20261024_v1/completed.json` と受入記録 `parallel_recovery_acceptance_20261024_v1/receipt.json` は、監査時点ではignoredでgit ls-filesにも含まれていなかった。
これらはローカルに保存されているが、GitHubや新しいcloneで取得できる状態とは区別する。

並列dispatch・flow・merge・tail、physical capacity、worker binding、PBS projectionと関連テストは `output/` 内にある。
後段のcensus・独立計時・報告driverと、そこからimportされるhelperも同様に保存対象を確認する必要がある。
受入receiptやsources.jsonにsource hashがあっても、対応するsource bytes自体が配布物に含まれるとは限らない。
特に今回の小さい受入記録と算術照合の回収物は、参照された全sourceや全raw traceのarchiveではない。

本番で使用するコードが固定され受入を通った後、実際に解決されたsourceと依存helperの全体、受入テスト、設定、環境、seed仕様、qsub手順、収集・照合・再集約手順を識別子除去済みarchiveとmanifestへ保存する。
v5 snapshot265599のprivate保存済みsource1031参照・metadata75件・参照edge19692件と、v8 snapshot265617のsource1252参照・metadata112件・参照edge31512件は別のscopeとして管理する。
v8の対象はfront v6・並列merge v6・tail v3/設定v8・実controllerの明示された資料と歴史的baselineであり、保存完了receiptの原本hashを確認した。
snapshotの保存、公開用識別子除去、raw/nativeの取得、環境再構築、科学的な完全再現、最終証拠の保存を別々に判定する。
現在は科学的な完全再現と全12条件・独立計時・最終報告の証拠保存を達成していない。
生データは所在・形式・量・hash・取得手順・保存期限を索引に記録し、公開しない大容量原本は保管場所と利用条件を明示する。
生データ索引のみで、原本の永続保存や再計算可能性まで検証済みと扱わない。
元sourceと公開用sourceに置換差がある場合は、原本hash・保存後hash・変更理由の対応を残す。
クラスタのユーザー名・ホスト名・個人の絶対homeパスを追跡ファイルへ追加しない。
選択的な追跡追加または配布archiveへの格納は別作業とし、この監査ではgit add・commit・pushを行っていない。

2026年10月25日の追加監査でも、今回のtail受入と算術照合の対象directoryは `git ls-files` に含まれていなかった。
保存用の小規模toolは [`tools/reproducibility/`](../../tools/reproducibility/README.md) に新規作成し、実行中のimmutable bundleやmain package sourceを変更しない。
具体的な最小closure、元hashと公開hashの区別、任意workspaceへ再配置する際の再pin範囲は[追加保存計画](reproduction_archive_plan_2026-10-25_ja.md)に記録する。
documentary archiveの作成だけで再現完了とはせず、大容量入力の取得、依存関係の不足、実環境の再構築と受入を別に確認する。

主4条件の過去の集計には、分析当時の消費trace・anchor hashを完全には再構成できない制約がある。
後日のpayload監査を、過去の入力をその時点で固定した証拠に置き換えず、[tile検証報告](tile_validation_report_2026-10-18_ja.md)の制約を最終報告にも引き継ぐ。
全項目を確認するまでgoalを完了扱いにせず、主4条件だけ・全12条件の入力完成だけ・fixture受入だけへ完了範囲を縮小しない。

## 追補：有限PBS処理への切替と完了証拠（2026-10-25）

2026-10-25 04:18:38 JSTの別SSH観測で、新設定v9のcontrollerへの本番切替を確認した。
PID 898820・start ticks 767964369の生存と起動識別子一致、旧controllerの不在、9件のworker terminal採用、`errors={}`・`completed=false` を小さい起動後観測と照合した。
元workerの残り3件は処理中で、本番merge・acceptance・tail完了の証拠はまだ取得していない。
上記の実設定v8とその表は過去の証拠を探す起点として保持し、この時点の切替後の一次資料には以下の実設定v9を使っていた。
新しいflow sourceは `output/low_parallel_flow_v8/flow.py` であり、ここでのsource版v8と、旧controller設定v8を混同しない。
実flow設定v9はPBS265644のnative受入F/0を経て起動され、そのaccepted原本SHA-256は `1c95d2ed0ab6095cf2ef903f0fb18865a408f2e1b74387758791c83d2d0ad96d` である。
起動記録と別SSH観測の原本は `output/low_parallel_flow_v8/start-actual-executed.stdout` と `post-start-observation.json` に保存する。
既存front v6の全12件の実prepared・manifest・job IDと、上記Mのmerge rootを引き継ぐ設計であり、workerを再実行したことにはしない。

小さい受入記録とsourceの読取りで確認した範囲は次のとおりである。

| PBS job番号 | 確認済みの範囲 | 本番証拠との区別 |
|---|---|---|
| 265626、F/0 | 新flowの84 fixture | 実設定v9の生成・native受入・controller起動の証拠ではない。 |
| 265628・265629、F/0 | merge acceptance v2の31 fixtureと実CLI probe | 本番merge preparedの検査と本番accept_terminalは未実施。 |
| 265633、F/0 | family・dispatch・collection・共通jobの96 fixture | 実科学payloadの後段処理全経路の完了ではない。 |
| 265641、F/0 | outer 68件・binding 21件・native用pure fixture 6件、計95件 | receiptは `actual_native_pipeline_accepted=false`・`scientific_payload_executed=false` を明示する。 |

265626のaccepted原本SHA-256は `afc45be918cad190ea149fbfebcf4e4b3439d4243bbf5d0877d50755f6f35a28`、265641は `5ce224502426470bbab29eaa2d71275cb6a67caaa9574334fe4c2402184c09b5` であり、いずれも識別子除去前の原本を指す。
小証跡はそれぞれ `output/low_parallel_flow_v8/fixture-acceptance.json`、`output/finite-tail-outer-tests-v2-evidence/`、merge acceptanceは `output/merge_terminal_acceptance_v2_evidence/` に保存され、公開・追跡済みとは限らない。
family受入の失敗原本と再試験の区別は[有限PBS受入記録](finite_tail_fixture_acceptance_2026-10-25_ja.md)に残す。

source上の受理順は、本番で次の証拠を取得するための契約として確認した。

1. 元mergeの実jobと別のacceptance jobを束縛し、acceptance自身の実PBS allocationと同一job内のnative preflightを確認した後、元の `accept_terminal` を実行する。
   既存のaccepted・selectionの意味を保持し、新comparisonには `merge_job`・`acceptance_job`・`acceptance_completion` と元accepted・selectionのpinを併記する。
2. flow handoffを読むfinite outerは、同じacceptance completion・元merge ID・selection pinを照合してからcensus準備へ進む。
   各有限actionではprepared・operation・payload・source・実PBS終端F/0・completionを結合し、元の科学的検査をPBS内で行う。
3. 子jobの投入は、元submitのdeep検査を済ませてqsub直前で停止し、親actionの退場後に実gateと元lock・script・intentを再確認して一度だけqsubする。
   外側の大容量controlに対するstat照合やalias検査を、独立した内容hash検証やraw全体の不変性の保証には読み替えない。

切替後の実config・起動receiptから確認した探索場所は次のとおりであり、パスの基準は上記と同じクラスタの `$HOME/workspace/mcmc4qec` とする。

| 証拠 | 実パス・固定値 |
|---|---|
| flow設定 | `20261025-low-parallel-controller-v9/flow-config.json`、SHA-256 `5b44a838edcf35f9d02d119c323530ef17bab880aeb8c29e74ff3fe81c4748ed` |
| flow source | `20261024-c3t2-index-relocation-v1/output/low_parallel_flow_v8/flow.py`、SHA-256 `58ada8dedaf393d01f501a9615ee7e920146c6596989b20c1b0f67b47a21e138` |
| F9：flow journal・起動 | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v9`、起動は同階層の `parallel-flow-v9-launch` |
| merge・acceptance | 元M `20261025-low-parallel-front-v6/merge-parallel-v1`、別acceptanceは `20261025-low-merge-terminal-acceptance-v1` |
| outer設定 | `20261025-finite-tail-outer-v9/config.json`、SHA-256 `f4dc8a4b9ff57cbe2c1f6e8867fd2d31b4b1b6c09be57a812c353681a7cbf114` |
| 内側tail設定 | `20261025-low-parallel-tail-config-v9/tail-config.json`、SHA-256 `eed3366d1be6737a2ab283d2bd5db3370c10c3c8c164f8010dc48734e466119c` |
| T9：tail journal | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-tail-v9` |
| A9：有限action | `20261025-finite-tail-actions-v9/<role>/<連番-action>/` |

F9の `comparison-completed.json` と `tail-handoff/completed.json` を元M・別acceptanceのreceiptへ結合し、T9の6段階のjournalを順に確認する。
A9の各 `accepted.json` が指すprepared・PBS終端・completionを照合し、submitでは `dispatch-completed.json` の元形式submissionと子の実job IDも確認する。
最終段階ではT9の `report-execution/completed.json` が指す回収報告2ファイルと、`finite-final-report.json` が指す有限final-reportの実F/0・completionを照合する。
さらにF9の `final-report/stdout.log` と `completed.json` を結合し、上記の全成果物要件を満たして初めて完了と判定する。
これらの未作成receiptは探索対象であり、controller起動や9件のterminal採用を最終完了の証拠とはしない。

最初の照会時点ではouter実設定組立のPBS265642は投入済み・完了未確認だったが、その後の[識別子を省いた受入証跡](data/finite_tail_outer_native_20261025/receipt.json)で265642の組立と265643の全6role各2経路＋final-reportの計13 constructor・実CLI確認がともにF/0であることを確認した。
265642のprepared receipt原本SHA-256は `fb0be410d0393c42422b84a3cf89f4c5c04de65014517f144f4aed95106bf540`、265643のaccepted原本は `95cf799d681479553f2817f21705df22585d539b68da2c12f03c7f3461c3d990` であり、回収証跡はprivate保存で公開済みとは扱わない。
constructor受入の `scientific_payloads_read=false` のとおり、この受入と後続のcontroller切替は、本番の大容量入力に対する科学的検査やmerge・acceptance・tailの完了を示すものではない。
受入順をsourceから確認できることと、この順で本番が完了したことを分けて記録する。

移行によって、正式selection24行、独立計時・報告48行と各192分母、未実行・非選択・診断未収集の理由、全要件に対応する日本語最終報告と原本保存の完了条件は変えない。
本番で追加されるsource・設定・実PBS receiptは既存v8 snapshotに保存済みとは扱わず、最終保存索引へ追加する。
科学的な全再実行や全rawの一般公開を新たな必須条件にはせず、必要な原本保存・取得手順・再現手順とその限界を確認するという本監査の範囲を維持する。

## 追補：v11復旧後の現行到達証拠（2026-10-25 06:47 JST）

全12workerの正常終端後、旧v9はparent selectorのalias照合で停止し、旧v10のmerge265651は後段worker verifierのalias照合でF/1・walltime6秒となった。
それぞれのerror・config・journalと旧merge rootを保存し、元worker・values・科学source・native環境・seed・資源設定を変更せず、新しいmerge rootとv11 controllerへ移行した。
[worker alias復旧仕様と受入](worker_alias_recovery_flow_spec_2026-10-25_ja.md)および[tail移設の受入](finite_tail_merge_relocation_2026-10-25_ja.md)で、許可した差分と実metadata確認を科学payloadの深い受理から区別している。
265657の31fixture、265658の実12terminal採用と隔離prepare、265659の12fixtureと実13constructorはF/0であり、これらを本番merge完了とは扱わない。
v11の実起動後、PID1145733・start ticks768839164・command一致、生存・errorなし、12terminal採用を確認した。
本番merge265660はqsub投入済みで、06:47 JSTにはR・run_count=1・8CPU・32GiB、walltime1分50秒・CPU時間3分25秒であり、終了受理は未確認である。

以下のパスはクラスタの `$HOME/workspace/mcmc4qec` からの相対パスである。
記載hashは識別子を除去する前のprivate原本を指し、この文書のbytesのhashではない。

| 現行証拠 | 実パス・固定値 |
|---|---|
| flow設定 | `20261025-low-parallel-controller-v11/flow-config.json`、SHA-256 `63b8b4d149fdbb56c043fb053e75bfabc73b0b38ea16b88b7dbbd820734d0f4b` |
| flow source | `20261024-c3t2-index-relocation-v1/output/low_parallel_flow_v10/flow.py`、SHA-256 `1cc96b7bb6688f11471d019b443e7f26f84704036cca1e70a255bd8939e51075` |
| F11：flow journal・起動 | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v11`、起動は同階層の `parallel-flow-v11-launch` |
| launch started / process | SHA-256 `23d1cd1d3a26d727d62c93b135c4d9ee5a64b5a03763d6386e799012e59a2473` / `226dfe855a8cf0d4ffad398683db7e0e1a1cb50195d1048f19b7a859d07371e7` |
| native flow受入 | `20261024-c3t2-index-relocation-v1/pipeline-submissions/parallel-flow-native-v11/accepted.json`、SHA-256 `618617ebb91bd1f07fc4a484079790a2656b10fc1c464d72ad3cb4761d408d9f` |
| M2：新merge / request | `20261025-low-parallel-front-v6/merge-parallel-v2` / 同階層の `merge-parallel-request-v3` |
| 新prepared / request / submission | SHA-256 `ccb3fc9dc85fe3c7e9f20a20e15b531615519abf64e7ee9c45ca9414ddb9c03c` / `37e850bb62162f1180336fea056edf8216c4c1605f453d3891a80353f0642c50` / `ffd43e6cf69e56321abe45935dfa7e0408bc68452345bb2fe83f133481b236d8` |
| 移設後outer設定 | `20261025-finite-tail-merge-relocation-v1/config.json`、SHA-256 `970850291825f1af351b81a29f652e7c5deba027edeb6dfea32674cf483d90e8` |
| 移設後effective設定 | `20261025-finite-tail-merge-relocation-v1/effective-config.json`、SHA-256 `902befd0dd048fa6fa2bd81c78e5f7158e8bb0aa617732dc1a4e89d9d898f23b` |
| 継承するhandoff・tail journal | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v9/tail-handoff/completed.json` / 同階層の `parallel-tail-v9` |
| 継承する有限action・報告job | `20261025-finite-tail-actions-v9` / `20261023-low-partition-report-job-v1/runs/report-all24-parallel-v9` |
| 継承するmerge終端受理先 | `20261025-low-merge-terminal-acceptance-v1` |

sourceのv10、実controllerのv11、未使用出力先から継承したtailのv9を区別し、directory名だけで旧処理を再開しない。
tail outerはeffective config・loader・merge root・source mapの4項目だけを変更し、元source map・runner・科学条件・親環境・報告環境・資源を保持した。
旧 `merge-parallel-v1` は失敗原本であり、今後の受理対象はM2の実job265660と新preparedへ結合する。
handoffの所在は旧v9名のままでも、新v11の `flow_config`・migration pinと同じcomparison・selectionへ結合して確認する。

到達済みはF11の12terminal採用とM2の実投入・R観測までであり、今後は次の順で未完の証拠を照合する。

1. M2の正常終端と深い受理、別acceptance PBSの実終端・completion、正式selection24行を確認する。
   12×352×192の811,008基礎行を含む原本入力とselectionを別々に扱い、12terminalのF/0だけで入力closureや科学的受理の完成とはしない。
2. F11の `comparison-completed.json` と、継承先 `parallel-flow-v9/tail-handoff/completed.json` の新flow/migration・実merge・acceptance・selection pinを照合する。
3. `parallel-tail-v9` の6段階journalと `20261025-finite-tail-actions-v9` の実PBS action、独立計時48行・各192分母、非選択・対象なし・未実行理由を照合する。
4. `report-execution/completed.json` と回収済みreport2ファイル、`finite-final-report.json` の実PBS completion、F11の `final-report/stdout.log`・`completed.json` を結合し、本書の全要件との対応を確認する。

小さい起動証拠とobserverはlocal `output/low_parallel_flow_v10/`、tail移設の小原本は `output/finite_tail_merge_relocation_evidence_v1/` に保存されている。
これらはignored outputでのローカル保持であり、利用者が公開取得できる再現資料へ自動的に含まれるわけではない。
保存済みv9 snapshotはその当時の有限scopeで、新しいv11制御source・alias修正・移設設定・本番265660の証拠を収録済みとは扱わない。
新snapshotの採取は準備中・未完了であり、最終科学proofの取得・保存・日本語報告と状態文書への反映も未完了である。
既存の科学結果・適用限界・分母・完了要件は変更せず、全体ETAは未定とする。
