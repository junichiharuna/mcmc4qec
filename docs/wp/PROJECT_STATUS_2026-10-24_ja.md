# mcmc4qec：2026-10-24の継続状態

## 2026-10-29 02:21 JSTの独立計時完了と最終report受理

独立計時48手法行は2026-10-28 11:04 JSTに全件terminal・exit 0となり、v13 controllerの代わりに動かした並列driverの記録は[並列化の記録](independent_parallel_execution_2026-10-26_ja.md)にある。
v13のreport段は最初の役で`selection and evaluation WSS audit differ`により失敗した。
原因は受理済みselectionの復旧由来9 bindingsが参照audit reportの`source_sha256`のpath接頭辞（v7→v11）だけで凍結scriptの照合に落ちることで、所有者の決定により同じscriptに1箇所のdeltaを当てたreport環境v2を別経路で実行した。
report job 265940は2026-10-29 01:58 JSTにexit 0・walltime 9時間43分で終了し、seal補助job 265950の受理後に`report.json`（SHA-256 `79d1357d…`）と`report_ja.md`（SHA-256 `3614ab8f…`）を確定した。
別経路の完了記録・写し検証・受領書は`report-job-v2/{completed,collection,final-receipt}.json`で、v13 configに束ねたfinal-report役は未実行、v13 journalの完了markerは書いていない。
選択12条件はMC・BARとも192/192がcompletedで、凍結reportの費用比MC/BARは精度gateを両方通った3条件（case 0のp=0.003・0.001）で2.03・3.03・29.7である。
残り9条件は片方の相対RMSEがεをわずかに上回って比がNoneだが、task費用ではp=0.01でMCが安く、p=0.003以下でBARが安いクロスオーバーがある。
条件別の表と読み取りは[最終報告草稿の第3節末尾](final_validation_report_draft_2026-10-24_ja.md)、原本の写しは`data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/`にある。
残るのは9条件の扱いの判断、最終科学証拠のsnapshot保存、再現資料の照合、クラスタ上の実行rootの整理である。

## 2026-10-26 09:12 JSTのBAR本計時正常終了

`c0t1e1-bar-main0` の科学job265772はfresh PBSでF/0・run_count=1・38分18秒を確認した。
同じrun directoryの小summaryは192反復すべての記録、failed=0、unavailable=0を報告した。
full summaryは99,580,446 bytesで4 MiB上限を超えるためremoteに保持し、回収・再読・hashは未実施である。
個別記録の重複・欠落、full summaryのmanifest/job対応、全計算コストの整合、precision gateは未確認で、小summaryの所在だけを完全な科学検証とは扱わない。
範囲と原本pinは[BAR本計時の結果監査メモ](../../output/census_active_node_migration_v1/BAR_T1E1_MAIN_RESULT_AUDIT_ja.md)に保存した。
audit原本SHA-256は `9179c3b4b2f71b637cd144768c8d1da9041803e884709aadccff723176a47749` である。
正式finish監査案は未知job番号をUNSETとして実行を止める状態で準備済み・未実行であり、本計時の正式受理は6/24件のままである。

## 2026-10-26 08:59 JSTのメモリ診断結果

qsub診断job265775はF/0・run_count=1・1秒で終了し、合成fixture12件は0.009秒で成功した。
対象BAR本計時265772は観測前後で同一executionのRを確認したが、compute SSHが255で失敗し、process別RSS/PSSは未取得、samplesは空だった。
PBS記録のmemは7,608,952 kb（約7.26 GiB）であり、集計scopeや全履歴の最大同時使用量は断定できず、予約削減の根拠にはしない。
投入前の2回のfresh gate観測ではBAR・finish helper・診断を合わせて2物理ノード内、各96 CPU・340 GiB以内だった。
回収小metadataのhashとrequest・policy・admission・submission・実PBSの対応は[診断メモ](../../output/independent_memory_probe_v1/PBS_PROBE_2026-10-26_ja.md)に記録した。
memory原本SHA-256は `c01debda6d97e8019ba2175843857462e96ffa3bd70edcf6a3bb4cfa37ae5cef` で、診断処理の正常終了とprocess実測の未取得を区別する。
次ジョブ内のlocal proc monitorは準備中・未実行であり、本計時の正式受理は6/24件のままである。

## 2026-10-26 08:41 JSTのMC本計時結果監査

`c0t1e1-mc-main0` の科学job265770は実PBSでF/0・run_count=1・56分07秒を確認した。
結果collectorとverifierは192反復全件のok・推定値available、重複・欠落なし、manifest・terminal・計算コストの対応を確認した。
full summaryは3,176,184 bytes、原本SHA-256は `ebf9ceaedf7bb675afe7b344f5a2a770bdff9eb2d92addcfb1334d7667fa568b` で、4 MiB以内の全記録を監査した。
execution wallは3365.589183917269秒、pool wallは1815.8080099485815秒、outside pool wallは1549.7811739686877秒だった。
既知task CPU時間の下限は36237.50418158299秒、既知task wall時間合計の下限は36353.43116008863秒、parent peak RSSは10507.65234375 MiBだった。
ジョブ内終了記録の状態Rとは区別してfresh qstatのF/0で終端を確認し、科学rawの再読・推定値の再計算は行っていない。
詳細と原本pinは[MC本計時の結果監査メモ](../../output/census_active_node_migration_v1/MC_T1E1_MAIN_RESULT_AUDIT_ja.md)に保存した。
監査原本は `output/census_active_node_migration_v1/mc-t1e1-main-result-audit-1792971680426190900/audit.json`、SHA-256は `430f3541b396600b607e94d297e80bff5752ea3b148832594d0411e7301ea40b` である。
controllerの正式finish受入とprecision gateはまだ未確認であり、本計時の正式受理は6/24件のままで、精度・被覆の保証とは扱わない。

## 2026-10-26 08:33 JSTのMC・BAR本計時の2ノード割当

`c0t1e1-bar-main0` の投入前helper265771はF/0・run_count=1・47分11秒で終了し、科学job265772がqsubで投入され08:31:57 JSTにRへ進んだ。
08:33:03 JSTの割当監査で、state・manifest・intent・submission・script・実PBSの対応と、192反復・1 partition・21 workers・96 CPU・337 GiB・要求1時間の一致を確認した。
全所有activeはMC本体265770とBAR本体265772の別2物理ノードで、各96 CPU・337 GiB、未配置jobと所有Q状態jobなし、親265771解放済みだった。
範囲と科学4pinは[BAR本計時の割当メモ](../../output/census_outer_operation_v1/BAR_T1E1_MAIN_ALLOCATION_2026-10-26_ja.md)に保存した。
監査原本はlocal `output/census_outer_operation_v1/bar-t1e1-main-allocation-1792971182972444900.json`、SHA-256は `fc2a75ab687b46cf6944e837b73181cdcc8b67614b41fcdd40469c7ab889394d` である。
BAR本体rootのexecution-intent・actual-pbs-start・native preflight・summary・failureは同監査時点で未生成で、存在とsizeだけを確認した。
PBSのRと割当を推定器開始・192反復完了へ読み替えず、本計時の正式受理は6/24件のままである。
ローカルでは保存済み小原本の確認と文書更新を行い、追加科学計算・qsub・本番source変更は行っていない。

## 2026-10-26 07:44 JSTのMC本計時投入

`c0t1e1-mc-main0` の投入前helper265769はF/0・run_count=1・45分37秒で終了し、科学job265770がqsubで投入され07:44:20 JSTにRへ進んだ。
割当照合で、state・manifest・intent・submission・script・実PBSの対応と、192反復・1 partition・21 workers・96 CPU・337 GiB・要求2時間が一致した。
確認範囲と原本pinは[MC本計時の割当メモ](../../output/census_outer_operation_v1/MC_T1E1_MAIN_ALLOCATION_2026-10-26_ja.md)に保存した。
全所有activeは科学265770とBAR投入前helper265771（00045-submit）の別2物理ノードで、各96 CPU以内・未配置jobなし・親265769解放済みだった。
監査原本はlocal `output/census_outer_operation_v1/mc-t1e1-main-allocation-1792968288696586100.json`、SHA-256は `4a191fc53991ddcc5c3a8a4f7ca1e203fe0fcd917cd64cb752515764dc5f43cd` である。
submission原本SHA-256は `275be4156e100d1795264645f9af8cb4c01e7a6c6083c0ce7621492de528650c`、scriptは確認済み `cee904d98bcd99ac3ea03172df66404500335ef56f5e654fa894e1de39b9a005` と一致した。
BAR helperはpayloadで `c0t1e1-bar-main0` のsubmitに対応し、07:44:22 JSTのRを確認した。
本体の開始marker・native preflight・summaryは割当監査時点で未生成であり、PBSのRを推定器task開始や192反復完了とは扱わない。
本計時の正式受理は6/24件のままで、ローカルでは小metadataの回収・照合のみを行った。
08:01 JSTの追加観測では科学job265770の開始記録とnative preflightが生成され、job・canonical manifest・投入記録の一致を確認した。
有限なdecoder probeは全mismatchとsyndrome violationが0だったが、単一状態の反復であり普遍的な決定性の証明ではない。
native preflight原本SHA-256は `e829bd854431186ef4e11238e2027f0ecf2494ec5e730a9b899f02c7a3f04567`、小観測は `output/finite_tail_resume_controller_v1/mc-c0t1e1-main-run-markers-1792969304686226400.json` であり、summary・failure・終了記録は同観測時に未生成だった。
08:08 JSTにはBAR本計時のtiming.sh生成を確認し、2,071 bytesの原本と1 node・96 CPU・337 GiB・要求1時間・PBS_JOBID必須の内容を確認した。
原本SHA-256は `371de2bcc098c337e9da0950dd11d7b7ee152639ccd4c36ae00b9f89acbd187b`、local保存は `output/census_outer_operation_v1/c0t1e1-bar-main-reviewed-timing.sh` であり、upstream・intent・submissionと本体job番号は同観測時に未生成・未確定だった。

## 2026-10-26 06:58 JSTのBAR予備計時正式受理と本計時準備

`c0t1e1-bar-capacity` の正式finish265768はF/0・run_count=1・41分37秒で終了した。
小原本19件の照合で、元科学job265764・予備計時結果・資源決定・本計時manifest・親action受入の対応を確認した。
確認範囲と原本pinは[BAR正式受理メモ](../../output/census_active_node_migration_v1/BAR_T1E1_CAPACITY_FINISH_AUDIT_ja.md)に保存した。
監査原本はlocal `output/census_active_node_migration_v1/bar-t1e1-capacity-finish-audit-1792965499771757900/audit.json`、SHA-256は `fe71177afcecfbd3675e5afc105e6cf1d0513a9fc6e9f872a84074ad6945a94e` である。
BAR本計時は192反復・1 partition・21 workers・1 node・96 CPU・337 GiB・要求1時間の計画であり、要求時間を完了予測とは扱わない。
本計時manifest原本SHA-256は `362b25ca031b4aebc7d3a74f46084bcc6be0f95805935bd1d99374276276261d`、資源決定は `dfaa3c7798cf687025f6fb1aca33aa950025cf6a99ddf173414a4db3b25d6137`、正式完了記録は `d420ac9bc6615cd1a16cb9017e3b357c72790c3e6e9d0ae9845d07d9c07d40ae` である。
本計画と予備計時の保存source mapは既存digestと一致し、最大小原本は1,219,753 bytes、capacity summaryは1,041,084 bytesで4 MiB以内だった。
科学rawや実sourceファイルの再hashは行っていない。
state小観測 `output/finite_tail_resume_controller_v1/independent-state-1792965522364835700.json` はterminal14・submitting1・pending17で、次の `c0t1e1-mc-main0` がsubmittingへ進んだ。
terminal14は予備計時8件と本計時6件の合計であり、本計時の正式受理数は6/24件のままである。
MC本計時の科学job IDは同観測で未確定、BAR本計時のsubmission・開始・summaryも受入監査時点で未生成だった。
06:59 JSTには投入前helper265769（00044-submit）のRを確認し、照会原本をlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792965569992048900.json` に保存した。
MC/BAR本体投入後の割当照合collectorは実親job番号と確認済みscript SHAを必須入力として準備・レビュー済みであり、本体投入前のため未実行である。
07:21 JSTにはMC本計時のtiming.sh生成を確認し、主担当が2,068 bytesの原本と計画どおりの資源指定・runner・PBS_JOBID必須を確認した。
原本SHA-256は `cee904d98bcd99ac3ea03172df66404500335ef56f5e654fa894e1de39b9a005`、local保存は `output/census_outer_operation_v1/c0t1e1-mc-main-reviewed-timing.sh` である。
小観測 `output/finite_tail_resume_controller_v1/mc-c0t1e1-main-submit-markers-1792966868061049500.json` ではupstream・intent・submissionは未生成で、本体job番号と実割当はまだ未確認だった。

## 2026-10-26 06:12 JSTのMC予備計時正式受理

`c0t1e1-mc-capacity` の正式finish265766はF/0・run_count=1・41分18秒で終了した。
[小原本の照合](../../output/census_active_node_migration_v1/MC_T1E1_CAPACITY_FINISH_AUDIT_ja.md)で、元科学job265762・予備計時結果・資源決定・本計時manifest・親action受入の対応を確認した。
監査原本はlocal `output/census_active_node_migration_v1/mc-t1e1-capacity-finish-audit-1792962757203704300/audit.json`、SHA-256は `02ceb3a6f2dcf1d60e391843f6a81773be0a23681ad3a04b192bae902842bd72` である。
本計時は192反復・1 partition・21 workers・1 node・96 CPU・337 GiB・要求2時間の計画であり、要求時間を完了予測とは扱わない。
本計時manifest原本SHA-256は `0bab02e17ddefb47d4b8fea60d0336016eb4dd9039a2631a0324151a4b2d984f`、資源決定は `43b30e39a31378a7b6c8db151effeb20b9b121dd28e99cc6180723b7ebb49561`、正式完了記録は `f6a8ca8fbc8ef7d641e29e40c4ed5797cb3562437352a6a0055e8fb82ab28c98` である。
本計画と予備計時の保存source map一致を確認したが、実sourceファイルの再hashや科学rawの再読は行っていない。
監査時点で本計時のsubmission・開始・summaryは未生成であり、本計時の正式受理数は6/24件のままである。
次の終了確認helper265767（00042-observe）は実PBSでR、payloadは `c0t1e1-bar-capacity`・科学job265764を対象としていた。
payloadの小射影はlocal `output/finite_tail_resume_controller_v1/action42-payload-projection-1792962804354837100.json` に保存した。
state-latestには先行段階のfinishing/runningが残っていたため、段階の完了は実PBSと正式受入原本に基づいて判定した。
06:17 JSTにはBAR終了確認265767のF/0・3分43秒と、後続正式finish265768（00043-finish）のRを確認した。
照会原本はlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792963024797768200.json` に保存し、BAR正式受理の照合は終了記録が揃うまで待機する。

## 2026-10-26 05:35 JSTのBAR予備計時終了

`c0t1e1-bar-capacity` の科学job265764はfresh qstatでF/0・run_count=1・8分08秒を確認した。
小要約はplanned/recorded各2件・failed/unavailable各0件・execution_complete/all_estimates_available trueで、原本SHA-256は `8a4bebf23746d5b4b0c610117ce83b222f609562f3a629f21ee8ff124ddb3969` である。
観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792960502419875900.json` と `bar-c0t1e1-capacity-run-markers-1792960504827305200.json` に保存した。
job内のactual-pbs-endはRの記録なので、終了判定は独立したfresh qstatに基づく。
小要約は他の予備計時と同じbytesを持ち、job固有の結合情報を含まないため、hash一致を個別科学結果の完全照合とは扱わない。
MC終了確認helper265765はF/0・3分46秒で終了し、正式finish265766（00041-finish）が実PBSでRへ進んだ。
MC/BAR両方の予備計時本体は終了したが、資源決定・正式finishの受入はまだ確認しておらず、本計時の正式受理は6/24件のままである。
controllerの生存・同一起動識別を `diagnostic-window-observation-1792960513232291900.json` で確認し、MC正式finish用collectorは265766のF/0と受入記録が揃うまで実行しない。

## 2026-10-26 05:27 JSTのMC予備計時終了とBAR開始

`c0t1e1-mc-capacity` の科学job265762はfresh qstatでF/0・run_count=1・10分40秒を確認した。
小要約はplanned/recorded各2件・failed/unavailable各0件・execution_complete/all_estimates_available trueで、原本SHA-256は `8a4bebf23746d5b4b0c610117ce83b222f609562f3a629f21ee8ff124ddb3969` である。
観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e1-capacity-run-markers-1792959713620970100.json` と `independent-state-1792959956462014900.json` に保存した。
小要約にはjob固有の結合情報がなく、個別結果・資源決定・正式finishの受入は未完了であり、本計時6/24件という正式受理数は変更しない。
BAR投入前helper265763はF/0・15分08秒で終了し、科学job265764がqsubで投入され05:26:31 JSTにRへ進んだ。
割当監査はstate・manifest・intent・submission・script・実PBSの対応を確認し、BARの2 CPU・340 GiBとMC終了確認helper265765の1 CPU・96 GiBが別2物理ノードに配置され、各96 CPU以内・未配置jobなし・投入前helper解放済みだった。
監査原本はlocal `output/census_outer_operation_v1/c0t1e1-bar-capacity-allocation-1792960005291700400.json`、SHA-256は `fa74b6683b806cb6389b24d17da233073bcc98f32a6c3b621344885e8455a472` である。
BAR submission原本SHA-256は `32646332be43e708c0f80be562cda2f82b5d1c0e12fde47388db4ffc40b4e2c4` で、開始marker・native preflight・科学summaryは割当監査時点で未生成だった。
controllerの同一起動識別・生存を確認し、元科学計算の再実行やローカル計算ジョブは行っていない。
限定結果の範囲は[MC予備計時メモ](../../output/census_active_node_migration_v1/MC_T1E1_CAPACITY_RESULT_BOUNDARY_ja.md)、BARの原本対応は[割当メモ](../../output/census_outer_operation_v1/C0T1E1_BAR_CAPACITY_ALLOCATION_2026-10-26_ja.md)に保存した。
BAR正式finish用collectorは実job番号・小summary SHAを必須入力として静的準備・独立確認を済ませたが、正式finish未到達のため未実行である。
05:30 JSTにはBAR開始marker・native preflightと既知投入pinの対応を確認し、選択した1状態の有限probeは保存sectorと一致・各不一致0だった。
原本pinと確認範囲は上記BAR割当メモへ追記し、全入力の決定性・科学結果・正式finishの完了とは扱わない。

## 2026-10-26 05:11 JSTの次条件MC capacity投入

`c0t1e1-mc-capacity` の投入前helper265761はF/0・run_count=1・14分42秒で終了し、科学job265762がqsubで投入され05:10:57 JSTにRへ進んだ。
[割当照合](../../output/census_outer_operation_v1/C0T1E1_MC_CAPACITY_ALLOCATION_2026-10-26_ja.md)で、state / manifest / intent / submission / timing.sh / 実PBSの対応を確認した。
全ownerの割当は科学265762の2 CPU・340 GiBと、次のBAR投入前helper265763の1 CPU・96 GiBの別2物理ノードで、各96 CPU以内・未配置jobなし・親265761解放済みだった。
監査原本はlocal `output/census_outer_operation_v1/c0t1e1-mc-capacity-allocation-1792959087814183600.json`、SHA-256は `3b01b25a875ec9da2116a9689246ee17de28a17b7c20bb9ac06aeee316425bcf` である。
manifest原本SHA-256は `5dca6379f05dfd8fc8d828f7bfe80f6e92faa2f95e2c346478c9cd7e918275f9`、submissionは `9fe17e2a4827c35c274504905da9bc4c19863d76c9d3ded6905c79272f766d07` である。
開始markerとnative preflight、科学summaryは監査時点では未生成であり、Rのみで推定器task開始や結果取得を認定しない。
capacityは本計時ではないため、正式受理済み本計時は6/24件のままである。
05:15 JSTにはexecution-intent・actual-pbs-start・native preflightの生成を確認し、job265762・manifest canonical digest・既知script / intent / submission pinとの対応を確認した。
native preflight原本SHA-256は `5d51051d16ce117b9a1abf79efb488c0dc59dc4a23b38aba9b77b5ee3166b033` で、保存sectorへの一致と有限probeの各不一致0だった。
これは選択した1状態の反復確認であり、普遍的なdecoder決定性の証明ではない。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e1-capacity-run-markers-1792959310976456500.json` に保存し、科学summaryと終了記録は同時点で未生成だった。

## 2026-10-26 04:56 JSTのBAR正式受理と次条件への移行

BAR本計時265755の正式finish265760はF/0・run_count=1・22分58秒で終了し、[小原本の受入照合](../../output/census_active_node_migration_v1/BAR_T1E0_MAIN_FINISH_AUDIT_ja.md)を完了した。
本計時の正式受理は6/24件となり、`c0t1e0` のMC/BAR両方が受理済みである。
監査原本はlocal `output/census_active_node_migration_v1/bar-t1e0-main-finish-audit-1792958166335120200/audit.json`、SHA-256は `7b8f98aa70dc2badea3424c5e3e99a87c5571111eece1d331cff37e4fbac864f` である。
controls / collected原本と親action / 実PBSの結合を確認し、巨大summaryの宣言pin `4a4f9cef673b2f80a4c26a268feddfd867cc4c84bb160cbcda52852f57759c1a` は独立hash済みとは扱わない。
個別BAR結果・費用・精度gate・最終科学検証は後続PBS reader待ちである。
次の `c0t1e1-mc-capacity` はsubmittingで、投入前helper265761（00038-submit）が実PBSでRに進んだ。
これはtile72・bit-flip・p=0.003・目標相対誤差10%の条件で、科学job IDは同時点で未確定である。
state原本の小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792958190798562700.json` に保存し、terminal12・submitting1・pending17を確認した。
terminal12はcapacity6件とmain6件を合わせた値であり、本計時12/24とは解釈しない。
05:09 JSTには次のMC capacityのtiming.sh・upstream完了記録・submission-intentの生成を確認したが、submission.jsonと科学job IDは未確定だった。
timing.shの実原本2061 bytesを読み、SHA-256 `c7f5eb0fe312bec8d646785da3ce623737ca59bc3c02881583ee9a833f3a1b95` とintent内のscript pin・qsub commandの一致を確認した。
要求は2 CPU・340 GiB・1 node・24時間であり、実割当を意味しない。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e1-capacity-submit-markers-1792958955442665700.json` に保存した。

## 2026-10-26 04:23 JSTのMC正式受理・BAR終了・保存fixture受入

MC本計時265753の正式finish265757はF/0・run_count=1・22分52秒で終了し、[完了記録の照合](../../output/census_active_node_migration_v1/MC_T1E0_MAIN_FINISH_AUDIT_ja.md)を経て本計時の正式受理は5/24件となった。
監査SHA-256は `a7f92b67f4a388bdbfb3e2e6683cf32ff080cccfa8759671111c194b7ebbd76d` で、原本とcollected copy、先行192個別結果監査へのpin一致を確認し、summary/rawの再読は行っていない。
BAR本計時265755もF/0・run_count=1・33分11秒で終了し、[限定結果監査](../../output/census_active_node_migration_v1/BAR_T1E0_MAIN_RESULT_AUDIT_ja.md)で小要約192/192・failed/unavailable 0を確認した。
BAR監査SHA-256は `a021f7fad2a17f15409f5fed0b11b56092b9e83f19d6408d8540d7c1b32a5d30` で、159,972,736 bytesのsummary本体はstatのみとし、個別結果・費用・full bindingと正式finishは未確認である。
state-latestのrunning/finishing表示が実PBS終端より遅れる場合があるため、終了判定はfresh PBSと実receiptに基づく。
最終snapshot preparerの合成fixtureを既存gate経由でqsub投入し、job265759はF/0・run_count=1・2秒、37 tests・1.071秒・skipなしで成功した。
投入前2回の資源判定では既存helper265758とfixtureを合わせて1物理ノード・2 CPU・100 GiBとなり、2ノード・各96 CPUの上限内だった。
fixture accepted原本SHA-256は `99e1d1ac945536545c63c96ba671a331f068cefe6aaa9425e558c892ff149bcf`、小原本はlocal `output/operational_census_acceptance_v1/final-snapshot-preparer-fixture-evidence-v1/` に保存した。
これは合成入力による保存準備処理の受入であり、本番snapshot保存や科学検証の完了ではない。
ローカルでは小metadataの回収・照合だけを行い、テストと科学計算は実行していない。
04:33 JSTにはBAR終了確認265758のF/0・11分29秒と、正式finish265760（00037-finish）のRを確認した。
照会原本はlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792956798223049000.json` に保存し、正式finish完了までは5/24件を維持する。

## 2026-10-26 04:09 JSTの最終保存処理の受入準備

最終snapshotの有限入力準備・分割保存receipt統合処理は独立静的レビューの指摘を解消し、実装と37件の合成fixture sourceを凍結した。
実装SHA-256は `fb163d0257b325523f53cdc02572a6ce3eaa5a0ee76e33a7702a28d27681c947`、fixtureは `40575c41899fa193162ae0c72375290e29f5f5311109bda0419e1851f391a3fd` である。
[PBS投入準備記録](../../output/final_snapshot_prepare_v1/PBS_FIXTURE_ROUTE_ja.md)に8本のsource・期待37件を指定するspecと既存policy pinの確認を記録した。
fixtureは未投入・未実行であり、最終科学報告や本番snapshotの完成を意味しない。
04:08 JSTの実PBS照会ではBAR本体265755がR・経過20分18秒、MC正式finish265757がR・経過9分59秒で、controllerも同一起動識別のまま生存している。
正式受理済み本計時は4/24のままとし、現行の資源gateが受理できる時点でfixtureをqsub投入する。
ローカルでのfixture実行・科学計算は行っていない。

## 2026-10-26 03:48 JSTの次条件BAR本計時投入

`c0t1e0-bar-main0` は投入前helper265754のF/0・run_count=1・46分02秒を経てqsubで投入され、本体265755が03:46:41 JSTにRへ進んだ。
[限定割当監査](../../output/census_active_node_migration_v1/BAR_T1E0_MAIN_ALLOCATION_AUDIT_ja.md)で、全ownerの実割当は本体96 CPU・337 GiBとMC終了確認helper265756の1 CPU・96 GiBの別2物理ノードで、各96 CPU以内・親265754解放済み・未配置jobなしを確認した。
manifest・台帳・script・intent・upstreamと実PBSの対応、identity `[0,1,0]`・partition 0・192予定反復・21 workers・要求1時間が一致した。
submission原本SHA-256は `4ac832e594b5352257790df5064f1f18e2b0c9289f2b5b135e834422d82b389a`、manifest canonical digestは `4ea111a9dd172bb0e9de0b16b94881ceb6aa6aa653d5989083f0dbb96c19b765` である。
監査原本はlocal `output/census_active_node_migration_v1/bar-t1e0-main-allocation-1792954086088867100.json`、SHA-256は `308bec17a230d03c1575f13a2bf7f1254eebf184b1219cf5a52d24cc85911238` である。
追加の小原本pin照合は同階層 `bar-t1e0-main-allocation-supplement-1792954086088867100/pin-check.json`、SHA-256は `bd53e506bf98d3ae60518be64fa327bf23746a85975e8ab2576775f13e6fa949` である。
BARの開始marker・native・結果は監査時点で未生成であり、PBSのRを推定器task開始や192反復の完了とは扱わない。
MC265753は結果照合済みで終了確認helperが進行中だが、正式finishは未確認で、正式受理済み本計時は4/24のままである。
03:58 JSTには終了確認helper265756のF/0・11分27秒と、正式finish265757（00035-finish）のRを確認し、MC taskはfinishingへ進んだ。
BARのexecution-intentとactual-pbs-startも生成され、job265755・manifest digest・既知投入pinとの対応が一致した。
原本SHA-256はintent `6c51afb4cb177007107dfeaea22983fbdd235a66a86016b0dc57fa41876e9691`、start `e7cf6e75e7f9c28449aa23f0357e7e3c2ad96eb6a1194e008b20c447c46e71f4`、小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t1e0-main-run-markers-1792954728056386600.json` に保存した。
native preflight・科学summary・MC正式finish受理は同時点で未確認であり、正式受理済み件数は変更していない。
04:02 JSTにはBAR native preflightの生成を確認し、job265755・manifest digest・保存sectorへの対応と有限probeの各不一致数0を確認した。
原本SHA-256は `0b47856984db65fb99680c1f9167b35e553a0b701996b6f9cb4098a5a7a027b2`、小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t1e0-main-run-markers-1792954952219340800.json` に保存した。
選択した1状態に限る反復確認であり、普遍的なdecoder決定性・他native環境との一致は証明せず、科学summaryと終了記録は同時点で未生成である。

## 2026-10-26 03:35 JSTの次条件MC本計時終了と結果照合

`c0t1e0-mc-main0` の科学job265753はF/0・run_count=1・33分49秒で終了し、[限定結果監査](../../output/census_active_node_migration_v1/MC_T1E0_MAIN_RESULT_AUDIT_ja.md)で192反復すべてのstatus ok・available trueと重複欠落なしを確認した。
summaryは3,174,797 bytesで4 MiB以内であり、manifest・snapshot・submission・intent・script・native job ID・小summaryへの結合と費用metadataの整合を確認した。
監査JSONのSHA-256は `ff238aca6cfdba6a3a5a719d9eeb5a54aa09ba70dfe64604f9339fd44373c85f`、summary原本は `91ca37820a8c1d5c8ffc50631bab42c366babb48a6693200213ed3677e343556` である。
原本はlocal `output/census_active_node_migration_v1/mc-t1e0-main-result-audit-1792953312658977200/` に保存した。
execution wallは2027.202565秒、poolは459.797105秒、outside poolは1567.405460秒であり、これらをtask CPU合計9003.334556秒やtask wall合計9032.729495秒と混同しない。
job内のactual-pbs-endはRの採取記録なので、終端判定には独立したfresh qstatのF/0を用いた。
controller正式finishと精度gateは未確認であり、正式受理済み本計時は4/24のままである。
BAR投入前helper265754は実PBSでR、controllerの生存・起動識別一致を確認し、元科学rawの再読・再計算・追加qsubは行っていない。

## 2026-10-26 03:01 JSTの次条件MC本計時投入

`c0t1e0-mc-main0` は投入前helper265752のF/0・run_count=1・45分39秒を経てqsubで投入され、本体265753が03:00:34 JSTにRへ進んだ。
03:01:17 JSTの[限定割当監査](../../output/census_outer_operation_v1/MC_T1E0_MAIN_ALLOCATION_2026-10-26_ja.md)で、state・manifest・intent・submission・scriptと実PBSの対応、identity `[0,1,0]`・partition 0・192予定反復・21 workers・96 CPU・337 GiB・要求1時間を確認した。
submission原本のSHA-256は `6889f9aef2bfa9b63b668d645e539167cbef7f1f2edf3ab5f4ee2ceb5dc0f600`、既知script・intent pinとmanifest canonical digestは投入前観測に一致した。
親265752は実active一覧から解放され、次のBAR `c0t1e0-bar-main0` の投入前helper265754（00033-submit）がRとなった。
両active jobは本体96 CPU・337 GiBとhelper1 CPU・96 GiBの別2物理ノードに配置され、各96 CPU以内、Q・配置未確定の所有jobなしだった。
原本はlocal `output/census_outer_operation_v1/mc-t1e0-main-allocation-1792951277635363700.json`、SHA-256は `848768f418bd2e675c60ab61aefe03f82c78b37444fd8d37ce12213794d5a2b0` である。
開始marker・native・summaryは監査時点で未生成であり、PBSのRを推定器task開始や192反復の完了とは扱わない。
controllerの生存・起動識別一致を確認し、stateはterminal10・pending18・running1・submitting1へ進んだが、正式受理済み本計時は4/24のままである。
小観測はlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792951255167481200.json` と `independent-state-1792951265750392400.json` に保存した。
03:12 JSTの追跡では265753は実PBSでRのまま、execution-intentとactual-pbs-startが生成され、job・manifest・投入記録への対応が一致した。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e0-main-run-markers-1792951959978845100.json` に保存し、intent原本SHA-256は `42983980fe902b46b14ddfc3e30a8b26f195829f814f4f60dc21f64441664e12`、startは `c2059235e3b7d2fa8cdca281c67e256253834ce21d9c59a6706979abd8173ddf` である。
native preflightと科学結果は同時点で未生成であり、推定器taskの開始・192反復完了・正式受理はまだ確認していない。
03:16 JSTにはnative preflightが生成され、manifest digestとjob265753への対応、保存sectorとの一致、有限probeの各不一致数0を確認した。
原本SHA-256は `6d13455a750b6d7ba5d20f31d2d56408e6759330c03c2cc88765d2ce7cd023df`、小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e0-main-run-markers-1792952187809498600.json` に保存した。
このprobeは選択した1状態に限る反復確認であり、普遍的なdecoder決定性や異なるnative環境での一致を証明しない。
科学summaryと終了記録は同時点で未生成である。
03:24 JSTにはBAR本計時のtiming.shが生成され、2,071 bytes・SHA-256 `a0a56ae27a05e1d7980fdfd64dedf363335654c8735f9e852093e73573734887` を確認した。
小scriptの内容は予定したBAR run root・1 node・96 CPU・337 GiB・要求1時間に一致し、local `output/census_active_node_migration_v1/bar-t1e0-main-script-observation-1792952675264488600.json` に保存した。
upstream-completion・submission-intent・submissionは同時点で未生成であり、script生成を実qsub投入や本計時開始とは扱わない。

## 2026-10-26 02:15 JSTの次条件BAR予備計時の正式受理

`c0t1e0-bar-capacity` の正式finish265751はF/0・run_count=1・walltime40分51秒で終了し、[小原本監査](../../output/census_active_node_migration_v1/BAR_T1E0_CAPACITY_FINISH_AUDIT_ja.md)でaccepted・completion・controls receipt・capacity proof・本計時manifestの対応を確認した。
元capacity265747のF/0・7分32秒、既知manifest/submission/scriptと小要約のpin、capacity summaryの2件成功・failed/unavailable各0も一致した。
本計画のreplicate 0〜191に重複・欠落はなく、1 partition・21 workers・96 CPU・337 GiB・要求1時間でdecision・prepared・manifestが一致した。
原本19点はlocal `output/census_active_node_migration_v1/bar-t1e0-capacity-finish-audit-1792948532493495500/`、監査JSONのSHA-256は `a941d791bf3e883626590b753769920a18d2131ed56f0ace0706540e3db3e8c9` である。
controls completedは `c12cfd25ffb2192876b536e5fb2ec79bb4453e66db7f6be65c526fc185e154d9`、preparedは `8856ba520d14ff2481a08fa89474d6adaf0760254be6ed0a904a33c43c701865`、本計時manifestは `577d897469bd82b975d95b2ff57113680b246d4a75f4e44889d760d405327038` に一致した。
最大原本はmain manifestの1,848,776 bytes、capacity summaryは1,670,105 bytesで、各4 MiB上限の小原本のみ確認し、科学rawや60 sourceの実ファイルは再読していない。
controllerの生存・起動識別一致・errorなしを確認し、監査時点のBAR本計時submission・execution-intent・summaryは未生成だった。
状態はterminal10・pending19・submitting1へ進み、`c0t1e0-mc-main0` の投入前helper265752（00032-submit）がRとなったが、科学本体のjob IDはまだ未生成である。
観測はlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792948510816864200.json` と `independent-state-1792948534484376900.json` に保存した。
terminal10にはcapacity6件が含まれ、独立本計時の正式受理済みは4/24のままで、残り本計時・最終科学評価・報告保存は未完了である。
02:37 JSTの小観測でMC `c0t1e0` 本計時のtiming.shが生成され、2,068 bytes・SHA-256 `8f397be3599851e1a6e5e985631a918e72c5dd1b1ee37f2be322c2c6d5467a6e` を記録した。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e0-main-submit-markers-1792949861753290400.json` に保存し、upstream-completion・submission-intent・submissionは同時点で未生成だった。
投入前helper265752は直前の実PBS照会でR・20分18秒であり、scriptの生成をqsub投入や本計時の開始とは扱わない。
02:49 JSTにはupstream-completion-at-submitとsubmission-intentが生成され、intentのscript SHAと資源指定は既観測のscriptおよび本計画に一致した。
原本SHA-256はupstream `9d6a9dfe53a5809b1dbf5486f7bba504631b73ce75aa4cbbceaca346f421aae9`、intent `79860ca3789a9dadc1d268e05734e939ce03986637562f3e6d9692de346c1038` であり、小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e0-main-submit-markers-1792950559059448200.json` に保存した。
intentのmanifest canonical digestは `effe37dbe910c38f14ea5f21e1e74279a4dad41d906e03f7c2f80793c409584d` であり、実投入時に保存済みmanifestとの対応を照合する。
同時点でsubmissionは未生成で、投入前helper265752も直前実PBS照会ではR・32分20秒だったため、qsub投入・本計時開始とは扱わない。

## 2026-10-26 01:30 JSTの次条件MC予備計時の正式受理

`c0t1e0-mc-capacity` の正式finish265749はF/0・run_count=1・walltime41分30秒で終了し、[小原本監査](../../output/census_active_node_migration_v1/MC_T1E0_CAPACITY_FINISH_AUDIT_ja.md)でaccepted・completion・controls receipt・capacity proof・本計時manifestの対応を確認した。
元capacity265743のF/0・8分00秒、既知manifest/submission/scriptと小要約のpin、full capacity summaryの2件成功・failed/unavailable各0も一致した。
本計画のreplicate 0〜191に重複・欠落はなく、1 partition・21 workers・96 CPU・337 GiB・要求1時間でresource-decision・prepared・manifestが一致した。
原本19点はlocal `output/census_active_node_migration_v1/mc-t1e0-capacity-finish-audit-1792945819428973100/`、監査JSONのSHA-256は `3742642c2387f954144a678ec985cf0bbe906a9a50cc83588bd415da079b6734` である。
controls completedは `25b9dd762c08cc71c854b29a6c9de3106d549b062a7f645df78f6ef51788fdf7`、本計時manifestは `157f1a0621b928bf721a085a9edf741a616965caafeb84be1bd6e5f69cf7cf75`、action acceptedは `75e1577623598021a1280d1fbbcdcf5e7f4f114268c4361505b29de4b81aa073` に一致した。
最大原本215,594 bytes・capacity summary36,973 bytesを4 MiB上限で確認し、科学rawや60 sourceの実ファイルは再読していない。
controllerの生存・起動識別一致・errorなしを確認し、監査時点の本計時submission・execution-intent・summaryは未生成だった。
予備計時の正式受理と本計画の生成であり、独立本計時の正式受理済みは4/24のままで、BAR capacity正式受理・残り本計時・最終科学検証・報告保存は未完了である。
後続observe helper265750のRをlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792945799710963900.json` で確認した。
01:33 JSTにはobserve265750がF/0・3分41秒となり、正式finish helper265751（00031-finish）のRと、stateの `c0t1e0-bar-capacity` finishingを確認した。
小観測はlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792946007425661700.json` と `independent-state-1792946021503530800.json` に保存し、stateはterminal9・finishing1・pending19となった。
terminal9にはcapacity5件が含まれ、正式受理済み本計時4/24と区別する。
01:48 JSTにはBAR `c0t1e0` のresource-decisionが生成され、status ready・192反復・1 partition・21 workers・96 CPU・337 GiB・要求1時間を確認した。
原本は1,549 bytes・SHA-256 `a668706ca1be450f7308c6876dc40aa4bd0f081525ba13a14d762e168ddbc527`、小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t1e0-finish-markers-1792946919400895500.json` に保存した。
予測661.92秒は資源計画値であり、追加検証・投入待ちを含む完了見込みや精度保証ではない。
prepared-partition・completedは同時点で未生成で、正式finish265751の直前実PBS照会はR・13分01秒だった。

## 2026-10-26 01:07 JSTの公開状態再確認

GitHub REST APIの読み取り専用照会で、repositoryがpublic・非archive、default branchがmain・head `837a96b8836ba8c81043fcba15b065eb1a8b5296`、Release `v0.1.0.dev5` が非draft・prerelease・配布物5件であることを再確認した。
tag対象commitは `c27ca896a1025c74975bc45322798eea2e0409b0` で、前日の公開状態および既存公開記録との変更はなかった。
公開識別子だけを含む[確認記録](publication_state_check_2026-10-26.json)を保存し、SHA-256は `fccd62e8b2ffa554d2691c35d86ef06ba5a377bd5e07f48e6e93a4b6dc834a08` である。
配布物bytes・CI・Zenodoの再検証は行っておらず、未コミット作業の公開や科学検証全体の完了を示す確認ではない。
クラスタの独立本計時の正式受理済みは4/24のままで、MC capacity正式finish265749の稼働を継続確認している。

## 2026-10-26 00:53 JSTの次条件BAR予備計時終了

`c0t1e0-bar-capacity` 本体265747はF/0・run_count=1・walltime7分32秒で終了した。
小scientific-summaryはplanned/recorded各2、failed/unavailable各0、execution_complete/all_estimates_availableともtrueを記録し、2,284 bytes・SHA-256 `8a4bebf23746d5b4b0c610117ce83b222f609562f3a629f21ee8ff124ddb3969` である。
actual-pbs-endは603 bytes・SHA-256 `dc46c3aae5858429c776d2e948ede66613c9e950ee3ff511db2a1bbf5fd21e8a`、小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t1e0-capacity-run-markers-1792943602475499600.json`、実PBS照会は同階層の `independent-state-1792943602540503200.json` に保存した。
小要約の成功件数と本体終了の確認であり、個別結果・正式capacity finish・本計時192反復の完了とは扱わない。
MC capacity終了確認265748はF/0・3分44秒となり、正式finish265749（00029-finish）がRへ進んだことを00:51の `diagnostic-window-observation-1792943462556800700.json` で確認した。
stateはMC finishing・BAR runningだがBARの実PBSはF/0であり、台帳更新との時差を区別する。
独立本計時の正式受理済みは4/24のままで、両予備計時の正式回収と本計時計画の生成・受理は後続確認である。
01:03 JSTの小観測でMC `c0t1e0` のresource-decisionが生成され、status ready・192反復・1 partition・21 workers・96 CPU・337 GiB・要求1時間の計画を確認した。
原本は1,552 bytes・SHA-256 `a4284536bb85eb130ac0d831a702fbf68cc8d2f75d94f67197f8f10b54e4f7e9`、小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e0-finish-markers-1792944225420962500.json` に保存した。
予測951.72秒は予備計時からの資源計画値であり、本計時の追加検証・投入待ちを含む完了予測や精度保証ではない。
prepared-partitionとcompletedは同時点で未生成で、正式finish265749も直前の実PBS照会ではR・14分42秒だった。

## 2026-10-26 00:45 JSTの次条件BAR予備計時投入

次の `c0t1e0-bar-capacity` 本体265747はqsubで投入され、00:43:44 JSTにRへ進んだ。
00:45:31 JSTの[限定割当監査](../../output/census_outer_operation_v1/C0T1E0_BAR_CAPACITY_ALLOCATION_2026-10-26_ja.md)で、state・manifest・submission/intent・scriptと実PBSの対応、identity `[0,1,0]`・2 CPU・2 workers・340 GiB・1ノード・要求24時間を確認した。
要求時間は運用上限であり、完了見込みではない。
親helper265746はF/0・run_count=1・14分48秒で解放され、並行するhelper265748（00028-observe）は終了済み `c0t1e0-mc-capacity` の確認処理としてRだった。
両active jobは別2物理ノード・各96 CPU以内で、Q・配置未確定の所有jobはなかった。
原本はlocal `output/census_outer_operation_v1/c0t1e0-bar-capacity-allocation-1792943131581169000.json`、SHA-256は `47a090165e161879fa0d16e52deb05e6ed764479236f2cdb8a78474622b44494` である。
manifestのSHA-256は `07c584d8c994e9aefb640b816812e0b653c60d6861820a896df1f74e04cfa201`、submissionは `c1ae9c5278a050cc778efe12150fd9c5c08d4aeafb6981a09f98dc59c18b9724`、scriptは `af73ae26d84c556b8cb08211f11638adf25a64f2bb4c1a2ec094a811e8f2aaee` に一致した。
開始marker・native・summaryは監査時点で未生成であり、PBSのRを推定器task開始や計時成功とは扱わない。
独立本計時の正式受理済みは4/24のままで、controllerの生存・起動識別一致はlocal `output/finite_tail_resume_controller_v1/diagnostic-window-observation-1792943080528768000.json` に記録した。
00:49 JSTの小観測ではBAR265747のexecution-intent・actual-pbs-start・native_preflightが生成され、job・manifest digest・submission/scriptの結合は投入時の記録に一致した。
原本SHA-256はexecution-intent `d0ee6be411e6c79aa579a7e3cce64e35022ba4dfc3fbf5127bd9a8f8f066665d`、actual-pbs-start `f57fc0e14513dd824089ef3df8d446c61a2b91f548a1978497f47b345b58b27e`、native `91b99c3e66061aefbd7971c836965167f32578216f51e9be2103ce085b578dd0` である。
nativeは保存sectorに一致し各mismatch・syndrome violation 0だったが、選択された1状態の有限反復であり普遍的なdecoder決定性の証明ではない。
小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t1e0-capacity-run-markers-1792943361944924600.json` に保存し、同時点でsummary・failure・actual-pbs-endは未生成だった。

## 2026-10-26 00:32 JSTのBAR本計時正式受理

`c0t0e1-bar-main0` の正式finish265745はF/0・run_count=1・walltime23分05秒で終了し、[限定監査](../../output/census_active_node_migration_v1/BAR_E1_MAIN_FINISH_AUDIT_ja.md)でaction受理・controlsとcollectedの原本一致・元job265739とmanifest/submissionへの対応を確認した。
監査JSONはlocal `output/census_active_node_migration_v1/bar-e1-main-finish-audit-1792942346698024800/audit.json` に保存し、SHA-256は `98acf701e009170d57c0dfe62bc22d99f9e60659cde59d739d1201cb6a528058` である。
独立本計時の正式受理済みは4/24となり、残り20件の本実行・回収、全条件の最終科学検証・費用比較・再現用最終保存は未完了である。
receiptの `scientific_validation_complete=false` を保持し、291,433,034 bytesのBAR summary本体と個別192件の結合・費用は後続PBS readerで確認する。
00:32の実PBS照会では次MC capacity265743がF/0・8分00秒、次BAR capacityの投入前helper265746（00027-submit）がR・3分16秒で、controllerの生存を確認した。
小観測はlocal `output/finite_tail_resume_controller_v1/window-observation-1792942325077992600.json` と `independent-state-1792942325447511500.json` に保存した。
全工程の暫定終了見込みは10月28日午前〜29日JSTであり、直近MC/BAR一組の準備・回収込み約4〜5時間を外挿したもので、低ノイズ条件や待ち行列による変動を含む。
以下は各観測時刻の履歴として保持する。

## 2026-10-26 00:01 JSTの次条件MC予備計時終了

`c0t1e0-mc-capacity` 本体265743はF/0・run_count=1・walltime8分00秒となり、小要約はplanned/recorded各2・failed/unavailable各0・execution_complete/all_estimates_availableともtrueを記録した。
小要約は2,284 bytes・SHA-256 `8a4bebf23746d5b4b0c610117ce83b222f609562f3a629f21ee8ff124ddb3969`、actual-pbs-endは602 bytes・SHA-256 `fb7dcc20731f16d6298d0be8eecf8c2677a923f638cabca18cdab3f20d7a44b8` である。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e0-capacity-run-markers-1792940478664412600.json`、実PBS照会は同階層の `independent-state-1792940479668204100.json` に保存した。
これは予備計時本体の終了と小要約の確認であり、個別結果・正式capacity finish・本計時192反復の完了とは扱わない。
前条件BARの終了確認helper265744はRで、controllerの生存・起動識別一致・errorなしを確認した。
独立本計時の正式受理済みは3/24のままであり、BARの正式受理と全体の最終科学検証は未完了である。
00:05 JSTにはBAR終了確認265744のF/0・walltime11分32秒と、後続の正式finish helper265745（00026-finish）のRを確認した。
stateでも `c0t0e1-bar-main0` がfinishingへ進み、次MC capacityのstateはrunningのままだが実本体265743はF/0であり、状態記録と実PBSの時差を区別する。
小観測はlocal `output/finite_tail_resume_controller_v1/window-observation-1792940725863147600.json` と `independent-state-1792940745573185400.json` に保存し、正式受理の完了とは扱わない。

## 2026-10-25 23:54 JSTの次条件MC予備計時投入

次の `c0t1e0-mc-capacity` は投入前helper265742のF/0・walltime14分47秒を経てqsubで投入され、本体265743が23:53:05 JSTにRへ進んだ。
23:54:08 JSTの[限定割当監査](../../output/census_outer_operation_v1/C0T1E0_MC_CAPACITY_ALLOCATION_2026-10-25_ja.md)で、state・manifest・submission/intent・scriptと実PBSを照合し、identity `[0,1,0]`・capacity・2 CPU・2 workers・340 GiB・1ノード・要求24時間を確認した。
要求24時間は運用上限であり、完了時刻の見積もりではない。
manifestのSHA-256は `f02d898ef97ec6021a6da38a99b97c6920f86eb2ed477a9b2d98294faafe0bf9`、submissionは `bcfc9385bc293ca101c7eff6710be7b85ddfd18807660eac08a66d5e0d864adc`、scriptは `901e3c987b303f9ad5204dd44beda7a25981f9491e458c58a9c58c2eeefc7df6` である。
同時に前条件BAR `c0t0e1-bar-main0` の終了確認helper265744（00025-observe）がR・1 CPU・96 GiBで、実active jobはこの2件、別2物理ノード・各96 CPU以内、Q・配置未確定jobなしだった。
親265742は実active jobsから解放済みで、本体の開始marker・native・summaryは観測時点で未生成であり、PBSのRを推定器task開始や容量計測成功とは扱わない。
小原本はlocal `output/census_outer_operation_v1/c0t1e0-mc-capacity-allocation-1792940048637038500.json` に保存し、SHA-256は `a6c12e1162e1481b6fcc52abe5f7fdc47ade35e86ba6bd312e2d709805f74625` である。
controllerの生存・起動識別一致・errorなしを確認し、独立本計時の正式受理済みは3/24のままである。
前条件BAR265739の本体F/0・小要約192/192は確認済みだが、正式finishと個別結果・費用・最終科学評価は後続確認として保持する。
23:56 JSTには次MC265743のexecution-intent・actual-pbs-start・native_preflightが生成され、job ID・manifest digest・submission bindingが投入時の値と一致した。
各原本SHA-256はexecution-intent `474f6a933ffeb67303169d77a06d15e66c663b38de7ac457fec4de885fcff818`、actual-pbs-start `8c2a75f910c58a14f73009f167967df6620b0882fde80706c7c5c1f4efbc1e8e`、native `dfeaf5652a258145af0e86bb352be6bdd034fcff7fa27b3f6ea789e8b1256c0e` である。
nativeでは保存sectorとの一致と各mismatch・syndrome violation 0を確認したが、選択された1状態の有限反復であり普遍的なdecoder決定性の証明とは扱わない。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t1e0-capacity-run-markers-1792940215692492800.json` に保存し、同時点でscientific-summary・failure・actual-pbs-endは未生成だった。

## 2026-10-25 23:41 JSTの次精度条件BAR本計時結果

BAR本計時 `c0t0e1-bar-main0` 本体265739はF/0・run_count=1・walltime37分31秒となり、小scientific-summaryはplanned/recorded各192・failed/unavailable各0・execution_complete/all_estimates_availableともtrueを記録した。
23:41:35 JSTの[小原本限定監査](../../output/census_active_node_migration_v1/BAR_E1_MAIN_RESULT_AUDIT_ja.md)でmanifest・実投入・script・開始記録・新しいPBS終端の結合と、小要約の指定run rootへの対応を確認した。
小要約自体にはjob ID・manifest digestがなく、他の成功jobと同じhashであることだけでは結果とjobの結合証明にはならない。
summary本体は291,433,034 bytesで4 MiB上限を超えるため、今回の監査では読取り・転送・hash照合を行っていない。
個別192件のidentity・重複欠落、費用、full summaryを介したmanifest・終端への結合は、既存の後続PBS readerで確認する。
小原本11点はlocal `output/census_active_node_migration_v1/bar-e1-main-result-audit-1792939296079063300/` に保存し、監査JSONのSHA-256は `f4a14eba8d4b469211754c5b46a2cc407025a3dd060037b4e4c17f57dee3448a` である。
actual-pbs-end原本のSHA-256は `294c19191484313370be93432c34cd7551b108a338ff6d5af8e86f79efd27e2c` だが、job内採取時はRであり、終端判断はfresh qstatのF/0による。
当該BARの正式finish受理は未確認で、独立本計時の正式受理済みは3/24のままである。
controllerは生存・起動識別一致・errorなし、次の `c0t1e0-mc-capacity` の投入前helper265742はRであり、状態観測をlocal `output/finite_tail_resume_controller_v1/window-observation-1792939274658270900.json` と `independent-state-1792939275008349600.json` に保存した。
元科学計算の再実行、科学rawのローカル読取り、凍結controllerの変更は行っていない。
23:45 JSTに限定監視の応答JSONを読めない観測エラーが1回あったが、同じcontroller/jobの即時再照会で265742のR・起動識別一致・制御errorなしを確認した。
失敗と再照会の記録はlocal `output/finite_tail_resume_controller_v1/window-observation-1792939549237619800.json`・`window-observation-1792939562115219500.json` に保持し、remote returncodeは0、観測エラーからjob終了を推定せず再起動・再投入は行っていない。

## 2026-10-25 23:38 JSTの次精度条件MC本計時の正式受理

MC本計時 `c0t0e1-mc-main0` の正式finish265741（00023-finish）はF/0・run_count=1・walltime22分50秒で終了した。
23:38:29 JSTの[限定監査](../../output/census_active_node_migration_v1/MC_E1_MAIN_FINISH_AUDIT_ja.md)で、action accepted・completion・controls receipt/terminal・collected copyの原本一致と、既存192record監査のmanifest・submission・summary pinへの結合を確認した。
payloadのtask key・root・元job265737・mode・partitionもreceiptに一致し、元265737のF/0・run_count=1・28分13秒をfresh qstatで再確認した。
原本12点はlocal `output/census_active_node_migration_v1/mc-e1-main-finish-audit-1792939109111173600/`、監査JSONのSHA-256は `200c143dab9175132ca63d7a3d090e82a7c303729732714db4f022c58dfb8657` である。
controlsとcollectedのcompleted原本SHA-256は `1b589d87b1b53d5d8e3c41be917dcef8700359d0d4be9fa8d7cc62a970455165`、terminalは `d46dc5d0d6522ec8b255fb44d14179d0786633e2898c2bd6a7092b078d400654` に一致した。
receiptは `main_terminal_recorded`・`scientific_validation_complete=false`・`raw_payloads_rehashed_now=false` を保持し、今回はsummary/rawを再読していない。
独立本計時の正式受理済みは3/24であり、capacity4件を含むstateのterminal7件とは区別する。
BAR本計時265739は同時点でR、次の `c0t1e0-mc-capacity` はsubmittingで、投入前helper265742（00024-submit）がRへ進んだ。
controllerの生存・起動識別一致・errorなしを確認し、状態観測をlocal `output/finite_tail_resume_controller_v1/independent-state-1792939082135748800.json` と `window-observation-1792939129297433700.json` に保存した。
BARの結果監査・正式受理、残り独立計時、最終精度gate・費用比較・全証拠保存は未完了である。

## 2026-10-25 23:04 JSTの次精度条件BAR本計時投入

BAR投入前検証265738はF/0・run_count=1・walltime47分33秒で終了し、本計時 `c0t0e1-bar-main0` のjob265739がqsubで投入されて23:02:54 JSTにRへ進んだ。
23:04:00 JSTの[実割当監査](../../output/census_outer_operation_v1/BAR_E1_MAIN_ALLOCATION_2026-10-25_ja.md)で、state・manifest・submission・intent・scriptと実PBSの対応を確認した。
要求は1ノード・96 CPU・337 GiB・1時間、計画worker数21で、submissionのSHA-256は `c7ee38bbff9eaaa573f2b7d36b6fd4aabfd3b6576848d0ae75a0b0b53d09515f`、scriptは既観測の `fe73ae3af310ca2c664896e04160ceb84932f82e8e13d2f96e7958390635b64e` に一致した。
同時にMC本計時の終端確認helper265740（00022-observe、`c0t0e1-mc-main0`）がR・1 CPU・96 GiBとなり、両jobは別2物理ノード・各96 CPU以内で、待機・配置未確定の所有jobはなかった。
親265738は23:02:23 JSTに終了して実active jobsからも解放済みである。
監査原本はlocal `output/census_outer_operation_v1/bar-e1-main-allocation-1792937040583622400.json`、SHA-256は `f761ebb468e44a6a5a2138025583f982b2935c6f7c25c5eefd5d85aab6879f7f` である。
開始marker・native・summaryは観測時点で未生成であり、PBSのRを推定器task開始や192反復完了とは扱わない。
controllerの生存・起動識別一致・errorなしを確認したが、stateのrunning2件には実PBSでは終了済みのMC265737が含まれ、正式受理済み本計時は2/24のままである。
MC265737の個別192件監査完了と、BARの実投入・稼働、正式finish受理、後続の科学評価を区別する。
23:14 JSTにはMC終端確認265740のF/0・walltime11分31秒と、BAR265739のexecution-intent・actual-pbs-startの生成を確認した。
BARのjob ID・manifest digest・submission bindingは投入監査の値に一致し、execution-intentのSHA-256は `b7ee38ccd4fc0113b5b719ed81089c20b35cfdb0fa0cc2707642e57e5fad582b`、actual-pbs-startは `6a348b4d26ac10fcc6de614c2f14c4b0157d2733ed547695c1174efc7b8aa13b` である。
小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t0e1-main-run-markers-1792937668371171200.json` と `window-observation-1792937668193999600.json` に保存した。
同時点でBARのnative・summaryは未生成で、MC正式finishも未受理である。
23:16 JSTにはMC正式finish265741（00023-finish）のRを確認し、小観測 `output/finite_tail_resume_controller_v1/window-observation-1792937760782693500.json` に保存した。
正式finishの開始は受理完了とは区別し、終了後に小原本と既存MC結果のpinを照合する。
23:18 JSTにはBAR265739のnative_preflightを確認し、job ID・manifest digestが開始記録に一致し、保存sectorとの一致と各mismatch・syndrome violation 0を記録した。
選択された1状態の有限反復であり、普遍的なdecoder決定性の証明とは扱わない。
原本は3,645 bytes・SHA-256 `c13a0a5a7eb4aa30bc8170091f5010aafa2d27666106c7c7d1e5b55fdf4dac90`、小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t0e1-main-run-markers-1792937914956103800.json` に保存した。
同時点の実PBSでBARはR、stateはMC finishing・BAR runningで、BARのsummary・failure・actual-pbs-endは未生成だった。

## 2026-10-25 22:45 JSTの次精度条件MC本計時結果

`c0t0e1-mc-main0` 本体265737はF/0・run_count=1・walltime28分13秒で終了し、22:45:46 JSTの[限定独立監査](../../output/census_active_node_migration_v1/MC_E1_MAIN_RESULT_AUDIT_ja.md)で192反復の全件成功・重複欠落なしを確認した。
summaryは3,173,991 bytesで4 MiB以内だったため、identity `[0,0,1]`・replicate 0〜191、manifest・snapshot・submission・intent・native・script・小要約への結合と費用記録の整合まで確認した。
原本12点はlocal `output/census_active_node_migration_v1/mc-e1-main-result-audit-1792935947116004600/` に保存し、監査JSONのSHA-256は `0ffd304cb4df2b907ac5e9e00971b934f4cdeb7c0efaeafb29ea3276bf3a59a7`、summary原本は `29bf688da80fe68de057cfe693f4d75999875ca4cb9860bd25aeb754e8fe75b3` である。
記録されたexecution wallは1690.903秒、pool wallは113.350秒、outside pool wallは1577.553秒であり、費用指標を区別して後続の同一精度比較へ渡す。
job内のactual-pbs-endはRで採取されているため、終端の根拠は独立したfresh qstatのF/0とする。
正式finish受理と最終精度gateは未確認で、正式受理済み本計時は2/24のまま、別にこの1件の計算終了・個別結果監査が完了した状態である。
BAR投入前helper265738は22:45 JSTにR・経過30分20秒で、controllerは生存・起動識別一致・errorなしだった。
BARのtiming.shは生成済みでSHA-256は `fe73ae3af310ca2c664896e04160ceb84932f82e8e13d2f96e7958390635b64e`、submissionは同時点で未生成であり、本体の実投入とは扱わない。
小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792935927552412500.json`、`window-observation-1792935927213667600.json`、`bar-c0t0e1-main-submit-markers-1792935954419545800.json` に保存した。
科学rawの再読・推定値の再計算・重複投入・凍結controllerの変更は行っていない。
22:51 JSTにはBAR本計時のupstream completionとsubmission intentを確認したが、submissionは未生成だった。
intentはqsub・1ノード・96 CPU・21 workers・337 GB・要求1時間を指定し、script pinは既観測値に一致した。
upstream記録は265703と265731のF/0・run_count=1を含み、SHA-256は `985e05d28f6d5e964f5e59cb4b798c3e345b985e8db551bff2ae75d81e0886b9`、intentは `737b24c1fa742cc3eb0881570859d088a58640cae4314753371767791e4f7d81` である。
小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t0e1-main-submit-markers-1792936263771181800.json` に保存し、投入予定の生成を実qsubや計算開始の証拠とは扱わない。

## 2026-10-25 22:16 JSTの次精度条件MC本計時投入

MC投入前検証265736はF/0・run_count=1・walltime45分39秒となり、`c0t0e1-mc-main0` の本計時job265737がqsubで投入されてRへ進んだ。
22:16:19 JSTの[実割当監査](../../output/census_outer_operation_v1/MC_E1_MAIN_ALLOCATION_2026-10-25_ja.md)で、state・manifest・submission・intent・scriptと実PBSの対応を確認した。
本計時の要求は1ノード・96 CPU・337 GiB・30分、計画worker数21で、PBS開始は22:14:47 JSTだった。
submissionのSHA-256は `88585c6665ea43b3eb557c8e3dcc57de68b08b1ea932968f17506a191fb3805c`、scriptは既観測の `9f7230db30a0b68fe0fb9933f8d2d9be4a9fd0418ae060ca692e1604ec323b73` に一致した。
次の `c0t0e1-bar-main0` はsubmittingで、その投入前検証helper265738もR・1 CPU・96 GiBだった。
両jobは別2物理ノードで各96 CPU以内、所有する待機・配置未確定jobはなく、先行265736の解放も確認した。
小原本はlocal `output/census_outer_operation_v1/mc-e1-main-allocation-1792934179775290100.json` に保存し、SHA-256は `db14fbe343dcb8a47e29986f91f2c3bb08ab39994f4c4908852f0787ebac7753` である。
execution-intent・actual-pbs-start・native_preflight・summary・failureは監査時点で未生成であり、PBSのRを推定器task開始や192反復完了と同一視しない。
controllerの生存・起動識別一致・errorなしと、terminal6件・running1件・submitting1件・pending20件を確認したが、terminal6件は容量4件を含むため本計時完了は2/24のままである。
小状態観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792934117815593500.json` に保存した。
22:26 JSTにはMC265737のexecution-intentとactual-pbs-startが生成され、job ID・script・submission・intentの各pinが先の投入監査に一致した。
原本SHA-256はそれぞれ `58bde759c09017a719a8b9874d719ad874187cc5196ca28cd8bad6e0c8b9d6ef` と `8a0d58742705d6b43b521186f0232047ce54064fd94ddd77b32706f86175f3c3`、小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t0e1-main-run-markers-1792934778779009400.json` に保存した。
同時点ではnative_preflight・scientific-summary・failure・actual-pbs-endは未生成で、192反復完了やnative検査完了とは扱わない。
22:30 JSTにはMC265737のnative_preflightを確認し、job ID・manifest digestが開始記録に一致し、保存sectorとの一致と各mismatch・syndrome violation 0を記録した。
選択された1状態の有限反復であり、普遍的なdecoder決定性の証明とは扱わない。
同原本は3,645 bytes・SHA-256 `fb8fddeee9fe282caa2ef70db6bd11f56d1dcdbf1963dd97543d412f5c1720b9`、小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t0e1-main-run-markers-1792935042527441800.json` に保存した。
scientific-summary・failure・actual-pbs-endは同時点で未生成だった。
22:29 JSTの利用者向け全体ETAは、直近MC/BAR一組の予備計時・本計時・受理を約4〜5時間として残件へ単純外挿した10月28日午前〜29日の暫定値であり、未計測の低ノイズ条件が長引く場合や再処理・待機が発生する場合を含む完了保証ではない。

## 2026-10-25 21:29 JSTの次精度条件BAR予備計時の正式受理

`c0t0e1-bar-capacity` の正式finish265735（00019-finish）はF/0・run_count=1・walltime41分52秒となった。
21:29:44 JSTの[小原本監査](../../output/census_active_node_migration_v1/BAR_E1_CAPACITY_FINISH_AUDIT_ja.md)で、accepted・action completion・controls completedから元容量proofと本計時manifestへの対応、元265731のF/0・7分49秒と容量2 task成功を確認した。
本計画のidentity `[0,0,1]`・replicate 0〜191の重複欠落なし、1 partition・21 workers・96 CPU・337 GB・要求1時間が資源決定と一致した。
completedのSHA-256は `f17f6374b04596ca6761f3117a150e9014e24f53d2bfab5b5c26be11bff4c69f`、本計時manifestは `fb188c6ed0b12cebc8c921217c177d1af236c186009b891dd3aba568f5d5b748` である。
小原本18点はlocal `output/census_active_node_migration_v1/bar-e1-capacity-finish-audit-1792931384462299400/` に保存し、監査JSONのSHA-256は `b34353c1e509983686baa7d21240b8c256ba2878922c9470c55733af1c9293c1` である。
source mapは既存closure digestと一致したが、実60sourceの再hashや科学rawの再読は行っていない。
監査時点で当該BAR本計時rootのsubmission・execution-intent・summaryは未生成であり、capacity受理を本計時の開始・完了とは扱わない。
controllerは生存・起動識別一致・errorなしで、後続の投入前処理265736がRとなった。
21:29 JSTのstate照合では対象は `c0t0e1-mc-main0` のsubmittingで、本計時job IDはまだ未記録だった。
stateのterminal6件はcapacity4件と先頭main2件を含み、独立本計時の完了件数は2/24のままである。
実状態観測はlocal `output/finite_tail_resume_controller_v1/window-observation-1792931353753952900.json` と同階層の `independent-state-1792931379173363600.json` に保存した。
22:03 JSTには投入前処理265736のR・経過34分21秒と、MC本計時rootのscript・upstream completion・submission intentの生成を確認した。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t0e1-main-submit-markers-1792933406199387200.json` に保存し、intentのSHA-256は `3eadc16077138dbf545f1ab41b8e5cf3c605a7fab5369e9b13e73f3d07840c96` である。
intentはqsubを指定し、script pin `9f7230db30a0b68fe0fb9933f8d2d9be4a9fd0418ae060ca692e1604ec323b73` とupstream記録pin `40a90cee8180b6dec4573fbc0eef46dff81cf0de2feb80d0c63303884a9a1438` が同観測に一致し、資源は1ノード・96 CPU・21 workers・337 GB・要求30分だった。
保存upstream記録は265703と265729のF/0・run_count=1を含むが、本計時のsubmission.jsonは未生成であり、intentを実投入や本計時開始の証拠とは扱わない。

## 2026-10-25 21:02 JSTの次精度条件BAR本計時資源計画

`c0t0e1-bar-capacity` の正式finish265735は実PBSでR・経過14分42秒、controllerは生存・起動識別一致・errorなしだった。
新しく生成された `resource-decision.json` は1,549 bytes・SHA-256 `8b2fd379a27b08482fc0969ca89264a7100c000e57f919406f4a93c0ab5d5d43` であり、反復0〜191の1 partition・96 CPU・実worker上限21・337 GB・要求1時間を記録した。
予備計時からの予測値831.417秒は本計時の実測や完了時刻の保証ではなく、正式受理・本計時の開始とも区別する。
同観測では `prepared-partition-0.json` と `completed.json` は未生成だった。
小原本観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t0e1-finish-markers-1792929745831024300.json`、実PBS・controller観測は同階層の `window-observation-1792929745695096700.json` に保存した。
独立本計時の正式受理済み件数は引き続き2/24であり、最終reportと科学的結論の確定は未完了である。

## 2026-10-25 20:43 JSTの次精度条件MC予備計時の正式受理

`c0t0e1-mc-capacity` の正式finish265733（00017-finish）はF/0・run_count=1・walltime41分24秒となった。
20:43:38 JSTの[小原本監査](../../output/census_active_node_migration_v1/MC_E1_CAPACITY_FINISH_AUDIT_ja.md)で、accepted・action completion・controls completedから容量proofと本計時manifestへの対応を確認した。
容量summaryの2 task成功と元265729のF/0・7分15秒、本計時のidentity `[0,0,1]`・replicate 0〜191の重複欠落なし、1 partition・21 workers・96 CPU・337 GB・30分の一致を確認した。
completedのSHA-256は `4fc32d4f806e316bf30649d22f625aa46e13edb0406de864454b17b7af3df791`、本計時manifestは `a47ce040a2f6ce1f7418f09dc90317924875e33bae6ba800405595806a7f7738` である。
小原本18点はlocal `output/census_active_node_migration_v1/mc-e1-capacity-finish-audit-1792928618950558400/` に保存し、監査JSONのSHA-256は `8861209b44d20e4c456787db24a8ed88fda00a569f30e8b6313becefb5fd458b` である。
source mapは既存監査のclosure digestと一致したが、実60sourceの再hashや科学rawの再読は行っていない。
監査時点で本計時rootのsubmission・execution-intent・summaryは未生成であり、正式capacity受理を本計時192反復の実行完了とは扱わない。
controllerは生存・起動識別一致・errorなしで、後続のBAR終了確認265734（00018-observe）がRへ進んだ。
20:47 JSTには265734のF/0・3分45秒と、BAR正式capacity finish265735（00019-finish）のRを確認した。
同照会でもcontrollerは生存・起動識別一致・errorなしであり、BARの正式capacity受理はまだ完了とは扱わない。

## 2026-10-25 20:18 JSTの本計時資源計画と監視手順

`c0t0e1-mc-capacity` の正式finish265733は実PBSでR、controllerは生存・起動識別一致・errorなしだった。
20:16 JSTには `resource-decision.json`（1,554 bytes、SHA-256 `2e314d6eb6555f615db234aa044cdf3550047d8921622a126a2f78803c9943c3`）が生成され、本計時192反復・1 partition・96 CPU・実worker上限21・337 GB・要求30分の資源計画を確認した。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t0e1-finish-markers-1792926980270627100.json` に保存し、同時点ではprepared-partition-0とcompletedは未生成だった。
これは予備計時からの資源決定であり、正式受理や本計時の実行結果、要求時間内の完了保証ではない。
台帳増加に備えて別名のread-only `observe_window.py` を用意し、現在の小metadata観測1回と独立した静的レビューを完了した。
原observerのSHA-256 `379cd9094d1df40c2f82cf6e0c46a1df38f6ac70db6d390acf19bf22ad974f89` は不変、新observerは `cde0277453058eaad2dbd052f3f2f6b5b59dcaa42eb25f4737708db922a06352` である。
観測原本 `output/finite_tail_resume_controller_v1/window-observation-1792926926031745600.json` のSHA-256は `8a1f94e4672211741300b8c63ef631c15f62d9358e7317a486d5d732a4516568` で、候補23件中10件のPBS照会とprocess identity一致を確認した。
原observer・本番処理は変更せず、全job監査の代替や上限超過・timeout等の実試験成功とは扱わない。
実行コマンドと範囲外jobの扱いは[再起動後の確認手順](cluster_resident_resume_2026-10-25_ja.md)へ追記した。
20:38 JSTに限定監視の外側応答をJSONとして読めない観測エラーが1回あったが、同じcontroller/jobの即時再照会と別の直接qstatで265733のR・起動識別一致・制御errorなしを確認した。
失敗と成功の記録は同observer階層の `window-observation-1792928290993861100.json`・`window-observation-1792928325243998000.json` に保持し、原因を断定せず、再起動・再投入・source変更は行っていない。

## 2026-10-25 20:05 JSTの次精度条件BAR予備計時終了

`c0t0e1-bar-capacity` 本体265731は実PBSでF/0・walltime7分49秒となり、小要約はplanned_tasks=2・recorded_tasks=2・failed=0・unavailable=0・execution_complete=true・all_estimates_available=trueを記録した。
小要約は2,284 bytes・SHA-256 `8a4bebf23746d5b4b0c610117ce83b222f609562f3a629f21ee8ff124ddb3969`、actual-pbs-endは603 bytes・SHA-256 `28306d9ff991cc7f07c9e120a0008e92b12348e15e4ff2bbc9ded0c16b0fe1bf` である。
小観測はlocal `output/finite_tail_resume_controller_v1/bar-c0t0e1-capacity-run-markers-1792926345496678200.json`、実PBS照会は同階層の `independent-state-1792926345691679100.json` に保存した。
20:01 JSTには同BARのexecution-intent・actual-pbs-start・native_preflightを同階層の `bar-c0t0e1-capacity-run-markers-1792926072472680800.json` に保存し、job ID265731、保存sectorとの一致と各mismatch・syndrome violation 0を確認した。
native確認は選択された1状態の有限反復であり、普遍的なdecoder決定性や全状態の再復号検証とは扱わない。
MC終了確認265732（00016-observe）はF/0・3分45秒となり、正式capacity finish265733（00017-finish）がRへ進んだ。
20:05 JSTでもcontrollerは生存・起動識別一致・errorなしで、265733はRだった。
目標相対RMSE10%のこの組ではMC/BARとも予備計時のF/0と小要約2/2が揃ったが、正式capacity finishと本計時192反復は未完了である。
同一小要約hashをjob結合や個別recordの監査証拠に読み替えず、最終科学検証は既存の後続PBS readerへ残す。

## 2026-10-25 19:57 JSTの次精度条件BAR予備計時開始

`c0t0e1-bar-capacity` の投入前検証265730（00015-submit）はF/0・walltime14分45秒で終了し、BAR予備計時本体265731がR・run_count=1となった。
同じidentityのMC終了確認265732（00016-observe）もRで、controllerは生存・起動識別一致・errorなしだった。
MC本体265729は実PBSでは既にF/0・7分15秒であり、stateのcapacity running2件を両本体が計算中という意味には読まない。
小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792925859118699500.json` に保存した。
19:58 JSTの実PBS照会で、BAR265731の2 CPU・340 GiBとMC終了確認265732の1 CPU・96 GiBが別2物理ノードに割り当てられ、両jobのrun_count=1と各96 CPU以内を確認した。
この2jobの照会結果をlocal `output/census_outer_operation_v1/c0t0e1-bar-capacity-pbs-1792925900950.json` に保存し、保存JSONのSHA-256は `a8535ccfba671d97a66e6f8081c718fb5811c0001ee8f2469d126dae1464489a` である。
BAR予備計時の2反復完了、両capacityの正式finish受理と当該精度条件の本計時は未完了である。

## 2026-10-25 19:49 JSTの次精度条件MC予備計時終了

`c0t0e1-mc-capacity` 本体265729は実PBSでF/0・walltime7分15秒となり、小scientific-summaryはplanned_tasks=2・recorded_tasks=2・failed=0・unavailable=0・execution_complete=true・all_estimates_available=trueを記録した。
小要約は2,284 bytes・SHA-256 `8a4bebf23746d5b4b0c610117ce83b222f609562f3a629f21ee8ff124ddb3969`、actual-pbs-endは601 bytes・SHA-256 `b0220070e816d53380af37d0bd842758b6e6dc22d3042980e1cd67df1528a43b` である。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-c0t0e1-capacity-run-markers-1792925386246698900.json`、実PBS照会は同階層の `independent-state-1792925385298292400.json` に保存した。
小要約はjob IDやmanifest digestを含まず、同じ件数の別capacityとhashが同じでも同一jobの証拠とは扱わない。
今回の限定確認は指定run rootの小記録と実PBS終端であり、個別結果の深い監査・正式finish受理・当該条件の本計時192反復は後続処理に残る。
controller stateのrunning表示は同時点の実PBS終端より遅れており、MCが引き続き計算中という意味には読み替えない。

## 2026-10-25 19:42 JSTの次精度条件の予備計時開始

`c0t0e1-mc-capacity` の投入前処理265728（00014-submit）はF/0・walltime14分47秒となり、MC予備計時本体265729がR・run_count=1へ進んだ。
対象はtile72 bit-flip、p=0.01、目標相対RMSE10%で、capacityは2反復、本計時は192反復という既存計画を維持する。
実PBS要求は1ノード・2 CPU・340 GB・24時間であり、Rを推定器taskの開始や2反復の完了とは扱わない。
同じidentityのBAR予備計時の投入前処理265730（00015-submit）もRとなった。
controllerは生存・起動識別一致・errorなし、stateはterminal4件・running1件・submitting1件・pending20件だった。
小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792924944843861800.json` に保存した。
本計時の正式finish受理まで完了した対象は引き続き先頭MC/BARの2件であり、上のstate件数を独立本計時完了件数とは読み替えない。
19:43:09 JSTの[実割当監査](../../output/census_outer_operation_v1/C0T0E1_CAPACITY_ALLOCATION_2026-10-25_ja.md)で、MC265729のstate・manifest・submission・scriptと実PBS command/resourcesの対応、BAR投入前helper265730の台帳・payload・実commandを照合した。
MCの2 CPU・340 GiBとhelperの1 CPU・96 GiBは別2物理ノードで、各96 CPU以内、配置未確定の所有jobなしだった。
小原本はlocal `output/census_outer_operation_v1/c0t0e1-capacity-allocation-1792924989512703700.json`、SHA-256は `8c780902e7468e5d929bcd195f6dbc2ad2a2cdc09040348bd9b0cab3d10c79c7` である。
MCのexecution-intent・actual-pbs-start・native_preflight・summary・failureは監査時点で未生成だった。
19:46 JSTにはMC265729のexecution-intent・actual-pbs-start・native_preflightを確認し、小観測をlocal `output/finite_tail_resume_controller_v1/mc-c0t0e1-capacity-run-markers-1792925163214281500.json` に保存した。
execution-intentのjob ID・script・submission hashは上の実投入監査に一致し、同原本SHA-256は `faeb4a1dc0e35caa626515a934e881e919278f17f9ee013de57527c752c7c1c9`、actual-pbs-startは `df348eeeb388a277733b7b53850d06462d3d1c0f161ac1662d3b31419ee442c6`、native_preflightは `90cf75cb5862e2b0aa229ce8834ac0ac46896d931c7d5a93bbcc91e4f730220d` である。
native probeでは保存sectorとの一致と各mismatch・syndrome violation 0を確認したが、選択された1状態の有限反復でありdecoderの普遍的決定性を証明しない。
同時点でscientific-summary・failure・actual-pbs-endは未生成であり、予備計時2反復の完了はまだ確認していない。

## 2026-10-25 19:27 JSTの先頭BAR本計時finish受理

BAR正式finish265727（00013-finish）はF/0・run_count=1・walltime23分02秒となり、[限定独立監査](../../output/census_active_node_migration_v1/BAR_MAIN_FINISH_AUDIT_ja.md)でactionのaccepted・completionからcontrolsのcompleted・terminal、既存collected copyへの原本一致を確認した。
manifest・submission・rootは先のBAR小原本監査と一致した。
小原本12点はlocal `output/census_active_node_migration_v1/bar-main-finish-audit-1792924049441551400/`、監査JSONのSHA-256は `b7a7dbc90b10d1100c0074433d514e010ab7471fa5d1ca69c329f89e7d8d4167` である。
completedのSHA-256は `83042d7fb42383085929544142a6641884e859f4608d48778040b3bf2640ce35`、terminalは `22015243389683ceccec5e03e0d3e665d1aa0ae7c0b976b9af9dde3524f5d792` である。
receiptは `main_terminal_recorded`・`scientific_validation_complete=false`・`raw_payloads_rehashed_now=false` を保持する。
receiptのsummary宣言pin `bfc7419f74537078b0dee0141d986e81095c963e9c65930a9b864f9fc7a47264` は記録したが、75,487,436 bytesの本体とrawを今回読み直しておらず、個別192recordの監査や精度gate・費用比較の完了とは扱わない。
先頭C0T0・目標相対RMSE20%のMC/BAR本計時は両方とも正式finish受理・回収まで完了した。
後続265728（00014-submit）がRとなり、stateはterminal4件・submitting1件・pending21件へ更新された。
terminal4件には先頭MC/BARのcapacity各1件とmain各1件を含み、独立本計時4件完了という意味ではない。
投入前処理の対象は `c0t0e1-mc-capacity`（tile72 bit-flip、p=0.01、目標相対RMSE10%）であり、当該capacity本体のjob IDはまだ記録されていない。
状態と実PBSの小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792924052154617900.json` に保存した。

## 2026-10-25 19:12 JSTの指定raw archive現存確認

BAR正式finish265727の実行中に、独立した小metadata監査としてportable7条件の指定273 ZIPをクラスタでlstatした。
全273件が通常file・非symlinkとして存在し、欠落・未観測各0、合計42,880,266,375 bytesだった。
観測原本と条件別容量は[raw保存先の追記](raw_access_followup_2026-10-25_ja.md)に保存した。
ZIP本体の読取り・再hash・展開・全directory走査は行っておらず、全12条件の全raw保存や内容一致の認定ではない。

## 2026-10-25 18:56 JSTの先頭MC本計時finish受理

先頭MC本計時265721の正式finish action265725はF/0・run_count=1・walltime22分51秒となり、[限定独立監査](../../output/census_active_node_migration_v1/MC_MAIN_FINISH_AUDIT_ja.md)でactionのaccepted・completionからcontrolsのcompleted・terminal、既存collected copyまでの原本一致を確認した。
manifest・submission・summaryのpinは先の192個別record監査と一致し、今回は科学summary本体とrawを再読していない。
completedのSHA-256は `9f69d00a3935af0932bd9c213efac87e987924f6f28b80531c643f78d9ebfbb7`、terminalは `3a5fcf526e51519893dc1fe87c6a0127ccb420fdbc9773cfe39771199aad80a2` である。
小原本12点はlocal `output/census_active_node_migration_v1/mc-main-finish-audit-1792922200060383600/` に保存し、監査JSONのSHA-256は `145b7a25613031499b91066438e9a1d7d99dd219deb7726270743ff8fe56296f` である。
receiptは `main_terminal_recorded`・`scientific_validation_complete=false`・`raw_payloads_rehashed_now=false` を記録しており、正式finish受理を最終科学検証の完了とは扱わない。
後続のBAR終了確認265726（00012-observe）はRで、controllerは生存・起動識別一致・errorなしだった。
19:04 JSTの実PBS照会では265726がF/0・walltime11分31秒となり、BAR正式finish265727（00013-finish）がRへ進んだ。
この時点でもcontrollerは生存・起動識別一致・errorなしであり、BAR finishの起動を正式受理の完了とは扱わない。
BARの正式finish受理、残る独立計時、精度gate・費用比較と最終reportは未完了である。

## 2026-10-25 18:47 JSTの先頭BAR本計時正常終了

先頭BAR本計時265723は実PBS照会でF/0・walltime29分52秒となり、scientific-summary.jsonでplanned_tasks=192・recorded_tasks=192・failed=0・unavailable=0・execution_complete=true・all_estimates_available=trueを確認した。
同原本は2,288 bytes・SHA-256 `ad24aa1ba7df8a065f1eb75a80f2fad62cc379dd4dc71c6ba90c37bd0f33ce24`、actual-pbs-end.jsonは611 bytes・SHA-256 `bda6967576231bc381e3ab528714a3395d0248402c796c37677130e0e37474a2` である。
小観測はlocal `output/finite_tail_resume_controller_v1/bar-main-run-markers-1792921620775537900.json`、状態と実PBSは同階層の `independent-state-1792921621016538600.json` に保存した。
先頭条件のMC・BARとも本計時jobのF/0と小要約の192件の記録が揃った。
18:48:13 JSTの限定独立監査で、BARのmanifest・実submission・script・実PBS終端の対応と、小scientific-summary原本の所在・hash・件数を確認した。
小原本11件はlocal `output/census_active_node_migration_v1/bar-main-result-audit-1792921693129783600/`、監査JSONのSHA-256は `53f64e49a1be7ea8709d48dd8a75b9984cb8e55818848de62ec5d88a07008bb9` で、同親階層の `BAR_MAIN_RESULT_AUDIT_ja.md` に範囲と限界を保存した。
BAR summary本体は75,487,436 bytesで4 MiB上限を超えるため、今回の限定監査では読取り・転送・hash計算を行っていない。
小要約単独にはjob ID・manifest digestがなく、個別192件の重複欠落・費用・full summaryとmanifest/terminalの結合、rawの深い検証と精度gate・比較は後続PBS readerと最終reportで確認する。
要求walltime30分に対する今回の実PBS walltimeは29分52秒であり、この成功を後続条件の予算内完了の保証とは扱わない。
MC正式受理265725はR・制御エラーなしで、両本計時の正式finish受理と独立計時全体は引き続き未完了である。

## 2026-10-25 18:17 JSTの先頭BAR本計時job開始

BAR本計時の投入前検証265722（00009-submit）はF/0・walltime46分04秒で終了し、本計時265723がqsubで投入されてR・run_count=1となった。
実PBSの要求は1ノード・96 CPU・337 GB・30分で、先に受理した192反復・worker上限21の計画に対応する。
submission.jsonは13,342 bytes・SHA-256 `090d208bfe21edf9651a195d816146baf4b412c0b8830dc95af5da692617bc12` で、小観測はlocal `output/finite_tail_resume_controller_v1/bar-main-submit-markers-1792919840464201600.json` に保存した。
後続265724（00010-observe）がRとなり、controller stateはcapacity terminal2件・main running2件・pending22件で、制御プロセスは生存・起動識別一致・errorなしだった。
実PBSでは先頭MC main265721はF/0であり、stateのrunning表示を実計算継続とは解釈せず、正式finish受理と区別する。
状態と実PBSの小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792919840669203000.json` に保存した。
18:18:18 JSTの独立監査で、BARのstateからmanifest・submission・script・実PBSのSubmit_argumentsと資源要求への結合を確認した。
265722は18:16:08にF/0で終了してactive jobsから解放済み、BAR本計時265723は18:16:39、MC終端確認helper265724は18:16:41に開始した。
BAR本計時の96 CPU・337 GiBとhelperの1 CPU・96 GiBは別2物理ノードに配置され、各96 CPU以内で、配置未確定の所有jobもなかった。
小原本はlocal `output/census_outer_operation_v1/bar-main-two-node-observation-1792919898499735300.json`、SHA-256は `07f324a3087d74cecebf4f5645cbb39f72632ac3c5e8f01a45f369cfe221ea2d` で、詳細は同階層の `BAR_MAIN_ALLOCATION_2026-10-25_ja.md` に保存した。
監査時点でBARのexecution-intent・actual-pbs-start・native_preflight・summary・failureは未生成であり、BAR本計時のRを推定器task開始や192反復完了とは扱わない。
18:27:40 JSTにはBAR execution-intent.json（457 bytes、SHA-256 `20cb9a0eb9a002a3be5d8409df94132a9afad931b128d1577d991116f6fd730c`）とactual-pbs-start.json（609 bytes、SHA-256 `9141b629a1013094a743039223bb09d9a3869bc2e8315830e991368e61fe808e`）の生成を確認した。
execution-intentのjob ID・intent・script・submission hashは上記265723の実投入記録に一致し、local `output/finite_tail_resume_controller_v1/bar-main-run-markers-1792920459721163300.json` に小観測を保存した。
同時点でBAR native_preflight・scientific-summary・failure・actual-pbs-endは未生成で、実行開始記録の生成を192反復完了とは扱わない。
18:28:59 JSTにはMC終端確認265724（00010-observe）のF/0・walltime11分29秒と、正式受理処理265725（00011-finish）のRを確認した。
controller stateはMC mainがfinishing、BAR mainがrunning、capacity terminal2件・pending22件で、制御エラーはない。
状態と実PBSの小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792920539002734100.json` に保存し、MC正式finish受理は引き続き未完了として区別する。
18:32:00 JSTにはBAR native_preflight.json（3,645 bytes、SHA-256 `955e474bb23a72ab6ca2de59aff16cc0067eacd8eeeb54d72b01161f94e65a58`）の生成を確認し、local `output/finite_tail_resume_controller_v1/bar-main-run-markers-1792920719521287900.json` に小観測を保存した。
保存済みsectorとの一致、decoder probeの各mismatchとsyndrome violationが0であることを確認したが、原本warningどおり単一選択状態での限定確認であり、一般的な決定性の証明ではない。
BAR scientific-summary・failure・actual-pbs-endは同時点で未生成で、BAR本計時265723とMC正式受理265725はR・制御エラーなしだった。

## 2026-10-25 17:57 JSTの先頭MC本計時正常終了

先頭MC本計時265721は実PBS照会でF/0・walltime26分53秒となり、scientific-summary.jsonでplanned_tasks=192・recorded_tasks=192・failed=0・unavailable=0・execution_complete=true・all_estimates_available=trueを確認した。
同原本は2,288 bytes・SHA-256 `ad24aa1ba7df8a065f1eb75a80f2fad62cc379dd4dc71c6ba90c37bd0f33ce24`、actual-pbs-end.jsonは609 bytes・SHA-256 `6c9cee65134a313d5963231bda46f88aba3aa802ece619ea86b9150ac06dab13` である。
小観測はlocal `output/finite_tail_resume_controller_v1/mc-main-run-markers-1792918626056130100.json` に保存した。
17:58:24 JSTの独立照会でF/0・run_count=1を確認し、main manifest・実submission・PBS終端・192件の結果と費用記録の結合監査を完了した。
replicate 0から191までの全192件は予定と一致し、重複・欠落なし、全件status=ok・available=true・failure=nullだった。
原本はlocal `output/census_active_node_migration_v1/mc-main-result-audit-1792918704434460000/`、監査JSONのSHA-256は `4c10d1f4e7c0ef10f7226d7fe544248ab34268958e758ee967375755384d874b` で、同親階層の `MC_MAIN_RESULT_AUDIT_ja.md` に限定範囲を保存した。
summary.jsonは3,172,160 bytes・SHA-256 `82151bf1d214682298e6c564eae57477e289beced3a1531f16a6c5f74cd5297f` で、execution wall 1610.983415秒、pool wall 29.472078秒、outside pool wall 1581.511338秒を記録する。
job内で保存したactual-pbs-endの状態はRであり、F/0の証拠には独立照会原本を使い、費用指標を同一視せず、rawの再検証や精度gate・比較優劣の判定は今回の監査に含めない。
これは先頭条件のMC本計測の完了であり、残る本計測や最終精度gate・費用比較の完了ではない。
controllerはBAR本計時の投入前検証265722を実行中で、error記録はない。
同時点のcontroller stateはMC mainをrunningと表示していたが、実PBSのF/0を確認しており、正式finish受理は後続処理として区別する。
18:05:34 JSTにはBAR mainのupstream-completion-at-submit.json（1,312 bytes、SHA-256 `5aa2662d99749e6535493298eb7c96445fa304e0a71629bf9f80ded4077c6e76`）とsubmission-intent.json（13,307 bytes、SHA-256 `f41af2d1ac5b717e4c67f1ac8dd9044116af8ad95e2b4c1f7ecdbf623b36f390`）の生成を確認した。
BAR timing.shは2,071 bytes・SHA-256 `b2e7a2122e110cd59a2ea121b53c0cf667d2eff18bbe8ab711512ee67885515f` で、小観測はlocal `output/finite_tail_resume_controller_v1/bar-main-submit-markers-1792919134704447300.json` に保存した。
同時点でBAR submission.jsonは未生成、265722はR・制御エラーなしであり、投入intentを実qsub投入とは扱わない。

## 2026-10-25 17:30 JSTの先頭MC本計時job開始

MC本計時の投入前検証265719（00008-submit）はF/0・walltime45分36秒で終了し、計測本体265721がqsubで投入されてR・run_count=1となった。
実PBSの要求は1ノード・96 CPU・337 GB・30分で、生成済み192反復・worker上限21の計画に対応する。
submission.jsonは13,341 bytes・SHA-256 `afc1e2eea76cf414f301899e443d640467247989590c03f5d4ed4df525a3f091` で、小観測はlocal `output/finite_tail_resume_controller_v1/mc-main-submit-markers-1792917040159724000.json` に保存した。
controller stateはcapacity terminal2件・本計時running1件・submitting1件・pending22件で、次のBAR本計時投入前検証265722（00009-submit）がRとなった。
制御プロセスは生存・起動識別一致・errorなしで、状態と実PBSの小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792917040186723900.json` に保存した。
この段階のRはPBS jobの開始であり、推定器taskの計測開始や192反復の完了はまだ確認していない。
17:31:46 JSTの独立監査で、stateからmanifest・submission・script・実PBSのSubmit_argumentsと資源要求への結合を確認した。
265719は17:29:33にF/0で終了してactive jobsから解放済み、MC本計時265721は17:30:01、BAR投入前検証265722は17:30:03に開始した。
MC本計時の96 CPU・337 GiBとhelperの1 CPU・96 GiBは別2物理ノードに配置され、各96 CPU以内で、配置未確定の所有jobもなかった。
小原本はlocal `output/census_outer_operation_v1/main-two-node-observation-1792917106380261800.json`、SHA-256は `9f725014c71f28f1d7874c48437842c0c6b5845ac7ba9ad4ea12df586df81428` で、詳細を同階層の `MAIN_ALLOCATION_2026-10-25_ja.md` に保存した。
監査時点でexecution-intent・actual-pbs-start・native_preflight・summary・failureはいずれも未生成であり、PBSのRを推定器task開始や結果成功とは断定しない。
17:42:56 JSTの小観測ではexecution-intent.json（457 bytes、SHA-256 `bd6329a2de888b2e2f780907958eb7fc8254c3d41e66866b7004f2a5cb5819b5`）とactual-pbs-start.json（608 bytes、SHA-256 `73e4de0cfe651526d4333bd41b56b5ce99f9380130e27cc98d8a27adbe225441`）の生成を確認した。
execution-intentのjob ID・script・submission hashは上記265721の実投入記録に一致し、観測をlocal `output/finite_tail_resume_controller_v1/mc-main-run-markers-1792917776579320700.json` に保存した。
同時点でnative_preflight・scientific-summary・failure・actual-pbs-endは未生成で、MC本計時265721とBAR投入前検証265722はR・制御エラーなしだった。
実行開始記録の生成を推定器task poolの開始や192反復完了とは扱わない。
17:45:54 JSTにはnative_preflight.json（3,645 bytes、SHA-256 `83595bd6508d318878f6ff648581afee4fcfb05b32fa66ff3bc82f78edc90ea2`）の生成を確認し、local `output/finite_tail_resume_controller_v1/mc-main-run-markers-1792917953262472200.json` に小観測を保存した。
保存済みsectorとの一致、decoder probeの各mismatchとsyndrome violationが0であることを確認したが、原本のwarningどおり単一選択状態を使った限定確認であり、一般的な決定性の証明ではない。
scientific-summary・failure・actual-pbs-endは同時点で未生成であり、192反復の完了と計時結果は未確認である。

## 2026-10-25 17:08 JSTのMC本計時投入script生成

MC本計時rootのtiming.shは17:06:27 JSTの観測では未生成だったが、17:08:12 JSTには2,068 bytesの新規生成を確認した。
SHA-256は `df889600d05c58b30714c49d042c15b9143e30a7babbecab61f1d30586585f88` で、生成状況の小観測はlocal `output/finite_tail_resume_controller_v1/mc-main-submit-markers-1792915692929832400.json` に保存した。
同時点でupstream-completion-at-submit.json・submission-intent.json・submission.jsonは未生成、投入前検証265719はR・controllerにerrorなしだった。
固定sourceの静的確認ではtiming.sh生成後にも入力再検証と資源確認があり、投入scriptの生成を実qsub投入や本計測開始とは扱わない。
検証経路・中間記録・helperと計測本体の時間枠の区別はlocal `output/finite_tail_census_recovery_v1/INDEPENDENT_SUBMIT_CALLGRAPH_ja.md` に保存した。
17:19:20 JSTにはupstream-completion-at-submit.json（1,311 bytes、SHA-256 `9c5597883c8611443057d9e5c4dc971d079ce7e7bb84001fd5aa8f1b0efeb5a4`）とsubmission-intent.json（13,306 bytes、SHA-256 `fc80fa627b400ce4651a922b4d228016c40da0dd300ed5c4cf319951d4df174a`）の生成を確認した。
intent内のscript hashは上記timing.shに一致し、小観測はlocal `output/finite_tail_resume_controller_v1/mc-main-submit-markers-1792916360019441800.json` に保存した。
submission.jsonは引き続き未生成、265719はR・controllerにerrorなしであり、intent保存を実qsub投入とは扱わない。

## 2026-10-25 16:44 JSTの先頭BAR finish正常終了とMC本計時投入前検証

BAR capacityのfinish action265718（00007-finish）はF/0・walltime41分36秒で終了し、controlsのcompleted.jsonが生成された。
同原本4,834 bytesのSHA-256は `f7da12e3ea0644cdd97f434166dc1602e9bd687a5a37fa9a7d28a0ad23edbe97` で、小観測はlocal `output/finite_tail_resume_controller_v1/bar-finish-markers-1792914220819114000.json` に保存した。
prepared-partition-0.jsonは1,084 bytes・SHA-256 `d7f5e13a27823967d06775af4f814afb97ce67f6cd68561d58044422233b6e34` で、identity [0,0,0]・replicate 0から191・1 partition・96 CPU・worker上限21・337 GB・30分の計画を記録している。
記録された本計時manifestのSHA-256は `bf7db95de15db8f5a220c2e1f9baf3070408a69e79f9f24ca0bbbc6709b4ac83` である。
16:47:41 JSTの独立監査で、正式受理・action completion・controls completed・元capacity proof・192反復manifestの結合を確認した。
acceptedのSHA-256は `bb5759b83be62fb1721f926bb5d6f3cb7909d0794acd617c60e80c500e27f728`、action completionは `c034399cc9ebadd822cbd7374431ddc5693fe49349e5fbf24b73dbaffde6b5b1` で、小原本18件をlocal `output/census_active_node_migration_v1/bar-capacity-finish-audit-1792914461448805900/` に保存した。
265718と元capacity265714のF/0・run_count=1、容量時と本計画のsource pin60件および現在ファイルのhash一致も確認し、計画受理を本計測実行完了とは扱わない。
監査JSONのSHA-256は `5302ec536e54d202325d296e3c050dda842295d6b74b4d5d17198021227feff5` で、詳細はlocal `output/census_active_node_migration_v1/BAR_CAPACITY_FINISH_AUDIT_ja.md` に保存した。
後続265719（00008-submit）はRとなり、controller stateは先頭MC/BAR capacityがterminal、MC本計時がsubmitting、pending23件へ進んだ。
この時点でMC本計時のjob IDはまだなく、265719は投入前検証用の補助jobである。
制御プロセスは生存・起動識別一致・errorなしで、状態の小観測はlocal `output/finite_tail_resume_controller_v1/independent-state-1792914244538696200.json` に保存した。
準備完了や投入前検証を192反復の本計測完了とは扱わず、独立計時全体と最終reportは引き続き未完了である。

## 2026-10-25 16:17 JSTの先頭BAR本計時資源計画生成

BAR finishのresource-decisionが生成され、status=ready、replicate0から191までの192反復を1 partition・実worker21・要求96 CPU・337 GB・30分とする計画を確認した。
原本1,554 bytesのSHA-256は `6be6493d083060ea21d99b234c428cf729fc434b0cd5b011a97ad7df4d189089` で、内容と生成状況の小観測をlocal `output/finite_tail_resume_controller_v1/bar-finish-markers-1792912630117461200.json` に保存した。
prepared-partitionとfinish completedは未生成で、265718はR・controllerにerrorなしだった。
これは資源計画の生成であり、本計時manifestの正式受理・投入・実行完了ではない。

## 2026-10-25 16:02 JSTのMC本計時計画正式受理とBAR finish開始

MC finishの独立監査で、265716のF/0・run_count=1、acceptedからcompletion・controls completed・本計時manifestへのhash結合を確認した。
本計時のidentityは[0,0,0]、replicateは0から191までの全192件で、1 partition・96 CPU・worker21・337 GB・30分要求の計画と一致した。
capacityの2/2成功結果・正式terminalと本計時capacity proofの対応も確認し、小原本18件と監査結果をlocal `output/census_active_node_migration_v1/mc-capacity-finish-audit-1792911711939257400/` に保存した。
監査JSONのSHA-256は `81ce9eb7f0b96dba9279df201b5472cedfc851f611e13871b8cfcd40f5c76c8a` で、巨大科学payloadの再読・再hashはしていない。
状態確認265717はF/0・walltime3分46秒で終了し、BAR capacityのfinish action265718（00007-finish）がRになった。
controller stateはMC capacityがterminal、BAR capacityがfinishing、本計時1件を含むpending23件で、制御プロセスにerrorはない。
本計時の実投入・実行はまだ未確認であり、計画受理を192反復の実行完了とは扱わない。

## 2026-10-25 15:58 JSTの先頭MC finish正常終了

先頭MC capacityのfinish action265716（00005-finish）はF/0・walltime41分27秒で終了した。
controls結果のcompleted.json（4,823 bytes）の生成を確認し、SHA-256は `c1a1fbfdba90a2f14c03cb43360114b0bf4776c9b87eaca37b24709ff42e9036` である。
中間マーカーと完了記録の小観測はlocal `output/finite_tail_resume_controller_v1/mc-finish-markers-1792911520979734900.json` に保存した。
後続の状態確認action265717（00006-observe）がRで、controllerは生存・起動識別一致・errorなしだった。
完了記録から本計時計画と正式回収への結合を独立監査中で、本計時の投入・実行はまだ未確認である。

## 2026-10-25 15:48 JSTの先頭MC本計時資源計画確認

MC capacityのfinish処理はresource-decisionを生成しており、status=ready、192反復を1 partition、実worker21、要求96 CPU・337 GB・30分という本計時計画を確認した。
原本1,551 bytesはlocal `output/finite_tail_census_recovery_v1/independent-finish-source/resource-decision-original.json` に保存し、SHA-256は `e3a9b5ffbed67f648a5bfaa72cbbac4659c858153bad4d147485ac5d65313248` である。
これはcapacity受理とresource決定までの中間証拠で、prepared-partition・finish completed・本計時の投入は監査時点では未確認である。
固定sourceの読取り監査では今回の成功finishは大入力検証11回と追加hash走査を行う構成で、resource-decision保存後にも本計時manifestの作成・再読検証が残る。
この回数を実行済み回数や物理ディスクI/O量、完了ETAとは扱わず、local `output/finite_tail_census_recovery_v1/INDEPENDENT_FINISH_CALLGRAPH_ja.md` に根拠source pin・途中記録・同root再開不可の制約を保存した。
実行中の265716と固定source/configは変更せず、正式finish完了と後続投入を待つ。
15:55 JSTには `prepared-partition-0.json` の生成を確認し、本計時manifestの作成・再読検証まで進んだ。
同マーカーは1,082 bytes、SHA-256は `ee4d94ff3c7f2855f8b3cf5b39f67d6c3fb153c56e2de66b72e34feb7b1d6dc2` で、小原本内容と生成状況をlocal `output/finite_tail_resume_controller_v1/mc-finish-markers-1792911322727004200.json` に保存した。
この時点ではfinish completedは未生成で、265716はR・controllerにerrorなしのため、最後の入力再検証とPBSの正式終端を待つ。

## 2026-10-25 15:20 JSTの先頭BAR予備計時正常終了

先頭BAR capacityのjob265714はF/0・walltime7分24秒で終了し、MCとBARの先頭予備計時がそれぞれ2反復を完了した。
BAR summaryはplanned_tasks=2・recorded_tasks=2・failed=0・unavailable=0・execution_complete=true・all_estimates_available=trueを記録している。
小原本7件をlocal `output/finite_tail_resume_controller_v1/first-bar-capacity-completed-1792909268183359900/` に回収し、取得bytesのSHA-256一致を確認した。
BAR summaryのSHA-256は `94ab8ae49eef0d4af93ff3b1a528d1f74374347c4f1e4ca47d6d2ea164f4f256` で、pool wallは14.716秒、pool外は427.163秒だった。
この2反復の予備結果だけで同じ精度での速度比や被覆を結論づけず、本計時の独立192反復と最終科学readerによる受理を待つ。
MCの回収・受理action265716は引き続きRで、本計時の生成・実行はまだ未確認である。

## 2026-10-25 15:12 JSTの先頭BAR予備計時ジョブ開始

BARの投入前検証helper265713はF/0・walltime14分46秒で終了し、先頭BAR capacityのjob265714がR・run_count=1・2 CPU・340 GiB・1ノードとなった。
次の状態確認action265715（00004-observe）もRで、controllerは生存・起動識別一致・errorなしだった。
MC265712のF/0は保持されており、state上のrunning2件を稼働中の科学job2件と解釈せず、実PBSではMC終了・BAR実行中を区別する。
小状態記録と実PBS照合はlocal `output/finite_tail_resume_controller_v1/independent-state-1792908750813360300.json` に保存した。
予備計時の正式受理、本計時の生成・実行と最終科学評価は未完了である。

## 2026-10-25 15:05 JSTの先頭MC予備計時正常終了

先頭MC capacityのjob265712はF/0・walltime7分16秒で終了した。
生成済みsummaryはplanned_tasks=2・recorded_tasks=2・failed=0・unavailable=0・execution_complete=true・all_estimates_available=trueを記録している。
小原本をlocal `output/finite_tail_resume_controller_v1/first-capacity-completed-1792908322941100400/` に回収し、summaryのSHA-256は `0bbbadbb8e7122ccf0051012b329d9e934538cee6a9a3ed45ff0e694d6867bb6`、scientific-summaryは `8a4bebf23746d5b4b0c610117ce83b222f609562f3a629f21ee8ff124ddb3969` である。
実行記録のpool wallは3.415秒、pool外は427.139秒であり、job全体の7分16秒を推定器そのものの計算費用と混同しない。
次BARの投入前検証helper265713は引き続きRで、controller上の先頭taskはまだrunning表示だったため、正式回収・capacity受理・本計時partition生成は後続処理で確認する。
この2反復の予備計時を独立192反復の校正や計時全体の完了とは扱わない。

## 2026-10-25 14:58 JSTの予備計時ジョブ開始

先頭MCの投入前検証265711はF/0・walltime14分39秒で終了した。
先頭の `c0t0e0-mc-capacity` はjob265712でR・run_count=1・2 CPU・340 GiB・1ノードを確認した。
次のBAR capacityはsubmittingとなり、その投入前検証helper265713がRだった。
capacity taskはrunning1件・submitting1件・pending22件で、独立本計時の完了を意味しない。
小状態記録と実PBS照合はlocal `output/finite_tail_resume_controller_v1/independent-state-1792907883360168200.json` に保存した。
14:59 JSTの独立監査では、265712とhelper265713が別物理ノードに割り当てられ、同時使用2ノード・各96 CPU以下を確認した。
科学task・manifest・submission・scriptと実PBS jobを結合し、小証拠をlocal `output/census_outer_operation_v1/two-node-independent-observation-1792907955668032100.json` に保存した。
この時点の本体execution-intent・actual-pbs-startは未生成であり、PBSのRを推定器自体の計測開始や成功と同一視しない。
controllerは生存・起動識別一致・errorなしで、計時結果と最終科学評価は引き続き未完了である。

## 2026-10-25 14:41 JSTの独立計時準備完了

準備job265709はF/0・walltime3時間00分53秒で終了し、preparation roleはreturncode=0、controllerは独立計時のexecution roleへ進んだ。
全24件の行別マーカー、prepared-inventory、prepared-receiptの生成を確認した。
小原本8件をlocal `output/finite_tail_resume_controller_v1/preparation-completed-1792906940834427900/` に回収し、全8件の取得前後hash一致、receiptからinventory、acceptedからcompletion・terminalへのhash結合を確認した。
prepared-inventoryのSHA-256は `82e5b3b884495bdbddfba49eb564c1deca73d93490604a2b3262dae048222d42`、prepared-receiptは `28484dd5ba1e1cb183d80d20f725575512b5e40bc43c1b7b06efa8684d825561`、action受理記録は `9266fd2c948647ff2f98aec21adb0a96f8be7a008a5cc97830ec5054f5da00c1` である。
inventoryは全48手法行を保持し、ready24行・not_selected24行、各行の予定capacity2反復・benchmark192反復とcapacity manifest24件を確認した。
receiptの `independent_timing_executed=false` のとおり、この準備完了は予備・本計時の実行完了ではない。
14:43 JSTの独立監査では、capacity24 taskの先頭1件がsubmitting、残り23件がpendingで、本計時partitionは未作成だった。
稼働中の投入前検証helper265711は1 CPU・96 GiB・1物理ノードで、capacity本体の投入台帳はまだ未生成だった。
この観測範囲では2物理ノード上限を遵守しており、小証拠をlocal `output/census_outer_operation_v1/first-independent-submit-observation-1792906995689926000.json` に保存した。
独立計時の実投入・資源配置・結果、最終reportと科学証拠保存は引き続き未完了である。

## 2026-10-25 11:40 JSTの独立計時準備開始

censusの確定action265707はF/0・run_count=1・walltime15分46秒、回収action265708はF/0・run_count=1・walltime2秒で終了した。
v13 controllerのcensus実行roleはreturncode=0となり、独立計時の準備roleへ進んだ。
11:43 JSTの独立監査でdescriptorから元265703のresult・completionへの結合、回収13ファイルの原本一致、回収manifest21項目のhash一致と正式受理を確認し、[census保存資料](data_tile_validation_2026-10-17/low_timing_full_census_v13_20261025/README_ja.md)へ追記した。
準備job265709はqsubでR・run_count=1・walltime10秒を確認し、controllerは生存・起動識別一致・errorなしである。
これは計時の入力・制御構成の準備であり、予備計時や独立192反復の本計時の開始・完了ではない。
その後、入力rootにrequest・timing-config・planned-inventoryが生成されたことを確認し、25,190 bytesのplanned-inventoryだけを回収した。
計画は48手法行を保持し、readyが24行、not_selectedが24行、全行に予備計時2反復・本計時192反復の予定分母を記録する。
対象外の予定分母を実行済み反復と解釈せず、準備完了・実際の投入と結果は別途確認する。
計画原本のSHA-256は `c7843412b596b943eb26ff9d5a5ac913a56e9542336356d3bdabdbc2b3f09afd`、local保存先は `output/finite_tail_resume_controller_v1/independent-plan-1792896639118752000/planned-inventory.json` である。
準備処理の静的確認ではeligible24行を逐次処理し、各行で大入力を含む検証を2回行うため、`preparation.prepare` 内の `inputs` 呼出し予定は初回を含め49回である。
これは呼出し構造の確認であり49回の実行完了を意味せず、page cacheがあるためbyte走査量を物理ディスクI/O量とは同一視しない。
265709のwalltime22分19秒の観測では先頭MC/BARの2行に検証完了マーカーが存在し、そのmtime差は456.2秒だった。
14:36 JSTの小metadata観測では行別マーカーが23/24件へ増え、JSONとして読める各原本とhashをlocal `output/finite_tail_resume_controller_v1/independent-markers-1792906606254674100.json` に保存した。
この行別進行を全対象の準備完了や予備・本計時の実行済み反復とは扱わず、全体のprepared-inventory・prepared-receiptはまだ未生成である。
全行のprepared-inventoryは24行終了後、control rootは次roleで生成するため、途中の不在だけを失敗とは判定しない。
実要求は1 CPU・96 GB・4時間で、途中物をskipして同じrootへ再実行する契約はないため、現jobを保持して正常終端を待つ。
これらはlocal `output/finite_tail_census_recovery_v1/INDEPENDENT_PREPARE_CALLGRAPH_ja.md` に根拠source pinとともに保存し、4時間枠や1区間の実測を完了ETAとは扱わない。
最新の小観測原本はlocal `output/finite_tail_resume_controller_v1/observation-1792896037934918100.json` に保存した。
準備投入台帳のSHA-256は `36b7e4b02a0dc973f96e9f3469c0f1bc5eaf6a21c4c2a5c7335bb14354b28ea4` である。
48手法行の状態と分母、全12条件の最終評価、最終科学証拠・再現手順の統合保存は未完了である。
準備待機と並行し、[最終報告草案](final_validation_report_draft_2026-10-24_ja.md)第4節へ符号・noise・decoder API・利用例・受入範囲の対応表を追加した。
追加decoder関連9 sourceとtile workflowの保存済み受入hashとの一致を確認し、有限受入をBAR校正へ拡張せず、tile288の新CLI実native再実行は未実施と明記した。
[再現資料の取得索引](reproduction_access_inventory_2026-10-25_ja.md)にはv13差分・完了census・24行射影の取得起点を追加し、公開版・working tree・private原本を区別した。

## 2026-10-25のcensus正常終了と比較表回収

census265703はF/0・run_count=1・walltime40分47秒・CPU時間24分27秒で終了し、全件結果・小catalog・manifestとcompletion前後の記録・実PBS終端の結合を独立監査でも確認した。
[全件照合の保存資料](data_tile_validation_2026-10-17/low_timing_full_census_v13_20261025/README_ja.md)へ結果原本と根拠hash、確認範囲・限界を記録した。
controllerは生存・起動識別一致・errorなしで、後続の確認action265704（`00002-observe`）はF/0・walltime3分58秒で終了した。
続く確定action265707（`00003-seal`）はR・run_count=1・walltime27秒を確認した。
独立計時のrole開始と後段正式受理はこの時点ではまだ未確認である。

比較表の受入265705は18 fixtureが成功してF/0、実抽出265706もF/0・run_count=1・walltime20秒・CPU時間19秒で完了した。
既存selectionだけをPBS内で読み、前後のhash・stat一致を確認して24行を抽出し、元の5 GB result・rawや再選択・再集計は使っていない。
JSON115,511 bytesと日本語表5,033 bytesはlocal `output/accepted_selection_projection_v1/actual-evidence/results/` へ回収し、[共有用の小成果物と受入証拠](data_tile_validation_2026-10-17/accepted_selection_projection_v1_20261025/README_ja.md)にも識別子置換前後のhashを付けて保存した。
case0/2（tile72）の12行が選択され、case1/3（tile288）の12行は `ineligible_reference_width` として非選択理由を保持する。
選択された12行も全て診断flag192/192であり、診断・被覆filterを適用しない元selectorによる計時候補の選択であって推奨設定や独立校正とは扱わない。
全条件の元評価と24行の候補選択を区別して日本語報告へ統合し、残る独立計時・最終report・科学証拠の保存を進める。

## 2026-10-25 11:15 JSTの全件stream照合結果

census265703の[全件stream結果](data_tile_validation_2026-10-17/low_timing_full_census_v13_20261025/result.json)が生成され、予定4,208,002件を全件検査し、未検査0・予期しない衝突0・意図した共有8,448件・一意seed4,199,554件だった。
stream処理の実測は1,365.132秒で、結果原本のSHA-256は `4d1e7bb7ce49f6332f49682d4f55592256b7376bc8ce27ae7eacc56b059dc476`、stream SHA-256は `a3c81da49255ca658c0cca6e56601149a1915c58cd6ea44759109bde06b26999` である。
この1781 bytesの結果には個人・接続先識別子がなく、原本bytesをそのまま保存した。
これは有限な予定seedの重複検査であり、統計的独立性の証明や実sampling metadata全件の監査とは異なる。
同時点ではjobはR・run_count=1・PBS記録walltime36分20秒で、最終入力・source照合後の `completion.json` と終端F/0はまだ未取得である。
後続controllerによる受理と独立計時への移行を待ち、比較表抽出の別担当も終端確認後に既存gateを通してqsubする。
全件streamの完了を独立計時・最終報告・goal全体の完了とは扱わない。

## 2026-10-25 10:51 JSTの実行確認と残成果物

全件census265703はR・run_count=1・PBS記録walltime11分27秒・CPU時間11分24秒で、`execution-intent.json` と `actual-pbs-start.json` の生成を確認した。
`completion.json` と `failure.json` はこの時点では存在せず、完了件数・衝突検査結果は未確定である。
小原本はlocal `output/finite_tail_resume_controller_v1/census-child-1792893070031778400.json`、SHA-256 `92dddea3ad7e6a235226de36827c31e71b5ae3c049def379f75d395394eaea6c` に保存した。
同じ確認区間にv13 controllerの生存・起動識別一致・errorなしと、準備265700・投入前検証265702のF/0を再確認した。
受理済みselectionから24行の保存値を取り出す処理は仕様・実装・18 fixtureを準備したが、fixtureと実抽出は未実施である。
既存aux投入制御が実行中censusのvnode未指定selectを扱わないため、制御や本番jobを変更せず終端後に同じ未投入stageで再照合する。
この24行表は設定選択cohortの説明であり、独立計時や非選択条件を含む全12条件の科学評価を置き換えない。
残りは全件censusの受理、独立計時48行・各192分母、全条件の最終結論、科学証拠・再現資料の保存であり、goalは未完了である。

## 2026-10-25 10:39 JSTの全件censusジョブ開始

投入前検証265702はF/0・run_count=1・walltime14分44秒・CPU時間14分40秒で終了した。
全件census本体はqsub265703でR・run_count=1・walltime26秒・CPU時間25秒を確認し、要求資源は1 CPU・96 GiB・4時間である。
controllerのPID1598334・start ticks770092111の一致、生存とerrorなしも確認した。
この観測時点では内側の `execution-intent.json` は未作成で、jobの初期入力検証中であり、全件streamを検査済みという意味ではない。
全予定4,208,002件の完了・衝突検査結果、独立計時48行と各192分母、最終reportと科学証拠保存は未完了である。
本体jobの小原本はlocal `output/finite_tail_resume_controller_v1/census-child-1792892352499140400.json`、SHA-256 `69908c31d073244fd4b74c6ee787f14f2f692f51ab681ba08c8d7b8417da7c8c` に保存した。
元12worker・比較結果を再実行せず、クラスタ内で後続処理を継続している。
全体ETAは未定で、要求walltimeを完了時刻の予測とは扱わない。

2026-10-25の[公開状態の読取り確認](publication_state_check_2026-10-25.json)では、GitHubはpublic・非archive、Release `v0.1.0.dev5` は非draftのprereleaseで5 assetsを保持し、mainは `837a96b8836ba8c81043fcba15b065eb1a8b5296` だった。
この確認はAPI metadataの照合であり、配布物bytes・CI・Zenodoの再検証や新規公開・pushは行っていない。

## 2026-10-25 10:24 JSTの準備完了と次工程

初回の準備265700はF/0・run_count=1・walltime10分15秒・CPU時間10分10秒で終了し、controllerの準備roleもreturncode=0となった。
v13 controllerのPID・起動識別情報の一致、生存とerrorなしを確認し、次の投入前検証265702がqsubでR・run_count=1・walltime26秒まで進んだ。
265702は全件census本体を投入するための検証actionであり、このR観測を全件照合の開始・完了とは扱わない。
新manifestはstatus=ready、新規割当244,440、予備1,000件のunexpected collision=0で、運用資源96 GiB・4時間と元式の候補16 GiB・45分を区別して記録している。
manifestのSHA-256は `5bee7685b66ed00329a200221aa9e49f9c854d47a4a65febe86c051c67e3f3da` であり、全予定4,208,002件のcensusは未完了である。
元12worker・比較・handoffは保持し、独立計時48行・各192分母、最終report、最終科学証拠の保存は残る。

[v13復旧差分保存](finite_flow_v13_delta_snapshot_acceptance_2026-10-25_ja.md)265701はF/0・run_count=1・1秒で、10 fixtureとsource参照92件・metadata217件のprivate保存を完了した。
保存は復旧コード・設定・投入証拠の有限範囲で、科学payloadや過去ZIPの再読取り・再hashは行っていない。
265700の保存観測は10:19:22 JSTのR状態であり、後の準備完了や今後の全件census・計時・報告の証拠はこのsnapshotに含まない。
最新の進行観測はlocal `output/finite_tail_resume_controller_v1/observation-1792891456999426800.json` に保存した。
全体ETAは未定、goalは未完了である。

## 2026-10-25 10:13 JSTの本番後処理再開

実設定の組立265698はF/0、13通りの実constructor確認265699はF/0・15秒となり、login上の小metadataによるreadinessと起動previewも成功した。
後続だけを実行するv13 controllerを起動し、別SSHでPID1598334・start ticks770092111・commandの一致、生存とerrorなしを確認した。
最初の準備処理はqsub265700でR・run_count=1・walltime10秒・CPU時間9秒を確認し、新しいcensus構成の準備をクラスタで開始した。
元12worker、merge265660、acceptance265661、比較結果とhandoffは保持し、再計算していない。
今回の運用変更は資源割当、census専用のsource/environment、後続の配置と接続であり、元科学関数・seed構成・全域衝突判定を保持する。
全件census、独立計時48行と各192分母、最終report・科学証拠の統合保存はまだ未完了である。
controllerとqsub処理はクラスタ内で継続し、ローカルPCの接続維持を必要としない。
小原本はlocal `output/finite_tail_resume_controller_v1/` と[接続受入記録](tail_census_resume_acceptance_2026-10-25_ja.md)に保存した。
再開後の確認先は[再起動手順](cluster_resident_resume_2026-10-25_ja.md)の最新節とし、旧v12やv13を重ねて起動しない。
全体ETAは未定で、初回準備の1 CPU・96 GiB・4時間は運用上限であり完了予測ではない。

## 2026-10-25の復旧用資源設定・準備処理の受入

専用環境の組立265687はF/0・run_count=1・walltime4秒で、実Pythonでのimport・bootstrap・preimportを確認した。
原本はlocal `output/operational_census_acceptance_v1/build-evidence-v1/` に保存し、元科学入力不変と本番出力root未作成を別SSHでも照合した。
outerの環境選択に関する19項目は265688、後続専用controllerの27項目は265689で成功したが、これらは全件censusや最終接続の完了ではない。
資源policyの28項目はqsub265685、準備bindingの23項目はqsub265686で成功し、両jobのF/0・run_count=1を確認した。
既存の投入先2ノードが他ユーザーのjobで埋まったため、試験専用の新policyを作り、空きのある別ノードへ既存gate経由で投入した。
元policyと未投入stageは保持し、最大2物理ノードの制限は維持している。
接続確認で見つかった全予定件数4,208,002と新規割当244,440の混同を修正し、元baseline3,963,562との関係を受入試験に追加した。
小原本と正確なsource pinsは[運用受入記録](census_operational_pbs_staging_2026-10-25_ja.md)およびlocal `output/operational_census_acceptance_v1/` に保存した。
本番census、独立計時、最終reportはまだ実行完了していない。
新実環境の組立と後続処理の接続受入、本番の投入先移行を進めており、元12worker・merge・比較受理は再利用する。
再開用controllerの起動先が未作成であることは、読取り専用observerで確認した。
全体ETAは未定で、96 GiB・4時間は運用予算であり終了予測ではない。

## 2026-10-25の資源実測完了と限定再開の準備

実測265678はF/0・run_count=1・walltime5分56秒・CPU時間5分55秒で終了し、[測定原本と受入](census_measurement_submission_2026-10-25_ja.md)を保存した。
全予定4,208,002件のうち1,000件pilotを検査し、unexpected collisionは0で、全件censusは未実施である。
元式の候補は16 GiB・45分で、今回の旧判定はメモリ項のみ拒否したが、失敗265675の未保存測定値を復元した結果ではない。
この45分はcensus streamの外挿であり、本番の複数回の入力再検証や親子processの同時メモリを含む総予算の保証ではない。
既存外側と同じ1 CPU・96 GiB・4時間を運用上の余裕枠として使う限定policyを準備し、元候補・実割当・根拠を別々に記録する。
元科学関数・seed・全域衝突判定・stream hashを保持し、新source・専用環境・fresh出力先の受入後に、既存comparisonとhandoffから後続だけを再開する。
tail専用controllerの独立25 fixtureは265679でF/0となったが、最終policyと環境を結合した本番native検証・再起動は未実施である。
本番後処理は停止中で、元12worker・merge・比較結果・旧失敗rootは保持している。

## 2026-10-25 09:37 JSTの資源計測開始

測定専用helperの21 fixtureはqsub265677でF/0となり、別stageの実測265678を既存shared gate経由で投入した。
別SSHで265678のR・run_count=1・walltime10秒を確認し、要求資源は1 CPU・96 GiB・4時間である。
この枠は計測用の上限であり、完了時間の予測ではない。
未受理の既存census-configとbundleを固定pinで再検証し、同じ1,000件pilotの測定値・段階別時間・RSSを資源判定より先に保存する。
元2時間・4 GiBの判定結果と候補資源を分け、計測成功だけで本番censusの投入を承認しない。
元12worker・merge・selection・比較結果は変更せず、旧v12 controllerと本番後処理は停止したまま、測定とtail専用再開処理の準備を進めている。

## 2026-10-25 09:29 JSTのcensus準備失敗と停止

有限tail265675はF/1・run_count=1・walltime13分32秒・CPU時間13分24秒・PBS記録mem15,084,044KBで終了し、v12 controllerのPID1432966も不在と確認した。
内側censusは1,000件のpilotをcollision=0で終えた後、`measured census exceeds two-hour / four-GiB ceiling` により資源計画を拒否した。
計測値の保存前に停止したため、時間・メモリのどちらが個別に超過したかと実際の予測値は未確定である。
先行する大きなbundle検証を含むprocessのpeak selfRSSがメモリ判定へ入った可能性を調査中であり、PBS記録memと同じ測定値とは断定しない。
censusの `planning-failure.json` は `root_reusable:false` で、catalog・manifest・prepare受理記録は生成されていない。
科学bundle1,757,600,835 bytesとconfigは保持され、元12worker・merge265660・acceptance265661・comparison・handoffの受理を取り消したり元計算を再実行したりしていない。
小証跡はlocal `output/low_parallel_flow_v11/census-failure-readonly.json` に保存した。
09:29:23 JSTの独立観測 `output/census_tail_incident_v1/inspection.json` でPID不在と元comparison・handoffのhash不変を確認し、flow errorは09:28:01 JST終了・`automatic_retry:false` だった。
資源計測を保存できる新計画を準備中で、自動再試行はせず、独立計時・最終report・goalは未完了、全体ETAは未定である。
以下のv12復旧差分保存の完了と09:15の稼働観測は保持し、controllerが現在も稼働しているとは扱わない。

## 2026-10-25のv12復旧差分保存の完了

qsub265676はF/0・run_count=1・walltime1秒で、10 fixtureと[復旧差分のprivate保存](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)を完了した。
source参照94件・metadata109件を保存し、追加した元acceptanceのPBS開始記録1件も別SSHで原本hash・job265661との結合を照合した。
大きなresult・selection・raw・過去archiveは読み直しておらず、今後の独立計時・最終科学proofの保存はこの完了に含めない。
本番controller・科学結果・旧保存物は変更していない。

## 2026-10-25 09:15 JSTのv12再開と比較受理・handoff

跨hostのdevice対応を固定authorityで限定して照合するobserverとtailを受入後、v12 controllerを起動した。
別SSHの09:14:10 JST観測でPID1432966・start ticks769736422・全command一致、生存、errors空、元12terminalの採用を確認した。
元merge265660・acceptance265661・12workerは再実行せず、元completion・content hash・sourceと旧v11のstat失敗記録を保持して採用する。
native265673はF/0・walltime18秒、tail265674はF/0・walltime7秒で、実constructorとlogin側のnamespace roundtripを[独立レビュー](cross_host_artifact_stat_review_2026-10-25_ja.md)した。
これらの受入は元計算の再実行や後段科学処理の完了ではない。
新journalは `pipeline-state/parallel-flow-v12`、実configは `20261025-low-parallel-controller-v12/flow-config.json` であり、comparison本文の `all_twelve_processed=true` と元merge265660・acceptance265661への結合を確認した。
継承したv9名のhandoff本文も `partition_started=true`・`flow_completed=true`・`cluster_controller=true` で、新v12設定への対応を確認した。
独立した09:15:07 JST観測では初回の有限tail265675がR・walltime48秒・CPU時間46秒で、census準備を開始している。
comparisonの `independent_timing_performed=false`・`nominal_coverage_certified=false` を保持する。
selection24行の内容は元acceptanceの検証に依拠し、今回その巨大payloadを読み直しておらず、後段reportとの対応照合・独立計時・最終reportの完了は残る。
ローカル接続は不要で、確認先は[再起動手順](cluster_resident_resume_2026-10-25_ja.md)に固定する。
独立計時・最終報告・goalは未完了、全体ETAは未定で、以下の旧停止記録は履歴として保持する。

## 2026-10-25 08:49 JSTの終端確認とcontroller停止

fresh qstatで本番merge265660はF/0・run_count=1・walltime1時間58分44秒・CPU時間3時間19分30秒、後続acceptance265661もF/0・run_count=1・walltime2分37秒・CPU時間2分31秒を確認した。
acceptanceのcompletionには `original_accept_terminal_executed=true` があり、元の終端受理処理とproduction selection生成はPBS内で実行済みと記録されている。
一方、v11 controllerは `acceptance.observe` の `check_artifact_stat` で `Previously PBS-verified artifact stat changed` を検出し、errorを記録して停止した。
PID1145733は不在で、errorの `finished_unix=1792885604.099464`・`automatic_retry=false` を確認した。
PBS内の処理成功とcontrollerの統合受理を区別し、comparison受理・handoff・独立計時・最終報告は未完了である。
元12workerとmerge・acceptanceの成功原本、停止journalを保持し、独立した小metadata確認で4artifactとも差はdeviceだけと判明した。
PBS側のdevice46とcontroller側の2049に対し、inode・size・mtime_ns・ctime_ns・modeは全て一致し、canonicalな通常fileでsymlinkではなかった。
共有filesystemを異なるhostから見る際のhost-localな `st_dev` 比較が停止原因であり、この確認でartifact内容を再読込み・再hashしたわけではない。
小証跡はlocal `output/acceptance_stat_incident_v1/inspection.json` にあり、元completionのSHA-256は `c44b7cddc0b1bbefeab3a629ff932054a5d9c045301415cf41f38ccd7bce5946` である。
元wrapper・proof・hash・sourceを保持したobserver移行を準備するが、修正版の受入・本番再開は未完了である。
重い集約や元workerを再投入せず、旧controllerもそのまま再起動しない。

[v11運用差分の保存](finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md)265662はF/0・run_count=1・walltime2秒で、8fixtureと実snapshot採取を完了した。
source参照474件・metadata109件はprivate保存済みだが、mergeの科学result・後続科学証拠・可変journalは対象外であり、全科学検証や最終proofの保存完了とは扱わない。
goalは未完了、全体ETAは未定で、以下の稼働・保存準備の記録は当時の履歴として保持する。

## 2026-10-25 07:13 JSTの稼働確認と保存準備

集約265660はR・run_count=1で、最新qstatのwalltimeは28分20秒、CPU時間は51分49秒だった。
v11 controllerのPID1145733・起動識別情報の一致、生存、errorなし、全12workerの終端記録保持を再確認した。
集約の終了・深い受理・正式selection・独立計時・最終報告は未完了であり、CPU時間の増加を科学的受理の証拠とは扱わない。
v11制御差分の保存は[準備記録](finite_flow_v11_delta_snapshot_preparation_2026-10-25_ja.md)のstageまで用意し、相対source基準の修正を独立レビューした。
保存用8fixture・実採取・qsubは未実施で、集約終端後も後続jobを含む既存資源gateで確認してから投入する。
本番controllerや集約を再起動せず、公開済み版と科学設定を維持する。

## 2026-10-25 06:45 JSTのv11本番集約再開

後続設定の18件の受入と実設定生成は265655・265656でF/0、controllerの31件と実設定確認は265657・265658でF/0となった。
265659では12件のprobe受入と新merge先を使う実13constructorが成功し、元科学設定と元12workerの記録を維持した。
v11 controllerを起動し、別SSHでPID1145733・start ticks768839164・command一致、生存とerrorなし、全12terminalの採用を確認した。
新しい集約265660はqsubで投入され、R・run_count=1・8CPU・32GiBを確認した。
06:45のqstatではwalltime26秒・CPU時間47秒で、前回の6秒停止点を越えて実行中である。
新mergeは`20261025-low-parallel-front-v6/merge-parallel-v2`、requestは同階層の`merge-parallel-request-v3`を使い、失敗した265651のrootと記録は保持する。
preparedのSHA-256は`ccb3fc9dc85fe3c7e9f20a20e15b531615519abf64e7ee9c45ca9414ddb9c03c`、requestは`37e850bb62162f1180336fea056edf8216c4c1605f453d3891a80353f0642c50`である。
configは`20261025-low-parallel-controller-v11/flow-config.json`、SHA-256は`63b8b4d149fdbb56c043fb053e75bfabc73b0b38ea16b88b7dbbd820734d0f4b`である。
制御sourceは`output/low_parallel_flow_v10/flow.py`、journalは`pipeline-state/parallel-flow-v11`で、sourceとjournalの世代番号を区別する。
科学的な集約結果の受理・独立計時・最終報告はまだ未完了で、全体ETAは未定である。

## 2026-10-25 06:38 JSTの後段alias修正受入

元worker verifierの記録を保持した限定変換に対し、qsub265652で39件の受入が成功した。
実入力probeの265653は文字コード名の誤記でF/1となり、未受理の記録として保持した。
誤記だけを修正した265654はF/0・run_count=1・walltime18秒で、旧checkerの失敗再現、実combine入口から最初の値読込直前、全12件それぞれの受理処理から値読込直前までを確認した。
accepted原本SHA-256は`08faf448bfdcede1ab46663060928b87aabec159c67dc8545cd4461eb8b78e78`である。
values・rawの読込みや科学的受理結果の返却は行っておらず、全12条件の科学的受理の完了とは扱わない。
実71sourceの照合箇所棚卸しと[独立レビュー](parallel_worker_alias_review_2026-10-25_ja.md)を完了し、新merge rootへの後続設定とcontrollerの受入を準備している。
本番集約はまだ停止中で、全体ETAは未定である。

## 2026-10-25 06:30 JSTの集約実行停止

起動直後にRを確認した集約265651は、その後F/1・run_count=1・walltime6秒で終了した。
v10 controllerもエラーを記録して終了し、PID1082214の不在を確認した。
集約準備の親source照合は通過したが、後段の元worker verifierから導出した`accept_worker`内で`selector closure differs from environment`を検出した。
実行記録は`20261025-low-parallel-front-v6/merge-parallel-v1/`の`execution-error.json`・`merge.err`に保持し、同じ出力先への再投入は行わない。
元workerの12件はF/0のまま保持し、別名パス照合が後段に残っていないか、実際の受理経路を調査している。
実manifest・環境の小metadata照合では全12件に同じ1件の表現差があり、承認targetと実SHAは一致していた。
失敗箇所は最初のworker値を読む前であり、前回のnative準備確認はこの後段の`accept_worker`を実行対象に含んでいなかった。
元verifierの記録を改変せず、実受理経路に限定した明示変換と、全12件で値の読込直前まで通す検証を追加する。
失敗した集約rootを保持するため、次回は新merge rootへ後続処理の参照を接続し直す。
全12条件の深い受理・正式比較・独立計時・最終報告は未完了である。

## 2026-10-25 06:29 JSTの本番集約再開

controller引継ぎのqsub265649は18件成功し、実設定のqsub265650もF/0・walltime21秒で、12既存terminalの採用と隔離した集約準備を確認した。
修正版v10 controllerを起動し、別SSHでPID1082214・start ticks768745045・command一致、生存とerrorなしを確認した。
全12件を再投入せずに引き継ぎ、本番集約をqsub265651で投入し、R・run_count=1・8CPU・32GiBを確認した。
本番preparedのSHA-256は`2bc6fc0f3a19c971e0f31171ff96787bddd08741bb86428ecd9d81d524a3a645`、新requestは`23bf1b86b0ef323546265ae07997f82b5c3a14ef5e19d68b80268c4245801175`である。
新configは`20261025-low-parallel-controller-v10/flow-config.json`、SHA-256は`1263c2ed2264a19c69b0a29c692cf9277fb402d1d94f578364b73b94ab1046da`である。
旧v9の失敗記録を保持し、新journalは`pipeline-state/parallel-flow-v10`を使う。
未作成だったmerge・acceptance・tail出力先は元の固定設定を継承し、将来のhandoffには新flow configとmigrationのpinを記録する。
集約の科学的受理、独立計時、最終報告はまだ未完了であり、全体ETAは未定である。

## 2026-10-25 06:16 JSTの集約準備停止と06:22 JSTの修正受入

最後のindex11の265592（tile288 depolarizing、p=0.001）がF/0・run_count=1で終了し、walltime4時間38分27秒・CPU時間3時間56分4秒だった。
全12件のterminalはv9 journalへ回収済みだが、集約準備の`validated_policy`が`Parent scientific selector closure differs`を検出し、controllerは終了した。
PID898820の不在、merge-prepared・merge-submittedの未作成を確認し、原因調査と独立レビューを開始した。
エラー原本は`$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v9/error.json`に保持し、SHA-256は`a81a6784bec2f1a0d38cd6baf77d77e582db5cc3d5da7bd1a346547ab26d7bf6`である。
完了したworkerを再投入せず、元の科学コードと実行環境の整合性を保った復旧を行う。
独立した原本照合では、manifestの53 source中1件だけが実体パスをキーに持ち、parent環境の宣言キーは別名パスだった。
parentの明示`resolved_sources`、実際のsymlink解決先、両側SHA-256は一致しており、異なる科学コードを使ったことを示す不一致ではない。
修正版ではこの明示対応を検証し、同じhashだけを持つ無関係なパスによる代用は拒否する。
修正版の小規模受入はqsub265647で25件成功し、F/0・walltime20秒だった。
qsub265648では実12terminal metadataから元の失敗箇所を含むrequest検証、builder・control.prepare・preflight、実CLIとnative環境の確認まで成功し、F/0・walltime10秒だった。
そのaccepted原本SHA-256は`42f7da2047b5d2e23b6564c05f43e414056b454e877fcea5b44f37bc67212c33`であり、科学payload・worker値の読込みと本番merge実行は含まない。
controllerの引継ぎ設定の受入と本番再起動はまだ未実施である。
集約・深い結果受理・独立計時・最終報告は未完了で、全体ETAは未定である。

## 2026-10-25 05:38 JSTの確認

index10の265591（tile288 depolarizing、p=0.003）がF/0・run_count=1で終了し、walltime4時間2分19秒・CPU時間3時間23分50秒だった。
v9 controllerの生存・起動識別情報一致・errorなしとterminal11件の採用を確認した。
残るindex11の265592（同p=0.001）はR・run_count=1で、walltime4時間2分26秒・CPU時間3時間25分34秒だった。
全12条件の深い受理・集約・独立計時・最終報告は未完了であり、全体ETAは未定である。

## 2026-10-25 04:38 JSTの確認

index9の265590（tile288 depolarizing、p=0.01）がF/0・run_count=1で終了し、walltime3時間1分8秒・CPU時間2時間30分38秒だった。
v9 controllerは生存・起動識別情報一致・errorなしで、indices 0〜9のterminal10件を採用した。
残る265591・265592はR・run_count=1であり、全12条件の深い受理・集約・独立計時・最終報告は未完了である。
切替後のcontrol資料は[private snapshot](finite_flow_v9_snapshot_acceptance_2026-10-25_ja.md)へ保存し、[raw取得索引](raw_access_followup_2026-10-25_ja.md)も整理した。
これらの保存と10件の正常終端を、未完了の科学工程の代わりにはしない。

## 2026-10-25 04:18:38 JSTのv9切替確認

04:18:17 JSTに旧v8 controllerの起動識別情報・command一致、sleep待機、子processなし、残り3worker実行中、merge未作成を確認してSIGTERMで停止し、不在を確認した。
最初の停止試行はpidfd APIがないため無変更で終了した記録を保持し、workerや旧journalを変更していない。
実native constructorの265644がF/0となった新設定を起動し、04:18:38 JSTの別SSH接続でv9 controllerの生存・起動識別情報一致、旧controller不在、errors空を確認した。
新journalはindices 0〜8のterminal9件を採用し、残るindices 9・10・11は実行中、最終completedは未作成である。
新flowはmerge終端の深い受理とtailの重い管理処理を有限PBS actionへ渡す構成だが、切替時点で後段の実科学payloadは未実行である。
ローカルPCの接続は不要であり、再起動後は[現行v9の読取り確認手順](cluster_resident_resume_2026-10-25_ja.md)を使い、旧v8や起動コマンドを再実行しない。
全12条件の正式比較・独立計時・最終報告は未完了、全体ETAは未定である。
以下の切替前記録は履歴として保持する。

## 2026-10-25 04:11:16 JSTの確認

新しいqstatでindex 5の265589がF/0となり、walltime2時間24分54秒・CPU時間2時間13分44秒だった。
全12workerは9件F/0・3件Rで、残るindices 9・10・11の265590・265591・265592は各walltime約2時間35分・CPU時間約2時間9分である。
PBS正常終了は深い科学的受理とは区別し、全12条件の正式比較・独立計時・最終報告は未完了で、全体ETAは未定である。
現行v8から新版controllerへの本番切替はまだ行っていない。

[動的な物理ノード配置](dynamic_physical_aux_acceptance_2026-10-25_ja.md)は265637の31fixtureと265639の実補助CLIで成功したが、実CLIはknown childなし・科学payloadなしの枝であり、稼働中のunbound science childとの共存はfixture検証の範囲である。
[report環境の受入](finite_tail_effective_acceptance_2026-10-25_ja.md)は265635の26fixture、265636の実report bootstrap/source closure、265638の新設定validator照合が成功したが、本番merge再検証・科学payload・tail起動は実施していない。
[265641の結合受入](finite_tail_outer_review_2026-10-25_ja.md)はouter68・binding21・native constructor純試験6の計95fixtureがF/0で成功し、実全role constructorや本番pipelineの受入とは区別する。
新たな[明示ladder CLI](tile_example_target_cli_acceptance_2026-10-25_ja.md)はqsub265640で契約23件・既存default1件とtile72 bit/depolarizing実CLIを通過し、任意目標の接続を補ったが、低ノイズ精度校正・正式selectionの代わりにはしない。
以下の観測は各時点の履歴として保持する。

## 2026-10-25 03:51:42 JSTの確認

index 4の265588もF/0となり、walltime2時間13分49秒・CPU時間1時間55分24秒だった。
全12件中8件が正常終了し、残るindices 5・9・10・11の4件はRで、CPU時間が増加している。
現行v8 controllerの生存・起動識別情報・command一致、errorなし、terminal8件、最終completed未作成を確認した。
新flow・acceptance wrapperは受入を進めたが、全tailの有限PBS化と配置対応の統合が残っており、本番切替は未実施である。
全12条件の科学的受理・独立計時・最終報告はまだ完了していない。
保存済みv8の共有候補は生成後の[独立レビュー](share_snapshot_v8_candidate_review_2026-10-25_ja.md)まで完了したが、未公開で、新controller差分や未完成の最終成果物を含むとは扱わない。

## 2026-10-25 03:38:20 JSTの確認と追加受入

実workerは7件F/0・5件Rのままで、残る5件のCPU時間増加、現行controllerの起動識別情報一致・生存・errorなしを確認した。
現行journalはparallel-flow-v8であり、新版への本番切替はまだ行っていない。
merge終端受理のPBS隔離wrapperは265621で27fixture、265623で実CLIと現native環境の前倒し確認に成功した。
実merge preparedを使う確認はまだ未実施であり、それを本番の受理ジョブ冒頭で自動実行する次版を準備している。
新flow source v8は265626で84fixtureに成功し、最終stdoutを含む大JSONの読込み上限を強制した。
これは新journal v9の起動ではなく、全tail有限PBS actionと次版wrapperの統合・実環境受入後に切り替える予定である。
保存済みv8資料の共有候補は265624で正常生成・hash検証が完了し、約9.1MBのarchiveと小さいbuilder source sidecarを保存した。
実際の公開・独立した識別子レビューの完了・新しいcontrol差分の保存は、その生成成功と別に判定する。

## 2026-10-25の後段管理処理の追加監査

生成済み7workerのvalues.jsonはstatによる確認で合計1,196,553,264 bytesあり、本番merge-resultはまだ未作成だった。
source監査で、merge終端のaccept_terminalとtail各roleの管理経路が巨大JSONの読込み・複製・hash・書出しを非PBS側でも行うことを確認した。
計算自体がPBSで実行されても、この管理経路は軽い状態確認だけでは済まない。
元の科学検証を保持して重い有限処理をqsub内へ移し、軽い待受・状態確認・資源確認と分離する新版を準備している。
この監査時点では稼働中v8と実workerを変更せず、切替は実環境の受入後に行う。

## 2026-10-25 03:11:42 JSTの確認

index 3の265587もF/0となり、全12条件中7件が正常終了、残りindices 4・5・9・10・11の5件がRである。
v8 controllerは起動識別情報とcommandが一致して生存し、errorなし・terminal7件・最終completedなしを確認した。
残る5件ではCPU時間の増加も確認した。
現行構成の[private保存結果](reproduction_snapshot_v8_acceptance_2026-10-25_ja.md)と[取得可能性の監査](reproduction_access_inventory_2026-10-25_ja.md)を保存した。
全12条件の比較・独立計時・最終報告は未完了であり、次の依存工程は実worker全件の正常終端後に進む。

## 2026-10-25 03:06:44 JSTの確認

置換したindex 0の265605がF/0となり、walltime42分46秒・CPU時間31分46秒で正常終了した。
全12件中indices 0・1・2・6・7・8の6件が正常終了し、残るindices 3・4・5・9・10・11の6件はRである。
v8 controllerの生存・起動識別情報・command一致、terminal 6件の回収、errorなしを確認した。
本番merge・独立計時・最終報告の完了はまだ確認していない。
最終報告草案から過去の稼働履歴を整理し、履歴は本書と復旧記録に保持した。
現行v8のprivate snapshot採取265616は保存用metadataの原本hash照合で停止したが、科学ジョブを変更せず、正しいクラスタ原本hashとその生成証拠へ束縛した265617が正常終了した。
265617は03時08分台にF/0・run_count 1・walltime6秒となり、source1252参照・metadata112件・envelope1223件・one-hop edge31512件をprivate保存した。
このscopeは歴史的baselineと現行設定からの参照を含み、全sourceが実行されたことや、raw/native・最終成果物の完全保存を意味しない。
公開用資料の識別子除去と利用者向け取得監査を別タスクとして進め、原本保存・公開可能性・科学的再現を別々に判定する。

## 2026-10-25 02:50:38 JSTの常駐再開確認

別のSSH接続でv8 controllerの起動識別情報・全commandが一致して生存することを独立に確認し、error記録なし・stderr 0バイトだった。
indices 1・2・6・7・8の5件はF/0でterminal回収済み、indices 0・3・4・5・9・10・11の7件はRだった。
新index 0は265605で、他11件の元の実行証跡は保持している。
parallel mergeの統合受入と実CLI・8CPU guard、tailの受入とnative確認、flowの受入とactual shadowは成功した。
後段controllerはクラスタ常駐を再開し、このPCの接続を維持する必要はない。
ただし全12条件を対象とする深い結果受理・本番merge・独立計時・最終報告はまだ開始しておらず、5件のF/0や受入試験をその完了証拠とは扱わない。
比較・全体ETAは未定で、以前の完了予測の撤回を維持する。
以下の未再開・未投入などの記録は、それぞれの時点の履歴として保持する。

## 2026-10-25 02:22 JSTの最新確認

新index 0を265605としてqsub投入し、新しい照会でR・経過walltime2分31秒・CPU時間2分20秒を確認した。
親のexecution、子readerのintentとhandleが存在し、execution-errorはないが、完走・結果受理はまだ確認していない。
旧265564のF/-29を失敗記録として保持し、他の8件はR、3件はF/0である。
新native準備265602とpolicy265603は全12件を固有のruntimeに対応付けて正常終了し、shadow265604も正常終了した。
shadow成功は実controller起動ではなく、後段のクラスタ常駐処理はまだ再開していない。

直列merge用controllerは再起動せず、hash並列化mergeの統合受入後に新しいv7 controllerを起動する準備を進めている。
hash core265606は同じ元snapshot・phase確認を用いる18fixture×2の検証でF/0だったが、完全なmerge統合と性能は未検証である。
比較・全体ETAは引き続き未定とする。
private snapshot265599はv5のsource1031参照・metadata75件・参照edge19692件の保存であり、v6差分や最終証拠はまだ含まない。
以下の未投入・旧controller停止などの記録は当時の履歴として保持する。

## 2026-10-25 02:01:52 JSTのwalltime超過と復旧準備

index 0の265564は要求walltime65分を超過し、02:01:52 JSTにF/終了コード-29となった。
実walltimeは66分28秒、CPU時間は32分12秒だった。
旧flow v5はerrorで終了し、controllerのプロセスが存在しないことを確認した。
他の11件は保持し、indices 6・7・8の3件はF/0、8件はRである。
index 0だけを4時間のwalltime上限と新しい出力先で再実行するfront v6を準備中で、この確認時点では未投入である。
4時間はジョブの資源上限であり、完了予測ではない。
[投入契約](single_worker_wall_recovery_dispatch_spec_2026-10-25_ja.md)の265598は13テスト、[復旧flow](low_parallel_wall_recovery_flow_spec_2026-10-25_ja.md)の265600は54テストが成功し、ともにF/0だった。
新しいnative準備と[walltime復旧後のmerge](low_parallel_wall_merge_v5_spec_2026-10-25_ja.md)の受入は、この確認時点では未完了である。

比較の07〜10時JSTという以前の目安も撤回し、比較・全体とも完了時刻は未定とする。
mergeは現状1CPUの直列処理で入力hashを繰り返し確認し、確認済み3条件の約73.8万ファイル・約42.7GBだけでも少なくとも約187GBの読込みを見込む。
これはコードとメタデータによる下限見積りで、残る9条件の規模・実転送速度・総所要時間は未計測である。
mergeの24時間要求も完了保証ではなく、全検査を維持した8threadのhash照合案は実装中で、受入・本番実行は未実施である。

[限定的な形状検査](completed_worker_shape_probe_2026-10-25_ja.md)265595は既存3条件の各2行・352候補・192分母の検査を通ったが、全入力hash・完全な算術・全12条件受理は検証していない。
[再現資料snapshot](reproduction_snapshot_v2_spec_2026-10-25_ja.md)265599はF/0で、flow v5のsource1031参照とmetadata75件のprivate保存を完了した。
この保存は公開archive・科学的再現・最終結果の証明ではなく、新しいfront v6の保存済み資料とも扱わない。
以下の01:39以前の稼働観測は履歴として保持し、旧controllerが現在も生存しているとは解釈しない。

## 2026-10-25 01:39 JSTの最新確認

新しいqstat照会でindex 8の265573もF/0となり、PBS walltime38分44秒・CPU時間31分23秒だった。
現在はindices 6・7・8の3件がF/0、残る9件がRである。
flow controllerはプロセスの起動識別情報が一致して生存し、error記録はなく、stderrは0バイト、finished journalは3件だった。
この3件はPBS正常終了とterminal回収の確認であり、深いworker結果の受理・merge・独立計時・最終報告は未完了である。
再開時の照会先と手順は[クラスタ常駐処理の再開記録](cluster_resident_resume_2026-10-25_ja.md)、実装・利用例の確認範囲は[符号・decoder・利用例の監査](code_decoder_examples_audit_2026-10-25_ja.md)にある。
以下の01:36 JSTまでの観測は当時の履歴として保持する。

## 2026-10-25：置換7条件の投入完了後の観測

置換対象7条件を全てqsubで投入した。
index 2は265586、3は265587、4は265588、5は265589、9は265590、10は265591、11は265592である。
保持しているindex 6の265571は終了コード0・walltime36分5秒、index 7の265572は終了コード0・walltime36分11秒を確認した。
この2件のPBS正常終了はflowによる科学的結果の受理前であり、条件別結果の受入完了とは区別する。
残る10件はR、全12件はrun_count=1で、配置は2物理ノード以内だった。
その後、混合flowの実controllerをクラスタで起動し、SSH終了後の別接続で生存・起動識別情報の一致、全12件の初回journal、errorとstderrが空であることを確認した。
indices 6・7は元のpreparedを保持してterminalを回収し、他10件はpendingであり、深い科学的結果の受理は後続mergeで未実施である。
controllerはクラスタに常駐し、このPCの接続を維持する必要はない。
全12条件の結果受理・merge・独立計時・最終報告は未完了であり、比較の条件付き07〜10時JSTという目安と全体ETA未定の扱いは維持する。
以下の先行1件投入時の節は、その時点の履歴として保持する。

## 2026-10-25 01:31 JSTの観測と7条件の再投入

01:31 JSTの新しいqstat照会で、既存5ジョブ265564・265566・265571・265572・265573はRだった。
この5件はindices 0・1・6・7・8に対応し、実行中のprepared・manifest・入力・実job IDを変更せず保持する。
v4の残り7条件はPBS出力の外側のtimestampが観測ごとに変わるため終了コード1となり、旧失敗記録を保持して新しい実行先へ置き換える。
修正は比較から最上位timestampだけを除外するもので、元のPBS全出力の保存・返却とそれ以外の項目の照合、科学計算・入力・分母は維持する。

修正受入265581・265582は各17テストと対象7条件の実CLI・live qstatの検証に成功した。
混合版の投入処理265578、merge265579、flow265580、native準備265583、配置policy265584はいずれも終了コード0であり、policy確認はPBS walltime32秒だった。
この受入は正常完了した本番比較値を認定するものではなく、保持5件と再実行7件をそれぞれ固有の証跡で扱えることの確認である。
仕様と範囲は[混合版のnative準備](low_parallel_native_preparation_v5_spec_2026-10-25_ja.md)、[合流契約と受入](low_parallel_recovery_merge_v4_spec_2026-10-25_ja.md)、[混合版flow](low_parallel_mixed_flow_spec_2026-10-25_ja.md)にある。
置換対象indices 2・3・4・5・9・10・11のうち、index 2の先行ジョブ265586をqsubで投入した。
265586の成功と残り6条件の投入は、この記録ではまだ確認しておらず、再実行7件や全12条件の完了とは扱わない。
最大2物理ノード×96コア・最終的に各ノード6workerを維持し、ローカルPCで数値計算・テストを行わない。

比較工程の暫定見込みは10月25日07〜10時JSTだが、先行ジョブが成功し、後続6条件が進行することが条件である。
過去の所要時間の最長4.83時間を参考にした見積りであり、失敗・待機・新しい処理時間によって変わる。
独立計時・最終報告を含む全体の完了時刻は未定で、以前の18〜24時という予測は撤回する。
以下は過去時点の観測として保持する。

## 2026-10-25 00:22 JSTの本番起動失敗

新しい入力準備265533は22件の受入と実metadata・全12workerのnative検証を通り、終了コード0・PBS walltime51秒だった。
全12条件の新版merge受入265534も47件成功・終了コード0だった。
その後12workerをqsubで投入したが、265535〜265546は全て約3秒で`actual import origin differs`により終了コード1となった。
割当は2ノードに各6件で資源上限を守ったが、数値結果は全件未生成である。
実runnerのディレクトリにある別コピーが環境で指定したisolated moduleを隠しており、準備用entrypointでの検証ではこの起動時の探索順を検出できていなかった。
[失敗記録と修正方針](parallel_startup_failure_2026-10-25_ja.md)に証拠と検証範囲を保存した。
検証済みコードの配置だけを変更した新runtimeと新frontを準備し、実起動コンテキストの検証・1条件の本番起動確認から再開する。
この時点で本番の比較ジョブは稼働しておらず、全体完了時刻はまだ再見積りできない。

## 2026-10-25 00:14 JSTの12条件並列化の受入

12worker用の投入処理265529は18件、監視・再開処理265531は30件、全12件の資源予約の事前評価265532は4件が成功し、全て終了コード0を確認した。
[制御処理の受入記録](data_tile_validation_2026-10-17/parallel_controls_20261025_v2/receipt.json)に小さなログ・source hash・PBS終端状態を保存した。
後続処理の12worker引継ぎ265528も17件成功し、実際の親環境・報告用環境・census source closureの検証265530は終了コード0・PBS walltime8秒だった。
[後続環境の受入記録](low_parallel_tail_v2_acceptance_2026-10-25_ja.md)に対応する証拠を保存した。
不足していた投入記録・スクリプトのhashは、既に固定されていた最終集約設定のupstream参照に存在するため、元の値との照合に基づいて追加する。
全12条件の本番投入は、このメタデータ修正と新しい入力準備の受入後に行う。
上記は制御・環境の受入であり、全12条件の数値比較や独立計時の完了ではない。

## 2026-10-25 00:06 JSTの再構成

旧比較265521は00:00:47 JSTに終了コード1で終了し、PBS walltimeは38分43秒だった。
エラーは`external submission pin required`であり、有効なworker結果は生成されていない。
staged readerの3条件（indices 6・7・8）で、upstreamジョブの投入記録とスクリプトのhashが入力証拠に不足していることをメタデータ調査で確認した。
元の投入記録・スクリプト・終端snapshotを照合した上で、追加するhashを明示した新しい入力を準備する。
数値データ・推定式・selector本体を変更する修正ではない。
旧265520・265521を完了結果として再利用せず、失敗記録として保持する。

旧8条件＋保持4条件用の実環境準備265527は終了コード0・PBS walltime38秒で終了した。
この成功はnative bootstrap・manifest・資源設定の検証であり、失敗した265521の数値結果を有効化しない。
[回収記録](data_tile_validation_2026-10-17/native_preparation_20261025_v1/receipt.json)に準備の成功と旧workerの失敗を分けて保存した。
検証済みの環境とhelperを再利用し、全12条件をsingleton workerとして2物理ノードに6本ずつ配置する構成へ変更する。
12条件の本番ジョブはこの時点では未投入で、最終完了の見込みは修正の受入と本番の進行を確認後に更新する。
後続の引継ぎを12workerに対応した受入ジョブ265528はqsub投入済みであり、終了結果はまだこの記録では確認していない。

## 23:56 JSTの統合処理の受入

版を分けたworker結果の統合は、単体23件と旧・新PBS証拠の結合および入力構築4件、計27テストがクラスタで成功した。
受入ジョブ265526は23:56:55 JSTに終了コード0で完了し、PBS walltimeは9秒だった。
先行265525はテスト用環境情報ファイルの不足で失敗し、その記録を保持して別の配置先で修正した。
[受入回収記録](data_tile_validation_2026-10-17/versioned_merge_acceptance_20261024_v2/receipt.json)には原本・保存後hashと終端状態を保存した。
この結合テストは合成fixtureによるものであり、本番9workerの完了や全12条件の数値結果の受理を示さない。
並列本番の実環境準備、投入処理の受入、後続のcensus・独立計時・報告への環境引継ぎは作業中である。

## 23:52 JSTの受入確認と本番投入前の状態

PBS情報の投影修正265522は39テスト成功・終了コード0、実native環境のbootstrapと封印済みsnapshotのスモーク265523はc0t0/c0t1の2条件で成功・終了コード0・PBS walltime15秒だった。
物理ノード配置制御とworker bindingの受入265524は26件と16件、計42テストが成功し、終了コード0を確認した。
小さな証拠11ファイルと原本・保存後hash、3ジョブのPBS終端状態を[受入回収記録](data_tile_validation_2026-10-17/parallel_recovery_acceptance_20261024_v1/receipt.json)に保存した。
これらは修正・実環境スモーク・配置制御の受入であり、並列本番pipeline全体の完了検証ではない。

23:51の照会では旧比較265521はRで、経過約28分、CPU時間22分34秒、メモリ約1.5GBだった。
旧比較265520の失敗記録は保持し、実行中265521の入力・環境・manifestは変更していない。
8本の条件別本番ジョブは23:52時点で未投入であり、受入テスト成功を本番の開始・完了として数えない。
本番投入側ではlegacy bindingを実行中265521の1件に限定し、新規処理を別の固定物理ノードへ配置する条件を維持する。
上限は2物理ノード×各96コアであり、同一物理ノード内の複数ジョブを許可する。

直前の継続区間は、実行中ジョブの照会による検証済み待機（verified wait）として記録する。
今回の42件の受入成功と証拠回収は、新たに確認した進捗である。
全体完了の暫定見込みは10月25日18〜24時JSTだが、8本の本番投入・全条件比較・独立計時・最終報告が残り、10月26日へ延びる不確実性がある。
この見込みは確約やPBS要求walltimeから計算した完了時刻ではない。
ローカルPCでの計算ジョブは実行していない。

## 23:28 JST以降の比較復旧と並列化

比較265520は、保存済みPBSの8項目とqstat全出力の形式差を同一視した検査で異常終了した。
比較265521は実行を継続しており、旧controllerは比較の失敗を受けて停止している。
保存対象の8項目には値の差が見つからず、余分なPBS項目が原因だったが、修正版の本番検証は未完了である。
稼働中の旧workerの入力・環境・manifestを変更せず、版を分けたreader修正・合流・配置制御を並列に実装している。
所有者の上限は2物理ノード×96コアであり、2ジョブという意味ではないことを確認した。
新規処理を特定ノードへ配置する制御を検証し、条件ごとの並列処理へ移行する。
サブエージェント起動は今回成功しており、過去の利用上限記録を現在の制限と断定しない。
[日本語最終報告の草稿](final_validation_report_draft_2026-10-24_ja.md)を別作業で準備したが、最終受入済み報告ではない。

## 23:22 JSTの復旧確認

最後の条件の最終集約265507は正常終了したが、後続265513が再現用ログの不足で停止していた。
不足ログを固定hashで補い、qsubによる復旧265519は正常終了し、全67,584行の算術照合と再現資料の保存を完了した。
全12条件の比較用候補が揃い、固定環境で比較用の2workerとflowの準備・起動を確認した。
比較の本番ジョブ265520・265521が各1ノードで実行中であり、比較結果・独立計時・最終報告の完了は未確認である。
詳細と受入38テスト、保存証拠、再開時の確認方法は[復旧結果](cluster_postprocess_recovery_result_2026-10-24_ja.md)にある。
ローカルPCでの計算ジョブは実行していない。

## 12:01 JSTの継続確認

GitHub experimental版の公開結果は[公開記録](publication_result_2026-10-24_ja.md)に保存済みである。
低ノイズの最後の条件C3T2の最終集約265507はPBS状態Rで、実行記録のjob IDと固定config hashも一致している。
クラスタcontrollerは生存しており、controllerのエラー記録と最終集約のfailure記録はなく、completion記録とfinal-reportはまだない。
観測証跡は`output/cluster_postprocess_pipeline_v1/controller-observation-1792810865160278600.json`に保存した。
全12条件比較・独立計時・日本語最終報告は未完了であり、最終集約の結果待ちを継続する。
確認用scriptは実行・完了・失敗記録とreaderログ末尾も表示するように更新し、稼働中の計算sourceや設定は変更していない。
Zenodoの公開記録とDOIは未確認で、GitHub側webhook一覧0件の観測後、所有者へZenodo設定画面の対象Releaseの状態を問い合わせている。
この回答待ちはクラスタ計算の継続を妨げず、このPCの起動維持や旧待受の再起動も必要ない。

## 11:15 JSTのクラスタ自律継続確認

クラスタcontrollerは親PID1の独立プロセスとして生存し、最終集約265507は実行中で、controllerのエラー記録はなかった。
全条件比較・独立計時・日本語報告までの後続はクラスタ側へ接続済みであり、Windows上のmcmc4qec Pythonプロセスは今回の再確認でも0本だった。
この計算を継続するためにローカルPCを起動し続ける必要はないが、後続の本番完走はまだ未確認である。

並行する保存済み診断集計265508は終了コード0・run count 1で完了し、PBS実測は2分42秒・最大メモリ59,648 KiBだった。
全38バッチ・768群・352設定各192反復・67,584行と2,893,824件の保存診断を照合し、分母除外は0だった。
全67,584行にundefined・high R-hat・low ESSのflagがあり、区間未取得は0だった。
logical bit診断の未定義は全768群で見られた一方、syndrome weight診断の未定義は0件であり、全行のflagを全観測量が未定義という意味には解釈しない。
保存flagを再構成する記述的な集計であり、未定義の原因、混合不良の機構、精度・被覆の保証を確定するものではない。
小さな結果4ファイルをhash照合して回収し、投入証跡と再現用sourceを[data_tile_validation_2026-10-17/c3t2_saved_diagnostic_census_v1/](data_tile_validation_2026-10-17/c3t2_saved_diagnostic_census_v1/)に保存した。
群別詳細はクラスタに保存し、そのhashとサイズを回収receiptに記録した。
観測量別の件数、設定ごとの192反復分母、判定閾値と解釈上の制限を[保存済み診断の結果](c3t2_saved_diagnostic_result_2026-10-24_ja.md)にまとめた。

## 11:11 JSTの保存済み診断内訳の並行集計開始

索引で全行にundefinedがあったため、どの観測量族・欠落項目に由来するかを保存済みJSONから記述的に集計する独立処理を追加した。
小仕様と4件の合成受入をWindows・クラスタで検証し、qsubジョブ`265508.node-PRISM`として1ノード1CPU4GB1時間で投入した。
投入時の所有者の他ジョブは最終集約265507の1ノードであり、共有lockと最大2ノード制限を確認した。
全768群・352設定各192反復・67,584行を保持し、全予定診断keyと保存flagの再構成を要求する。
新しいsampling・decode・BAR・IAT等を実行せず、結果を見た後の記述的集計を事前校正や収束保証と混同しない。
仕様は[保存済み診断内訳](c3t2_diagnostic_census_spec_2026-10-24_ja.md)、source・投入証跡・観測scriptは`output/cluster_diagnostic_census_v1/`に保存した。

## 11:03 JSTのC3T2最終集約投入・開始確認

C3T2の最終集約を元のwrapperからqsub投入し、ジョブ`265507.node-PRISM`が11:02:46 JSTに実行開始したことを確認した。
PBSのowner・run count 1・投入script・1ノード1CPU32GB12時間の要求と、元の投入ledger・driverの投入記録を照合した。
この観測時点の所有者の稼働ジョブはこの1ノードのみで、最大2ノードの制約内である。
prepared configと実scriptのhashも一致し、入力設定を変えずに最終集約を開始した。
固定された投入証跡8件・200,782 byteを`data_tile_validation_2026-10-17/c3t2_final_cluster_submission_v1/`へ回収した。
集約結果は未取得であり、終了後の回収・算術照合・比較用candidate準備・全12条件比較・独立計時・日本語報告はクラスタcontrollerが順に実行する。
ジョブ開始を科学的合格や全goal完了とは扱わない。

## 10:55 JSTのC3T2最終集約準備完了

元のnative preparerがsource135件・metadata383件を検証して正常終了し、C3T2の最終集約設定を確定した。
config SHA256は`7d3e4fc4b0143e70c8c79f0dfa93099e62c53981c73e44accec356b1373404b7`であり、保存済み完了記録と実ファイルのhashを照合した。
PBSスクリプトの要求は1ノード・1CPU・32GB・12時間で、元のnative Pythonとplanned wrapperを使用する。
script SHA256は`e63b1de60f78c229428dbe3b92540357a2a17442ac22457368a5d74b5ee22f52`である。
この時点の受入は`prepared_not_submitted`であり、科学的結果の合格や数値集約の完了ではない。
クラスタcontrollerは最終execution段階へ自動で進み、実行driverの投入前照合が継続している。
確認記録は`output/cluster_postprocess_pipeline_v1/prepared-result-verification.json`に保存した。

## 10:47 JSTの入力配置完了・最終集約準備開始

qsubジョブ265506は終了コード0・run count 1で終了し、PBS実測は3分55秒・最大メモリ105,192 KiBだった。
転送receiptと配置先contextのhashを照合し、元の予定先への全入力配置を確認した。
context SHA256は`f65967f7df350ad3b790e37ecf4d30dc34b34c79829e006abb11df445545f2e9`である。
クラスタ常駐controllerは配置完了を記録し、元のnative preparerを用いたC3T2最終集約準備へ自動で進んだ。
この時点では最終集約ジョブの投入は未完了であり、既存preparerの実プロセス生存を確認して待機している。
観測とhash照合は`output/cluster_postprocess_pipeline_v1/distribution-result-verification.json`と同階層のprocess観測に保存した。

## 10:43 JSTの索引完了・後続自動開始

qsubジョブ265505は10:42:56 JSTに終了コード0・run count 1で終了し、PBS実測は25分10秒・最大メモリ3,687,584 KiBだった。
全38バッチ・768群・67,584行の索引を集約し、未回収行・pending群・infrastructure失敗・context失敗はいずれも0だった。
完了snapshotとregistryのhash、38バッチの終端とsnapshot hashを照合し、42件・862,409 byteの小さな証跡を`data_tile_validation_2026-10-17/c3t2_index_cluster_terminal_v1/`へ回収した。
snapshot SHA256は`ae3c1dfd76773d238a5146172f8bf0319a6132992dce4c02f8759ed0a0196f2d`である。
全67,584行にflagged・undefinedがあり、区間は取得済みだが、これを混合・精度・被覆の合格とは扱わない。
この段階では保存済みの診断を集計したものであり、数値推定の再計算や全物理状態の再decodeは行っていない。
依存ジョブ265506が自動で実行開始し、クラスタcontrollerが同じ索引ジョブの成功を記録して後続を待っていることを確認した。
条件別最終集約・算術照合・全12条件比較・独立計時・最終報告は引き続き未完了である。

## 10:39 JSTの全後処理クラスタ移設

C3T2の索引を8並列のqsubジョブ265505へ移し、全38解析archiveの転送・hash照合を完了した。
入力配置はqsubジョブ265506として索引正常終了後の依存を設定した。
条件別集約・算術照合・全12条件比較・独立計時・日本語報告までの後続controllerもクラスタに配置し、SSH切断後の生存を確認した。
このPCの旧待受は未投入状態を照合して停止済みであり、計算の継続はPC再起動に依存しない。
13件の受入と既存driverの参照確認は成功したが、後続の本番完走と最終結論の検証は未完了である。
詳細・確認script・異常時の手順は[全後処理の移設記録](cluster_postprocess_pipeline_2026-10-24_ja.md)を参照する。

## 09:47 JSTの不要待受整理

固定資源規則では完了済み11条件だけで通常経路の必要時間下界が約34.17時間となり、上限24時間を超えることを確認した。
通常経路の後段6本は未投入・待機中で到達不能と判断し、所有者の依頼に従って終了した。
Pythonは22本から16本になり、索引処理・正式な経路判定・代替経路の後続処理は維持した。
停止PID・照合・証跡は[待受整理の記録](unreachable_waiter_cleanup_2026-10-24_ja.md)を参照する。

## 09:39 JSTのexperimental公開確認

所有者の承認に従い、直近2コミットの識別子を修正し、リポジトリをpublicにして[0.1.0.dev5 experimental Release](https://github.com/junichiharuna/mcmc4qec/releases/tag/v0.1.0.dev5)を公開した。
公開対象は`c27ca896a1025c74975bc45322798eea2e0409b0`で、mainとtagのCIはいずれもsuccessだった。
認証なしの公開照合、配布物・履歴更新・継続事項は[公開結果](publication_result_2026-10-24_ja.md)に保存した。
計算用作業ツリーは固定入力と未コミット差分を維持するため旧履歴を保持しており、この作業ツリーから旧履歴をmergeまたはpushしない。
数値検証は継続中であり、公開を精度・混合・被覆の保証とは扱わない。

## 07:18 JSTの全件回収完了・index開始確認

C3T2（tile288 depolarizing、p=0.001）のPC解析・回収は全38バッチ、768/768群・67,584行が完了した。
DGXは33/33バッチ、laboは5/5バッチで、最後の回収照合時刻は10月24日07:13:54 JSTだった。
[全件の運用記録と再現script](data_tile_validation_2026-10-17/c3t2_runtime_observation_20261024_v9/observation.json)では、固定割当・全batchの開始終了・回収metadataの対応を確認した。
[watch完了記録](data_tile_validation_2026-10-17/c3t2_collection_observer_watch_v1/run/completed.json)でも38バッチ・768群・67,584行が揃っている。
再現scriptのSHA256は `336dbb64ae48a743434bf8a67918decfab892e030a4608117425263958487403` であり、この確認でraw archiveの再hashや数値解析の再実行は行っていない。
後続indexは07:14:33 JSTに開始し、07:18 JSTにローカルPython PID20604の生存と、実commandのscript・registry・registry hash・出力先がindex-intentに対応することを確認した。
この段階は回収archiveの照合・索引作成であり、qsubによる条件別最終集約は後続工程である。
過去のindex実績2.2〜3.1時間を当てはめると終了は本日09:30〜10:30頃が目安だが、データ量とストレージ負荷によって変動する。
条件別集約は本日午後〜夜、全条件比較・独立計時・最終報告は25〜26日を目安とし、queue待ちと検証結果による延長可能性を残す。
全条件比較用の完成入力はまだ11/12条件であり、全件回収の成功を混合・精度・被覆の合格とは扱わない。

## 07:02 JSTのDGX最終バッチ開始

C3T2のDGX batch32は入力生成・転送・stageを終え、実機PID3343504の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch32_start_observation_v1.json)で確認した。
これは残る8群の最終バッチであり、既存serial制御による継続である。
正式回収は760/768群・66,880行のままで、実行中のbatchを完了件数へ加えていない。
全batch回収後の親完了記録は同じ復旧driverがserial完了記録を照合して作成する構成であり、親intentのPID5212と実プロセスのcommand対応を確認した。
この時点で親の完了・停止記録は未作成で、後続の集約・比較は未完了である。

## 06:59 JSTのDGX第32バッチ回収確認

C3T2のDGX batch31は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch31_collection_observation_v1.json)が完了した。
正式回収はDGX 32/33バッチ・labo 5/5バッチ、計760/768群・66,880行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは182,825,719 byte、SHA256は `4449a5ed413f1019266274496c08c6fdb16d30ee78b0490f82b103b681b01a30` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は最後のbatch32の入力生成へ進んでおり、重複投入や制御の再起動はしていない。
残る8群・1バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 06:33 JSTのDGX第32バッチ開始

C3T2のDGX batch31は入力生成・転送・stageを終え、実機PID3331306の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch31_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は740/768群・65,120行のままで、実行中のbatchを完了件数へ加えていない。

## 06:26 JSTのDGX第31バッチ回収確認

C3T2のDGX batch30は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch30_collection_observation_v1.json)が完了した。
正式回収はDGX 31/33バッチ・labo 5/5バッチ、計740/768群・65,120行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは182,509,450 byte、SHA256は `620b285553974c7318ef2b5867bdec00df1ddf05ceb2bb91e8e858fc06196a64` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch31の入力生成へ進んでおり、重複投入や制御の再起動はしていない。
残る28群・2バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 06:00 JSTのDGX第31バッチ開始

C3T2のDGX batch30は入力生成・転送・stageを終え、実機PID3270403の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch30_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は720/768群・63,360行のままで、実行中のbatchを完了件数へ加えていない。

## 05:54 JSTのDGX第30バッチ回収確認

C3T2のDGX batch29は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch29_collection_observation_v1.json)が完了した。
正式回収はDGX 30/33バッチ・labo 5/5バッチ、計720/768群・63,360行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは183,333,441 byte、SHA256は `f1912208cc71e69cbe479286911638d7527e679addcae6642406ebffa84c84af` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch30の入力生成へ進んでおり、重複投入や制御の再起動はしていない。
残る48群・3バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。
続く05:54 JSTの[運用時間の再集計](data_tile_validation_2026-10-17/c3t2_runtime_observation_20261024_v8/observation.json)では平均回収間隔33.07分、残る3バッチへの単純外挿は7:33頃となった。
全回収の目安は引き続き24日7:30〜8:00頃とし、この外挿を終了保証や同じ科学的精度に達するまでの独立計時とは扱わない。

## 05:27 JSTのDGX第30バッチ開始

C3T2のDGX batch29は入力生成・転送・stageを終え、実機PID3257232の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch29_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は700/768群・61,600行のままで、実行中のbatchを完了件数へ加えていない。

## 05:21 JSTのDGX第29バッチ回収確認

C3T2のDGX batch28は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch28_collection_observation_v1.json)が完了した。
正式回収はDGX 29/33バッチ・labo 5/5バッチ、計700/768群・61,600行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは182,785,787 byte、SHA256は `426be1b848e14cdcb511e47e0edd28867010b34f247065564eaa13cb5fdd1772` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch29の入力生成へ進んでおり、重複投入や制御の再起動はしていない。
残る68群・4バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 04:55 JSTのDGX第29バッチ開始

C3T2のDGX batch28は入力生成・転送・stageを終え、実機PID3197350の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch28_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は680/768群・59,840行のままで、実行中のbatchを完了件数へ加えていない。

## 04:48 JSTのDGX第28バッチ回収確認

C3T2のDGX batch27は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch27_collection_observation_v1.json)が完了した。
正式回収はDGX 28/33バッチ・labo 5/5バッチ、計680/768群・59,840行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは183,467,514 byte、SHA256は `22a0761af30435f1b2fc1fbae0306a7024f96a51b4f21d9b55afaf03a52dbc2b` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch28の入力生成へ進んでおり、重複投入や制御の再起動はしていない。
残る88群・5バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 04:23 JSTの所要時間更新

[実測の再集計](data_tile_validation_2026-10-17/c3t2_runtime_observation_20261024_v7/observation.json)は完了したDGX 27バッチ・labo 5バッチの計660群を対象とし、固定割当・開始・正常終了・回収記録を照合した。
DGXの平均回収間隔33.09分から残る6バッチを外挿すると7:33頃となり、全回収の目安は引き続き24日7:30〜8:00頃とする。
残るkernel・初期化の組合せも実測に含まれるが、処理時間や転送条件の変動を除いた終了保証ではない。
詳細と後続処理の見込みは[所要時間の実測基準](runtime_forecast_2026-10-23_ja.md)に記録した。
この集計は運用上の見込みであり、同じ科学的精度に達するまでの独立計時とは区別する。

## 04:22 JSTのDGX第28バッチ開始

C3T2のDGX batch27は入力生成・転送・stageを終え、実機PID3183565の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch27_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は660/768群・58,080行のままで、実行中のbatchを完了件数へ加えていない。

## 04:15 JSTのDGX第27バッチ回収確認

C3T2のDGX batch26は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch26_collection_observation_v1.json)が完了した。
正式回収はDGX 27/33バッチ・labo 5/5バッチ、計660/768群・58,080行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは183,256,685 byte、SHA256は `56e902863bf94a00d124ca45c929f6ac86b5bd6b9a4f1b0c746bf085a7946e6a` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch27の入力生成へ進んでおり、重複投入や制御の再起動はしていない。
残る108群・6バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 03:50 JSTのDGX第27バッチ開始

C3T2のDGX batch26は入力生成・転送・stageを終え、実機PID3121712の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch26_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は640/768群・56,320行のままで、実行中のbatchを完了件数へ加えていない。

## 03:44 JSTのDGX第26バッチ回収確認

C3T2のDGX batch25は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch25_collection_observation_v1.json)が完了した。
正式回収はDGX 26/33バッチ・labo 5/5バッチ、計640/768群・56,320行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは182,627,025 byte、SHA256は `b24ce8dc910a686bb50f292625de6bcd6049b7103500655e6ac0bb75e6afc283` だった。
観測記録とwatch progress、参照metadata 5件のhash、先に確認した実機終了時のcompletion・configのhash対応を照合した。
数値解析やarchiveの再hashは行っていない。
既存serial制御はbatch26の入力生成段階へ進んでおり、serial・回収watch・C3T2の後続5処理・全条件比較の後続10処理のプロセス生存を確認した。
残る128群・7バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。
平均回収間隔約33分に基づく全回収の目安は引き続き24日7:30〜8:00頃であり、後続の集約は同日午後〜夜、全条件比較・独立計時・最終報告は25〜26日を目安とする。
後続処理やqueue待ちによる延長可能性がある。

## 03:17 JSTのDGX第26バッチ開始

C3T2のDGX batch25は入力生成・転送・stageを終え、実機PID3106478の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch25_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は620/768群・54,560行のままで、実行中のbatchを完了件数へ加えていない。

## 03:10 JSTのDGX第25バッチ回収確認

C3T2のDGX batch24は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch24_collection_observation_v1.json)が完了した。
正式回収はDGX 25/33バッチ・labo 5/5バッチ、計620/768群・54,560行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは182,233,651 byte、SHA256は `cc14cd7d6a3ebe3d2e1b5b65444a09e6940126caab8574061fc7b93aa567e998` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch25の入力準備へ進んでおり、重複投入や制御の再起動はしていない。
残る148群・8バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 02:44 JSTのDGX第25バッチ開始

C3T2のDGX batch24は入力生成・転送・stageを終え、実機PID3044305の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch24_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は600/768群・52,800行のままで、実行中のbatchを完了件数へ加えていない。

## 02:38 JSTのDGX第24バッチ回収確認

C3T2のDGX batch23は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch23_collection_observation_v1.json)が完了した。
正式回収はDGX 24/33バッチ・labo 5/5バッチ、計600/768群・52,800行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは181,619,524 byte、SHA256は `06af4e0d77466df2716b634aaccae3ebbe54ba9e47191b116d00a516588d86cb` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch24の入力準備へ進んでおり、重複投入や制御の再起動はしていない。
残る168群・9バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。
続く02:38 JSTの[運用時間の再集計](data_tile_validation_2026-10-17/c3t2_runtime_observation_20261024_v6/observation.json)では平均回収間隔33.16分、残る9バッチへの単純外挿は7:36頃となった。
この見込みには未観測のkernel・初期化割当や転送条件によるずれがあり、終了時刻や科学的精度の保証ではない。

## 02:11 JSTのDGX第24バッチ開始

C3T2のDGX batch23は入力生成・転送・stageを終え、実機PID2982588の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch23_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は580/768群・51,040行のままで、実行中のbatchを完了件数へ加えていない。

## 02:05 JSTのDGX第23バッチ回収確認

C3T2のDGX batch22は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch22_collection_observation_v1.json)が完了した。
正式回収はDGX 23/33バッチ・labo 5/5バッチ、計580/768群・51,040行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは180,960,808 byte、SHA256は `f7a3c8624a694f20522cc6ce4545423a9af131bbc19d4f729cbb4563a7afd9d4` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch23の入力準備へ進んでおり、重複投入や制御の再起動はしていない。
残る188群・10バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 01:37 JSTのDGX第23バッチ開始

C3T2のDGX batch22は入力生成・転送・stageを終え、実機PID2967713の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch22_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は560/768群・49,280行のままで、実行中のbatchを完了件数へ加えていない。

## 01:31 JSTのDGX第22バッチ回収確認

C3T2のDGX batch21は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch21_collection_observation_v1.json)が完了した。
正式回収はDGX 22/33バッチ・labo 5/5バッチ、計560/768群・49,280行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは181,389,414 byte、SHA256は `670259f6a0a24d29145c87d91b99a3b94dcf4f3def2003639d2070ca9889dbe5` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch22の入力準備へ進んでおり、重複投入や制御の再起動はしていない。
残る208群・11バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 01:05 JSTのDGX第22バッチ開始

C3T2のDGX batch21は入力生成・転送・stageを終え、実機PID2906506の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch21_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は540/768群・47,520行のままで、実行中のbatchを完了件数へ加えていない。

## 00:59 JSTのDGX第21バッチ回収確認

C3T2のDGX batch20は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch20_collection_observation_v1.json)が完了した。
正式回収はDGX 21/33バッチ・labo 5/5バッチ、計540/768群・47,520行となった。
このbatchは20群・1,760行、infrastructure failed 0・context failed falseで、archiveは181,460,488 byte、SHA256は `2c0520c8c0ca424e1626a705a7882b864a4f7d62d5034330c3848794789cabca` だった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
既存serial制御は次のbatch21の入力準備へ進んでおり、重複投入や制御の再起動はしていない。
残る228群・12バッチと後続の集約・全条件比較は未完了であり、回収の正常終了を混合・精度・被覆の合格とは扱わない。

## 00:32 JSTのDGX第21バッチ開始

C3T2のDGX batch20は入力生成・転送・stageを終え、実機PID2892940の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch20_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は520/768群・45,760行のままで、実行中のbatchを完了件数へ加えていない。

## 00:25 JSTのDGX第20バッチ回収

C3T2のDGX batch19は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch19_collection_observation_v1.json)が完了した。
archiveは181,744,851 byte、SHA256は `fc2dff351cd20cb27ebd10bfbfe203ecb5fb0df51546c314482006487d521364` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認し、数値解析やarchiveの再hashは行っていない。
正式回収はDGX 20/33バッチ・labo 5/5バッチ、計520/768群・45,760行となった。
残る248群の解析・回収と後続の集約・全条件比較は未完了であり、回収完了を混合・精度・被覆の合格とは扱わない。

## 00:22 JSTのDGX第20バッチ計算終了

C3T2のDGX batch19は実機の終了記録を確認し、ローカルの[launch完了記録](data_tile_validation_2026-10-17/portable_condition_c3t2_dgx_batch19_launch_v1/completed.json)のcompletion hashと一致した。
SSH実行の終了コードは0で、completionのSHA256は `3631c36033ad5947e9f47bb84243b7be68bb54ef710a4dd7a54c679289bb134c` だった。
既存serial制御は回収へ進んだが、この時点では回収・照合は未完了である。
正式回収は500/768群・44,000行のままで、このbatchの20群は未加算である。

## 00:12 JSTの実機稼働確認

DGX batch19の親PID2831416の生存と終了記録未作成を再確認した。
同PIDの子プロセスを `ps -o pid,ppid,stat,pcpu,time,comm --ppid 2831416` で照会し、20個の計算workerが全てR状態で、各workerのCPU使用率は1論理CPU基準で99.1〜99.6%だった。
これとは別にCPU使用率0.0%の補助Pythonプロセスが1個あった。
追加benchmarkや計算の再投入は行っておらず、この観測は計算資源の使用確認であって科学的な計時比較ではない。
正式回収は500/768群・44,000行のままである。

## 00:00 JSTの確認

低ノイズ12条件のうち11条件の比較用入力が揃い、残るtile288 depolarizing p=0.001（C3T2）の後処理を継続している。
C3T2のsamplingとtrace監査は完了済みで、現在のPC処理は保存済みtraceの解析である。
前日までの経緯と各バッチの照合記録は[10月23日の状態文書](PROJECT_STATUS_2026-10-23_ja.md)に残す。

| 対象 | 確認した状態 |
|---|---|
| C3T2の正式回収 | 500/768群・44,000行、全38バッチ中24バッチ |
| DGX | 19/33バッチ回収済み、20番目のbatch19を実行中 |
| labo | 全5バッチの計算・回収・照合が完了、120群・10,560行 |
| クラスタ | qstatで投入scriptに本プロジェクト名を含むactive jobは0件 |
| 後続処理 | index・配送・最終集約・全条件比較・独立計時・報告の制御プロセスは稼働し、必要な入力を待っている |

DGXの実機PID2831416が生存し、終了記録がないことを確認した。
この実行は[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch19_start_observation_v1.json)と同じ設定hashに対応する。
laboは[serial完了記録](data_tile_validation_2026-10-17/portable_condition_c3t2_labo_serial_driver_v1/completed.json)の `all_assigned_batches_collected=true` を再確認した。
完了したlabo制御を再起動せず、既存DGX serialと自動回収監視を継続する。
クラスタのactive jobが0件であることは、後続クラスタ処理が不要になったことを意味しない。
クラスタ投入はqsub・共有lock・最大2ノードの既存計画に従う。

## 残作業と見込み

1. DGXに残る14バッチ・268群の解析と回収・照合。
2. 全768群を揃えたC3T2のindex、最終集約、算術照合、比較用入力の準備。
3. 低ノイズ全12条件の正式比較、事前規則に従う独立計時、最終報告と再現情報の照合。

[最新の運用時間観測](data_tile_validation_2026-10-17/c3t2_runtime_observation_20261023_v5/observation.json)ではDGXの平均回収間隔は33.22分で、残り14バッチへの単純外挿は24日7:38頃である。
DGXで未計測のkernel・初期化組合せと転送・queue待ちの影響があり、確定した終了時刻ではない。
C3T2集約は24日午後〜夜、全条件比較・独立計時・最終報告は25〜26日という目安を維持し、後続処理による延長可能性を残す。
この運用見込みを、同じ精度に達するまでの計算時間の科学的比較には使わない。

## 科学的な到達点と限界

[Goalの完了条件と確認済み範囲](goal_completion_status_2026-10-23_ja.md)に、実装・主4条件の校正・公開候補と未完了項目を整理している。
tile符号とBP-LSD・BeliefFind・Union-Findの実装・受入記録はあるが、新decoderのBAR被覆や速度順位は未校正である。
[tile288 depolarizing p=0.003の結果](low_c3t1_result_2026-10-23_ja.md)は集約・回収・算術照合まで完了した一方、全352設定の各192反復に診断flag・診断未定義があり、経験的な相対RMSE 10%・20%の判定も未達だった。
部分的な重み層別推定値を真値とせず、広いreference区間との整合から精度や95%被覆を認定しない。
[日本語の途中結果の利用案内](low_noise_interim_usage_2026-10-23_ja.md)と[英語の検証案内](../tile_validation_interim_en.md)に、最初の再現対象候補と適用限界をまとめている。
計算や回収の正常終了と、混合・精度・被覆の合格を区別する。

## 公開準備

00:00 JSTのGitHub API照会ではリポジトリはPRIVATE、mainは `98222e1daf80e4387a5fd588729052baee923515`、Releaseは0件だった。
過去の文書にある公開済みという記載を、現在の公開状態の根拠にはしない。
[公開候補の状態](publication_candidate_status_2026-10-23_ja.md)には、source ZIP・wheel・Release本文・検証記録を保存済みである。
既に提示した直近2コミットの履歴修正・反映方法の判断を待っており、この確認でcommit・push・公開切替・Release作成は行っていない。
experimental公開は数値検証の全完了を待つ必要はなく、公開準備と継続中の数値検証は並行して扱う。
新しい状態文書や途中結果の英語案内は作業ツリーの更新であり、固定済みの公開候補archiveへ追加したとは扱わない。
