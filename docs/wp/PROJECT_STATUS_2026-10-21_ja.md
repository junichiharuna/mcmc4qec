# mcmc4qec：2026-10-21の継続状態

10月22日以降の最新状態は[翌日の継続記録](PROJECT_STATUS_2026-10-22_ja.md)を参照する。

## 最新状況（23:52 JST）

低ノイズ検証の正式完了は7/12条件で、残る5条件・独立計時・最終報告は未完了である。
22:42 JSTにC3T0（tile288 depolarizing、p=0.01）のsample1で30,720/30,720件の完了マーカーを観察し、22:35 JSTの観察から98件増加した。
sample0と合わせて61,440/61,440件がそろい、固定sourceから生成した全タスク集合と独立列挙に対する想定外ファイル名は0件だった。
PBS job265411はR・run_count 1、sample1のsummaryは未作成であり、マーカーの存在をタスク成功や数値検証の合格とは扱わない。
観察は `data_tile_validation_2026-10-17/c3t0_sample1_full_task_marker_observation_20261021_v14.json`、SHA256は `a1d11a07e47877711a0b536f19243cb2f0b172c54e19e547f2c684006be8d361` に保存した。
22:42 JSTの観察でも265411はRであり、全マーカーの存在をジョブの正常終了や全タスクの成功とは扱わず、summary・後続の監査・最終集計を待つ。
終了手順のコードを確認すると、`run_partition` は並列タスクの戻り値を集めた後、全taskのJSON・NPZ・markerのhashと保存recordを照合し、その後にsummaryを書き出す。
確認した `cluster_scripts/tile_low_noise_sampling_partitions.py` はクラスタbundle内の同名sourceとSHA256 `766e34275905eaeb13a99402cc963f0bc9894047a33f3a58b38aa7afb8047455` で一致した。
これは全マーカー作成後にも終了処理が残る構成の確認であり、実行中プロセスの現在の関数位置を特定したものではない。
22:26 JSTにDGXのC1T2 batch8とLabo batch1の実PID終了・対応するcompletionを確認した。
C1T2（tile288 bit-flip、p=0.001）はDGX batch11の実PID終了・対応するcompletionと23:51 JSTの回収・転送検証完了を確認し、独立なbyte照合を加えた確認済み結果は288/768群・25,344行となった。
新20群の固定割当との一致、既存群との重複なし、ZIP全体と全96 memberのhash、前回観察で固定したmetadataの不変性を確認した。
新1,760行は全行に診断警告・未定義項目があり、区間未取得は0行で、これらを分母から除かず保持する。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v12.json`、SHA256は `dfa80d44504688557606be06f3fb57374e4184ed82fb4058259439c96aaaedd4` に保存した。
この確認は転送・構造・保存データのbyte照合であり、数値再計算・native再decode・条件全体の科学的受入ではない。
23:26 JSTに既存の後続driver・待機処理37個のsessionが生存していることを確認した。
既存serial driverは次のDGX batch9・Labo batch2へ進み、22:30 JSTに固定configに対応する実PID3567505・13892の稼働と、両batchのcompletion未作成を確認した。
その後DGX batch9の回収を終え、23:00 JSTにはbatch10の固定configに対応する実PID3577642の稼働とcompletion未作成を確認した。
batch10の回収後、23:27 JSTにはbatch11の固定configに対応する実PID3634372の稼働とcompletion未作成を確認した。
21:57 JSTのqstatではC3T0 samplingの265411がR、C1T2 capacity auditの265416がQで、要求ノード数合計2を維持している。
C1T1（tile288 bit-flip、p=0.003）の転送検証済み回収はDGX648群・Labo120群、計768/768群となった。
新たに回収したDGX batch32のarchiveをローカルで再hashし、receiptと一致することを確認した。
最後のbatchのreceiptに記録された数値行検証は704行、infrastructure failureは0群、context failureはfalseであり、条件全体の科学的受入とは区別する。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v40.json`、SHA256は `7e52cf2a706e37ede72a570a5ec721b419ac94957402953f0af56e6d23f3dc80` に保存した。
前回観察が記録した全receiptとLabo担当完了観察のhashが変わっていないことも確認した。
DGXのserial driverは18:01:13 JSTに全33 batchの回収を記録し、exit code 0で終了した。
両hostの全38 batchのassignment・config・completionのmetadataをreceiptのhashと照合し、独立に列挙した全768群と重複・欠けなく一致すること、保存completionが計67,584行を記録していることを確認した。
この確認はmetadataの照合であり、過去の全ZIP payload再hash・全群の数値再計算・科学的受入は含まない。
観察は `data_tile_validation_2026-10-17/c1t1_all_hosts_assignment_completion_observation_20261021_v1.json`、SHA256は `d0db7053a06dc8028a2cee0a67313066edccfeeb64aab462996e0b3a537130f0` に保存した。
全群回収を受けて既存driverがcohort index作成を開始し、20:43:15 JSTに正常終了した。
固定readerの全archive照合後のsnapshotは768/768群・67,584/67,584行、pending 0・区間未取得0・infrastructure/context failure各0で、診断警告67,584行・診断未定義65,908行を保持している。
完了record・registry・assignment・snapshotのhash対応、独立に列挙した全768群と行数・診断数の集計、現在の検証source 45ファイルのhashを確認した。
観察は `data_tile_validation_2026-10-17/c1t1_full_index_completion_observation_20261021_v1.json`、SHA256は `9e502884299533e11ed0a96ec2c4da380e4cd14a019d59c690b134a13679f389` に保存した。
これは保存済み結果の全件照合であり、数値再計算・全状態再decode・科学的なcohort受入とは区別する。
既存の後続driverは20:55:21 JSTに最終集計用の転送を正常終了し、170ファイル・5,029,753,220 byteのremote census・payload hash検査を記録した。
ローカルのplan・context・完了記録・indexとのhash対応と、remoteの保存済みtransfer receipt・contextを独立に読み照合した。
この追加確認では全5 GBのpayload再hashや科学的計算を再実行していない。
観察は `data_tile_validation_2026-10-17/c1t1_distribution_completion_observation_20261021_v1.json`、SHA256は `7bc9e0a714e8f586b8310e11689a8ef388aa765d8bb5cc188dcc7af5034f188b` に保存した。
既存driverは21:01:48 JSTに最終設定のprepare処理を正常終了した。
remoteの設定・投入script・転送context・sampling条件・native reference・監査設定のhash対応を確認し、保存されたpreflight成功記録と照合した。
最終集計用設定は1 CPU・32 GB・walltime上限12時間であり、この上限は終了予想時刻ではない。
観察は `data_tile_validation_2026-10-17/c1t1_final_preparation_observation_20261021_v1.json`、SHA256は `08aa000faea94aeb08123506ad9c56604f5cac6a81a0ed7281f44624db901cee` に保存した。
後続の投入driverもpreflightを完了したが、21:03 JST時点では既存2要求ノードが使用中・待機中のため、最終集計のqsubは未実施である。
最終report・独立再集計は未完了である。
19:00 JSTの再確認ではindexの実PID38164が稼働し、CPU累積時間は1,393.5625秒で、snapshot・完了記録は未作成だった。
DGXのC1T2 parityも受理され、1群の全88行・2,328診断・2,328 ACF配列の照合結果、回収ファイルのhash、native referenceとの対応を確認した。
許容誤差rtol=1e-10・atol=1e-12と未定義位置・離散フラグの一致を確認し、保存traceの数値照合と別環境のnative decoderの一致を区別する。
観察は `data_tile_validation_2026-10-17/c1t2_dgx_parity_acceptance_observation_20261021_v1.json`、SHA256は `672d9a666b0e3a6c7d3f6231e09e822ab241aba91e0532cd7333e26328bcd5fe` に保存した。
その後、DGXのC1T2 batch0本解析が開始し、18:18 JSTに固定configに対応する実PID3289068の稼働を確認した。
Labo担当の5 batch・120群は割当表と重複・抜けなく一致し、担当driverは正常終了した。
後続C1T2用Labo waiterはnative referenceの受理を検知し、17:22 JSTに次条件のserial driverを起動した。
Laboのparityは17:45 JSTに受理され、1群の全88行・2,328診断・2,328 ACF配列を比較した保存結果、実SSH終了コード0、回収ファイルのhashとnative referenceとの対応を確認した。
数値照合の許容誤差はrtol=1e-10・atol=1e-12で、未定義位置・離散フラグの一致も記録されている。
これは保存traceの数値解析の照合であり、decoder factory呼出しは0回で、別環境のnative decoderの一致や条件全体のbias・被覆の保証ではない。
観察は `data_tile_validation_2026-10-17/c1t2_labo_parity_acceptance_observation_20261021_v1.json`、SHA256は `261a98466478665c0c022f376e4401673d70195c09fbd73bca3efcf3851b5f12` に保存した。
その後、LaboのC1T2 batch0本解析が開始し、固定configに対応する実PID21388の稼働を確認した。
条件全体の受入は未完了である。
18:35 JSTにもC1T2 batch0のDGX実PID3289068・Labo実PID21388が固定configに対応して稼働し、両batchのcompletionは未作成であることを確認した。
その後、DGX batch0は18:38 JSTに転送検証まで完了し、C1T2の回収済み結果は20/768群・1,760行となった。
固定割当表の全768群を独立に列挙した集合と照合し、今回の20群が担当batchと一致すること、receipt・転送検証・source pinの対応、保存ZIP全体と記録された全96 memberのbyte hashを確認した。
このbatchはinfrastructure failure 0群・context failure false・区間未取得0行だが、警告行と診断未定義行はそれぞれ1,760行であり、未定義項目や警告を分母から除かず保持する。
これは保存結果の転送・構造確認であり、数値再計算・native再decode・条件全体の科学的受入を意味しない。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v1.json`、SHA256は `f1d67dc004c6fe14fe630d72dd5d7227dc2a23dc10892530dafe489bf2db7ad7` に保存した。
DGXの既存serial driverは次のbatch1本解析へ進み、19:00 JSTに固定configに対応する実PID3299202の稼働とcompletion未作成を確認した。
batch1は19:05 JSTに終了し、実PIDの終了と対応するcompletionのhashを確認した後、19:07 JSTに回収・転送検証を完了した。
C1T2の回収済み結果はDGXの2 batch・40/768群・3,520行となり、既存20群との重複がなく固定割当表に一致することを確認した。
新batchのZIP全体と記録された全96 memberのbyte hashを再確認し、前回観察で記録したmetadataのhashが変わっていないことも確認した。
新batchも全1,760行に診断警告・未定義項目があり、区間未取得0行で、保存した診断を保持する。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v2.json`、SHA256は `2da06692e9d683550bfc076a3e487084a088a94c05f8e24057c57f0b587b8e58` に保存した。
DGXの既存serial driverはbatch2本解析へ進み、19:12 JSTに固定configに対応する実PID3309489の稼働を確認した。
同時点でLaboのbatch0実PID21388も稼働し、両batchのcompletionは未作成で、C1T1の全群indexも実PID38164で継続中である。
DGX batch2は19:34 JSTに終了し、実PIDの終了とcompletionのhashを確認した後、19:35 JSTに回収・転送検証を完了した。
C1T2の確認済み回収はDGXの3 batch・60/768群・5,280行となり、今回も新20群の割当との一致・既存40群との重複なし・新ZIP全体と全96 memberのbyte hashを確認した。
新batchの1,760行も全行に診断警告・未定義項目があり、区間未取得0行で、これらを保持する。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v3.json`、SHA256は `48ecd348343b9ccbb0ce566a6a494c3087df74a8a1112ce71b72b47be9326ca5` に保存した。
今回の読取専用確認スクリプト・実行引数・実データでの確認記録は `data_tile_validation_2026-10-17/c1t2_collection_observer_20261021_v1/manifest.json`、SHA256は `1afa81ad07e962f417ae497431ab673751582997ef552d89efda925407bbd13c` に保存した。
この補助確認は記録された回収時点のcensusを前提とし、計算・投入・数値受入を変更せず、全条件の科学的検証とは区別する。
19:40 JSTにはDGXの既存serial driverがbatch3本解析へ進み、固定configに対応する実PID3365979の稼働とcompletion未作成を確認した。
C1T1の全群indexも継続中で、クラスタの265411・265415はともにR、要求ノード数合計2である。
DGX batch3は20:04 JSTに回収・転送検証を完了し、同じ観察時点でLabo batch0の24群も回収済みとなった。
C1T2の確認済み回収はDGX80群・Labo24群、計104/768群・9,152行となった。
新44群の割当との一致・元60群との重複なし・新ZIP全体と全208 memberのbyte hashを確認し、追加3,872行の診断警告・未定義項目を保持した。
単一batch追加用の読取専用補助観察が同時回収の検知で停止したため、旧版と停止ログを保持し、明示した複数batchを確認してから実回収集合と完全一致を要求する別版を用いた。
追加を1 batchだけ指定した場合の拒否と、今回の2 batchを指定した実確認の成功を確認し、計算・回収・科学的受入の実装は変更していない。
詳細は[同時回収の観察手順](c1t2_collection_observer_increment_2026-10-21_ja.md)、観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v4.json`、SHA256は `e131609e629cfa34c8b3deba74bf9f74696b039d62a388e552186e9b5e470bbb` に保存した。
20:08 JSTにはDGX batch4の実PID3375498とLabo batch1の実PID13040が固定configに対応して稼働し、両batchのcompletionは未作成であることを確認した。
その後、DGX batch4の実プロセス終了と対応するcompletionのhashを確認し、回収・転送検証済みの20群を追加照合した。
C1T2の確認済み回収はDGX100群・Labo24群、計124/768群・10,912行となった。
新20群の割当との一致・既存104群との重複なし・新ZIP全体と全96 memberのbyte hashを確認し、以前のmetadata hashが変わっていないことを確認した。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0行で、これらを保持する。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v5.json`、SHA256は `608a9aa210306e57394315bee22422bcc2760a13b8185ad8b23a14c1a62445bf` に保存した。
これは保存結果の転送・構造確認であり、数値再計算・native再decode・条件全体の科学的受入を意味しない。
DGXの既存serial driverはbatch5本解析へ進み、20:37 JSTに固定configに対応する実PID3432945の稼働とcompletion未作成を確認した。
batch5の実プロセス終了とcompletionのhashを確認し、21:02 JSTに回収・転送検証済みの20群を追加照合した。
C1T2の確認済み回収はDGX120群・Labo24群、計144/768群・12,672行となった。
新20群の割当との一致・既存124群との重複なし・新ZIP全体と全96 memberのbyte hashを確認し、前回のmetadata hashが変わっていないことを確認した。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0行で、これらを保持した。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v6.json`、SHA256は `b2063610a9b682fa03361ae5c5a4bbc6f07c72cdc7bb32706a25c32e245272bf` に保存した。
DGXの既存serial driverはbatch6本解析へ進み、21:06 JSTに固定configに対応する実PID3443622の稼働とcompletion未作成を確認した。
batch6の実プロセス終了とcompletionのhashを確認し、21:30 JSTに回収・転送検証済みの20群を追加照合した。
C1T2の確認済み回収はDGX140群・Labo24群、計164/768群・14,432行となった。
新20群の割当との一致・既存144群との重複なし・新ZIP全体と全96 memberのbyte hashを確認し、前回のmetadata hashが変わっていないことを確認した。
追加1,760行は全行に診断警告・未定義項目があり、区間未取得は0行で、これらを保持した。
観察は `data_tile_validation_2026-10-17/c1t2_pc_collection_observation_20261021_v7.json`、SHA256は `463089bcdae18421feaf09b9091f6e8cbed58c99c8a71de7cf81c5021e9bf023` に保存した。
DGXの既存serial driverはbatch7本解析へ進み、21:33 JSTに固定configに対応する実PID3500596の稼働とcompletion未作成を確認した。
C1T2（tile288 bit-flip、p=0.001）のsampling前半265389は12:17:34 JSTにF・Exit_status=0で終了し、summaryの全46,080件・失敗0・欠損0と投入記録の対応を確認した。
sampling後半265390も16:55:31 JSTにF・Exit_status=0・run_count=1で終了し、実walltimeは4時間37分56秒だった。
summaryの全46,080件が予定task列と一致し、失敗0・欠損0・重複0で、manifest・execution intent・native preflight・qsub投入記録・実PBS終端の対応を確認した。
この確認はmetadataとtask一覧の照合であり、raw trace全体の独立再hashや再decode、条件全体の科学的受入とは区別する。
既存driverがqsubで投入したC3T0（tile288 depolarizing、p=0.01）のsampling後半265411は16:55:31 JSTに開始している。
C1T2 native reference265414は17:21:14 JSTにF・Exit_status=0・run_count=1で終了し、実walltimeは25分15秒だった。
回収・受理記録を実PBS終端と照合し、保存ZIP全491ファイルのhashとmarker対応を固定readerで再確認した。
このreferenceは1群・88行・2,328 ACF配列の照合用結果であり、数値再実行・条件全体の受入・別環境での全decoder入力の一致を意味しない。
観察は `data_tile_validation_2026-10-17/c1t2_native_reference_collection_observation_20261021_v1.json`、SHA256は `5e6a3efa9121a8a7c0bdf4bd94bdbee36e2df817521107ca4f886505dd1177c4` に保存した。
既存driverがqsubで投入したC1T2 sampling collector265415は17:21:41 JSTに開始し、script・投入記録・実PBSの対応を確認した。
C1T2 sampling collector265415は20:26:11 JSTにF・Exit_status=0・run_count=1で終了し、実walltimeは3時間4分29秒だった。
既存driverの回収受理記録を実PBS終端・qsub投入記録・remote script hashと照合した。
full trace監査と条件全体の科学的受入は未完了である。
続くcapacity監査265416は既存driverが20:29 JSTにqsubで投入し、20:36 JSTの確認ではQだった。
そのqsub記録・script hash・collector参照を照合し、実行中265411と待機中265416の要求ノード数の合計は2だった。
観察は `data_tile_validation_2026-10-17/c1t2_collector_terminal_capacity_submission_observation_20261021_v1.json`、SHA256は `4f59646d2c9ddf20451580058a195a5e6e9e30d670d334ccf32c3ed64826e3be` に保存した。
21:40 JSTのC3T0 sampling後半では、予定30,720 taskに対し25,433件のdone marker名を観測し、21:17 JSTから2,233件増えた。
固定sourceのtask生成と独立な列挙で全61,440 taskが一致し、前半を含む観測56,153 marker名の全7座標を照合して範囲外0件を確認した。
後半job265411はR・run_count=1で、summaryは未作成である。
marker名の存在はtask成功・数値artifactの正しさ・区画完了を意味せず、更新中のfilesystemの観察である。
確認コードを含む観察は `data_tile_validation_2026-10-17/c3t0_sample1_full_task_marker_observation_20261021_v10.json`、SHA256は `ac1d389ebb7ceba561e79e267be16da9cdaa698000706648201b33fe878de04e` に保存した。
前回と同じ確認コード・metadata・sourceのhashで照合し、前回観察のhashも保存した。
観察と確認コードは `data_tile_validation_2026-10-17/c1t2_sample1_terminal_followup_observation_20261021_v1.json`、SHA256は `c375ebf382db5fb928485fa4e13d15be0a70814479826b7d8636ad33d558d7f1` に保存した。
以下のmarkerとCPU時間の記述は、終了前の観察経緯である。
16:02 JSTのsampling後半のdone markerは46,080/46,080件となり、15:56 JSTの全task照合から1,209件増えて予定task名が全て揃った。
job265390はR・run_count=1、summaryは未作成だった。
hashで固定された生成コードと独立に列挙したplanの予定92,160 taskが一致し、前後半を合わせた観測92,160 markerの全7座標を照合して範囲外0件を確認した。
全marker名が揃ったことはtask成功や区画完了を意味せず、区画内の終了検証・summary作成・回収・独立監査を待つ。
16:13 JSTにもjob265390はR・run_count=1、summaryは未作成で、前回観察からPBS報告のCPU使用時間は8,035秒、walltimeは721秒増えていた。
PBSの集計には遅延があり、この増加だけで検証工程の進捗や成功を証明しない。
全marker作成後の観察は `data_tile_validation_2026-10-17/c1t2_sample1_post_marker_observation_20261021_v1.json`、SHA256は `195c15bd421dcaa4ee945f8c43d5e01120ec01c280e68f4c385b53ae85735886` に保存した。
観察中もmarkerが追加されるため同時刻の厳密なsnapshotではなく、marker payload・成功判定・数値artifactの監査とは区別する。
確認コードを含む観察は `data_tile_validation_2026-10-17/c1t2_sample1_full_task_marker_observation_20261021_v4.json`、SHA256は `455018990e4ebc9a2b36f5a3f9dfb3aa9d53c5898bbb71704d0e4032972d8be4` に保存した。
前回観察のhashを保存し、同じ確認コードとmetadata・sourceのhashで照合した。
待機中を含む要求ノード数は2であり、区画の終了を条件全体の検証完了とは扱わない。
以下の実行経緯には過去時点の進捗を残しており、最新の完了数・回収数は本節を参照する。

## 公開準備

GitHub experimental版の準備は完了済みで、配布候補は `47ef1b6ad957a93dae3bbd6cf1d79fab86457e96` に固定している。
添付対象は `output/experimental_release_20261019/assets_with_platform_v2/` のsource ZIP・wheel・platform validation ZIP・単一の `SHA256SUMS` で、日英Release本文は `output/experimental_release_20261019/release_body_final_v2.md` にある。
過去の `assets_with_platform_v1` は今回の候補とsource ZIPが異なるため、添付対象には用いない。
状態文書の案内を更新した後も、現行v2の配布物3点とSHA256SUMSが固定候補のhashに一致し、Release本文が候補commitを指すことを再確認した。
観察は `data_experimental_release_2026-10-19/release_asset_integrity_20261021_v1.json`、SHA256は `3f9b758f940b31ec618ba3c653396ab29973c84e6acf0212399dfa838388160f` に保存した。
この再確認はbyte hashと本文の参照先の確認であり、配布物の再build・テストの再実行・公開操作・未完了の数値校正は含まない。
テスト・配布物・日英Release本文・実装範囲の根拠は[前日の状態文書](PROJECT_STATUS_2026-10-20_ja.md)を参照する。
22:41 JSTの再確認でもlocal HEAD・remote main・CI run39325976119のheadは `886b44b9fdc56d5b86491302dfb651285bbc4113` で一致し、同CIの全12 jobは成功している。
確認対象のsrc・tests・examples・notebooks・英日README・pyproject・CI workflowの追跡済みファイルにHEADからの差分はなく、repositoryはprivate、Release一覧は空だった。
観察は `data_experimental_release_2026-10-19/remote_status_20261021_v4.json`、SHA256は `37598e04dafd65741d4428fd7120bc64097ea02000f5a9b1f33bb9158d2a338b` に保存した。
公開操作・新しいcommit/pushは行っていない。

## 科学検証

主4条件の比較は完了し、低ノイズはtile72の6条件とtile288 bit-flip p=0.01の計7/12条件を完了した。
tile288の残る5条件と低ノイズ独立計時は未完了である。
C1T0の完了と適用限界は[2026-10-21の条件別報告](low_c1t0_recovered_result_2026-10-21_ja.md)を参照する。
前日23:55までに[C0T2の独立算術レビュー](low_c0t2_arithmetic_review_result_2026-10-20_ja.md)を追加し、全67,584行・352設定・11,968照合値が最終reportと最大差0で一致した。
[6条件比較](low_long_six_comparison_result_2026-10-20_ja.md)に使った長い16設定の432値も最大差0だった。
この一致を混合や名目95%被覆の保証とは扱わず、診断警告を保持する。

## 実行と環境修正

C1T1 sampling後半265361は前日23:55:18に正常終了した。
native reference265368は00:17:22にF・Exit_status=0・run_count=1で終了し、回収・受理も完了した。
C1T0 capacity監査265367は前日23:56:09に正常終了し、受理済みである。
その後のfull-planは、生成時とthread_environmentが異なるため停止した。
旧引継ぎと、依存するC1T1収集・C1T2生成・C1T0最終設定・C1T0最終投入の4本はerrorを保存して停止した。
失敗記録を削除せず、同じnative判定を使ったread-only診断で、元の1 thread設定をPython起動前に与えると全比較項目が一致することを確認した。
詳細は[環境修正記録](recovery_full_thread_environment_2026-10-21_ja.md)に保存する。

local PID46920の別引継ぎで未作成のfull planから再開し、00:04時点でplanを正常作成してpreflightへ進んだ。
元worker・監査config・source・数値計算・qsub protocolは変更していない。
保存capacityに基づくfull監査要求は1 node・96 CPU・62 GB・1時間30分であり、要求時間をETAとは扱わない。
その後full監査265369をqsubで投入し、00:11:21にF・Exit_status=0・run_count=1で終了した。
実walltimeは4分30秒で、terminalを受理済みである。
旧capacityは再計算していない。
停止した後続4本は、旧sourceと失敗記録を残し、3本の新しいdriverへ接続し直した。
C1T1収集・監査は `planned_c1t1_thread_resume_v1` のPID28916で再開し、collector265370をqsubで投入して00:18時点で実行中である。
C1T0最終設定・最終投入は `c1t0_final_resume_v1` のPID47776で順に実行する構成とし、full監査受理済み・全PC回収未完了の状態で待機している。
C1T2生成は `c1t2_generation_resume_v1` のPID6248で再開し、C1T1 full監査とnative referenceの受理待ちである。
新しい制御用driverと元driverの回帰テストは、それぞれ38・59・21件がWindows上で成功した。
元のnative worker・数値計算・受理条件は変更していない。
source・テスト・red/greenログの12ファイルと環境manifestは [orchestration_thread_resume_20261021_v1](data_tile_validation_2026-10-17/orchestration_thread_resume_20261021_v1/manifest.json) に保存した。
新しいdriverのLinux単独テストは未実施であり、テスト成功を数値結果の検証完了と扱わない。

## PC処理と待機

C1T0のhost側回収はDGX400群・Labo96群の計496/768群である。
DGX batch19は00:13:44、Labo batch3は00:08:30に回収記録を保存した。
全群のlocal独立index・転送は両PCの正常完了待ちである。
00:17のpollで、新しいC1T0最終処理とC1T2生成待機のsession継続を確認した。
正常終了したC1T0監査とC1T1 native referenceのsessionは終了を回収済みである。
失敗を確認した旧5 sessionは再起動せず、別記録のdriverを使用している。
クラスタの投入は引き続きqsubを用い、Qを含め最大2要求ノードを維持する。

## 00:23 JST：独立anchorの先行実行

C1T1 collectorが1ノードを使う間の空き枠で、事前準備済みC3T0 anchor partition 0を先行実行した。
実行順だけを前倒しし、固定された設定・seed・resource・既存投入guardは変更していない。
qsubで受け付けられた265371はRであり、265370と合わせて合計2要求ノードである。
詳細と実PBS記録は [C3T0投入記録](c3t0_anchor_dispatch_2026-10-21_ja.md)に保存した。
C3のsampleは未投入であり、旧preflightのexecute未使用状態を現状として流用しない。
DGX batch20の実PID2133962とLabo batch4の実PID30280の継続を独立observerで確認した。

## 00:26 JST：C3T0 sampling前半へ進行

C3T0 anchor265371は00:24:32に正常終了し、元validatorで実PBS・script・resource・ownerを照合して受理した。
実walltimeは2分35秒だった。
空き枠を継続活用するため、事前固定済みsample partition 0まで先行実行する判断へ更新した。
sample265372をqsubで投入し、265370と合わせて2要求ノード・両方Rを確認した。
sample partition 1は未投入であり、C3T0の生成全体や科学的検証の完了とは扱わない。
投入と終端の証跡は [C3T0投入記録](c3t0_anchor_dispatch_2026-10-21_ja.md)に追記した。

## 00:34 JST：C1T2生成後の引継ぎ準備

C1T2の生成registry完成後に既存native driverを起動し、各PCを前条件から引き継ぐ親処理を追加した。
初版は実受入記録のschema差を検出して子起動前に停止し、証拠を保存した別v2で修正した。
修正版は実ファイルの照合と実子processの終了検査を含む23件、接続先の回帰20・19件に成功した。
PID22720で起動し、生成registry未完了・子process未起動の待機状態を確認した。
sourceと受入・実行記録は [仕様と実施結果](c1t2_downstream_launch_spec_2026-10-21_ja.md)に保存した。
クラスタは265370と265372がRで、最大2要求ノードを維持している。
DGX batch20の回収が完了し、C1T0 host側回収はDGX420群・Labo96群の計516/768群となった。
正式な低ノイズ検証完了数は6/12条件のままである。

## 00:39 JST：C1T2収集・監査の引継ぎ準備

C1T2の生成registryと実sampling正常終端を待ち、既存collector・capacity監査・full監査へ順に進むdriverを追加した。
既存のLinux受入済みconfigを使い、新しい接続13件と元制御・環境・registryの回帰64件がWindowsで成功した。
local PID7312で起動し、生成registry待ちのsession継続を確認した。
新collectorや監査のqsubは未実施であり、科学的なcohort受理は宣言していない。
詳細は [仕様・実施結果](c1t2_collection_audit_handoff_spec_2026-10-21_ja.md)に保存した。
クラスタではC1T1 collector265370とC3T0 sample前半265372がRで、引き続き2要求ノードである。

## 00:46 JST：PC全回収後の独立indexへの接続

残り5条件のsource・assignmentと全batchを明示的に結ぶ接続用driverを追加した。
全5条件で元の113 sourceとの完全一致を確認し、追加10件と既存indexの回帰8件がWindowsで成功した。
C1T1のPID37216とC1T2のPID12872で全回収待ちを開始し、両sessionの継続を確認した。
本番index、shared parityの回収・再検証、転送、最終report結合は未実施である。
詳細は [全回収後indexの仕様・実施結果](planned_cohort_index_spec_2026-10-21_ja.md)に保存した。
C3用の同driverは準備済みだが、待機processは起動していない。
クラスタ2ジョブは引き続きRで、DGXはbatch21の処理へ進んでいる。

## 00:55 JST：残り5条件のshared入力・転送準備

PC保存parityと前条件の完了証跡を回収・再検証し、全件indexと合わせて最終転送contextを作るadapterを残り5条件へ対応させた。
旧sourceは維持し、明示conditionへの変更を導出記録へ保存した。
Windowsで元回帰を含む82件と、導出差分・実CLI確認5件が成功した。
本番shared回収・replay再検証・distribution作成・転送は未実施で、自動待機と最終qsubへの接続は残る。
詳細と17ファイルのsource・証跡は [仕様と受入結果](planned_condition_distribution_spec_2026-10-21_ja.md)に保存した。
DGX batch21の回収が完了し、C1T0 host側回収はDGX440群・Labo96群の計536/768群となった。
クラスタ265370・265372はRで、正式な低ノイズ完了は6/12条件を維持する。

## 01:05 JST：shared回収と全件転送の自動引継ぎ

各hostの初回検証を待ってshared入力を回収し、両hostの保存replayを検証した後、全件index完成を待ってクラスタへ転送するdriverを追加した。
実childの終了検査と二重実行拒否を含む15件のWindowsテストが成功した。
C1T1のPID46160とC1T2のPID44204で待機を開始し、両sessionの継続を確認した。
詳細とsource・受入証拠は [引継ぎ仕様と実施結果](planned_distribution_handoff_spec_2026-10-21_ja.md) に保存した。
本番shared回収・転送と、転送後の最終集計qsubへの接続は未実施である。
既存C1T0 final待機・C1T2生成待機もlive sessionを確認し、DGXはbatch22のlaunchへ進んでいる。
クラスタ265370・265372は実qstatでRを確認し、2要求ノードを維持する。
正式な低ノイズ完了数は6/12条件のままである。

## 01:13 JST：残り5条件の最終集計設定の準備処理

既存C1T0設定作成処理から条件と初回collector監査の接続を明示的に変更し、全5条件の最終設定preparerを追加した。
Windows43件とLinux43件が成功し、クラスタの元venvで全5条件の実監査config・source bootstrapを確認した。
テストではprepareと非投入preflightまでを確認したが、本番のfull入力照合・設定作成・qsub・最終report実行は未実施である。
source・受入・実配置の証跡は [最終設定準備の仕様と実施結果](planned_final_preparation_spec_2026-10-21_ja.md) に保存した。
全件転送とfull監査を待つ親driver、最終集計qsubと回収への自動接続が残る。
公開候補と稼働中の元sourceは変更していない。

## 01:19 JST：最終設定の準備待機を接続

全件転送・full監査・native reference受理を照合して、既存preparerを一度だけ呼ぶ親driverを追加した。
Windows19件が成功し、C1T1のPID17424とC1T2のPID44648で待機sessionの継続を確認した。
本番prepareは未起動であり、設定作成後のqsubとreport回収への自動接続は残る。
仕様・受入・開始記録は [最終準備への引継ぎ](planned_final_handoff_spec_2026-10-21_ja.md) に保存した。
DGX batch22の回収が完了してbatch23が稼働し、C1T0のhost側回収はDGX460群・Labo96群の計556/768群となった。
この回収数は最終科学的受理の完了数ではなく、正式な低ノイズ完了は6/12条件を維持する。

## 01:26 JST：C1T1・C1T2の最終投入・回収まで接続

受入済み最終設定の完成後に、preflight・空き枠待ち・qsub・実PBS終端確認・13成果物回収へ進むdriverを起動した。
追加と元回帰の計36件がWindowsで成功し、条件引数・1 thread環境・投入の曖昧性に関する停止条件を確認した。
C1T1のPID16360とC1T2のPID39644は最終設定の完成待ちであり、この接続によるqsubは未実施である。
両条件について前段から最終回収までの待機処理を接続したが、本番の全段成功を意味しない。
sourceと検証範囲は [最終実行の仕様と実施結果](planned_final_execution_spec_2026-10-21_ja.md) に保存した。
既存を含む18本の保持sessionをpollして全てliveを確認した。
実qstatではC1T1 collector265370とC3T0 sample前半265372がRであり、最大2要求ノードを維持する。
正式な低ノイズ完了数は6/12条件で、C3の後続sampling・収集・監査・PC処理への接続は残る。

## 01:32 JST：C3T0の未投入partitionへの引継ぎ

使用済みanchor265371とsample前半265372を固定して引き継ぎ、未投入sample後半だけを対象とするdriverを追加した。
C1T2の全generator投入とregistry完成を待ち、元wrapperのslot検査と共有lockを使って投入する順序とした。
追加20件と元registryの回帰26件がWindowsで成功した。
PID17484で待機sessionの継続を確認し、新しいqsubは未実施である。
仕様・受入・使用済みreceiptの記録は [C3T0生成の引継ぎ](c3t0_generation_handoff_spec_2026-10-21_ja.md) に保存した。
実qstatでは265370・265372の2ジョブがRで、C1T0の両PC driverもliveである。
C3T0のnative reference・collector・監査・PC処理、およびC3T1・C3T2の生成と後続接続は残る。
正式な低ノイズ完了数は6/12条件を維持する。

## 01:38 JST：C3T0の生成後とPC全件回収後の接続

C3T0のnative reference・PC handoffを起動する親と、collector・capacity/full監査のdriverを追加した。
元受入と導出確認の計41件がWindowsで成功した。
launcherのPID47520とaudit driverのPID12660で生成registry待ちを開始し、live sessionを確認した。
既存indexのPID46444とdistributionのPID41120もC3T0の全件回収待ちで起動した。
本番child・新規qsub・全件index・転送・最終reportの完了はまだない。
source・実設定照合・導出記録は [C3T0生成後の接続](c3t0_downstream_spec_2026-10-21_ja.md) に保存した。
C3T0の最終設定・最終qsub・回収への自動接続、およびC3T1・C3T2の生成と後続接続は残る。
DGX batch23の回収が完了し、C1T0のhost側回収はDGX480群・Labo96群の計576/768群となった。
クラスタ265370・265372はRで、正式な低ノイズ完了は6/12条件である。

## 01:46 JST：C3T0の最終集計・回収まで接続

C3T0の全件転送・full監査・native reference受理後に最終設定を準備し、qsubからreport回収まで進む待機処理を接続した。
準備側22件と実行側31件がWindowsで成功した。
PID8696とPID30128のlive sessionを確認し、両方とも前段の完了待ちである。
本番最終設定・新しいqsub・report回収は未実施で、接続完了を科学的な条件完了とは扱わない。
source・受入範囲・開始記録は [C3T0最終接続](c3t0_final_handoff_spec_2026-10-21_ja.md) に保存した。
DGXはbatch24のlaunchへ進み、クラスタ265370・265372は引き続きRである。
C3T1・C3T2の生成と後続接続が残り、正式な低ノイズ完了数は6/12条件を維持する。

## 02:10 JST：C3T1・C3T2も最終回収まで接続

C3T1・C3T2について、先行条件のfull監査とnative reference受理後の生成、生成後の収集監査・PC処理、全件indexと転送、最終設定、最終qsubと13成果物回収までの待機処理を接続した。
両条件とも追加受入は生成11件・生成後41件・最終準備22件・最終実行31件がWindowsで成功した。
C3T1については元生成driverの14件も回帰確認した。
元の科学計算sourceと既存稼働sourceは変更していない。
本番の前提条件が揃っていないため、この接続からの新しいqsub・PC child開始・最終report完了は未実施である。
実際の全段成功を意味せず、正式な低ノイズ完了は6/12条件のままである。
02:08の実session pollで、既存25本と今回14本の計39本すべての継続を確認した。
qstatでは265370と265372がRで、2要求ノードを維持する。
C1T0の受理済みtransfer記録と固定assignmentを照合し、DGX500群・Labo120群の計620/768群がhost側で回収済みと確認した。
export・stageの完了数は回収数に含めていない。
DGX batch25のPID2205965とLabo最終batch5のPID23744を02:08〜02:09に実観測し、いずれもliveかつterminal未取得であることを確認した。
残る主作業は本番の計算・収集・監査・最終集計の完遂と結果の科学的評価である。
接続の仕様と実施範囲は [C3T1生成](c3t1_generation_handoff_spec_2026-10-21_ja.md)・[生成後](c3t1_downstream_spec_2026-10-21_ja.md)・[最終回収](c3t1_final_handoff_spec_2026-10-21_ja.md)、および [C3T2生成](c3t2_generation_handoff_spec_2026-10-21_ja.md)・[生成後](c3t2_downstream_spec_2026-10-21_ja.md)・[最終回収](c3t2_final_handoff_spec_2026-10-21_ja.md) に記録した。

## 02:18 JST：tile288の独立計時に向けたmetadata reader

既存portable計時経路はC0T2専用であり、C1T0の復旧wrapperと残る5条件の初回collector用wrapperを受け付けないことをsourceから確認した。
新しい明示経路 `portable_condition` の親metadata readerを別配置で追加し、6条件・collector種別・固定wrapper・sampling manifest・portable context・監査config・最終PBS実測を照合する処理を実装した。
旧経路の26件を含む94件がWindowsとLinuxの両方で成功した。
これは小さいmetadata fixtureの受入であり、実final report、raw reader、全12条件の選択、独立計時の成功ではない。
新経路のfull readerとselectorへの接続、全12条件の実入力と資源準備は引き続き未完了である。
仕様・結果・保存証跡は [計時readerの拡張](low_timing_condition_reader_spec_2026-10-21_ja.md) に記録した。
DGX batch25は02:12:27に回収を終え、02:17の実session pollでbatch26のlaunchへ進んでいることを確認した。
正式な低ノイズ完了は6/12条件を維持する。

## 02:39 JST：計時readerの受入と実復旧authority接続

tile288の6条件に対応する計時用full reader、子process入口、selector親の接続を追加し、WindowsとLinuxで各167件が成功した。
最初のLinux検証は検証scriptの変数名誤記で停止したため、その記録と配置を保持して別配置で再検証した。
模擬row・authorityを含む受入と区別して、元クラスタvenv・C1T0の実復旧authorityとjoinへの接続を確認し、254 sourceの前後一致と元joinの56 sourceを照合した。
仕様、結果、保存manifestは [計時readerの拡張](low_timing_condition_reader_spec_2026-10-21_ja.md) にまとめた。
本番final config、各条件の全raw読取、全12条件の正式選択、独立計時はまだ未完了である。
受入manifestの189ファイルと実機接続manifestの6ファイルを再照合した。
02:38の実PC観測ではDGX batch27のPID2255626とLabo最終batch5のPID23744がliveで、terminalは未取得だった。
固定assignmentと回収済みreceiptを照合し、C1T0はDGX540群・Labo120群、計660/768群をhost側で回収済みと確認した。
export・stage完了は回収に含めず、正式な条件完了とも区別する。
このturnの実session pollで全39本の計算・引継ぎhandleの継続を確認し、qstatでは265370と265372がRで2要求ノードを維持している。
正式な低ノイズ完了は6/12条件であり、独立計時と最終評価は引き続き残る。

## 02:45 JST：tile288の計時用子process環境

復旧collector用と初回collector用の計時reader環境を別々に配置した。
いずれも元venvの実子processで100 source・137 native binaryを固定し、既存bootstrapが前後とも成功した。
C1T0では間に実復旧authorityとjoinを読み、残る5条件ではcollector完了を必要としない元CLIの設定bootstrapを行った。
残る5条件のsampling root・full監査root・collector config・bundle sourceの対応を確認した。
両環境のstderrは空で、保存manifestの12ファイル・13ファイルを再照合した。
環境JSON・実行script・stdout/stderr・受入範囲は [計時readerの拡張](low_timing_condition_reader_spec_2026-10-21_ja.md) に保存した。
親PBS、本番final config、全raw読取、全12条件の正式選択、独立計時はまだ未実施である。
02:44のqstatで265370と265372がR、C1T1収集監査とC1T0最終処理の実handleも継続中だった。
正式な低ノイズ完了は引き続き6/12条件である。

## 02:55 JST：最終回収から計時入力候補への待機処理

6条件の最終回収が完了した後、元snapshot validator・受理receipt・13成果物・準備済み環境・独立referenceの対応を照合してmetadata候補を作る処理を追加した。
Windows43件・4.26秒、Linux43件・0.69秒で受入が成功した。
模擬化した部分と本番で未実施の範囲は [計時readerの拡張](low_timing_condition_reader_spec_2026-10-21_ja.md) に記録した。
既存最終処理6本の実handleの継続を確認し、新しい待機処理をPID24708・session10693で開始した。
最初のrunpy形式の起動はimport前に停止したため、待機記録先が未作成であることを確認して通常script形式で起動した。
6条件とも最終回収待ちであり、本番候補作成や追加qsubはまだ行っていない。
DGXはbatch27を回収し、batch28の準備へ進んだ。
固定assignmentと回収済みreceiptを照合し、C1T0はDGX560群・Labo120群、計680/768群をhost側で回収済みと確認した。
Labo最終batch5の実PID23744は02:55にliveでterminal未取得だった。
クラスタ265370・265372はRで2要求ノードを維持し、正式な低ノイズ完了は6/12条件である。

## 03:04 JST：親binding修正とC1T1 collector正常終了

親wrapperの準備時検査で新経路の親script・資源・子出力directoryの照合が漏れていたため、別版で追加した。
修正前の拒否漏れ3件を確認し、修正後はWindows・Linuxで各41件が成功した。
既存の稼働sourceと回収待機処理は変更していない。
専用配置の実クラスタprocessで親source93個・native binary137個・selector source53個のbootstrapとsource closureを照合した。
受入と実機確認の範囲は [計時readerの拡張](low_timing_condition_reader_spec_2026-10-21_ja.md) に記録した。

C1T1 collector265370は03:01:53にF・Exit_status=0・run_count=1で終了した。
実walltimeは2時間48分32秒、最大使用メモリは358876 KBだった。
元driverがcollector完了を受理し、terminal SHA-256 `4448bd5f3cd83a0308e679a700b2ce5f8aad49d552659d1211cf7b55f6251b3d` を保存した。
これは収集の成功であり、full trace監査や科学的な条件完了ではない。
03:04時点でcapacity planとpreflightが成功し、既存driverがcapacityのsubmit処理へ進んでいる。
その時点のqstatでは265372のみがRで、追加の投入結果はまだ未確認である。
正式な低ノイズ完了は引き続き6/12条件であり、全12条件の親入力・資源決定と独立計時も残る。

## 03:05 JST：C1T1 capacity監査をqsubで投入

既存driverがcapacity監査265373をqsubで投入し、03:05の実qstatではQだった。
265372がR、265373がQで、待機中を含めて2要求ノードである。
capacityの要求は既存の初回上限で96 CPU・340 GB・24時間、実worker数は8であり、上限時間を実測や終了予測とは扱わない。
capacity manifestのSHA-256は `c7bead9204d8c111894dcf417c0fc8d28778e2f78520c18963b4fbb9bb2e17b9` である。
実測後に続くfull監査の完了はまだない。
これと独立に、C1T1の実初回collector authorityを新計時readerから構成し、元joinの201 sourceと前後の子bootstrapを確認した。
この接続確認では追加qsubやraw読取を行っていない。
正式な低ノイズ完了は6/12条件のままである。

## 03:18 JST：既存stagedとの互換性と全12条件の組立

既存C2T0・C2T1・C2T2はstage2専用venvと元の数値比較module配置を前提にするため、親環境v1の単体bootstrap成功だけでは不十分と判断した。
v1を保持したまま既存staged親環境を基準とするv2を別配置し、元runtime、93 source、137 native binary、selectorの53 sourceを確認した。
実metadataで3条件の保存planと数値比較sourceの契約が一致し、以後の親入力はv2を基準にする。
全12候補の組立と資源計算はWindows・Linuxで各16件が成功し、実inventoryは6/12準備済みとして部分集合を後段へ返さないことを確認した。
実parent入力の保存・全metadata検査・正式qsubへの接続は未完了である。
詳細と受入範囲は [計時readerの拡張](low_timing_condition_reader_spec_2026-10-21_ja.md) に記録した。

LaboのC1T0担当は全144群を回収して正常終了し、旧session23921の終了コード0を確認した。
固定assignmentと回収済みreceiptの照合では、DGX580群・Labo144群、計724/768群をhost側で回収済みである。
DGXはbatch29のlaunchへ進み、残るC1T0の44群はDGX担当である。
C1T1のLabo引継ぎsession55397が次のserial driverを開始し、03:18時点で最初のexportを開始している。
PC計算本体の開始はこの時点ではまだ確認していない。
クラスタ265372はR、265373はQで、265373の待機理由はCPU資源不足だった。
待機を含めて2要求ノードを維持し、正式な低ノイズ検証完了は6/12条件のままである。

## 03:33 JST：全12条件の親準備と設定選択の後続処理

全12候補から親input・acceptance・resource_decisionを保存し、元wrapperのprepareとread_planへ渡す処理を追加した。
Windows10件・1.22秒、Linux10件・0.08秒で接続テストが成功した。
Linuxでは実wrapperのprepared_valueを使い、9条件のisolated readerが実際の親script・資源・子directoryに結び付くことを確認した。
実inventoryは6/12のため正式入力を作らず、準備待機処理をsession51497で開始した。
受入manifestの16ファイルを再照合し、範囲を [親入力準備仕様](low_timing_parent_preparation_spec_2026-10-21_ja.md) に記録した。

親準備後に最大2ノードの空きを待ち、既存wrapperからqsubを1回だけ実行し、同じjob IDの終了観察とseal・回収へ進む後続処理を追加した。
Windows21件・0.61秒、Linux21件・0.05秒で接続テストが成功した。
投入応答不明時の再投入禁止と、観察時の通信障害を終了と扱わない経路も確認した。
実クラスタのread-only観察では要求ノード2、共有lockなし、既存coordinatorなしだった。
後続driverはsession67915で親入力の完了を待ち、追加qsubはまだ実行していない。
受入manifestの11ファイルを再照合し、範囲を [設定選択の実行仕様](low_timing_selection_execution_spec_2026-10-21_ja.md) に記録した。
本番12条件へのprepare、設定選択の実投入・実行・回収、独立計時は未実施である。

DGXはbatch29を回収し、batch30のexportへ進んだ。
固定assignmentと転送receiptの照合で、C1T0はDGX600群・Labo144群の計744/768群をhost側で回収済みだった。
観察は `data_tile_validation_2026-10-17/c1t0_host_collection_observation_20261021_0332.json` に保存した。
LaboのC1T1一致確認は実PID13584が稼働し、照会時点のCPU使用時間は717.34秒だった。
この一致確認の完了や、次の本計算batch開始はまだ確認していない。
03:31のqstatでは265372がR、265373がQで、正式な低ノイズ検証完了は6/12条件のままである。

## 03:42 JST：独立計時seed監査への準備とLabo本計算開始

独立計時前の新旧seed全数監査に向け、旧job265253の固定記録を現在の親環境v2で読み直した。
旧56区分・3,963,562割当の保存結果と現在のcatalog metadataが一致し、12 producerの一対一のpath対応と同じbytesを確認した。
bridgeの依存source61個とcore28個を固定親環境に照合し、親bootstrapを前後に通した。
新しいseed streamの生成や本番監査は行っていない。
基礎入力と実行ログは [seed監査への接続仕様](low_timing_census_connection_spec_2026-10-21_ja.md) の参照先へ保存した。

設定選択のseal済みdescriptorから元make_plans・validate_plansを通し、既存census bridgeのprepareへ渡す処理を追加した。
接続テストはWindows9件・0.80秒、Linux9件・0.10秒で成功し、選択0件のno-opも保持する。
科学的な境界をmock化した受入であり、本番科学bundleやpilotの完了ではない。
設定選択の完了を待つ準備driverをsession11507で開始し、実handleの継続を確認した。
本番census投入・回収の接続と独立計時の実行は引き続き残る。

LaboのC1T1一致確認は990.43秒で正常終了し、受理recordのSHA-256は `dbb39fba5f486a1645fb2ff4fa011cc2cd9a1015e07ce7ec141d2d2baa871004` だった。
元driverがC1T1のbatch0本計算を24 workerで開始した。
実機でexecution-intentのPID12132・workers24・未完了を読み、OSへの照会でPID12132の稼働と子Python process24個を確認した。
DGXはC1T0のbatch30を開始している。
後続処理を含む42セッションの実handleを照会し、全て継続中だった。
03:40のqstatは265372がR、265373がQで、要求ノード数2を維持している。
正式な低ノイズ検証完了は引き続き6/12条件である。

## 03:48 JST：seed全数監査の投入・回収を接続

census準備の完了後、共有lockと最大2ノードの空きを待って既存bridgeからqsubし、同じjob IDの終了を確認してseal・回収するdriverを追加した。
独立計時用seedの割当、既存census、資源計算式は変更していない。
no-opでは元read_planを再検査し、全数監査を実行したというdescriptorを作らず終了状態を保存する。
Windows16件・0.75秒、Linux16件・0.06秒で接続テストが成功した。
受入はschedulerと科学的な境界をmock化したもので、本番seed監査の実行証拠ではない。
詳細と保存source・ログは [seed監査への接続仕様](low_timing_census_connection_spec_2026-10-21_ja.md) に追記した。
待機driverはsession74370で開始し、実handleの継続を確認した。
独立計時capacity・mainの投入連携と最終集計はまだ残っている。

03:48のqstatでは265372がR、265373がQで、待機中を含む要求ノード数は2である。
DGXのC1T0 batch30とLaboのC1T1本計算driverも実handleの継続を確認した。
正式な低ノイズ検証完了は6/12条件であり、今回追加したdriverからのqsubは未実施である。

## 03:54 JST：独立計時の入力・capacity準備とC1T0最終batch

正式seed監査後に既存execution.inputsで科学入力を受理し、独立MC・BARのcapacity manifestを準備する処理を接続した。
24通りの精度目標と両手法の48行を保持し、対象行だけに元の2 full estimatorを割り当てる。
benchmarkの192 replicate、seed区分、選択設定、MC予算、capacity資源は変更していない。
no-opでは元の科学bundle・registry・selectionへの対応を照合し、独立計時未実施として全48行を保存する。
Windows18件・0.76秒、Linux18件・0.08秒で接続テストが成功した。
科学的な境界はmock化した受入であり、本番capacity manifestの作成や計時成功ではない。
保存source・実行ログと範囲は [独立計時の準備仕様](low_independent_timing_preparation_spec_2026-10-21_ja.md) に記録した。
driverはsession72330で正式seed監査の完了を待っている。
capacity・mainの本番投入、実測後の分割、最終集計への接続は引き続き残る。

DGXはC1T0のbatch30を回収し、残るbatch31の実行へ進んだ。
固定assignmentと転送receiptの照合で、DGX620群・Labo144群、計764/768群をhost側で回収済みと確認した。
観察記録は `data_tile_validation_2026-10-17/c1t0_host_collection_observation_20261021_0354.json` に保存した。
LaboのC1T1本計算も元handleの継続を確認した。
host側の回収は最終数値検証の完了ではなく、正式な低ノイズ検証完了は6/12条件のままである。

## 04:01 JST：C1T0全768群の回収とcapacity後処理

DGXのC1T0最終batch31が正常終了し、元session39752の終了コード0を確認した。
固定assignmentと全転送receiptを照合し、DGX624群・Labo144群、合計768/768群をhost側で回収済みと確認した。
観察記録は `data_tile_validation_2026-10-17/c1t0_host_collection_observation_20261021_0401.json` に保存した。
既存の全件回収driverは索引作成へ進み、最終集計・検証はまだ完了していない。
DGXの次条件C1T1への引継ぎsession54293がserial driverを開始し、export完了後のprepositionへ進んだ。
C1T1のDGX本計算開始はこの時点ではまだ確認していない。
LaboのC1T1本計算は継続中である。

独立計時capacityの正常終了metadataを既存accepted_capacityで受理し、元resource_planから本計算の分割を準備するhelperを追加した。
非ゼロ終端や資源計画不能ではmainを作らず、192 replicateを未実行として保持する。
Windows12件・0.78秒、Linux12件・0.11秒で接続テストが成功した。
既存runnerの科学的な境界はmock化した受入であり、本番capacityの受理や本計算の準備ではない。
詳細は [capacity実測後の準備仕様](low_independent_capacity_result_spec_2026-10-21_ja.md) に保存した。
このhelperの投入監視driverへの接続は次の作業であり、独立計時本番は未実施である。

04:00のqstatでは265372がR、265373がQで、要求ノード数2を維持している。
正式な低ノイズ検証完了は6/12条件のままである。

## 04:15 JST：独立計時capacity・mainの投入監視を接続

準備済みの全48行を保持し、既存submitterからcapacityをqsubして、実測後のmain partitionへ進むdriverを追加した。
待機中を含む最大2ノード制約と共有lockを維持し、同じjob IDを再観察する。
投入応答不明時は自動再投入せず、非ゼロ終端・計時不能を成功測定へ置き換えない。
Windows20件・0.84秒、Linux20件・0.09秒で接続テストが成功した。
科学的な読み取り・PBS境界をmock化した受入であり、本番計時の検証完了ではない。
保存source・ログと適用範囲は [独立計時の投入・監視仕様](low_independent_timing_execution_spec_2026-10-21_ja.md) に記録した。
待機driverをsession39834で開始し、正式な独立計時入力の準備完了を待っている。
本番計時の実行と最終集計への接続は残る。

## 独立計時の最終集計入力と実参照データの接続

全48行の終端記録から、元reportが受け取る24 identity・各MC/BARのcapacityとmain partitionを組み立てる処理を追加した。
失敗・未選択を除外せず、孤立したmain・異なるjob結果・欠落した192 replicate分割を拒否する。
実WSS生成側の投入記録名が `submission_intent.json` であるのに元reportが `submission-intent.json` を要求する不具合を実機で確認し、別版で修正した。
元report・既存親環境は変更していない。
元report受入、全条件引継ぎ、intent名の回帰を合わせ、Windows78件・18.53秒、Linux78件・11.38秒で成功した。
固定済みWSS監査の実artifactへ修正版を接続し、全16監査結果と評価対象12条件の参照区間を確認した。
これはmetadataの接続確認であり、正式な設定選択や元chunk全数の再検証、最終計時評価ではない。
保存source・環境・証拠は [最終集計への接続仕様](low_independent_timing_report_connection_spec_2026-10-21_ja.md) にまとめた。
最終config準備・reportのqsub・回収への接続は残る。

後続処理を含む44セッションの実handleを照会し、全て継続中だった。
DGXのC1T1 batch0は一致確認と配置を終えて20 workerで本計算へ進み、実機のexecution-intentに対応するPID2328545の稼働を確認した。
観察記録は `data_tile_validation_2026-10-17/c1t1_dgx_process_observation_20261021_0423.json` に保存した。
LaboのC1T1 driverも継続中で、クラスタは265372がR、265373がQの要求2ノードを維持している。
正式な低ノイズ検証完了は引き続き6/12条件で、C1T0の768群は回収後の索引作成・最終集計を進めている。

## 04:40 JST：最終集計の準備・qsub・回収まで接続

最終集計では、計時時のPYTHONPATHを保ち、修正版reportだけを固定directoryから明示的に読み込む環境へ接続した。
実Linuxで元bootstrapとexecution.current_runtimeを通し、Windows・Linuxの各8件の受入も成功した。
本番計時manifestは未作成であり、その読取り完了を主張するものではない。

全計時終端state・正式selector・census・固定WSS参照から元report.prepareへ渡すdriverを追加した。
Windows10件・1.06秒、Linux10件・0.07秒で接続テストが成功し、session41156で全独立計時の終端を待っている。
続くreport jobは、qsubの1回制限、共有lock、待機込み最大2ノード、PBSの実資源とhost、終端と報告bytesの照合を実装した。
Windows16件・2.11秒、Linux16件・0.50秒で接続テストが成功した。
逐次readerに1 CPU・32 GB・24時間の上限を設定しており、これは完了時間の実測予測ではない。
投入・終端監視・回収driverをsession43539で起動し、最終report準備完了を待っている。
session41156・43539と独立計時driver39834の実handleの継続を確認した。

これで最終集計までの待機処理を接続したが、本番の全独立計時、report.prepare、報告jobのqsub、JSON・日本語報告の回収は未完了である。
科学計算をmock化した受入と実データでの検証を区別し、証拠・環境・再現sourceは [最終集計への接続仕様](low_independent_timing_report_connection_spec_2026-10-21_ja.md) に追記した。
受入manifestの再照合とgit diff --checkは成功した。

04:39のqstatでは265372がR、265373がQの要求2ノードだった。
DGX・LaboのC1T1 driver、C1T0全件回収、C1T1監査driverも継続中である。
04:40に全12条件のinventoryを読み直し、tile72の6条件がmetadata候補、tile288の6条件が準備待ちであることを確認した。
正式な低ノイズ検証完了は6/12条件のままである。

## 計算中processとC1T1の進行確認

04:45 JSTに後続待機処理を含む46セッションの実handleを照会し、全て継続中であることを確認した。
C1T0の全件indexは実PID20728でCPU時間と読取量が増えており、親processが待機していることを計算停止とは扱わない。
連続観察ではCPU時間が80.27秒、読取量が856,820,932 bytes増えた。
観察記録は `data_tile_validation_2026-10-17/c1t0_index_progress_check_20261021_v1.json` に保存した。
この観察は検査中processの進行確認であり、indexや最終科学検証の完了ではない。

DGXのC1T1 batch0は正常終了し、元transfer receiptで20群の回収成功を確認した。
元serial driverはbatch1へ進み、設定hashが一致するexecution-intentのPID2373045が20 workerで稼働していることを実機で確認した。
観察と入力hashは `data_tile_validation_2026-10-17/c1t1_dgx_progress_observation_20261021_v1.json` に保存した。
batch0回収とbatch1実行を条件全体の完了とは扱わず、正式な低ノイズ検証完了は6/12条件を維持する。

## 05:04 JST：実行中partitionの進捗と終了見込み

job265372の実行状態Rと同じ投入script・execution-intentを確認し、最初のsampling partitionの保存済み完了マーカーは24,800/30,720件（80.7%）だった。
前回観察から425.74秒で659件増え、直近速度を一定と仮定した残り時間は約64分となる。
単純外挿は06:08 JSTごろだが、終盤の処理時間の偏り・summary作成・後続検証を含まないため、目安は06〜07時とする。
これは現在のpartitionだけの見込みであり、後続partition、残り条件、独立計時、最終報告を含む全体の終了予測ではない。
完了マーカー数を科学的な検証成功数とは扱わない。
観察値・元観察のhash・外挿の前提は `data_tile_validation_2026-10-17/c3t0_sampling_progress_observation_20261021_v2.json` に保存した。
05:03 JSTの実handle照会では、後続待機処理を含む46セッション全てが継続中で、新たな標準出力はなかった。

## 05:10 JST：DGXのC1T1で40群を回収

DGXのC1T1 batch1は正常終了し、batch0と合わせて40群の転送検証済み回収を確認した。
batch2は20 workerで進行し、設定hashとexecution-intentに一致する実PID2381813の稼働を確認した。
観察と回収証拠のhashは `data_tile_validation_2026-10-17/c1t1_dgx_progress_observation_20261021_v2.json` に保存した。
元serial driverが次batchへ進んだため、終了済みbatch1を再実行していない。
これらは条件内の部分回収であり、正式な低ノイズ検証完了数は6/12条件のままである。

## 05:21 JST：C1T0の全件索引と入力準備が完了

C1T0の768群・67,584行について全件索引を作成し、予定行と観察行が一致し、未回収行・インフラ失敗群・context失敗群はいずれも0だった。
区間未取得は0行だが、診断フラグは67,584行、診断未定義は31,028行であり、これらを分母から除外しない。
索引は暫定集計で、最終科学検証・数値推定の再計算・raw trace状態の再decodeの完了を意味しない。
証拠は `data_tile_validation_2026-10-17/portable_condition_c1t0_snapshot_v5.json` で、SHA256は `dde55bfa2c60b27e2f451f52e1aec7d900081a0bfe2c6600d2defea7340cc660` である。
元driverのindex・prepareの正常終了を確認し、05:21 JSTから固定transfer planに従うクラスタへの入力転送へ進んだ。
転送完了・最終検証jobの投入はまだ確認しておらず、正式な低ノイズ検証完了数は6/12条件を維持する。

05:31 JSTにjob265372を再観察し、保存済み完了マーカーは27,361/30,720件（89.1%）だった。
前回から1,642.93秒で2,561件増え、直近速度を一定と仮定した残りは約36分、単純外挿は06:08 JSTごろで、先の06〜07時という目安を維持する。
現在のpartitionだけの推定であり、後続検証を含む完了時刻や科学的な成功数を示さない。
観察値と前提は `data_tile_validation_2026-10-17/c3t0_sampling_progress_observation_20261021_v3.json` に保存した。

## 05:35 JST：C1T1のDGX回収60群、Laboの最初のbatch終了

DGXのC1T1はbatch0〜2の計60群で転送検証済み回収を確認した。
batch3は設定hashが一致する実PID2426374で20 workerが稼働している。
Laboのbatch0は元launchの正常終了記録を確認し、既存serial driverが回収処理へ進んだが、転送検証の完了はまだ確認していない。
観察と元証拠のhashは `data_tile_validation_2026-10-17/c1t1_pc_progress_observation_20261021_v3.json` に保存した。
条件全体の最終検証を終えたものではなく、正式な低ノイズ検証完了数は6/12条件のままである。

## 05:53 JST：C1T1の回収が104群へ進行

転送検証済みの回収はDGX80群・Labo24群の計104群となった。
DGXはbatch4の実PID2435115で20 worker、Laboはbatch1のexecution-intentに対応する実PID30536で24 workerが稼働している。
両機ともconfigのhashが固定値と一致することを確認した。
観察・対象batch・元回収証拠のhashは `data_tile_validation_2026-10-17/c1t1_pc_progress_observation_20261021_v4.json` に保存した。
完了したbatchを再実行せず、既存serial driverの後続処理を継続している。
条件内の部分回収なので、正式な低ノイズ検証完了数は6/12条件を維持する。

## 06:03 JST：C1T0の入力転送が正常終了

全170ファイル・3,968,906,245 bytesの入力転送が正常終了し、session17439のexit code 0を確認した。
転送receiptのhash、全入力hash、ファイル数、総bytes、context hashが固定transfer planと完了記録に一致した。
receiptは `data_tile_validation_2026-10-17/portable_condition_c1t0_distribution_transfer_v1/receipt.json` で、SHA256は `5d077ee5f519b36701cdb6d667e0043bcbb03eaab560cd7725fd1112f3381364` である。
既存のsession31431が回収完了とfull audit完了を受け取り、最終検証のprepareを開始した。
転送とprepare開始を最終科学検証の完了とは扱わず、正式な低ノイズ検証完了数は6/12条件を維持する。
この転送処理によるqsubは行っておらず、最終検証jobの投入・終了は別途確認する。

06:05 JSTにC1T0のprepareがacceptedとなり、135 source・204 metadataとfull audit job265369への接続を確認した。
最終configのSHA256は `6b4c325f69cacdbb52f8d684784105ad6f24e8da9f615f2a8923d3738157b94a`、report.shのSHA256は `0d5e52f9e478ffe7fef01f971aa3a6efecc3d2230b229248f3edb2b60adb461b` である。
32 GB・12時間はjobの資源上限であり、完了時間の実測予測ではない。
session31431は `c1t0_final_execution_resume_v1` の投入前処理へ進み、qsub未実施の状態から、待機込み最大2ノードの確認を続ける。

## 06:09 JST：C3T0の最初のpartitionで全タスクの保存マーカーを確認

job265372の最初のsampling partitionで、予定30,720件すべての保存済み完了マーカーを確認した。
次partitionのexecution-intentはまだ存在せず、この件数を次partitionとの合算として扱っていない。
qstatの状態はRのままで、最終記録の保存と正常終了を待っている。
保存マーカーの全件確認を科学的な検証成功や条件全体の完了とは扱わない。
観察値は `data_tile_validation_2026-10-17/c3t0_sampling_progress_observation_20261021_v4.json` に保存した。

## 06:15 JST：C1T1のtrace監査capacityが実行開始

待機していたjob265373は06:15:27 JSTにnode009で実行を開始し、qstatの状態Rとrun_count 1を確認した。
投入先は `partitioned-trace-capacity-1-1-budget4h-v1/trace-audit.sh` で、要求は1ノード・96 CPU・340 GB・24時間である。
これはtrace監査のcapacity測定の開始であり、全trace監査や独立計時の完了ではない。
job265372もRのため、クラスタは2ノード実行中で上限を維持する。
観察は `data_tile_validation_2026-10-17/c1t1_audit_capacity_running_observation_20261021_v1.json` に保存した。

## 06:18 JST：C1T1のcapacity終了、C1T0の最終検証をqsub

C1T1のtrace監査capacity job265373は06:17:22 JSTにexit status 0で終了し、実測walltimeは1分55秒だった。
これは全trace監査ではなく、後続の資源計画へ渡すcapacity測定である。
C1T0の既存driverが固定report.shをqsubし、job265383が06:18:54 JSTにnode009で実行を開始した。
実際のSubmit_argumentsとscript hashが保存済み投入記録に一致し、run_count 1、要求1ノード・1 CPU・32 GB・12時間を確認した。
job265372と265383の2ノード実行を維持し、3ノード目は要求していない。
終了・開始履歴と投入記録のhashは `data_tile_validation_2026-10-17/c1t0_final_and_c1t1_capacity_observation_20261021_v1.json` に保存した。
C1T0の最終結果の回収・検証はこれからで、正式な低ノイズ検証完了数は6/12条件のままである。

## 06:31 JST：明示assignmentの独立算術readerを追加

`output/planned_condition_arithmetic_review_v1/` に、C1T0以降の明示assignmentと固定transfer planを読む独立算術readerを追加した。
仕様と受入テストを先に作成し、未実装による失敗を記録してから実装した。
既存の算術helperと設定列挙helperはbyteを変えずに再利用し、実行中のsourceは変更していない。
Windows Python 3.11の20テストが4.05秒で成功した。
合成データの全768群・67,584行・352設定・192 seedを通し、区間未取得と診断未定義の行を分母に保持すること、欠落・重複・異なる条件・改変archive・既存出力への上書きを拒否することを確認した。
これはreaderの受入であり、実データの算術レビューは最終report回収後に実施する。
source・仕様・ログ・環境を `data_tile_validation_2026-10-17/planned_condition_arithmetic_review_acceptance_v1/` に保存した。
`accepted.json` のSHA256は `b3b94abad13cfdfacafc34c5c9afbd2ffb6eba9eb1c8cc192f558d5ee5f25050` である。

C1T1の転送検証済み回収はDGX100群・Labo24群の計124群に進んだ。
回収receiptの照合とhashは `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v5.json` に保存した。
45件の既存driver sessionが引き続きliveであることをpollで確認し、重複起動は行っていない。
qstatでjob265372と265383の実行中を確認し、クラスタは最大2ノードを維持している。
C1T0最終reportは未回収のため、正式な低ノイズ検証完了数は6/12条件を維持する。

06:34 JSTにDGXのbatch5（PID2479821、20 worker）とLaboのbatch1（PID30536、24 child worker）の実プロセスを確認した。
両PCの設定ファイルは固定launchのhashと一致し、Laboのexecution-intentにある `execution_config_sha256` も一致した。
観察v6では存在しない `config_sha256` を照合したためLaboのintent一致欄がfalseになったが、正しい項目による再観察と訂正理由を `c1t1_labo_process_observation_20261021_v7.json` に保存した。
この監視上の訂正に伴う計算の再起動や設定変更は行っていない。
クラスタのjob265372と265383はRでCPU累積時間が増加しており、C1T0最終reportはまだ存在しない。
クラスタ観察は `data_tile_validation_2026-10-17/cluster_running_observation_20261021_0634_v1.json`、PC観察は同階層の `c1t1_pc_process_observation_20261021_v6.json` と上記v7に保存した。

## 06:40 JST：残計算の見積もりを明確化

未開始sampling 7区画とanchor 3区画について、元capacity計画の予測値は合計69.47ノード時間だった。
常時2ノード・依存関係なしの単純除算でも34.74時間となるが、実測下限や全体ETAではない。
実行中partitionの残処理、監査、PCのBAR解析、回収・最終検証、独立計時はこの計算に含まない。
数値検証全体を本日中に完了する前提にはせず、公開後も10月22日以降へ継続する計画として扱う。
証拠・集計式・除外工程は `remaining_work_estimate_2026-10-21_ja.md` と対応する観察JSONに保存した。

## 06:46 JST：独立算術レビューの回収後実行を接続

残る6条件を正常回収後に一度だけ独立算術レビューへ渡す別driverを追加した。
既存の計算・回収・metadata候補・独立計時driverは変更していない。
小仕様と未実装時の受入失敗を先に記録し、実装後は22テストが1.23秒で成功した。
成功childの結果もcondition・report hash・出力manifestと照合し、不整合や失敗を再実行で上書きしない。
元snapshot検証と実算術処理はこの接続受入では模擬化し、本番回収後に実行する。
実sourceのpinを確認し、PID27868・session76495で起動して6条件ともpendingであることを確認した。
仕様と受入証拠は `planned_arithmetic_handoff_spec_2026-10-21_ja.md` に記録した。
job265372と265383は引き続きRで、新規qsubは行っていない。
正式な低ノイズ検証完了数は6/12条件を維持する。

06:51 JSTにC1T1の転送検証済み回収がDGX120群・Labo24群の計144/768群へ進んだ。
前回の124群から20群増加し、回収receiptのhashとarchive hashの対応を保存した。
証拠は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v8.json` にある。
クラスタの2ジョブ、PC側driver、最終回収と独立算術レビューのdriverは引き続きliveである。
C1T0の最終reportは未回収であり、部分回収の増加を条件全体の検証完了として扱わない。

07:01 JSTに空き容量を確認し、local Aは203.1 GB、DGXは262.6 GB、Labo Dは7.92 TB、クラスタの共有homeは13.63 TBだった（10進表記）。
観察は `data_tile_validation_2026-10-17/storage_observation_20261021_0701_v1.json` に保存した。
この確認に伴うデータ削除・移動・計算設定変更は行っていない。

07:10 JSTにC1T1の転送検証済み回収がDGX140群・Labo24群の計164/768群へ進んだ。
DGXはbatch7の実PID2497841で20 worker、Laboはbatch1の実PID30536で24 child workerの継続を確認した。
両PCのconfig hashは固定launchと一致し、Laboのexecution-intentも一致した。
観察と回収receiptのhashは `data_tile_validation_2026-10-17/c1t1_pc_process_collection_observation_20261021_v9.json` に保存した。
条件内の部分回収のため、正式な低ノイズ検証完了数は6/12条件を維持する。

## 07:25 JST：C3T0のsampling partition 0が正常終了

job265372は07:24:17 JSTにexit status 0で終了し、run_countは1、実測walltimeは6時間58分14秒だった。
保存されたsummaryはcomplete=true、completion_class=success、観測30,720/予定30,720 task、failed=0、missing_tasks=0、errorsなしだった。
summaryのSHA256は `617415f8cc5e86dafaa77492182a71a170d86a55df413a060093806e35e7c1df` である。
PBS終端とsummaryの観察は `data_tile_validation_2026-10-17/c3t0_sampling_partition0_terminal_observation_20261021_v1.json` に保存した。
これは最初のsampling区画の終了であり、残り区画・監査・BAR解析・条件全体の校正は完了していない。
既存C3T0 driverはC1T2を先行させる固定の順序を持ち、次の区画はその順序に従って投入する。
job265383のC1T0最終検証は引き続きRである。

C1T1の既存driverは07:24:28 JSTにfull-submitの一度だけの実行intentを保存し、全trace監査の投入処理へ進んだ。
07:27 JST時点では新しいqsubのjob IDはまだ確認できず、投入完了とは扱わない。
session77652の実handleは継続しており、再投入や別経路からの追加投入は行っていない。

## 07:29 JST：C1T1の全trace監査をqsubし実行開始

既存driverのfull-submitが完了し、job265387は07:28:36 JSTにnode010で実行を開始した。
実際のSubmit_argumentsが固定した `trace-audit.sh` に一致し、script SHA256、run_count 1、状態Rを確認した。
scriptのSHA256は `e581d8fb9a42f954acf4d9c9684bb2f09a047815c8f5157b85107cf89f427912` である。
要求資源は1ノード・96 CPU・67 GB・3時間で、3時間は完了見込みではなく上限である。
投入完了記録のSHA256は `504ba44e3789f78246393ddadc9a87b2d0a4208edff884885cb0615d2a9aa5df` である。
PBS状態、元scriptと投入記録の照合、capacityに基づく資源計画は `data_tile_validation_2026-10-17/c1t1_full_audit_running_observation_20261021_v1.json` に保存した。
C1T0の最終検証job265383と合わせて2ノード実行を維持する。
全trace監査の開始を条件全体の校正完了とは扱わず、正式な低ノイズ検証完了数は6/12条件を維持する。

07:33 JSTにC1T1の全trace監査で768群分の保存マーカーを確認した。
job265387はRで、summary.jsonとterminal.jsonはまだ存在せず、保存マーカーの件数を監査全体の正常終了として扱わない。
観察は `data_tile_validation_2026-10-17/c1t1_full_audit_progress_observation_20261021_v1.json` に保存した。

## 07:36〜07:37 JST：C1T1監査の正常終了とC1T2 anchorの投入

C1T1監査job265387は07:35:17 JSTにexit status 0で終了し、実測walltimeは6分39秒、run_countは1だった。
summaryは768群・79,872予定task、failed_audit_groups=0、failed_sampling=0、context_errorなし、input_changesなし、native_platform_verified=trueを記録した。
summaryのSHA256は `5e92a6ecb60141d6a7f4bbb02b4cd9d509eba5de71ca231c98b2dd707503f76c` である。
全compact entryを確認し、保存されたinitial/checkpoint状態を再復号する既定の監査で、全物理状態や全RNG軌道を再実行したものではない。
同じdecoder実装を使うため、decoderの独立な正しさ・混合・精度・被覆の保証とは扱わない。
PBS終端と監査範囲は `data_tile_validation_2026-10-17/c1t1_full_audit_terminal_observation_20261021_v1.json` と `c1t1_full_audit_summary_observation_20261021_v2.json` に保存した。
session77652はfull_audit_accepted=true、scientific_cohort_accepted=falseを返し、exit code 0で終了した。

既存C1T2 driverは優先監査の完了を受け、anchor partition 0をqsubした。
job265388は07:37:07 JSTにnode010で開始し、実Submit_arguments、script hash、submission ledger、run_count 1を照合した。
要求は1ノード・96 CPU・32 GB・2時間で、2時間は資源上限である。
証拠は `data_tile_validation_2026-10-17/c1t2_anchor_running_observation_20261021_v1.json` に保存した。
C1T0の最終検証job265383と合わせて最大2ノードを維持する。

PC側のC1T1回収はDGX160群・Labo24群の計184/768群に増えた。
転送検証receiptの対応は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v10.json` に保存した。
BAR解析と最終校正は未完了のため、正式な低ノイズ検証完了数は6/12条件を維持する。

## 07:42 JST：C1T2 anchor終了とsamplingへの引継ぎ

C1T2 anchor job265388は07:38:45 JSTにexit status 0で終了し、実測walltimeは1分38秒だった。
summaryは192/192 task、192 records、failed=0、missing_tasks=0、errorsなし、complete=trueを記録した。
summaryのSHA256は `99b0f2d9ffc9ccd7f4409b2f09c9bce8aa774f806bd6c0eb077abc62f6394cf1` である。
既存driverはsampling partition 0をqsubし、job265389は07:39:48 JSTにnode010で開始した。
実Submit_arguments、投入記録のqsub commandとjob ID、script SHA256、run_count 1の一致を確認した。
scriptのSHA256は `c0e5dbaf263a47750a6c74bf3a13094943544c00bd2360810a20698b79183472` である。
要求walltime 13時間は上限であり、終了見込みではない。
C1T0最終検証job265383もRで、CPU時間の増加を確認した。
観察と照合結果は `data_tile_validation_2026-10-17/c1t2_anchor_terminal_sample_running_observation_20261021_compact_v1.json` に保存した。
元観察にはanchor recordsが含まれるため、compact版は元観察のSHA256を保持し、recordsを件数へ置き換えている。
監視対象45個の既存sessionは実handleのpollで継続を確認し、終了済みのC1T1監査sessionは対象に含めていない。
保存行の独立再集計handoffも継続しているが、6条件とも最終report回収待ちで、本番再集計は未実施である。
anchorの終了は条件全体の校正完了ではなく、正式完了数は6/12条件を維持する。

## 07:44 JST：PC側のC1T1回収が208群へ進行

C1T1は転送検証済みreceiptの集計でDGX160群・Labo48群、計208/768群となった。
DGX batch8の実PID2541856が継続しており、20 worker、起動commandの対象directoryとconfig hashの一致を確認した。
Labo batch1のPID30536は終了し、正規の `result/completion.json` と回収receiptを確認した。
既存Labo session55397は継続しており、batch2のplanned exportへ進んでいるため、新しいworkerを手動で重複起動していない。
観察は `data_tile_validation_2026-10-17/c1t1_pc_process_collection_observation_20261021_v11.json` に保存した。
v11のcompletion_presentは正規名ではないcompleted.jsonを照会していたため、Laboの終端確認を `c1t1_labo_terminal_observation_20261021_v12.json` に追補した。
この観察上の訂正は、実process census・転送検証済み群数・計算入力や実行に変更を加えない。
正規completionのSHA256は `287a5a9a57354215be0c9a1f3900ae2ba8a4af872319abf8ae884ed616dc4fe0` である。
条件全体のBAR校正は未完了であり、正式完了数は6/12条件を維持する。

07:46 JSTにLabo batch2の実PID20352、24 worker、固定config hashの一致を確認した。
正規completionはまだ作られておらず、計算中である。
観察は `data_tile_validation_2026-10-17/c1t1_labo_batch2_running_observation_20261021_v1.json` に保存した。
クラスタはjob265383と265389が引き続きRであり、最終検証・sampling・PC解析の既存経路を継続する。

## GitHubの公開準備状態の再確認

GitHub APIでremote main、local HEAD、CI run39325976119の対象commitが `886b44b9fdc56d5b86491302dfb651285bbc4113` に一致することを再確認した。
当該CIの全12 jobはcompleted・successである。
source・tests・examples・README・pyproject・CI設定・gitattributesには未コミット差分がないことを確認した。
repository visibilityはPRIVATE、Release一覧は空であり、公開済みとは扱わない。
再確認の記録は `data_experimental_release_2026-10-19/remote_status_20261021_v1.json`、SHA256は `69bc8b9a2dd99ad13781ff4cdae365ec14d11232907c1a23674d5085ee01c725` である。
この確認でcommit・push・tag・release・visibilityの変更は行っていない。
CI成功は公開候補のソフトウェア検査であり、進行中の低ノイズ数値校正の完了を意味しない。

## C1T0の回収・独立再集計完了とreaderの実入力修正

C1T0最終検証job265383は07:54:06 JSTにexit status 0で終了し、実測walltimeは1時間35分11秒だった。
元session31431は回収を完了してexit code 0で終了した。
最終reportとreceiptの外部hash、accepted、remote_snapshot_unchangedを確認した。
独立再集計の実入力確認で、追加readerのexport manifest hashとsampling manifest hashの混同、およびkernel mappingをlistとして扱う不一致を検出した。
旧sourceと受入・停止記録を保持し、[小仕様・失敗受入・別版での修正](planned_arithmetic_reference_fix_spec_2026-10-21_ja.md)を行った。
修正後のreaderはWindows34件、待機接続は22件に成功し、実データ8群・704行の接続確認も完了した。
旧待機session76495は全条件pending・子レビュー未起動で停止し、新待機session69708・PID33972で再接続した。

C1T0の全768群・67,584行・352設定・192 seedの独立再集計は51.460秒で正常終了した。
最終reportの11,968値との最大絶対差は1.1102230246251565e-16で、既存の相対許容差1e-10・絶対許容差0を満たした。
review manifestの全16ファイルのbytesとhashを再確認し、長い16設定の報告値とローカルリンク9件も照合した。
低ノイズ検証の正式完了は7/12条件となった。
長い設定でも診断flagは192/192で、広いreference区間との重なり192/192を真値の95%被覆として扱わない。
詳細と生データ・再現sourceへのリンクは[条件別報告](low_c1t0_recovered_result_2026-10-21_ja.md)へ保存した。
既存metadata候補driverもC1T0を受理し、残り5条件の最終回収待ちを継続している。
clusterはjob265389がR、次のsampling job265390がQとなり、待機を含めて2要求ノードを維持する。

## 08:05 JST：C1T2後半の投入照合とPC回収進行

C1T2のsampling partition 1は既存driverからqsubされ、job265390として07:54:41 JSTにqueueへ入った。
実Submit_arguments、submission ledgerのjob IDとqsub command、script SHA256の一致を確認した。
scriptのSHA256は `3ae8544075a91f24d2638e5bf53c64e8518373c3f73aa247e75d8c2e4dbd3dc6` である。
08:05の状態はQで、実行開始や完了はまだ確認していない。
観察は `data_tile_validation_2026-10-17/c1t2_sample1_submission_observation_20261021_v1.json` に保存した。
投入を担当したsession34209はexit code 0で終了し、既存の後続parentはnative・DGX・Laboの待機子processを起動した。
これは後続の科学計算の完了を意味せず、PCの前条件やsampling等の依存条件を引き続き待つ。

C1T1の転送検証済み回収はDGX180群・Labo48群の計228/768群へ進んだ。
receiptとhashの対応は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v13.json` に保存した。
正式完了数は7/12条件を維持し、独立再集計session69708は残る5条件を待っている。

job265390のPBS commentは、要求96 CPUに対して空き88 CPUのため開始できないと記録している。
既存sampling partition実装ではresource_planのcpus=96、投入ledgerと計画の一致、終了時のselect=1:ncpus=96検査が結び付いている。
単純なqalterによる資源変更では既存の終了検証を満たさないため、現在のjob IDと固定計画を維持する。
今後CPU数を可変にする場合は、実行計画・投入記録・終了検証・下流の照合を一体で変更し、稼働中のbundleから分離して検証する必要がある。

C1T1の転送検証済み回収はDGX200群・Labo48群、計248/768群へ進んだ。
C1T2のnative・DGX・Labo後続子processはPID40888・12648・3816で継続しており、実commandのconditionと親PID22720を確認した。
該当3待機directoryにはerror記録もcompleted記録もなく、処理完了とは扱わない。
観察は `data_tile_validation_2026-10-17/c1t1_collection_c1t2_process_observation_20261021_v14.json` に保存した。
同時のPBS照会はjob265389がR、job265390がQで、正式完了数は7/12条件を維持する。

C1T2 sampling partition 0の途中観測では、replicate範囲[0,96)の予定46,080 taskに対し、10,520件のdone markerファイルを確認した。
範囲外・形式外のmarkerは0件で、partition summaryはまだ存在しなかった。
job265389はR・run_count 1、観測されたCPU時間は82時間27分39秒、walltimeは52分25秒だった。
marker内容や成功状態を全件監査した観測ではなく、区画全体の正常終了・科学的な完了には読み替えない。
証拠は `data_tile_validation_2026-10-17/c1t2_sample0_partial_progress_20261021_v1.json` に保存した。

C1T1のDGX batch10が終了・回収され、転送検証済み回収はDGX220群・Labo48群、計268/768群へ進んだ。
新しいarchiveのローカルSHA256を再計算し、receipt・転送検証記録との一致、およびremoteで観察したcompletionのhashとの一致を確認した。
このbatchの数値行検証は1,760行、infrastructure failureは0群だが、条件全体の科学的受入は未完了である。
同時にLabo batch2のPID20352が生存し、固定config hashと一致することを確認した。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v15.json`、SHA256は `deb4cdae3a3063a464847a820bd231449608bd38a6efe42f54bad08c453764a8` である。
正式完了数は7/12条件を維持する。

09:05 JSTのC1T2 sampling partition 0では、done markerが10,520件から16,767/46,080件へ増えた。
partition manifestのhashは前回と同一で、範囲外・形式外のmarkerは0件、partition summaryは未作成だった。
job265389はR・run_count 1、walltimeは1時間24分32秒、CPU時間は133時間2分44秒である。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_partial_progress_20261021_v2.json`、SHA256は `da04e93fd24fddb49f403f4274363a7cd7eb12e6c74b0e3fcd1ebc5df2fc447c` に保存した。
これはmarker名の増加とPBSの稼働を確認した途中経過であり、各taskの成功や科学的完了を示す監査ではない。

09:13 JSTにC1T1のDGX batch11の回収を確認し、転送検証済み回収はDGX240群・Labo48群、計288/768群へ進んだ。
新しいarchiveのSHA256再計算はreceiptと一致し、記録された数値行検証は1,760行、infrastructure failureは0群、context failureはfalseである。
条件全体の科学的受入は未完了で、正式完了数は7/12条件を維持する。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v16.json`、SHA256は `e4eb67174ecb0a5a47121ca0c33ee27e5d8eee29557d2dd204b9723cd8f789f8` に保存した。

09:37 JSTのC1T2 sampling partition 0では、done markerが23,093/46,080件となり、前回から6,326件増加した。
partition manifestのhashは同一で、範囲外・形式外のmarkerは0件、partition summaryは未作成、job265389はR・run_count 1だった。
walltimeは1時間56分35秒、CPU時間は183時間33分4秒で、marker数の約半分への到達を確認したが、task成功や区画完了はまだ監査していない。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_partial_progress_20261021_v3.json`、SHA256は `a8487096a6ff477140c3024988d6bba04bd10dcb9015491798b27f0815937dc3` に保存した。

C1T1のDGX batch12を回収し、転送検証済み回収はDGX260群・Labo48群、計308/768群へ進んだ。
新しいarchiveのローカルSHA256はreceiptと一致し、記録された数値行検証は1,760行、infrastructure failureは0群、context failureはfalseである。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v17.json`、SHA256は `915d4a0073bd6a88486cf0888ff8cf209d631363b99a62265dda47555e1d57cb` に保存した。
条件全体の科学的受入は未完了で、正式完了数は7/12条件を維持する。

09:47 JSTにC1T1のLabo batch2の回収を確認し、転送検証済み回収はDGX260群・Labo72群、計332/768群へ進んだ。
新しいarchiveのローカルSHA256はreceiptと一致し、記録された数値行検証は2,112行、infrastructure failureは0群、context failureはfalseである。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v18.json`、SHA256は `13fb26d68ab9ad7f5cf8d9674bfce3d8e0b3cd7d1881865570c9a3219a8932a9` に保存した。
同時のPBS照会ではjob265389がR、265390がQで、正式完了数は7/12条件を維持する。

10:05 JSTにC1T1のDGX batch13の回収を確認し、転送検証済み回収はDGX280群・Labo72群、計352/768群へ進んだ。
新しいarchiveのローカルSHA256はreceiptと一致し、記録された数値行検証は1,760行、infrastructure failureは0群、context failureはfalseである。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v19.json`、SHA256は `b0b0e8350881c2d6075c36d44c5f63a8518a475821ebcff6068c2f78a236fcec` に保存した。
条件全体の科学的受入は未完了で、正式完了数は7/12条件を維持する。

10:08 JSTのC1T2 sampling partition 0では、done markerが29,819/46,080件となり、前回から6,726件増加した。
partition manifestのhashは同一で、範囲外・形式外のmarkerは0件、partition summaryは未作成、job265389はR・run_count 1だった。
walltimeは2時間26分39秒、CPU時間は230時間53分22秒である。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_partial_progress_20261021_v4.json`、SHA256は `394e34319dee7e57d830c9721d5de965cc7af3584223c543571d267b2025faec` に保存した。
約65%というmarker数の進捗は、task成功や区画完了の監査とは区別する。

C1T1のDGX batch14を回収し、転送検証済み回収はDGX300群・Labo72群、計372/768群へ進んだ。
新しいarchiveのローカルSHA256はreceiptと一致し、記録された数値行検証は1,760行、infrastructure failureは0群、context failureはfalseである。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v20.json`、SHA256は `27d2591d1ae4ce5d5773c66c31b083c31b1d1df5a24449aac46b94c1b635d9dd` に保存した。
条件全体の科学的受入は未完了で、正式完了数は7/12条件を維持する。

10:37 JSTのC1T2 sampling partition 0では、done markerが36,131/46,080件となり、前回から6,312件増加した。
partition manifestのhashは同一で、範囲外・形式外のmarkerは0件、partition summaryは未作成、job265389はR・run_count 1だった。
walltimeは2時間56分44秒、CPU時間は278時間15分17秒である。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_partial_progress_20261021_v5.json`、SHA256は `83672887d4d039521c27f663a0c70a46a65601d36f45b27b6d3faba954dfce44` に保存した。
約78%というmarker数の進捗は、task成功や区画完了の監査とは区別する。

C1T1のDGX batch15を回収し、転送検証済み回収はDGX320群・Labo72群、計392/768群へ進んだ。
新しいarchiveのローカルSHA256はreceiptと一致し、記録された数値行検証は1,760行、infrastructure failureは0群、context failureはfalseである。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v21.json`、SHA256は `e9ec168739dc99076a8e784f3cf7e98bd07654a07141a051562926f9306d930b` に保存した。
解析回収はこの条件の半分を超えたが、条件全体の科学的受入は未完了で、正式完了数は7/12条件を維持する。

11:06 JSTのC1T2 sampling partition 0では、done markerが42,419/46,080件となり、前回から6,288件増加した。
partition manifestのhashは同一で、範囲外・形式外のmarkerは0件、partition summaryは未作成、job265389はR・run_count 1だった。
walltimeは3時間26分50秒、CPU時間は325時間37分56秒である。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_partial_progress_20261021_v6.json`、SHA256は `34e1a58ae91181d631f0fd92bdbb90b6be6f6e2cacdbbe2e9b5613bb31f3e51a` に保存した。
約92%というmarker数の進捗は、task成功や区画完了の監査とは区別する。

11:25 JSTにC1T1のDGX batch16の回収を確認し、転送検証済み回収はDGX340群・Labo72群、計412/768群へ進んだ。
新しいarchiveのローカルSHA256はreceiptと一致し、記録された数値行検証は1,760行、infrastructure failureは0群、context failureはfalseである。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v22.json`、SHA256は `c77182ca8b874094d430907643f2d534b308146220326584fa6b8d027316804e` に保存した。
同時のPBS照会ではjob265389がR、265390がQで、正式完了数は7/12条件を維持する。

11:26 JSTのC1T2 sampling partition 0では、予定と同数の46,080件のdone markerを確認した。
範囲外・形式外のmarkerは0件、partition manifestのhashは同一だったが、partition summaryは未作成で、job265389はR・run_count 1だった。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_partial_progress_20261021_v7.json`、SHA256は `9043cb77a520c9d5b74d83063c637d66f13a6e3a025ecec71b579029f59f042f` に保存した。
全marker名が揃ったことは全taskの成功や区画の正常終了を意味せず、終了summaryとPBS終端の照合を引き続き待つ。

全marker確認後の2回のPBS観測でもjob265389はR、summaryは未作成だった。
PBSのwalltime差480秒に対してCPU時間は472秒増えており、単に終了記録を待つだけの無活動状態とは判断しない。
この差分はPBS counterの観測であり、更新遅延がありうるため、正確な実行phaseの特定やbenchmarkには用いない。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_post_marker_observation_20261021_v1.json`、SHA256は `8d12e7973d7b7cb9f065fc14e3f71fef1539429fe00401ac5d623845ec6c771e` に保存した。

11:47 JSTにC1T1のDGX batch17の回収を確認し、転送検証済み回収はDGX360群・Labo72群、計432/768群へ進んだ。
新しいarchiveのローカルSHA256はreceiptと一致し、記録された数値行検証は1,760行、infrastructure failureは0群、context failureはfalseである。
観察は `data_tile_validation_2026-10-17/c1t1_pc_collection_observation_20261021_v23.json`、SHA256は `99294af1c6df5ccd7c93e14a6391b0e582598a4acd1f84350cda313f615beb73` に保存した。
同時のPBS照会ではjob265389がR、265390がQで、正式完了数は7/12条件を維持する。

## C1T2 sampling前半の終了と後続投入

job265389は12:17:34 JSTにF・Exit_status=0・run_count=1で終了し、walltimeは4時間37分45秒だった。
summaryは46,080件の予定と観測が一致し、一意のtaskも46,080件、全recordがok、失敗・欠損・errorsはいずれも0である。
summaryのSHA256は `930e4ee590ee3666fff637ba4e0c7dc650dafe1d89c061c6abac0e2ebb98fb21` である。
PBSの実行script・resourceと保存済みqsub command・submission intentを照合し、従来のscript・submissionのhash、およびsummaryとexecution intent・native preflightのhash対応も確認した。
今回の観察でraw trace payloadの独立再hashや全状態の再復号は行っておらず、後続collector・監査・解析の完了を待つ。
job265390は12:17:34 JSTに実行開始し、C3T0生成driverは12:18:03 JSTにjob265411をqsubで投入して正常終了した。
265411の要求は1 node・96 CPU・32 GB・21時間30分であり、要求walltimeはETAではない。
12:20 JSTの照会では265390がR、265411がQで、待機中を含めて2 nodeである。
観察は `data_tile_validation_2026-10-17/c1t2_sample0_terminal_followup_observation_20261021_v1.json`、SHA256は `9667f5a10dbffee67b6162932eb8c2bd942b6868c9eedaff90d4422b989f6dfe` に保存した。
正式な条件完了数は7/12を維持する。

13:08 JSTのC1T2 sampling後半では、done markerを9,907/46,080件確認し、12:40 JSTの観察から5,586件増加した。
範囲外・形式外のmarkerは0件、partition manifestのhashは同一で、job265390はR・run_count=1、summaryは未作成だった。
これはmarker名の進捗観察であり、task成功や区画完了の監査とは区別する。
観察は `data_tile_validation_2026-10-17/c1t2_sample1_partial_progress_20261021_v2.json`、SHA256は `d63fb7c7455ac44e91d1434c6ac598247c75c455138ea54e1d065775621d73c8` に保存した。

13:39 JSTのC1T2 sampling後半では、done markerが16,081/46,080件となり、前回から6,174件増えた。
範囲外・形式外のmarkerは0件、partition manifestのhashは同一で、job265390はR・run_count=1、summaryは未作成だった。
観察は `data_tile_validation_2026-10-17/c1t2_sample1_partial_progress_20261021_v3.json`、SHA256は `148013e3417be4c5be458ba73ee2bd3f6f509faabc5a055968deb7dd5ad8141a` に保存した。
marker名の件数をtask成功・区画完了・条件全体の検証完了とは扱わない。

## C1T1のLabo担当分の回収完了

Laboのserial driver（session55397）はexit code 0で終了し、保存済みcompleted.jsonでも担当全batchの回収完了を確認した。
割当表にあるLaboのsequence 0–4と、各archiveのassignment・config・completionのmember hash、およびtransfer receiptの対応を照合した。
completionのgroup集合は割当の120群と重複・抜けなく一致し、保存済み完了記録の行数は計10,560行である。
各batchのpending group・infrastructure failure・未観測行は0で、全groupのstatusはok、failed sampling taskの記録もなかった。
これは担当分の保存済みmetadataと割当の照合であり、全cohortの独立算術レビューや再復号の完了とは扱わない。
全batchでscientific_cohort_accepted=falseを保持し、正式な条件完了数は7/12のままである。
観察は `data_tile_validation_2026-10-17/c1t1_labo_assignment_completion_observation_20261021_v1.json`、SHA256は `19b357042fbfeb3f013843204008404377a6cab028883383e0cc8be6f9114a2c` に保存した。
13:57 JSTに後続C1T2のLabo waiter（PID3816）が動作中であることを確認し、同waiterの最新観察はprevious_completed=true・native_completed=falseだった。

14:08 JSTのC1T2 sampling後半では、done markerが21,825/46,080件となり、前回から5,744件増えた。
範囲外・形式外のmarkerは0件、partition manifestのhashは同一で、job265390はR・run_count=1、summaryは未作成だった。
観察は `data_tile_validation_2026-10-17/c1t2_sample1_partial_progress_20261021_v4.json`、SHA256は `dd33def8edafda05a9640253f740f8ab1c409c3ce5cb53ae81443628315af388` に保存した。
marker名の進捗は成功判定とは区別し、正式な条件完了数は7/12を維持する。

14:37 JSTのC1T2 sampling後半では、done markerが27,826/46,080件となり、前回から6,001件増えた。
確認したファイル名形式・case/target・replicate範囲の違反は0件、partition manifestのhashは同一で、job265390はR・run_count=1、summaryは未作成だった。
この部分観察では他のtask次元を含む予定task集合との全照合やmarker payloadの検証は行っていない。
観察は `data_tile_validation_2026-10-17/c1t2_sample1_partial_progress_20261021_v5.json`、SHA256は `a43c1b8c5ad803e25c10bb3ed7b60e3e47a6d4cda3d25c54c6a7206312c54696` に保存した。
正式な条件完了数は7/12を維持する。
