# mcmc4qec：2026-10-22の継続状態

翌日の確認では低ノイズ検証作業が10/12条件まで進んだ。
最新状況は [2026-10-23の状態](PROJECT_STATUS_2026-10-23_ja.md) を参照する。

## 23:16 JST：分割集約からseed censusへの接続を検証

[分割結果の再検証とseed census準備](low_timing_partition_census_bridge_result_2026-10-22_ja.md)を実装した。
Windowsで実行証跡13 test・準備接続9 test・科学計算との接続1 test、Linuxで実行証跡と準備接続の22 testが成功した。
全12条件・24行の実際の選択規則とseed割当数を維持し、単一selectorの証跡を作り替えず分割経路を明記する。
本番待受への組込み、通常経路との投入前照合、censusと独立計時の実行、最終報告への接続は残っている。

実PBSではcollector265457がR・経過1時間41分、sampling265448がR・経過6時間49分で、合計2要求nodeだった。
全12条件準備待受PID46024とC3T0 cohort index PID16928は実commandで生存を確認した。
inventoryは9/12条件で、新たな本番準備や追加qsubは行っていない。

## 23:06〜23:07 JST：全12条件の分割準備待受を起動

[分割準備と転送](low_timing_partition_front_result_2026-10-22_ja.md)を実装し、前段の11 testがWindows・Linuxの両方で、転送境界の8 testがWindowsで成功した。
全12条件が揃うまで待つPID46024の実commandと生存を確認し、inventoryは9/12条件だった。
この待受は準備だけを行い、qsubやflow起動は行わない。
本番flow起動前の通常経路との照合、後続census・独立計時への接続は残っている。

実PBSではcollector265457がR・経過1時間31分、sampling265448がR・経過6時間39分で、合計2要求nodeだった。
DGXのC3T1 batch0は終了記録あり・旧PIDなしで、後続batch3のPID1102209が実稼働していることを確認した。
laboのC3T1 batch0はPID7540が実稼働し、終了記録はまだなかった。
C3T0のcohort index PID16928も生存し、CPU消費3483秒・working set約3.9 GBだった。
全体の正式完了数は9/12条件で、数値検証・独立計時・最終報告は未完了である。

## 22:49 JST：分割worker・結合jobの待受を接続

[分割実行の待受](low_timing_partition_flow_result_2026-10-22_ja.md)を実装し、Windows・Linuxの両方で33 testが成功した。
全workerの正常終了後だけ結合へ進み、投入済みjobの観測timeoutや異常終了から重複投入しない。
本番configの生成、既存serial経路との切替、後続census・独立計時への接続は残っており、本flowは本番起動していない。

実metadata inventoryを読み直し、正式完了は9/12条件、残りはtile288 depolarizingの3条件であることを確認した。
実PBSでは265457がR・経過1時間15分、265448がR・経過6時間21分で、合計2要求nodeだった。
今回の開発・Linux人工データ試験で追加の数値計算jobは投入していない。

## 22:39 JST：結合jobの準備・qsub接続とLinux試験

[結合jobの準備・投入処理](low_timing_merge_submission_result_2026-10-22_ja.md)を実装し、Windowsの28 testと、実クラスタLinuxの48 testが成功した。
両者は重複する小さな人工データ試験を含み、本番traceや実qsubによる結合jobの実行ではない。
共有lockと最大2要求nodeを維持し、投入応答が不明な場合はintentとlockを保持して重複投入を拒否する。
本番requestの組立・分割処理全体の待受・後続censusへの接続は残っている。

直近の実PBS照会ではcollector265457がR・経過1時間04分、sampling265448がR・経過6時間11分だった。
要求nodeの合計は2で、新しい数値計算jobはこの追加開発では投入していない。
低ノイズの正式完了数は9/12条件のままである。

## 22:25 JST：分割結合jobの実行・正常終了受理を検証

[結合job runner](low_timing_merge_execution_result_2026-10-22_ja.md)を実装し、22 testが成功した。
未終了・異常終了・実行証跡不一致を拒否し、正常終了後にだけ既存計時planへ渡す選択結果を作る。
PBS・native環境とraw入力は人工fixtureで、本番request作成・qsub接続・全12条件の実行・後続census接続は未実施である。
結合jobの24時間枠は実行予算であり、終了時間の予測ではない。

22:21の実PBS照会では265457・265448がともにRで、合計2要求nodeだった。
22:25にはC3T1 collector監視、C3T2 generator、新native・PC launcherの実processとcommandを確認した。
C3T0 cohort indexも22:21の実process照会で稼働中だった。
低ノイズの正式完了は9/12条件のままで、全体の数値検証・独立計時・最終報告は未完了である。

## 22:11 JST：C3T2 native・PC解析の開始待受を再接続

旧launcherが子を1件も起動せず停止していたことと、C3T2 native・DGX・laboの実processと子保存先がないことを確認した。
[native・PC開始待受](c3t2_pc_slot_reconnection_2026-10-22_ja.md)を新generatorへ接続し、6 testと実入力照合が成功した。
新launcher PID49448の稼働を確認し、現在はregistry未完成のため子を起動せず待機している。
先行C3T1 PC解析の完了待ち、native reference受理、固定群割当と回収検証を維持する。
C3T0のindex・distribution、C3T1のcollector、C3T2のgenerator・auditにはerror記録はなく、いずれも未完了である。
低ノイズ検証の正式完了は9/12条件のままである。

## 22:07 JST：C3T1/C3T2の最終集約と後処理を再接続

[最終集約の再接続](final_slot_reconnection_2026-10-22_ja.md)で、準備・qsub実行・算術確認と計時候補作成までの監視経路を更新した。
旧記録の未着手状態と固定sourceを確認し、14 testが成功した。
両条件の計6監視processは実commandで稼働を確認し、errorはなく、先行データと監査の完了を待っている。
既存の科学設定・remote集約root・検証関数は保持し、local保存先を別にした。
新たな集約jobはまだ投入していない。
クラスタでは265457が回収処理、265448がsamplingを継続しており、直近の実照会で合計2要求nodeだった。
低ノイズの正式完了数9/12条件、全12条件の集約・独立計時・最終報告が未完了という状態は変わらない。

## 21:58 JST：C3T2の後続投入と回収・監査を再接続

[generator再接続](c3t2_generator_slot_reconnection_2026-10-22_ja.md)と[回収・監査の再接続](c3t2_audit_slot_reconnection_2026-10-22_ja.md)を実装し、保存sourceから10 testと7 testが成功した。
実入力の照合後、generator PID19608とaudit PID45828の起動・実生存を確認した。
generatorは正常終了したanchor265444と実行中のsample0の265448を引き継ぎ、C3T1 full audit受理後に未投入sample1だけを投入する。
auditは新generatorのregistry完成を待っており、既存の回収・capacity監査・full監査の手順を保持する。
新規cluster jobのqsubはこの再接続ではまだ行っておらず、直近の実照会では265457・265448の2jobがRだった。
C3T0のcohort index PID16928も引き続き実稼働している。

現在の2jobが終わっても、C3T1の監査、C3T2の残りsampling・回収・監査、最終集約・独立計時は残る。
条件の最終集約に進む停止済み経路の再接続も未完了である。
低ノイズの正式完了数は9/12条件のままで、公開準備と全数値検証の完了は区別する。

## 21:43〜21:44 JST：実稼働の再確認とnative経路の訂正

低ノイズの正式完了は9/12条件で、C3T0は768/768群を回収済みだがcohort indexと後続集約は未完了である。
cohort indexのPID16928とC3T1 collector監視のPID39268は稼働中である。
クラスタではcollector265457とsampling265448がRで、合計2要求nodeである。
DGXとlaboはC3T1 batch0を実行中であり、実PID1010955・7540の生存と未完了状態を照会した。

21:37の「C3T1 native経路の再接続が必要」という記載は誤りだった。
native job265455は正常完了し、21:11:08にreferenceの受入記録を回収済みである。
nativeとPC計算は再起動せず、停止したC3T2 generatorと監査後の集約経路が再接続対象である。
C3T2 generatorの再接続用guardは7 testが成功したが、新driverの実装・起動は未完了である。

公開候補のZIP・wheel・Release本文・checksumは準備済みで、実GitHubのvisibilityはPRIVATEである。
全12条件の集約、独立計時、最終報告は未完了であり、現時点で全工程の確実な完了時刻は提示できない。

## 21:37 JST：新公開物の検証、C3T0全回収、C3T1 collector再接続

公開tagの[新しいsource ZIP・wheel・Release本文・checksum](publication_artifacts_rebuilt_2026-10-22_ja.md)を別checkoutで作成し、984 Git blob、package 33ファイル、README metadata、licenseの一致を確認した。
installed coreの利用例検証とRelease本文の2 testも成功し、GitHubは引き続きPRIVATEだった。
旧履歴・旧配布物・稼働中の計算用sourceは上書きしていない。

C3T0のDGX batch26〜32の終了と全回収を照合し、DGX 648群・labo 120群の計768/768群、67,584行となった。
追加128群・11,264行は全行に診断flagと未定義項目があり、区間未取得は0で、分母から除外していない。
[全回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v32.json)のSHA256は `db1703e9fdd32c775e72b3bd80a0637f2bdf0e005910f2ff6fce95b931c74b90` である。
cohort indexの実process PID16928は20:58:57から稼働中で、21:37にCPU消費と約1.4 GBのworking setを確認した。
条件全体の集約・最終比較は完了しておらず、低ノイズの正式完了数は9/12条件のままである。

C3T1 sampling265438はF・exit 0、実walltime8時間00分20秒で終了した。
後続collectorは投入直前の2node gateで停止していたため、remoteに台帳・実行記録・出力が存在しないことを確認し、[別controllerで再接続](c3t1_collection_slot_resume_2026-10-22_ja.md)した。
qsubで投入したcollector265457とC3T2 sampling265448はともにRで、最大2要求nodeを維持している。
C3T1 native経路とC3T2 generatorの新auditへの再接続が次の残作業である。

## 19:00 JST：worker証跡と設定選択規則の結合を受入

[結合処理](low_timing_partition_merge_result_2026-10-22_ja.md)は19 testが47.41秒、保存sourceからの再実行も19 passed・48.91秒で成功した。
workerのprepared・qsub応答・PBS終了記録・出力・入力とnative fileのhashを照合し、全24行のreference・rank・選択設定を既存の計時plan検証関数で再構成する。
raw readerとnative環境は人工fixtureで、結合job自身の実行・資源評価・正常終了の受理と後続censusへの接続は未完了である。
候補は正式計時入力として受理されない状態に保持している。
DGX batch25のPID808747は19:00 JSTの照会で稼働中であり、回収数620/768群と低ノイズの正式完了数9/12条件は維持した。

## 18:52 JST：公開側の新履歴とRelease本文を確認

[公開側との整合確認](remote_publication_reconciliation_2026-10-22_ja.md)で、remote mainとtag `v0.1.0.dev5` は `e7e5239`、同commitのCIはsuccess、PRIVATE・Release 0件を確認した。
localとの共通祖先がない履歴更新であり、旧履歴をmerge・pushしない。
`src/` 33ファイルと `pyproject.toml` は同一blobだが、公開文書・証跡等は更新されているため、旧添付候補を最新公開物として再認定しない。
現行tag用Release本文を生成し、相対リンク0件と7本のrepository linkのpath存在を確認した。
稼働中controllerのsource・旧raw証跡・未コミット作業は保持している。

## 18:47 JST：分割workerの単発投入処理を受入

DGX batch24の終了後、回収archive全体・全96 member・固定割当を照合し、C3T0を620/768群・54,560行へ更新した。
追加1,760行は全行に診断flagと未定義項目があり、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v30.json)のSHA256は `fce96914d083fd1cbfd0b87d8efbe39b9cc965d63aebfbce2bfa9d96a1831381` である。
DGX batch25のPID808747の実稼働を確認し、クラスタ265438と265448もRだった。
低ノイズの正式完了数は9/12条件のままである。

[単発qsub投入処理とrunner v2](low_timing_partition_submission_result_2026-10-22_ja.md)の保存sourceからの再実行で、それぞれ35 passed・15.14秒と33 passed・5.14秒を確認した。
共有lock・最大2要求node・qsub応答異常時の予約保持・同一workerの再投入拒否を検証した。
schedulerとnative事前検査はdoubleで、実metadata全12条件による準備・本番投入・結合と後続censusへの接続は未実施である。
実行中のcontrollerと固定入力は変更していない。

## 18:38〜18:40 JST：現状の再確認

低ノイズのmetadataを実読込し、正式完了は9/12条件、残るtile288 depolarizingの3条件はpendingであることを確認した。
qstatの実照会では265438と265448がともにRで、各96 CPU・1要求node、経過時間はそれぞれ5時間45分と2時間10分だった。
DGX batch23の終了を確認し、回収archive全体・全96 memberと固定割当を照合して、C3T0の回収を600/768群（78.125%）へ更新した。
追加1,760行は全行に診断flag・未定義項目があり、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v29.json)のSHA256は `73e2727733fc898483ff2afba52c7fa3829e5e635aea5957ad8c27f949822ce6` である。
DGX batch24のPID801321は実稼働し、localのDGX serial・labo待受・C3T2 generatorも生存している。
GitHubはPRIVATEのままで、remote mainは `e7e5239f977fa6162e58570726100e3fcd717afa`、同commitのtests run39742521637はsuccessだった。
local HEADは `886b44b9fdc56d5b86491302dfb651285bbc4113` でremote mainと異なり、直近の運用文書には未コミット分がある。
この確認ではpull・commit・push・公開操作・新規job投入は行っていない。
全12条件の後処理・独立計時・最終報告は引き続き未完了である。

## 科学的な結果の参照先

下表は完了済みの検証記録への案内であり、新たな数値計算や精度認定を追加するものではない。
現在の「9/12」は低ノイズ条件の検証作業の完了数で、主4条件は別に数える。

| 対象 | 結果と再現資料 | 適用限界 |
| --- | --- | --- |
| 主4条件 | [符号・decoder・混合・BAR校正の中間報告](tile_validation_report_2026-10-18_ja.md) | 全対象で名目95%被覆や良好な混合を確認したという意味ではない。 |
| tile72低ノイズ6条件 | [長い設定の比較と再現資料](low_long_six_comparison_result_2026-10-20_ja.md)、[C0T2の独立算術確認](low_c0t2_arithmetic_review_result_2026-10-20_ja.md) | 有限reference区間との重なりを真値の被覆と同一視しない。 |
| tile288 bit-flip、p=0.01 | [C1T0の結果・保存データ・再現手順](low_c1t0_recovered_result_2026-10-21_ja.md) | 長い16設定でも診断警告が残り、校正済み推奨設定や速度優位を主張しない。 |
| tile288 bit-flip、p=0.003 | [C1T1の結果・保存データ・再現手順](low_c1t1_recovered_result_2026-10-22_ja.md) | 長い16設定の全seedに診断警告があり、reference区間も広い。 |
| tile288 bit-flip、p=0.001 | [C1T2の結果・保存データ・再現手順](low_c1t2_result_2026-10-22_ja.md) | 長い16設定で全seedに診断警告・未定義項目があり、精度gateも未達である。 |
| 残る低ノイズ3条件・低ノイズの独立計時・最終報告 | 未完了。以下の実行履歴を参照する。 | 公開準備の完了とは区別する。 |

完了9条件の長い144設定は[統合比較](low_long_nine_comparison_result_2026-10-22_ja.md)にまとめた。
保存reviewの比較であり、旧8条件128設定との全数値一致、20テスト、保存sourceからの再実行でCSVのbyte一致を確認した。
tile288の広いreferenceとの交差192/192を精度達成と扱わず、全体包含・診断flag・診断未定義を併記する。

全12条件の計時前処理が既存資源枠を超えた場合に備え、[分割方針案](low_timing_partition_contingency_2026-10-22_ja.md)を整理した。
条件ごとの選択規則を維持する一方、全24出力・入力不変性・実PBS証跡を結合する新しい契約が必要である。
分割資源計画器、入力準備処理、worker runner、結合の値処理中核、PBS証跡検証関数は下記の受入まで進んだが、実metadata全12件による準備・実PBS実行・後続計時との接続・投入は未実施である。
全12条件の資源上限超過を確認したものではなく、実行中のcontrollerと固定入力は変更していない。

## 18時台：分割worker入力準備処理の受入

[入力準備処理](low_timing_partition_preparation_result_2026-10-22_ja.md)の16 testが3.29秒、保存sourceからの再実行が4.76秒で成功した。
全12条件を保ったworker割当、manifest・prepared・scriptのhash関係、事前検査失敗時の非作成、保存中の変更検出を確認した。
native側の事前検査はdoubleであり、実metadata全12件による準備の完了ではない。
既存inventoryを実読込し、metadataは9/12条件、C3T0・C3T1・C3T2はpendingであることを再確認した。
部分集合での本番入力作成は行っていない。

## 18:17 JST：DGX batch22を回収、580/768群

DGX batch22のPID739041の終了と固定configのcompletionを確認し、archive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `e2de9e5e228c62f1e54033560167415d6648f9d1d0ea6b057fb40068347ab6b3` である。
C3T0の回収はDGX 460群とlabo 120群の計580/768群・51,040行となった。
追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v28.json)のSHA256は `82247a64b4a299f78dfb625773b636ac135ce783d5fe4b7e1a9fde7b6c06eb0e` である。
batch23のPID747301が実稼働していることも確認した。
条件全体の科学的受入ではなく、正式完了数は9/12条件のままである。

## 18:04 JST：分割worker runnerの受入とクラスタbootstrap確認

[実行runner](low_timing_partition_runner_result_2026-10-22_ja.md)の28 testが3.60秒、保存sourceからの再実行が4.68秒で成功した。
クラスタの固定parent環境v4でもimport・source closure・native binding・runtimeの整合性確認が3.240秒で成功した。
実PBS内のworker実行や新しいnative probe、trace再読込、qsub投入は行っていない。
全12条件の分割入力作成・共有lock下の投入・結合ジョブ・後続censusとの接続は未完了である。
実照会でクラスタ265438と265448はともにR、DGX batch22のPID739041も実稼働している。

## 17:53 JST：DGX batch21を回収、560/768群

DGX batch21のPID731799の終了と固定configのcompletionを確認し、archive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `936775d499f2b913b77bfd2001ffe2eb23442f6a7a42598df8aa92b0e4e957b6` である。
C3T0の回収は560/768群・49,280行となり、追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v27.json)のSHA256は `11c238bba95ef34dc411334d3bc45aef4005c667e347f66568a4aa9f77440b55` である。
batch22のPID739041が実稼働していることも確認した。
条件全体の科学的受入ではなく、正式完了数は9/12条件のままである。

## 17:44 JST：分割workerのPBS証跡検証関数を受入

[保存証跡の検証関数](low_timing_partition_execution_evidence_result_2026-10-22_ja.md)を追加し、人工証跡の30 testが4.02秒、保存sourceの再実行が4.98秒で成功した。
全体manifest・資源計画・qsub台帳・script・PBS状態・host・値hashを結合し、検証終了時の入力不変性も確認する。
実schedulerへの照会や本番runnerへの接続を行ったものではなく、投入lock・native環境の事前検査・結合ジョブ・後続censusとの接続は未完了である。
クラスタ265438と265448は実照会でともにR、DGX batch21のPID731799も実稼働している。

## 17:35 JST：DGX batch20を回収、540/768群

DGX batch20のPID724100の終了と固定configのcompletionを確認し、archive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `9230d9532a958197a602120d2bd5fdccbf5de465e9f7069a742deff68da0059a` である。
C3T0の回収は540/768群・47,520行となり、追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v26.json)のSHA256は `34e8aa90736033110e215ec40dd00b29e9812bed21a78fa2e37fcdf3c2a883d0` である。
batch21のPID731799が実稼働していることも確認した。
条件全体の科学的受入ではなく、正式完了数は9/12条件のままである。

## 17:32 JST：分割reader・結合中核の受入

[条件単位のreader呼出しと結合処理](low_timing_partition_values_result_2026-10-22_ja.md)の33 testが16.35秒、保存sourceからの再実行が17.31秒で成功した。
実 `choose` 関数と人工metadataを使い、単一経路と分割・結合経路で全24行と12件のbindingの全値一致を確認した。
raw readerとsource closure探索はテスト用doubleであり、実traceの再検証や実PBS実行の認定ではない。
中間結果は正式selector結果と区別し、実PBS証跡・native環境・後続censusとの接続と投入は未実施である。
低ノイズの正式完了数は9/12条件のままである。

## 17:18 JST：DGX batch19を回収、520/768群

DGX batch19のPID668677の終了と固定configのcompletionを確認し、archive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `1e23950f0590634a5d517b14b65ee1e3f7cfc7a93163e3cccd153414fe07f450` である。
C3T0の回収は520/768群・45,760行となり、追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v25.json)のSHA256は `b96babe6f559435a7043a3a987b08fb64083864f33cb7f6de1fa0744ddc4fa9e` である。
batch20のPID724100が実稼働していることも確認した。
条件全体の科学的受入ではなく、正式完了数は9/12条件のままである。

## 17時台：分割資源計画器の受入

[分割資源計画器](low_timing_partition_plan_result_2026-10-22_ja.md)を小仕様・受入テスト・実装の順で追加し、27 testが0.82秒、保存sourceからの再実行が2.81秒で成功した。
単一ジョブで収まる場合の既存資源判定との全項目一致と、上限超過時の全12条件の欠落・重複のない割当を確認した。
実metadata全12件による本番計画作成、worker・結合・後続readerとの接続、qsub投入は未実施である。
これは後段の資源枠に備える実装であり、科学的な完了数9/12や推定精度を更新するものではない。

## 17:00 JST：DGX batch18を回収、500/768群

DGX batch18のPID657582の終了と固定configのcompletionを確認し、回収後にarchive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `d9be7f530e34ade4e4f1f6d9b70bd3a75c5189331d953dd28fb38bdf04d7b441` である。
C3T0の回収は500/768群・44,000行となり、追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v24.json)のSHA256は `f19e25feb404ffe7659a577124f058f4f9b4b7d64ce08f55768d46168a7da665` である。
元serialはbatch19のlaunchへ進んだ。
条件全体の科学的受入ではなく、正式完了数は9/12条件のままである。

## 16:43 JST：480/768群を回収、先行入力の本番再利用を確認

DGX batch17のPID646790の終了と固定configのcompletionを確認し、回収後にarchive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `2509cc961dd92cb07046acdf3d814e497fcca88112d34a7b026b0110d625b1ab` である。
C3T0の回収は480/768群・42,240行となり、追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v23.json)のSHA256は `030a7320a122a7e831b9086f8317e517f2018dcdc344aa0f7b0a64122d30e0a4` である。

batch18では元serialのexport-reused記録を確認し、先行準備の独立検証記録・prepared_input・archive全体・source pinとの一致、および実数値processの稼働を照合した。
このbatchのexport再実行を示すintent・log・completionが存在せず、既存の再利用経路から計算が開始した。
[本番再利用観察](data_tile_validation_2026-10-17/c3t0_prefetch_first_actual_reuse_20261022_v1.json)のSHA256は `2e30d1da121310313432ee7c1e3ef51e772ad6938a7e97b16652e2773f30dd89` で、照合sourceも同名の `.py` として保存した。
今回の観察ではarchive全体を再hashしたが、全memberの個別再hashは先行準備時の検証記録を引き継ぐ。
本番再利用は確認できたが、条件全体の時間短縮量や科学的な精度向上を測定したわけではない。
正式完了数は9/12条件のままである。

## 16:27 JST：C3T2 anchor終了、sampling第1分割を開始

C3T2 anchor job265444は16:25:50 JSTにF・exit 0・run_count 1で終了し、実walltimeは2分38秒だった。
既存generatorが後続sample0をqsubで投入し、job265448は16:26:39 JSTに開始した。
単発投入receiptと固定intent、qsub command、remote script hash、実PBSのSubmit_arguments、要求96CPU・32GB・1node・22時間30分枠を照合した。
C3T1 sampling265438とC3T2 sampling265448がともにRで、要求node合計は2である。
[終端と次投入の観察](data_tile_validation_2026-10-17/c3t2_anchor_terminal_sample0_observation_20261022_v1.json)のSHA256は `fb09f58108f085ae73bc602855de5a75984d3b0c945a28264680027a12d6ce99` である。
今回の観察はPBS終端と次工程の実行確認で、anchor結果の再計算・trace監査・条件全体の科学的受入ではない。
正式完了数は9/12条件のままである。

## 16:25 JST：C3T2 anchorが実行開始

qsub投入済みのC3T2 anchor job265444は16:23:11 JSTに開始し、16:25の実照会でR・run_count 1を確認した。
実PBSのSubmit_arguments、remote script SHA256、固定投入receipt、要求96CPU・32GB・1node・3時間枠を照合した。
C3T1 sampling265438もRで、両jobの要求node合計は2である。
[開始観察](data_tile_validation_2026-10-17/c3t2_anchor_running_observation_20261022_v1.json)のSHA256は `491cf416d7642e4505c69172024855d214f19dd58036dde698ab465737bf1002` である。
これは実行開始の確認であり、anchor結果や条件全体の科学的受入ではない。
正式完了数は9/12条件のままである。

## 16:20 JST：DGX batch16を回収、460/768群

DGX batch16のPID576419の終了と固定configのcompletionを確認し、回収後にarchive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `7feef2319426dd082f16cbf96dab8ca50315e4e37738d7b0760c5abcbdf6f246` である。
C3T0の回収は460/768群・40,480行となり、追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v22.json)のSHA256は `4700f8db06f97688b8ec5e80d4c7be5700ac9a37450ddb2fbd2399c920415bea` である。
元serialはbatch17のexportへ進んだ。
PBSの実照会では265438がR、265444がQで、要求node合計は2だった。
条件全体の科学的受入ではなく、正式完了数は9/12条件のままである。

## 16:04 JST：PC利用状況と既存実行時間の確認

DGX batch16のPID576419が実稼働し、labo向けC3T1待受PID13536も既定commandで稼働している。
C3T0の既存launchからcompletionまでの記録では、labo batch2〜4は各24群で5,315.7〜5,322.7秒、DGX batch13〜15は各20群で910.6〜938.4秒だった。
終了pollなどの制御時間を含み、群の入力・並列worker数・負荷を揃えた速度benchmarkではない。
[既存時間の比較](data_tile_validation_2026-10-17/c3t0_existing_pc_elapsed_comparison_20261022_v1.json)に6件の時刻・完了artifactのhashを保存し、新たな速度測定は行っていない。
観察SHA256は `b0fa02467e267b0471397d0023ea01fea2ea10ec51da109d2f8ec9c00503d663` である。
現serialは全担当batchを固定順に処理し、helperと入力のhashを各工程で確認するため、稼働中sourceや担当hostを直接変更しない。
laboは次のC3T1入力とnative referenceの受理を待つ既存経路を維持し、再割当ては行っていない。

## 15:58 JST：DGX batch15を回収、440/768群

DGX batch15のPID566696の終了と固定configのcompletionを確認し、既存collectorによる回収後にarchive全体・全96 member・source/input hash・固定割当を照合した。
completion SHA256は `179f031c0893bbc52ce43376def18963e19fbc3734541b67f303207188d0e44f` である。
C3T0の回収は440/768群・38,720行となり、追加1,760行は全行に診断flagと未定義項目があるが、区間未取得は0で、全行を分母に保持した。
[回収観察](data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v21.json)のSHA256は `b9d753810185a219bc2b427857d1f3a0e3c72bf56ee71c3984f44a6e7402601c` である。
元serialはbatch16のexportへ進んだ。
条件全体の科学的受入ではなく、正式完了数は9/12条件のままである。

## 15:50 JST：計時前処理の資源余裕を再計算

受理済みmetadata候補9件を読み、既存算定式で既知部分だけでも最低22時間25分の要求時間になることを確認した。
24時間枠に収めるには、残る3条件の最終解析時間合計が約52分46秒以下であることが必要である。
これは既存の時間算定式から得た条件であり、未完了3条件の所要時間予測や全12条件の正式な資源判定ではない。
[分割方針案](low_timing_partition_contingency_2026-10-22_ja.md)に算定値と入力hashを追記した。
現在の実行経路を変更せず、全12条件のmetadata・設定選択規則・24出力を維持する。

DGX向け先行準備queueはbatch29〜18の12本をprepare・verifyして正常終了した。
先行距離の条件で次batch17の準備を止め、元serialは稼働を継続している。
実PIDと検証記録の照合は[先行準備の結果](c3t0_prefetch_queue_result_2026-10-22_ja.md)に追記した。
本番での再利用・時間短縮は未観察であり、数値検証の完了数は変わらない。

## 15:49 JST：9条件の比較と再現を確認

長い144設定・方法別36行を保存し、旧8条件128設定の由来欄を含む一致を確認した。
保存sourceで20テストが成功し、別directoryへの再実行で2種のCSVがbyte単位で一致した。
[結果・再現手順](low_long_nine_comparison_result_2026-10-22_ja.md)に診断flag、未定義、区間未取得、有限reference全体の包含と交差を併記した。
新しいsamplingやBAR再計算ではなく、完了数は9/12のままである。
同時刻の実照会で、DGX batch15のPID566696が稼働し、クラスタ265438はR、265444はQで、要求node合計は2だった。
全12条件の独立計時と最終報告は未完了である。

## 15:40 JST：C1T2の回収・独立再集計を完了、低ノイズ9/12条件

C1T2の回収は15:37 JST、独立再集計は15:38 JSTに正常終了した。
全768群・67,584行・352設定・各192 seedを保持し、元reportの11,968値との最大絶対差は5.551115123125783e-17、再集計の所要時間は57.771秒だった。
回収artifactと再集計出力の計29ファイル、および長い16設定CSVとreviewの全セル一致を追加照合した。
[結果と再現資料](low_c1t2_result_2026-10-22_ja.md)を保存し、低ノイズ条件の検証作業を9/12条件完了とする。
長い16設定の全192 seedに診断flagと未定義項目があり、referenceの幅も広いため、完了を精度・混合・名目95%被覆の認定とは扱わない。
全16設定で20%・10%の経験的精度gateは未達であり、公開既定を変更しない。
全12条件の計時入力候補も9件となったが、残る3条件が未完了のため親入力は未作成である。
全体の完了時刻は未確定である。

## 15:35 JST：DGX batch14の回収、420/768群

DGX batch14の実PID555529の終了と、固定configに対応するcompletionを確認した。
completion SHA256は `e0cfb8b3a59edb9bbaca739d04070a10f917d14e29577da4d1cce5cf15a587dc` である。
既存collectorの回収後、archive全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は420/768群・36,960行となり、追加1,760行は全行に診断警告と未定義項目があるが、区間未取得は0で全行を分母に保持する。
観察は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v20.json`、SHA256は `b3d69e65dc6cb8d427f768919643fa88a1bbc55df829f4ab09fd61481ed7d4aa` である。
既存serialは次batch15のexportへ進んだ。

C1T2のcomplete検査は15:29 JSTに正常終了し、reportとterminalのhashを受理した。
report SHA256は `f620a244ce380d0530f26d8bf4c880daec8fdaba4c3bf0484029f6309661e3d6`、terminalは `fc0671cdc90f388d5d69b3821194d180416ef64058b7f589972e038144007c62` である。
結果artifactは転送され、collector13652が転送前後の入力不変性を検査している。
独立算術確認の待受33972も実稼働しており、正式完了は8/12条件のままとする。

## 15:28 JST：C1T2最終解析の正常終了とC3T2 anchor投入

C1T2（tile288 bit-flip、p=0.001）の最終解析265435は15:24:48 JSTにF・exit 0・run_count 1で終了した。
実walltimeは2時間44分04秒で、保存configとscriptのhashが実PBSの投入先に対応することを確認した。
既存driver39644は終了後のcomplete検査を継続しており、回収・独立再集計の完了はまだ確認していない。
したがって低ノイズの正式完了は8/12条件のままである。

空いた枠で既存C3T2先行生成driverがanchor0をqsubで投入し、job265444を受領した。
選択はcase3・target2・anchors0、要求資源は1node・96CPU・32GB・上限3時間である。
固定preflight、単発投入台帳、qsub command、実PBSのSubmit_arguments、remote script hashが一致することを確認した。
観察時点の実PBS状態はQであり、数値計算の開始はまだ確認していない。
C3T1 sampling265438はRで、Qを含む所有jobの要求node合計は2である。
[実観察](data_tile_validation_2026-10-17/c1t2_terminal_c3t2_anchor_observation_20261022_v1.json)のSHA256は `443ed388f3c3d48065851b791bc6374d8063746796d981d6d6f8622cc9e0d152` で、読取・照合用sourceも同名の `.py` として保存した。
この観察はジョブ終端と次の投入の確認であり、条件全体の科学的受入ではない。

## 15:12 JST：DGX batch13の回収、400/768群

DGX batch13の実PID497289の終了と、固定configに対応するcompletionを確認した。
completion SHA256は `d861ba3786074d68f5b13abdc06d1d6a806c5b23ffe3dcfd7983df765267b0e9` である。
既存collectorの回収後、archive全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は400/768群・35,200行となり、追加1,760行は全行に診断警告と未定義項目があるが、区間未取得は0で全行を分母に保持する。
観察は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v19.json`、SHA256は `3e483fa8052c52da83876f88eb516922dc2917b8f0cbf07473f96db2a93f61de` である。
serial49444と次batch14のexport helper40976の実稼働を確認した。
先行入力準備はbatch25までの照合記録があり、controller6992とbatch24のwrapper22340が稼働していた。
直近15:11 JSTのPBS照会では最終解析265435とsampling265438がともにR・各1nodeだった。
正式完了8/12条件、独立計時と最終報告の未完了、全体ETA未確定は変わらない。

## 14:50 JST：DGX batch12の回収、380/768群

DGX batch12の実PID486842の終了と、固定configに対応するcompletionを確認した。
completion SHA256は `c1b2dbf9219210c160e8bd78a64f403eb924d1ba26d59e2e39c64eacad58401b` である。
既存collectorの回収後、archive全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は380/768群・33,440行となり、追加1,760行は全行に診断警告と未定義項目があるが、区間未取得は0で全行を分母に保持する。
観察は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v18.json`、SHA256は `292f9b3aec7ac942b799def0dd499af046334758100b15e24afa19177c084c6f` である。
serial49444と次batch13のexport helper21244の実稼働を確認した。

先行準備はbatch28の20群・全4,977 memberの照合まで完了し、controller6992は数値解析の再開を待っている。
元serialのexport中に次の先行準備を起動しない状態と、実controller・serial・export helperを確認した。
観察は `data_tile_validation_2026-10-17/c3t0_prefetch_queue_wait_observation_20261022_v1.json` に保存した。
正式完了8/12条件、独立計時と最終報告の未完了、全体ETA未確定は変わらない。

## 14:45 JST：先行入力準備の最初の自動移行を確認

batch29のprepareとverifyの正常終了、全4,977 memberの照合記録とsource hash、両工程の終了後に次batch28が開始した時刻順を確認した。
controller6992が継続し、batch28のwrapper21772とhelper34064の実commandと親子関係を確認した。
[移行観察](data_tile_validation_2026-10-17/c3t0_prefetch_queue_first_transition_20261022_v1.json)と[実行結果](c3t0_prefetch_queue_result_2026-10-22_ja.md)に記録した。
入力準備の自動移行は確認できたが、本番serialでの実再利用や時間短縮量は未確認である。
数値検証の完了数と解析結果の回収数は増えていない。

## 14:40 JST：先行入力準備を逐次実行する待受を起動

batch30の入力準備が正常終了し、全20群・4,977 memberの独立照合を完了した。
DGX batch12の実PID486842の稼働を確認し、受入済み単発helperとverifierを順番に呼ぶ別controllerを起動した。
20テストと保存sourceからの再実行が成功し、controller6992、最初のbatch29 wrapper25440、helper22252の実commandを確認した。
詳細と固定hashは[逐次待受の起動結果](c3t0_prefetch_queue_result_2026-10-22_ja.md)に記録した。
元serial・科学的設定・担当割当は維持し、入力準備は一度に一つだけ進める。
新controllerによる最初の準備完了から次batchへの実移行、本番serialによる実再利用、時間短縮量は未確認である。
正式完了8/12条件、C3T0回収360/768群、全体ETA未確定は変わらない。

## 14:28 JST：現状確認とDGX batch11の回収

GitHubの実照会でリポジトリはprivate、mainのCI 39325976119はcompleted・successだった。
公開候補の準備と数値検証の完了を区別し、低ノイズの正式完了は8/12条件のままである。
PBSの実照会で265435（C1T2最終解析）と265438（C3T1 sampling）はともにR・run_count 1・各1nodeで、合計2nodeだった。
DGX batch11は実PID430743の終了と固定configに対応するcompletionを確認し、既存collectorの回収後にarchiveと全96 member、割当、入力のhashを独立照合した。
C3T0の回収済みは360/768群・31,680行となり、追加1,760行は診断警告と未定義項目を含むが全行を分母に保持する。
観察は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v17.json`、SHA256は `60441856aedbc85cd41bb93fa38c04144716131d4e28683896ee8af8c2fdfbbf` である。
serial49444の実稼働と次batch12のexport開始を確認し、この時点ではbatch12の数値解析開始を確認していない。
laboの次条件waiter13536とC3T2先行生成driver42324の実稼働も確認した。
先行準備batch31はwrapper41712・helper21232の終了と正常completionを確認し、20群・全4,977 memberの追加照合を完了した。
その照合記録は `data_tile_validation_2026-10-17/c3t0_dgx_export_prefetch_v1/batch31/independent-verification.json`、SHA256は `51d4aedf9d9a8149e3d4a7ea4850827ff978a6eeca3570e98b14ee727523de29` である。
先行入力の本番serialでの実再利用と時間短縮量は引き続き未確認である。
低ノイズの残る4条件、全12条件の独立計時、最終報告は未完了で、全体の終了時刻は確定していない。

## 14:21 JST：DGX解析と並行した入力準備

既存serialが完成済みexportを再利用する経路を使い、未着手の末尾batch32の入力準備を先行した。
15テスト後に元helperで8群分を準備し、正常終了と全2,061 memberの追加照合を確認した。
元serial、割当、seed、科学的設定、実行中の数値workerは変更していない。
続いてbatch31の先行準備を開始し、local実PID41712とhelper21232を確認した。
DGX batch11の実PID430743は解析を継続している。
本番serialによる入力の実再利用と全体の時間短縮量は未確認で、詳細は[先行準備の結果](c3t0_dgx_export_prefetch_result_2026-10-22_ja.md)に記録した。
正式完了8/12条件とC3T0回収340/768群は変わらない。

## 14:10 JST：labo担当分の回収完了、C3T0回収340/768群

labo batch4の実PID21040の終了と固定configに対応するcompletionを確認した。
completion SHA256は `90486da3b3112adb348cd27fa3279343bab50ecf829de823288446059af189ea` である。
既存collectorによる回収後、archive全体・全112 member・固定割当・source/input hashを独立照合し、C3T0の回収は340/768群・29,920行となった。
追加2,112行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v16.json`、SHA256は `d78cb52a2b21eb126f591a8348888627db22073f9144da69f5f1e0c773f6b274` である。

laboの全5batch・120群の回収完了記録、既存照合台帳、各receiptとtransferのhash、およびserial47168の実process終了を確認した。
次条件C3T1のwaiter13536は稼働しており、前条件完了を受理してnative referenceの完了を待っている。
laboは現在、数値解析を実行中ではなく次条件の前段待ちである。
この確認は `data_tile_validation_2026-10-17/c3t0_labo_serial_completion_observation_20261022_v1.json`、SHA256は `c24cfeea3dea3886857693e294c580ce9fe7f9648fdc103daa6ede2f5e8e4312` に保存した。

DGXはbatch11の入力準備・転送・stageを完了し、実PID430743・config `54bc36794b7e0f10d3f7ae5d183d195a830522a51fba859dc539f6c25ede76f3` で解析が稼働中である。
正式完了8/12条件は変わらず、labo担当分の終了をC3T0全体の完了と扱わない。

## 14:05 JST：DGX batch10を照合、C3T0回収316/768群

DGX batch10の実PID420153の終了と、固定config `702193f19b5da3cd44c4d7a85b5db80ccdbfca81a77b75f7e02e40fa4352fff1` に対応するcompletionを確認した。
completion SHA256は `cdc7215e6cead6475e124e63269658e8fe2df4424e7af9d0b16f388ef727cd48` である。
既存collectorの回収後、archive全体・全96 member・固定割当・source/input hashを独立照合した。
回収済みは316/768群・27,808行となり、追加1,760行は全行に診断警告と未定義項目があり、区間未取得は0だった。
全行を分母に保持し、今回の回収を科学的精度の認定とは扱わない。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v15.json`、SHA256は `82cce8d227fd2f2fa228ed51003ef30294694d5f023650287515b5c490a3893b` である。
既存serial49444と、次batch11の入力exportを行う子PID15276の実稼働を確認した。
labo batch4は直近14:02の実照会でPID21040が稼働中だった。
クラスタ265435と265438は14:05のPBS照会でR・run_count 1・各1nodeであり、C3T2は空き枠待ちを継続する。
正式完了は低ノイズ8/12条件のままである。

## 13:47 JST：C3T2先行生成へ切替、C3T0回収296/768群

C3T2のanchorとsampling前半を空き枠で先行するgeneratorへ切り替え、監査・native/PC launcher・最終解析準備・実行・独立集計の接続も完了した。
関連113テストと、Windowsの既知console補助processに限定した切替検査7テストが成功した。
旧6waiterの未着手を確認して停止し、新6controllerの実PID・command・intent・全固定hashを確認した。
稼働中のクラスタjobとPC解析は維持し、元payload・task・seed・科学的設定・qsub・共有lock内の最大2node検査を変更していない。
C1T2最終解析265435とC3T1 sampling265438は各1nodeで稼働中で、C3T2は空き枠待ちであり、C3T2のqsubは未実施である。
詳細・保存source・テストlog・実process観測は[C3T2先行生成の接続結果](c3t2_parallel_generation_result_2026-10-22_ja.md)にまとめた。

DGX C3T0 batch9の回収後にarchive全体・全96 member・固定割当・source/input hashを独立照合し、回収済みは296/768群・26,048行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持する。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v14.json`、SHA256は `b506a6c7cbed5b1d4af8317e06b0186b5fd07ff1ffac18a9557a917a1e433a0d` である。
DGXの次batch10は実PID420153・config `702193f19b5da3cd44c4d7a85b5db80ccdbfca81a77b75f7e02e40fa4352fff1` で稼働中、labo batch4も実PID21040で稼働中だった。
正式完了8/12条件と全体ETA未確定は変わらず、今回の接続と回収を科学的精度の認定とは扱わない。

## 13:38 JST：現状の実照会

正式完了は低ノイズ8/12条件で、主4条件は別枠で完了している。
C1T2最終解析265435とC3T1 sample1の265438はPBS実状態R・run_count 1で、各1node・合計2nodeだった。
実walltimeはそれぞれ56分24秒・44分23秒である。
DGX C3T0 batch9は実PID411399の終了と固定configに対応するcompletionを確認した。
completion SHA256は `8bf4efca1a1bdbeb528e2c0905dee67912e6915b5a440afae7408335472a9939` であり、local collection receiptはまだ存在せず、独立照合済みの回収数は276/768群のままとする。
labo C3T0 batch4の実PID21040は稼働中で、completionは未作成だった。
C3T2先行生成driverと切替検査の保存テスト結果は16 passedであるが、後続接続・旧waiterからの切替・C3T2のqsub投入は未実施である。
旧C3T2の6waiterが稼働中で、切替完了記録がないことを確認した。
GitHub実照会でリポジトリはprivate、main CI 39325976119と公開候補CI 39267489093はsuccessだった。
全体の完了時刻は引き続き未確定であり、工程別の仮定付き見通しは13:14 JSTの記録を参照する。

## 13:22 JST：後続batch9のexport正常終了とDGX解析開始

復旧serialはbatch9のexport・preposition・stageを完了し、DGX上の実PID411399と固定config `344271becbb8919833397b29e688d86503aef43e70ce530254893522a4799244` の一致を確認した。
export開始からprepared_inputまで297.71秒で、元の全member・metadata・assignment検証を維持した正常終了だった。
このbatchは旧300秒上限を超えた実行ではなく、上限超過時の待機継続を実測で証明したものではない。
観測は `data_tile_validation_2026-10-17/c3t0_dgx_future_export_success_20261022_v1.json`、SHA256は `43f1bd48ce9556095b78e8a0d3d4d81ee8805927d816b6268e914bff7ea8f05e` である。
科学的な設定変更や再投入をせず次batchへ継続できたことの確認であり、正式完了8/12条件と回収276/768群は変わらない。

## 13:17 JST：復旧したDGX batch8を照合、276/768群へ進展

DGX batch8の実PID355285の終了と固定configに対応するcompletionを確認した。
既存collectorの回収後にarchive全体・全96 member・固定割当・source/input hashを独立照合し、C3T0の回収は276/768群・24,288行となった。
追加1,760行は全行に診断警告と未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v13.json`、SHA256は `bf1a8baf5f631e553fd2d97e5c4a3a0f5801cce6f5711f4612055450cfe7dfbb` である。
completion SHA256は `435cf9ddeb0ad9c8014e9b0750bef473295c1c071e5ee6b9dcb62a25f16311e6`、archive SHA256は `db5a346346cfd76718a096a80644c34617078f52ee785d3052d3e052d02adfe5` である。
復旧serialはbatch9の入力exportへ進んでいる。
正式完了8/12条件は変わらず、この回収を精度認定や条件全体の完了とは扱わない。

## 13:14 JST：実測に基づく工程別の見通し

正常完了したbatchの周期はDGXが約23分、laboが約98分で、現在のC3T0担当分回収は同じ周期ならそれぞれ10月22日22:40頃・14:15頃となる。
C3T1 sampling前半の実walltimeは7時間59分27秒で、後半も同じなら10月22日20:52頃、事前capacity外挿を使うなら23:27頃となる。
これらは工程別の仮定付き参考値であり、予測区間でも全体の終了時刻でもない。
全12条件の独立計時と最終報告を含む終了時刻は未確定で、計算式と証跡は[残工程の見通し](remaining_work_estimate_2026-10-21_ja.md)に追記した。
正式完了8/12条件は変わらず、現在の処理は再起動していない。

## 13:06 JST：DGX解析と後続controllerを復旧

DGX batch8の完成済み入力を全member照合して回収し、batch0〜7の41操作を再利用して解析を再開した。
実DGX PID355285と固定configの一致を確認し、labo batch4の実PID21040も稼働中だった。
集約・転送・最終解析準備・実行待機・後処理の停止したcontrollerを別のsourceと記録で再接続し、共有入力も再利用した。
C3T1のlauncherも旧DGX停止の影響で終了していたため、稼働中のnative controller10120を維持し、両PCのwaiterを復旧serialへ再接続した。
関連テストは111 passedで、詳細・保存source・log・証跡は[復旧結果](c3t0_dgx_recovery_result_2026-10-22_ja.md)にまとめた。
クラスタは265435と265438がR、各1node・合計2nodeを維持する。
正式完了8/12条件とC3T0回収256/768群は変わらず、今回の復旧を科学的精度の認定とは扱わない。

## 12:55 JST：現状確認、全trace監査終了とDGX処理の停止

低ノイズ正式比較は8/12条件、主4条件は別枠で完了している。
C3T0全trace監査265436は12:51:32 JSTにExit_status 0で終了し、既存controllerのcompleted.jsonでもfull_audit_acceptedを確認した。
これはC3T0全体の科学的受理ではない。
C1T2最終解析265435とC3T1 sample1の265438はPBS実状態Rで、各1node・合計2nodeである。
265438のSubmit_argumentsはC3T1のsample/1/partition.shに対応し、開始時刻は12:52:51 JSTである。
laboはC3T0 batch4の実PID21040が稼働中で、completionは未作成だった。
C3T0の独立照合済み回収は256/768群・22,528行である。
DGX向けserialはbatch8のexportで約300秒のSSH待機上限に達して停止し、集約・転送・最終解析準備・実行待機・後処理の各driverも前段失敗を検知して停止した。
クラスタ側の入力アーカイブは完成しており、[完成証跡](data_tile_validation_2026-10-17/c3t0_dgx_batch8_export_completed_proof_20261022_v1.json)に全体hash・receipt・元入力と生成jobの照合を保存している。
[復旧仕様](c3t0_dgx_export_reconciliation_spec_2026-10-22_ja.md)は作成済みだが、DGX向け復旧adapterの実装・受入テスト・再開は未実施である。
既存計算の再実行は行っていない。
GitHub実照会でリポジトリはprivate、mainのHEADは886b44b9fdc56d5b86491302dfb651285bbc4113で、同headのCI 39325976119と公開候補のCI 39267489093はsuccessだった。
公開候補の準備と長期数値検証の完了を区別し、今回の確認ではcommit・push・公開操作を行っていない。
全体完了時刻は復旧後の実測で再見積もりが必要で、従来の10月24〜25日という目安を確約とは扱わない。

## 12:45 JST：C3T0全trace監査をqsub投入、2jobの実行を確認

既存audit controllerが全trace監査をqsub投入し、job IDは265436.node-PRISMで、PBS実状態R・run_count 1・開始時刻12:44:16 JSTを確認した。
投入記録とPBSのSubmit_arguments・資源要求の一致を確認し、1node・96CPU・82GB・walltime上限90分である。
投入completion SHA256は `17b59ff2c2bc33c29ff931a4877eb311037cddb5cb061172e56c67d99d89d7ec` である。
独立PBS観測は `data_tile_validation_2026-10-17/c3t0_full_audit_submission_observation_20261022_v1.json`、SHA256は `ee184f80791004306af0ecffe1eb4e481d91da6cdce24ba52aa9c460d6616d86` である。
C1T2最終解析265435もR・run_count 1で、両jobは各1要求node・合計2nodeを維持する。
全trace監査と最終解析の実行開始であり、正式完了8/12条件とC3T0回収256/768群は変わらない。

## 12:43 JST：C3T0の回収が256/768群へ進展

DGX batch7の実PID342434の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は256/768群・22,528行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v12.json`、SHA256は `81601237d41bda56873478365136d69f9fb66eeaf0c05ad9e8c4d423a529c006` である。
completion SHA256は `08e4dfea09986f102bd2c47bdbbffd7a1b6a54ff1d26c81866324850aa48f081`、ZIP SHA256は `6d7a05c0e0b0b08139ea18e70f4dbc43baf5376b5213d38122fceef9aff75b42` である。
既存serialの次batch8のexport子PID21744とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 12:42 JST：C1T2最終解析をqsub投入、実行開始を確認

既存controllerが `qsub /home/user/workspace/mcmc4qec/20261021-planned-c1t2-final-v1/report.sh` を実行し、job IDは265435.node-PRISMである。
PBS実状態RとSubmit_argumentsの一致を確認し、実要求は1node・1CPU・32GB・walltime上限12時間だった。
投入completion SHA256は `747a90d39659714a7ade109e96caeec43c80cacb00bdf0c253f4f58c0f6fe76e`、独立PBS観測は `data_tile_validation_2026-10-17/c1t2_final_submission_observation_20261022_v1.json`、そのSHA256は `592ddbc5e646b2e93edd33129adf7d72f33b06332229e6eafd68ea63b6baab85` である。
C3T0の全trace監査planも完了し、1node・96CPU・82GB・walltime上限90分の構成で投入前検査へ進んだ。
全trace監査plan completion SHA256は `cd43fd2d6421bb303f1733eb284f73a6d249a29fb37c95c79499274b2538916a` である。
容量監査からの予測2210.79秒は資源外挿であり、96worker時のI/O競合や完了時刻を保証しない。
全trace監査のjob IDはこの時点で未確認で、正式完了8/12条件は維持する。

## 12:39 JST：C3T0容量監査の正常終了を受理

PBS実照会で265424はF・Exit_status 0・run_count 1、walltime1分05秒、終了時刻12:37:39 JSTだった。
既存audit controllerは容量監査の終端を受理し、全trace監査のplan作成へ進んだ。
容量監査の終端SHA256は `a3094521ae24485b93180daba1305948117ea1398bdcbc4b8ff676c31d4055b7`、local capacity-complete-completed.jsonのSHA256は `694cef3f69ee83a47fc4a0b2d0f37f1fc603293b94923296cc9435126617e6e4` である。
全trace監査のjob IDとC1T2最終解析のjob IDはまだ未確認で、各controllerのSSH子PID24404と20648の稼働を確認した。
容量監査の終了は全trace監査や条件全体の科学的受理ではなく、正式完了は8/12条件を維持する。

## 12:38 JST：C3T1 sample0終了、C3T0容量監査開始、labo batch4開始

PBSの実状態で265423（C3T1 sample0）が12:36:32 JSTにF・Exit_status 0・run_count 1で終了し、walltimeは7時間59分27秒だった。
同時刻に265424（C3T0容量監査）がRへ移行し、実要求は1node・96CPU・340GBである。
PBS生記録は `data_tile_validation_2026-10-17/cluster_transition_observation_20261022_1237.json`、SHA256は `7167e33f5c31387d960b928ca83d681d4b1f0451278ffb2f962d4e7e601d146f` である。
これはsampling partitionの正常終了であり、C3T1全体の生成・監査・BAR解析の完了とは扱わない。
C1T2の既存実行controllerはsubmit-000-intentを作成し、SSH子PID20648が稼働中だが、この時点ではqsubのjob IDをまだ確認していない。
labo batch4は起動子PID24616へ進み、labo上の実PID21040と固定config `8a1c3333b4c56982db207abee6417bb69153b53c0112ce86240b69b54bb15fad` の一致を確認した。
DGX batch7の実PID342434も稼働中で、C3T0回収236/768群と低ノイズ正式完了8/12条件は変わらない。

## 12:32 JST：C3T0の回収が236/768群へ進展

labo batch3の実PID21316の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全112 member・固定割当・source/input hashを独立照合した。
C3T0の回収は236/768群・20,768行となった。
追加2,112行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v11.json`、SHA256は `2e7ce534509181baf38e0c2c3191ae8565b031ddc3606fb645c08b2b15609a60` である。
completion SHA256は `82f841c1a9dccf02d0cc7955b2f6466c3a1f2fe23ec5608afb44a944276085a6`、ZIP SHA256は `3fa4935c4649d7631a54f1591debbfaebaf851652c36c4ec50fbe83be2c08daa` である。
既存serialの次batch4のexport子PID39280とcommandの一致を確認し、再投入・停止は行っていない。
qstatでは265423がR、265424がQで、正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 12:24 JST：C3T0 DGX batch7の解析開始を確認

既存serialはbatch7のexport・preposition・stageを完了し、launch子PID41612へ進んだ。
DGX上の実PID342434の生存と固定config `450782870990153da261d4118eb6443ab24a4564c7260c74f77157894276ff7d` の一致を確認し、completionは未作成だった。
labo batch3の実PID21316も稼働中である。
解析開始の確認でC3T0の回収212/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 12:19 JST：C3T0の回収が212/768群へ進展

DGX batch6の実PID285094の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は212/768群・18,656行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v10.json`、SHA256は `958b14931558d5c88bad6322df01a20b2350029f9ef55196684956246aaa3499` である。
completion SHA256は `14799eb2735de819502dab0cdf7a90fe216926a15cf471dad036992f80f13919`、ZIP SHA256は `ce1d0b1d0932f6a39a48f1568874bad26e7445f52812265e446feabbbe79611c` である。
既存serialの次batch7のexport子PID49232とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 12:01 JST：C1T2の最終解析準備完了とC3T0 DGX batch6開始

C1T2の既存preparerは正常応答し、最終解析のconfigとqsub用scriptを生成した。
クラスタ上の実ファイルをsha256sumで確認し、config `9958c602d6f7a02e67125718c410c9489b53302c8de552c71c127a115af5c54e` とscript `9d7360ea7827864ac1d39cdadc7b11c362eefc7f1ddaf7455977361b42690b3b` が準備結果に一致した。
準備completion SHA256は `b8ba20317e8cfae385c5170bd11e5a2948b657f332280db6ba2b608278558bc4` である。
要求メモリ32GB・walltime上限12時間で、これは所要時間の予測ではなく、状態はprepared_not_submittedである。
既存実行controller PID39644は後続preflightへ進んだが、最終解析jobの投入・完了や科学的受理は未確認である。
12:03 JSTの確認では後続preflightも完了し、configとscriptのhashは上記に一致した。
preflight completion SHA256は `aa38ca0abcb0fa36d68882c1a55df657a431a859612c86d2f1b0be34b4e9a416` である。
実行controller PID39644は稼働中で、265423のRと265424のQが各1要求nodeを占めるため、2node上限の枠待ちとなっており、C1T2のqsubは未実施である。
DGX batch6の実PID285094とconfig `d90ef5f518f2eacd05e3a2ca3f537d822d4b02b37c1158e7f7d924758e568cd4` の一致を確認し、解析開始を確認した。
labo batch3の実PID21316も稼働中で、C3T0回収192/768群と低ノイズ正式完了8/12条件は変わらない。

## 11:57 JST：C3T0の回収が192/768群へ進展

DGX batch5の既存driverによる転送後に、ZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は192/768群・16,896行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v9.json`、SHA256は `fa2429cbbf7fdcdb24b9104de5f16e1ff5b177e9ca3cfb1a69e6b40b087308e2` である。
ZIP SHA256は `528002ccdcde00bd35396114a473f92efde5adeca1227703cf8163da52c37245`、転送検証記録SHA256は `8c00ee979ee8c37c780219c7a6e929f77a3c921cd4496747846d454789fcd5db` である。
既存serialの次batch6のexport子PID23456とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 11:55 JST：C1T2の入力転送完了と最終解析準備の開始

既存distribution controllerが170ファイル・5,602,897,252 byteの転送完了receiptを保存した。
固定planとreceiptの全target/hash・件数・byte合計・context・転送先の一致を独立照合した。
receipt SHA256は `bae56ab2cca92550fc3c94f477c6ec6735a000c015a3d7c154301a2bcb73183a`、controller completion SHA256は `7b1863b4179671b77370c1eca77854aa5605cbff3b75731a748c3e8c3d8bc43c` である。
既存の最終解析準備waiter PID44648はrequestを生成し、固定preparerを呼ぶSSH子PID34040の稼働を確認した。
最終解析jobのqsubはこの時点で未実施であり、正式完了8/12条件は維持する。
C3T0 DGX batch5は実PID274966の終了とcompletion `6fc50ce7d16f948be877a76e17fd4fd3c3087ad15d0426a0fc6a6fd232301054` を確認し、既存回収子PID47248が稼働中である。
batch5はまだ転送検証前のため、C3T0回収172/768群には加えていない。

## 11:44 JST：C1T2の全体index完了と後続準備の開始

C1T2の全体index PID30568は終了し、既存controllerのcompletionとsnapshotが作成された。
snapshotとregistryのSHA256を独立照合し、38batch・768群の重複なし・67,584行・未観測0と群別集計の一致を確認した。
診断警告は67,584行、未定義項目を含む行は67,572行、区間未取得は0であり、分母から除外していない。
snapshot SHA256は `5f04a5b71647632391a7231e4173e8df7b0dd186f3b13c16a8275d33394c3387`、completion SHA256は `c233757e8d7d628fce6d64ad2425b4b21b9bb1efd399bc623b0eca52b4dd34a1` である。
既存distribution controllerは最終解析用の入力準備へ進み、子PID45920と固定recipeを指定するcommandの一致を確認した。
その後170ファイルの入力準備が完了し、11:45 JSTに転送PID46800と実scp子PID40516の稼働を確認した。
転送plan SHA256は `e4ef22c2847fa4ac68ac47d4138ab7ddb539e9cab6f8988e4f58107e1502f444` で、転送完了receiptはまだ作成されていない。
これは保存結果の全体index完了であり、最終解析・独立数値照合・条件全体の科学的受理は未完了のため、正式完了は8/12条件を維持する。

## 11:42 JST：稼働状況と公開状態の再確認

DGX batch5のexport・preposition・stageの完了記録と、DGX上の実PID274966の生存を確認した。
固定configは `08e5be32eca9aaf40689b2e883fe6298602cb788736578a2364df8b54cf14ad9` で、completionは未作成だった。
labo batch3の実PID21316も生存し、固定configの一致を確認した。
C1T2の全体index PID30568は稼働中でCPU累積4096.47秒、最終snapshotは未作成だった。
qstatでは265423がR・経過7時間03分、265424がQで、各1要求node・合計最大2nodeを維持している。
GitHub APIではリポジトリはPRIVATE、Releaseは0件であり、local HEADは `886b44b` だった。
C3T0回収172/768群と低ノイズ正式完了8/12条件は変わらず、手動再投入・停止・公開操作は行っていない。

## 11:33 JST：C3T0の回収が172/768群へ進展

DGX batch4の実PID265461の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は172/768群・15,136行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v8.json`、SHA256は `fb9ad5270b182c0f3093318320347ff012d6c7e5bdc593bc3180c5ad619eef86` である。
completion SHA256は `ab361151e3ebd763490474edd12c325b64419312797fcc28232b3caa4687d4bd`、ZIP SHA256は `6ecaaefa41af1882934ddb7aa3ca949519c3b3a4cdd8d5b85d38b8869e458c17` である。
既存serialの次batch5のexport子PID42728とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 11:14 JST：C3T0 DGX batch4の解析開始を確認

既存serialはbatch4のexportを終了コード0で完了し、preposition・stageを経てlaunchへ進んだ。
DGX上の実PID265461の生存と固定config `77df43d755d0fa0e3fdcb394f96120c29ad2a3f9d402c6af881bfb932583beeb` の一致を確認し、completionは未作成だった。
解析開始の確認でC3T0の回収152/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 11:10 JST：C3T0の回収が152/768群へ進展

DGX batch3の実PID209394の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は152/768群・13,376行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v7.json`、SHA256は `5ccb4fa6f6c76242c960c45d17dc5f18fa867c4a237b07704e645c8182b7b7e7` である。
completion SHA256は `e1f175a18e04ef8977bd22f13b0b9e53fbb9decc410284de6e823e2001321ed4`、ZIP SHA256は `5605eb05fdd4f104394e4108132e410ccc3b1b1a396975da8ccac160a98eda39` である。
既存serialの次batch4のexport子PID30484とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 10:59 JST：C3T0 labo batch3の解析開始を確認

既存serialの子がbatch3のlaunch PID46828へ進んだことをcommandとともに確認した。
labo上の実PID21316の生存と固定config `7c39b975f083159ca184f83e2166a5ffec050845e047c33b67fcddf535784a22` の一致を確認し、completionは未作成だった。
解析開始の確認でC3T0の回収132/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 10:54 JST：C3T0の回収が132/768群へ進展

labo batch2の既存driverによる転送後に、ZIP全体・全112 member・固定割当・source/input hashを独立照合した。
C3T0の回収は132/768群・11,616行となった。
追加2,112行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v6.json`、SHA256は `1470ebe1a0d7f2b0c2212efb6210df0455953d1c073f986798d4204b2f551225` である。
completion SHA256は `fb7e0c6b8d30af5636f4785fd948264d4f122fa58b50d887c14ce4c46f4bb797`、ZIP SHA256は `354be3d4c611caba2acc13a6f5c1b3ed77c87e29c5349a0d0144f587c865986d` である。
既存serialの次batch3のexport子PID29700とcommandの一致を確認し、再投入・停止は行っていない。
C1T2の全体index PID30568も実行中であり、正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 10:52 JST：C3T0 DGX batch3の解析開始とlabo batch2の終了を確認

DGXの既存serialはbatch3のexport・preposition・stageを完了し、launch子PID45280へ進んだ。
DGX上の実PID209394の生存と固定config `519aaab237b59fd281be46a047a7147a2a9acc1966725a41a4c512bf9b565c5f` の一致を確認し、completionは未作成だった。
labo batch2は実PID30420の終了と固定configに対応するcompletionを確認し、そのSHA256は `fb7e0c6b8d30af5636f4785fd948264d4f122fa58b50d887c14ce4c46f4bb797` だった。
laboの既存回収子PID43184は稼働中で、転送検証記録はまだないため、このbatchを回収済み件数に加えていない。
C3T0の回収108/768群・正式完了8/12条件を維持し、手動再投入・停止は行っていない。

## 10:46 JST：C3T0の回収が108/768群へ進展

DGX batch2の実PID199961の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は108/768群・9,504行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v5.json`、SHA256は `3802a6d7a01e4ded683a017321d70354b1a69686329a800fbdc0076e0a278f9b` である。
completion SHA256は `91b9e0e0f6204aae0838cb10fb3ffc857034abf3dfab540c355910985f7e4a38`、ZIP SHA256は `67a1e356bf70ddc4a9be7aeb9835ad004052aa1db08da0636b16978379e9053b` である。
既存serialの次batch3のexport子PID4124とcommandの一致を確認し、再投入・停止は行っていない。
C1T2の全体index PID30568も実行中であり、正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 10:28 JST：C3T0 DGX batch2の解析開始を確認

既存serialのbatch2についてexport・preposition・stageの完了記録を確認し、launch子PID22572とcommandの一致を確認した。
DGX上の実PID199961の生存と固定config `9374eef89b30cbfed2d0a0e7ab04ba08c61f9ffd19eae283dc7021150a54f383` の一致を確認し、completionは未作成だった。
解析開始の確認でC3T0の回収88/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 10:24 JST：C3T0の回収が88/768群へ進展

DGX batch1の実PID143705の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は88/768群・7,744行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v4.json`、SHA256は `5b44c1a7218acc41da3487ebb714b0c6186ebde7cf2bfa4eb375e108fc66d4cd` である。
completion SHA256は `2ee95243da7e4514d3a77cb1005979c76d034fb67510e4e339f77884e02df090`、ZIP SHA256は `224e8bb47f058146ed5b7a820306eb44db6b14efb29ea874eba0cf0c2dcf43d8` である。
既存serialの次batch2のexport子PID19816とcommandの一致を確認し、再投入・停止は行っていない。
C1T2の全体index PID30568も実行中であり、正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 10:06 JST：C3T0 DGX batch1の解析開始を確認

既存serialのbatch1についてexport・preposition・stageの完了記録を確認し、launch子PID47956とcommandの一致を確認した。
exportの実終了コードは0で、DGX上の実PID143705の生存と固定config `26807c5e25267ee658109394417d5a7e551a19d73c408b3648f19732a1841819` の一致を確認し、completionは未作成だった。
解析開始の確認でC3T0の回収68/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 10:01 JST：C3T0の回収が68/768群へ進展

DGX batch0の実PID134500の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C3T0の回収は68/768群・5,984行となった。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v3.json`、SHA256は `ed9ed30c515528ba257b418e27068fdfd68ab0cb3c80cd7e9a4d937168236276` である。
completion SHA256は `264eff17a8cbdc8147e55e0fdebd2036331c0ab83b32e1b9ab425b1bed172dbd`、ZIP SHA256は `7e73f4d69885005145e46c74b20ed73ef1ac8179d4a70a6681012fd34042bcbb` である。
既存serialの次batch1のexport子PID35040とcommandの一致を確認し、再投入・停止は行っていない。
C1T2の全体index PID30568も実行中であり、正式完了8/12条件は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 09:45 JST：C3T0 DGXの基準照合を通過しbatch0が解析開始

既存serialはexport・preposition・基準環境とのreplay照合・stageを完了し、launch子PID46828へ進んだ。
照合の受入記録は `data_tile_validation_2026-10-17/portable_condition_c3t0_dgx_parity_dispatch_v1/accepted.json`、SHA256は `b63b65c80866033433e608aa71e862a0e84a381cb022143c6f35995e160b0f87` である。
serialの完了記録とのhash一致と受入記録が参照するlocal source/inputのhashを再確認し、`replay_verified=true`・`scientific_cohort_accepted=false` を保持した。
DGX上の実PID134500の生存と固定config `a6a8bce7d11cbadbc9fe5017710b02486e4492afdcd0b6fd3cd99cebbf8e18e2` の一致を確認し、batch0のcompletionは未作成だった。
この照合と解析開始を条件全体の精度認定とは扱わず、C3T0の回収48/768群・正式完了8/12条件は変更しない。

## 09:34 JST：C1T2全768群の回収・byte照合が完了し全体集計へ移行

DGX batch32の実PID122615の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全48 member・固定割当・source/input hashを独立照合した。
過去の固定観測記録と今回の結果を結合し、C1T2の回収は全768/768群・67,584行となった。
最後の704行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v33.json`、SHA256は `939d05c220c393631b8f9a09ba8de56239e7b11b38fc4e98eae6e44c14eca4b0` である。
completion SHA256は `dbc6f51a9b8aee3989ed4d64fac495820c88c12a5e6bd6ace86d4e868c87c975`、ZIP SHA256は `ef549c785c115f52c8bb5880e6c4e0d30579a3ecee63565bb9edd5d968855ce0` である。
DGX serialの完了記録のSHA256は `19ded0b0be625bf69af41c02f8057c877a9b6524497f7395e1d926b3ec056921`、PC handoffの完了記録は `4f511ff2bb1b7ffe55249d1a7b7cd23222da3de42184f38a528ca0e6c615b816` である。
既存cohort indexの子PID30568とcommandの一致を確認し、全体集計が開始した。
DGXは既存C3T0 waiterを通じて次条件のserial PID37208へ進み、手動再投入・停止は行っていない。
回収完了は科学的な精度認定や最終集計の完了とは区別し、正式完了は8/12条件のままである。

## 09:21 JST：C3T0 labo batch2の解析開始を確認

既存serialのbatch2についてexport・preposition・stageの完了記録を確認し、launch子PID46752が実行中であることを確認した。
labo上の実PID30420の生存と固定config `f79f5c8ec86cb544e91feb4a202cb35510c183ee68b7f1458a6e46c6f09ced81` の一致を確認し、completionは未作成だった。
解析開始の確認でC3T0の回収48/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 09:19 JST：C1T2 DGXの最終batch32が解析開始

既存serialのbatch32についてexport・preposition・stageの完了記録を確認し、launch子PID17484が実行中であることを確認した。
DGX上の実PID122615の生存と固定config `67c6e33d828feb35a62f5c066ac7aa22b7b238fabad56ce4d34a973a4ee00947` の一致を確認し、completionは未作成だった。
このbatchは残る8群に対応し、解析開始の確認で回収760/768群や正式完了8/12条件は増やさない。
監査ジョブ265424の実qstatはQで、確認時のcommentは要求96 CPUに対して利用可能88 CPUという資源不足だった。
入力検証の失敗とは扱わず、既存の投入・固定入力を保持して待機し、手動再投入・停止は行っていない。

## 09:17 JST：C1T2の回収が760/768群へ進展

DGX batch31の実PID63966の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C1T2の回収は760/768群・66,880行となり、残りはDGXの最後の1 batch・8群である。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v32.json`、SHA256は `c63fcf06b4a2bfba02f80ccacaeacf50210569da79f3625440453bd21dfc5aa5` である。
completion SHA256は `6d55ba1038953f83138a31c695abe74671e3f8b7cca1fde5fe271bfb9e756884`、ZIP SHA256は `76733c64f5738baf9cefb8b8767c9740f3f894b40ef45df89bd5bf7f68545ffe` である。
既存serialの次batch32のexport子PID5212とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件と、別条件C3T0の回収48/768群は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 09:15 JST：C3T0 laboの回収が48/768群へ進展

labo batch1の実PID14196の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全112 member・固定割当・source/input hashを独立照合した。
C3T0の回収は48/768群・4,224行となった。
追加2,112行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v2.json`、SHA256は `6d33c076ef6a5e6200fc8173a5d24c4b64fc08a1912864f3e725b8f4a1913e79` である。
completion SHA256は `100a54a68e5e4e918a9353b263c29b6b5b65522b285b25eaba053993af0a23e5`、ZIP SHA256は `0574b5cf16de55e59efd6e93f1bae37edfbf36fd824cd722a7fb9e5c67e188ee` である。
既存serialの次batch2のexport子PID7416とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件と、別条件C1T2の回収740/768群は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 09:12 JST：C3T0のcapacity監査を既存driverがqsub投入

既存handoffはcapacity preflightを完了し、`qsub .../partitioned-trace-capacity-3-0-retry8h-v1/trace-audit.sh` で265424を投入した。
投入記録は `data_tile_validation_2026-10-17/c3t0_recovery8h_audit_handoff_v1/capacity-submit-completed.json` にある。
要求は1 node・96 CPU・340 GB・24時間、worker数8であり、この時間・メモリは初期capacity上限であって実測値や終了予測ではない。
実qstatでは265423がR、265424がQで、稼働・待機を合わせた要求node数は2だった。
full trace auditと条件全体の検証は未完了で、正式完了8/12条件は変更しない。

## 09:10 JST：C3T0 collectorが正常終了し監査準備へ移行

PBSの実履歴で265421がF・Exit_status 0・run_count 1、walltime 04:45:02で終了したことを確認した。
既存handoffは固定configに対するcollector完了検証を通り、`recovery_collected=true`・`full_trace_audit_still_required=true` を記録した。
worker completionのSHA256は `b13cb4c17e5cca0fc8fcc204358feeb73a91334db630244b7b7bbf80d9a1cd79` である。
PBS終了記録は `data_tile_validation_2026-10-17/c3t0_recovery8h_audit_handoff_v1/collector-observed-terminal.json`、SHA256は `1bc65ea85bec7d91bf2c539e5f35dbd265a4a5c95d971abf6d66be488b9d9d8e` である。
完了検証記録は同directoryの `collector-complete-completed.json`、SHA256は `ee1ea8b17948492dbcc78db37f7cf4fbccce2bf9f69bf356ed418526ef0e82a1` である。
既存controllerの実PID24324とcapacity preflight子PID42884を確認し、後続監査の事前確認へ進んでいる。
この時点のクラスタ実行中ジョブはC3T1 samplingの265423だけで、手動の再投入・停止は行っていない。
収集工程の正常終了を条件全体の検証完了とは扱わず、正式完了は8/12条件のままである。

## 08:54 JST：C3T0 collectorの可視出力が進展

265421はR・run_count 1・cpupercent 99で、PBSが返すwalltimeは04:28:39、summaryは未作成だった。
保存済み08:00時点のtask indexは14,677,250 byteで、今回17,822,202 byte、最後の完全行はsample partition 1のtask `[3,0,1,1,137,0,2]`・status okへ進んだ。
記録は `data_tile_validation_2026-10-17/c3t0_collector_progress_20261022_v5.json`、SHA256は `3ef6bfe17773955c6bf3061b049769e6cf8e8bcf491300b796a6458bf535906e` である。
固定sourceと保存済み観測器のbyte一致を確認し、同じremote programで32 KiBだけを読み取った。
可視出力の進展を正確な完了率・残り時間・全収集成功へ換算せず、processへのattach・停止・再投入は行っていない。

## 08:53 JST：C1T2 DGX batch31の解析開始を確認

既存serialのbatch31についてexport・preposition・stageの完了記録を確認し、launch子PID43268が実行中であることを確認した。
DGX上の実PID63966の生存と固定config `5c873724b460d4d710b747eb5af1560f51adc2d47409fe10f9416c370f716385` の一致を確認し、completionは未作成だった。
解析開始の確認で回収740/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 08:49 JST：C1T2の回収が740/768群へ進展

DGX batch30の実PID51646の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C1T2の回収は740/768群・65,120行となり、残りはDGXの2 batch・28群である。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v31.json`、SHA256は `16df5788a47890a39e4cf5f9db3f8f081d78cf89c6af7df5ef241ba92c73a50e` である。
completion SHA256は `d73850c6a0e9521438627368d09d62aa4da9247f4310e992ae4266b57f442a3f`、ZIP SHA256は `e33f2be7cb844f0f25b77fa336e1b198df7a44a9d1b45d264817f8520255b4e4` である。
既存serialの次batch31のexport子PID41216とcommandの一致を確認し、再投入・停止は行っていない。
正式完了8/12条件と、別条件C3T0の回収24/768群は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 08:29 JST：保存先の空き容量を確認

各実行環境の保存先について、Pythonの `shutil.disk_usage` とクラスタの `df -B1` でファイルシステムの空き容量を読み取った。
ローカルAドライブは188,778,708,992 byte、DGXの実行環境は212,102,762,496 byte、laboのDドライブは7,907,623,657,472 byte、クラスタの `/home` は13,574,472,536,064 byteだった。
DGXの固定実行環境直下の `c1t2-*` 124 directoryは `du -sb` の合計で28,439,296,723 byteだった。
このdirectory合計はapparent sizeであり、ファイルシステムの使用block数や未開始条件の必要容量と同一視しない。
現在の空き容量は個人quotaや今後の全工程の容量保証ではなく、ローカルとDGXは回収の進行に合わせて再確認する。
ファイルの削除・移動は行っておらず、DGX batch30の実PID51646は引き続き生存し、completionは未作成だった。

## 08:25 JST：C1T2 DGXの次batchが解析へ移行

既存serialのbatch30についてexport・preposition・stageの完了記録を確認し、launch子PID30976が実行中であることを確認した。
DGX上の実PID51646の生存と固定config `a20956664a7bb32d7ab9f61c778ed60d9cb597aecb55d94012282dfa48e0cbd9` の一致を確認し、completionは未作成だった。
C1T2のサンプリング監査とnative referenceの完了記録、後続index・distribution・final preparation・final executionの実processを点検し、確認した経路にerror記録はなく、残るPC回収待ちだった。
解析開始の確認で回収720/768群や正式完了8/12条件は増やさず、手動再投入・停止は行っていない。

## 08:21 JST：C1T2の回収が720/768群へ進展

DGX batch29の実PID4187527の終了と固定configに対応するcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C1T2の回収は720/768群・63,360行となり、残りはDGXの3 batch・48群である。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v30.json`、SHA256は `18308f7d00d03cb5c5ec0f0d07f6192a1274526c9bf6213928fde5bd25f187eb` である。
completion SHA256は `27c7a9c3dbfd51c5731d7744e21d9f1a3f091b2e5b0ad6304266a72df71e29c3`、ZIP SHA256は `823468517612c1d067dc71f494283ccccddc7816dcf600e49751411cba65daa4` である。
既存serialの次batch30のexport子PID12740とcommandの一致を確認し、再投入・停止は行っていない。
後続の集計・独立計時・報告など10個のcontrollerについて実processとcommandを確認し、確認対象の履歴にerror記録はなく、先行入力待ちだった。
正式完了8/12条件と、別条件C3T0の回収24/768群は変わらず、この回収を科学的な精度認定や条件全体の完了とは扱わない。

## 08:05 JST：公開候補とGitHub状態を再確認

GitHubの実APIでリポジトリはPRIVATE、release一覧は空であることを確認した。
local HEADとremote mainはともに `886b44b9fdc56d5b86491302dfb651285bbc4113` で、対応CI run39325976119は全12job成功のままだった。
固定公開候補 `47ef1b6ad957a93dae3bbd6cf1d79fab86457e96` のCI run39267489093も全12job成功を確認した。
候補から現在のHEADまでのコミット差分はdocs・ignore・TODOの範囲で、src・tests・examples・notebooks・pyproject・日英READMEには未コミットまたは未追跡の差分がなかった。
公開用4ファイルとrelease説明文を再hashし、保存済みの固定値と一致した。
記録は `data_experimental_release_2026-10-19/remote_status_20261022_v2.json`、SHA256は `69743ef8bf31b53905de6927d9a48f8daff1aa1eeec36f926a6e7e7068877a30` で、読み取り用scriptも同階層に保存した。
この確認でCI再実行・再build・commit・push・公開操作は行っていない。
クラスタの265421・265423はこの時点でもR・run_count 1・合計2要求nodeで、未完了の数値検証は継続中である。

## 08:00 JST：C3T0 collectorの可視出力が進展

265421はR・run_count 1・cpupercent 99で、経過時間03:34:33、summary未作成だった。
保存済み07:12時点の観測で10,483,986 byteだったtask indexは14,677,250 byteとなり、最後の完全行はsample partition 1のtask `[3,0,1,0,107,0,1]`・status okへ進んだ。
07:12時点の短い観測で見えなかった出力の進展を今回確認したもので、正確な完了率・残り時間・全収集成功へは換算しない。
記録は `data_tile_validation_2026-10-17/c3t0_collector_progress_20261022_v4.json`、SHA256は `76239380f837ad65716e13b04d48d11b3ab8afb2c25983613555f0220d83f4f1` である。
保存済み観測器と同一のremote programで32 KiBだけを読み、計算processへのattach・停止・再投入は行っていない。

## 07:54 JST：C1T2の回収が700/768群へ進展

DGX batch28の実PID4176692の終了と固定configのcompletionを確認し、既存driverによる転送後にZIP全体・全96 member・固定割当・source/input hashを独立照合した。
C1T2の回収は700/768群・61,600行となり、残りはDGXの4 batch・68群である。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v29.json`、SHA256は `a85bccd74081dfe8969b04925c198ec8a42a327d3a861ba724ed722d23f6696a` である。
completion SHA256は `0444b67564609198e93e7acfa2e4e63c820036ecf77a33547a0b82656d7a1180`、ZIP SHA256は `13843ea51f4f44132fcc11e7615afa58e919e1da8f88fceca683f476722e4a9a` である。
既存serialの次batch29のexport子PID33984とcommandの一致を確認し、再投入・停止は行っていない。
クラスタの265421・265423もR・run_count 1・合計2要求nodeを確認した。
正式完了8/12条件と、別条件C3T0の回収24/768群は変わらない。

## 07:44 JST：C3T0 laboの次batchが解析へ移行

batch1の入力exportは正常終了し、同一local serialの開始・完了記録によるexport工程全体は329.84秒だった。
この時間は転送を含む工程全体であり、SSH subprocessだけの時間や科学的な計時結果とは区別する。
完了記録のhash、prepared input、stdout/stderr、受け入れ済みexport helper、後続preposition・stageの完了記録を照合した。
記録は `data_tile_validation_2026-10-17/c3t0_labo_export_wait_runtime_20261022_v1.json`、SHA256は `49e69b4f59020502faf3d4ac53bef4023571f1ed7fbddfe530a480e6089add11` である。
laboのbatch1では固定config `a05bf6bc6a3b295b6ef77d524fbe91e8e810b54e5e7993e6cae2964fbec1364f` と実PID14196の生存を確認し、completionはまだ存在しない。
この入力準備・起動の確認でC3T0の回収数24/768群や正式完了8/12条件は増やさない。

## 07:38 JST：C3T0 labo初回24群を回収

tile288 depolarizing、p=0.01のlabo batch0について、実PID10356の終了と固定configに対応する正常completionを確認した。
completion SHA256は `9893df7080d2b80a5141f5be9febb3a8b46c33fd44b62d1827136ad060d692c3` である。
既存driverによる回収後、ZIP全体・全112 memberのbyte hash・固定割当・source・transfer receiptを独立照合し、C3T0の回収を24/768群・2,112行とした。
追加行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持する。
観測は `data_tile_validation_2026-10-17/c3t0_pc_collection_observation_20261022_v1.json`、SHA256は `65b597bb28708faaf5fca8f8a96d2f7f36187e45847e71ac78ac6591fad78e7d` である。
ZIP SHA256は `63b31cac37a8ed8b75aab38a4d11d0367591a5995d4dd03a1f0f5fc48cacdf84` である。
観測器は既存C1T2の固定sourceを保持し、C3T0の固定assignment・全768群の集合・条件名だけを明示的に対応させたもので、数値再計算やnative再decodeは行っていない。
既存serialのPID47168と、次batch1のexport子PID40932のcommand一致を確認した。
exportはC3T0 labo向けに既に受け入れた完了待機版を使用しており、今回新しい計算を手動再投入していない。
正式な低ノイズ検証完了は8/12条件で、C1T2の回収680/768群とC3T0の回収24/768群は別に数える。

保存済みの正常completionから、解析本体のwall timeも入力hashとともに記録した。
C3T0 labo batch0の24群は88.48分、C1T2 labo batch0/1の各24群は134.67/133.99分、C1T2 DGX batch0/27の各20群は22.33/22.06分だった。
export・転送・回収・後続監査を含まず、hostごとの担当群も異なるため、公平な計算機性能比較や残条件への時間外挿とは扱わない。
記録は `data_tile_validation_2026-10-17/pc_completed_durations_20261022_v1.json`、SHA256は `86bfc46b2bb6eac6b1ef9f12fee75458ddfd61bf53f2ab066b0c9975cbf01430` である。
観測器は `data_tile_validation_2026-10-17/pc_completion_observers_20261022_v1/` に保存した。
この観測だけでは全工程の終了見込みを狭めず、独立計時の完了とも扱わない。

## 07:29 JST：未開始PC経路のexport待機修正と回収680/768群

[小仕様](future_pc_export_wait_spec_2026-10-22_ja.md)に従い、C3T1/C3T2のDGX・labo入力exportを完了まで待つ別helperを用意した。
変更はlocal SSH exportの300秒待機上限と新helperへの接続に限り、元sourceのhash・固定割当・native parity・archive検証・scp timeout・失敗時停止と再試行禁止を保持した。
元serialのsource pinも新intentへ残し、後続cohortとC3T2の先行条件検査が使う出力先・完了契約を維持する。
C3T1 laboの先行条件は引き続きC3T0 labo復旧serialである。
Windows上のscope、source保持、argv、失敗時停止、入力・native待機、旧履歴固定など65テストが成功した。
最初の実装試験はAST走査順を誤ったテスト期待値だけが失敗し、元sourceの比較とscp timeout保持を変えず、走査順の期待値を修正している。
これはlocal Windows controllerの検証であり、将来の本exportやnative parityを実行済みと扱わない。
受入記録は `data_tile_validation_2026-10-17/future_pc_export_wait_acceptance_v1/`、manifest SHA256は `10a3481c66af21f9d23328e5731fc2ec4066f580c73854ed85630a3f019f1272` である。

旧launcherのPID18780・29256についてcommand・生成時刻・source不変・registry未取得・子処理未開始を確認し、旧intentと観測履歴を保持したまま待受のみを切り替えた。
新PID8700・24964はそれぞれC3T1/C3T2のregistry待機中で、起動後の実生存とchildren空を確認した。
新履歴は `c3t1_future_pc_launch_v1`・`c3t2_future_pc_launch_v1` にあり、切替manifestは `data_tile_validation_2026-10-17/future_pc_export_wait_transition_v1/manifest.json`、SHA256は `f6f866e92d85bd284540d2a60fff95e2a397d57fe09ee1513ecb83912ffb9ced` である。
C1T2・C3T0の稼働中の計算、科学設定、qsub、最大2node制約は変更していない。

DGXのC1T2 batch27は実PID4119947の終了と固定configのcompletionを確認し、回収済みZIP全体・全96 member・固定割当を独立照合した。
回収は680/768群・59,840行となり、残りはDGXの5 batch・88群である。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0で、全行を分母に保持した。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v28.json`、SHA256は `ca7f39e45259896ab4dc7e8d0158b10222cdf589f0f7329706db47f5ca647b94` である。
laboのC3T0 batch0・実PID10356は同じconfigで稼働中、completion未作成だった。
正式な低ノイズ検証完了は8/12条件のままである。

## 07:12 JST：C3T0 collectorの可視出力を読み取り確認

265421に対応するexecution intentと実PBSを照合し、既存のtask index末尾を32 KiBだけ読む観測を約57秒間隔で2回行った。
両観測でR・run_count 1・cpupercent 99、summary未作成であり、可視indexは10,483,986 byte、最後の完全行はsample partition 1のtask `[3,0,0,0,130,9,7]` だった。
この間の可視末尾は変わらなかったが、PBSに記録されたCPU時間は進んだ。
bufferと共有filesystemの可視性、後段の全payload再hashがあるため、これを完了率・ETA・停止判定へ変換しない。
記録は `data_tile_validation_2026-10-17/c3t0_collector_progress_20261022_v3.json`、SHA256は `81f81e7352613d7fdb4d72c5d74022fbf6f6b531b5919ca089aeab9c0bdcce44` である。
最初の観測保存は過去のv1記録と保存名が重複して排他的作成が拒否したため、過去のv1/v2を保持し、別名で再観測した。

計算ノードnode008上のprocessとopen file位置の直接確認も試したが、clusterからのSSH認証が拒否され、node側の観測codeは実行されていない。
この制限を回避したり、計算processへattachしたり、jobを再投入・停止したりはしていない。
SSH拒否の記録は `data_tile_validation_2026-10-17/c3t0_compute_process_observation_20261022_v1.json`、観測器は `data_tile_validation_2026-10-17/c3t0_collector_progress_inspection_20261022_v1/` に保存した。
現時点の観測だけではファイルの可視性の遅延と内部処理の停滞を区別できず、既存のPBS終端監視を継続する。
正式完了8/12条件と回収660/768群は変わらない。

## 06:58 JST：C1T2の回収が660/768群へ進展

DGX batch26の実PID4110139が終了し、固定configに対応するcompletionを確認した。
既存driverが回収したZIP全体・96 memberのbyte hash、固定割当、前回記録の不変性を独立照合し、回収は660/768群・58,080行に進んだ。
追加1,760行は全行に診断警告・未定義項目を含み、区間未取得は0で、全行を分母に保持する。
正式な低ノイズ検証完了は8/12条件で、PC回収だけをC1T2全体の科学的受入とは扱わない。
残りはDGX側の6 batch・108群で、既存serial driverの実PID46624とcommandの一致を確認し、batch27の入力exportへ進んだ記録を確認した。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v27.json`、SHA256は `191541a9eb7ff00e87151e3ebc896be8c8e88c9bfd3db698af949502a2442016` である。
batch26のcompletion SHA256は `467ff23e04a201ed0939ac28250280caecb4956358d12f37fc922038efc73f0d`、ZIPは `e27a6ad9428b83cb86cbd25e2e79d5cac88ad19ad40e54fcccd07c7eb747bd35` である。
計算の再投入・停止は行っていない。

## 06:56 JST：残工程の時間目安を保存記録から更新

C1T2のDGXで回収済みの直近3 batch（23〜25）について、同一local controllerのexport開始から回収完了までの周期は28.64・27.86・27.59分だった。
固定割当の残りは実行中を含む7 batch・128群で、すべてDGX側である。
最後の回収時刻にこの周期の最小値・最大値を7回加える単純外挿は、10月22日09:42〜09:49 JSTとなる。
小さい最終batchにも全batch分の周期を割り当てた条件付きの目安であり、予測区間・完了保証・条件全体の最終集計の終了時刻ではない。

C3T1/C3T2の未終了の標本生成とC3T2 anchorについて、保存capacity予測から実行中265423のPBS経過時間だけを差し引いた合計は42.13 node時間だった。
2nodeを中断なく標本生成だけに使う仮定なら21.07時間に相当するが、現行の依存関係・他工程との資源共有を再現したスケジュールではない。
C3T0 collector・full監査、PC解析、最終集計、全12条件の選択、seed census、独立計時、報告、障害対応は含まれないため、これから全体の終了時刻を算出しない。
実265423はこの確認でもR・run_count 1であり、未投入partitionのsubmission記録がないことも確認した。
入力hash、同一controllerの元時刻、固定割当、capacity予測、PBS経過時間と式を `data_tile_validation_2026-10-17/remaining_work_estimate_20261022_v1.json` に保存した。
SHA256は `b4c0fb9667ecd8de0c93716331d5131c3d959732ad89c810d95f923431c172a3` で、観測器も同階層へ保存した。
全体の10月24〜25日という暫定見込みを狭める証拠はまだなく、正式完了8/12条件と回収640/768群を維持する。

## 06:53 JST：クラスタ・PCの実稼働を確認

クラスタの265421と265423はともにR・run_count 1で、要求node合計2を維持している。
実PBSの経過時間はそれぞれ02:26:29・02:14:36で、cpupercentは99・9502だった。
これは経過時間と稼働の確認であり、残り時間の予測ではない。
DGXのC1T2 batch26・PID4110139と、laboのC3T0 batch0・PID10356は実processが存在し、completionは未作成だった。
生成・PC serial・後続launcher・独立計時と報告の計11 local handleでPIDとcommandが一致し、確認した22の実行履歴に新しいerror/stoppedはなかった。
停止した旧経路のエラー記録はこの22履歴とは別に保持している。
計算の再投入・停止・qsubは行っておらず、正式完了8/12条件と独立照合済み回収640/768群を維持する。
観測は `data_tile_validation_2026-10-17/live_resources_observation_20261022_v2.json`、SHA256は `c798240e569322df8f8f6bda1a645307158f8bd2d3f3d744cface0404a460157` である。
最初のread-only観測はlocal PowerShellの引数指定不備で集約に失敗したため、観測器だけを修正して同じ実job・processを再確認した。
観測器の両版を `data_tile_validation_2026-10-17/live_resources_observer_sources_v1/` に保存した。

## 06:51 JST：独立計時から最終報告までの待機環境を接続

[後段接続仕様](low_timing_execution_v4_reconnection_spec_2026-10-22_ja.md)に従い、census実行・独立計時入力準備・独立計時実行に残っていた親環境v2の固定参照を、別版のdriverでv4へ接続した。
旧環境を渡すとv4の準備receiptを拒否し、v4なら受け取ることを受入テストで確認した。
科学計算と制御ロジックの変更はなく、no-op、48 method行、capacity/main、失敗と曖昧な投入応答、最大2nodeの判定を維持する。
Windows・クラスタLinuxで各88テストが通り、実v4環境のbootstrapと科学moduleの対応を確認した。
受入記録は `data_tile_validation_2026-10-17/low_timing_execution_v4_acceptance_v1/manifest.json`、SHA256は `b9aaacfe4483d3534a75a294270cb8628bbf99cae6bcfe5f9a217781205fa8e1` である。

旧PID8588・40228・38784の実command・生成時刻・source不変・待機出力のみ・計算子processなしを確認し、旧履歴を保持して引き継いだ。
新PID47848・21496・33616は、それぞれcensus準備・census完了・計時準備を待機している。
この切替で実censusや独立計時を開始したわけではない。
切替記録は `data_tile_validation_2026-10-17/low_timing_execution_v4_transition_v1/manifest.json`、SHA256は `c586f2f7e5907a16ec60a0356967ae999ed7ef0f0a58ecbcd9dddcdfdd6844c0` である。

最終報告環境も、計時時のPYTHONPATHをv2に固定していたため、新しい親環境に同じ報告readerだけを重ねた別環境v2を作成した。
計時runtimeのsource・Python・core・PYTHONPATHを元の検査で受け入れることを実クラスタで確認し、環境制約の8テストがWindows・Linuxで通った。
環境SHA256は `e58ac5e1b870bea7e444c453ffa1eac9deba62ae6f57a13e9de8438bea0736c9`、記録は `data_tile_validation_2026-10-17/low_independent_timing_report_environment_v2/` にある。
これは新環境から構成したruntime snapshotの検証であり、未生成の本計時結果を読み終えたという意味ではない。

報告準備と報告jobの接続試験では、複製時の改行変換によって既配置helperとbyte hashが異なることを検出し、最初のnative確認を停止した。
この失敗は計算・投入前であり、sourceと失敗記録を `data_tile_validation_2026-10-17/low_timing_report_v2_reconnection_acceptance_v1/` に保存した。
helperを元とbyte単位で同一に保ち、その一致を追加検証した別試行ではWindows・Linuxで各48テストが通り、既配置report job helperの実bootstrapも確認した。
受入記録は `data_tile_validation_2026-10-17/low_timing_report_v2_reconnection_acceptance_v2/manifest.json`、SHA256は `720d2f32df923ef36ec820ec354f08f6306ee78ff88e8ceaa5fc79a84b5ee3af` である。
旧PID36464・47272も未着手の待機であることを確認して引き継ぎ、新PID19116・49488の実生存と入力待機を確認した。
報告準備・本report jobのqsub・最終報告の受入は未実施である。

5つの新待機process、source不変、旧履歴の保持を06:50 JSTに再確認した。
制御テストは両環境で各136件、環境制約のテストは別に各8件であり、これを本計算の完了や科学的保証へ読み替えない。
統合記録は `data_tile_validation_2026-10-17/low_timing_post_selection_reconnection_v1/manifest.json`、SHA256は `1c7ae81c31cc944d3d22a0ec537b04a6be08020dae0ca17a7e5026dc40731f29` である。
後から追記される待機ログも含め、観測時点の178ファイルを同directoryの `snapshots/` に複製し、`snapshot-manifest.json` にhashを保存した。
科学的な正式完了は8/12条件、C1T2の独立照合済み回収は640/768群を維持する。
06:50 JSTのqstatでは265421と265423がともにRで、要求node合計は2だった。
公開・commit・pushは行っていない。

## 06:40 JST：全12条件の後続接続とPC回収640/768群

正式な低ノイズ検証の完了数は8/12で、残る4条件・独立計時・最終報告は未完了である。
GitHub experimental版の公開準備と区別し、公開操作は行っていない。
全工程の10月24〜25日JSTという見込みは暫定で、後続計算と資源確認が残るため時刻は確定できない。

[最終後続処理の仕様](planned8h_final_downstream_spec_2026-10-22_ja.md)に従い、C3T1/C3T2の新しい最終出力から保存行の算術再確認と計時候補作成へ接続した。
両方が成功した場合だけ完了とする既存の契約を保ち、条件の取り違え、改変入力、片方だけの成功を拒否する58テストが通った。
初回テストの2 failed・56 passedは、source変換が参照元C3T0の固定pathまで置換した実装不備であり、変換後に固定source情報を注入する修正を加えた。
失敗ログを保持し、修正後は58 passed・2.21秒である。
受入記録は `data_tile_validation_2026-10-17/planned8h_final_downstream_acceptance_v1/manifest.json`、SHA256は `bef4c508341dc40ecd9dc4926781900bbd8a309d6ee96392993c182978454a9f` である。
両条件の待機係をPID49384・40684で起動し、06:40 JSTに実processの生存とcollection_ready=falseを確認した。
実最終出力の算術再確認・候補作成そのものはまだ行われていない。

[親環境接続仕様](low_timing_parent_v4_reconnection_spec_2026-10-22_ja.md)に従い、全12条件の親準備とseed census準備も受入済みv4環境へ接続した。
クラスタ上で、元の56 namespace・3,963,562割当の保存監査、source relocation 12件、61 source・28 coreファイルの結合を確認した。
seed列の再生成や新namespaceのcensus、selector、本計時、qsubはこの確認で行っていない。
新basisのSHA256は `c8135e85e23fa877a66e185ab29cc5968be8cae9a601025e570b62558a14c13f`、確認記録は `data_tile_validation_2026-10-17/low_timing_census_preflight_v3/` にある。
8候補だけでは準備しないこと、全12候補の固有環境を保持すること、実basisと親環境の一致、引継ぎの改変・重複・着手済み出力を拒否する56テストが通った。
内訳はassembly 16、parent 21、census 19で、各群の最大実測時間は1.85秒である。
試験とsource・native確認の40ファイルを `data_tile_validation_2026-10-17/low_timing_parent_v4_reconnection_acceptance_v1/manifest.json` に保存し、SHA256は `3202a4a0510f39dc0a75bb00152316862efbc1b2fe4a40d3efb91a193229e6ab` である。

旧親準備PID45160と旧census準備PID49100は、実command・生成時刻・source不変・待機履歴のみ・計算子processなしを確認して引き継いだ。
旧履歴の全byte hashを保ち、新親準備PID41652は8候補で待機、新census準備PID43972はselectorを待機している。
既存のクラスタjobとPC計算は停止していない。
切替証跡と4待機processの実生存確認は `data_tile_validation_2026-10-17/low_timing_parent_v4_transition_v1/manifest.json`、SHA256は `d439bb7ed99317496ba927b76a049f91807eebb80e6fb2e7a13bf42080975b56` である。
全12条件の資源確定と後続selector・独立census・計時は未実施で、24時間枠に収まらない場合は条件を削らず停止する。

C1T2のDGX batch25は実PID4054074の終了とcompletionを確認した。
ZIP全体と96 memberのbyte hash、固定割当、転送記録を独立照合し、回収は640/768群・56,320行に進んだ。
追加1,760行は全行に診断警告があり、未定義項目を含む行は1,756、区間未取得は0で、全行を分母に残す。
観測は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v26.json`、SHA256は `f162336c4424337bcf3878a587783ac5aa8f55950b2f7b061f969143d4687ad6` である。
06:38 JSTの実観測ではC3T0のlabo batch0・PID10356は稼働中でcompletion未作成だった。
クラスタのC3T0 collector265421とC3T1 sample0の265423はともにRで、要求node合計2を維持している。
このPC・クラスタ観測は `data_tile_validation_2026-10-17/parent_v4_transition_observation_20261022_v1.json`、SHA256は `128317f13e2e9ffbbb66446581ba36d501a48e1affff3174b7d22e430457a2bb` である。

## 06:27 JST：8時間版の計時readerと実環境を受入

[計時reader仕様](planned8h_timing_reader_spec_2026-10-22_ja.md)に従い、plannedのcase 3・target 1/2に限って新しいsnapshot source・最終wrapper・初回budget8h ledger・8時間要求へ対応した。
元readerが新fixtureに対してbudget4hのsubmissionを探して停止することを1 failed・4 passedで確認した。
他条件の4時間版とC3T0 retry8h、失敗した旧collectorの履歴、全192 seedと未定義を含む算術、reference、実PBS、archive、source/input検証は保持した。
既存の実行中readerや実環境は変更していない。

初回planned経路へのrecovery_guard・prior_job_idの混入やprior_collection_attempt=true、旧4時間要求、旧snapshot、旧wrapperを拒否する試験を追加した。
追加した履歴混入fixtureを特定の拒否理由まで検証すると、保存report側のauthorityを更新していなかったため、手前のreport整合検証で停止することが分かった。
最初の受入試行はこのfixture不備による1 failed・56 passedを保存して終了し、fixture内の保存reportと監査記録を整合させたうえで、初回回収の履歴検証が拒否することを確認した。
この修正で科学的な検証条件を緩めていない。
旧試行は `data_tile_validation_2026-10-17/planned8h_timing_reader_native_v1/` に保持した。

新しい受入試行ではWindows・クラスタLinuxで各327テストが通った。
内訳はreader 107、dispatch 68、parent 26、metadata 126であり、Windows各群は最大28.75秒、Linux各群は最大13.27秒だった。
受入記録は `data_tile_validation_2026-10-17/planned8h_timing_reader_native_v2/accepted.json`、SHA256は `24834de2b96922f6721a2d5a49a0061da5e1f317794b25df603662c2e3f1933e` である。
これらは小規模fixture・source・metadata・process境界の検証であり、本計算の生traceを用いた子readerの完走ではない。

実クラスタの別directory `20261022-planned8h-timing-environment-v1` で、新readerと受入済みfinal controlsを使う子環境を構成した。
実venvのPython・依存version・source 100ファイル・native 137ファイルと、C3T1/C3T2両方の実監査configのbootstrapを確認した。
各監査のsampling root・full audit rootとmetadata hashを照合し、import前後の環境不変性を確認した。
環境記録は `data_tile_validation_2026-10-17/planned8h_timing_environment_v1/environment.json`、SHA256は `ded046e4ae0cc77edbc01314ea28d102aeb6dac4f9f55bdecc966a3f02a7ab27` である。
実full監査authority、最終report、本計算のraw reader、独立計時の完了はまだ確認していない。

親環境も別版v4を構成し、既存parent wrapperに新readerを組み合わせた27テストが通った。
クラスタではsource 93・native 137・selector source 53を照合し、元runtimeの一致と保存済みstaged 3条件のmetadata互換性を確認した。
親環境記録は `data_tile_validation_2026-10-17/low_timing_parent_environment_v4/parent-environment.json`、SHA256は `0b19df715d970b03c92a806538753c17a13599c72fd3672f90d7222636ad326b` である。
全12条件の入力準備、資源確定、selector実行、独立計時、qsubはこの環境受入で行っていない。

仕様・source・試験ログ・旧失敗・両環境の86ファイルを `data_tile_validation_2026-10-17/planned8h_timing_reader_environment_acceptance_v1/manifest.json` に保存した。
manifest SHA256は `d7c6cdeb0461e438b35a0e75064d9252f9d849879680b6deac6df921658eabc3` である。
次はC3T1/C3T2の新最終出力から算術再確認と計時候補を作る係を接続し、全12条件の親準備と計時計画のbasisをv4環境へ整合させる。
現在稼働中の親準備・census待機係はv3環境のままであり、今回の環境作成だけで接続完了とは扱わない。
正式な低ノイズ検証完了数は8/12を維持し、C1T2の独立byte照合済み回収数は引き続き620/768群である。

## 06:18 JST：C3T1のPC待機を引継ぎ、C3T1/C3T2の最終投入経路を接続

[PC引継ぎ仕様](c3t1_pc_reconnection_spec_2026-10-22_ja.md)に従い、C3T1のlaboだけをC3T0の復旧serial記録へ接続した。
新待機係は元waiter・復旧serial・受入manifest・実intentを固定し、全5 batchと元の先行completion・transfer検証を維持する。
元serialと科学的設定・native reference・DGXの待機先・各条件の出力先は変更していない。
旧launcherの実PID28696・command・生成時刻、registry未取得、children空、childの起動記録と実processの不在を確認し、計算を持たない待機processだけを停止した。
停止の直前と直後に未起動状態を確認し、旧intent・観測履歴は保存した。
切替証跡は `data_tile_validation_2026-10-17/c3t1_pc_reconnection_transition_v1/stopped.json`、SHA256は `0e8ee4294669324196d56d7db28261e97733e82500ce7c81915a02cf89eba252` である。
新launcherはlaboだけの新待機先と新waiterを使い、元の子process所有、一度限りの起動、generator/native/PCの検証手順を維持する。
待機・launcherを合わせた49テストが通り、受入manifest SHA256は `645b8d6a0988975715c13aa011b6fd225fffe70a6d01bb0afe21dea6360821d1` である。
PID18780で新launcherを起動し、実process生存、registry未取得・child未起動を確認した。
実C3T1 registryとnative referenceがまだないため、それらを用いたlabo待機係の実起動受入は未実施である。

[最終接続仕様](planned8h_final_reconnection_spec_2026-10-22_ja.md)の続きとして、C3T1/C3T2の新audit intentと受入済みpreparerに対応する待機係を作成した。
旧準備係はintent・errorだけでremote準備未着手であることを確認し、旧記録を固定して別directoryに続行する。
新audit configのpath/hash、全入力・full監査・native reference、prepared responseの資源・root・qsub未実施の検証を保持した23テストが通った。
両条件の実sourceと実intentを読み込んでも準備へ進まず待機することを確認した。
受入記録は `data_tile_validation_2026-10-17/planned8h_final_handoff_acceptance_v1/manifest.json`、SHA256は `2f24d5e69365550600d20b56c2f8f0dca956cecdde139bbe1dc736e69c51c23b` である。

最終投入係は新待機係、既にクラスタで受入済みの8時間版native controls・qsub wrapper・回収器を固定した。
最終集計のrootとconfig rootを `20261022-planned8h-{condition}-final-v1` と対応するconfig側へ接続し、local出力には `planned8h_final_{condition}_*` を使う。
case 3のtarget 1/2、全67,584行、192 seed、元のqsub手順、共有lock、最大2ノード、12時間32 GBを維持する。
旧最終投入係はpreflight・submission未着手で停止していたことを照合した。
元の投入・待機・失敗処理の構文比較、実remote commandの境界、native回収transport、両条件の実bindingと待機を含む39テストが通った。
受入記録は `data_tile_validation_2026-10-17/planned8h_final_execution_acceptance_v1/manifest.json`、SHA256は `d9d6469e6d370de32a1bcfdc163994b454cd95acfac3df5fc510ac2b2be45f09` である。
最終driver SHA256は `7e647cc55891032eb91ab0a7bc5b9ad132819031213698bcff4e8e2298d3b7c8`、回収entryは `3f3fc76572d946af68f4f5e077709f35dd27513ff495648faeddd98e003def2d` である。

C3T1の準備PID39288・投入PID27028、C3T2の準備PID35588・投入PID23112の実process生存を確認した。
両条件とも入力待機中で、prepare・新規qsub・report回収は未実施である。
実観測は `data_tile_validation_2026-10-17/planned8h_reconnection_observation_20261022_v1.json`、SHA256は `f3f36c9cc5673ed54c774449ac3154e13c800d10a957a548aaa01ee6d608bd03` である。
クラスタは265421・265423の2件が各1ノードでRを維持し、低ノイズ検証の正式完了数は8/12のままである。

残る接続作業はplannedの8時間版に対応する計時reader・環境の実クラスタ受入と、C3T1/C3T2の新final出力先から算術再確認・計時候補・全12条件集約への接続である。
これらの未実施部分を最終投入係のテスト成功で代替しない。
公開操作、commit、pushはこの作業で実施していない。

## 06:09 JST：C3T0の後続経路を再接続、C1T2を620群まで回収

[再接続仕様](c3t0_pc_downstream_reconnection_spec_2026-10-22_ja.md)に従い、C3T0のcohort indexと転送係を復旧labo serialへ接続した。
元indexの全batch・assignment・archive検証を維持した14テスト、転送の17テストを確認し、転送係をPID43636で起動した。
旧係は失敗記録だけを残し、旧転送のshared回収・転送が未着手であることを照合した。
旧PID41120は観測時に別のssh processへ再利用されていたため、PID番号だけで旧係が生存しているとは判定せず、process名とcommand lineを照合した。
新転送係はlaboの保存parity入力回収を終え、DGX側と完全なindexを待っている。
転送係の受入記録は `data_tile_validation_2026-10-17/c3t0_distribution_recovery_acceptance_v1/manifest.json`、SHA256は `959d9f4099abf434af208475b7f467aa7563ffcabd0a760e388384360538e3f8` である。

停止した8時間版の最終準備・投入・算術係も、未実行の操作が重複しないことを確認して新しい記録directoryへ接続した。
最終準備は新distributionのsource・受入・intentを固定し、元のnative-tested preparer、remote config/job root、全入力・監査・reference検証を維持する。
新準備係と元の完了検証の22テストが通り、現在のC3T0実入力でremote準備へ進まず待機することを確認した。
元テストの過去C1T1/C1T2がpendingであるという2件は現状態に適用できないため除外し、C3T0の実入力試験を別に実行した。
準備係の受入manifest SHA256は `cec018e41acd65d7083b286bbbc7f310199eee8ee07536bf39861d7e23100e9a` である。

投入係は新準備係に接続し、元のqsub lifecycle・最大2ノード・12時間32 GB・native回収器を保持した。
接続5テストと元の投入手順24テストが通り、受入manifest SHA256は `3623936aa46dddbcae3dbea2ea3e2adf7e4a176b78add6f4c0fffac8ad9b5d24` である。
最初の一括test呼出しは元テストのmodule探索方法と合わずcollection errorとなったため、そのログを保存し、各テスト群を元の方法で個別に実行した。
最終算術確認と計時候補作成も、新投入係・新準備係・新distribution完了先へ接続した。
全行の算術確認、snapshot、入力改変拒否、転送、candidate検証を維持した30テストが通り、受入manifest SHA256は `421ec2f33d4f69ae3df9451df1ab8ea6da45f7e02815bb75f5976f36c66d5009` である。
旧source・intent・errorは保存し、計算条件・final回収先・計時環境・candidate出力先は変えていない。

実process観測ではlabo serial PID47168、index PID49492、転送 PID43636、最終準備 PID17032、最終投入 PID42456、算術・候補作成 PID20500が生存していた。
最終準備・投入・算術係は入力待機中であり、C3T0の最終qsub・report受入・candidate作成は未実施である。
laboのC3T0 batch0はparity・stageを終え、remote実PID10356が生存しcompletionは未作成である。
この実観測は `data_tile_validation_2026-10-17/c3t0_downstream_reconnection_observation_20261022_v1.json`、SHA256は `79dc9330465e57c504dc10b920651b6a23e7682caa4ff6516c97194b0ad0cd44` に保存した。

C1T2のDGX batch24は実PID終了とcompletionを確認し、全ZIP・96 member・固定assignment・source・receipt・転送記録を独立照合した。
回収数は620/768群・54,560行となり、追加1,760行のflagged・undefinedは各1,760、区間未取得は0である。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v25.json`、SHA256は `17e02c75058a00c74240e64632e6c2659f91f844530264594e7be65587bd0006` である。
低ノイズ条件の正式完了は8/12のままであり、620群の回収を条件全体の科学的受入とは扱わない。
クラスタ265421・265423は各1ノードでRを確認した。

次の作業はC3T1のlabo待機先を復旧serialへ接続すること、C3T1/C3T2の受入済み8時間版preparerを最終投入・回収係へ接続すること、およびplanned条件の計時readerを同じ8時間経路へ接続することである。
C3T1の現launcherはregistry未取得・children空で待機しており、この後続接続はまだ実施していない。
公開準備の完了と公開操作の未実施を維持し、公開・commit・pushはこの作業で行っていない。

## 05:54 JST：最終8時間経路のcontrolsとpreparerを受入、labo入力回収を復旧

[最終接続仕様](planned8h_final_reconnection_spec_2026-10-22_ja.md)に従い、最終CLIは検証済みの元workerとCRLF版workerの2 hashだけを受け入れるようにした。
未知のworkerをconfig側のhash変更だけで受け入れない試験を含め、Windowsで144 passed・11 skipped、クラスタでreader 68・qsub protocol 33・回収器54 passedを確認した。
元版でCRLF workerを拒否する1 failed・2 passedと、中間版の回収器再生成先不一致のログも保存した。
新しいwrapper・回収器のhashと配置先を固定し、クラスタの別directoryで22 helper・113 native source・75 import sourceとC3T1・C3T2の実audit configを確認した。
新preparerは対象をC3T1・C3T2に限定し、固定の科学的条件・元の転送先を維持しながら、新audit config・root・native controlsと別のfinal config/job rootを使う。
Windows・クラスタで各37 passedを確認し、実venv bootstrapと未作成のfinal config/job rootを照合した。
実full入力・監査authority・reportの完走は未確認で、新preparer用のwaiterと最終投入係もまだ接続していない。
74ファイルの受入記録は `data_tile_validation_2026-10-17/planned8h_final_reconnection_acceptance_v1/manifest.json`、SHA256は `67b7232c2b7e072fce5ad8dea9c58c4210d46d5488c79d46ec62d2bad5f18e33` である。

C1T2はDGX batch23とlabo batch4の実completion、転送記録、ZIP全体と全member hashを照合し、600/768群・52,800行まで回収した。
追加44群・3,872行のflagged・undefinedは各3,872、区間未取得は0であり、混合や被覆の保証ではない。
観測記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v24.json`、SHA256は `b8ec7f8f0b3ec18c5fc64b4db210b5282d8125661511f1d2697f3f7f81f01b39` である。
最初の追加照合はDGXだけを指定したため、同時に回収されていたlabo分との全集合一致で停止し、両batchを指定して検証した。
DGX batch24は実PID4043950の生存・completion不在を確認した。

laboはC1T2終了後にC3T0 batch0の入力exportへ進んだが、ローカルのSSH待機300秒を超え、serialと後続のdistribution・final準備・final投入・最終算術確認係が停止していた。
クラスタ側を実観測するとexport processは既に存在せず、ZIP・receipt・sampling-terminalが完成していた。
現在の3件のgenerator PBS終端、保存終端、固定source/input、ZIP全体hashとサイズを読み取り専用で照合した。
[復旧仕様](c3t0_labo_export_reconciliation_spec_2026-10-22_ja.md)に従い、exportを再実行せず、64,499,575 byte・5,949 member・24群の完成済みarchiveを転送し、元exportの全検証を維持してprepared_inputを作成した。
対象外の拒否と元検証の保持を含む15 passed、続行係の8 passedを確認した。

旧serialのexport以外が未着手であることと重複processがないことを確認し、新serialをPID47168で起動した。
固定全5 batchのtask順・parity・stage・launch・回収を維持し、batch0の完成済みexportを再利用する。
今後のC3T0 labo batch1〜4のexportではSSH keepaliveを維持してローカル300秒待機期限だけを外し、自動再試行はしない。
新serialはlaboへのprepositionを完了し、05:54時点でparity用SSHのPID40236が生存している。
parity完了と通常batch計算開始はまだ未確認である。
35ファイルの受入記録は `data_tile_validation_2026-10-17/c3t0_labo_export_reconciliation_acceptance_v1/manifest.json`、SHA256は `fb3d6aa2da216630de8c5be0ac9a3356c325543b476e950e498ace1fc223cd8a` である。
C3T0の停止したcohort/distribution/final各係と、次条件のlabo待機係を新serialの記録へ再接続する作業が残る。
旧失敗記録は保持し、成功や科学的完了として読み替えていない。
クラスタの265421・265423は各1ノードでRであり、低ノイズ完了数は8/12を維持する。

## 05:41 JST：C3T2の初回8時間回収と監査待機を接続

[C3T2の仕様](c3t2_first_collection8h_spec_2026-10-22_ja.md)に従い、対象をcase 3・target 2だけに制限した8時間・1 CPU・32 GBの回収処理を作成した。
旧回収・retry・4時間版のdirectoryがある場合は拒否し、元の768群・192 seedの全task検証とsampling sourceを維持する。
旧C3T1 scopeのままでは2 failed・7 passedとなることを確認し、C3T2への制限後、Windowsとクラスタで回収60 passed・監査54 passedを確認した。
中間版のsource pin拒否のログも保存し、派生後のbackend hashへ固定して試験した。
実クラスタでC3T2のconfig bootstrap、回収の未開始、監査rootの不在を確認した。
この確認でqsub・実回収・実trace監査は行っていない。

新しい監査係は復旧したC3T2 generationとC3T1の8時間版full監査のsource・intentを固定する。
接続20 passedと元lifecycleの25 passedを確認した。
旧監査係は先行監査失敗で終了し、collector・capacity・fullの操作記録がなく、旧PID32224が存在しないことを実観測した。
新監査係をPID752で起動し、registry待機・errorなしを確認した。
新source SHA256は `417925b6549ecce191796d2b0db06162c1c9ed9feb05298b2f46fe1bb8558bd4` である。
generator receiptが揃った後も実sampling終端と先行full監査を照合し、共有lock・最大2ノード検査を経てqsubする。
元の一度限りの操作、capacityからfullへの資源推定、実PBS終端照合は維持した。
49ファイルの受入記録は `data_tile_validation_2026-10-17/c3t2_collection8h_acceptance_v1/manifest.json`、SHA256は `693e4ee206f31340448fad38d99e27db7fa873a9a6507206891b401f23d619e3` である。

低ノイズ完了数は8/12のままで、C3T1・C3T2の最終preparer、final controls、最終実行係、計時readerの8時間経路への接続は未完了である。
最終接続ではaudit rootだけでなく、native controls・audit config・workerの固定hashと実bootstrapを一緒に検証する必要がある。
C3T2の派生workerはCRLF化だけで元workerとbyte hashが異なることを比較確認したため、旧final CLIの単一worker hashでは受理されない。
稼働中の係が固定したsourceを変更せず、次のfinal controlsでこの検証済みworkerを明示的に扱う必要がある。

## 05:36 JST：全12条件の親準備と計時計画の基礎設定を復旧環境へ接続

[接続仕様](low_timing_parent_reconnection_spec_2026-10-22_ja.md)に従い、親環境v3を作成し、実クラスタで93 source・137 native binaryと既存staged 3条件の互換性を確認した。
親環境SHA256は `126bdf1b4e0ff0ba80c8af61e723ee6aba9a5ad707c60ab8b5ac85cb9dfd87ae` である。
親準備v2とassembly v2は全12条件のgate、条件順、candidateごとの固定環境、既存の資源上限を維持し、引継ぎを含む37 passedを確認した。
8条件の実inventoryでは入力準備もqsubも実行しないことを確認した。

後続のcensus準備の環境参照だけを更新した中間版では、basis内の旧親環境との不一致が残ると確認した。
中間版はselector待機中で、prepareとqsubは実施していない。
元preflightを新親環境で再実行し、既存56 namespace・3,963,562割当の保存済み監査との対応、12 sourceの移設対応、61 source・28 core sourceのbindingを確認した。
seed列の再生成や新namespaceの監査は行っていない。
新basisは `data_tile_validation_2026-10-17/low_timing_census_preflight_v2/collected/basis.json`、SHA256は `0fdeae516d394f8c544276fa02d30f41b4150f3355a2eebd9118ddf7450bd11a` である。
このbasisを使うcensus準備v3は、実設定の親環境・runtime・source binding一致と旧科学的baselineの不変性を含む19 passedを確認した。
最初の実設定試験はsymlinkの解決前後のpathを同一視して1 failed・18 passedとなり、実環境に保存されたresolved_sourcesで比較して修正した。

旧waiterの実PID・command・pending状態・未投入の出力先を確認し、既存のintentと観測履歴を残して引き継いだ。
新規sourceと旧履歴のhashをhandoverに固定し、排他的claimで二重起動を拒否する。
最初の停止確認では終了済みPIDへのWait-Processが非零を返し、実PID消失を再確認して継続した。
親の起動後には起動用processがpipe回収待ちとなったため、新waiterの生存を確認して起動用processだけを停止し、重複起動は行っていない。
censusの次の引継ぎでは子process検査がconhostを検出して停止したが、Windowsのconsole hostだけであることを照合して継続した。
これらの履歴と中間版の記録も保存している。

05:35以降の実process観測では親準備v2のPID45160、census準備v3のPID49100が待機中であり、既存のselector投入係PID47428とcensus投入係PID8588も生存している。
canonicalなaccepted・completed・errorの出力先を維持しているため、後続係のsourceは変更していない。
受入記録は `data_tile_validation_2026-10-17/low_timing_parent_reconnection_acceptance_v1/manifest.json`、77ファイルのmanifest SHA256は `56fedbe626717eca7bec85e079ed5cc228363b2bfce12ea443655342d034e511` である。
クラスタでは265421と265423の2ジョブが各1ノードでRであり、この引継ぎによるqsubと科学計算の停止はない。
低ノイズ条件は8/12完了のままで、全12条件の入力準備、raw readerの完走、独立計時、最終報告は未完了である。
C3T1・C3T2の8時間回収経路に対する下流接続とreaderの対応も別途残る。

## 05:20 JST：C3T0の実読み取り環境と下流待機係を接続

[環境と下流接続の仕様](c3t0_recovery_timing_environment_spec_2026-10-22_ja.md)に従い、新しいhelpers directoryに検証済みreaderとC3T0用snapshot validatorを配置した。
実クラスタの別processで100 source・137 native binaryのbindingとbootstrapを確認した。
環境のSHA256は `b5155f23fec6de658600dca19dbb7ed7877426fe121da0cb1642a2bc95274aab`、環境受入は `data_tile_validation_2026-10-17/c3t0_recovery_timing_environment_v1/accepted.json` に保存した。
full監査は未完了なので、そのauthorityの検証・raw reader・production final configの検証は未実施とreceiptに明記した。

C3T0だけを対象とするadapterで元candidateの全検証を再利用し、kind・final root・audit root・snapshot validator・読み取り環境を復旧版へ接続した。
元の算術readinessの転送・receipt・report照合を維持し、prepared-inputと固定preparer完了記録のhash・内容、およびreceiptのconfig hashの一致も要求する。
既存の失敗記録と実行中のfinal係は変更していない。
29 passed・1.20秒を確認し、未完了で待機すること、異なるconfig・root・転送・jobの拒否、両結果が揃うまで完了を書かないこと、一度しか実行しないことを検証した。
20ファイルの受入manifestは `data_tile_validation_2026-10-17/c3t0_recovery_final_downstream_acceptance_v1/manifest.json`、SHA256は `1eb817d436fb7137d0111bd39d061fd6c1b8fdc4ca1206a01753230086d0e4eb` である。
新待機係PID45396の生存と、回収未完了・errorなしを05:20に実観測した。
成功した回収後に元の全行算術確認とmetadata candidate作成を並行して一度だけ実行するが、この係はqsubしない。
全12条件の親への新環境接続と実計時は未完了で、低ノイズ条件の完了数は8/12を維持する。

## 05:14 JST：C3T0復旧を計時readerで扱う別版を受入

[reader拡張仕様](c3t0_recovery_timing_reader_spec_2026-10-22_ja.md)に沿って、復旧をC1T0だけに限定していた計時readerを別版へ拡張した。
case 3・target 0・recoveryについて、C3T0用snapshot validatorの固定source hash、retry8hの成功collector、budget4hの旧時間切れcollectorを要求する。
成功側は8時間・exit 0・run_count 1、旧失敗側は4時間・exit -29・run_count 1で、元guardと実PBS終端を照合する。
その他の既存条件の契約を保ち、既存reader13 moduleのうち変更はcondition readerとfinal metadata readerの2 moduleだけである。
元sourceは全てhash不変を確認した。

旧metadataの受入不能を1 failed・6 passedで確認した。
最初のderivationは式の出現数検査で停止し、その中間版で9 failed・107 passedとなったログも保持した。
式の位置を明示して修正後、対象試験154 passed、さらにWindows・Linuxの各313 passedを確認した。
内訳はreader 93、dispatch 68、parent 26、metadata 126である。
合成fixtureでの数値集計・元履歴・source pin・資源・別条件拒否の検証であり、実C3T0 reportの読み取り成功ではない。
native受入は `data_tile_validation_2026-10-17/c3t0_recovery_timing_reader_native_v1/accepted.json`、SHA256は `dac967d681eefd68ac059e6d70ce280ed7287314911d5bfac9e204184c942c14` である。
仕様・RED・元sourceの不変性を結ぶmanifestは `data_tile_validation_2026-10-17/c3t0_recovery_timing_reader_acceptance_v1/manifest.json`、SHA256は `e1e156823f775329d6ca4da549bf5731339f5351d1980ddecf5e5bac8235abaa` である。
実native環境の準備、C3T0 candidateと算術確認の待機係、全12条件parentへの接続は未完了である。

DGX batch23の実PID3987700の生存とcompletion不在を確認した。
05:13のqstatでは265421と265423が各1ノードでRであり、PC回収556/768群・低ノイズ条件8/12完了は維持する。

## 05:07 JST：C1T2のPC回収が556/768群へ進行

DGX batch22の実completion `1ca90e32ced44fd1d4eb6e03b988c51a4237661e147d6589237a459fb1382b56` とprocess終了を確認し、既存serial driverが回収した転送物を照合した。
新しい20群・1,760行のassignment・receipt・転送記録・source pin・ZIP全体・96 member payloadのhashを確認し、既回収群との重複がないことを検証した。
回収済みは556/768群・48,928行となった。
追加行のflagged・undefinedは各1,760、区間未取得は0であり、良好な混合や被覆を保証するものではない。
観測記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v23.json`、SHA256は `30a4e87939778b9bc8755b1c3877ee727e153c47a31bf8fd029a46c50ac4ca96` である。
DGX batch23の入力export process PID43416とserial driver PID46624の生存、labo batch4の実PID12628の生存・completion不在を確認した。
batch23の数値処理開始やC1T2全体の科学的受入はまだ確認していない。

## 05:06 JST：C3T2 generationとnative・PC起動待機を再接続

[再接続仕様](c3t2_generation_reconnection_spec_2026-10-22_ja.md)に従い、先行C3T1監査の失敗で投入前に停止したC3T2 generationを別版で再接続した。
クラスタ上のanchor 0・sample 0・sample 1についてsubmission-intent・submission・terminalの不在を確認し、qstatの自分の実行中ジョブにもC3T2がないことを確認した。
旧PIDの消失と、旧generationがintent・errorだけを残したこと、旧native・PC起動係が子processを開始していないことを照合した。
新generationはC3T1の8時間版に続くfull監査と既定native referenceの実成功終端を待ち、元の固定preflight・payload・qsub helper・投入順・最大2ノード検査を維持する。
新generationの16 passed、native・PC起動係と元launcherの29 passedを確認した。
新generationはPID44108、新native・PC起動係はPID29256で実processの生存を確認した。
後者はregistry未取得・children空・errorなしであり、この再接続によるC3T2のqsubは未実施である。
27ファイルの受入manifestは `data_tile_validation_2026-10-17/c3t2_generation_recovery_acceptance_v1/manifest.json`、SHA256は `3f2e45ab8a85f3e0b9e42ad6f9c133511f57a252d7431ebd9c9c7fc3dcc9e70a` である。
新generation source SHA256は `805e6146a337b23e692bc3379fceecc1c3bfac40b96007582a753cfeaa2d44b4` である。
C3T2の回収・監査係と各条件の最終集計後の接続は別途残っており、低ノイズ完了数は8/12を維持する。

## 05:02 JST：C3T1初回回収8時間版と監査待機係を接続

[小仕様と受入方針](c3t1_first_collection8h_spec_2026-10-22_ja.md)に従い、未投入のC3T1回収を8時間・1 CPU・32 GBとする別版を作成した。
対象はcase 3・target 1に限定し、旧回収・retry・4時間版のdirectoryがあれば初回実行として受理しない。
旧版に対する契約試験は6 failed・3 passedで、新版はWindowsとクラスタで回収器の60 passedを確認した。
監査はWindowsの53 passed後、4時間terminal拒否を加えたauthorityの16 passedを確認し、クラスタで全54 passedを確認した。
768群・192 seedの失敗taskを含む完全なindex照合、元の科学計算と資源推定、共有lock・qsub・最大2ノードの検査を維持する。
実C3T1 configのbootstrapと新回収・監査の未実行状態をクラスタで確認したが、実trace監査や条件完了を意味しない。

新しい実行係はC3T1の新generationとC3T0の復旧full監査を参照し、20 passedと元lifecycleの25 passedを確認した。
最初の合併pytestはimport modeによるdriver importエラーで停止しており、そのログを保持した上で別processで検証した。
51ファイルの受入manifestは `data_tile_validation_2026-10-17/c3t1_collection8h_acceptance_v1/manifest.json`、SHA256は `6dc288db44aee9fb431ec79ff6ba639c87c3b79e75346d1f704f8923ba71bede` である。
旧係のPID43488の消失と、回収・監査の投入前に失敗した記録を確認し、新係をPID44832で起動した。
新source SHA256は `90307b01b42a00a5b8c5cb5744e4a3b8a27029fb369b2ffacefce4ca93d2a4a2` である。
05:02の実process観測ではregistry待機中・errorなしで、C3T1回収のqsubはまだ実施していない。
実sampling終端、先行full監査、空きノードを確認してから投入する。
05:01のqstatでは265421と265423が各1ノードでRであり、低ノイズ検証の完了数は8/12のままである。

## 04:52 JST：C3T0復旧finalのqsub・回収係を接続

[実行・回収仕様](c3t0_recovery8h_final_execution_spec_2026-10-22_ja.md)に従い、C3T0用の回収器と最終実行係を別版で接続した。
回収器は元の復旧版から対象caseを3に変更し、target 0・p=0.01・67,584行・192 seed・352設定を維持した。
別条件への拒否試験では、reportを書き換えた際のchecksum不一致だけで通過しないよう、completion・terminalのhashも整えたfixtureでcase 1の拒否を確認した。
旧scopeでは2件の試験が失敗することを保存し、変更後はWindows 37 passed・8 POSIX専用skip・2.67秒、Linux 45 passed・1.91秒だった。
Linuxでは実wrapperへのmetadata接続を合成fixtureで確認しており、実C3T0 report回収の成功とは区別する。
回収器受入は `data_tile_validation_2026-10-17/c3t0_recovery8h_final_collection_acceptance_v1/accepted.json`、SHA256は `f57103bea752db22ff8f978f213994c09759403d6f55a9bce0b688bb56479335` である。
同directoryのmanifest SHA256は `e2b72909dc1c5696cc670a0836765c64cc75c840985bbdac95689f6db4f0f421` である。
初回のfixture derivation import衝突による1件の失敗も保存し、元sourceからの明示2差分のbyte照合へ修正した。

最終実行係は元の一回限りのqsub lifecycleを再利用し、新しい準備・job root・成果物回収先と単一thread環境を固定した。
新規4 tests passed・0.91秒、既存lifecycleの24 passed・0.74秒を確認した。
14ファイルの受入manifestは `data_tile_validation_2026-10-17/c3t0_recovery8h_final_execution_acceptance_v1/manifest.json`、SHA256は `1fc0819ed8495451b1affc2da9afae692a1ce426c2928101aa44fe94941bfac6` である。
旧実行PIDの消失を確認し、失敗記録を残して新local実行係をPID6048で起動した。
04:52の実観測は準備未完了の待機であり、新しい最終集計qsub・最終report回収は未実施である。
準備完了後も実qsub前の最大2ノード検査、固定preflight、実成功終端、13成果物の転送前後照合を経る。
回収後の独立算術確認と全12条件の計時candidateへの接続は残っている。

C1T2 DGX batch22は実PID3978062の生存と固定config `ae68596886bc4c8606944c8156ccba6d7be40c0b89d54a161202eef6f50af9cc` を確認した。
完了はまだ観測されておらず、回収済み536/768群と科学的検証作業8/12条件は維持する。

## 04:46 JST：C3T0復旧final準備を実native環境で確認

[復旧final準備仕様](c3t0_recovery8h_final_preparation_spec_2026-10-22_ja.md)に従い、実績のある復旧preparerをC3T0の新full監査に接続する別版を用意した。
科学計算・qsub adapterは維持し、5つの明示式と固定条件・root・native terminalを変更した。
case 3・target 0・production manifest・8時間復旧監査config・38 batch・native referenceのhashを照合する。
Windowsは30 passed・0.93秒、Linuxは30 passed・0.10秒だった。
クラスタの実Pythonで135ソースと新監査configのbootstrapを確認し、最終config・job rootをまだ作成していないことも確認した。
受入記録は `data_tile_validation_2026-10-17/c3t0_recovery8h_final_preparation_acceptance_v1/accepted.json`、SHA256は `bb7d12a7710870b04cd19257ef4771022c6aa37a7bbcbd153888abc0ef3e4126` である。
同directoryのmanifest SHA256は `343cf89cf2bb4afe9bde5bf71dfa6006faaee7833a79775f4bcba86e8887d432` である。

旧final準備の失敗を保持し、新監査・全PC転送・native referenceを待つlocal waiterをPID18816で起動した。
待機・受理処理の試験は22 passed・1.30秒で、新C3T0の実入力に対する未準備判定も確認した。
初回のpytest同名module衝突と、旧テストがC1T1未完了を仮定したことによる1件の失敗も保存した。
旧条件の状態に依存する2ケースを分け、C3T0用の実入力確認と他の共通受入を実行したもので、元suite全件成功とは扱わない。
13ファイルの受入manifestは `data_tile_validation_2026-10-17/c3t0_recovery8h_final_waiter_acceptance_v1/manifest.json`、SHA256は `38e30bdc7f7e1b3bf4001bbd93444eabb69c97214229ee4b0295771b5bf08aee` である。

実full監査と全転送が揃った後に12時間・1 CPU・32 GBの最終集計をpreflightまで準備するが、このwaiterはqsubしない。
最終集計の実行・回収係の接続は未完了である。
既存復旧collectorの回収器はcase 1・target 0を固定しているため、C3T0用に明示scopeを変更した別版と受入が必要である。
最終config作成・BAR最終集計・科学的受入はまだ完了しておらず、低ノイズ完了数は8/12のままである。

## 04:39 JST：C3T1 sample 0開始・PC起動係再接続・C1T2回収536群

C3T1 anchor265422は04:36:30にF・exit 0・run_count 1で終了し、walltimeは2分35秒だった。
新生成driverがその実終端を確認し、sample partition 0をqsubで265423として投入した。
04:38のqstatでは265421の復旧回収と265423のsamplingがともにRで、要求ノード数は合計2を維持した。
sample 1は新C3T0復旧full監査の完了待ちであり、未投入である。

C3T0のnative・PC起動係、PC待機、indexとdistributionの実プロセスは生存しており、再起動していない。
旧C3T1のnative・PC起動係はchildrenなしで失敗し、旧PID42248も存在しなかった。
[再接続仕様](c3t1_downstream_recovery_spec_2026-10-22_ja.md)に従い、元sourceを変更せず新生成記録を参照する別の起動係を用意した。
関連29 tests passed・1.11秒を確認し、新PID28696を起動した。
実観測はregistry未完成・childrenなしの待機であり、native referenceやPC数値計算を新たに開始したとは扱わない。
11ファイルのsnapshotは `data_tile_validation_2026-10-17/c3t1_downstream_recovery_acceptance_v1/manifest.json`、SHA256は `e1faf109a9d60400fc52a25f2b3ac46d2792a7f59bdd50a9ee39e4b9de3cecee` である。

C1T2 DGX batch21の正常終端、回収receiptと転送検証を照合し、全ZIPと96 member payloadを再hashした。
C1T2の回収は536/768群・47,168行で、追加1,760行の診断flag・未定義項目を保持し、区間未取得は0だった。
記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v22.json`、SHA256は `14901146178ee5820fe6ab5b7a97ada6c4a283cd0f5ee2a887c81417d906a1c9` である。
DGXの次batch22は入力export処理中で、local serial PID46624とexport PID15396の生存を確認した。
batch22の数値計算開始はこの観測時点では未確認であり、launch記録がまだないことを失敗とは扱わない。
Laboのserial PID25116も生存していた。

C3T0の旧final準備・実行係は監査失敗に伴って停止しており、新8時間復旧監査への接続が残る。
C3T1 collection監査の新生成証跡への接続、後続finalとC3T2への接続も未完了である。
低ノイズの科学的検証作業の完了数は8/12条件のままである。

## 04:35 JST：C3T1生成を復旧回収と並行して開始

旧C3T1生成driverは先行collectorの失敗を検出し、投入前に停止していた。
旧error・intentを保持したまま、[並行生成の仕様](c3t1_parallel_generation_spec_2026-10-22_ja.md)と受入テストに従って別driverへ接続した。
C3T1の3 partitionの固定preflight・source・seed・入力・資源・qsub helperは変更していない。
新規12件・1.18秒、再利用する生成driverとqsub処理の43件・3.18秒のテストが成功した。
受入22ファイルのsnapshotは `data_tile_validation_2026-10-17/c3t1_parallel_generation_acceptance_v1/manifest.json`、SHA256は `cc539bdd9f7951ddbf1d79016a24a8a3ea698aef6c148012905e2de40b5245d1` である。

C3T0の3 generatorとnative referenceについて固定receiptと実qstatの正常終端を確認し、C3T1 anchorをqsubで投入した。
実jobは265422で、投入receiptのSHA256は `2f8b9ad305012c9b8ed64847cb4e8cd9f791ff0ae97d353122b377222f4c556b` である。
実qstatでは265421と265422がともにR、所有jobの要求ノード数は合計2だった。
観測は `data_tile_validation_2026-10-17/c3t1_parallel_start_observation_20261022_v1.json`、SHA256は `1afd032d5e05ac4ea8e781c0df073fe54b0e66973b61d75de0390f30f8631700` に保存した。
新local生成driverのPID7552と、復旧監査driverのPID24324の生存も確認した。

anchorの実成功終端後にsample 0を投入し、sample 1は新C3T0復旧full監査の実成功終端・completeを確認してから投入する。
この順序変更はC3T0の監査結果をC3T1の科学入力に使うものではなく、回収と生成の並行化である。
両sampling投入後のregistry作成、C3T1の後続collection・PC・finalの新生成証跡への接続、C3T0のfinal/計時接続は未完了である。
低ノイズの科学的検証作業の完了数は8/12を維持する。

## 04:28 JST：C3T0回収を8時間枠で復旧投入

旧collector265419は04:18:14にF・exit -29・run_count 1・walltime 4:01:21となり、旧成果物12ファイルのhashと終端を `data_tile_validation_2026-10-17/c3t0_collector_timeout_20261022_v1/` に保存した。
旧driverの失敗記録は保持し、成功へ置き換えていない。
受入済みの別版で実preflightを通し、qsubで新job265421を投入した。
新jobは04:25:07開始、04:28の照会ではR・walltime 0:03:16・CPU 0:03:14で、1ノード・1 CPU・32 GB・8時間上限である。
8時間は要求上限であり終了予測ではない。
固定configのSHA256は `77f05d6d940cb9a602a40e9db60e29f4732d5c4640516e5ba10894d936fbd659`、実投入記録は `data_tile_validation_2026-10-17/c3t0_collection8h_execution_v1/submitted.json` にある。
全samplingの再生成は行わず、保存済みデータの回収・検査を別出力先でやり直す。

後続監査config `81beb3383044076259fb9a4831330edfd49fd1885e8a6e3c0fdd1a20853cd83c` を別rootに配置し、native workerのconfig・source・root照合を通した。
[別の引継ぎ仕様](c3t0_recovery8h_handoff_spec_2026-10-22_ja.md)に従うlocal driverは48 tests passed・0.78秒で、実265421の正常終端を待ってからcapacity/full監査へ進む。
新driverのPID24324の生存と265421の実R観測を確認した。
この受入と実投入の24ファイルsnapshotは `data_tile_validation_2026-10-17/c3t0_recovery8h_handoff_acceptance_v1/manifest.json`、SHA256は `4947f6757db3a689e6a5ead96325c5e600237f07eac3cf1ab4b41435ff37a3a8` である。
回収・監査の本番完了、BARの最終集計・計時への接続、旧C3T1生成driverの失敗を保持した後続接続は未完了である。
低ノイズの科学的検証作業は8/12条件のままである。

## 04:10 JST：C1T2回収516/768群

DGX batch20の実PID3912281の終了と固定configに対応するcompletionを確認し、既存driverの転送検証後にZIP全体と全96 member payloadを再hashした。
固定割当・metadata・重複なしの照合を通り、C1T2回収は516/768群・45,408行となった。
追加1,760行の診断flag・未定義項目をすべて保持し、区間未取得は0行である。
記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v21.json`、SHA256は `5d9003a871cf86183002e5e2fb8f1ded9aec52617689879bbf4c5f200cb156ac` である。
これは回収・構造・byte照合であり、C1T2の科学的受入は未完了である。
04:07のqstatではcollector265419はR・walltime 3:49:08で、監視driver98953の稼働も確認した。
低ノイズ検証作業の完了数は8/12条件を維持する。

## 04:06 JST：条件付きcontrolsの配置確認

受入済みcollector controlsをクラスタの `20261022-c3t0-collection8h-recovery-v1`、trace controlsを `20261022-c3t0-recovery8h-trace-v1` へ別配置した。
8ファイルの転送前後のhashと、元bundle Pythonでのimport、case 3・target 0のみの受理、1 CPU・32 GB・8時間の資源値、trace backendが固定するcollector hashを確認した。
配置の[accepted記録](data_tile_validation_2026-10-17/c3t0_conditional_controls_stage_v1/accepted.json)のSHA256は `b43126d68c26b5e47a7d74b50aa4ca10dd806e9f2d5b7d1f65f0c0865ef953e1` である。
再現用配置script・remote program・応答も同directoryに保存した。
これはsource配置の確認であり、旧jobの確定失敗guard・復旧context・実preflight・qsub・復旧完了authorityは未作成である。
元265419は04:05の照会でR・walltime 3:47:08・CPU time 3:32:09であり、現job・driver・既存sourceは変更していない。

## 04:03 JST：条件付き復旧trace controlsの受入

[8時間collectorから監査への受理仕様](c3t0_recovery_trace_contingency_2026-10-22_ja.md)に従い、別版のauthorityとbackendを用意した。
変更は新collectorの8時間要求の検査と、受入済みcollector adapterのsource hashの固定であり、qsub/workerのbyte列と科学計算は維持した。
Windowsは47 passed・24.34秒、Linuxは47 passed・12.49秒だった。
旧authorityでの2件の拒否、旧adapter hashが残る統合試験の2件の拒否、Linux初回のfixture転送漏れによる停止も保存した。
[40ファイルのsnapshot](data_tile_validation_2026-10-17/recovery_4h_timeout_trace_acceptance_v1/manifest.json)のmanifest SHA256は `5a3680f3282db089ba200621bdb42908d0d581831f671477eec7b6eca04851d1` である。
実旧jobの終端、復旧contextとcollector、新監査config、次条件の引継ぎ、最終report/計時への実接続は未完了である。
現job・既存driverは変更せず、これらの合成fixture受入を復旧済みとは扱わない。

## 条件付き復旧で残る後続接続

既存の復旧trace authorityは新collectorの上限を4時間と明示検査しているため、準備した8時間collectorをそのまま受理できない。
既存handoffもC1T0のconfig・scriptに固定されており、C3T0への置換は別版の受入が必要である。
待機中のC3T1生成driverは元C3T0監査の完了と固定投入先を要求するため、復旧時は旧失敗を保持した新しい引継ぎも必要となる。
読み取り確認の対象sourceとhash、適用範囲は `data_tile_validation_2026-10-17/c3t0_recovery_downstream_review_20261022_v1.json` に保存した。
準備済み51件の受入を、これらの実接続や復旧全体の完了とは扱わない。

## 03:55 JST：C3T0の条件付き復旧controlsを準備

collector265419はqstatでR・walltime 3:37:06・1要求nodeを維持しており、失敗は確定していない。
4時間上限で確定時間切れとなった場合に備え、[別版の復旧仕様と受入](c3t0_collection_timeout_contingency_2026-10-22_ja.md)を用意した。
旧成果物をその場で保持し、全taskの検査を別出力先で行う1 CPU・32 GB・8時間上限のcontrolsであり、case 3・target 0以外を拒否する。
WindowsとLinuxの合成fixtureは各51件成功し、source・赤/緑ログ・実行環境・仕様を[24ファイルのsnapshot](data_tile_validation_2026-10-17/collection_4h_timeout_recovery_acceptance_v1/manifest.json)に保存した。
manifest SHA256は `c18cd6755ed844b018852eeb34c63440b65e455604ccb85c313ebb5b359e7fea` である。
これは実旧jobの失敗受理、実preflight、復旧qsub、後続controllerへの接続が完了したという意味ではない。
元job・既存driver・科学計算は変更しておらず、成功終了すればこの復旧は使用しない。
DGX・Laboの既存serial driverも実プロセスの生存を確認した。

## 03:45 JST：collector実プロセスと計算ノードの時計差

手元の既存SSH鍵とcluster経由のProxyJumpを用い、node008上のcollector PID759266を確認した。
対象rootとcollect actionに対応する実プロセスはRで、5秒間にCPU tickが451増加し、clock tick毎秒100に対して約4.51秒のCPU実行があった。
同区間のscheduler実行待ち時間の増分は411,417 nsであり、この短い区間ではCPU待ちが主因とは確認できない。
記録は `data_tile_validation_2026-10-17/c3t0_collector_process_observation_20261022_v1.json` に保存し、Python内の実行位置や将来の終了時刻の確認とは区別する。

ログインノードと計算ノードで同じ中間ファイルを同時照会したところ、inode 55240827735・サイズ13,628,938 byteは一致した。
計算ノードが返す時刻はlocal照会の開始・終了時刻に対して約957〜959秒進んでいた一方、ログインノードの時刻はlocal照会区間内だった。
この時計差の原因は未調査であり、時計設定は変更していない。
別hostの絶対時刻を差し引いて計算時間やETAを求めず、回収中ファイルの可視行数も正確な実行位置とは扱わない。
対応記録は `data_tile_validation_2026-10-17/c3t0_collector_file_views_20261022_v1.json`、SHA256は `bbff6b7aed556ae04e5a25496396380a2ac25c887a943dee801a3cfecd2f131e` である。
ローカルの `cluster_scripts/tile_low_noise_timing_execution.py` はtask・inclusive・pool・executionの経過時間を同一process内の `time.perf_counter()` の差で計測していることを確認した。
このsource確認は、未実施の独立計時や全環境の時刻監査が完了したことを意味しない。

DGX batch20はPID3912281の生存を確認し、completionは未作成だった。
config hashは `d88fc8dd0040a14b0fbfb1d0344b3c8b4dbe35114f9203e31797936b45b0a2fd` で、C1T2回収済み群数は496/768を維持する。

## 03:42 JST：C1T2回収496/768群と空き容量

DGX batch19の実PID3902275の終了と固定configに対応するcompletionを確認し、既存driverによる回収後にZIPと全96 member payloadを再hashした。
固定割当・metadata・重複なしの照合を通り、C1T2回収は496/768群・43,648行となった。
追加1,760行の診断flag・未定義項目をすべて保持し、区間未取得は0行だった。
記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v20.json`、SHA256は `d4eccd91e2aa46c88e34a089dd5cd00cc4d08f57b4aaddb07602d32810ff0463` である。
これは回収・構造・byte照合であり、C1T2の科学的受入は未完了である。
collector265419は同時点のqstatでR・walltime 3:25:05・CPU time 3:11:14だった。

03:42の空き容量はlocal Aが191,404,347,392 byte、DGXが222,090,129,408 byte、Labo Dが7,910,210,461,696 byte、クラスタが13,585,699,368,960 byteだった。
読み取り観察を `data_tile_validation_2026-10-17/storage_observation_20261022_v4.json` に保存し、そのSHA256は `c003903a52669c3864844ad53df8c125380d74edc5daf7fc8e0d0a7d39a2dcae` である。
容量の予約や残り全作業の容量保証は行っていない。

## 03:33 JST：C3T0 collectorの中間観察

collector265419はPBSでRを維持し、03:33の照会ではwalltime 3:15:03・CPU time 3:01:44だった。
回収出力の `tasks.jsonl` を読み取り専用で観察し、03:29と03:32に完全な改行まで書かれたanchor 192件・sampling 40,241件を確認した。
この2回の可視行数は同じだったが、PBSのCPU時間は増えている。
書き込み中のファイルの可視行数は正確な実行位置や全工程の進捗率ではなく、その後にも全payload再hash・context確認が残るため、この値から終了時刻を外挿しない。
観察は `data_tile_validation_2026-10-17/c3t0_collector_progress_20261022_v1.json` と `c3t0_collector_progress_20261022_v2.json` に保存した。
計算ノード内のプロセス確認はSSH認証で拒否されたため、詳細な実行位置は未確認であり、停止や正常終了とは判定していない。
既存のcollector復旧コードは2時間上限で失敗した旧collection向けに固定されており、今回の4時間上限・別出力先へそのまま適用できない。
現ジョブ・driver・固定sourceは変更せず、確定終端が出るまでは新しい回収を投入しない。

## 03:15 JST：PCの次batchと計時前処理の費用確認

DGX batch19はPID3902275、Labo batch4はPID12628の生存を実確認し、completionはいずれも未作成だった。
固定config hashはDGXが `9f1ea4660aa1edbb67c9b32f90720586818772ac24768e811bda8b781a946e7f`、Laboが `fe483102e3ecd6a121ecc9ccc0e8559d3202ec569d564cf73d8c531e28b9e6fd` である。
既存serial driverが処理を進めており、追加投入は行っていない。

C1T1の受理済みcandidateの実測walltime 8,649秒を含め、計時前処理の保存費用を8条件分へ更新した。
既存のhash余裕を含む基準値の合計は40,937.877秒で、24時間の要求上限・1.5倍係数・600秒余裕の式に対する残り4条件分の余地は16,262.123秒である。
これは要求資源計算の途中経過であり、終了予想や全12条件の実行可能性の確認ではない。
元candidate・sourceのhashを再照合し、`data_tile_validation_2026-10-17/low_timing_saved_cost_headroom_20261022_v2.json` に保存した。
そのSHA256は `e5f8e71c8e35f7fbe2dc3b4d68936c1aab29a916621aee74b0517989841613ff` である。
上限超過時は分割方針の実装・受入を行い、条件の除外や上限判定の無効化は行わない。

## 03:14 JST：C1T1受入とC1T2回収476/768群

C1T1最終reportの回収は03:09、独立算術確認と後続candidate作成は03:10に完了した。
回収13ファイルのhashをreceiptと再照合し、accepted・remote_snapshot_unchangedを確認した。
独立算術確認は67,584行・352設定・各192 seedを保持し、11,968値の最大絶対差は5.551115123125783e-17だった。
[結果報告](low_c1t1_recovered_result_2026-10-22_ja.md)を保存し、低ノイズ検証作業の完了数を8/12へ更新した。
長い16設定でも全seedに混合診断の警告が残り、名目95%被覆や精度を認定したものではない。
旧watcherの失敗記録は保持し、復旧後の独立算術確認は `data_tile_validation_2026-10-17/c1t1_final_downstream_recovery_v1/completed.json` を参照する。

C1T2ではDGX batch18とLabo batch3の実PID終了とcompletionを確認し、回収ZIPと全208 member payload、固定割当・metadata・重複なしを照合した。
回収は476/768群・41,888行となった。
追加3,872行のうち診断flagは3,872行、診断未定義は3,868行、区間未取得は0行であり、すべて保持する。
記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v19.json`、SHA256は `85c0bed7cfb6581ab37dfab510306cf6eeccb0254684957e4393740479f22d21` である。
これは回収データの構造・byte照合であり、C1T2全条件の科学的受入ではない。
03:13時点の自分のPBS一覧では、C3T0 collector265419のみがR・1要求nodeだった。

## 03:01 JST：C1T1最終集計ジョブの正常終了

C1T1最終集計265420は02:57:27 JSTにF・exit status 0・run_count 1で終了した。
実測walltimeは2時間24分9秒、CPU時間は2時間18分42秒、保存peak memoryは1,526,868 KBだった。
実PBSの終了情報と復旧rootのscript対応を確認し、`data_tile_validation_2026-10-17/c1t1_recovered_terminal_observation_20261022_v1.json` に記録した。
そのSHA256は `f20e4fea94dcaf973c41d632253a1043d941f0ddd2b728b4fb7daf31da9179b8` である。
既存driverは終了後のcomplete処理に進んでおり、最終reportの回収・独立算術確認・後続candidate作成はこの時点では未受理である。
正式完了は7/12条件のままとし、ジョブ正常終了だけでは増やさない。
同時点の自分のPBSジョブ一覧では、C3T0 collector265419のみがR・1要求nodeだった。

## 02:46 JST：DGX batch18の実行を確認

既存serial driverがC1T2のDGX batch18を起動し、固定config hash `5d6d4821a852af62213afa98a07703c7cbd908bed61505e20309e05a990f208f` に対応する実PID3845048の生存を確認した。
completionは未作成で、確認済み回収は432/768群のままである。
観察は `data_tile_validation_2026-10-17/c1t2_dgx_batch18_process_observation_20261022_v1.json` に保存した。
クラスタ最終集計driverも稼働を継続し、正式完了数は変わっていない。

## 02:43 JST：C1T2回収が432/768群へ進展

DGX batch17は実PID3835137の終了と固定configに対応するcompletionを確認し、既存driverによる転送検証後に追加20群を照合した。
ZIP全体と全96 memberのbyte hash、固定割当、既存群との重複なし、前回metadataの不変性を確認した。
確認済み回収は432/768群・38,016行となり、追加1,760行の診断警告・未定義項目をすべて保持する。
追加分の区間未取得は0行である。
記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v18.json`、SHA256は `a812e83f026ac397579016f64f8becc8ae3c773e9a48e43e961cb8a255b98003` である。
これは保存データの転送・構造・byte照合であり、条件全体の科学的受入ではない。
既存driverはDGX batch18の入力exportへ進み、クラスタの265419・265420はともにRである。
正式完了は7/12条件のままである。

02:42 JSTの空き容量はlocal Aが192,192,901,120 byte、DGXが224,105,914,368 byte、Labo Dが7,911,336,529,920 byte、クラスタが13,586,025,873,408 byteだった。
読み取り観察を `data_tile_validation_2026-10-17/storage_observation_20261022_v3.json` に保存した。
この時点の空き容量であり、残作業全体の容量を保証しない。

## 02:17 JST：DGX batch17の実行を確認

既存serial driverがC1T2のDGX batch17を起動し、固定config hash `fd66a0ff7957ecface78a7ae62dbe870e3678dc01315c00dc7d63ab13e2b70ba` に対応する実PID3835137の生存を確認した。
completionは未作成で、確認済み回収は412/768群のままである。
観察は `data_tile_validation_2026-10-17/c1t2_dgx_batch17_process_observation_20261022_v1.json` に保存した。
クラスタ最終集計driverも稼働を継続し、正式完了数は変わっていない。

## 02:14 JST：C1T2回収が412/768群へ進展

DGX batch16は実PID3778965の終了と固定configに対応するcompletionを確認した。
既存driverによる転送検証後、ZIP全体と全96 memberのbyte hash、固定割当、既存群との重複なし、前回metadataの不変性を照合した。
確認済み回収は412/768群・36,256行となり、追加1,760行の診断警告・未定義項目をすべて保持する。
追加分の区間未取得は0行である。
記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v17.json`、SHA256は `8413c76be62b7d0eab21cde43cf1f234e150b4542488e2981c09ea7ef2e3a0e0` である。
これは保存データの転送・構造・byte照合であり、条件全体の科学的受入ではない。
既存driverは次のDGX batch17の入力exportへ進み、クラスタの265419・265420はともにRである。
正式完了は7/12条件のままである。

## C1T2のPC解析工程の時間目安（392群回収時点）

保存済みの同一local controller時刻から、入力export開始から回収完了までの周期を確認した。
DGXの直近3batchは各28.28〜28.75分、Laboの直近2batchは各141.70〜141.82分だった。
固定割当の残りは実行中を含めDGXが17batch・328群、Laboが2batch・48群である。
同じ周期が続くと仮定した単純外挿では、C1T2のPC回収は10月22日10時頃が目安となる。
この外挿は後半の群ごとの費用差・障害・待ち時間を見込んだ予測区間ではなく、全検証の終了予想でもない。
残る最終集計・他条件・独立計時・最終報告の所要時間は含めず、最後の小さいbatchにも全batch分の周期を割り当てている。
host間で割当群とworker数が異なるため、これを同条件の機種間benchmarkとしても扱わない。
入力hash・元の時刻・計算式と外挿値は `data_tile_validation_2026-10-17/c1t2_pc_cycle_observation_20261022_v1.json` に保存した。

## 01:49 JST：DGX batch16の実行を確認

既存serial driverがC1T2のDGX batch16を起動し、固定config hash `1b68b0201f1f661a167e1deae5eea2624bcdc57e383083c7872e763d4212f614` に対応する実PID3778965の生存を確認した。
completionは未作成で、確認済み回収は392/768群のままである。
観察は `data_tile_validation_2026-10-17/c1t2_dgx_batch16_process_observation_20261022_v1.json` に保存した。
クラスタ最終集計driverも稼働を継続している。

## 01:46 JST：C1T2回収が392/768群へ進展

DGX batch15は実PID3768730の終了と固定configに対応するcompletionを確認し、既存driverによる転送検証後に追加20群を照合した。
ZIP全体と全96 memberのbyte hash、固定割当、既存群との重複なし、前回metadataの不変性を確認した。
確認済み回収は392/768群・34,496行であり、追加1,760行の診断警告・未定義項目をすべて保持する。
追加分の区間未取得は0行である。
記録は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v16.json`、SHA256は `b25ba491045ba95d182637373124b670331bc3dfdc8662cd27ece6d01c09c1c2` である。
これは保存データの転送・構造・byte照合であり、条件全体の科学的受入ではない。
クラスタ最終集計driverは引き続き稼働し、正式完了は7/12条件のままである。

01:41 JSTの空き容量はlocal Aが192,743,538,688 byte、DGXが226,036,269,056 byte、Labo Dが7,911,336,529,920 byte、クラスタが13,586,176,966,656 byteだった。
読み取り観察を `data_tile_validation_2026-10-17/storage_observation_20261022_v2.json` に保存し、残作業全体の容量保証とは区別する。

## 01:22 JST：DGX次batchの実行開始

既存serial driverによるC1T2のDGX batch15の入力転送と起動が進み、固定config hash `b198994b86d13801747bb3f4346f9b043744ee9517d7940c08eb9b2350d74724` に対応する実PID3768730の生存を確認した。
completionは未作成であり、確認済み回収は372/768群のままである。
観察は `data_tile_validation_2026-10-17/c1t2_dgx_batch15_process_observation_20261022_v1.json` に保存した。
クラスタの265419と265420もRで、前回確認からCPU時間が増加している。

## 01:19 JST：DGXの追加20群を回収・照合

C1T2のDGX batch14について、実PID3711364の終了と固定configに対応するcompletionを確認した。
転送済みZIP全体・全96 memberのbyte hash、固定割当、既存群との重複なし、前回metadataの不変性を照合した。
確認済み回収は372/768群・32,736行となった。
追加1,760行はすべて診断警告と未定義項目を含み、区間未取得は0行で、全行を分母に保持する。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v15.json`、SHA256は `cc79f0153b24c2d6b22bf262a158d75e8f406acc498d33b89f8b1a7ebd0f3f7f` である。
これは転送・構造・byte照合であり、数値再計算や条件全体の科学的受入ではない。

DGXの既存serial driverの実PID46624は生存し、次のbatch15の入力exportへ進んでいる。
batch15のlaunch intentはこの時点では未作成であり、解析開始とは扱わない。
Labo batch3は実PID25052の生存を確認し、completionは未作成である。
クラスタの265419と265420はともにR・run_count 1で、C1T1最終回収のcompleted.jsonはまだ存在しない。
実行観察は `data_tile_validation_2026-10-17/execution_observation_20261022_0120_v1.json` に保存した。
正式完了は7/12条件のままで、公開候補の公開承認待ちとは独立に計算を継続する。

## 00:54 JST：公開候補の再確認と次batch

GitHubのmainはlocalと同じ `886b44b9fdc56d5b86491302dfb651285bbc4113` で、CI39325976119は全12jobが成功している。
凍結した公開候補 `47ef1b6ad957a93dae3bbd6cf1d79fab86457e96` のCI39267489093も全12job成功を再確認した。
両commit間でsrc・tests・examples・notebooks・pyproject.toml・英日READMEの差分はない。
source ZIP・環境差検証ZIP・wheel・SHA256SUMSの4配布物と日英release本文のhashは準備済みの値に一致した。
00:53 JST時点でリポジトリはPRIVATE、releaseは0件、remote tag `v0.1.0.dev5` は未作成である。
再確認は `data_experimental_release_2026-10-19/remote_status_20261022_v1.json` に保存した。
AGENTS.mdの所有者判断に関する指示に従い、検証済み候補を当該tagのGitHub pre-releaseとして公開し、リポジトリをpublicにする確認を依頼した。
回答までは公開操作を行わず、数値検証を継続する。

C1T2の既存serial driverは次batchへ進み、DGX batch14の実PID3711364とLabo batch3の実PID25052が固定configに対応して稼働していることを確認した。
両batchのcompletionは未作成である。
観察は `data_tile_validation_2026-10-17/c1t2_pc_process_observation_20261022_v1.json` に保存した。
同時点のクラスタは265419と265420がRで、要求ノード合計2を維持する。

## 00:49 JST：追加PCの44群を回収・照合

C1T2（tile288 bit-flip、p=0.001）のDGX batch13とLabo batch2について、実PID終了・固定configに対応するcompletionを確認した。
両batchの転送検証後、ZIP全体と全208 memberのbyte hash、固定割当、既存308群との重複なし、前回保存metadataの不変性を照合した。
確認済み回収は352/768群・30,976行となった。
追加3,872行はすべて診断警告を含み、診断未定義は3,868行、区間未取得は0行で、全行を分母に保持した。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v14.json`、SHA256は `16fdb3b6e155e468101917672be5e4681051f74c435ea1e1859b7b9e765539c0` である。
これは保存済み結果の転送・構造・byte照合であり、数値再計算・native再decode・条件全体の科学的受入とは区別する。
両hostを管理する既存serial driverの実PID25116・46624は同じC1T2設定で生存しており、次batchの処理を引き続き担当する。

00:43 JSTに保存先の空き容量も読み取り確認した。
local Aは193,401,548,800 byte、DGXは227,998,425,088 byte、Labo Dは7,912,420,069,376 byte、クラスタは13,586,438,647,808 byteだった。
観察は `data_tile_validation_2026-10-17/storage_observation_20261022_v1.json` に保存し、容量予約や残作業全体の容量保証ではない。
正式完了は引き続き7/12条件であり、クラスタのC1T1最終集計・C3T0 collectorと残るPC解析を継続する。

## 00:41 JST：復旧後の実行と後続経路の確認

C1T1最終集計265420とC3T0 collector265419はともにR・run_count 1で、CPU累積時間が増えている。
C1T1のexecution.jsonに実job ID・固定config hash・実行hostが記録され、readerの標準出力・標準エラーの保存先も作成された。
この時点でcompletion・final-report・failureは未作成であり、処理完了や結果の受入を意味しない。

新しいfinal rootを使う後続経路について、candidate作成、metadata reader、全12条件のinventoryとassemblyを読み取り確認した。
確認したmetadata readerとCLIは、固定native環境に記録されたsource hashとローカルsourceが一致した。
これらの処理は受理したdescriptorからfinal config・script・report・submissionのパスを導出する。
このsource確認は `data_tile_validation_2026-10-17/c1t1_relocated_downstream_source_review_20261022_v1.json` に保存し、新rootの最終結果や全12条件での実行受入は未実施として区別する。

計時前処理の資源計画も、受理済み7条件の保存実測値と既存の割増式で確認した。
既知のwall basisは30,126.627秒で、既存の24時間上限・1.5倍・600秒加算の式では残る5条件のbasisに使える範囲は27,073.373秒である。
この値は許容資源計画の残枠であり、計算の残り時間やETAではない。
全12条件の資源は未確定で、今後の実測が式の上限を超えれば既存controllerは停止し、条件を削らず実行方式を見直す必要がある。
観察は `data_tile_validation_2026-10-17/low_timing_saved_cost_headroom_20261022_v1.json` に保存した。

## 最新状況（00:34 JST）

C1T1の最終集計をqsubで投入し、job265420が00:33:17 JSTからR・run_count 1であることを確認した。
要求資源は1 node・1 CPU・32 GB、walltime上限12時間であり、上限を終了予想とは扱わない。
ローカルとremoteの投入台帳が一致し、実PBSのSubmit_argumentsが保存scriptと一致することを確認した。
configとscriptのhashは復旧前と同一で、`No closing quotation` の失敗記録は同じbyte hashの履歴ファイルとして保持されている。
qsub応答・intent・台帳・保全記録のhashを `data_tile_validation_2026-10-17/c1t1_recovered_qsub_observation_20261022_v1.json` に保存した。
00:34 JSTのactive jobはC3T0 collector265419とC1T1最終集計265420の2件で、Qを含む要求ノード合計は2である。
復旧driverは正常終了の確認・元collectorによる回収・新rootに対応した算術再集計と計時候補作成へ進む構成であり、後続の実完了は未確認である。
正式完了は引き続き7/12条件で、C1T2の全trace監査は完了、PC回収の独立byte照合は308/768群まで完了した。

## 00:29 JSTの確認

正式完了は7/12条件のままであり、公開準備と数値検証の完了を区別する。
C1T2の全trace監査265418は00:14:56 JSTにF・exit 0・run_count 1で終了した。
summaryは768群・92,160 planned task、failed_audit_groups=0・failed_sampling=0・input_changes=[]・context_error=nullである。
native platformの確認はtrueだが全physical stateの再decodeはfalseであり、混合・精度・被覆の保証ではない。
summary SHA256は `2d30957443c145d88ecd30f16163c81b39d71e676505c6e70117817edeb9ab72` である。
C3T0のcollector265419は00:16:52 JSTに開始し、00:28 JST時点でR・1 node・1 CPU・32 GBである。
この観察は `data_tile_validation_2026-10-17/cluster_transition_observation_20261022_v2.json` に保存した。

C1T2のDGX batch12は実PID終了とcompletionを確認し、ZIP全体・全96 memberのbyte hashと固定割当を独立照合した。
回収済みは308/768群・27,104行となった。
追加1,760行は診断警告・未定義項目を含み、区間未取得は0行で、全行を分母に保持する。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261022_v13.json`、SHA256は `01460e5af74c0b99c70ca59fa3a0abc4ea9f620e19dd706da278bdd2af257718` である。

C1T1の復旧版v1はprepareとpreflightを完了したが、投入前の既存プロセス検査がpsの表示文字列をshell引数として解析し、`No closing quotation` で停止した。
新rootにも投入intent・qsub応答・ジョブIDはなく、response_uncertain=falseのerrorを保存した。
旧root・旧controller・科学的設定を保持し、実argvを `/proc` から読む検査と同一scriptの復旧を別版v2に実装した。
投入前の失敗記録は共有lock下でhashを確認して履歴名へ移し、削除しない。
Windowsの投入・接続試験19件、Linuxのプロセス検査・証拠保存試験10件、およびLinux実プロセスの検査が成功した。
受入記録は `data_tile_validation_2026-10-17/c1t1_final_capacity_recovery_acceptance_v2/` に保存した。
v2 driverは00:26:52 JSTに起動し、00:28 JST時点で復旧前の入力照合を実行中である。
実行履歴は `data_tile_validation_2026-10-17/planned_final_c1t1_execution_resume_v2/` に保存し、この時点では復旧jobのqsubは未確認である。
v1で見つかった後続candidateの固定rootも、C1T1と同一configに限定した別adapterで接続し、元のcollector検証を保持する。
これらの後続処理は最終集計の正常回収後に実行するため、まだ検証結果の受入は完了していない。

## 00:12 JSTの確認

公開準備は完了しているが、GitHubリポジトリの公開・release作成は未実施である。
最後の公開候補確認は前日の記録を参照し、この更新でCIや公開状態を再確認したものではない。
低ノイズ検証の正式完了は7/12条件で、残る5条件・独立計時・最終報告は未完了である。
全体の10月24〜25日という見込みは暫定であり、残る全工程を実測した完了時刻や保証ではない。

C3T0（tile288 depolarizing、p=0.01）のsample1 job265411は10月21日23:52:52 JSTにF・exit 0・run_count 1で終了した。
summaryは30,720タスク・complete=true・failed=0・missing_tasks=0で、sample0と合わせた全samplingが終了した。
summaryのSHA256は `4e5ec289147dde287a37dc87474d2f7d8d6537e5d8a48662f28be97fcc3fa795` である。
後続のnative reference job265417も00:11:01 JSTにF・exit 0・run_count 1で終了した。
これらはPBSと保存summaryの確認であり、後続の解析・全trace監査・条件全体の科学的受入とは区別する。

C1T2（tile288 bit-flip、p=0.001）のcapacity audit job265416はF・exit 0で終了し、既存driverが全trace監査job265418をqsubで投入した。
265418は00:07:17 JSTに開始し、00:11 JST時点でR・1 node・96 CPU・70 GBである。
walltime要求3時間は上限であり、終了予想ではない。
クラスタの状態とC3T0 summaryの観察は `data_tile_validation_2026-10-17/cluster_transition_observation_20261022_v1.json` に保存した。
C1T2のPC回収は直近の独立byte照合で288/768群であり、DGX batch12の実PID3644303の稼働を00:10 JSTに確認した。
この時点でbatch12のcompletionは未作成だった。

## C1T1の投入競合と復旧

C1T1（tile288 bit-flip、p=0.003）は全768群の回収・監査・最終設定を完了していたが、元の最終集計driverが10月21日23:54 JSTに停止した。
空き枠の確認後に他の後続jobが投入され、共有lock取得後の最初の検査で最大2要求ノードを超えるとして拒否された。
固定backendの該当箇所はsubmission-intent作成とqsub呼出しより前であり、remoteの旧rootにはconfig・report.sh・submission-error.jsonのみが存在した。
errorは `queued/running node budget exceeded`・`response_uncertain=false` であり、旧rootに投入intent・qsub応答・ジョブIDはない。

[復旧仕様](c1t1_final_capacity_recovery_2026-10-22_ja.md)に従い、旧rootと元のdriverを保ったまま、同一configを新しい出力rootにprepareする別driverを用意した。
投入前の容量不足だけを待機に戻し、intent後の失敗・未知の例外・qsub応答不明は停止する。
Windowsの受入試験20件と、クラスタLinuxの投入・証拠保存に関する17件の試験が成功した。
元のreader・科学的設定・入力・要求資源は変更していない。
受入記録とsourceは `data_tile_validation_2026-10-17/c1t1_final_capacity_recovery_acceptance_v1/` に保存した。

復旧driverは00:10:22 JSTに起動し、00:11 JST時点では新rootのprepare処理が実行中であり、復旧jobのqsubは未確認である。
実行履歴は `data_tile_validation_2026-10-17/planned_final_c1t1_execution_resume_v1/` に保存する。
旧監視処理がC1T1をfailedとして固定済みであることを確認し、正常回収後はその条件だけの算術再集計と計時候補作成を別の接続で実行する。
元のerrorは正常回収後にhashを確認して履歴名へ移し、既存の完了待受先へ復旧の出典付き記録を置く。
失敗の証拠を削除したり、曖昧な投入を再試行したりはしない。

過去の計測と公開準備の詳細は[前日の状態](PROJECT_STATUS_2026-10-21_ja.md)を参照する。
