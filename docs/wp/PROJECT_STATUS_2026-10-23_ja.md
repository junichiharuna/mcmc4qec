# mcmc4qec：2026-10-23の継続状態

[Goalの完了条件と確認済み範囲](goal_completion_status_2026-10-23_ja.md) に、公開準備・主校正の完了分と、低ノイズの残り1条件・全条件比較・独立計時・最終報告の残作業を整理した。
現在のpackage 33ファイルがwheelと一致し、基本decoder受入対象46ファイルも保存済み受入時の内容と一致することを追加確認した。

残処理の所要時間は[運用上の実測基準](runtime_forecast_2026-10-23_ja.md)に整理した。
indexの前段待機時間と実処理時間、PCの本解析時間と転送・回収を含む経過時間を区別する。

比較用入力が揃った11条件の[experimental利用時の読み方](low_noise_interim_usage_2026-10-23_ja.md)を整理した。
既存CSVとmanifestを照合し、最初の再現対象候補、低p・tile288での診断とreferenceの限界、追加decoderへ結果を外挿しないことを整理した。
全12条件の正式比較や校正済み推奨設定の選定は未完了である。

## 23:59 JSTのDGX第20バッチ開始

C3T2のDGX batch19は入力生成・転送・stageを終え、実機PID2831416の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch19_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は500/768群・44,000行のままで、実行中のbatchを完了件数へ加えていない。

## 23:53 JSTのDGX第19バッチ回収

C3T2のDGX batch18は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch18_collection_observation_v1.json)が完了した。
archiveは181,979,310 byte、SHA256は `199204c236c7e66fe9326e4f8c9f4ebb5b6f69e1cdcaced18d5526b761c3017c` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認し、数値解析やarchiveの再hashは行っていない。
正式回収はDGX 19/33バッチ・labo 5/5バッチ、計500/768群・44,000行となった。
残る268群の解析・回収と後続の集約・全条件比較は未完了であり、回収完了を混合・精度・被覆の合格とは扱わない。

## 23:49 JSTのDGX第19バッチ計算終了

C3T2のDGX batch18は実機の終了記録を確認し、ローカルの[launch完了記録](data_tile_validation_2026-10-17/portable_condition_c3t2_dgx_batch18_launch_v1/completed.json)のcompletion hashと一致した。
SSH実行の終了コードは0で、completionのSHA256は `a8286e7849faddb06785707853160a461c925e6961c7b7fe87124d6fe17d608a` だった。
既存serial制御は回収へ進んだが、この時点では回収・照合は未完了である。
正式回収は480/768群・42,240行のままで、このbatchの20群は未加算である。

## 23:42 JSTのlabo全バッチ回収完了

C3T2のlabo batch4の[自動回収の照合](data_tile_validation_2026-10-17/c3t2_labo_batch4_collection_observation_v1.json)が完了した。
archiveは220,292,473 byte、SHA256は `f90e01c0aed86e74be1895d15902bcb589ff265dd50eca1e953e9609feb540cf` で、24群・2,112行、infrastructure failed 0・context failed falseだった。
観測記録とwatch progress、最終バッチの参照metadata 5件のhash、実機終了時のcompletion・configの対応を確認した。
labo全5件の観測記録のhashと件数も照合し、計120群・10,560行だった。
[serial完了記録](data_tile_validation_2026-10-17/portable_condition_c3t2_labo_serial_driver_v1/completed.json)の `all_assigned_batches_collected=true` と制御プロセスの終了を確認し、同記録のSHA256は `0f16111f8ea2e023c02e9e57ca893e3b306b22015042222832e3d212323625c8` だった。
正式回収はDGX 18/33バッチ・labo 5/5バッチ、計480/768群・42,240行となった。
数値解析やarchiveの再hashは行っておらず、残るDGXバッチの解析・回収と後続の集約・全条件比較は未完了である。

## 23:36 JSTのlabo最終バッチ計算終了

C3T2のlabo batch4は実機の終了記録を確認し、ローカルの[launch完了記録](data_tile_validation_2026-10-17/portable_condition_c3t2_labo_batch4_launch_v1/completed.json)のcompletion hashと一致した。
SSH実行の終了コードは0で、completionのSHA256は `84acbd5f8cf3292f529aba53dccef19c1120d45e1ec45ae294147d44d6179e04` だった。
laboに割り当てた5バッチの計算は終了し、既存serial制御は最後の回収へ進んだ。
この時点では最終バッチの回収・照合は未完了で、正式回収は456/768群・40,128行のままである。
DGXの残りバッチと後続の集約・比較は未完了であり、全数値検証の終了とは扱わない。

## 23:26 JSTのDGX第19バッチ開始

C3T2のDGX batch18は入力生成・転送・stageを終え、実機PID2818626の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch18_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は456/768群・40,128行のままで、実行中のbatchを完了件数へ加えていない。

## 23:19 JSTのDGX第18バッチ回収

C3T2のDGX batch17は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch17_collection_observation_v1.json)が完了した。
archiveは181,184,005 byte、SHA256は `6cef4fe10c242fd21c601a41dd4b74af35442294c9a0d98c4a3d9b7f55b5e5af` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とwatch progress、参照metadata 5件のhash、実機終了時のcompletion・configのhash対応を確認し、数値解析やarchiveの再hashは行っていない。
正式回収はDGX 18/33バッチ・labo 4/5バッチ、計456/768群・40,128行となった。
回収・照合の完了は混合・精度・被覆の合格を意味せず、全768群の集約と全条件比較は引き続き未完了である。

## 23:15 JSTのDGX第18バッチ計算終了

C3T2のDGX batch17は実機の終了記録を確認し、ローカルの[launch完了記録](data_tile_validation_2026-10-17/portable_condition_c3t2_dgx_batch17_launch_v1/completed.json)のcompletion hashと一致した。
SSH実行の終了コードは0で、completionのSHA256は `26bcd11d1017f579a14989fb4eaf50e2ca9a8f5dbb9100835725215365667669` だった。
既存serial制御は回収へ進んだが、回収・照合の完了はまだ確認していない。
正式回収は436/768群・38,368行のままであり、このbatchの20群は未加算である。

## 22:52 JSTのDGX第18バッチ開始

C3T2のDGX batch17は入力生成・転送・stageを終え、実機PID2759223の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch17_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は436/768群・38,368行のままで、実行中のbatchを完了件数へ加えていない。

## 22:45 JSTのDGX第17バッチ回収

C3T2のDGX batch16は22:41に終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch16_collection_observation_v1.json)が完了した。
archiveは182,277,414 byte、SHA256は `55d75b5ad7c8e5862224f1b26e0b5698eabe56dd5efc6260019800f316cf9dbc` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とwatch progress、参照metadataのhash、実機終了時のcompletion・configのhash対応を確認し、数値解析やarchiveの再hashは行っていない。
正式回収はDGX 17/33バッチ・labo 4/5バッチ、計436/768群・38,368行となった。
kernel・初期化index `(1,0)` を含む最初のDGX混在batchの計算時間は23.04分だったが、組合せ単独の所要時間測定や残り全batchの保証ではない。
[更新した実測記録](data_tile_validation_2026-10-17/c3t2_runtime_observation_20261023_v4/observation.json)では、平均回収間隔を使う単純外挿はDGXが24日7:35、laboが23日23:41である。
PC回収は24日朝、最終報告は25〜26日の目安を維持し、未観測の組合せと後続処理による延長可能性を残す。

## 22:18 JSTのDGX第17バッチ開始

C3T2のDGX batch16は入力生成・転送・stageを終え、実機PID2746050の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch16_start_observation_v1.json)で確認した。
このbatchにはDGX上でまだ完了時間が未観測のkernel・初期化index `(1,0)` が含まれるため、前半の平均回収間隔を終了保証として扱わない。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は416/768群・36,608行のままで、実行中のbatchを完了件数へ加えていない。

## 22:12 JSTのDGX第16バッチ回収

C3T2のDGX batch15は22:08に終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch15_collection_observation_v1.json)が完了した。
archiveは184,211,410 byte、SHA256は `48ccc5c18a9634b2c931b053e7c36a5f54f805dd74316b1844f6e177af3c02dd` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とwatch progress、参照metadataのhash、実機終了時のcompletion・configのhash対応を確認した。
数値解析やarchiveの再hashは行っていない。
正式回収はDGX 16/33バッチ・labo 4/5バッチ、計416/768群・36,608行となった。

## 21:45 JSTのDGX第16バッチ開始

C3T2のDGX batch15は入力生成・転送・stageを終え、実機PID2686578の生存と終了記録未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch15_start_observation_v1.json)で確認した。
既存serial制御による継続であり、重複投入や制御の再起動はしていない。
正式回収は396/768群・34,848行のままで、実行中のbatchを完了件数へ加えていない。

## 21:39 JSTのDGX第15バッチ回収

C3T2のDGX batch14は終了コード0で終了し、[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch14_collection_observation_v1.json)が完了した。
archiveは183,929,584 byte、SHA256は `34d67125583cdc393f8ed30678d14e2922e7c5c1fe5cc533337452afb5038a18` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
今回の確認では観測記録とwatch progress、参照metadataのhash、実機終了時のcompletion・configのhashが一致した。
数値解析やarchiveの再hashは行っていない。
正式回収はDGX 15/33バッチ・labo 4/5バッチ、計396/768群・34,848行となった。
既存serial制御はDGX batch15の入力準備へ進んだが、この時点で次バッチの計算開始はまだ確認していない。
全12条件比較用の待受は11条件分の入力を認識しており、最後のC3T2を待っている。
新しい[英語の検証案内](../tile_validation_interim_en.md)は作業ツリーに保存し、固定済み公開候補へは追加していない。

## 21:26 JSTの最終集約回収と後続入力準備

C3T1（tile288・depolarizing・p=0.003）の最終集約jobは正常終了し、21:19に13ファイルの回収が完了した。
[回収結果の観測](data_tile_validation_2026-10-17/c3t1_final_report_observation_20261023_v1/observation.json)でreceiptと成果物hashを確認した。
後続処理も21:22に終了し、11,968個の集計値の独立照合と全条件比較用candidateの準備が完了した。
今回の確認ではreview・candidate・receiptの実ファイルhashが後続完了記録と一致した。
これにより比較用入力は11/12条件分となったが、全条件比較・独立計時は未実施である。
352設定の各192反復で点推定と区間は得られた一方、全設定でflagged・undefinedが各192件であり、混合や名目95%被覆の認定には使えない。
重み層別referenceのfull point estimateも未取得であり、partial estimateを真値とは扱わない。
C3T2（p=0.001）の正式回収は376/768群・33,088行で、DGX 14/33バッチとlabo 4/5バッチが完了している。
実機照会でDGX batch14とlabo最終batch4のプロセス生存・終了記録未作成を確認した。
クラスタの現在のqueue照会では投入scriptに本プロジェクト名を含むactive jobはなかったが、残条件の集約と全条件比較・独立計時の後続jobは残る。
運用上の見込みはPC解析・回収が10月24日朝、残条件集約が同日午後〜夜、比較・独立計時・最終報告が10月25〜26日であり、後半batchの所要時間やqueue待ちにより延びうる。

## 21:13 JSTのlabo第4バッチ回収とDGX第15バッチ開始

labo batch3の終了コード0・実機終了記録と[自動回収の照合](data_tile_validation_2026-10-17/c3t2_labo_batch3_collection_observation_v1.json)が対応した。
archiveは218,084,242 byte、SHA256は `534527d1ebe88319bb4a48c26f232688e09ec07d78c51f7dce01c34c82adee50` で、24群・2,112行、infrastructure failed 0・context failed falseだった。
観測記録とprogress、参照metadataのhashを追加照合し、数値解析やarchiveの再hashはしていない。
正式回収はDGX 14/33バッチ・labo 4/5バッチ、計376/768群・33,088行になった。
laboの既存制御は最後のbatch4の入力生成へ進み、DGXのbatch14は実機PID2653753の生存とterminal未作成を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch14_start_observation_v1.json)で確認した。
C3T1は21:08にcomplete処理が終了し、既存制御による回収へ進んだ。
この確認時点ではexecutionのcompleted記録はなく、回収・科学的集計照合・全条件比較用入力の準備は未完了である。

## 21:07 JSTの最終集約job終了とDGX第14バッチ回収

C3T1最終集約job265495のF・Exit_status 0を、投入記録・設定hash・script hash・要求資源と対応させた[終了観測](data_tile_validation_2026-10-17/c3t1_final_completion_observation_20261023_v1/observation.json)に保存した。
実walltimeは3時間45分37秒、CPU時間は3時間39分26秒で、要求上限12時間とは区別する。
既存のexecution制御は21:03に終了観測とcomplete-intentを保存し、設定・結果の再照合へ進んでいる。
この時点では回収・科学的集計照合・全条件比較用入力の準備は未完了であり、低ノイズ条件全体の完了や名目被覆の認定とは扱わない。
DGX batch13も実機終了記録と[自動回収の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch13_collection_observation_v1.json)が対応した。
archiveは184,029,086 byte、SHA256は `902a3ea0176bf4bd526adaab5034452cae7ad979d33b650daf66ff3a747c555f` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とprogress、参照metadataのhashを追加照合し、数値解析やarchiveの再hashはしていない。
正式回収はDGX 14/33バッチ・labo 3/5バッチ、計352/768群・30,976行になった。
labo batch3は21:06の実機照会でPID18184が生存し、terminal記録はなかった。

## 20:40 JSTのDGX第14バッチ開始

C3T2のDGX batch13が入力生成・転送・stageを終え、実機のPID2617229が生存しterminal記録がないことを[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch13_start_observation_v1.json)で確認した。
正式回収は332/768群・29,216行のままであり、解析中のbatchを完了件数へ加えていない。
C3T1最終集約job265495もR・実walltime3時間22分で、結果の回収は未完了である。
既存のserial制御による継続で、重複投入や再起動はしていない。

## 20:32 JSTのDGX第13バッチ回収

DGX batch12の実機終了記録と、自動待受による[archiveと完了記録の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch12_collection_observation_v1.json)を確認した。
archiveは184,149,355 byte、SHA256は `8d2f9f98bfc4c1c4636828eaa5daa1005270fa71dd9b6edb4f79841ab2ce3bb1` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とprogress、参照metadataのhash対応を追加確認し、archiveの再hashや数値解析の再実行はしていない。
正式回収はDGX 13/33バッチ・labo 3/5バッチ、計332/768群・29,216行になった。
C3T1最終集約job265495は直近の照会でR・実walltime3時間14分であり、最終結果の回収・全12条件比較・独立計時・最終報告は未完了である。

## 20:06 JSTのDGX第13バッチ開始

C3T2のDGX batch12が入力生成・転送・stageを終え、実機のPID2558692が生存しterminal記録がないことを[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch12_start_observation_v1.json)で確認した。
正式回収は312/768群・27,456行のままであり、解析中のbatchを完了件数へ加えていない。
C3T1最終集約job265495もR・実walltime2時間48分で、結果の回収は未完了である。
既存のserial制御による継続で、重複投入や再起動はしていない。

## 19:59 JSTのDGX第12バッチ回収

DGX batch11の実機終了記録と、自動待受による[archiveと完了記録の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch11_collection_observation_v1.json)を確認した。
archiveは184,304,183 byte、SHA256は `05d11ee56afb59af0741d9ccf50e79ddb237a2582a7005f5faa5e23612eb160f` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とprogress、参照metadataのhash対応を追加確認し、archiveの再hashや数値解析の再実行はしていない。
正式回収はDGX 12/33バッチ・labo 3/5バッチ、計312/768群・27,456行になった。
既存serial制御は次のDGX batch12の入力生成へ進んだが、その計算開始はまだ確認していない。
C3T1最終集約job265495は直近の照会でR・実walltime2時間40分であり、最終結果の回収・全12条件比較・独立計時・最終報告は未完了である。

## 19:32 JSTのDGX第12バッチ開始

C3T2のDGX batch11は入力生成・転送・stageを終え、実機のPID2546170が生存しterminal記録がないことを[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch11_start_observation_v1.json)で確認した。
正式回収は292/768群・25,696行のままであり、解析中のbatchを完了件数へ加えていない。
labo batch3のPID18184も19:29の実機照会で生存し、terminal記録はなかった。
C3T1最終集約job265495は19:30の照会でR・実walltime2時間12分だった。
既存制御による継続であり、重複投入や再起動はしていない。

## 19:24 JSTのDGX第11バッチ回収

DGX batch10の正常終了後、自動待受による[archiveと完了記録の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch10_collection_observation_v1.json)が完了した。
archiveは183,895,287 byte、SHA256は `fe26d919b21a3fb62bc96bc611bb873d5545511ed318f3c10d83e9b68b737e8a` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とprogress、参照metadataのhash対応を追加確認し、archiveの再hashや数値解析の再実行はしていない。
正式回収はDGX 11/33バッチ・labo 3/5バッチ、計292/768群・25,696行になった。
C3T1最終集約job265495はR・実walltime2時間6分で、最終結果の回収と内容照合は未完了である。
全12条件比較・独立計時・最終報告は引き続き未完了であり、回収確認を科学的校正の完了とは扱わない。

## 18:58 JSTのDGX第11バッチ開始

C3T2のDGX batch10は次の入力準備を終え、実機のPID2487813が生存しterminal記録がないことを[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch10_start_observation_v1.json)で確認した。
正式回収は272/768群・23,936行のままで、解析中のbatchを完了件数へ加えていない。
既存serial制御による継続であり、新たな制御の起動や重複投入はしていない。

## 18:51 JSTのDGX第10バッチ回収とlabo第4バッチ開始

DGX batch9の終了後、自動待受による[archiveと完了記録の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch9_collection_observation_v1.json)が完了した。
archiveは183,859,478 byte、SHA256は `da36e979ee860fb6425304ad698ee1173d03ab9300785465036d598cbc33f8e3` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録とprogress、参照metadataのhash対応を追加確認し、archiveの再hashや数値解析の再実行はしていない。
正式回収はDGX 10/33バッチ・labo 3/5バッチ、計272/768群・23,936行になった。
labo batch3は次の入力準備を終え、実機のPID18184が生存しterminal記録がないことを[開始観測](data_tile_validation_2026-10-17/c3t2_labo_batch3_start_observation_v1.json)で確認した。
クラスタの最終集約job265495もRであり、低ノイズ条件全体の集約と全12条件比較は未完了である。
GitHubも再照会し、PRIVATE・Release0件を確認した。
公開用の履歴修正・commit・pushは所有者への確認が未回答のため実施していない。

## 18:44 JSTのlabo第3バッチ回収

labo batch2の正常終了後、自動待受による[archiveと完了記録の照合](data_tile_validation_2026-10-17/c3t2_labo_batch2_collection_observation_v1.json)が完了した。
archiveは218,720,892 byte、SHA256は `c407205369158842674745317348e20c3ab1ee8ebc127327c7f167aed3df8a2e` で、24群・2,112行、infrastructure failed 0・context failed falseだった。
観測記録と待受progress、参照metadataのhash対応を追加確認し、archiveの再hashや数値解析の再実行はしていない。
正式回収はDGX 9/33バッチ・labo 3/5バッチ、計252/768群・22,176行になった。
C3T1最終集約job265495は引き続きRで、最新照会の実walltimeは1時間25分55秒だった。
条件全体の集約・全12条件比較・独立計時は未完了であり、回収確認を科学的校正の完了とは扱わない。

## 18:24 JSTのDGX第10バッチ開始

C3T2のDGX batch9が入力export・転送・stageを終え、実機のPID2476107が生存しterminal記録がないことを[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch9_start_observation_v1.json)で確認した。
正式回収は228/768群・20,064行であり、解析中のbatchを完了件数へ加えていない。
既存serial制御による次バッチへの接続で、新たな制御の起動や重複投入はしていない。

## 18:17 JSTのC3T2第9DGXバッチ回収

DGX batch8の終了・自動回収後、待受による[archiveと完了記録の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch8_collection_observation_v1.json)が完了した。
archiveは184,698,889 byte、SHA256は `2c4f9d8f9afd3bb23b6118964d050b9718758009f91299e8b5735abf5d1f2e3a` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
待受progressと観測記録、参照metadataのhashを追加照合し、同じarchiveの再hashや数値解析の再実行はしていない。
正式回収はDGX 9/33バッチ・labo 2/5バッチ、計228/768群・20,064行になった。
この回収確認を混合・精度・被覆の認定とは扱わず、全12条件の最終比較は引き続き未完了である。

## 17:51 JSTの次DGXバッチ開始

C3T2のDGX batch8は入力export・転送・stageを終え、実機のPID2416900が生存しterminal記録がないことを[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch8_start_observation_v1.json)で確認した。
これは第9バッチの解析開始であり、正式回収件数は208/768群のままである。
C3T1最終集約job265495も、直近のPBS照会でR・実walltime32分19秒だった。
既存の自動制御による処理を継続し、新たなjob投入や再実行はしていない。

## 17:43 JSTのC3T2第8DGXバッチ回収と集約時間の確認

DGX batch7の終了後、自動待受が[archiveと完了記録の照合](data_tile_validation_2026-10-17/c3t2_dgx_batch7_collection_observation_v1.json)を完了した。
archiveは182,325,453 byte、SHA256は `ddf7b6d04bfaadd6654183535587a580aaa6f98e92a322a130d42e2c486b78fd` で、20群・1,760行、infrastructure failed 0・context failed falseだった。
観測記録と待受progressのhash、参照metadataのhashを追加照合し、raw archiveを重複して再hashしていない。
正式回収はDGX 8/33バッチ・labo 2/5バッチ、計208/768群・18,304行になった。
先行C3T0最終集約job265459のF・exit 0と実walltime2時間30分28秒をPBS履歴で確認した。
C3T1最終集約job265495はR・実walltime24分18秒で、今夜の完了を運用上の目安とするが、終了後の回収・照合も残る。
具体的な比較条件と限界は[終了見込み](runtime_forecast_2026-10-23_ja.md)へ追記した。

## 17:26 JSTの最終集約とPC解析の実稼働確認

C3T1の最終集約は17:17にqsubで投入され、job265495のR状態と実walltime8分36秒を確認した。
要求は1 node・1 CPU・32 GB・walltime上限12時間で、投入receiptとPBS情報の対応を保存済みである。
終了・回収・内容照合はまだ完了しておらず、正式な低ノイズ最終入力は10/12条件のままである。
C3T2はDGX batch7のPID2405813とlabo batch2のPID23596を実機上で確認し、両方とも実行中でterminal記録はなかった。
回収照合済みは188/768群・16,544行であり、開始したbatchを回収件数へ加えていない。
今回の[実稼働観測](data_tile_validation_2026-10-17/runtime_observation_20261023_1726_v1.json)は既存の投入・解析の読み取りのみで、新たなjob投入や再実行はしていない。
PC解析・回収を24日朝、C3T2条件別集約を24日午後〜夜、全条件比較・独立計時・最終報告を25〜26日の目安とする。
独立計時は未開始のため26日以降へ延びる可能性を残し、時刻の確約とは扱わない。

## 17:14 JSTのC3T1投入前検査とC3T2の188群回収

C3T1のpreparationは135 source・383 metadataと完了済み監査job265461への接続を受理し、completedを作成した。
configのSHA256は `346bafffcfb4ad2480fe7635fc68374d54225af102de39b4b8026e060bebaadc`、job rootは `20261022-planned8h-c3t1-final-v1` である。
execution制御はpreflightを完了し、submit-000-intentへ進んだ。
実際のreport.shを読み、qsub用の1 node・1 CPU・32 GB・walltime上限12時間を確認した。
この時点ではsubmit-completedとPBS job IDをまだ取得しておらず、投入処理のSSH子PID17424と制御PID26316の生存を確認した。
上限walltimeを所要時間の予測として使わない。

C3T2のDGX batch6は自動待受による[回収照合](data_tile_validation_2026-10-17/c3t2_dgx_batch6_collection_observation_v1.json)が完了し、20群・1,760行、infrastructure failed 0・context failed falseだった。
archive本体182,555,047 byteのSHA256は `5398a71f43935ba39e84ab89ac2eb0342ebb7588aa4a037d5ab6929b5e535e21` である。
正式回収済みはDGX 7/33バッチ・labo 2/5バッチ、計188/768群・16,544行になった。
自動照合待受PID16268は継続し、errorは存在しない。

## 17:03 JSTのC3T1転送完了と最終集約の準備

既存distribution制御は17:01:27に転送を完了し、最終集約のpreparation制御がrequestとprepare-intentを作成した。
転送receiptの170ファイル・6,535,632,313 byte、destinationとcontextの対応をcompleted記録と照合した。
receiptのSHA256は `1e63df17f801640e03512484204a416a60d66ff7bc8b58031529a36ba5dc05aa`、contextは `40041bcfa64512cb166c2d30bd670dcf2c27267872cb4711e3947dd042a720bf` である。
この追加照合では転送payloadを再hashせず、既存転送検証のreceiptと完了記録を対応させた。
preparation・execution・downstreamの制御プロセスは生存し、確認したjournalにerrorはなく、後続qsubの投入はまだ確認していない。

DGX batch6のPID2348649、labo batch2のPID23596を実機上で確認し、解析を並行して継続している。
公開用コピーのGitHubへの反映方針は所有者への確認待ちであり、履歴更新・commit・pushはしていない。

## 16:53 JSTのC3T1 index終了照合と公開用コピーの検証

C3T1 indexは16:49:57に終了し、実処理時間は3.809時間だった。
[終了照合](data_tile_validation_2026-10-17/c3t1_index_completion_observation_20261023_v1.json)で38バッチ・768群・67,584行、pending 0、infrastructure/context failure 0と、registry・snapshot・completedのhash対応を確認した。
全67,584行にflaggedとundefinedが記録され、区間未取得は0行であり、この診断を分母から除外していない。
これはindexの完了であり、混合・精度・被覆や最終cohort受理の認定ではない。
snapshotのSHA256は `33645b12e17b0179025c594cf8e5ce879f81dba43383f362897416efad2ac015` で、既存distribution制御は転送へ進んだ。

DGX batch5は自動待受による照合も完了し、C3T2は8バッチ・168/768群・14,784行まで回収済みで、待受errorはなかった。
別checkoutでは、公開済みという誤記と識別子再導入を修正した[レビュー用snapshot](publication_review_snapshot_2026-10-23_ja.md)を作成し、source ZIP・wheel・core install/verifyを確認した。
公開用コピーは未コミットで、既存tag・remote・計算中の入力は変更していない。

## 16:27 JSTのC3T1 index入力規模の照合

保存registryとZIP中央directoryを読み、先行C3T0に対してC3T1はtrace数1.30倍、展開後の入力・結果ファイル量約1.27倍であることを[観測記録](data_tile_validation_2026-10-17/index_input_scale_observation_20261023_v1/observation.json)に保存した。
C3T1 indexは13:01開始から約3.44時間経過して継続中であり、先行実測を規模比だけで換算した17時前後を参考値として[終了見込み](runtime_forecast_2026-10-23_ja.md)に追記した。
サイズや経過時間を完了率と読み替えず、実際のcompletedを待つ。
稼働中のindex sourceや入力、後続driverは変更していない。

## 16:23 JSTのlabo第3バッチ開始

labo batch2はexport・転送確認・stageを終え、解析PID23596の実稼働を[開始観測](data_tile_validation_2026-10-17/c3t2_labo_batch2_start_observation_v1.json)で確認した。
DGXとlaboの解析を並行して継続し、自動照合待受PID16268のprogressは148群・13,024行、errorは存在しない。
C3T1 indexのPID16732はCPU時間6395.63秒まで増加し、completedもerrorもまだ存在しない。
この更新は解析開始と実稼働の確認であり、正式な回収件数は増やしていない。

## 16:19 JSTの回収照合待受開始

[小仕様](c3t2_collection_observer_watch_spec_2026-10-23_ja.md)、受入テスト、実装の順で、既存collect-completedを待って読み取り専用observerを呼ぶ待受を追加した。
assignmentの重複・欠落・別条件、未回収batch、既存観測の件数・入力hashの不一致、intent上書きの拒否を含む7 testが0.79秒で成功した。
[受入記録とsource保存](data_tile_validation_2026-10-17/c3t2_collection_observer_watch_v1/accepted.json)のSHA256は `a8ccd892f9d17ce623f4e7499f6d858d4d1fc1e378944cd392bcd71a6bd46f6b` である。
本番の既存7観測・148群・13,024行と入力hashの対応を確認してからhiddenで起動し、PID16268の実command・生存と初回progressを確認した。
待受は全38バッチの回収照合が揃うと終了し、失敗時にはerrorを保存して自動再試行しない。
今後の回収観測はこの待受が排他作成するため、同じbatchのobserverを手動で重ねて起動しない。
待受のsource・固定assignment・既存observerを実行中に変更しない。

実行入口は `output/c3t2_collection_observer_watch_v1/watch.py --run`、記録は `data_tile_validation_2026-10-17/c3t2_collection_observer_watch_v1/run/` にある。
既存の計算・転送・投入driverは変更せず、追加のsampling・BAR計算やqsubは実行していない。
全batchの回収照合が揃っても、科学的な集約・混合・被覆の検証を代替せず、scientific_validation_completeはfalseのままとする。
DGX batch5のPID2279640は実機上で生存し、labo batch2はまだlaunch intentがない準備段階だった。
C3T1 indexのPID16732もCPU時間6285.64秒まで増加しており、引き続き正式完了を待つ。

## 16:14 JSTのlabo第2バッチ回収完了

labo batch1の24群・2,112行を[回収照合](data_tile_validation_2026-10-17/c3t2_labo_batch1_collection_observation_v1.json)で確認した。
archive本体220,115,427 byteのSHA256は `498c0dea8584c5c4daa351507b8350f26d9347a70862f5a8ab6d667f2fa59bf6` で、割当・config・terminal・report・parentの対応が一致した。
infrastructure failed 0、context failed falseであり、DGX 5/33バッチ・labo 2/5バッチ、計148/768群・13,024行の回収が完了した。
これらの合計は7件の保存済み回収観測から再計算した。
既存labo serialはbatch2のexportへ進み、DGX batch5の解析と並行する。
C3T1 indexはCPU時間6134.64秒まで増加しており、正式完了はまだ確認できていない。

## 16:12 JSTのDGX第6バッチ開始とlabo第2バッチ回収中

DGX batch5はexport・転送確認・stageを終え、解析PID2279640の実稼働を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch5_start_observation_v1.json)で確認した。
labo batch1はlaunch-completedが作成され、回収PID2224とそのSSH子PID42500が稼働中である。
collect-completedはまだ存在せず、正式回収件数は124/768群・10,912行のままとする。
C3T1 indexのPID16732はCPU時間6055.64秒まで増加し、snapshotとcompletedはまだ存在しない。
実行中の処理を経過時間だけで再起動せず、既存制御で完了を待つ。

## 16:05 JSTのDGX第5バッチ回収と後続待機

DGX batch4の20群・1,760行を[回収照合](data_tile_validation_2026-10-17/c3t2_dgx_batch4_collection_observation_v1.json)で確認した。
archive本体182,556,456 byteのSHA256は `cb049ee68262efa84dc89a6ad939a3f8a455ec488b99df413b049942cd432bb3` で、assignment・config・terminal・report・parentの対応が一致した。
infrastructure failed 0、context failed falseであり、正式な回収済み件数はDGX 5/33バッチ・labo 1/5バッチ、計124/768群・10,912行となった。
既存DGX serialはbatch5のexport PID38816へ進み、実commandと生存を確認した。

qstat -u userの出力は空であり、この観測時点では所有者のクラスタジョブはなかった。
C3T1 indexのPID16732は継続中でCPU時間が増加しており、distributionと条件別finalの既存制御はその完了を待っている。
PCの全固定batch・768群を揃えるindexと後続の入力照合を省略して、部分集合の条件別集約を投入することはしない。
今後の条件別集約・全条件比較・独立計時にはqsubが残るため、この一時点の空キューをクラスタ作業全体の完了とは扱わない。

## 16:02 JSTのC3T2 full trace audit終了照合

job265494はF・Exit_status 0で終了し、実walltimeは12分14秒だった。
既存監視のfull-complete-completed.jsonとcompleted.jsonが作成され、PID28788は終了し、error.jsonは存在しなかった。
[終了照合](data_tile_validation_2026-10-17/c3t2_full_audit_completion_observation_20261023_v1.json)で実PBS履歴・封印済みterminal・qsub記録・native preflight・ローカル受理記録の対応を確認した。
summaryの全768群・92,160 taskと、各taskの保存checkpoint 19件、合計1,751,040件が固定manifestの予定件数と一致した。
全groupのstatusはok、failed_auditsとfailed_samplingは0、summaryとのgroup digest照合は全てtrueで、input_changesは空、context_errorはnullだった。
summaryのSHA256は `6b0ec6231d9b594c50da6febcc38cc725de9babc9a1231b96a95a950b9b57ca2`、terminalは `b65ec1da52806799f07fc59a5547aa3e9678e87d7459ab1c6946c973cd3fec83` である。

監査は全compact観測値と保存された初期状態・checkpointを対象とし、全物理状態の再復号やRNG軌道の完全再生ではない。
今回のobserverは監査summaryとgroup marker等の対応を照合し、raw trace payloadの再hashやdecoderの独立実装による検証はしていない。
監査の成功を混合・精度・被覆の保証として扱わず、scientific_validation_completeはfalseのまま保存した。
C3T2のsampling・collector・trace監査は完了し、PC解析の回収・条件別集約・全12条件比較・独立計時・最終報告は引き続き未完了である。
DGX batch4はlaunch-completedまで進んだが、collect-completedはまだ存在せず、正式回収件数にはまだ加えていない。

## 15:58 JSTの稼働確認と終了照合の準備

job265494はqstatでR状態を維持し、15:57の実walltimeは8分38秒だった。
DGX batch4のPID2268866、labo batch1のPID17684は実機上で生存し、両バッチのcompletionはまだ存在しなかった。
C3T1 indexのPID16732もCPU時間の増加を確認し、後続20制御プロセスの生存を確認した。
確認したC3T1/C3T2のindex・distribution・final制御とC3T2監査の11 journalにerror.jsonはなかったが、これは数値検証の成功を意味しない。

監査終了後に実PBS terminal・qsub記録・native preflight・全768群・92,160 task・checkpoint件数・受理記録を照合する[読み取り専用observer](data_tile_validation_2026-10-17/c3t2_full_audit_observer_v1/observe.py)を準備した。
保存sourceのSHA256は `9d65859d6a3888c6276990862cb49d239e0f730296a73c4bc36e1af405bf0a75` である。
今回の実行はR状態を観測して終了し、完了時の照合分岐はまだ未実施である。
既存の監査・解析・投入driverは変更せず、新たなジョブ投入や再計算はしていない。

## 15:49 JSTのC3T2 full trace audit開始

既存監視がfull auditのpreflightを完了し、[投入記録](data_tile_validation_2026-10-17/control_newline_recovery_v1/c3t2_collection8h_audit_handoff_v1/full-submit-completed.json)にqsubとjob265494を保存した。
qstatでjob265494のR状態、1 node・96 CPU・94 GB・walltime上限4時間を確認した。
実行worker数は96で、現在の要求node数は1であり、最大2nodeの制約を維持している。
collectorの終了・capacityの受理に続くfull trace監査の開始であり、監査完了や科学的な条件全体の受理とは扱わない。
C3T1 indexのPID16732とC3T2監視PID28788も生存を確認した。

## 15:40 JSTのfull audit資源計画とDGX第5バッチ開始

capacityの実測に基づく[full audit計画](data_tile_validation_2026-10-17/control_newline_recovery_v1/c3t2_collection8h_audit_handoff_v1/full-plan-completed.json)が完成し、96 worker・1 node・96 CPU・94 GB・walltime上限4時間となった。
native platformの確認とcapacity job265493への対応を含む計画であり、この時点ではpreflight中でqsub投入はまだ未実施である。
walltime上限を予想終了時刻と同一視しない。
DGX batch4はexport・転送確認・stageを終え、解析PID2268866の実稼働を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch4_start_observation_v1.json)で確認した。
正式な回収済み件数は104/768群のままであり、解析開始を完了件数へ加えない。

## 15:33 JSTのcapacity audit受理とDGX第4バッチ回収完了

capacity audit job265493は15:31:40 JSTにF・Exit_status 0で終了し、実walltimeは2分49秒だった。
既存監視は[終了記録](data_tile_validation_2026-10-17/control_newline_recovery_v1/c3t2_collection8h_audit_handoff_v1/capacity-complete-completed.json)を受理し、full trace auditの資源計画へ進んだ。
この時点ではfull auditはまだ未投入であり、capacityの成功を全trace監査の完了とは扱わない。

DGX batch3の20群・1,760行を回収し、archive本体182,182,443 byteのhash・size、割当、config・terminal・report・parentの対応を[回収照合](data_tile_validation_2026-10-17/c3t2_dgx_batch3_collection_observation_v1.json)で確認した。
infrastructure failed 0、context failed falseで、DGXは4/33バッチ、laboは1/5バッチ、計104/768群・9,152行の回収が完了した。
既存serialはbatch4のexport PID7312へ進み、実プロセスの生存を確認した。
条件全体の科学的な検証・精度・被覆の認定は未完了である。

## 15:29 JSTのC3T2クラスタ回収完了とcapacity audit開始

collector job265470は15:24:51 JSTにF・Exit_status 0で終了し、実walltimeは4時間50分52秒だった。
summaryのsample 92,160件・anchor 192件・768群・記録上の失敗0件と、索引92,352行を[終了照合](data_tile_validation_2026-10-17/c3t2_sampling_collection_completion_observation_20261023_v1.json)で確認した。
索引本体のhash、summary、worker-completion、封印済みPBS terminalとローカル受理記録の対応を照合し、[観測source](data_tile_validation_2026-10-17/c3t2_sampling_collection_completion_observation_20261023_v1.py)も保存した。
この追加観測ではraw payloadを再hashしておらず、full trace auditと科学的な条件全体の検証は未完了である。
追加観測scriptの初回はsummaryとworker-completionを同じhashと誤認してassertに失敗したため、既存workerの形式を読み直し、worker-completion内のsummary hashを介した対応へ修正して照合を完了した。
実計算や回収ジョブを再実行したものではない。

既存監視PID28788はcapacityのplan・preflightを完了し、qsubによるjob265493の投入記録と実際のR状態を確認した。
要求は1 node・96 CPU・340 GB・walltime上限24時間、実行worker数は8であり、現在の要求node数は1である。
capacityの結果が受理された後にfull trace auditの資源判定と投入が続く。
DGX batch3も解析完了記録を取得し、回収PID32064が稼働しているが、この時点では正式な回収済み件数に加えず84/768群のままとする。
C3T1 indexのcompleted.jsonはまだ存在しない。

## 15:06 JSTのC3T2 DGX第4バッチ開始

DGX batch3はexport・転送確認・stageを完了し、解析PID2211598の実稼働を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch3_start_observation_v1.json)で確認した。
回収済み件数は引き続き計84/768群であり、この解析開始を完了件数へ加えない。
C3T1 indexのPID16732も生存し、CPU時間は3995.5秒まで増加したが、completed.jsonはまだ存在しない。

## 14:59 JSTのC3T2 DGX第3バッチ回収完了

DGX batch2の20群・1,760行を回収し、archive本体182,623,295 byteのhash・size、割当、config・terminal・report・parentの対応を[回収照合](data_tile_validation_2026-10-17/c3t2_dgx_batch2_collection_observation_v1.json)で確認した。
infrastructure failed 0、context failed falseであり、DGXは3/33バッチ、laboは1/5バッチ、計84/768群・7,392行の回収が完了した。
既存serialは次のbatch3のexport PID42988へ進み、実プロセスの生存を確認した。
C3T1 indexのPID16732とlabo serialのPID46152も生存を確認した。
この件数は解析結果の回収・対応照合であり、条件全体の科学的検証や精度・被覆の認定ではない。

## 14:43 JSTのPC worker実稼働確認

DGX batch2は親PID2200028の子21プロセスを2時点で照合し、設定worker数と同じ20プロセスでCPU時間の増加を確認した。
約10秒の観測区間における1 core相当のCPU使用率は、この20プロセスで99.37〜99.97%だった。
labo batch1も親PID17684の子24プロセスすべてでCPU時間が増加し、約12秒の観測区間で1 core相当の92.65〜98.58%だった。
[DGXの観測値](data_tile_validation_2026-10-17/c3t2_dgx_worker_activity_20261023_v1.json)と[laboの観測値](data_tile_validation_2026-10-17/c3t2_labo_worker_activity_20261023_v1.json)を保存した。
親プロセスの生存だけでなく、割当済みworkerがCPU計算を進めていることを確認したものであり、OS間の性能比較や同精度までの独立計時ではない。
worker数や実行中の設定は変更していない。

## 14:34 JSTのC3T2 DGX第3バッチ開始

DGX batch2はexport・転送確認・stageを完了し、解析PID2200028の実稼働を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch2_start_observation_v1.json)で確認した。
回収済み件数は引き続き計64/768群であり、この解析開始を完了件数へ加えない。
labo batch1のPID17684とC3T1 indexのPID16732も直近の実プロセス確認で稼働中だった。

## 14:26 JSTのC3T2 DGX第2バッチ回収完了

DGX batch1の20群・1,760行を回収し、archive本体182,988,603 byteのhash・size、割当、config・terminal・report・parentの対応を[回収照合](data_tile_validation_2026-10-17/c3t2_dgx_batch1_collection_observation_v1.json)で確認した。
infrastructure failed 0、context failed falseであり、DGXは2/33バッチ、laboは1/5バッチ、計64/768群・5,632行の回収が完了した。
既存serialは次のbatch2のexport PID42752へ進み、実プロセスの生存を確認した。
この件数は解析結果の回収・対応照合であり、全条件の科学的検証や精度・被覆の認定ではない。
クラスタの途中索引は14:21の再観測で22,018,098 byte、mtime 14:19:58となり、14:20節で記録した更新停止から再び増加したことを確認した。

## 14:20 JSTの稼働再確認

DGX batch1のPID2142591とlabo batch1のPID17684は、各ホストの実プロセス一覧で生存を確認し、terminalはまだ存在しない。
C3T1 indexのPID16732も生存し、CPU時間は14:19の2482.69秒から2512.625秒へ増加した。
C3T2の新しい後続5プロセスと、全条件比較・独立計時・報告を待つプロセス群も生存を確認した。
C3T2の回収済み件数は引き続きDGX 1/33バッチとlabo 1/5バッチ、計44/768群であり、条件全体の検証は未完了である。
クラスタcollector 265470はqstatでRを確認し、CPU時間は03:25:05から03:26:56へ増加した。
一方、途中索引tasks.jsonlは14:10更新の20,969,762 byteのままで、summary.jsonはまだ存在しないため、索引の件数だけで進行段階や完了時刻を断定しない。
PBSの指定出力先にはpartition.outとpartition.errがまだ存在せず、実行中ログによる追加確認はできなかった。
現時点では稼働確認付きの待機とし、途中索引が更新されないことだけを理由に再実行しない。

## 14:01 JSTのC3T2 DGX次バッチ開始

DGXのbatch1はexport・転送確認・stageが正常に完了し、本解析PID2142591の実稼働を[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch1_start_observation_v1.json)で確認した。
両PCは2つ目のバッチを解析中で、回収済み件数は44/768群のままである。

## 13:54 JSTのC3T2両PC最初のバッチ回収完了

DGXは1/33バッチ、laboは1/5バッチの回収を完了し、C3T2の回収済み件数は計44/768群・3,872行となった。
DGXのarchive本体182,419,618 byteのhash・size、割当20群・1,760行、config・terminal・report・parentのhashを[回収照合](data_tile_validation_2026-10-17/c3t2_dgx_batch0_collection_observation_v1.json)で確認した。
infrastructure failed 0、context failed falseである。
DGXは次のbatch1のexport PID44812へ進み、laboはbatch1の本解析PID17684が実稼働していることを[開始観測](data_tile_validation_2026-10-17/c3t2_labo_batch1_start_observation_v1.json)で確認した。
この件数はPC解析の回収進捗であり、全条件の科学的検証や精度・被覆の認定ではない。

## 13:51 JSTのC3T2 DGX最初のバッチ解析完了

DGXのC3T2 batch0は20群すべてがstatus okとなり、1,760行の解析を報告して正常終了した。
terminalと起動・終了記録を照合し、[解析完了の観測](data_tile_validation_2026-10-17/c3t2_dgx_batch0_analysis_completion_observation_v1.json)に保存した。
既存serialが回収へ進み、回収PID33784の実稼働を確認した。
この時点ではarchive回収・ローカル照合は未完了であり、DGXの回収済みバッチ数にはまだ加えない。
laboは次バッチのexport PID26044で入力準備を継続している。

## 13:45 JSTのC3T2 labo最初のバッチ回収完了

laboのC3T2は1/5バッチの回収を完了した。
24群・2,112行の回収記録と割当の一致、archive本体219,296,960 byteのhash・size、埋め込まれたconfig・terminal・report・parentのhashを照合した。
infrastructure failed 0、context failed falseであり、結果は[回収照合記録](data_tile_validation_2026-10-17/c3t2_labo_batch0_collection_observation_v1.json)に保存した。
既存serialが次のbatch1のexportを開始し、PID26044の実稼働を確認した。
DGXは最初のバッチを解析中で、クラスタ回収job265470もR・経過3時間10分で稼働している。
回収完了を精度・被覆や条件全体の検証完了とは扱わない。

## 13:40 JSTのC3T2 labo最初のバッチ解析完了

laboのC3T2 batch0は24群すべてがstatus okとなり、2,112行の解析を報告して正常終了した。
最初のバッチの受理済みterminalは取得済みであり、[解析完了の照合](data_tile_validation_2026-10-17/c3t2_labo_batch0_analysis_completion_observation_v1.json)に保存した。
回収プロセスPID48832が起動し、13:43時点ではarchive回収・ローカル照合は未完了である。
バッチ解析の終了を条件全体の校正や精度・被覆の認定とは扱わない。

## 13:30 JSTのDGX本解析開始と報告集計レビュー

復旧後のDGX parityとstageが完了し、C3T2 batch0の本解析PID2131609が稼働していることを確認した。
parity受理記録と14入力のhash、実行configのhashを照合し、[開始観測](data_tile_validation_2026-10-17/c3t2_dgx_batch0_start_observation_20261023_v1.json)に保存した。
最終報告の配備済み5 module・8関数を読み直し、全192 seedの分母、欠測と失敗の保持、referenceなしの評価不能扱いが保たれていることを確認した。
詳細は[集計規則の追加レビュー](low_report_scientific_contract_review_2026-10-23_ja.md)に保存し、稼働中のsourceは変更していない。
独立BAR計時の診断placeholderを実測不合格件数と読まないこと、点推定RMSEの時間比を区間被覆の保証と読まないことも明記した。
実データの全12条件集計と最終報告は未完了である。

## 13:23 JSTのC3T2 DGXと後続経路の復旧

DGXのC3T2は13:09に転送後のhash確認SSHがタイムアウトして停止したが、転送済み14ファイルの一致と旧プロセスの不存在を確認して復旧した。
元の停止記録・入力・科学helperを保持し、再転送やsamplingのやり直しは行っていない。
復旧serial PID5212でparityを開始し、DGX実プロセスPID2127569の稼働を確認した。
依存して停止したindex・distribution・最終準備・最終実行・最終回収の5待受も、別の記録先へ接続して実稼働を確認した。
受入は入力側12件・後続側9件が成功し、詳細は[復旧結果](c3t2_dgx_recovery_result_2026-10-23_ja.md)に保存した。
laboのC3T2 batch0 PID23488、C3T1 index PID16732、C3T2クラスタcollectorの待受PID28788も稼働中である。
全条件比較・独立計時・最終報告は引き続き未完了である。

## 13:01 JSTのC3T1 PC回収完了と後続開始

C3T1 DGXは13:00:28に33/33バッチの回収を完了し、laboの5/5バッチと合わせて両PCの割当分が回収済みとなった。
最新batch32のarchive本体67,367,831 byteのhash・size、config・terminal・reportのhash、および33件のserial完了記録からtransfer記録へのhashを照合した。
最後のバッチは8群・704行、infrastructure failed 0、context failed falseである。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch32_collection_observation_v1.json) に保存した。
C3T1の索引driverがregistryを保存し、後続のindex処理を開始した。
DGXのC3T2 serial PID31264と最初のexport PID22752が起動した。
laboのC3T2 batch0とクラスタcollector job265470は引き続き稼働中である。
PC回収完了を条件全体の科学的な校正完了とは扱わず、C3T1の集約・監査とC3T2の解析を継続する。

## 12:46 JSTのDGX回収進行

C3T1 DGXは32/33バッチを回収済みとなった。
最新batch31のarchive本体168,215,898 byteのhash・size、config・terminal・reportのhash、および32件のserial完了記録からtransfer記録へのhashを照合した。
回収記録は20群・1,760行、infrastructure failed 0、context failed falseである。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch31_collection_observation_v1.json) に保存した。
既存serialが最後のbatch32のexportを開始し、その実プロセスPID47928を確認した。
laboのC3T2 batch0とクラスタcollector job265470は引き続き稼働中である。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 12:16 JSTのDGX回収進行

C3T1 DGXは31/33バッチを回収済みとなった。
最新batch30のarchive本体167,626,691 byteのhash・size、config・terminal・reportのhash、および31件のserial完了記録からtransfer記録へのhashを照合した。
回収記録は20群・1,760行、infrastructure failed 0、context failed falseである。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch30_collection_observation_v1.json) に保存した。
既存serialが次のbatch31のexportを開始し、その実プロセスPID8440を確認した。
laboのC3T2 batch0とクラスタcollector job265470は引き続き稼働中である。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 11:48 JSTのDGX回収進行

C3T1 DGXは30/33バッチを回収済みとなった。
最新batch29のarchive本体168,040,878 byteのhash・size、config・terminal・reportのhash、および30件のserial完了記録からtransfer記録へのhashを照合した。
回収記録は20群・1,760行、infrastructure failed 0、context failed falseである。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch29_collection_observation_v1.json) に保存した。
既存serialが次のbatch30のexportを開始し、その実プロセスPID25580を確認した。
laboのC3T2 batch0とクラスタcollector job265470は引き続き稼働中である。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 11:28 JSTのlabo C3T2解析開始

laboのC3T2環境間一致確認はreplay_verified trueで完了し、serial完了記録とaccepted記録のhash、およびaccepted記録が参照するlocal input 14件のhashを照合した。
laboのC3T2 batch0はremote PID23488、DGXのC3T1 batch29はremote PID1986852の生存とterminal未取得を確認した。
クラスタのcollector job265470もRを確認した。
[起動観測記録](data_tile_validation_2026-10-17/c3t2_labo_start_observation_20261023_v1.json) に保存した。
この一致確認は固定入力の再現確認であり、科学的な校正完了とは扱わない。

## 11:19 JSTのDGX回収進行

C3T1 DGXは29/33バッチを回収済みとなった。
最新batch28のarchive本体のhash・size、configとreportのhash、29件のserial完了記録からtransfer記録へのhashを照合した。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch28_collection_observation_v1.json) に保存した。
既存serialが次のbatch29のexportを開始し、その実プロセスPID24004を確認した。
laboのC3T2は環境間の一致確認プロセスPID8096が継続中で、解析バッチの起動はまだ確認していない。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 10:58 JSTのC3T2 native reference回収

native reference job265469は10:56:00に終了コード0、実行時間22分24秒で終了した。
接続済みdriverが結果を回収し、reference_ready trueの完了記録を保存した。
accepted記録からhandoffへのhash、archive本体、付随5ファイルとsource inputのhashを[照合記録](data_tile_validation_2026-10-17/c3t2_native_reference_collection_observation_20261023_v1.json)に保存した。
labo側C3T2のserial PID46152と最初のexport PID13128が起動し、実プロセスの生存を確認した。
DGX側はC3T1の29番目がPID1927824で解析中で、C3T2の解析開始はまだ確認していない。
native referenceの回収時点ではPC parity未実施であり、科学的な校正完了とは扱わない。
collector job265470は引き続き実行中である。

## 10:49 JSTのDGX回収進行

C3T1 DGXは28/33バッチを回収済みとなった。
最新batch27のarchive本体167,710,812 byteのhash・size、configとreportのhash、28件のserial完了記録からtransfer記録へのhashを照合した。
回収記録は20群・1,760行、infrastructure failed 0、context failed falseである。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch27_collection_observation_v1.json) に保存した。
既存serialが次のbatch28のexportを開始し、その実プロセスPID36968を確認した。
クラスタのnative reference job265469とcollector job265470は10:48時点でRを確認している。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 10:35 JSTのC3T2 sampling完了と後続起動

p=0.001の後半sampling job265462は10:33:07に終了コード0で完了し、実行時間は8時間31分21秒だった。
前半・後半ともsummaryはcomplete true、success、46,080 task、failed 0、missing 0で、合計92,160 taskの生成完了が記録された。
両summaryのhashとPBS状態を[完了観測記録](data_tile_validation_2026-10-17/c3t2_sampling_completion_observation_20261023_v1.json)に保存した。
接続済みのdriverがqsubでnative reference job265469とcollector job265470を投入し、両方のRを確認した。
それぞれ要求1node・1CPU・32GBで、観測時の所有者ジョブはこの2件のみだった。
DGXはC3T1の28番目を解析中で、C3T2のPC解析はnative referenceを待つ。
samplingの正常終了を最終校正完了とは扱わず、C3T2の回収・監査・BAR解析と全条件比較を継続する。

## 10:19 JSTのDGX回収進行

C3T1 DGXは27/33バッチを回収済みとなった。
最新batch26のarchive本体168,037,931 byteのhash・size、configとreportのhash、27件のserial完了記録からtransfer記録へのhashを照合した。
回収記録は20群・1,760行、infrastructure failed 0、context failed falseである。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch26_collection_observation_v1.json) に保存した。
既存serialが次のbatch27のexportを開始し、その実プロセスPID28896を確認した。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 09:51 JSTのDGX回収進行

C3T1 DGXは26/33バッチを回収済みとなった。
最新batch25のarchive本体167,414,158 byteのhash・size、configとreportのhash、26件のserial完了記録からtransfer記録へのhashを照合した。
回収記録は20群・1,760行、infrastructure failed 0、context failed falseである。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch25_collection_observation_v1.json) に保存した。
既存serial PID45416が次のbatch26のexportを開始し、その実プロセスPID45892を確認した。
クラスタjob265462は引き続きRである。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 09:22 JSTのDGX回収進行

C3T1 DGXは25/33バッチを回収済みとなった。
最新batch24は20群・1,760行で、serial完了記録とtransfer記録、167,390,533 byteのarchive本体のhash・sizeを照合した。
[回収照合記録](data_tile_validation_2026-10-17/c3t1_dgx_batch24_collection_observation_v1.json) に保存した。
既存serial PID45416が次のbatch25のexportを開始し、その実プロセスPID33724を確認した。
この確認は回収物の一致であり、科学的な収束や精度の認定ではない。

## 09:13 JST頃のC3T2生成記録確認

p=0.001のtrace保存先で、manifestから構成した92,160 taskの完了marker名が全て存在し、欠落・余分なmarker名が0件であることを確認した。
[観測記録](data_tile_validation_2026-10-17/c3t2_sampling_marker_observation_20261023_v1.json) を保存した。
前半partitionは46,080 task・failed 0・successのsummaryが存在するが、後半partitionのsummaryはまだ存在せず、job265462はR・経過7時間11分だった。
実行中sourceはlocalとremoteで同じSHA256であり、並列生成後に全成果物のhashとrecordを照合してからsummaryを書く処理がある。
全marker名の存在は確認したが、実行中の正確な処理位置を調べたわけではなく、payloadの完全性・後半partitionの成功・科学的検証完了をこの観測で認定しない。
PBSの指定stdout・stderrは共有保存先にまだ存在せず、そのことを停止や失敗とは判定していない。
後続の正式な回収・監査・解析を引き続き待ち、全低ノイズ条件の検証完了数は10/12のままとする。

## 09:03 JSTの改行変換防止

停止原因となった仕様書1ファイルに.gitattributesのtext eol=lfを追加した。
隔離したGit作業領域で、core.autocrlf=trueの修正前checkoutが観測済みCRLF版を再現し、修正後checkoutは元のLF版のhashを保持することを確認した。
稼働中の入力バイト列を変更せず、commit・pushも行っていない。
詳細は [復旧報告の追記](control_newline_recovery_result_2026-10-23_ja.md) に保存した。

## 09:00 JSTの後段接続確認

[復旧した転送完了記録への接続](recovered_distribution_binding_result_2026-10-23_ja.md) で、C3T1算術検証のdistribution_doneが古い転送待受を指していた1箇所を修正した。
検証処理が未実行の旧待受PID3756だけを停止し、新PID40984の実稼働を確認した。
受入4件が成功し、両条件の実intentと算術検証・candidateの参照先の一致を確認した。
元の科学設定・数値計算・qsub制約は維持している。
残る2条件の最終集約、全条件比較、独立計時、最終報告は継続中である。

## 08:56 JSTの制御経路復旧

[仕様書の改行差分からの復旧](control_newline_recovery_result_2026-10-23_ja.md) を完了した。
C3T1 laboの正常な回収完了後に親のhash検証が停止し、索引・転送・最終集約にも停止が伝播していた。
固定仕様書のCRLFからLFへの復元は本文を変更しないが、CRLF版を固定していたC3T2待受4件にも停止を起こしたため、それらも明示的な証拠照合を経て接続し直した。
停止記録を保持し、10件の復旧待受を起動した。
指定24プロセスの実稼働と復旧intentの848ファイルを確認し、不一致は0件だった。
復旧制御の受入は20 passed・3.59秒であり、samplingやPC数値計算の再投入はしていない。
クラスタjob265462はR・1要求node・経過6時間53分、DGXのC3T1は24/33バッチを回収済みである。
残る2条件の最終集約、全条件比較、独立計時、最終報告は未完了である。

## 08:16以降のlabo回収完了

laboのp=0.003担当分は全5バッチの回収を08:16 JSTに完了した。
[回収記録とarchiveの照合](data_tile_validation_2026-10-17/c3t1_labo_collection_observation_20261023_v1.json) で、全5件の記録のhash、archiveのhashとsize、計画行数と回収行数の一致を確認した。
担当分は120群・10,560行で、回収記録上のinfrastructure失敗は0群だった。
この確認を精度・被覆の認定とは扱わず、p=0.003全体の最終集約はDGXの残りの解析を待つ。
DGXは23番目／33バッチを実行中で、クラスタjob265462のp=0.001 samplingも継続している。
laboの次条件p=0.001を待つPID49424が、該当するcommand lineで実稼働していることを確認した。

## 07:44 JSTの実行状態

[稼働観測と回収記録の照合](data_tile_validation_2026-10-17/runtime_observation_20261023_0744_v1.json) を保存した。
所有者のactive cluster jobは265462の1件で、R・96 CPU・1要求node、scheduler報告の経過時間は5時間41分12秒だった。
DGXのp=0.003解析は21バッチの回収済み記録と参照先hashの一致を確認し、22番目／33バッチのPID1704721が実稼働している。
laboは最後の5番目のバッチをPID6732で実行中である。
この照合は実行状態と回収記録の確認であり、数値結果の科学的な再検証ではない。
残る2条件の最終集約、全条件比較、独立計時、最終報告は未完了であり、goalは継続中である。

## 06:29 JSTの公開候補と実行状態

[公開候補のRelease本文](publication_candidate_status_2026-10-23_ja.md) の公開済みという誤記を訂正し、同一bytesのsource ZIP・wheelと新しいchecksum manifestを用意した。
GitHubはPRIVATE・Release0件であり、今回も公開操作は行っていない。
remote mainは `55cd5998`、公開候補tagは `e7e5239f` で、差分は文書159ファイルのみだった。
mainのCI run39778387464はsuccessである。
06:26 JST時点のsampling job265462はR・96 CPU・1要求nodeで、DGXはp=0.003の19番目のバッチを回収中、laboは最後のバッチを解析中だった。
全条件の入力準備は10/12のままである。

## 06:25 JSTの報告経路更新

[分割集約から最終報告までの接続](low_partition_report_result_2026-10-23_ja.md) を実装し、修正版v2の準備PID30784・実行PID47980を稼働確認した。
報告環境と元merge環境のimport元が衝突する問題を、元環境の別プロセスで検証して証拠を親へ引き継ぐ形で修正した。
最初の報告待受v1は、remote準備・投入前の待機中に停止し、記録を保持している。
分割専用の待受は最終報告の回収まで接続済みだが、本番の分割flow・独立計時・報告jobはまだ未実施である。
実際の数値計算と報告内容のレビューが終わるまで、検証完了とは扱わない。
独立計時の準備PID19316・実行PID27136も継続稼働を確認した。
この更新で、以下の時点にある最終報告側の未接続を解消した。

## 06:11〜06:12 JSTの接続更新

[分割seed censusの準備・実行待受](low_timing_partition_census_wait_result_2026-10-23_ja.md) と、[独立計時の準備・実行待受](low_timing_partition_independent_result_2026-10-23_ja.md) を接続した。
censusのPID41028・36092、独立計時のPID19316・27136をcommand line付きで実稼働確認した。
独立計時の追加接続はWindows50件とLinux38件の制御試験に成功した。
数値計時は未開始であり、この接続による新しいqsub投入もまだない。
通常経路が選ばれた場合は分割専用待受が投入せず終了する。
最終報告側に分割mergeの受理証拠を検証する接続が残る。
以下の05:54〜06:00時点にあるseed census未接続の記述は、この更新で解消した。

## 05:54〜06:00 JSTの確認

低ノイズ条件の検証作業は10/12条件が完了し、残りはtile288 depolarizingのp=0.003・p=0.001である。
新しく完了したp=0.01の[結果報告](low_c3t0_result_2026-10-23_ja.md)と29ファイルの追加照合を保存した。
全352設定・各192 seedを保持したが、長い16設定の全seedに診断flagと未定義項目があり、20%・10%精度gateも未達だった。
正式な検証作業の完了数を、精度や名目95%被覆の認定とは扱わない。

| 処理 | 実確認した状態 |
|---|---|
| p=0.01最終集約 | job265459が正常終了、独立再集計と回収物照合まで完了 |
| p=0.003回収 | job265457がF・exit 0、実walltime3時間51分32秒 |
| p=0.003監査 | capacity・full監査の受理記録あり、PC解析と最終集約は未完了 |
| p=0.001 sampling前半 | job265448がF・exit 0、実walltime8時間34分57秒 |
| p=0.001 sampling後半 | job265462がR、経過3時間52分、96 CPU・1要求node |
| 全12条件の集約準備 | inventory10/12、準備待受PID46024と切替待受PID45920が実稼働 |

所有者の全active jobをqstatで照会し、265462の1job・1要求nodeだけが稼働していた。
前の2jobが終わっても後続sampling・解析・監査・最終集約・独立計時は残る。
クラスタ投入は引き続きqsub・最大2要求nodeとする。

[通常経路と分割経路の切替待受](low_timing_partition_route_guard_result_2026-10-23_ja.md)を接続済みであり、通常経路が資源上限超過で未投入のまま終了したことを確認した場合だけ分割flowへ進む。
分割flowの本番起動、seed census接続の本番待受への組込み、独立計時、最終報告は未完了である。
公開候補の配布物準備と数値検証の完了を区別し、この確認では公開操作・commit・pushを行っていない。
前日の経緯と公開候補の証跡は [10月22日の状態](PROJECT_STATUS_2026-10-22_ja.md) を参照する。
