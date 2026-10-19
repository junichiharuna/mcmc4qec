# 低ノイズ selector の正式実行に向けた最小親入口案

本書は親レビュー用の小仕様だけであり、wrapper実装、正式inputやpinの作成、remote操作、qsubは行っていない。
既存 `tile_low_noise_timing_selection.run(input_path, expected_sha256, output)` と受理済みLinux selection-v1を再利用する。
選択規則、科学関数、24行、192分母、既存bundleを変更せず、新科学moduleや汎用schedulerを追加しない。
第4段階の `tile_low_noise_timing_evaluation_report.selector_evidence` が要求する7descriptorに接続する。

## 開始条件と正式input

case 0..3 × target index 0..2の全12本校正について、sampling、anchors、全BAR analysis partition、full trace audit、最終collection、最終audited comparison reportが完了し、親の受理済み証拠が揃うまで正式inputを作らない。
固定WSS referenceの全16条件audit成功と、対象12条件のreference/report bindingも必要とする。
完了subsetを使った先行選択、pendingをcompleteへ補完すること、rawから今回得たhashだけを外部受理済みpinと呼ぶことは禁止する。
欠損・未受理・終端未取得が一つでもあれば、入口は未準備理由のmetadataだけを返し、正式input/selector job/descriptorを作らない。
既存selectorのpending用全24行出力は探索状態の表示には使えるが、本入口の正式selectionを代替しない。

正式inputのexact top-levelは `schema=1`、`purpose='low_noise_timing_selection_input'`、`source_sha256`、`conditions` とする。
conditionsは重複なしの全12identityで `status='complete'` とし、case/target順を固定する。
各entryは `root,audit_root,reference_root,reference_audit_root,reader,final_report,final_submission,terminal_receipt,input_sha256` を持つ。
別collection jobがある場合は `collection_submission`、staged readerの場合は既存受入済み `staging_control_pins` も必須とする。
readerは実際のsingle/partitioned/staged経路を明示し、都合のよい経路へ読み替えない。
各entryのinput_sha256には、selectorの `load_complete` が要求するmetadata、submission、script、WSS auditの対象三重artifact、正式terminal集合を親の既存受理記録から結合する。
必要metadata一覧は既存reader契約をauthorityとし、path名やjob番号を推測して埋めない。
全raw payloadの再hashは親の準備時には行わず、PBS内の既存readerへ委ねる。
元sampling/referenceの記録済み失敗を全分母へ残す既存allowed-exit契約を維持し、全上流F0を一律要求して失敗標本を除外しない。
解析・audit・collection・最終reportの必要成功条件は緩和しない。

## 配置と実行環境

selector sourceは `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-selection-v1/cluster_scripts/tile_low_noise_timing_selection.py` の受理済み実pathを使用する。
source closureは既存 `selector.source_hashes()` のresolved authority path→SHAと一致させ、staging/control aliasの既存解決先も維持する。
新しい実行rootは全入力rootの外に排他作成し、旧sourceのcopyや既存rootの書換えを行わない。
既存selection-v1の受理済みclosure/PYTHONPATH順を使い、実際にimportされるsourceの追加・差替えを拒否する。

Pythonの実呼出pathはstage3/bridge/第4段階と同じ `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-stage2-v1/venv/bin/python` に統一する。
selection-v1側の別Python aliasへ読み替えず、同binaryであることに加えて呼出pathを固定する。
第4段階担当と、このpath・既存selector sourceの組が `selector_evidence` と整合することを確認した。
runtimeのexact構造は `{'runtime': calibration.runtime(), 'scipy': version('scipy'), 'python_path': invocation, 'python_sha256': binary_sha}` とし、第4段階の `runtime()` と一致させる。
single-thread4変数、PYTHONHASHSEED=0、PYTHONDONTWRITEBYTECODE=1を固定する。
Python最適化による検査無効化を拒否する。
依存科学moduleのimport前に、受理済みsource/core/Python/nativeのbyte/path pinをstdlib-only gateで確認する。
native bindingは固定profile/fixture・既存native binaryと受理済み環境metadataのpath→SHAであり、このwrapperがfresh native probeや全物理状態の再decodeをしたとは記録しない。
一方で既存audited reader自身は小native fixtureを現在のprocessで再実行するので、wrapper descriptorの固定byte検査とreader内部の実probeを区別する。

## 最小親入口と1回投入

実装承認後は親用の一回処理を一つ作り、準備・投入・終端sealのmetadata処理をまとめる。
PBS scriptは固定した前gate、既存selector CLIの直接1回呼出し、後gateだけを実行する。
script中に `shlex.join(selector_argv)` の行をちょうど1行置き、selector CLIを別runnerの内部呼出しへ隠さない。
前後gateの制御は同じ親入口が生成する固定scriptに含め、新しい科学moduleを設けない。
受入済みsourceと実argvを守るため、親入口自身もsource SHAとscript bytesを保存する。

prepareはmetadata-onlyで全12完了証拠、resource、外部pin、fresh出力を確認し、正式inputとprepared/scriptを別々に排他保存する。
資源未確定ならprepare/executeを拒否し、上限候補をそのまま確定済みresourceへ変換しない。
確定resourceには全12 final/collectionの実費用とstaged copy/hash費用の根拠、scope差、保守係数、親の確定判断を固定metadataとして結合する。
submitは共通 `tile-low-noise-submission.lock` の所有token、controller不在、queuedを含む全体最大2nodeを確認し、intentを排他保存する。
intent保存後にも所有・node/controller・現input/prepared/source/core/native/Python/script/intentを再照合し、その後にqsubを一度だけ呼ぶ。
実stdout/job idを保存し、submissionに実job_idを結合する。
曖昧応答やtimeoutではintent/lock/応答証拠を保持し、自動retry、再qsub、別outputへの無断置換をしない。
他者のlockに変わった場合は削除せず、qsub前なら呼出0回で停止する。

計算nodeの前gateはPBS_JOBIDと実receipt、qstatのR・run_count=1・script・1node/resource・hostnameを確認し、入力source/runtime/Python/native bindingを再照合してexecutionを排他保存する。
続いて既存selector CLIを1回実行する。
selectorは全12のaudited readerから保存raw・ACF・全分析rows・WSSと終端証拠を再照合し、全24行を排他保存する。
全24のidentity/order、production_selection_validated=true、input_manifest_sha256、12 calibration bindings、source closureを後gateで確認する。
selected/ineligible/unmetを全て残し、speed_ratio=nullと精度・被覆の非保証flagを維持する。
source/runtime/Python/nativeと正式input bytesの終了時再照合に加え、selector内の全consumed input hash/resolve前後照合が成功した出力だけを完了とする。
後gateが失敗してselectionファイルだけが存在してもcompletion/descriptorを作らず、未受理artifactとして保持する。
compute内から自分のPBS Fを主張しない。

## 第4段階へ渡すexact descriptor

descriptorのexact keysは `prepared,intent,submission,script,execution,completion,terminal` とし、各値は元fileの絶対pathと外部byte SHA256のpinである。
selection report自体は別のselection pinで渡す。
preparedには `schema:1,purpose:'low_noise_timing_selector_execution',input:{path,sha256},report_path,selector_argv,source_sha256,runtime,python_path,python_sha256,native_binding,resource` を保存する。
selector_argvは `[同Python呼出path,既存selector絶対path,'--input',inputpath,'--expected-sha256',inputsha,'--output',reportpath]` である。
resourceは既存stage3型の `cpus,workers,memory_gb,wall_seconds,walltime,requested_nodes:1,max_nodes:2` とする。
intentは少なくとも `manifest=digest(prepared),command=['qsub',絶対script],script_sha256,resource` を持ち、submissionはその全値に実job_idだけを加えたものとする。
executionのexact構造は `manifest,pbs_job_id,hostname,input_sha256,selector_argv,source_sha256,runtime,python_path,python_sha256,native_binding` とする。
completionはexecutionの全値に `report_sha256,complete:true` だけを加えたexact構造である。
独自の追加値をexecution/completionへ入れず、wall/CPU/RSS・実PBS照会や追加control証拠は別sidecarへ保存する。

親sealは実qstatからF0/run_count=1、実script/Submit_arguments、resource/hostnameを取得し、descriptor対象bytesと全start/end bindingを再確認する。
terminalは必要fieldsだけを保存し、現qstatを捏造・推測したJSONで代替しない。
第4段階の実 `selector_evidence(descriptor,selection_pin,proof)` が通り、proofの終了時再照合が成功した場合だけdescriptorを正式受理する。
旧single readerが元jobについて未検証の全資源/run_countを、このselector jobのF0によって遡って認証したとは扱わない。

## 読取量と保守的な初期資源案

静的に追った正式selectorの経路は次のとおりであり、保存traceからACF・IAT・BAR・bootstrapを再計算する経路には入らない。

| 呼出経路 | 実際の処理 | 実行しない処理 |
| --- | --- | --- |
| `tile_low_noise_timing_selection.py:220–223` → `read_audited_collection` | single/partitioned/stagedを明示選択し保存結果を検査 | sampling・analysis jobの再起動 |
| `tile_low_noise_analysis_partitions.py:272–297` → `validated_groups:224–231` → `read_group:115–156` | 保存analysis NPZ読込、ACF key/shape、入力marker、rowsのidentity/countとJSONL一致 | ACF/IAT計算、`run_partition:159`、`analyze_group` |
| `tile_low_noise_audited_collection.py:119–205` | 保存audit結果とraw三重artifactのhash/identity、analysisとauditの結合、前後rows一致 | 全trace checkpointの再復号、anchor MC replay |
| `tile_low_noise_staging_control.py:263–269` → `read_all:252–260` | 保存phase metadata、実PBS終端とcontrol pin | `compute`やanalysis/audit再実行 |
| `tile_low_noise_staging.py:397–402` → `read_staged:268–270` → `_read_staged:234–265` | audited reader前後の各1回で、tree列挙・全copy payload hashを各2回照合 | copy再実行、科学解析 |
| `tile_low_noise_audited_collection.py:151–153` → `audit_tile_low_noise_traces.validate_native_environment:19–33` | 現processの小native fixture probe、固定profileとの一致 | 全保存状態の再復号 |
| `tile_low_noise_timing_selection.py:235–239` → `tile_low_noise_reference_comparison.compare_rows:32–47` | 保存point/interval/診断flagからbias・RMSE・被覆・paired summaryの算術、保存stratum countからWSS合成 | 元BAR推定・bootstrap・WSS標本生成 |

partitioned readerも同じ `read_group` と `verify_group` を用い、上記と同じ区別になる。
singleのaudited readerでは保存analysisを初回collection、中間group結合、終了時collectionの3回検査するため、NPZ展開・JSON解析・hashの重複費用は存在する。
staged readerはさらに全copy payloadの4走査を加えるので、同じbyte量でもsingle readerと所要時間を同一視しない。
selector外側も `evidence_sha256` を取り込むときと `proof.finish()` で再hashするため、保存受理証拠を参照するだけの処理ではない。

既存低ノイズ計画では4kernel/initialization組×192repで1条件768group、12条件で9,216group、anchorは2,304件である。
fine rung数はtarget順に10/13/15、case別chain数は16/8/8/8なので、予定trace taskは `768*(10+13+15)*(16+8+8+8)=1,167,360` 件となる。
trace三重artifactだけで3,502,080filesであり、analysis・audit・measurement・anchor・WSSのfilesは別途存在する。
現設定のanalysisは1group88行、各条件67,584行、全12条件811,008行である。
compact3系列の非圧縮要素量だけで約323.55GiBとなるが、NPZ実bytes、総I/O量、RSSではない。
checkpoint・初期終状態・ACF・JSON metadataと複数回hashを含まず、圧縮率も未実測なので、この数を実転送量や所要時間に変換しない。
readerは条件ごとの全rowsをmaterializeし、全12条件にまたがるEvidence mapを保持し、公開前に入力を再照合する。
既存synthetic analysis capacityの数秒/数分はBAR解析を含む別処理であり、selectorのI/O throughputや完了時間に流用しない。

実行方式は1node・1CPU・1workerを候補とし、資源量は未確定である。
340GiB・24時間は検討可能な政策上限としてのみ残し、現時点でこの内側に完了する実測根拠はない。
既存selectorは直列readerなので96CPUを要求せず、未知の大きなpath/hash map・JSONの複製と全payload読取に対して既定1node上限を安全側に使う。
これは資源要求の政策上限であり、完走予測、メモリ安全性、24時間内完了の保証ではない。
全12の最終report/collectionが揃った時点で、既存PBS elapsed/RSS、保存されたfile/row数・bytes情報をmetadataから追記して、今回selectorとのscope差と保守係数を明示する。
各final jobが実際に通ったreaderが同じかを確認し、全12の経過時間の和を基準に、selector追加hash・JSON/集計・全条件Evidence保持の費用を別に見積もる。
final reportは条件別にprocessを終了する一方、selectorは全12のEvidence mapを保持するため、RSSの最大値だけをselector RSSとする見積りは禁止する。
現在参照できるsynthetic analysis capacityは8tasks/8workersでphase約240.34秒、task約212.9–239.6秒、peak RSS約277–279.45MiBだが、人工compact系列のBAR解析を含むのでserial selectorへの外挿根拠にならない。
元96workerの解析時間をそのままserial化する推定も、解析を再実行しない上記経路とは対象が異なるため用いない。
必要容量がこの上限に収まる根拠がない場合や既存実測が明らかに上限超過を示す場合は、正式投入を停止して親へ資源再設計を戻す。
この小仕様では追加科学capacity、raw削減、条件partition、並列selector、新しいseedを作らない。
wall/OOM/validation failureでは全24 selectionを完了扱いせず、実費用と残留artifactを保持し、同じinputへの自動再実行をしない。

保存済み受理済みreportとexact全payload mapを外部pinし、current raw hashだけを再照合する代案は、NPZ展開・group/row再検査の反復を減らしうる。
ただしsource/runtime/native・path retarget・全入力census・各前後hash・元受理範囲・row/report結合を失わない別契約と受入が必要であり、単なるsummary自己申告への置換は同じ保証範囲にならない。
現経路には全ACF/BAR再解析がないため、この代案を現時点では採用せず、既存final/collection実費用を見て具体的なI/O制約が確認された場合だけ別の小仕様へ戻す。
本書に伴う既存reader/source変更は行わない。

## 親wrapperの入力interface

新moduleは `submit_tile_low_noise_timing_selection.py` だけとし、prepare/submit/begin/finish/sealを同じ入口に置く。
prepareは外部SHAで固定したconfigを受け取り、config中の正式selector input pin、親の全12受理receipt pin、資源確定decision pin、環境closure/native/Python/pathを検査する。
親受理receiptは `status='accepted_all_twelve'`、正式input SHA、case/target順の12entry canonical digest、各entryの最終report/上流terminal pinを結合し、外部pinされた既存受理判断の集約であると明示する。
共通reference_audit summary pinも結合し、全16条件の成功・終端・phase failure不在をmetadataで確認する。
receiptをwrapperが自動で捏造・自己承認する機能は持たず、computeの既存selector full validationは省略しない。
資源decisionは `status='confirmed'`、resource、全12条件のfinal/collection PBS証拠pin、staged時のcopy証拠pin、wall/RSS評価根拠、保守係数、scope差、親確定理由を必須とする。
実費用の数学的上界とはせず、wrapperは確定metadataの完全性・正数・resource上限・外部pinを検査する。
finalのPBS job IDは受理済みreportへ、collectionのjob IDは固定 `partition-collection/summary.json` へ結合し、実terminalのF0・resources_used walltime/memを読み取る。
collectionに独立jobが無い場合は `included_in_final=true` とし、同一jobを二重計上しない。
finalのscript/ledgerは正式inputの既存pinへ結合する。
staged copyは実summaryのdestination・copy job・copy成功flag・elapsedと実F0/PBS費用を結合し、追加hash pass数2以上・copy時間係数1以上から下限proxyを検査する。
wall基礎量は全12の実final/独立collection時間と追加hash予算の和以上、memory基礎量は各実RSS以上とし、全12Evidence保持の追加見積りとscope差は親の確定判断として明示する。
親の固定判断とraw再検査を区別するため、preparedとは別のcontrol metadataにconfig、受理receipt、資源decisionとsource/core/Python/nativeのpath/byte bindingを保存する。
scriptからbegin/finishへcontrol SHAとprepared SHAを明示的に渡し、submit/sealにも親が外部固定したcontrol SHAを要求する。
出力root、intent、lock、script、control、prepared、execution、completionはregular file/pathとして固定し、同byteのsymlink置換や親directoryの解決先変更も拒否する。
import前gateはsource mapから全cluster moduleとcore packageのmodule censusを導出し、全core Python fileとactual originの完全一致を要求する。
固定sourceのASTからローカル依存を読んでclosureの欠落を拒否し、origin照合でdotted module名を許さず、find_specのparent import副作用を避ける。
qsub例外はcommand、returncode、例外型と説明、partial stdout/stderrを保存し、bytesの部分応答はbase64で可逆保存する。

## 実装承認後の軽量受入案

1. 12条件の1欠落・重複・pending・不正なcomplete宣言で正式input/qsub/descriptorを作らず、正しい全12だけを通す。
2. stage4実readerに7descriptorを渡し、input/report/source/Python/native/runtime/script/resource/host/run_countの1項目変更を拒否する。
3. scriptの既存selector argv行はちょうど1回であり、旧source pathとstage2 Python呼出pathを維持する。
4. 全24行・全192分母・全候補・全12 bindingを確認し、ineligible/unmetを除外せず速度比をnullとする。
5. mock schedulerでmax2/controller/shared lock、intent後の4変異、qsub0回/1回、曖昧応答保持、二重投入拒否を検査する。
6. PBS guardとimport前byte gateが全raw読取前に働き、prepare/sealはmetadataしか読まず、全payload走査は既存selectorのPBS経路だけに置く。
7. 読取中source/input/path retargetと後gate failureでcompletionを作らず、未受理selectionを成功扱いしない。
8. 実小selector fixtureとstage4 descriptor readerを接続し、mock/native固定bindingの範囲を正式raw監査やfresh native probeと混同しない。
9. resource未確定・全12費用根拠欠落・staged hash費用未評価ならprepare/executeを拒否し、mock確定metadataを用いた受入でも正式資源を測定済みと主張しない。

受入は1file60秒以内の小fixtureのみとし、正式12入力や全raw scanを含めない。
本書は仕様段階であり、上記wrapper受入、正式input、remote、qsubは未実施である。
