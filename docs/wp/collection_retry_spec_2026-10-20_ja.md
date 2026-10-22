# sampling collector時間切れからの復旧

C1T0のcollector265356は2時間の初期上限を超えてExit_status -29となり、summaryを生成しなかった。
sampling・anchorは正常終了しており、再生成せず既存の全taskを検査する。
失敗したsubmission、tasks.jsonl、native preflight、stderrは元の場所へ保存したままにする。

## 分離する範囲

再実行の出力先を `sampling-collection-retry-v1`、submission先を `sampling-collection-submission-retry-v1` とする。
要求は1ノード・1 CPU・32 GB・4時間とし、2時間で第一照合が未完了だった実記録に基づく上限変更として扱い、所要時間の保証とはしない。
元のsampling plan、task・seed・partition・PBS receipt・bundle sourceの検査は元の関数へ委譲し、既存sourceを変更しない。
collectionに関わる関数は固定sourceのASTから分離し、出力先の文字列だけを変更する。
task record検査、全payloadの初回照合、二度目の全hash照合、全768群・192 anchorのcensus、失敗の保持は変えない。
新collectorのsource証跡には元sourceとこの分離処理のsourceを含める。

## 後段との接続

元の全trace監査へは、collectorの出力先を明示的に選ぶ別backendを渡す。
元のsampling source検査と新しいcollection source検査を混同せず、監査planには両方のsourceを保持する。
旧collector失敗を正常終了へ読み替えず、新collector自身の正常PBS終端・新ledger・新script・新resourceの一致を必須とする。
通常のreaderから失敗した旧collectionを暗黙に新collectionへ置き換えるfallbackは追加しない。

## 受入と投入条件

まずbackendの受入で、元関数の不変、変更したASTの範囲、4時間の資源、別出力先、新旧receiptの混入拒否と全分母の保持を確認する。
fixtureの全taskは合成metadataであり、実traceを読んだ結果とは扱わない。
実qsubには、元collectorの確定異常終端・停止、保存済み途中成果物のhash、新たなcontext・ledger・実行sourceの外部固定が別途必要である。
qsub制御の接続、native環境での実再実行、元trace監査と最終BAR readerへの実入力接続が終わるまで復旧完了とはしない。

## backend実装の受入

`output/collection_retry_v1/collection_backend.py` に、6つのcollection関数の出力先文字列だけを変更した独立namespaceを実装した。
4時間の資源設定とsource証跡の追加は別の関数として明示し、元の `read_plan`・`partition_evidence`・`artifact_record` の関数bindingを保持した。
元sampling moduleと元監査moduleの関数を書き換えず、監査側は同じ計算bytecodeと別のglobalsで明示的にretry collectionを選ぶ。
全768群・192 anchorの合成失敗metadataから新collector終端を読み、capacity/full監査planへ接続する受入を含め、Windows12 passed・13.95秒、Linux12 passed・4.22秒だった。
新旧job・resource・sourceの混入、taskの欠落/重複、終端の改変を拒否し、旧ファイルのbyte不変を確認した。
これは合成metadataの受入であり、実payloadの再照合や実checkpoint監査、実retry config作成・qsub投入を行った結果ではない。
失敗記録を外部固定する実行guard、qsub worker/controller、実監査投入と最終reportでのbackend選択は未接続である。
source・テスト・失敗/成功ログと元依存sourceを [41ファイルのmanifest](data_tile_validation_2026-10-17/collection_retry_backend_v1/manifest.json) へ保存し、SHA-256は `b6b1398731459c1a4e1294763b5d9330a146c1abb7a7c674513f5ca7fd94c792` である。

## 復旧実行guardの追加仕様

復旧contextは元root・production manifest・失敗job ID・元submission ledgerと、旧collection/submissionの全通常ファイルの相対path・hashを固定する。
旧summaryが存在しないこと、実qstatが元script・1 CPU・32 GB・2時間・run_count 1・F・Exit_status -29であることを必須にする。
保存済み失敗receiptと現在の実qstatは、変わり得る使用量ではなくjob ID・終端・投入script・要求資源の同一性で比較する。
元ledgerのintent・script・job binding、旧execution intentのledger hash、native preflightのjob/manifest/hostnameを照合する。
旧directoryのファイル集合も固定し、追加・削除・symlink・hash変化を拒否する。
新workerはledger成立を有界時間待ち、実PBS_JOBIDと新ledgerを照合してから既存backendのcollectを呼ぶ。
guardを実行前後に検査し、旧成果物が変わった場合は新collectorのsummaryだけで受理しない。
guard単体のfixture試験と、実qsub・全raw読取の成功は別々に記録する。

投入処理は元submit関数の別namespaceを使用し、workerコマンドとledgerの復旧contextだけを明示的に差し替える。
共有lock、待機中を含む最大2ノード、元samplingの正常終端、直前再検査、曖昧なqsub応答時のlock保持は元の制御を維持する。
workerは元bundleのPythonで実行し、復旧control・context・元manifestの外部hashを照合する。
通常終了した新collectorでも、旧成果物の実行後照合と新worker completionが揃わない場合は復旧済みと受理しない。

## 17:38 JSTまでの実装と実運用準備

guardのWindows受入は16 passed・1.22秒、元submitの限定AST変更・lock・最大ノード数・曖昧な応答を確認するscheduler受入は12 passed・5.15秒だった。
Linux統合は28 passed・2.49秒であり、qsub応答をfixtureで置き換えたscheduler試験を含む。
別途、実265356のF・Exit_status -29・run_count 1と元submissionを読み、旧collection/submissionの14ファイルを固定した [実guard記録](data_tile_validation_2026-10-17/collection_retry_guard_native_v1/accepted.json) を保存した。
元の時間切れ観測に記録されたファイルも同じhashを維持していた。
復旧context SHA-256は `94a2b6a16483b95c6a70d3e659932061d9df3201d1f9d4c869c9d13224c9b8ba` である。
新worker・guard・controller・backendは `/home/user/workspace/mcmc4qec/20261020-collection-retry-controls-v1` に配置し、元bundleと元sampling成果物を変更していない。
元samplingとanchorの完了証跡、source、native Python、復旧contextを検査した [実preflight](data_tile_validation_2026-10-17/collection_retry_controls_native_v1/accepted.json) は成功した。
新config SHA-256は `cdaf05234b3dffe62d3870056b929ddfa89e1263f2d4c802fcace78303e77234`、新PBS script SHA-256は `bf18a61b3e2d9b4d57f587150a5614cc4e0954b136d5e8b3d5b5b40a6dfc30c7` である。
`recovery_worker.py preflight` は使用済みであり、dry-run scriptと記録を作成したがqsubは呼んでいない。
`submit_when_slot_free_v1.py` をlocal PID3092で起動し、実qstatの要求ノード数と既存coordinatorを30秒間隔で確認する。
2ノード未満になれば、準備済みcontext・sourceを再検査し、元submitと同じ共有lock・直前ノード数検査を通してqsubを一度だけ呼ぶ。
17:38 JSTには265358がR、265361がQで計2要求ノードだったため待機中である。
この監視が生きている間に、同じ復旧jobを手動で重複投入しない。
投入応答が曖昧な場合はintentとlockを保持し、監視側でも自動再試行しない。
実worker終了・新PBS終端受理、実trace監査の再接続と最終reportの明示的backend選択は未完了である。

## 19:05 JSTまでの後段実装

元環境のcapacity/full trace監査へ復旧authorityを明示的に渡す [別の実行入口](recovery_trace_execution_spec_2026-10-20_ja.md) を追加し、Windows計45件・Linux45件の受入と実native bootstrapを通した。
復旧config・旧失敗guard・新workerの開始/終了・新ledger・新正常terminal・監査controlを外部hashで固定する。
元の監査計算、resource推定、qsubの共有lockと最大2ノードを維持し、元moduleを変更していない。
復旧collectorはまだ投入待ちであるため、新authorityの実正常終端検査と監査の本番plan・qsub・実行は未実施である。
最終BAR reportでの復旧backend選択は引き続き未接続である。

19:22 JSTまでに [最終reader/CLIの復旧backend選択](recovery_bar_final_reader_spec_2026-10-20_ja.md) を実装し、Windows64件・Linux64件と実配置configのbootstrapを通した。
本番のfinal qsub wrapper・全群context・回収入口のbindingは残っており、実reportの完了とは扱わない。
