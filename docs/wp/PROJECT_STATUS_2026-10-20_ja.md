# mcmc4qec：公開準備と数値検証の状態

日付を跨いだ最新状態とfull監査の起動環境修正は[2026-10-21の状態](PROJECT_STATUS_2026-10-21_ja.md)に記録する。

2026-10-20の状態を、公開候補と継続中の科学検証に分けてまとめる。
詳細な実行履歴は [公開候補固定後の記録](POST_FREEZE_STATUS_2026-10-19_ja.md) に保持する。

## 公開準備

GitHub experimental版向けのsource ZIP、wheel、環境差検証ZIP、SHA256SUMS、日英Release本文、利用例と文書を準備済みである。
配布候補はcommit `47ef1b6ad957a93dae3bbd6cf1d79fab86457e96` に固定し、その [CI](https://github.com/junichiharuna/mcmc4qec/actions/runs/39267489093) は成功した。
installed coreはPython 3.11/3.12それぞれ696 passed・252 skipped、optionalは各版の全shard合計2306 passed・7 skippedで、欠落・重複のない全case実行を確認した。
文書のstrict build、リンク検査、strict型検査、quick examplesとnotebookも [公開候補の検証記録](experimental_remote_ci_2026-10-19_ja.md) に保存している。
08:26 JSTの [再確認記録](data_experimental_release_2026-10-19/release_ready_recheck_20261020_v2.json) で、3配布物のhashが固定候補から変わっていないことを確認した。

現在のlocal/remote mainは文書・TODO・gitignoreの追加を含む `886b44b9fdc56d5b86491302dfb651285bbc4113` であり、その [別のCI](https://github.com/junichiharuna/mcmc4qec/actions/runs/39325976119) も成功している。
この文書追加commit向けに配布候補を作り直したわけではなく、配布物のcommit対応は上記の固定候補に保つ。
リポジトリは再確認時点でprivateであり、GitHub Release・visibility変更・PyPI公開は行っていない。
数値検証の完了を待たずexperimentalとして公開できる準備と、科学的な推奨設定を確定できる状態は区別する。

## 実装範囲

| 項目 | 状態と範囲 |
|---|---|
| Tile code | tile72/288のfactory、bit-flip/depolarizingのcode-capacity問題、論理失敗定義を実装・小規模検証済み。 |
| BP-OSD | 接続済みで、今回の科学校正のdecoderに使用。目標priorをladder全体で固定する。 |
| BP-LSD・BeliefFind・Union-Find | 接続・小規模検証・利用文書を公開候補に含む。各decoderのBAR被覆や速度順位の本校正は未完了。 |
| Bosonic codeとdecoder | [TODO](../../TODO.md)に追加済み。符号族・noise・decoderは未選定で、新規実装は未着手。 |

## 科学検証の到達点

| 対象 | 現在の検証範囲 |
|---|---|
| 主4条件：tile72/288 × bit-flip/depolarizing | 各192 seedのsampling、保存trace監査、BAR再集計、混合診断比較、独立計時の評価を完了。[主報告](tile_validation_report_2026-10-18_ja.md)に結果と限界を記録。 |
| tile72 bit-flip、p=.01 | 低ノイズの正式比較と回収を完了。[C0T0結果](low_c0t0_recovered_result_2026-10-19_ja.md)を参照。 |
| tile72 bit-flip、p=.003 | 低ノイズの正式比較と回収を完了。[C0T1結果](low_c0t1_recovered_result_2026-10-20_ja.md)を参照。 |
| tile72 depolarizing、p=.01/.003/.001 | 低ノイズ3条件の正式比較を完了。混合診断の警告が残り、名目95%被覆や低ノイズ全域の精度は保証しない。 |
| tile72 bit-flip、p=.001 | 最終集計265366が21:54:56 JSTに正常終了し、67,584行のreportと実行記録13点を回収した。[結果と適用限界](low_c0t2_recovered_result_2026-10-20_ja.md)を保存。全設定・全seedで診断flagが残る。 |
| tile288の低ノイズ6条件 | 未完了。bit-flip p=.01は両PCで後処理を継続中。復旧collector265362とcapacity監査265367は正常終了・受理済みで、full監査の準備へ進んだ。p=.003のsampling後半265361も正常終了し、native reference265368がqsub経由でRとなった。 |
| 低ノイズでの同精度到達時間比較 | 未完了。主4条件の計時結果から低ノイズ全域の速度優位を主張しない。 |

低ノイズの正式比較は6/12条件であり、tile72の6条件を完了した。
tile288の残り6条件と低ノイズ独立計時を継続する。
23:55 JSTまでに、[C0T2の保存BAR行の独立算術レビュー](low_c0t2_arithmetic_review_result_2026-10-20_ja.md)を追加した。
38 archive・768 group・67,584行を再集計し、352設定の11,968値はreportとの最大差0だった。
既存6条件図の長い16設定の432値も最大差0で一致し、集計値を訂正する必要はなかった。
診断flagと有限referenceの限界は維持し、正式完了数は6/12条件のままである。
23:56 JSTの実PBS確認では、sampling265361は23:55:18にF・Exit_status 0・run_count 1、capacity監査265367は23:56:09に同じく正常終端だった。
capacity監査のcompletionを既存driverが受理し、full-planへ進んだ。
次条件C1T1のnative reference265368を既存引継ぎがqsubで投入し、Rを確認した。
DGX batch18の回収が完了してbatch19のexportへ進み、C1T0のhost側回収は452/768群である。
23:44 JSTまでに、C1T0の最終設定作成後の[qsub・正常終端確認・report回収](c1t0_final_execution_handoff_spec_2026-10-20_ja.md)を実装・検証し、local PID21844で起動した。
Windows/Linux各24件の受入と実wrapperの起動確認を通過し、現在は設定作成の正常完了待ちである。
新しいqsub・最終report実行・回収は未実施であり、正式完了数は6/12条件のままである。
既存10 sessionと新引継ぎの計11 sessionの継続をpollで確認し、クラスタは265361がR・265367がQ、要求は計2ノードだった。
23:37 JSTまでに、[C1T0最終設定作成への引継ぎ](c1t0_final_preparation_spec_2026-10-20_ja.md)を実装・検証し、local PID34812で起動した。
元venvと135 source、Windows/Linux各18件の設定契約・各6件の待機処理を確認し、全回収・転送とfull監査の完了を待っている。
本番最終config・qsub・reportは未実施であり、設定作成成功後も投入・回収の接続が残る。
この時点でDGX batch17の回収が終わり、C1T0のhost側回収は432/768群、クラスタはsampling265361がR・capacity監査265367がQだった。
既存9 sessionと新待機sessionの計10 sessionの継続をpollで確認した。
23:27 JSTまでに、完了したtile72の[6条件・96設定の誤差法比較](low_long_six_comparison_result_2026-10-20_ja.md)を追加した。
受入9件、旧80設定の保持、再現CSVのbyte一致、描画96点の照合とPNGの目視確認を完了した。
追加したbit-flip p=.001は回収reportからの抽出であり、今回保存BAR行の独立算術レビューを追加したわけではない。
同条件の長い設定でも全seedに診断flagが残り、誤差法による重なり件数の増加を混合改善や95%被覆保証とは扱わない。
23:27 JSTにはDGX batch17のPID2076332とLabo batch3のPID20824がliveで、C1T0のhost側回収は412/768群だった。
9つの既存sessionは継続中で、全群ローカル独立検査・最終集計の完了とは区別する。
22:59 JSTまでにC0T2の[実venv wrapperへの計時reader接続](low_timing_portable_venv_spec_2026-10-20_ja.md)を別配置で検証し、Windows/Linux各16件と実子環境のbootstrapを通過した。
実metadata候補は[6/12条件](data_tile_validation_2026-10-17/low_timing_partial_input_inventory_20261020_v2.json)まで揃ったが、全条件のraw再読取・独立計時は未実施である。
同時点でDGXはbatch15の回収を終えてbatch16のPID2033529がliveとなり、C1T0のhost側回収は392/768群である。
既存8 sessionの継続を確認し、計時準備による新しいqsubは行っていない。
23:09 JSTまでに、[C1T0の全38 batch回収から独立index・context作成・転送への引継ぎ](c1t0_collection_finalize_handoff_spec_2026-10-20_ja.md)をlocal PID40448で起動した。
Windows/Linux各11件の受入と実入力照合を通過し、現在は両PCのserial driver正常完了待ちである。
全群index・転送・最終config・最終qsubは未実施であり、正式完了数は6/12条件を維持する。
既存8 sessionと新しい待機sessionの継続をpollで確認し、クラスタはsampling265361がR・capacity監査265367がQの計2要求ノードである。
23:15 JSTまでに、残るdepolarizing 3条件の[anchor/sample全9件の実preflight](low_remaining_generator_order_2026-10-20_ja.md)を並列に実施し、全件成功した。
全件で空き枠なし・qsub未実施を確認し、executeは未使用のままである。
DGXのbatch16は計算を終えて回収中であり、この時点では正式完了数6/12やhost側回収392/768を増やしていない。
21:59 JSTまでに、残る5条件の[入力export adapter](planned_input_export_spec_2026-10-20_ja.md)を作成し、Windows/Linux各38件の合成受入を通過した。
C1T1の実3投入receiptと固定条件のローカル照合は完了したが、本番terminal検査・入力export・PC転送は未実施である。
受入source・ログ・C0T2の集約と回収証跡・実ジョブ観測を[51ファイルのmanifest](data_tile_validation_2026-10-17/planned_input_export_progress_20261020_v1/manifest.json)へ保存した。
22:02 JST前後もDGX batch13（PID1975389）・Labo batch2（PID19744）はliveで、クラスタはsampling265361がR、capacity監査265367がQだった。
22:09 JSTまでに、残る5条件向けの[配置・stage・launch・回収adapter](planned_pc_lifecycle_spec_2026-10-20_ja.md)を追加し、Windows/Linux各32件の受入と6 CLIの起動確認を通過した。
初回native referenceの回収・条件間parity・serial driverの新条件への接続は未完了であり、これらのadapterで本番PC処理を開始したわけではない。
22:17 JSTまでに[初回native reference回収adapter](planned_reference_transfer_spec_2026-10-20_ja.md)も追加し、Windows/Linux各31件の合成受入とCLI起動確認を通過した。
5条件の実reference投入・回収、PC初回parityとserial driverの新条件接続は未実施である。
22:26 JSTまでに[PC初回parity](planned_pc_parity_spec_2026-10-20_ja.md)と[全batch serial driver](planned_pc_serial_spec_2026-10-20_ja.md)の新条件対応を実装し、Windows/Linuxでそれぞれ25件・31件の受入を通過した。
前条件の最終host batchと新条件native referenceの実回収を要求し、本番registry作成・新driver起動はまだ行っていない。
既存DGX driverはbatch13の回収を終えてbatch14のlaunchへ進み、クラスタはsampling265361がR・capacity監査265367がQを維持していた。
同時点の実qstatでもsampling265361がR、capacity監査265367がQで、4つの既存PC driver・監査引継ぎsessionは継続中だった。
22:41 JSTまでに、C1T1の[native reference引継ぎ](planned_native_handoff_spec_2026-10-20_ja.md)と[PC引継ぎ](planned_pc_handoff_spec_2026-10-20_ja.md)を起動した。
前者はWindows/Linux各20件、後者は各19件の受入と実入力照合を通過し、生成ジョブ正常終端と前条件回収を待つ。
referenceは既存controllerの共有lockと最大2ノード検査を経てqsubし、PCは既存parityのexecution lockと実process不在確認を経て新条件へ進む。
新referenceのqsub・新条件のPC計算はまだ始まっておらず、正式完了数は6/12のままである。
既存4 sessionと新しい3引継ぎsessionの継続を確認し、DGXはbatch14回収を終えてbatch15のPID2025839、Laboはbatch2回収を終えてbatch3のPID20824がliveだった。
22:43 JSTまでの実観測と引継ぎのsource・試験・開始記録は[157ファイルのmanifest](data_tile_validation_2026-10-17/planned_handoffs_started_20261020_v1/manifest.json)へ保存した。
C1T0のhost側回収はDGX300群・Labo72群の計372/768群であり、ローカル独立全archive検査の完了数とは区別する。
実qstatはsampling265361がR、capacity監査265367がQで、要求は引き続き計2ノードである。
22:49 JSTまでに、次のtile288 bit-flip p=.001の[生成引継ぎ](planned_c1t2_generation_handoff_spec_2026-10-20_ja.md)をlocal PID44160で起動した。
Windows/Linux各14件の受入と実3preflight receiptの照合を通過し、先行C1T1 full監査・native referenceの正常完了を待つ。
その後anchorの正常終端を確認してsample 0/1を最大2ノードの空き枠へ投入するが、この時点で新しいqsubは未実施である。
21:51 JSTまでに、残る5条件の[PC割当て](planned_condition_assignment_spec_2026-10-20_ja.md)を実C1T0のbatch時間から固定し、各条件DGX648群・Labo120群とした。
実native metadataと全768群の重複・欠落なしを確認し、各条件の初期indexは予定67,584行・観測0行である。
各条件の入力export・native reference計算・PC parity・数値worker起動は未実施であり、この準備を正式比較の完了には数えない。
既存C1T0の割当ては維持し、21:51のqstatでもsampling265361とfinal265366の2ジョブがRだった。
21:42 JST前後には、C1T0のhost側回収が288/768群となり、DGX batch12のPID1967670とLabo batch2のPID19744はliveだった。
ローカル独立検査は60群のままであり、sampling265361とC0T2 final265366の2ジョブがRだった。
C1T2のsample 0/1の実クラスタpreflightを一度ずつ並列に実施し、両方が正常終了したが、空き枠がなくqsubは行っていない。
これでC1T2のanchor 0・sample 0/1のpreflightは使用済み、3 executeは未使用である。
残る5条件の [native parity reference config/script](planned_native_reference_spec_2026-10-20_ja.md) を既存workerでprepare/preflightし、各1 CPU・32 GB・4時間の初期要求で固定した。
これはmetadataとscriptの検査であり、当該referenceのqsub・数値計算・raw入力の存在/整合性検査は未実施である。
既存controlと113 source、受理済みC1T0の保存実測・元PBS終端を照合した準備記録を [75ファイルのmanifest](data_tile_validation_2026-10-17/planned_next_conditions_readiness_20261020_v1/manifest.json) に保存した。
21:29 JSTまでに、C1T1の [生成終了から初回collector・capacity/full監査への引継ぎ](planned_c1t1_handoff_spec_2026-10-20_ja.md) をlocal PID13508で起動した。
Windows25件の受入と実197ファイルのbootstrap照合を通過し、anchor265357・前半265358の正常終端を確認したうえで、後半265361のRを観測して待機している。
新しいcollectorのqsub前には先行C1T0 full監査の受理・実PBS正常終端と実空き枠を要求し、既存schedulerの共有lock・最大2ノード検査を維持する。
C1T1のcollector/監査はこの新driverが担当するため、同じ操作を手動で重複実行しない。
この起動はC1T1のcollector投入・監査成功・科学的受理を示さない。
21:21 JSTまでの追加進捗では、初回4時間collectorを使う残る5条件について [最終reader・qsub接続](planned_final_reader_spec_2026-10-20_ja.md) と [report回収](planned_final_collection_spec_2026-10-20_ja.md) を別配置へ実装・検証した。
readerはWindows/Linux各65件、qsub接続はWindows30件・3 skipとLinux33件、回収はWindows46件・8 skipとLinux54件を通過した。
本番用22 control、元113ソース・75 import先、5条件の実監査configを照合したが、5条件の本番最終config・qsub・report回収は未実施である。
C1T0のhost側回収は268/768群、ローカル独立検査は60群であり、DGX batch11のPID1960148とLabo batch2のPID19744のliveを確認した。
復旧collector265362は21:20:36 JSTにF・Exit_status 0・run_count 1、walltime 1時間48分17秒で終了し、既存completion readerが回収を受理した。
後続capacity監査はplan/preflight済みで、既存の引継ぎ処理が最大2ノードの空きを待つ。
C0T2最終集計265366のqsubとR、collector正常終端を [実観測記録](data_portable_bar_2026-10-19/mixed-c0t2-final-dispatch-observation-v1.json) に保存した。
最終集計の実時間は未確定であり、要求4時間を終了時刻の予測とは扱わない。
21:02 JSTまでにDGX batch9とLabo batch1の回収・転送照合も終わり、現在条件のhost側回収は248/768群になった。
21:02 JSTの実観測はDGX batch10のPID1916412がlive、Labo batch1のPID6556はterminalあり・終了済みで、Laboの既存driverはbatch2のexportを進めている。
初回4時間collectorから [capacity/full監査へ進む接続](planned_trace_audit_spec_2026-10-20_ja.md) はWindowsの分割53件・Linuxの統合53件を通過し、5条件の実configを別配置で固定した。
本番collectorの完了authority確認と監査実行は未実施であり、最終BAR readerへの接続を継続する。
20:37 JSTまでにDGX batch8の20群も回収し、現在条件のhost側回収は204/768群になった。
次のtile288 bit-flip p=.001のanchorは実クラスタpreflightを通過したが、空き枠がなく未投入である。
残る5条件のcollectorには [初回から4時間枠を選ぶ接続](planned_collection_budget_spec_2026-10-20_ja.md) を別配置で準備した。
20:47 JSTまでにbackend・scheduler・workerの統合受入がWindows/Linux各51件で成功し、5条件の実configと元入力の照合を完了した。
終端記録にrun_countが残らない問題を結合試験で修正し、元samplingの記録形式は維持した。
この時点ではauthority・後続監査と最終readerの接続、実上流jobの正常終端を要求するpreflight、および本番collector投入は未実施だった。
20:24 JST前後に、[復旧collectorからcapacity/full監査への引継ぎ](recovery_audit_handoff_spec_2026-10-20_ja.md)と、[C0T2最終ジョブの正常終端からreport回収への引継ぎ](portable_mixed_final_handoff_spec_2026-10-20_ja.md)を起動済みである。
追加受入はWindows計43件で成功し、実qstatの正常終端・固定job ID・hashを要求して既存workerへ引き継ぐ。
前者はC0T2の既存投入監視を優先し、後者はqsubを呼ばずに待つため、起動時点の要求は引き続き2ノードである。
起動時点では265361と265362がRであり、これらの引継ぎの後段qsub・監査・report回収はまだ実施していない。
20:21 JST前後にはDGX batch8の実PID1901208とLabo batch1の実PID6556のliveを確認した。
DGX batch7までの160群とLabo batch0の24群をhost側で回収済みであり、ローカル独立検査済み60群とは区別する。
DGXのC1T0 batch0〜6は各20群・1,760行、Labo batch0は24群・2,112行の回収・host上の保存値検査・転送hash照合を完了した。
batch0〜2のローカル独立検査は [snapshot v4](data_tile_validation_2026-10-17/portable_condition_c1t0_snapshot_v4.json) に保存し、60/768群・5,280行・未回収708群、全行flag・診断未定義2,440行を保持した。
最初の回収は隔離Pythonのimport入口、最初の独立検査は現在のcheckoutとsampling時のソース差で停止したため、失敗記録を保持して入口とソース配置を修正した。
gateを緩めず、保存入力から元113ソースを別directoryへ復元して検査を通した。
18:27 JSTの [実プロセス観測](data_tile_validation_2026-10-17/pc_live_after_dgx_batch2_v1.json) ではDGX batch2がPID1784989・20 worker、Labo batch0がPID14832・24 workerで稼働中だった。
その後Laboの旧C0T2最終batch5も実PID7544の終了・terminalを確認し、既存の準備済みcollectorで24群を一度だけ回収した。
全群回収後の [snapshot v20](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v20.json) は768/768群・67,584/67,584行を検査済みで、未回収は0である。
全67,584行に診断flagがあり、未定義診断は41,424行だったため、回収完了を混合や精度の保証とは扱わない。
この回収時点では元環境の全trace監査と独立referenceを結合する最終reportは未完了で、正式完了数は5/12条件だった。
その後21:54:56 JSTにC0T2の最終reportが正常終了し、現在は上表の6/12条件へ更新した。
LaboのC1T0 parityは747.04秒でacceptedとなり、保存値の再照合後に24 workerのbatch0へ引き継いだ。
DGX batch3とLabo batch1の入力も固定済み割当てから先行配置したが、これらの数値プロセスはまだ起動していない。
復旧collectorは実旧成果物14ファイル・旧qstat終端を照合し、Windowsのguard 16件とscheduler 12件、Linuxの統合28件の受入と実入力preflightを通過した。
要求済みノードが2未満になったら共有lockの下でqsubを一度だけ呼ぶ監視をlocal PID3092で起動したが、17:38 JSTの観測では265358がR・265361がQであり、復旧qsubはまだ呼んでいない。
詳しい実行条件と未完了の後段接続は [復旧仕様](collection_retry_spec_2026-10-20_ja.md) に記録する。
復旧collectorからcapacity/full監査への [実行入口](recovery_trace_execution_spec_2026-10-20_ja.md) は追加済みで、Windowsの分割45件・Linux統合45件の受入と実native bootstrapを通過した。
元監査の計算・資源推定を再利用し、復旧authorityとworker入口だけを明示的に接続した。
復旧collectorがまだqsub待ちのため、この新監査の本番plan・qsub・実行・completeは未実施である。
最終BAR reportの [reader/CLIでの復旧backend選択](recovery_bar_final_reader_spec_2026-10-20_ja.md) は実装し、Windows64件・Linux64件の受入と実配置済みconfigのbootstrapを通過した。
final qsub wrapperは [復旧専用の別配置](recovery_bar_final_qsub_spec_2026-10-20_ja.md) に実装し、Windows30 passed・3 skipped、Linux33 passedでfixture受入を確認した。
全38 batchの実context生成/転送、本番final config・qsubは残っており、本番reportはまだ実行していない。
復旧reportの [回収処理](recovery_final_collection_spec_2026-10-20_ja.md) は実装し、Windows31 passed・8 skipped、Linux39 passedで受入を確認した。
本番の別directoryへ22制御ファイルを配置し、元native referenceの113ソースと75 import先を照合したが、最終config・実行・本番回収は未実施である。
回収入口・受入・配置と20:10 JST前後の実プロセス観測は [51ファイルのmanifest](data_tile_validation_2026-10-17/recovery_final_collection_progress_20261020_v1/manifest.json) に保存した。
最終readerのsource・受入・native bootstrapと19:24 JSTの両PC実PID観測は [30ファイルのmanifest](data_tile_validation_2026-10-17/recovery_bar_final_reader_progress_20261020_v1/manifest.json) に保存した。
新監査のsource・受入・native bootstrapとsnapshot v4は [44ファイルのmanifest](data_tile_validation_2026-10-17/recovery_trace_execution_progress_20261020_v1/manifest.json) に保持した。
17:39 JSTまでの復旧control・実parity・初回batch起動証跡は [47ファイルの保存manifest](data_tile_validation_2026-10-17/c1t0_recovery_progress_20261020_v1/manifest.json) に保持し、その後の全群回収はsnapshot v20を参照する。
C0T2の130ファイル・9,532,490,259 bytesはクラスタへ転送・hash照合済みである。
元venvとその実体を区別する [Python binding](portable_mixed_venv_binding_spec_2026-10-20_ja.md) を実装し、Windows10 passed・1 skipped、Linux11 passedと実元環境の照合を通した。
最終config `4aa2210aafc1d0f25c987da488516f57f110bfe16413a2bf9a980999fbacf8b9` は156 source・136 metadataを固定してprepare/preflight済みである。
local PID30804の監視は復旧collectorの投入後に空き枠を待つ構成であり、復旧用PID3092とともに実qstatで2ノード上限を守る。
最終reportの回収入口もWindows/Linux各26件と実prepared wrapperの読取検査を通したが、本番reportの回収はまだ行っていない。
18:41 JST以降は [逐次driver](portable_condition_serial_driver_spec_2026-10-20_ja.md) を使い、DGX batch3〜31の実行・回収を継続する。
Laboにも現batch0の実終端・既存launcher受理を待って回収し、batch1〜5を順番に実行する引継ぎを起動した。
driverはWindows11件、引継ぎ判定は7件の受入を通り、実remote PIDでDGX batch3とLabo batch0の稼働を確認した。
逐次制御のsource・受入・実起動と18:49 JSTの実PID観測は [25ファイルのmanifest](data_tile_validation_2026-10-17/c1t0_serial_execution_20261020_v1/manifest.json) に保存した。
個々の操作を別途実行すると重複になるため、上記driverの記録と実プロセスを確認してから操作する。
最終config・元Python binding・Windows/Linux受入・失敗時の修正経緯は [73ファイルの保存manifest](data_portable_bar_2026-10-19/mixed-final-readiness-20261020-v1/manifest.json) に保持した。
このmanifestは準備時点の記録であり、最終reportのqsub・完成・回収を証明するものではない。
19:31:46 JSTにsampling前半265358がF・exit 0・run_count 1で終了し、walltimeは4時間24分28秒だった。
同時刻に後半265361が開始し、その後監視が復旧collector265362をqsubで一度だけ投入した。
19:37 JST前後の実qstatで265361と265362のRを確認し、最大2要求ノードを維持している。
C0T2最終reportの監視は引き続き空き枠待ちであり、同じ処理を手動で重複投入しない。
最終qsub wrapperのsource・受入ログと19:39 JSTの実qstat・両PCのlive PIDは [35ファイルのmanifest](data_tile_validation_2026-10-17/recovery_bar_final_qsub_progress_20261020_v1/manifest.json) に保存した。
続いて [最終集計入力の作成](portable_condition_distribution_spec_2026-10-20_ja.md) を別配置へ実装し、Windows/Linux各50件の受入を確認した。
両PCのparity・初回predecessor計14ファイルを回収し、保存parityは元native referenceとの各88設定比較、predecessorは最終providerの検査関数で照合した。
60/768群の実途中indexは全群contextとして拒否され、実全群index・本番context・転送と最終reportは未完成である。
source・両環境の受入・共有保存物・実入力照合・途中index拒否・19:52 JSTの実プロセス観測を [49ファイルのmanifest](data_tile_validation_2026-10-17/condition_distribution_progress_20261020_v1/manifest.json) に保存した。
新contextの転送入口も実装し、追加Windows22件・Linux統合72件の受入を確認した。
完全な実indexとcontextが揃っていないため、本番の全群転送と最終reportは未実施である。
転送入口のsource・受入と19:59 JSTのDGX batch7・Labo batch1の実PID観測は [25ファイルのmanifest](data_tile_validation_2026-10-17/condition_transfer_progress_20261020_v1/manifest.json) に保存した。
2026-10-20の[独立算術レビュー](low_recovered_arithmetic_review_result_2026-10-20_ja.md)では、C0T0/C0T1各67,584行・352設定・192 seedから各11,968項目を再計算し、保存reportと許容誤差内で一致した。
全block長を含む長い16設定ではreference区間と重なる件数がC0T0で172–186/192、C0T1で158–182/192となり、従来の8設定の抜粋と区別する。
このレビューは保存済み推定値・区間の集計確認であり、raw trace・decoder・BAR/bootstrapの再計算ではない。
完了済み5条件の[誤差法比較](low_long_uncertainty_comparison_result_2026-10-20_ja.md)では、各16設定・計80設定を維持してblock長32/128/1024とcross_chainを比較した。
bit-flipは16 chain・保存60,000、depolarizingは8 chain・保存12,000であり、noise間の同一計算予算比較とは扱わない。
全80設定で区間は取得されている一方、depolarizing p=.001では診断未定義が192/192であり、区間取得・混合・校正を区別する。
この5条件の比較表・図・元レビュー・再現sourceは[補足ZIP](low_long_comparison_export_2026-10-20_ja.md)にも保存し、別ディレクトリへの展開後にCSVのhashと描画80点の一致を確認した。
補足ZIPは保存レビューの比較用であり、raw traceやnative decoder環境の再現bundleではない。
直接MCと重み層別samplingのreferenceは有限標本によるもので、厳密な真値とは扱わない。
全16条件の層別referenceでは97,857,608試行のdraw/count監査と限定checkpoint照合を行っているが、全復号labelの独立再検証ではない。

長い設定でも混合上の懸念は残る。
例としてtile72 bit-flipのp=.003では、16 chain・burn-in 6,000・保存60,000・fine ladderの8設定すべてでflaggedとlow ESSが192/192だった。
同じ設定群の被覆件数は179–182/192であり、有限cohortの件数を名目95%被覆の保証にはしない。
p=.01の同じ長い設定群では診断flagが0だったが、この結果を別noise・別p・別設定へ一般化しない。
支持の連結性、詳細釣合い、非周期性の性質と、実測の混合診断は別々の評価項目として扱う。

## 環境間のdecoder差

[DGX/Laboの同一状態比較](paired_platform_mc_result_2026-10-19_ja.md)では、16条件・計1,048,576対の物理状態を一致させて比較した。
主4条件でfailure判定の不一致を確認しており、packageの版番号だけでは同じ失敗集合を保証できない。
16条件のLER差の調整済み区間は0を含んだが、環境間の等価性や全入力の一致を証明した結果ではない。
native decoder環境をまたいだreference・anchor・MCMC labelの混合は行わない。
現在のLabo/DGXでのBAR処理は、元クラスタの保存済み配列を同じ関数で後処理し、そこで新たな復号は行っていない。

## 現在の実行と残作業

17:18 JSTの更新ではnative reference265360が正常終了し、実walltime16分34秒・8,024,988 bytes・371 memberのarchiveを [回収受理](portable_bar_native_reference_spec_2026-10-20_ja.md) した。
referenceのcompleteと回収は使用済みであり、PC parity・初回batch配置は各hostの旧最終batch正常回収とprocess終了後に行う。
空き枠へC1T1のsample partition 1をqsubで投入し、[job265361のQを確認](low_c1t1_generation_dispatch_2026-10-20_ja.md)した。
sample 0の265358と合わせ、待機分を含め2ノードを維持する。
C1T0 collector復旧とC0T2最終集計は未完了であり、実行準備後も次の空き枠を要する。

17:14 JSTまでに、失敗したcollectorを保存したまま別出力先・4時間上限で検査する [復旧backend](collection_retry_spec_2026-10-20_ja.md) を追加した。
元sampling sourceとplan検査を維持し、新collectorの証拠を全trace監査へ明示的に渡す合成metadata試験12件がWindows/Linuxで成功した。
実retry config・qsub制御と最終reportでのbackend選択は未接続であり、collector復旧完了ではない。

16:58 JSTの更新ではC1T0 collector265356が2時間のwalltime上限を超えてExit_status -29となり、summary未取得の途中成果物を保持した。
自動引継ぎは停止し、collectorの正常completionは行っていない。
全群collectorを入力として要求しない既存の単一群reference契約に従い、正常終了済みsampling/anchorを再確認してreference265360を独立にqsubへ投入し、Rを確認した。
sampling265358と合わせて最大2ノードを維持し、collector復旧と全群trace監査は最終科学評価の必須条件として残す。
詳細は [collector失敗記録](low_c1t0_collector_dispatch_2026-10-20_ja.md) と [reference実行記録](portable_bar_native_reference_spec_2026-10-20_ja.md) に保存した。
後続のnative reference受理・PC parity・初回batch配置の操作sourceを追加したが、これら実データでの完了は未実施である。

16:42 JSTまでの実装更新として、条件別の完全cohort provider、最終集計CLIとqsub controllerを接続した。
provider関連235件はWindows/Linuxで成功し、CLI接続4件も両環境で成功した。
これらの [provider証跡](data_tile_validation_2026-10-17/portable_condition_provider_v1/manifest.json) と [CLI証跡](data_tile_validation_2026-10-17/portable_condition_final_cli_v1/manifest.json) はfixtureの受入範囲を明示し、実C1T0の科学検証完了とは区別する。
qsub接続の受入はWindows45 passed・1 skipped、Linux46 passedであり、[sourceと証跡](data_tile_validation_2026-10-17/portable_condition_final_qsub_v1/manifest.json)にmetadata fixture・scheduler置換の範囲を記録した。
実native referenceの受理、PCでの実parity、全batch実行・回収、実contextの作成・転送・qsub投入と最終raw監査/reference結合は引き続き必要である。

2026-10-20 17:14 JST前後の状態を記す。
C0T2の[途中index v18](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v18.json)は740/768群・65,120/67,584行を回収済みであり、未回収28群・2,464行を分母に保持している。
観測全65,120行に診断flag、39,880行に診断未定義があり、これらを除外していない。
受理済み群のinfrastructure failureは0、全科学検証完了flagはfalseである。
行数には複数設定が含まれ、独立seed数とは区別する。
snapshot SHA-256は `747091a4666e2d41342289ca067c3455cfdd6f8578e70f5732522a5671ca75ad` である。
DGXは元batch 17と再割当てbatch 0〜12の回収を完了した。
旧pipelineはbatch 8起動後の状態応答のJSON読取りで失敗したが、数値SSHの終了を待ってから停止し、batch 8自体の正常終端を確認した。
[引継ぎ復旧](portable_bar_dgx_handoff_recovery_2026-10-20_ja.md)で元sourceと割当てを維持したままbatch 9〜13を継続し、最終batch 13の実PID 1685632の稼働を確認した。
再開controller PID 45340は数値SSHを保持し、状態観測の読取り失敗だけを証跡を残して再試行する。
Laboはbatch 4の24群の正常回収を完了し、既存引継ぎ処理が起動した最終batch 5の実PID 7544の稼働を確認した。
batch 5の実execution intentを固定した回収準備も完了し、準備recordのSHA-256は `f9ea1987fac98728d9d2274cbd89646fa1b4ff4a7d8627e32cc01052bc0dd284` である。
batch 5の回収自体は未実施であり、実終端とprocess終了の確認後に行う。
DGX batch 13とLabo batch 5の[実process観測](data_portable_bar_2026-10-19/portable_live_20261020_v19.json)を保存し、どちらもlive・terminal未取得だった。
回収と次batch起動は各pipelineが担当し、観測timeoutを理由に計算を重複起動しない。
次のtile288条件への適用に備えた[縮小配列の一致確認](portable_bar_tile288_readiness_spec_2026-10-20_ja.md)では、4種類の符号・noise × 低ノイズ3点 × 成功・sampling失敗・zero anchorの36ケースがWindowsで一致した。
現在の実行driverと実parity入力はtile72の固定条件専用であり、この確認をtile288での実入力parityや本番投入の受理とは扱わない。
別配置に条件を明示するparity入口を追加し、Windows/Linux各49件のidentity・全設定reference・CLI拒否経路の受入が成功した。
次のC1T0照合群は元の生成準備へ固定したが、実referenceとarchive、実入力での成功parity、全群driverへの接続は未実施である。
[元クラスタreference作成](portable_bar_native_reference_spec_2026-10-20_ja.md)は小仕様・受入テストに続き、専用workerを隔離directoryへ実装した。
全88設定の保持、元入力とPBS証跡の照合、別領域へのexport、qsub未使用時のCLI拒否について、fixtureによる受入はWindows/Linux各26件で成功した。
専用qsub接続と終端受理controllerも別配置へ実装し、Windows/Linux各23件のfixture受入が成功した。
C1T0の実configとPBS scriptをクラスタへ準備し、元source・Python・入力・資源のpin、実preflight、`bash -n`を確認した。
要求は保存native解析recordを根拠とする1 CPU・32 GB・上限4時間で、所要時間の保証ではない。
実qsub、実reference・実入力export・各PCでの成功parityは未実施であり、既存の生成・collector・監査・次anchorの優先順を維持する。
[新条件の全群処理](portable_bar_condition_batch_spec_2026-10-20_ja.md)に向け、条件を明示した保存parity再照合を追加し、Windows/Linux各41件のfixture受入を確認した。
全row・診断・ACF、未定義や失敗の保持、元archive・source・runtime・外部hashを照合する関数であり、実C1T0の成功parityや全群driverの完成とは区別する。
その後、全768群の割当て契約と新条件driverを隔離directoryへ実装し、Windows/Linux各112件のfixture受入を確認した。
Windowsでfixture ZIPのmtime対応後に影響する結合試験1件を再確認した。
実subprocess・spawn worker、全88設定の未取得行保持、起動前後の保存parity再照合を含み、sourceと失敗・成功ログを[保存](data_tile_validation_2026-10-17/portable_condition_batch_driver_v1/manifest.json)した。
実割当てplan作成と配置・回収・途中index・最終readerへの接続、実C1T0の成功parityと本番投入は未実施である。
続いて転送前の入力検査を追加し、外部pin付きの割当て・receipt・batch ZIP・固定reference ZIPと、全taskのmarker・payload対応を照合した。
固定referenceと共通するtaskのbyte一致も確認し、追加26件を含む統合受入はWindows/Linux各138件で成功した。
合成入力の結び付けを検証した結果であり、実archiveの転送・配置や実trace監査は未実施である。
詳細とsource・ログは[入力転送前検査の記録](portable_bar_condition_batch_spec_2026-10-20_ja.md)に保存した。
PC上で新しい実行directoryへ配置するCLIと、配置したdriverへつなぐfixtureも追加した。
配置の上書き拒否や入力改変拒否などを含む統合受入はWindows/Linux各149件で成功し、source・ログを[保存](data_tile_validation_2026-10-17/portable_condition_staging_v1/manifest.json)した。
実parity subprocess・配置CLI・driver・spawn workerを使う合成失敗入力の結合試験であり、実C1T0の転送・parity・本番計算とは区別する。
新条件collectorまで接続したfixtureでは、全88設定と未取得行を保持し、出力改変を拒否し、context失敗の途中成果物を検証済み0行として回収した。
終端bindingの追加17件を含む統合受入はWindows/Linux各166件で成功し、[30ファイルのsourceと証跡](data_tile_validation_2026-10-17/portable_condition_collection_v1/manifest.json)へ保存した。
実運用の転送・回収、全群index・最終readerへの接続と新条件の科学評価は未完了である。
回収ZIPを転送先で独立に検査するreaderも追加し、元plan・input manifest・native profile・transformとsampling markerを外部入力として要求する。
追加13件を含む統合受入はWindows/Linux各179件で成功し、[33ファイルのsource・ログ・再現手順](data_tile_validation_2026-10-17/portable_condition_archive_reader_v1/manifest.json)へ保存した。
fixtureでは88未取得行を保持し、marker不一致を拒否し、context失敗の途中成果物を利用可能な数値行として返さないことを確認した。

クラスタはqsub・待機中を含め最大2ノードで運用する。
12:44 JST前後の実qstatでは、tile288 bit-flipのsampling 265343がR・経過5時間49分9秒、C0T2のfull trace監査265348がQだった。
12:35〜12:37 JSTの[実行中samplingの観測](data_tile_validation_2026-10-17/low_c1t0_live_progress_projection_20261020_v1.json)では、265343はRを維持し、61,440予定タスク中52,901件の終了markerを確認した。
約82秒で211件増えており、その短時間の生成速度が続く場合のmarker到達は13:32 JST前後という外挿になる。
終了markerには失敗タスクも含み得るため成功数や正式受理数とは扱わず、全成果物の照合と後続処理を含むjob終了予測ではない。
13:20 JSTの[追加観測](data_tile_validation_2026-10-17/low_c1t0_live_progress_20261020_v3.json)では60,080/61,440 marker、実qstatはR・経過6時間25分16秒で、partition summaryは未作成だった。
13:36 JSTの[追加観測](data_tile_validation_2026-10-17/low_c1t0_live_progress_20261020_v4.json)では61,440/61,440 markerが揃い、固定parity群の80 traceとanchorのmarkerも確認した。
実qstatはR・経過6時間41分19秒でsummaryは未作成であり、marker到達を正常終端や科学的受理と扱わず、collectorの投入は実終端確認後に行う。
14:01 JST前後の実qstatでも265343はR・経過約7時間5分、265348はQであり、追加qsubは行っていない。
14:26 JSTの実qstatでは265343はR・経過7時間31分、265348はQだった。
新driverの証跡保存時にもDGX再割当てbatch 8のPID 1496265とLabo batch 4のPID 6360がliveで、どちらもterminalは未取得と確認した。
14:35 JST前後の実qstatでも265343はR・経過7時間39分、265348はQであり、追加qsubは行っていない。
14:43 JST前後の実qstatは265343がR・経過7時間47分、265348がQだった。
265343は14:46:54 JSTにF・exit 0・run_count 1で終了し、実walltimeは7時間52分17秒だった。
前段anchorとsamplingの正常終端を確認して[collectorをqsubで投入](low_c1t0_collector_dispatch_2026-10-20_ja.md)し、job 265356のRを確認した。
要求は1ノード・1 CPU・32 GB・上限2時間で、実測所要時間の保証ではない。
14:53 JST前後はC0T2のfull trace監査265348とcollector265356がRであり、最大2ノードを維持している。
collectorの終端受理は未実施で、samplingの終了を正式な科学検証完了とは扱わない。
265348は14:55:16 JSTにF・exit 0・run_count 1で終了し、実walltimeは8分20秒だった。
full trace監査のcompletion readerは一度だけ起動してaccepted=trueで終了した。
768群・192 replicateのmeasurement artifactと監査done markerを再hashしたが、監査payloadと現在の全raw traceの照合は最終PBS collectorに残す。
receipt SHA-256は `fe900965d68d477b05a4aa9afbccd73aa5144f98c88e161fb89c68c6188d49d7` である。
予定どおり次のC1T1 anchorをqsubで投入し、job265357は1分36秒で正常終了した。
続くsampling partition 0をqsubで投入し、[job265358のRを確認](low_c1t1_generation_dispatch_2026-10-20_ja.md)した。
15:08 JST前後はcollector265356とsampling265358の2ジョブで、最大2ノードを維持している。
C0T2のcollectorとtrace capacityは受理済みで、full監査の[投入記録](low_c0t2_trace_full_dispatch_2026-10-20_ja.md)と[残条件の生成順](low_remaining_generator_order_2026-10-20_ja.md)を保持している。
全群回収後の最終集計は[資源設定](portable_bar_mixed_final_resource_2026-10-20_ja.md)と[runbook](portable_bar_c0t2_final_runbook_2026-10-20_ja.md)を準備したが、最終config作成・qsubは未実施である。

低ノイズ独立計時のため、回復済みBARとportable結果を扱う[reader拡張](low_noise_timing_reader_extension_spec_2026-10-20_ja.md)を隔離directoryで進めている。
子プロセスCLI、source/native bootstrap、selectorの起動・受理、親wrapperのmetadata・資源接続、fixtureによるstage4 descriptor受理までを追加した。
Windows/Linuxの追加受入は各212件、既存回帰は各120件で成功した。
実データとPBS応答をfixtureへ置き換えた部分があり、これを本番のraw読取や全計時planの実行証拠とは扱わない。
親の実97 source・137 native fileのbyte/import照合も別プロセスで通過した。
C0T1の元report・実qstatに基づく最終jobの実績は3071秒・約1.909 GiBで、要求251 GiBとは区別する。
さらにC0T0/C0T1それぞれの実子environment候補について各98 source・137 native fileと元reportのsource/runtime bindingを照合した。
初回の依存module不足を含め、実施範囲と失敗記録は[段階的実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md)へ保存した。
その後、実C0T1で同一referenceのsource配置先だけが異なることを確認し、両配置の実byte一致を検証した場合に限って受理する修正を加えた。
修正後の統合受入はWindows 222 passed・66.88秒、Linux 222 passed・49.81秒で、元recordと最終reportの表現を別々に保持する。
C0T0/C0T1のentry候補は各25ファイルのmetadataと実qstatで照合し、修正後の実子environment候補へ更新した。
続いてC2T0/T1/T2の既存sealed snapshot・実qstatを照合し、各77ファイルのentry候補を保存した。
親の元Python・core・科学moduleを保持した93 sourceとldpc native 8ファイルのbootstrapも通過したが、raw読取を実行した証拠ではない。
完了済み5条件と未完了7条件を[部分入力inventory](data_tile_validation_2026-10-17/low_timing_partial_input_inventory_20261020_v1.json)に保存し、selector inputや全12条件の受理記録とは区別した。
全12条件の実descriptor・親script/resourceは未決定であり、これらの候補を本番parent inputとして受理したとは扱わない。
全12条件の実descriptor、実測資源決定、本番reader・選択・独立計時は未実施である。
公開候補と稼働中pipelineのsourceは変更していない。

残るtile288の6条件の正式比較、低ノイズ計時、推奨設定の根拠と適用限界を含む日本語最終報告を継続する。

## 15:35 JSTの追加進捗

新条件の回収readerを全768群・67,584予定行の途中indexへ接続した。
外部pin付きのregistryから元inputと回収ZIPを照合し、未回収、基盤失敗、context失敗、sampling失敗、区間未取得と診断未定義を分母から除外せず保持する。
追加8件と実subprocess結合試験を含む受入はWindows187 passed・65.66秒、Linux187 passed・13.28秒で、source・ログ・再現手順は[保存manifest](data_tile_validation_2026-10-17/portable_condition_cohort_index_v1/manifest.json)にある。
実C1T0のreference・parity・全群割当てはまだ存在せず、この実装受入を本番の数値結果とは扱わない。
15:35の実qstatではcollector265356とsampling265358がともにRであり、各1ノード・計2ノードを維持していた。
この追記によって低ノイズ正式完了数5/12条件やC0T2回収snapshot v15の680/768群が増えたわけではない。

15:39 JSTにC1T0 collectorからnative referenceへの[一度限りの引継ぎ](portable_bar_native_reference_spec_2026-10-20_ja.md)をlocal PID46044で起動した。
実reference preflightは成功し、collector265356のRを観測して待機している。
collectorのF・Exit_status 0・run_count 1と既存completion readerのacceptedを確認した後、準備済みreferenceを既存controller経由のqsubで一度だけ投入する。
共有lockとQを含む最大2要求ノードの検査を維持し、曖昧な投入応答は再試行しない。
引継ぎの受入はWindows18 passed・0.40秒であり、開始証跡を[保存](data_tile_validation_2026-10-17/native_reference_handoff_v1/manifest.json)した。
実referenceの投入・成功を確認した記録ではなく、collector completionやreference submitの手動重複実行を避ける。

15:44 JSTにC1T0の[実割当て](data_tile_validation_2026-10-17/portable_condition_c1t0_assignment_v1/assignment.json)を固定した。
DGX624群・32 batch、Labo144群・6 batchとし、各kernel・初期化の192 seedも156対36に分けた。
元クラスタの実manifest・profile・fixtureのhash一致と、全768群の重複・欠落なしを確認した。
assignment SHA-256は `9e2f52087a92f7bdf246a935c932b2901f80882fb86f35ffb5a3de344d44e57d` であり、[初期index](data_tile_validation_2026-10-17/portable_condition_c1t0_assignment_v1/initial_snapshot.json)は予定67,584行・観測0行・未回収768群である。
この配置は直近C0T2の後処理時間を参考にしたもので、C1T0の実測速度ではない。
実reference・各PCのparity・入力exportと転送・実runtimeへのbindingは未完了であり、C1T0のPC数値処理はまだ起動していない。

15:58 JSTまでに、C1T0の最初のDGX20群・Labo24群を元クラスタからexportし、各PCの新規incoming directoryへ入力とcontrol 14ファイルを先行配置した。
元sampling jobのF・Exit_status 0・run_count 1、元sourceとmetadata、ZIP全memberと割当て・task marker、転送後の全ファイルhashを照合した。
DGX入力は50,082,015 bytes・4,977 member、Labo入力は59,998,081 bytes・5,949 memberである。
実referenceとの共通入力比較、各PCの数値parity、実runtime受理、起動config作成は未実施であり、新しい数値プロセスは起動していない。
source・実exportと配置の証跡を[47ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_c1t0_initial_inputs_v1/manifest.json)に保存し、大きなinput ZIPはreceiptに記録したlocalと元クラスタのpathへ保持する。
同時刻の実qstatではcollector265356とsampling265358がともにRであり、native referenceへの引継ぎはcollector終了待ちである。

16:09 JSTに、全12条件を明示的に検査する最終監査・報告の関数層を別moduleへ追加した。
元環境のfull audit・PBS・reference照合を維持し、driver全体のcontext失敗を群単位の基盤失敗と区別しながら予定88行ずつ保持する。
fixtureでI/Oとproviderを置き換えた受入はWindows54 passed・31.44秒、Linux54 passed・16.72秒で、[sourceとログ](data_tile_validation_2026-10-17/portable_condition_final_functions_v1/manifest.json)を保存した。
実condition provider、CLI・qsubとの接続、実raw trace・referenceの結合は未完了であり、低ノイズ正式完了数を増やす結果ではない。
