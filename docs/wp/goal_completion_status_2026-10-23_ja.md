# Goalの完了条件と確認済み範囲

## 2026-10-25 10:13 JSTの本番後処理再開

実設定の組立265698と13通りの実constructor確認265699はF/0となり、loginでのreadinessと起動previewを経て、後続専用v13 controllerを起動した。
別SSHでPID1598334・start ticks770092111・command一致、生存とerrorなしを確認し、最初のcensus準備265700はR・run_count=1・walltime10秒だった。
元12worker・merge265660・acceptance265661の計14ジョブ、全12条件comparisonとhandoffを保持し、元計算は再実行していない。
全件census、独立計時48行と各192分母、最終reportと科学証拠・再現手順の統合保存は未完了であり、goalは未完了のままとする。
小原本と受入範囲は[接続受入記録](tail_census_resume_acceptance_2026-10-25_ja.md)、現行source・config・確認手順は[再起動手順](cluster_resident_resume_2026-10-25_ja.md)の最新節に固定する。
処理はクラスタ内で継続でき、ローカル接続の維持は不要だが、観測timeoutだけを理由に停止や再投入を判断しない。
全体ETAは未定であり、以下の停止・準備記録は当時の履歴として保持する。

## 2026-10-25：資源実測完了後の残工程

元12worker・merge265660・acceptance265661・全12条件comparison・handoffの受理は完了済みで、これらを再計算せず後続処理へ再利用する。
[資源実測265678](census_measurement_submission_2026-10-25_ja.md)はF/0・run_count=1・walltime5分56秒で完了した。
予定4,208,002件のうちpilot1,000件でunexpected collisionは0だったが、全件censusは未実施である。
今回の実測では元式の候補16 GiB・45分に対して旧メモリ上限4 GiBのみが超過したが、265675で保存されなかった測定値を復元した結果ではない。
運用割当1 CPU・96 GiB・4時間の資源設定、専用環境への接続、後続だけを再開する制御処理を修正・検証中で、本番後処理は停止している。
この割当は予算枠であり、全体の終了時刻予測ではない。

残工程は修正版の接続受入とqsubによる再開、全件seed照合、独立計時48行と各192分母の評価、最終reportと科学証拠・再現手順の保存である。
未実行・非選択・未定義診断・区間未取得も理由付きで記録し、独立referenceのない領域の整合性を精度や被覆の保証としない。
goalは未完了であり、以下の時刻付き観測と状態表は過去時点の記録として保持する。

## 2026-10-25 09:29 JSTのcensus準備停止

有限tail265675はF/1・run_count=1・walltime13分32秒・CPU時間13分24秒・PBS記録mem15,084,044KBで終了し、v12 controllerのPID1432966は不在となった。
1,000件pilotはcollision=0で完了したが、計測値の保存前に `measured census exceeds two-hour / four-GiB ceiling` で資源計画が拒否された。
時間・メモリの個別超過と実predictionは未確定で、先行bundle検証を含むpeak selfRSSの影響を調査し、PBS記録memとの一致は仮定しない。
census rootは `root_reusable:false` で、catalog・manifest・prepare受理記録はなく、科学bundleとconfigを保持して新計画を準備する。
元12worker・merge265660・acceptance265661・全12条件comparison・handoffの受理は維持し、元計算は再実行していない。
失敗の小証跡はlocal `output/low_parallel_flow_v11/census-failure-readonly.json` に保存した。
[v12復旧差分保存](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)265676はF/0で完了したが、独立計時48行と各192分母、最終report、最終科学証拠の統合保存は未完了である。
goalは未完了、全体ETAは未定で、以下の稼働観測は履歴として保持する。

## 2026-10-25 09:15 JSTのv12再開と比較受理・handoff

元merge265660・acceptance265661・全12workerの成功原本を再実行せず採用するv12 controllerを起動し、別SSHでPID1432966・start ticks769736422・command一致、生存・errors空を確認した。
native265673とtail265674はF/0で、実constructor・login roundtripと[独立レビュー](cross_host_artifact_stat_review_2026-10-25_ja.md)を完了した。
固定したnamespace authorityに限定してdevice差を扱い、元proof・content hash・source・旧stat失敗記録を保持する。
comparison本文の `all_twelve_processed=true` とhandoff本文の完了flagsを確認し、元265660・265661への結合を保持して後段へ進んだ。
初回の有限tail265675は09:15:07 JSTにRで、census準備の実行中である。
独立計時48行と各192分母、最終report、最終証拠保存は未完了で、`independent_timing_performed=false`・`nominal_coverage_certified=false` を維持する。
新controllerの生存やfixture・constructor成功をgoal完了とせず、全体ETAは未定とする。
以下のv11停止記録は当時の履歴であり、旧controllerは再起動しない。

## 2026-10-25 08:49 JSTのPBS成功と統合受理停止

本番merge265660とacceptance265661はともにF/0・run_count=1で、それぞれwalltime1時間58分44秒・2分37秒、CPU時間3時間19分30秒・2分31秒だった。
acceptance completionは `original_accept_terminal_executed=true` とPBS内のproduction selection生成を記録するが、controllerによる統合受理・handoffは未完了である。
v11 controllerは `Previously PBS-verified artifact stat changed` を検出して停止し、PID1145733不在・`automatic_retry=false` を確認した。
独立検査では4artifactの差はhost-localなdevice番号だけで、inode・size・mtime_ns・ctime_ns・modeと通常file・非symlinkの条件は一致していた。
元worker・merge・acceptanceの原本を保持してobserver移行を準備し、重い集約・元workerの再投入や旧controllerの再起動は行わない。
[v11差分保存](finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md)265662は8fixtureと実採取に成功したが、そのscopeに最終科学result・後続proofは含まれない。
独立計時・最終報告・最終証拠の統合保存は未完了で、PBS正常終了をgoal完了へ読み替えず、全体ETAは未定とする。
以下の記録は当時の履歴として保持する。

## 2026-10-25 06:45 JSTの本番集約再開

後段worker受理のalias修正・実12件の値読込直前までの確認・新mergeへの後続設定・controller引継ぎをqsubで検証した。
新v11 controllerは元12workerの正常終端を採用し、新rootへ集約265660をqsubで投入した。
別SSHでcontrollerの起動識別情報一致とerrorなし、集約R・run_count=1・walltime26秒・CPU時間47秒を確認した。
失敗した265651と元worker記録は保持し、worker計算の再投入は行っていない。
全12条件の深い受理・正式selection・独立計時・最終報告は未完了であり、goalは未完了、全体ETAは未定である。

## 2026-10-25 06:30 JSTの本番集約異常終了

集約265651はR確認後にF/1・walltime6秒で終了し、v10 controllerも停止した。
準備段階の照合は修正済みだが、後段の元worker受理内で`selector closure differs from environment`を検出した。
完了済み12workerと失敗した集約記録を保持し、実受理経路の追加修正と受入を進める。
全12条件の深い受理・正式selection・独立計時・最終報告は未完了であり、goalは未完了、全体ETAは未定である。

## 2026-10-25 06:29 JSTの本番集約再開

alias照合の修正は25件と実request/nativeの受入を通過し、controller引継ぎも18件と実設定/nativeの受入を通過した。
新v10 controllerは全12件の正常終端を再利用し、本番集約をqsub265651へ投入した。
実ジョブR・run_count=1・8CPU・32GiBとcontrollerの生存・errorなしを確認した。
全12条件の深い受理・正式selection・独立計時・最終報告は未完了であり、goalは未完了、全体ETAは未定のままとする。

## 2026-10-25 06:16 JSTの集約準備停止

全12workerがF/0となり、v9 journalに12件のterminalを回収した。
集約準備で`Parent scientific selector closure differs`を検出し、controllerは終了、集約ジョブは未投入である。
科学コードの参照と実行環境の不一致を調査し、完了済みworkerを保持する復旧案を並列レビューしている。
全12条件の深い受理・集約・独立計時・最終報告は未完了であり、goalは未完了、全体ETAは未定のままとする。

## 2026-10-25 05:38 JSTの確認

index10の265591がF/0・run_count=1で終了し、全12worker中11件が正常終了した。
v9 controllerの生存・起動識別情報一致・errorなしとterminal11件の採用を確認し、残る265592はR・run_count=1だった。
全件終端後の深い結果受理・集約・独立計時・最終報告は未完了であり、goalは未完了のままとする。
全体ETAは未定であり、PBS正常終了を科学的受理の完了とは扱わない。

## 2026-10-25 04:38 JSTの確認

index9の265590がF/0となり、全12worker中10件が正常終了、残る265591・265592はRである。
v9 controllerの生存・起動識別情報一致・errorなしとterminal10件の採用を確認した。
元workerを再投入せず、全12件の終端後に本番の深い受理・集約・独立計時へ進む構成を維持する。
最終completedは未作成であり、全体ETA未定・goal未完了の扱いを維持する。

## 2026-10-25 04:25:56 JSTの稼働と追加保存

v9 controllerの生存・起動識別情報一致、terminal9件、errorなしを再確認した。
残る265590・265591・265592はRで、各walltime約2時間50分・CPU時間約2時間22分だった。
切替後のsource参照1,336件・metadata179件を[private snapshot](finite_flow_v9_snapshot_acceptance_2026-10-25_ja.md)へ保存し、qsub265646のF/0と9fixture成功を確認した。
保存した範囲は現在のcontrol・受入・起動証拠であり、今後生成される本番merge・独立計時・最終報告の証拠は含まない。
旧v8共有候補は保持し、v9保存物の公開・配布、科学工程の完了とは区別する。
全体ETAは未定であり、goalは未完了のままとする。

## 2026-10-25 04:18:38 JSTのv9切替確認

旧v8 controllerをworker待機中に停止して旧process不在を確認し、native constructor265644のF/0に結合したv9 controllerを起動した。
別SSH接続で新processの生存・起動識別情報一致、errors空、indices 0〜8のterminal9件の採用、completed未作成を確認した。
残る3workerは実行中で、後段の実科学payload・全12条件の深い受理・独立計時・最終報告は未完了である。
クラスタ常駐処理はローカル接続を必要とせず、[再起動後の確認先](cluster_resident_resume_2026-10-25_ja.md)をv9へ更新した。
本番controllerの切替完了と全科学工程の完了を区別し、新control差分・最終証拠の保存も含めgoalは未完了、全体ETAは未定とする。
以下の切替前の記録は当時の履歴として保持する。

## 2026-10-25 04:11:16 JSTの確認

全12workerは9件F/0・3件Rで、index 5の265589はwalltime2時間24分54秒・CPU時間2時間13分44秒で正常終了した。
残るindices 9・10・11の265590・265591・265592は実行中で、全12条件の深い受理・正式比較・独立計時・最終報告は未完了である。
現行v8から新版への本番切替は未実施、goalは未完了、全体ETAは未定のままとする。
[動的配置](dynamic_physical_aux_acceptance_2026-10-25_ja.md)の31fixtureと科学payloadなしの実補助CLI、[report環境](finite_tail_effective_acceptance_2026-10-25_ja.md)の26fixture・実bootstrap/source closure・設定validator照合、[265641の結合95fixture](finite_tail_outer_review_2026-10-25_ja.md)は成功した。
これらは本番全role constructor、稼働science childとの実共存、全科学解析・最終reportの完了を示さない。
[明示ladder CLI受入](tile_example_target_cli_acceptance_2026-10-25_ja.md)により任意目標への接続例は追加したが、正式selection・低ノイズの推奨設定や精度保証は未提供のままである。
新control差分と最終証拠の保存・利用者向け再現資料の整備も残っており、v8共有候補の保存や小規模受入をgoal完了へ読み替えない。
以下の記録は当時の観測として保持する。

## 2026-10-25 03:51 JST以降の確認

全12worker中8件がF/0、残るindices 5・9・10・11の4件がRで、現行v8 controllerは生存・errorなしだった。
後段を有限PBS処理へ分ける[96fixtureと実CLIの受入](finite_tail_fixture_acceptance_2026-10-25_ja.md)を完了したが、科学環境を含む全経路の統合受入はまだ終わっていない。
計時jobの固定先なし配置と補助jobの[容量境界](finite_tail_unbound_capacity_audit_2026-10-25_ja.md)も対応中であり、本番controllerの切替は未実施である。
保存済みv8の[共有候補の限定的な独立レビュー](share_snapshot_v8_candidate_review_2026-10-25_ja.md)を完了し、候補は未公開で保持した。
全12条件の正式比較・独立計時・最終報告の完成、新しいcontrol差分と最終証拠の保存は残っており、goalは未完了である。

## 2026-10-25の追加保存と後段処理の監査

03時12分JSTの実確認では全12worker中7件がF/0、残る5件がRで、v8 controllerは起動識別情報一致・生存・errorなしだった。
現行v8のsource1252参照・metadata112件を[private snapshot](reproduction_snapshot_v8_acceptance_2026-10-25_ja.md)として保存し、公開main・固定Release・private資料・生データの[取得監査](reproduction_access_inventory_2026-10-25_ja.md)を行った。
共有用archive exporterの専用26fixtureはqsub265618で成功したが、実archiveの生成・共有可能性の確認は別工程として進めている。
生成済み7workerのvalues.jsonはstat確認だけでも合計1,196,553,264 bytesであり、merge後のaccept_terminalとtail管理経路が巨大JSONを非PBSの常駐側でparse・複製・検証する問題を確認した。
後段の重い検証をqsubへ隔離する新版を準備しており、この確認時点では稼働中v8・worker・完了済み原本を変更していない。
全12条件の正式比較・独立計時・最終報告は未完了であり、private snapshotやfixtureの成功を代用しない。

## 2026-10-25 02:50:38 JSTの最新確認

v8 controllerは別のSSH接続で起動識別情報・全commandの一致と生存を確認し、error記録なし・stderr 0バイトだった。
indices 1・2・6・7・8の5件はF/0でterminal回収済み、残るindices 0・3・4・5・9・10・11の7件はRだった。
新index 0の265605を含む構成で常駐を再開し、他11件の実行証跡を保持して、このPCの接続には依存しない。
parallel merge・tail・flowの受入と実環境確認は成功したが、全12条件の深い結果受理・本番merge・独立計時・最終報告は未開始である。
goalは未完了であり、旧ETAの撤回と比較・全体ETA未定の扱いを維持する。
以下のcontroller停止・未再開などの記録は過去時点の履歴として保持する。

## 2026-10-25 02:22 JSTの最新確認

新index 0はqsub265605で投入済みとなり、新しい照会でR・walltime2分31秒・CPU時間2分20秒だった。
親execution・子reader intent/handleは存在し、execution-errorはないが、完了・結果受理は未確認である。
旧265564のF/-29を保持し、他の8件はR、3件はF/0である。
native265602・policy265603・shadow265604は正常終了したが、実controllerはまだ起動せず、後段の常駐処理は未再開である。
hash core265606の18fixture×2はF/0で、完全なmerge統合受入と性能は未確認のため、その受入後に新しいv7 controllerを起動する準備を進める。
private v5 snapshotはsource1031参照・metadata75件・参照edge19692件を保存したが、v6差分・最終証拠は未追加である。
goalは未完了、比較・全体ETAは未定とし、以下の未投入などの記録は各時点の履歴として保持する。

## 2026-10-25 02:01:52 JSTのwalltime超過後

index 0の265564は要求65分を超えてF/-29となり、実walltime66分28秒・CPU時間32分12秒だった。
旧flow v5はerrorで終了し、controllerの不在を確認した。
他の11件は3件F/0・8件Rとして保持し、index 0だけを4時間上限で再実行するfront v6を準備中だが、まだ投入していない。
dispatcher265598の13テストとflow265600の54テストはF/0で、新native準備とmerge受入は未完了である。
比較の旧07〜10時JST予測も撤回し、比較・全体ともETAは未定とする。
1CPU直列mergeには確認済み3条件だけでも少なくとも約187GBの読込みが見込まれ、残る9条件と実転送速度は未計測である。
全検査を維持した8thread hash照合案は実装中で、受入と本番は未実施である。
4時間・24時間の要求walltimeを完了予測や保証としない。
[復旧結果](cluster_postprocess_recovery_result_2026-10-24_ja.md)と[状態文書](PROJECT_STATUS_2026-10-24_ja.md)を一次の進捗として、以下の旧controller生存記録は当時の履歴として保持する。

2026-10-25 01:39 JSTの新しいqstatではindex 8の265573もF/0・walltime38分44秒・CPU時間31分23秒となり、現在はindices 6・7・8の3件がF/0、残る9件がRである。
flow controllerは起動識別情報一致・生存を確認し、error記録なし・stderr 0バイト・finished journal 3件だった。
PBS正常終了とterminal回収は深い科学的結果受理とは区別し、goalは未完了のままとする。
以下の01:36 JSTまでの状態は履歴として保持する。

## 2026-10-25：置換7条件の投入後

置換するindices 2・3・4・5・9・10・11は、順に265586〜265592として全てqsub投入済みである。
保持index 6の265571は終了コード0・walltime36分5秒、index 7の265572は終了コード0・walltime36分11秒だった。
残る10件はR、全12件はrun_count=1、2物理ノード以内の配置を確認した。
終了コード0の2件もflowによる科学的結果の受理前であり、全12条件の受入・merge・独立計時・最終報告は未完了である。
その後、混合flowの実controllerを起動し、SSH終了後の別接続で生存・起動識別情報の一致、全12初回journal、errorとstderrが空であることを確認した。
indices 6・7は元preparedに対応したterminalを回収し、他10件はpendingであり、深い科学的結果受理は後続mergeで未実施である。
controllerはクラスタで常駐し、ローカル接続には依存しない。
以下の先行投入時の記録を履歴として保持し、goalは未完了のままとする。

## 2026-10-25 01:31 JSTの観測と置換ジョブの投入

goalは未完了であり、01:31 JSTのqstatで既存5ジョブ265564・265566・265571・265572・265573はRだった。
正常に継続しているindices 0・1・6・7・8は固有のprepared・manifest・実job IDを保持し、v4で終了コード1となった残り7条件だけを再実行する。
失敗原因のPBS最上位timestampだけを比較から除く修正は、265581・265582で各17テストと対象7条件の実CLI・live qstat検証に成功した。
混合版の投入処理265578・merge265579・flow265580・native準備265583・配置policy265584も終了コード0だった。
置換対象index 2の先行265586をqsubで投入したが、成功と残り6条件の投入はこの記録では未確認である。
本番比較値の受理や再実行7件の完了は未確認であり、受入試験成功を全12条件の比較・独立計時・最終報告の完了とは扱わない。
[復旧結果](cluster_postprocess_recovery_result_2026-10-24_ja.md)と[最新状態](PROJECT_STATUS_2026-10-24_ja.md)に修正範囲と観測を保存する。
比較工程は先行成功と後続進行を条件に10月25日07〜10時JSTを暫定目安とし、過去最長4.83時間を参考にするが、全体の完了時刻は未定である。
以前の18〜24時という全体予測は撤回し、以下の各節は過去時点の観測として保持する。

## 2026-10-25：v3先行1条件の失敗後の確認

goalは未完了であり、この確認時点で数値比較の本番ジョブは稼働していない。
v3のmain実行環境probe265549・265550とnative準備265551は正常終了したが、先行1条件265553はwalltime17秒・終了コード1となった。
親の実行環境検証は通りexecution.jsonを保存したが、子readerの実CLI起動時にimport元が一致せず、受理済み数値結果は得られなかった。
v3の残り11条件は一度も投入していない。
[失敗の回収記録](data_tile_validation_2026-10-17/canary_reader_failure_20261025_v3/receipt.json)と[起動階層監査](nested_reader_startup_audit_2026-10-25_ja.md)に原因と検証範囲を保存した。
全9子CLIの静的確認では修正対象はindices 0・1のみであり、2ファイルの配置を直した新環境の全9CLI probe265559は固定ノードAで正常終了した。
固定ノードBのprobe265560は他利用者の96CPUジョブにより待機したため、未実行を確認してqdelで取り消し、別の固定ノードでmain・reader両環境を検証する準備へ移った。
v4のnative準備・front・配置policyと先行1条件の本番成功は未確認であり、それまで完了時刻は確定しない。
mergeの実CLIを修正した受入265557は59テスト、flow265556は36テスト、後段265552は3実CLIの検証が正常終了したが、本番pipeline全体の完了証拠とは扱わない。
以下は過去時点の観測であり、現在の実ジョブ状態とは分けて参照する。

2026-10-25 00:06 JST時点でもgoalは未完了である。
旧比較265521は00:00:47に終了コード1で終了し、PBS walltime38分43秒・CPU時間31分6秒で、有効なworker結果は得られなかった。
staged readerのindices 6・7・8で外部の投入記録・スクリプトのhashが不足しており、メタデータの固定と検証を修正中である。
旧265520・265521の失敗記録を保持し、旧worker結果を再利用せず、全12条件を2物理ノードに6本ずつ配置するsingleton構成へ変更する。
旧8条件＋保持4条件のnative環境準備265527は終了コード0・walltime38秒だったが、これは環境・manifest・資源検証の証拠であり、比較値の受理ではない。
[準備と失敗の回収記録](data_tile_validation_2026-10-17/native_preparation_20261025_v1/receipt.json)と[最新の復旧結果](cluster_postprocess_recovery_result_2026-10-24_ja.md)を参照する。
新しい12条件の本番は00:06時点で未投入であり、従来の10月25日18〜24時という暫定見込みは継続せず、修正受入と本番投入後の進行を見て再見積りする。

以下の23:52の観測は当時の履歴であり、現在の稼働状態ではない。
2026-10-24 23:52 JSTの追加確認では、PBS投影39テスト、実nativeスモーク2条件、配置制御26件・worker binding16件の受入がPBS終了コード0で完了した。
旧比較265521は継続中、265520は失敗記録を保持し、新しい8本の条件別本番ジョブは未投入である。
受入証拠は[回収記録](data_tile_validation_2026-10-17/parallel_recovery_acceptance_20261024_v1/receipt.json)、実行経過は[復旧結果](cluster_postprocess_recovery_result_2026-10-24_ja.md)にあり、並列本番pipeline全体の完了を示すものではない。

2026年10月23日時点ではgoalは未完了である。
2026年10月24日の追記として、experimental公開は完了し、残る低ノイズ後処理の待受は[クラスタ内完結の構成](cluster_postprocess_pipeline_2026-10-24_ja.md)へ移設・起動した。
索引以後の本番結果と最終結論は未完了であり、移設の起動成功をgoal完了とは扱わない。
2026-10-24 11:15 JSTの追加確認では、全38バッチの索引・入力配置・[保存済み診断内訳](c3t2_saved_diagnostic_result_2026-10-24_ja.md)は完了し、条件別最終集約265507が実行中である。
experimental版の利用開始に必要な公開候補の準備と、継続中の数値検証を分けて判定する。
計算が正常終了することと、精度・混合・名目95%被覆が成立することも区別する。

| 要件 | 現在の判定 | 根拠と残作業 |
|---|---|---|
| tile72/288の符号構築・code-capacity・論理失敗定義 | 実装・受入記録あり | [tile中間報告](tile_validation_report_2026-10-18_ja.md)第2節と構造監査に4組合せを保存。距離や全失敗支持の連結性の独立証明とは扱わない。 |
| BP-LSD・BeliefFind・Union-Find | 実装・受入記録あり | [decoder検証](basic_decoders_validation_2026-10-18_ja.md)と[利用例](basic_decoders_usage_2026-10-18_ja.md)。今回46入力の保存済み受入との一致を再確認。新decoderのBAR被覆・速度順位は未校正。 |
| 公開候補のテスト・配布物・利用例・日英文書 | 準備済み | [最新候補](publication_candidate_status_2026-10-23_ja.md)にsource ZIP・wheel・訂正したRelease本文とhashを保存。現在のpackage 33ファイルはwheelと一致。最新mainのCIもsuccess。 |
| GitHubで実際に公開 | 2026-10-24に完了 | [公開結果](publication_result_2026-10-24_ja.md)。public・experimental prerelease・main/tag同一commit・両CI成功・公開添付ファイルのdigestを確認。所有者からZenodo連携済みとの回答を受けたが、生成記録・DOIの照合は別途残る。PyPI公開は後続事項。 |
| decoder再現性・prior感度 | 有限な検査と限界の報告済み | [環境間差](tile_decoder_platform_2026-10-17_ja.md)と[prior感度](tile_decoder_prior_effect_2026-10-18_ja.md)。固定prior・native環境でfailure集合を保ち、全入力での決定性を証明したとは扱わない。 |
| 主4条件の混合・BAR校正・直接MC・重み層別reference | 計測と報告済み | [中間報告](tile_validation_report_2026-10-18_ja.md)に各192seed・全352設定と混合比較、有限referenceの不確実性を保存。未定義診断・未取得を分母から除外しない。 |
| 主4条件の独立計時 | 計測と報告済み | [計時の独立レビュー](data_tile_validation_2026-10-17/main_timing_scientific_review_v1/report_ja.md)。全192分母保持の記録を今回読み直した。速度優位の一般保証ではない。 |
| 低ノイズ12条件 | 全12条件の比較用入力が揃った | 最後のtile288 depolarizingのp=0.001も最終集約と算術照合を完了し、比較用候補を検証した。[復旧結果と証拠](cluster_postprocess_recovery_result_2026-10-24_ja.md)を保存。全条件比較の完了とは区別する。 |
| 低ノイズの全条件比較・独立計時 | index 0のwalltime超過でflow停止、11件保持して復旧準備 | 265564はF/-29、旧controllerは終了し不在。3件F/0・8件Rを保持し、新index 0だけ4時間上限で再投入するfront v6は未投入。dispatcher13件・flow54件の受入は成功したが、新native準備・merge受入と本番結果の完全受理は未完了。 |
| 日本語の最終報告・推奨設定の根拠と限界 | 未完了 | [最終報告までの接続](low_partition_report_result_2026-10-23_ja.md)は完了したが、本番結果の回収・内容照合・結論のレビューが残る。 |
| 生データ・環境・再現手順の保存 | v5の有限scopeをprivate保存、最終資料は未完成 | 265599はF/0でsource1031参照・metadata75件をprivate snapshotへ保存。公開archive・科学的再現・historical closure・新front v6の保存完了とは区別する。全raw datasetの公開用変換と公開先も別途残る。 |
| qsub・最大2node・複数計算機の活用 | 固定2ノードで11件保持、index 0だけの復旧を準備 | 上限は2物理ノード×96コアであり2ジョブではない。新dispatcher265598はindex 0だけの4時間上限の再投入を許し、保持11件の再投入・証跡変更を拒否する13テストに成功した。新native準備・本番再投入は未完了。CPU・メモリ予約を守り、ローカル計算・テストは禁止する。 |

## 今回実際に再確認したこと

wheel内のpackage 33ファイルと現在のsource、基本decoderの受入対象46ファイルをbyte単位で照合した。
tile72/288・bit/depolarizingの構造監査4記録が存在し、paired logical basisと未証明事項の記載を確認した。
直接MC referenceの保存summaryは監査記録のSHA256と一致し、監査記録の試行数は81,788,928、chunk数は1,248である。
主4条件のtrace監査記録は各768群・192replicateで、合計件数の整合を確認した。
これらは現在のsourceと保存証拠の照合であり、生traceの再監査・native decoderの再試験・新たな科学的検証ではない。
結果と再現scriptは [照合記録](data_tile_validation_2026-10-17/goal_evidence_20261023_v2/observation.json) に保存した。
そのSHA256は `9da117f9b1429036089a5c648370e2a5f3e31fd6f8e7d96baa9110c6846c5c2c` である。

goal完了の判断には、全12条件の比較、独立計時または事前規則に基づく実行不能・対象なしの記録、最終報告と再現情報の照合が必要である。
最後の1条件の集約・算術照合の完了を、これら残工程の完了とは扱わない。
検証の結果として精度gate未達や非推奨となる設定が残っても、それを隠さず結論へ反映する。
設定間の整合だけから、独立referenceのない領域の精度や被覆を保証しない。
