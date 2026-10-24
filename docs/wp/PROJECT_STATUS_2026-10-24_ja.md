# mcmc4qec：2026-10-24の継続状態

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
