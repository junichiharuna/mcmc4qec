# 新条件のportable parity用native reference

対象は最初にC1T0の事前固定群 `(1,0,0,0,0)` とし、production manifestと元rootは[条件入口の記録](portable_bar_tile288_readiness_spec_2026-10-20_ja.md)に従う。
既存 `portable_bar_qsub_v1.py` は全768群と元環境trace監査・科学referenceの最終結合を前提とするため、その条件検査を迂回して単一群のreference作成へ流用しない。
新しいreferenceは移植比較専用であり、本番samplingや全群BARの出力領域を変更せず別の未使用rootへ保存する。

## 計算と入力

元production plan、元クラスタPython、package・cluster_scripts・新しいcontrol source、native profileとfixtureのhashを固定する。
事前に固定した群の全rung・chainと共有anchorについて、既存の元環境loaderでmarker・payload・metadata・shapeを照合する。
元のnative preflightを用いてprofileとfixtureの一致を確認し、PC上のdecoderやfailure labelを参照しない。
元の解析関数で全88設定を計算し、全row・診断・ACF・未取得・失敗を保存する。
referenceのidentityにはparity専用の目的、元production、群、元input markerを記録する。
同じseed・bootstrap設定を保持するため、full cohortの追加独立標本として数えない。

## Exportと後段

元source、元planとprofile、対象群のpayloadとanchor、作成したreferenceを新しいarchiveへ保存する。
元rootは元sampling領域を指し、referenceの配置先を元rootへ読み替えない。
archiveの全memberとmanifest、元input marker、reference、native preflight、PBS実行記録を固定し、取得・実行の前後でhashを確認する。
新しいcondition parity入口が受理するschemaと全設定数を保ち、元archiveにreferenceを後から書き足す更新は行わない。
各PCでの全設定parity成功後にだけ、新条件の全群割当て・driver・回収へ接続する。
このparityとexportは全sampling終端、元環境の全trace監査、独立WSS referenceとの科学比較を代替しない。

## 実行制御

数値計算と大きいexportはqsubで行い、待機中を含め最大2ノードを守る。
共有submission lock、実所有jobのnode census、投入前後のsource/config/script hash、実qsub応答のjob IDを保持する。
曖昧なqsub応答や観測timeoutでは再投入せず、同じ実jobと保存intentを照合する。
computeは実PBS job、投入scriptとresource、元Python・source・native環境を確認してから開始する。
完了受理ではF・Exit_status 0・run_count 1と保存成果物を照合する。
資源は既存の実測を根拠に明示し、要求上限を実測所要時間やETAとして扱わない。

## 現在の状態

小仕様に続いて、隔離したnative reference workerの実装とfixtureによる受入を完了した。
専用qsub接続の実装・fixture受入とC1T0の実config/script準備を完了したが、qsub・実reference作成・実入力exportは未実施である。
既存の投入順を維持し、稼働中C1T0生成とC0T2監査の枠を無断で置き換えない。

## Workerの受入範囲

workerは独立したjob rootのconfig・投入script・submission記録を固定し、実PBSのR状態・run_count 1・所有者・Submit_arguments・要求資源と照合してから計算する。
元Python、thread設定、packageとcluster_scriptsの全Python source census、control source、元planとnative入力のbyteを計算前後に確認する。
元planを元runtimeの `read_production_plan` で再構成し、事前固定群だけを元loaderへ渡す。
loader通過後にもpayloadをmarkerのhashと照合し、その時点の全入力hashを計算後・archive作成後に再確認する。
新しいreferenceの元入力は全群集計の出力領域へ書き込まない。
受入テストではfixtureによるPBS bindingと小配列の保存・exportを確認し、本番qsubや実全88設定の数値一致とは明確に区別する。

## Workerの実装と受入結果

`output/portable_bar_native_reference_v1/native_reference.py` は元のloaderとanalyzerを呼ぶworkerであり、独自のBAR数値実装を追加しない。
元sampling領域と重ならない新規出力、固定群、全88設定の順序、diagnosticとACFの対応を検査し、失敗タスク・未取得区間・未定義の記録を保持する。
元inputのpayloadをmarkerに照合し、計算・exportの前後で元source・plan・profile・fixture・payload・PBS証跡のhashを確認する。
archiveには元source・入力・reference・native preflight・実行記録・worker sourceを含め、本番実行時はconfig・投入script・submission intent・qsub応答・submission記録も含める。
CLIは元Pythonとthread設定、PBS実jobのR・run_count 1・所有者・投入script・資源を確認し、qsubなしの開始を拒否する。
元runtimeでproduction planを再構成し、成功後も元設定と投入記録が変わっていないことを確認する。
worker自身はjobを投入せず、下記の専用controllerが準備・qsub投入・終端受理を担う。

Windowsは26 passed・2.53秒、Linuxは26 passed・1.07秒だった。
PBS状態の検査にはfixtureを使い、CLIのPBS未設定拒否は実subprocessで確認した。
受入は小配列の保存・exportとidentity検査であり、実PBS上での成功実行、実全88設定のreference計算、PCとの実parityは未実施である。
metadataがnative probe中に変わる場合の拒否と、archiveへのworker source同梱を、失敗する受入テストから追加した。
Linux v1の24件実行後に証跡同梱を拡張したため、最終26件は新しいLinux v2配置で実行した。
既存のbundle、公開候補、稼働中pipelineを変更していない。

[保存manifest](data_tile_validation_2026-10-17/portable_bar_native_reference_worker_v1/manifest.json)は24ファイルを束ね、SHA-256は `3e277bd0e238f98afffac31f4ec894a3c8adc49e39c26e3ff598a6d4b7935fe4` である。
workerのSHA-256は `a18015a8f052977620da89d3f371d657d39357fb20d98d0c4add6d2851a297c6` である。
実施範囲と再現手順は[receipt](data_tile_validation_2026-10-17/portable_bar_native_reference_worker_v1/receipt.json)に保存した。
再現時は保存した `sources/` 以下をoptional依存のある別checkoutに復元し、`python -B -m pytest output/portable_bar_native_reference_v1/test_native_reference.py -q` を実行する。
この保存物は軽量受入の再現用であり、本番計算のnative環境全体を封印したものではない。

## 専用qsub接続の受入

専用controllerは固定workerを変更せず、別directoryに置く。
既存の最終集計wrapperから再利用するのは、hashを固定したnode census・共有lock名・稼働controller検出のutilityに限る。
最終768群の受理条件を迂回した呼出しは行わない。
投入scriptは `qsub` に渡し、投入記録が完成したことを示すmarkerをatomicに公開してからworkerを起動できるようにする。
容量不足ではqsubを呼ばず、曖昧なqsub応答では共有lockとintentを残して自動再投入を禁止する。
終端受理は実F・Exit_status 0・run_count 1、worker成功、元configとscript、archiveとreferenceのhash・群・production・元rootを照合する。
成功したparity referenceも科学cohortの完了として数えない。

## Controllerの実装と準備結果

隔離した `output/portable_bar_native_reference_qsub_v1/reference_qsub.py` を実装し、Windows 23 passed・7.06秒、Linux 23 passed・12.16秒を確認した。
待機jobを含む2ノード制限、atomicな投入記録の公開、曖昧なqsub応答でのlock保持、重複投入拒否、終端jobとarchiveの対応、改変・失敗時の受理拒否を試した。
PBS応答と成功archiveはfixtureであり、実qsubの成功・実計算・実終端受理を確認したものではない。
既存の最終集計wrapperは変更せず、固定hashで読み込んだnode census等のutilityだけを再利用する。
固定workerのSHA-256も変更していない。

元クラスタのC0T0固定群 `(0,0,0,0,0)` の保存済み88設定referenceを既存exportのhashへ照合し、walltime 2,980.7399085583165秒・peak RSS 1,551.15625 MiBを確認した。
取得時はrecord・marker・npzのhashを読み取り前後で確認し、新たな数値計算は実行していない。
この記録の作成jobのPBS終端を今回再監査したものではなく、保存解析recordの時間・RSSを資源設定の根拠とする。
C1T0の要求は1ノード・1 CPU・32 GB・上限4時間とした。
walltimeは保存実測の4倍に読み込み・export用30分を足して30分単位に切り上げ、memoryはRSSの4倍に8 GiBを足した上で32 GBを下限とした。
C0T0は16 chain・66,000 step、C1T0は8 chain・18,000 stepで符号サイズも異なるため、同じ所要時間やmemoryを保証せず、科学的な同精度到達時間の比較とも区別する。

controller・worker・utilityは `/home/user/workspace/mcmc4qec/20261020-native-reference-controls-v1` に配置し、元bundleのsource・Python・plan・native入力と資源証拠を実configへ固定した。
job rootは `/home/user/workspace/mcmc4qec/20261020-native-reference-c1t0-v1` である。
config SHA-256は `0e96cb5fbb4c8db9b37dcac9c20e26fa6b1e855361e0499d68d7d32fc582f20d`、PBS script SHA-256は `a8623565bfe3ca889eaa2e327ccc58dda78713a427d0b7ff434e076bae3d5241` である。
実preflightと `bash -n` は通過し、観測した実jobは265343がR・265348がQ、要求node数は2だった。
qsubは呼んでおらず、既存の生成・collector・監査・次anchorの優先順と共有lockを維持する。

[保存manifest](data_tile_validation_2026-10-17/portable_bar_native_reference_qsub_v1/manifest.json)はsource・受入ログ・資源証拠・実config/scriptを35ファイルで束ね、SHA-256は `5d6f58d2dabeeec252eb576cffa52071753874cd21f2968aaf37cbd06d4d7095` である。
controllerのSHA-256は `0d09cba776f68086ede0af9c33316a9a678bc6345bf16a4969d201cda3e1f5ad` である。
[receipt](data_tile_validation_2026-10-17/portable_bar_native_reference_qsub_v1/receipt.json)に検査範囲と未実施事項を保存した。
再現時は保存sourceを別checkoutへ復元し、`python -B -m pytest output/portable_bar_native_reference_qsub_v1/test_reference_qsub.py -q` を実行する。
既に作成したremote stageとjob rootのprepareを繰り返さない。

次の投入対象として選び、実空き枠と既存優先jobを確認した時点で、元クラスタ上で次を一度だけ使用する。

```bash
/home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/venv/bin/python -B \
  /home/user/workspace/mcmc4qec/20261020-native-reference-controls-v1/output/portable_bar_native_reference_qsub_v1/reference_qsub.py \
  submit --root /home/user/workspace/mcmc4qec/20261020-native-reference-c1t0-v1 \
  --config-sha256 0e96cb5fbb4c8db9b37dcac9c20e26fa6b1e855361e0499d68d7d32fc582f20d --execute
```

SSH timeoutや曖昧なqsub応答では再実行せず、同じjob rootのintent・response・submission・共有lockと実qstatを照合する。
実F・Exit_status 0・run_count 1を確認後、同じcontrollerの `complete` modeを同じroot・config SHAで一度だけ実行してarchiveを受理する。
実archiveとmanifestのhashはまだ存在せず、PCへのparity実行configへ仮の値を設定しない。

## C1T0 collector完了後の一度限りの引継ぎ

collector265356の実qstatを読み、F・Exit_status=0・run_count=1・既知の投入scriptを確認してから、既存のcompletion readerを一度だけ実行する。
R・Qなどの未終端状態は待機し、観測失敗は保存して再観測するが、観測失敗からjob終了を推定しない。
completion readerがacceptedとなった後に限り、準備済みconfigのnative reference controllerを `submit --execute` で一度だけ呼び出す。
実qsubは既存controllerの共有lockとQを含む最大2要求ノードの検査に従う。
completion・qsub応答が曖昧な場合やsourceが変化した場合は証跡を保存して停止し、自動再投入しない。
開始前にlocal intentを排他的に保存し、起動済み引継ぎは再起動しない。
この引継ぎはreference生成を予約するだけであり、成功したreference、PC側parity、科学検証の完了とは扱わない。

固定jobの状態・所有者・script照合、異常終了・再実行・欠落jobの拒否、依存処理の失敗時に未投入となること、通信timeoutを未終端として扱うことについて、Windows18 passed・0.40秒だった。
`output/dispatch_c1t0_reference_after_collection_v1.py` のSHA-256は `7f20cb8645060ff3b9b063016a2ef8167ec5f987f7ca37e5342d511fd89adc55` である。
15:39 JSTにlocal PID46044で起動し、実reference controllerのpreflightはreturncode 0・prepared_not_submittedだった。
最初の実qstat観測はcollector265356がRであり、referenceのqsubはまだ呼び出していない。
開始時のsource・18件のテスト・失敗を含むログ・intent・preflightを[9ファイルのmanifest](data_tile_validation_2026-10-17/native_reference_handoff_v1/manifest.json)へ保存した。
manifest SHA-256は `821a333cc44a49edc7b58f2e4da1d9a33fe5d04c86e85146b5e2ec23e3aa3867` である。
稼働後はsourceを変更せず、`c1t0_reference_handoff_20261020_v1_*` の実観測・completion・submission・receiptを確認してから次の操作を決める。
collectorのcompletion readerとreference submitを手動で重複実行しない。

## collector時間切れ後の独立reference実行

collector265356はwalltime上限超過でExit_status -29となり、自動引継ぎは正常終端条件を満たさないため停止した。
その [失敗receipt](data_tile_validation_2026-10-17/c1t0_reference_handoff_20261020_v1_receipt.json) はqsub未実施・応答不確定なしであり、元controllerのprocess終了も確認した。
単一群referenceの専用workerとconfigは全群collectorを入力として要求せず、正常終了済みsamplingの対象群とanchor、元環境・元source・実PBSを独立に照合する。
この既存契約を維持して、collector復旧とは別にreferenceを進める順へ変更した。
元worker・controller・config・scriptは変更せず、別のdispatchでanchor265342/sample265343のF・exit 0・run_count 1とcollector265356の異常終端、元引継ぎの停止、実preflightを照合した。
16:55 JSTに `qsub /home/user/workspace/mcmc4qec/20261020-native-reference-c1t0-v1/reference.sh` がjob `265360.node-PRISM` として受理され、実qstatでRを確認した。
要求は1 CPU・32 GB・上限4時間であり、sampling265358と合わせて最大2ノードを維持した。
この上限を所要時間予測とは扱わず、全群collectorとtrace監査の正常受理も省略しない。
実投入記録は [独立dispatch receipt](data_tile_validation_2026-10-17/c1t0_reference_independent_dispatch_20261020_v1/receipt.json) にある。

後続の `collect_c1t0_native_reference_v1.py` は実F・exit 0・run_count 1を確認してから専用controllerのcompleteを一度だけ呼び、archive全memberと元task markerを照合する。
`dispatch_c1t0_pc_parity_v1.py` は各hostの旧最終batchの正常回収と実process終了、共通実行lockを確認してから、変更していないcondition parityで全88設定を比較する。
その成功後にも同じhost・元sourceで保存値の一致確認を繰り返し、5出力と外部hashを回収する。
`stage_c1t0_batch0_after_parity_v1.py` は実parity受理後にだけ、配置済みの20/24群を既存stage入口で新しい実行directoryへ配置する。
これら後続3手順はsyntax確認のみであり、referenceがRの時点ではcompletion・PC parity・batch配置を実施していない。
操作sourceと実投入・collector失敗の証跡を [14ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_c1t0_parity_operations_v1/manifest.json) に保存し、SHA-256は `53544ecac1637417f64e097273f1e52eb12a9bcc74db77847be5fb403564c2ff` である。

## 実native referenceの完了と回収

17:15 JSTまでにreference265360のF・exit 0・run_count 1を確認し、専用controllerのcompleteと回収を一度だけ実施した。
実walltimeは16分34秒、CPU timeは16分24秒、memoryは520,092 KBだった。
reference ZIPは8,024,988 bytes・371 memberで、全member・元task marker・元production identity、controller/worker completion、configと実PBS終端を照合した。
ZIP SHA-256は `9001df2430e8a2603a54fabfc693276e973e9b9d0d00d6b2b32b0fa269de2d41`、export manifest SHA-256は `fd8305e6c9353eec7e7e9973217ba0e1dbc0c7d308a7a25e7731019bd7b80903` である。
[回収受理record](data_tile_validation_2026-10-17/portable_condition_c1t0_native_reference_collected_v1/accepted.json) のSHA-256は `090ae150168777eddef377c6e1e2649c90382db2c96db0df65efe63d1941dd41` である。
native reference rootのcompleteと `collect_c1t0_native_reference_v1.py` の回収は使用済みであり、再実行しない。
PC parity・初回batch配置は未実施であり、各hostの旧最終batch正常回収とprocess終了を待つ。
この単一群referenceの受理は全群collectorの復旧や科学cohortの完了ではない。
