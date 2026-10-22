# 2026-10-21朝の残計算と終了見込み

06:39 JSTの実ファイル観察では、低ノイズ12条件の正式完了は6条件である。
公開候補の準備と、残る数値検証全体の完了は分けて扱う。
残る計算の終了をexperimental公開の前提にしない。

## 未開始samplingとanchor

元のsampling partition manifestに保存された `predicted_seconds` を用いる。
これはcapacity測定からの外挿であり、PBSの `walltime` 上限ではない。
各partitionのexecution-intentが未作成で、submission ledgerも未作成であることを観察した。
実行中のC3T0 partition 0はこの集計に含めない。

| 条件 | 未開始sampling区画 | 未開始anchor区画 |
|---|---:|---:|
| tile288 bit-flip、p=0.001（C1T2） | 2 | 1 |
| tile288 depolarizing、p=0.01（C3T0） | 1 | 0 |
| tile288 depolarizing、p=0.003（C3T1） | 2 | 1 |
| tile288 depolarizing、p=0.001（C3T2） | 2 | 1 |

計10区画の予測秒数の和は250,101.828580秒で、69.472730ノード時間に相当する。
単純に2で割った34.736365時間は、2ノードを常時使え、依存関係や他工程との競合を無視した参考値である。
実測の終了時刻、達成可能な下限、全体のETAのいずれでもない。
capacity外挿と本番実測は異なりうるため、この値を確定した所要時間として扱わない。

この集計には、実行中partitionの残処理、queue待ち、raw trace監査、PCでのBAR解析、回収・最終検証、独立計時、最終報告を含めていない。
したがって数値検証全体を10月21日中に完了する計画とはせず、10月22日以降にも継続する前提で公開を進める。
具体的な全体終了時刻は、後続工程の実測が揃ってから更新する。

## 証拠

観察は `data_tile_validation_2026-10-17/remaining_sampling_capacity_observation_20261021_v1.json` に保存した。
各元manifestのremote path・SHA256、各partitionの予測秒数・task数・execution有無・submission job、既存summaryのhashを含む。
観察ファイルのSHA256は `8047de8774114829de47b1bbe9c88b403e8ec339574f85fba947a8012fecd44e` である。
集計は `data_tile_validation_2026-10-17/remaining_sampling_capacity_estimate_20261021_v1.json` に保存した。
再計算式は、観察の各condition・phase・partitionのうち `execution_present == false` の `predicted_seconds` を合計し、3600で割ってノード時間、7200で割って理想化した2ノードの時間とする。
この観察と集計により新しい計算jobの投入や既存jobの変更は行っていない。

## C1T1のPC処理周期による参考見通し

C1T0の最終検証と独立再集計を完了し、正式な低ノイズ完了数は7/12条件へ進んだ。
C1T1の固定assignmentはDGX648群・33 batch、Labo120群・5 batchである。
保存済みlaunch intentの開始時刻から、直近最大5回のbatch開始間隔を求めた。
この間隔は計算だけでなく、batch間の回収・転送・準備の時間も含む。
DGXの直近5間隔の中央値は1,546.933秒、Laboは観測2間隔の中央値7,445.587秒だった。
「最後に起動したbatchの開始時刻＋そのbatchを含む残batch数×中央値」で外挿すると、DGXは10月21日18:19頃、Laboは同日13:58頃となる。
末尾の部分batchも通常batchとして数え、今後も同じ処理周期が続くと仮定した参考値であり、統計的な予測区間や完了の約束ではない。
この計算はC1T1のPC側処理だけを対象とし、条件全体の最終検証・後続条件・独立計時・最終報告を含まない。
そのため全体のETAには読み替えず、残る数値検証全体の終了時刻は引き続き未確定である。
元assignmentとlaunch intentのhash、開始時刻列、計算式は `data_tile_validation_2026-10-17/c1t1_pc_cycle_estimate_20261021_v1.json` に保存した。
記録のSHA256は `6477d1c566076e6e350e01b862f4455db6508f75feedfeb3a518fd3fc6b90dd2` で、新しいsampling・BAR・benchmarkは実行していない。

## C1T2 sampling後半の実測に基づく参考見通し

C1T2（tile288 bit-flip、p=0.001）のsampling前半265389は12:17:34 JSTに正常終了し、実walltimeは4時間37分45秒だった。
同じ固定planの前半・後半はそれぞれ46,080 task、96 worker、1 node・96 CPU・32 GBで、replicate範囲が0–95と96–191に分かれる。
後半265390は12:17:34 JSTに実行開始した。
前半と同じ所要時間だと仮定して開始時刻に4時間37分45秒を加えると、後半samplingの終了目安は10月21日16:55頃となる。
前半の実測は区画内の終了検証を含むが、1区画だけからの外挿であり、統計的な予測区間や完了の約束ではない。
この目安には後続の回収・独立監査・PC解析・他条件・独立計時・最終報告を含めず、条件全体や検証全体のETAとは扱わない。
計算式・参照したPBS観察・partition manifestのhashは `data_tile_validation_2026-10-17/c1t2_sample1_elapsed_estimate_20261021_v1.json` に保存した。
記録のSHA256は `bf157754aad3baba2f7df0af95296714c9a44a06fd132b520b34f8aad05c449f` であり、追加の数値計算やjob変更は行っていない。

## 17:05 JST：sampling終了の実績

C1T2 sampling後半265390は16:55:31 JSTにF・Exit_status=0で終了し、実walltimeは4時間37分56秒だった。
終了記録の46,080 taskは予定一覧と一致し、失敗・欠損・重複はいずれも0である。
観察は `data_tile_validation_2026-10-17/c1t2_sample1_terminal_followup_observation_20261021_v1.json`、SHA256は `c375ebf382db5fb928485fa4e13d15be0a70814479826b7d8636ad33d558d7f1` に保存した。
sampling終了後もnative reference、raw trace監査、PC解析、最終検証が残り、正式完了数は7/12条件のままである。
残る数値検証全体は10月23日以降を暫定の作業見通しとするが、後続条件・独立計時・最終報告の所要時間が未確定であり、終了時刻の予測区間や保証ではない。
experimental版の公開準備は既に完了しており、数値検証全体の完了とは分けて扱う。

## 17:12 JST：未開始区画の更新

固定済みpartition manifestのhashが朝の観察から変わっていないことを確認し、execution intent・submission ledger・summary・実PBS状態を再観察した。
未開始かつ未投入の区画は、tile288 depolarizing p=0.003とp=0.001の各sampling 2区画・anchor 1区画、計6区画である。
これら6区画のcapacity外挿の合計は45.672760ノード時間であり、朝の69.472730ノード時間から完了済み・開始済みの区画を除いた値である。
一方、tile288 depolarizing p=0.01のsampling後半265411はRであり、この45.672760ノード時間には実行中区画の残時間を含めていない。
native reference、queue待ち、raw trace監査、PC解析、回収・最終検証、独立計時、最終報告も集計対象外である。
これは未開始sampling・anchorの資源量の参考値であり、2ノードで割った値を全体の残時間や達成可能な下限とは扱わない。
観察と確認コードは `data_tile_validation_2026-10-17/remaining_sampling_capacity_observation_20261021_v2.json`、SHA256は `688cb99af13d0673f9cc49064771895596fb02adf57d08420519b8cfa84de77d` に保存した。
集計は `data_tile_validation_2026-10-17/remaining_sampling_capacity_estimate_20261021_v2.json`、SHA256は `5e088c5a4d4198980b6200e2686d5dd51941c9896f20ed91cdf06f18777557dd` に保存した。
新しいjob投入・計算設定変更・追加benchmarkは行っていない。

## 18:05 JST：C1T1のPC担当分を回収

C1T1のDGX serial driverは18:01:13 JSTに全担当分の回収を記録し、exit code 0で終了した。
先に完了したLabo担当分と合わせ、全768群の転送検証が揃った。
全38 batchのassignment・config・completionのmetadataを独立に列挙した768群と照合し、重複・欠けがないことを確認した。
観察は `data_tile_validation_2026-10-17/c1t1_all_hosts_assignment_completion_observation_20261021_v1.json`、SHA256は `d0db7053a06dc8028a2cee0a67313066edccfeeb64aab462996e0b3a537130f0` に保存した。
この時刻はPC担当分の回収完了であり、条件全体の最終検証・独立再集計の完了時刻ではない。
後続のcohort index作成が進んでおり、低ノイズの正式完了数は引き続き7/12条件である。

## 2026-10-22 13:14 JST：C3T0 PCとC3T1 samplingの実測による見通し

この時点の低ノイズ正式完了は8/12条件である。
C3T0のDGX入力exportの待機上限による停止は[復旧済み](c3t0_dgx_recovery_result_2026-10-22_ja.md)で、batch8の解析へ戻っている。
保存済みの正常完了記録から、DGX batch4〜7のexport開始から回収完了までの周期は22.83〜23.33分、中央値23.12分だった。
labo batch1〜3の周期は97.65〜98.39分、中央値98.07分だった。
現在batchのlaunch時刻に、そのbatchを含む残batch数と過去周期の積を加えると、C3T0の担当分回収の目安はDGXが10月22日22:40頃、laboが同日14:15頃となる。
既に済んだ現在batchのexportと末尾の小さいbatchも通常の一周期として含めており、厳密な終了予測や上限ではない。
過去周期の最小・最大で得た幅は統計的な予測区間ではなく、追加の停止や性能変動を含まない。

C3T1 sampling前半265423はExit_status 0で終了し、実walltimeは7時間59分27秒だった。
前半と実行中の後半265438は各39,936 task・96 worker・1 node・96 CPU・32 GBで、独立seed群のreplicate範囲は0〜95と96〜191である。
後半は10月22日12:52:51 JSTに開始し、前半と同じ所要時間なら同日20:52頃にsamplingが終了する計算になる。
一方、事前capacity外挿10時間34分01秒を用いると同日23:27頃となる。
両者は別の仮定に基づく参考値であり、その間に終了するという区間保証ではない。
終了を予測した対象はsamplingだけで、native reference・trace監査・PC解析・集約・科学的な受理は含まない。

残るC3T2、全12条件の設定選択とseed census、独立計時、最終報告の所要時間はこの計算に含めていない。
したがって全体の終了時刻は未確定とし、従来の10月24〜25日という作業目安を今回の計算で保証したとは扱わない。
入力hash、元timestamp、PBS生記録、計算式は `data_tile_validation_2026-10-17/remaining_work_estimate_20261022_v2.json` に保存し、SHA256は `f27398606182ca10bc7c636116db2b9104aec9312048dfc251330caf2d2de46a` である。
確認コードは同階層の `observe_operational_estimate_20261022_v2.py` に保存した。
追加benchmark、sampling、job投入・変更は行っていない。
