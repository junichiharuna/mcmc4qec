# DRAFT：tile検証の最終報告と完了監査

本稿は最終報告の草稿であり、独立計時・最終科学reader・report・証拠保存を含む全検証は未完了である。
以下は保存済み報告・回収証拠の要約であり、本稿の編集ではraw datasetの再読込や数値再計算を行っていない。

2026-10-29の追記: 独立計時48手法行は全件terminal・exit 0となり、最終report（`report.json`・`report_ja.md`）は10/29 02:21 JSTに別経路で受理した。
結果は第3節末尾の「独立計時の最終report（2026-10-29 02:21 JST受理）」に記載し、以下の本文と表は追記前の時点（2026-10-26 08:41 JST）の記述を履歴として保持する。
v13 final-report役の受領書、最終科学証拠のsnapshot保存、再現資料の照合は未完了である。

全12条件の比較とcomparison・handoffは受理済みで、元12worker・merge・acceptanceの計14ジョブを再実行せず引き継いだ。
[全件seed照合と正式受理](data_tile_validation_2026-10-17/low_timing_full_census_v13_20261025/README_ja.md)では4,208,002件を検査し、予期しない衝突0・意図した共有8,448件・一意seed4,199,554件を確認した。
これは有限な予定seedの重複検査であり、統計的独立性の証明や実sampling metadata全件の監査ではない。

| 対象 | 確認済み範囲と残工程（2026-10-26 08:41 JST時点） |
|---|---|
| 独立計時の準備・進捗 | 全48手法行（ready24・not_selected24）とcapacity manifest24件を保持し、実行対象の本計時は6/24件を正式受理済み。各本計時の予定分母は192で、非選択行も最終報告から除外しない。 |
| 現在の実行 | `c0t1e1` のMC265770はF/0・run_count=1・PBS wall56分07秒で計算を完了し、[08:41の結果監査](../../output/census_active_node_migration_v1/mc-t1e1-main-result-audit-1792971680426190900/audit.json)で個別192record・全件成功/取得済み・費用整合・summary/manifest/実PBSの結合を確認した。controller正式finishと精度gateは未確認で、本計時の正式受理数は6/24件を維持する。BAR265772は稼働中で、[08:33の割当原本](../../output/census_outer_operation_v1/bar-t1e1-main-allocation-1792971182972444900.json)ではR（08:31:57開始）、当時のMCと別2物理ノード・各96 CPU/337 GiB、queued/unplacedなしだった。同観測時点のBAR execution/native/summary/failureは未生成で、結果・正式受理は後続確認待ちである。 |
| 最終化 | 残る本計時、PBS readerによる全結果・費用・精度gateの照合、最終JSON・日本語報告への統合、実source・環境・seedと最終証拠のsnapshot保存が未完了。PBSの要求時間や一部jobの成功から全体ETA・精度・速度優位を推定しない。 |

最終保存preparerはクラスタjob265759で37件の合成fixtureを通過したが、本番の最終snapshot保存は未実施である。

正式finish receiptの`scientific_validation_complete=false`を保持し、運用上の受理と最終科学検証を区別する。
MCの確認済みcohortでは個別192recordと費用を監査した一方、BARは小要約・投入・終端・正式回収の監査に限り、巨大summaryの個別record・費用・full bindingは後続PBS readerで確認する。
小要約の指定pin・run root対応や、job ID・manifest digestを持たない要約のhash一致だけを、科学結果の完全な結合証明としない。

公開状態は01:07:44 JSTの[読み取り専用API確認](publication_state_check_2026-10-26.json)でpublic・非draft prerelease・配布物5件を維持し、前日のmain/tagと一致した。
配布物内容・CI・Zenodoは再検証しておらず、公開済みexperimental版を進行中の科学検証やworking treeの追加変更の公開と同一視しない。
[v13復旧差分snapshot](finite_flow_v13_delta_snapshot_acceptance_2026-10-25_ja.md)は準備時点の保存であり、後続計時・最終科学証拠の保存完了ではない。
個別jobの時刻・原本hash・限定監査へのリンクは[状態文書](PROJECT_STATUS_2026-10-24_ja.md)と[最終成果物監査](final_deliverable_audit_2026-10-24_ja.md)に保持し、本稿では科学的結論と適用限界を扱う。
実起動sourceと再開時の確認先は[接続受入記録](tail_census_resume_acceptance_2026-10-25_ja.md)と[再起動手順](cluster_resident_resume_2026-10-25_ja.md)を参照する。

## 1. 確認済み範囲

experimental版0.1.0.dev5はGitHubで公開済みで、公開記録にはmain/tag・CI・配布物の照合が保存されている。
公開済み状態を維持し、計算用作業ツリーの旧履歴を公開mainへpushしない。
公開は混合・精度・名目95%被覆・速度優位の一般保証ではない。
根拠は[公開結果](publication_result_2026-10-24_ja.md)であり、Zenodo記録・DOIの照合は別途未確認である。
現在の公開mainと固定Releaseの違い、配布物と利用例の取得先は[取得監査](reproduction_access_inventory_2026-10-25_ja.md)に記録する。

| 対象 | 確認済み範囲 | 未達・未確認の範囲 |
|---|---|---|
| tile72/288、bit-flip・depolarizing | 符号構築、CSS可換性、paired logical basis、code-capacityモデル、論理失敗定義 | 距離の独立証明、全失敗支持の連結性 |
| 固定BP-OSD | 有限fixtureでの環境内再現性、環境間差、prior感度、目標priorを固定した校正 | 全入力の決定性、別環境で同一failure集合となる保証 |
| 主4条件 | 独立MC/WSS、各192反復・352設定のBAR、保存trace監査、混合比較、独立計時 | 名目95%被覆の保証、一般的な速度優位 |
| 低ノイズ12条件 | 4符号・noise組合せ×p=0.01/0.003/0.001の条件別入力、最後の条件の集約・算術照合、全12条件comparison受理 | 正式selectionと最終reportの対応照合、独立計時、最終結論 |
| BP-LSD・BeliefFind・Union-Find | 実装受入、有限入力検査、利用例 | 追加decoderごとのBAR混合・bias・被覆・速度順位の校正 |

符号は`make_tile_code(6,6)`と`make_tile_code(12,12)`を用い、引数を距離とは呼ばない。
論理失敗は物理誤りxに対して`Lx XOR D(Hx) != 0`と定義し、推定量は「いずれかのlogicalに残余誤りがある確率」P_anyである。
P_anyを8で割った値を1logicalあたりの失敗率とは解釈しない。
depolarizingではI/X/Y/Zの同時分布を保持し、独立sector復号の近似と物理ノイズの相関を区別する。
構成・定義・計測条件の詳細は[tile中間報告](tile_validation_report_2026-10-18_ja.md)第2〜5節にある。

## 2. 主4条件の結果と利用判断

主4条件はtile72のp*=0.03、tile288のp*=0.05を、それぞれbit-flip・depolarizingで計測した。
独立MC referenceは合計81,788,928試行であり、有限標本の推定値をexact truthとして扱わない。
各目標priorのdecoderをladder全体・anchor・referenceで固定し、native binaryと環境を揃える。
同じpackage版でもWindowsと固定Linux環境で失敗判定が異なる保存状態が確認されており、版番号だけで同じfailure集合を保証しない。
prior感度の有限pilotは判定が変わることを示すが、可変prior BARのbiasを直接測定した結果ではない。
根拠は[decoder環境間差](tile_decoder_platform_2026-10-17_ja.md)と[prior感度](tile_decoder_prior_effect_2026-10-18_ja.md)にある。

次表は最大予定chain・burn-in 6,000・最長保存trace・fine ladder・ZH/rejectionという固定切り口の保存結果であり、結果を見て最良設定を選んだ表ではない。
固定切り口のchain数と保存数は次のとおりであり、4条件を同じ計算予算で比較したものではない。

| 条件 | 目標p | chain数 | 保存数 |
|---|---:|---:|---:|
| tile72 bit-flip | 0.03 | 16 | 60,000 |
| tile288 bit-flip | 0.05 | 8 | 12,000 |
| tile72 depolarizing | 0.03 | 8 | 12,000 |
| tile288 depolarizing | 0.05 | 8 | 12,000 |

共通のZH混合はZ=0.7・H=0.3、lazy=0.05、cluster_k=2であり、公開既定の1chainと区別する。
bias・RMSE・被覆は有限MC referenceの点推定に対する値で、被覆の分母は全192反復である。

| 条件 | 相対bias | 相対RMSE | block32被覆 | block1024被覆 | cross_chain被覆 | 診断flag |
|---|---:|---:|---:|---:|---:|---:|
| tile72 bit-flip | −0.060% | 0.805% | 183/192 | 185/192 | 186/192 | 0/192 |
| tile288 bit-flip | +0.439% | 4.815% | 124/192 | 178/192 | 176/192 | 192/192 |
| tile72 depolarizing | −0.125% | 1.903% | 166/192 | 180/192 | 177/192 | 191/192 |
| tile288 depolarizing | +0.407% | 7.211% | 114/192 | 177/192 | 178/192 | 192/192 |

全設定・有限reference区間に対する評価は[全4条件の再集計概要](data_tile_validation_2026-10-17/final_reaggregation_four_case_scientific_summary_v1_ja.md)、観測量別の診断は[混合比較](data_tile_validation_2026-10-17/mixing_comparison_four_case_v1/report_ja.md)に保存されている。
352設定はtraceを共有しており、352個の独立実験ではない。
区間法の変更による被覆改善を、traceの混合改善とは扱わない。
同じ固定切り口のZH/ZHS・rejection/logical比較では、stabilizer混合ZHSの一律な優位は示せなかった。
depolarizingのlogical初期化はX/Z各96反復の補助層別を保存し、主分母192を置き換えない。
診断flagが0でも収束・既約性の証明ではなく、flagがある場合も非既約性の証明ではない。
詳細釣合い、lazyによる非周期性、支持の連結性、実測混合診断は[支持とkernelの記録](tile_kernel_support_2026-10-17_ja.md)に従い別々に評価する。

主4条件の独立計時は目標相対RMSE 10%・20%の8組合せで行われた。
MCとBARの双方が有限reference区間全域で精度gateを通った3組合せでは、平均task wallのMC/BAR比は0.020834〜0.045489で、今回の固定候補ではMCの費用が小さかった。
残る5組合せでは少なくとも片方がgate未達またはreferenceに敏感であり、費用比はnullのまま保持する。
双方gate通過でも実達成精度は同一ではなく、最小time-to-accuracyや母時間比の推定とは呼ばない。
独立BAR計時の混合診断は`not_collected`であり、flagged/undefined=192のplaceholderを新たな実測R-hat/ESS警告と解釈しない。
一方、全8選択候補の校正cohortには実測診断flag192/192があり、独立BAR計時のreference点に対する経験的被覆も158〜172/192だった。
相対RMSE条件の通過を名目95%被覆の確認とはせず、実測された校正時の警告も保持する。
計時cohortは設定選択cohortと分離されているが、計算機性能差は補正されていない。
全8組合せ・費用定義・被覆・制約は[独立計時の科学的レビュー](data_tile_validation_2026-10-17/main_timing_scientific_review_v1/report_ja.md)にある。

## 3. 低ノイズの確定事項と未完了事項

全12条件の比較workerは正常終了し、現行v12 journalへ元preparedと実job IDに対応するterminal12件を採用した。
index 0は旧jobのwalltime超過後に265605へ置き換え、他11件の実preparedと証拠を保持した。
旧v9のparent selector照合停止と旧v10のmerge265651のF/1を履歴として残し、[worker alias照合の復旧](worker_alias_recovery_flow_spec_2026-10-25_ja.md)と[新mergeへのtail移設](finite_tail_merge_relocation_2026-10-25_ja.md)を受入後、v11へ切り替えた。
元worker・科学source・native環境・seed・資源設定を保持し、新merge先は `20261025-low-parallel-front-v6/merge-parallel-v2` とした。
08時49分JSTには新merge265660がF/0・walltime1時間58分44秒・CPU時間3時間19分30秒、後続acceptance265661もF/0・walltime2分37秒・CPU時間2分31秒と確認した。
acceptance completionの `original_accept_terminal_executed=true` はPBS内の元受理処理・selection生成の成功を示す一方、controllerは `acceptance.observe` のstat照合で停止し、統合受理・handoffへ到達していない。
対象4artifactはdeviceだけがPBS側46・controller側2049と異なり、inode・size・mtime_ns・ctime_ns・modeは一致、canonicalな通常file・非symlinkだった。
共有filesystemに対するhost-localな `st_dev` 比較が停止原因であり、小metadataの一致を内容の再hash検証と混同しない。
旧controllerのPID1145733・start ticks768839164・journal v11と失敗原本を保持し、限定したnamespace authorityを使うobserverとtailを受入後、新v12へ切り替えた。
native265673・tail265674とlogin roundtripの[独立レビュー](cross_host_artifact_stat_review_2026-10-25_ja.md)を経て、PID1432966・start ticks769736422・journal v12の生存とcommand一致・errors空を確認した。
comparison本文の `all_twelve_processed=true` と元265660・265661への結合、継承先handoffの完了flagsを確認し、09:15:07 JSTに初回の有限tail265675がR・walltime48秒・CPU時間46秒だった。
その後265675はF/1・run_count=1・walltime13分32秒・CPU時間13分24秒・PBS記録mem15,084,044KBで終了し、09:29:23 JSTにはv12 controllerのPID1432966不在と元comparison・handoffのhash不変を確認した。
censusは1,000件pilotのcollision=0を確認後、計測値保存前に `measured census exceeds two-hour / four-GiB ceiling` で拒否されたため、時間・メモリの個別超過と実predictionは未確定である。
先行bundle検証を含むpeak selfRSSの影響を調査中で、PBS記録memとの同一視はしない。
`planning-failure.json` は `root_reusable:false` でcatalog・manifest・prepare受理記録はなく、科学bundle1,757,600,835 bytesとconfigを保持して資源計測保存と新計画を準備する。
その後の別processによる実測265678は完了し、今回の測定値と旧判定のメモリ超過を保存したが、失敗265675の値や全件censusの結果を補完するものではない。
10時13分JSTには接続受入後のv13 controllerの生存と初回census準備265700のRを確認し、本番後処理を再開したが、同時点では全件censusの完了はまだ確認していなかった。
元worker・merge・acceptanceの再実行は行わず、独立計時と報告生成は未完了である。
fixture・隔離prepare・constructorの成功は、本番全入力での科学的受理・正式selection・独立計時・最終reportの完了を証明するものではない。
現行v12 config・起動pin・受理済みcomparison・継承したhandoffとtail配置は[最終成果物監査](final_deliverable_audit_2026-10-24_ja.md)と[再起動手順](cluster_resident_resume_2026-10-25_ja.md)で確認する。
PBSの要求walltimeを完了予測とせず、以前の終了時刻予測は撤回している。
実構成・確認手順は[再開記録](cluster_resident_resume_2026-10-25_ja.md)、成果物ごとの完了条件は[最終監査](final_deliverable_audit_2026-10-24_ja.md)を参照する。

完了済みの低ノイズ途中比較では、tile72 bit-flip・p=0.01の長い16設定が診断flag・未定義0/192で、経験的相対RMSE 10%・20%のgateを通った。
これは16chain・burn-in 6,000・保存60,000・fine ladderの限定結果であり、公開既定の1chainや短い例へ外挿しない。
tile288 depolarizing・p=0.01/0.003の長い16設定は全て精度gate未達で、校正済み設定として推奨しない。
途中結果の利用判断は[低ノイズ利用案内](low_noise_interim_usage_2026-10-23_ja.md)、詳細は[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)、[p=0.01](low_c3t0_result_2026-10-23_ja.md)、[p=0.003](low_c3t1_result_2026-10-23_ja.md)にある。

最後のtile288 depolarizing・p=0.001は最終集約265507が正常終了した。
不足した再現用ログを補った算術照合265519も23:17:49に正常終了し、352設定×192反復の67,584行、11,968比較値、最大絶対差2.220446049250313e-16、分母除外0を記録した。
追加4テストと既存34テストの成功は[復旧結果](cluster_postprocess_recovery_result_2026-10-24_ja.md)と[回収証拠](data_tile_validation_2026-10-17/c3t2_arithmetic_recovery_20261024_v1/receipt.json)にある。
同条件の[review](data_tile_validation_2026-10-17/c3t2_arithmetic_recovery_20261024_v1/c3t2/review/review.json)ではWSSのfull point estimateはnullであり、99.9%区間は約[9.487×10⁻²¹, 3.181×10⁻⁸]だった。
部分和・区間中点を真値に置き換えず、この広い区間との整合を精度や被覆の保証に使わない。

### 保存済み結果への全12条件の対応

下表は既存の9条件比較とC3T0・C3T1・C3T2の保存報告から転記した対応表であり、新しい設定選択や数値再集計ではない。
診断件数は各設定の全192反復を分母とし、範囲は事前固定した長い16設定内の最小値〜最大値で、設定間の反復を合算しない。
長い設定はburn-in 6,000・fine ladderで、tile72 bit-flipのみ16 chain・60,000保存、他の3組合せは8 chain・12,000保存であり、条件間の同費用比較ではない。
C3T1・C3T2の診断欄は長い16設定を含む全352設定について同じ件数が保存されている。

| 条件ID・符号・noise | p | 診断flag /192 | 診断未定義 /192 | 保存済みの説明・参照先 |
|---|---:|---:|---:|---|
| C0T0・tile72 bit-flip | 0.01 | 0 | 0 | 長い16設定は経験的相対RMSE 10%・20%のgate通過。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)、[利用判断](low_noise_interim_usage_2026-10-23_ja.md)。 |
| C0T1・tile72 bit-flip | 0.003 | 192 | 0 | reference全体包含158–182/192と診断警告を併記する。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)。 |
| C0T2・tile72 bit-flip | 0.001 | 192 | 0 | reference全体包含143–180/192と診断警告を併記する。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)。 |
| C1T0・tile288 bit-flip | 0.01 | 192 | 54–68 | referenceとの重なり192/192・全体包含0/192を真値の被覆とは解釈しない。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)。 |
| C1T1・tile288 bit-flip | 0.003 | 192 | 191–192 | referenceとの重なり192/192・全体包含0/192を真値の被覆とは解釈しない。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)。 |
| C1T2・tile288 bit-flip | 0.001 | 192 | 192 | 広いreference区間と長い16設定の経験的精度gate未達を保存。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)、[個別報告](low_c1t2_result_2026-10-22_ja.md)。 |
| C2T0・tile72 depolarizing | 0.01 | 192 | 0 | reference全体包含134–180/192と診断警告を併記する。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)。 |
| C2T1・tile72 depolarizing | 0.003 | 192 | 139–152 | reference全体包含123–180/192と診断警告・未定義を併記する。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)。 |
| C2T2・tile72 depolarizing | 0.001 | 192 | 192 | reference全体包含108–181/192と診断警告・未定義を併記する。[9条件比較](low_long_nine_comparison_result_2026-10-22_ja.md)。 |
| C3T0・tile288 depolarizing | 0.01 | 192 | 192 | 広いreference区間、full point estimate未取得、長い16設定の経験的精度gate未達。[個別報告](low_c3t0_result_2026-10-23_ja.md)。 |
| C3T1・tile288 depolarizing | 0.003 | 192 | 192 | 広いreference区間、full point estimate未取得、全352設定の10%・20%判定は`empirical_above_target`。[個別報告](low_c3t1_result_2026-10-23_ja.md)。 |
| C3T2・tile288 depolarizing | 0.001 | 192 | 192 | 広いreference区間、full point estimate未取得、全352設定で診断警告・未定義を記録。[診断内訳](c3t2_saved_diagnostic_result_2026-10-24_ja.md)、[集約review](data_tile_validation_2026-10-17/c3t2_arithmetic_recovery_20261024_v1/c3t2/review/review.json)。 |

表の12条件には有限WSS reference区間の記録があり、full point estimateの未取得や区間幅の広さをreference自体の欠如とは扱わない。
referenceがない場合、referenceが広いため結論が弱い場合、実測された混合警告がある場合、独立計時が未完了の場合は異なる制約である。
上表の対象設定では区間未取得は0/192だが、区間を取得したことやreferenceとの重なりを名目95%被覆の保証にしない。
診断未定義192/192は各反復が少なくとも一つの未定義診断を含む意味であり、全観測量が未定義とは限らない。
独立計時候補に選ばれない条件・設定も元の校正は計算済みであり、非選択を校正未計算と記載しない。
元352設定ずつの評価は受理済みselectionに保持される一方、本表は固定切り口を中心とする索引であり、全candidateのbias・RMSE・被覆・非選択理由を展開した表ではない。
全candidate評価と独立計時を結合した最終JSONは未取得であり、生成後に`selection.rows[*].candidates[*].assessment`と計時`records`の条件・件数・由来を照合する。
選択用cohortの評価を新しい独立校正へ読み替えず、独立計時48行・各192分母の完了と費用比較は後続reportの受入を待つ。
参照文書に残る当時の9/12・10/12などの進捗表現は履歴であり、本稿冒頭の現況とは区別する。

### 受理済みselectionの24行表

qsub265706はF/0・run_count=1・walltime20秒で完了し、元acceptanceが受理したselectionの値を再選択・数値再計算なしで[24行表](data_tile_validation_2026-10-17/accepted_selection_projection_v1_20261025/evidence/results/selection-projection_ja.md)へ射影した。
[JSON](data_tile_validation_2026-10-17/accepted_selection_projection_v1_20261025/evidence/results/selection-projection.json)は原fieldへの対応、選択設定、bias・RMSE範囲、被覆件数、診断、非選択理由と各192分母を保持する。
先行fixtureはqsub265705で18件成功し、実射影は同じ受理済みsourceを用いた。
PBS内で元selectionの前後hash・stat一致を確認し、元5 GB result・raw traceは再読していない。

tile72 bit-flipとtile72 depolarizingの各p=0.01・0.003・0.001、目標相対RMSE 10%・20%の計12行は`selected`だった。
ただし選択された校正cohortは全12行で診断flag=192/192であり、選択時の`diagnostics_filter_applied`と`coverage_filter_applied`はいずれもfalseだった。
この選択は独立計時に渡す候補の決定であり、混合・名目95%被覆を確認した推奨設定ではない。
上の固定long16の表と選択設定は異なるため、tile72 bit-flip・p=0.01のlong16の診断flag=0をこの候補へ移さない。
tile288 bit-flipとtile288 depolarizingの計12行は`ineligible_reference_width`で、選択設定と選択品の指標をnullのまま保存した。
広いreference区間による選択対象外を、校正未計算・reference自体の不存在・独立計時の失敗と解釈しない。
射影値は設定選択に用いたcohortの評価であり、新しい独立校正ではなく、独立計時48行と各192分母・最終reportの確認は未完了である。

[保存説明と受入証拠](data_tile_validation_2026-10-17/accepted_selection_projection_v1_20261025/README_ja.md)にはqsub・source・request・回収pinと、識別子置換前後のSHA-256を記録した。
小成果物はworking treeへ保存したもので、GitHub公開済みとは扱わない。
全12条件のcomparisonはcontrollerが受理しhandoffへ進み、selection24行も小射影として確認したが、後段reportとの対応照合・独立計時・最終の推奨設定表はまだ確定できない。
処理未完了による証拠不足と、完了済み計算で精度gateを満たさなかった科学的な否定結果を区別する。
全12workerのPBS正常終了や限定fixtureの成功を、全12条件の深い科学的受理へ読み替えない。

### 独立計時の運用費用と推定器の費用

今回の初期準備265709のPBS walltimeは3時間00分53秒、先頭容量MC265712は7分16秒、BAR265714は7分24秒だった。
正式受理と本計時計画の生成を含むfinish265716は41分27秒、265718は41分36秒だった。
先頭MC本計時265721のPBS walltimeは26分53秒であり、この値も推定器のtask費用とは分ける。
先頭BAR本計時265723は要求walltime30分に対して実PBS walltime29分52秒で終了したが、後続条件の予算内完了や十分な予算余裕を保証するものではない。
BARのtask・pool費用と精度gateは今回の小原本監査の対象外であり、MC/BARのPBS walltimeから同精度での優劣を判断しない。
結果照合済みのMC本計時4群について、192反復それぞれの費用metadataとsummaryの合計は一致した。
下表は保存値を小数第3位へ丸めたもので、poolとoutside poolの合計はexecution wallに対応する。

| MC計時群と結果監査 | PBS walltime | execution wall（秒） | pool wall（秒） | outside pool wall（秒） | task CPU合計lower bound（秒） |
|---|---:|---:|---:|---:|---:|
| [c0t0e0・265721](../../output/census_active_node_migration_v1/MC_MAIN_RESULT_AUDIT_ja.md) | 26分53秒 | 1610.983 | 29.472 | 1581.511 | 572.762 |
| [c0t0e1・265737](../../output/census_active_node_migration_v1/MC_E1_MAIN_RESULT_AUDIT_ja.md) | 28分13秒 | 1690.903 | 113.350 | 1577.553 | 2218.509 |
| [c0t1e0・265753](../../output/census_active_node_migration_v1/MC_T1E0_MAIN_RESULT_AUDIT_ja.md) | 33分49秒 | 2027.203 | 459.797 | 1567.405 | 9003.335 |
| [c0t1e1・265770](../../output/census_active_node_migration_v1/mc-t1e1-main-result-audit-1792971680426190900/audit.json) | 56分07秒 | 3365.589 | 1815.808 | 1549.781 | 36237.504 |

task CPU合計は記録上のlower boundであり、wall時間や全工程のCPU費用と同一視しない。
c0t1e1の記録にはtask wall合計lower bound36353.431秒、parent peak RSS10507.652 MiBもあり、並行taskの合計と実経過時間、parentの最大RSSを区別する。
outside pool全体を特定の検証処理へ帰属させたり、費用・精度gateの照合前にBARと比較したりしない。
この表は計時記録の整理であり、4群が同じ設定・精度であることや、最終科学検証・全正式finishの完了を意味しない。
MC265721のqsub・manifest・scriptへの結合と、BAR投入前helperと合わせた2物理ノード内の割当は[投入時の独立監査](../../output/census_outer_operation_v1/MAIN_ALLOCATION_2026-10-25_ja.md)に記録した。
これらは[状態文書](PROJECT_STATUS_2026-10-24_ja.md)、[MC finish監査](../../output/census_active_node_migration_v1/MC_CAPACITY_FINISH_AUDIT_ja.md)、[BAR finish監査](../../output/census_active_node_migration_v1/BAR_CAPACITY_FINISH_AUDIT_ja.md)に記録された個別PBS jobのwalltimeであり、推定器のtask wallやCPU時間とは異なる。
運用処理にはsnapshot入力の再検証・hash照合・本計時manifest生成などの準備・検証費用があり、[固定sourceの静的確認](../../output/finite_tail_census_recovery_v1/INDEPENDENT_FINISH_CALLGRAPH_ja.md)でも反復した入力検証を確認している。
[投入・実行経路の静的確認](../../output/finite_tail_census_recovery_v1/INDEPENDENT_SUBMIT_CALLGRAPH_ja.md)では、main投入前のinputs呼出しは12回（capacityでは4回）、計測本体では7回（capacityでは2回）であり、capacity由来の共通overheadと安全倍率がmain固有の検証費用を覆うかは実計測で確認する必要がある。
投入前helperの検証は別PBS時間枠であり、この呼出し回数を実時間・物理I/O量・本計測の時間超過へ読み替えない。
PBS walltime全体をsamplingやdecoderの時間に帰属させず、この部分実測から全体総時間・未計測の後続費用・MC/BARの優劣・終了時刻を推定しない。
同じ精度での効率評価には、後続の独立192反復と最終reportに保存する費用定義・精度gateの照合が必要である。

### 独立計時の最終report（2026-10-29 02:21 JST受理）

独立計時48手法行（12選択条件×MC/BAR×capacity・main、`c2t2e1` MC mainは2分割）は2026-10-28 11:04 JSTに全件terminal・exit 0となった。
凍結report scriptの`reference_evidence`は、受理済みselectionの12 calibration bindingsのうち復旧・portable readerに由来する9件を、参照audit reportの`source_sha256`のpath接頭辞（v7→v11）の違いだけで拒否した。
所有者の決定により、v13の凍結鎖は触らず、同じreport scriptに1箇所のdelta（移設後のsource一覧で差し替えたreportのdigestも受理する）を当てたreport環境v2を別経路で実行した。
経路・delta・job ID・所要時間の記録は[並列化の記録](independent_parallel_execution_2026-10-26_ja.md)にある。
report job 265940は2026-10-29 01:58 JSTにexit 0・PBS walltime 9時間43分で終了し、seal補助job 265950（最初の補助jobはメモリ上限で失敗）の受理後に`report.json`（1,848,735,353 bytes、SHA-256 `79d1357d…`）と`report_ja.md`（SHA-256 `3614ab8f…`）を確定した。
手元の写しは[report_ja.md](data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/report_ja.md)、[report.json.gz](data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/report.json.gz)、[条件別の抜粋](data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/condition_summary.json)、[経路の完了記録](data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/completed.json)にあり、展開後のSHA-256は`completion.json`と一致する。
v13 journalの`parallel-flow-v13/completed.json`と`finite-final-report.json`は書いていない。
v13のreport_job役末尾の結果写し検証（`collection_verified`）とfinal-report役の受領書に相当する検査は、別経路の`collection.json`・`final-receipt.json`で同じbyte照合として行ったが、v13 configに束ねたfinal-report役そのものは未実行である。

下表は`report.json`の`records`から転記した選択12条件の値で、数値の再計算は行っていない。
費用は192反復のtask単位の平均（秒）で、capacity・seed監査・選択・報告処理の費用は含まない。
相対RMSEは有限WSS reference区間に対する範囲、精度判定は凍結scriptの経験的gate（相対RMSE ≤ ε）、被覆は192反復中にreference区間全体（entire）・可能区間（possible）を含んだ件数である。

| case | p | ε | 手法 | 状態 | task wall 平均（秒） | CPU 平均（秒） | 相対 RMSE 範囲 | 精度判定 | entire 被覆 /192 | possible 被覆 /192 |
|---|---:|---:|---|---|---:|---:|---|---|---:|---:|
| 0 | 0.01 | 0.2 | MC | completed | 2.996 | 2.983 | [0.1951, 0.1952] | within_target | 185 | 185 |
| 0 | 0.01 | 0.2 | BAR | completed | 14.979 | 14.865 | [0.2061, 0.2063] | above_target | 160 | 160 |
| 0 | 0.01 | 0.1 | MC | completed | 11.594 | 11.555 | [0.1065, 0.1066] | above_target | 181 | 181 |
| 0 | 0.01 | 0.1 | BAR | completed | 39.140 | 38.768 | [0.0970, 0.0971] | within_target | 168 | 169 |
| 0 | 0.003 | 0.2 | MC | completed | 47.045 | 46.892 | [0.1951, 0.1951] | within_target | 183 | 183 |
| 0 | 0.003 | 0.2 | BAR | completed | 23.232 | 23.016 | [0.1896, 0.1896] | within_target | 162 | 162 |
| 0 | 0.003 | 0.1 | MC | completed | 189.341 | 188.737 | [0.0955, 0.0955] | within_target | 183 | 183 |
| 0 | 0.003 | 0.1 | BAR | completed | 62.566 | 62.259 | [0.0766, 0.0766] | within_target | 162 | 162 |
| 0 | 0.001 | 0.2 | MC | completed | 492.476 | 490.864 | [0.2015, 0.2015] | above_target | 183 | 183 |
| 0 | 0.001 | 0.2 | BAR | completed | 24.506 | 24.270 | [0.2404, 0.2404] | above_target | 158 | 158 |
| 0 | 0.001 | 0.1 | MC | completed | 1928.440 | 1922.762 | [0.0948, 0.0948] | within_target | 184 | 184 |
| 0 | 0.001 | 0.1 | BAR | completed | 65.032 | 64.700 | [0.0870, 0.0870] | within_target | 175 | 175 |
| 2 | 0.01 | 0.2 | MC | completed | 6.493 | 6.468 | [0.1874, 0.1879] | within_target | 183 | 183 |
| 2 | 0.01 | 0.2 | BAR | completed | 27.493 | 27.311 | [0.2185, 0.2197] | above_target | 166 | 166 |
| 2 | 0.01 | 0.1 | MC | completed | 25.914 | 25.820 | [0.1048, 0.1056] | above_target | 181 | 181 |
| 2 | 0.01 | 0.1 | BAR | completed | 104.814 | 104.349 | [0.0688, 0.0696] | within_target | 173 | 176 |
| 2 | 0.003 | 0.2 | MC | completed | 95.332 | 94.997 | [0.2004, 0.2005] | above_target | 178 | 178 |
| 2 | 0.003 | 0.2 | BAR | completed | 42.760 | 42.460 | [0.2063, 0.2063] | above_target | 161 | 161 |
| 2 | 0.003 | 0.1 | MC | completed | 382.497 | 381.284 | [0.1003, 0.1004] | above_target | 184 | 184 |
| 2 | 0.003 | 0.1 | BAR | completed | 119.599 | 119.047 | [0.0948, 0.0948] | within_target | 161 | 161 |
| 2 | 0.001 | 0.2 | MC | completed | 963.081 | 960.094 | [0.1809, 0.1809] | within_target | 186 | 186 |
| 2 | 0.001 | 0.2 | BAR | completed | 76.630 | 76.029 | [0.2057, 0.2058] | above_target | 151 | 151 |
| 2 | 0.001 | 0.1 | MC | completed | 3848.629 | 3837.132 | [0.1013, 0.1013] | above_target | 183 | 183 |
| 2 | 0.001 | 0.1 | BAR | completed | 204.073 | 203.143 | [0.0856, 0.0856] | within_target | 164 | 164 |

凍結reportの費用比MC/BARは、両手法が精度gateを通った3条件にだけ出る。
右2列の「参考」は本稿の編集で計算した精度正規化比（task費用×(相対RMSE範囲中点/ε)²のMC/BAR）であり、凍結reportの値ではなく、BARの費用がεに対してMCと同じ指数で伸びることも未検証である。

| case | p | ε | 凍結reportの比 wall MC/BAR | 同 CPU | 理由 | 参考: 精度正規化比 wall | 参考: 同 CPU |
|---|---:|---:|---:|---:|---|---:|---:|
| 0 | 0.01 | 0.2 | — | — | both_empirical_precision_gates_required | 0.18 | 0.18 |
| 0 | 0.01 | 0.1 | — | — | both_empirical_precision_gates_required | 0.36 | 0.36 |
| 0 | 0.003 | 0.2 | 2.03 | 2.04 | — | 2.15 | 2.16 |
| 0 | 0.003 | 0.1 | 3.03 | 3.03 | — | 4.70 | 4.71 |
| 0 | 0.001 | 0.2 | — | — | both_empirical_precision_gates_required | 14.12 | 14.21 |
| 0 | 0.001 | 0.1 | 29.65 | 29.72 | — | 35.16 | 35.24 |
| 2 | 0.01 | 0.2 | — | — | both_empirical_precision_gates_required | 0.17 | 0.17 |
| 2 | 0.01 | 0.1 | — | — | both_empirical_precision_gates_required | 0.57 | 0.57 |
| 2 | 0.003 | 0.2 | — | — | both_empirical_precision_gates_required | 2.11 | 2.11 |
| 2 | 0.003 | 0.1 | — | — | both_empirical_precision_gates_required | 3.58 | 3.59 |
| 2 | 0.001 | 0.2 | — | — | both_empirical_precision_gates_required | 9.72 | 9.77 |
| 2 | 0.001 | 0.1 | — | — | both_empirical_precision_gates_required | 26.44 | 26.48 |

読み取れることは次のとおりである。

- 選択12条件はMC・BARとも192/192がcompletedで、failed・unavailableは0である。
- 凍結reportの費用比が出た3条件（case 0のp=0.003・0.001）はいずれもBARが安く、MC/BARは2.03・3.03・29.7である。
- 残り9条件は片方または両方の相対RMSEがεを上回り（MCが6条件、BARが5条件、両方が2条件）、比はNoneである。gateは点比較で、192反復から求めたRMSEの相対標準誤差（正規近似で約5%）を考慮しない。超過11件のうち7件は1 SE以内の境界上で、明確に外れているのはcase 0・p=0.001・ε=0.2のBAR（0.240、+20%）とcase 2・p=0.01・ε=0.2のBAR（+9.6%）である。9条件を一括して「精度未達」とは書かない。
- 比の有無にかかわらず、task費用にはp依存のクロスオーバーがある。p=0.01の4条件ではMCがBARより安く（正規化なしで約5倍、精度正規化で2〜6倍）、p=0.003でBARが2〜5倍、p=0.001でBARが10〜35倍安い。
- 「BARが2〜30倍速い」という記述はp=0.003以下に限った主張であり、p=0.01では直接MCで足りることを併記する。
- 被覆はMCが178〜186/192（約93〜97%）、BARが151〜176/192（約79〜92%）で、BARの区間は名目95%に届かない。独立計時ではBARの混合診断を取得していないので、この過小被覆を診断flagと結び付けた説明はできない。

9条件の扱いについて、所有者は2026-10-29に、再実行せず、凍結reportのgate規則と比の定義を変えないまま、論文の「目標精度に達するまでの時間」と同じ趣旨の精度正規化費用C_ε = C×(r/ε)²を別の量として定義し、全12条件を示す方針を選んだ。
定義・bias分解・条件別の値・適用限界は[精度正規化のMC/BAR費用比較](low_noise_cost_comparison_2026-10-29_ja.md)にある。
正規化比はp=0.01で0.17〜0.57（MCが安い）、p=0.003で2.1〜4.7、p=0.001で10〜35（BARが安い）であり、凍結reportの比が出た3条件では凍結の比と同じ向きである。
case 2・p=0.001・ε=0.2のBARは相対bias −0.143がMSEの48%を占め、biasを数えるかどうかで正規化比が9.7と18.8に分かれるので、この条件は個別に注記する。

## 4. 利用例と再現資料

公開資料、private snapshot、生データの取得起点と未提供項目は[再現資料の取得監査](reproduction_access_inventory_2026-10-25_ja.md)を参照する。
private保存物の存在を第三者が取得可能な配布物と同一視せず、未確認の提供条件や保存期限を推測しない。
[全12条件と主独立計時のraw取得索引](raw_access_followup_2026-10-25_ja.md)には、各workerの実prepared世代、既存の保管先・pin・回収時の検証と、今回の限定した所在確認を区別して保存した。
19:12:06 JSTにはportable7条件の指定273 ZIPについて、全件の通常file・非symlinkとしての現存、欠落・未観測各0、stat容量合計42,880,266,375 bytesを確認し、[小観測原本](portable_zip_stat_observation_2026-10-25.json)を保存した。
ZIP本体は読まず、過去の内容hashと現在bytesの一致、全raw容量、archiveの完全性や第三者取得可能性はこの限定statでは検証していない。
今回の監査で原本の消失が判明した例はなく、全rawの現bytesを再照合していないことを消失・未保存とは判定しない。

利用開始時は[英語API](../api_en.md)、[英語チュートリアル](../tutorial_en.md)、[基本decoder比較例](basic_decoders_usage_2026-10-18_ja.md)、[英語の検証状況](../tile_validation_interim_en.md)を参照する。
追加decoderの契約・受入範囲は[基本decoder検証](basic_decoders_validation_2026-10-18_ja.md)にある。
現working treeのAPI・利用例と保存済み受入の対応は次のとおりであり、APIの適用可能性、有限入力の受入、科学的な校正を区別する。

| decoder・実API | 符号・noiseと利用例 | 保存済みの確認範囲・適用限界 |
|---|---|---|
| 固定BP-OSD：`bposd_decoder` | tile72=`make_tile_code(6,6)`、tile288=`make_tile_code(12,12)`のbit-flip。[tile workflow](../../examples/workflows/tile_capacity_fixed_prior.py)の`--size 6/12 --noise bit`。 | 目標pをpriorに固定し、min-sum・100反復・OSD-CS order10でanchor・全rung・独立MCに同じProblemを使用。主4条件と低ノイズの科学的評価は第2・3節の該当条件に限定する。例の短いtraceは校正設定ではない。 |
| 固定BP-OSD sector版：`depolarizing_bposd_decoder` | 同じtile72/288のjoint depolarizing。同workflowの`--size 6/12 --noise depolarizing`。 | 物理目標pに対してsector priorを2p/3に固定。独立X/Z復号はdecoderの近似であり、I/X/Y/Zの物理分布とY相関を保持する。科学的評価と利用例の受入を区別する。 |
| BP-LSD：`bplsd_decoder` / `depolarizing_bplsd_decoder` | CSSのX/Z sectorとdepolarizing sector版。[比較例](../../examples/decoder_comparison.py)はSteane・toric d=3・tile72のbit-flip。 | order0のみ。Steaneの全syndrome・全128状態とsector合成、toric・surface・Hamming HGP・BB72・tile72/288の固定少数X/Z入力を受入。zero syndromeは恒等補正とする明示規則を保持。tile72/288のjoint depolarizingを含むBAR混合・bias・被覆・速度順位は未校正。 |
| BeliefFind：`belief_find_decoder` / `depolarizing_belief_find_decoder` | 既定inversionは次数0列のない一般CSS、peelingは各列次数1または2。同比較例はSteane・toric d=3・tile72のbit-flipでinversionを使用。 | Steane・toricの全syndrome、toric・surfaceのpeeling、Steaneのsector合成、Hamming HGP・BB72・tile72/288の代表X/Z入力を受入。tileをpeelingへ渡さない。追加decoderとしてのBAR混合・bias・被覆・速度順位は未校正。 |
| 単独Union-Find：`union_find_decoder` / `depolarizing_union_find_decoder` | 既定peelingはgraphlike CSS、inversionは次数0列のない一般CSS。同比較例ではtoric d=3のbit-flipにpeelingを使用。 | toric d=2・surface d=2の全syndrome、Steane inversion、surfaceのdepolarizing sector組合せを受入。非重み付きでpriorを用いず、`ldpc==2.4.1`・`bits_per_step=1`に限定。tileのpeelingは対象外、inversionの一般CSS対応をtileの科学校正済みとは扱わない。 |

追加3decoderの単sector APIは`errors="X"`でbit-flip、`errors="Z"`でphase-flipへ接続し、depolarizingには各`depolarizing_*_decoder`を使う。
BP-LSD・BeliefFindのp引数は固定binary sector priorであり、物理depolarizing確率qに合わせる場合は2q/3を明示する。
各factoryは補正のbinary形状・Hc=sを検査し、不正補正やbackend例外を論理成功として扱わない。
比較例のBP-OSD baselineはorder0であり、本tile校正のorder10と同じdecoderではない。
同例のSteane exactと短いdirect MC、有限入力での再呼出し検査は、別OSでの決定性、追加decoderの精度・速度順位・BAR被覆を保証しない。
追加decoderへBP-OSDの校正結果を移さず、研究利用ではdecoderごとの固定環境・failure集合と独立referenceを必要とする。

2026-10-25の文書照合では、追加decoderの実装3本・共通補正検査・受入test4本・比較例の計9ファイルが[保存済み受入のinput hash](data_basic_decoders_2026-10-18/current_worktree_binding_2026-10-18_v1.json)と一致した。
tile workflowも[CLI受入のexample hash](tile_example_target_cli_acceptance_2026-10-25.json)と一致した。
これは現在の小sourceと既存証拠の対応確認であり、テスト・科学計算・native環境の再検証は実施していない。

tile固定prior workflowには `--ladder P0,P1,...` を追加し、末尾の物理確率を目標pとしてbit-flipではp、depolarizingでは2p/3のdecoder priorをanchor・全rungに固定できる。
省略時の旧size別ladderと目標を維持し、qsub265640で契約23件・既存default1件、目標0.025のtile72 bit/depolarizing実CLIを受入済みである。
このCLI追加の受入ではtile288の実native再実行は行っておらず、両sizeの結線は契約テストの範囲である。
[CLI受入と適用限界](tile_example_target_cli_acceptance_2026-10-25_ja.md)に記録したとおり、READMEの目標0.01は構文例であり、その数値実行・正式selection・低ノイズ精度校正の受入ではない。
この追加は公開commitとv8共有snapshotより後の変更であり、公開済み・同snapshotへ保存済みとは扱わない。

本計測を再現する際は符号・joint noise・failure定義・固定prior・decoder設定・native binary・thread数・seed群・初期化・kernel・ladder・trace長・burn-in・chain数・誤差法を固定する。
事前計画は[tile検証計画](tile_validation_plan_2026-10-17_ja.md)、保存データの限界と監査範囲は[tile中間報告](tile_validation_report_2026-10-18_ja.md)にある。
主4条件について、過去の集計が実際に消費したtrace・anchorのhashを完全には再構成できない制約がある。
後日のpayload照合を、過去の集計時点にその入力を固定・消費した証明へ置き換えない。
未収束・診断未定義・区間未取得を分母から除外せず、未収集の診断と実測された警告を区別する。
公開用証拠では識別子を置換し、原本hashと置換後hashのどちらを示すかを明記する。
重い処理は外部計算機で実行し、クラスタはqsubと共有lockで最大2物理ノード×各96コア（最大192コア）を守る。
同じ物理ノード上の複数ジョブを許可し、待機中の固定配置予約もCPU・メモリ上限に含める。
ローカルPCで計算ジョブを実行しない。

## 5. 最終化に必要な受入項目

| 残項目 | 完了を示す証拠 |
|---|---|
| 比較処理の復旧・全件census | 元12terminal、merge265660・acceptance265661とv12のcomparison・handoffを保持してv13へ接続済み。全件census265703とseal265707・collect265708のF/0、全4,208,002件の結果と正式受理・保存を確認した。旧265675などの失敗記録は履歴として保持し、後続計時・最終reportの完了とは区別する。 |
| 全12条件比較 | 元PBS受理とv12 comparisonの全12条件受理を確認済み。原本入力の12×352設定×192 seed＝811,008基礎行と正式selection24行を区別して後段reportへ結合し、有限reference幅、未達・未定義・未取得を含む分母と保存範囲を確認する。 |
| 独立計時 | 2026-10-28 11:04 JSTに48手法行が全件terminal・exit 0（第3節末尾）。以下は2026-10-26時点の記述である。全48手法行を保持した初期準備とcapacity manifest24件を生成済み。先頭MC/BAR容量計測各2/2とそのfinishは正式受理済み。先頭本計時MC265721・BAR265723はF/0で、小要約はともに192/192・failed/unavailable各0。MCの192個別record・費用・実PBS結合と18:56:40 JSTの正式finish受理・回収は監査済み。BARは投入・終端・小要約の指定pin/run root対応と19:27:29 JSTの正式finish受理・回収を監査済みだが、個別record・費用・full summaryの独立照合は未実施。両receiptはscientific_validation_complete=falseを保持する。全48行・各192分母、精度gate・費用比較と非選択等の理由の最終確認は未完了で、diagnostic_not_collectedを実測警告と混同しない。 |
| 最終報告 | 2026-10-29 02:21 JSTにreport job 265940の`report.json`・`report_ja.md`を別経路（report環境v2、1箇所のdelta）で受理し、報告hash・sealed descriptor・経路の完了記録と写し検証を照合した（第3節末尾）。v13 configに束ねたfinal-report役の受領書は未実行で、推奨の根拠と適用限界、9条件の扱いの最終文面は未確定。 |
| source・metadata保存 | v5・v8・[v9追加保存](finite_flow_v9_snapshot_acceptance_2026-10-25_ja.md)・[v11差分](finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md)・[v12差分](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)を保持し、[v13復旧差分](finite_flow_v13_delta_snapshot_acceptance_2026-10-25_ja.md)のsource参照92件・metadata217件をPBS265701でprivate保存した。v13 snapshot内の265700観測は10:19:22 JSTのR状態であり、その後の準備完了や後続計時・最終科学proofの保存は含まない。最終科学証拠、公開資料化、全rawの保存、科学的な完全再現は別に判定する。 |
| 再現可能な保存 | 生データ索引・環境・source/native hash・seed・設定・script・ジョブ台帳・回収receipt、原本と公開用コピーの対応、利用例と最終設定表へのリンクを確認する。科学的な完全再現は未達である。 |

[分割集約から最終報告への接続](low_partition_report_result_2026-10-23_ja.md)は準備・fixture受入の記録であり、本番結果の完了証拠を代替しない。
front v6・merge-parallel-v2・元tailの科学契約と、v12 comparisonを継承するv13 finite outerの完了条件は[最終成果物監査](final_deliverable_audit_2026-10-24_ja.md)にあり、実configと起動pinは[再開記録](cluster_resident_resume_2026-10-25_ja.md)で確認する。
主4条件の有限MC referenceを真値と扱わず、独立referenceがない領域のWSS整合を精度や被覆の保証にしない。
対象なしや実行不能が事前規則で正当化される場合は、その理由と分母を保存し、行を黙って削除しない。
最終的に精度未達・非推奨となる設定が残っても、その結論を記録した検証として報告する。
独立referenceが十分でない領域では設定間整合を精度・被覆の保証へ読み替えない。
保存の完了条件は、必要な原本・設定・環境・seed・実行scriptの保存、取得可能性を示す索引、再現手順、欠落と適用限界の確認である。
別環境で全科学計算を再実行して一致を検証することや、全rawを無条件で公開することは、保存作業とは別の未実施検証・公開判断として扱う。
この区別を理由に必要なsourceや入力の保存不足を省略したり、小規模snapshotだけで全原本の保存を宣言したりしない。
全項目の証拠確認が終わるまでgoalは未完了である。

2026-10-25の草案レビューでは、主4条件の固定切り口、独立MC試行数、主計時の精度gate・費用比・被覆、低ノイズの途中結果と最後の条件の算術照合値を、参照した小報告・JSONへ独立に照合した。
転記と解釈の必須訂正は見つからず、条件間の計算予算の違いを明示するためchain数・保存数の表を追加した。
この点検は保存済み報告との整合確認であり、rawの再解析・新しい科学計算・未完了の全12条件の最終結論や独立計時の代わりではない。
