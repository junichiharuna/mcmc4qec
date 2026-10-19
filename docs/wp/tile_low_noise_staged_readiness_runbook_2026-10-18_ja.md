# staged case2 target0のreadiness固定と実行順

本書は承認済みwrapperを変更せずに使う手順であり、正式copyは未実施のため実job ID・elapsed・新SHAを記入していない。
以下のprepare・executeは親だけが実行し、本書作成時点では実施していない。
`D=docs/wp/data_tile_validation_2026-10-17`、`W=output/submit_low_noise_staged_phase_once.py` とする。
Wの承認SHAは `378cca64cec2852c61ffa36f0ed79654d4cb01e4447d74a48475831b14b5e025`、独立受入は `D/low_noise_staged_phase_wrapper_independent_acceptance_v1.json` のSHA `5bdbea1626a01b42be1561cc569e5c9566af752ab0dd3782296ccdafb1fe3b10` である。

## pinのauthority

| readiness項目または前提 | 一次の根拠と照合先 |
|---|---|
| source/import/native/Python | Wの `local_accepted()` が外部固定したcopy wrapper SHA `77728306dd338e69135a2e66a7033317e4be4eca9f8f0378e319867a05204149` と既存配置/受入証拠から返す `preimport` と `software` を使う。remoteで今読めたsourceのhashを新しい正解にしない。 |
| control/staging/v11 | control-v2 deployment・Linux acceptance、staging-v1 deployment・Linux acceptance、v11 Linux provenanceを、上記copy wrapperのFIXED SHAで先に照合する。実control/staging import path、staging symlink先、全import root source censusをWの既存gateで照合する。 |
| 元samplingのmanifest/script | `local_accepted().original_manifest_sha256` と `.original_script_sha256`。固定root `.../20261018-tile-low-noise-v2/runs/production-2-0` の実bytesと比較する。 |
| 元samplingのsubmission | `local_accepted().original_receipt` と実 `submission.json` の内容一致、265259の現在F0、実low-noise.sh・run_count/resources/hostとの結合。 |
| analysis capacity | 固定265264、v3/runs/capacity-2-0の保存measured_profile SHA `33308fa70322c4ce031407362e601326e276b8e09de016b56a394f767d2dbfe8` とPBS stability supplement SHA `996236dd39ab18676697c1c55134c3fb21a99db75fefb90afdf3ad6852847eed`。supplementのscript/submission/intent pinsと現在の選択PBS fieldsを再照合する。 |
| copy job IDとreceipt | 親が実qsubで得たcopy wrapperのlocal stdout/receiptを別SHAで固定し、remote copy rootのsubmission.json・intent・stage.shへ結ぶ。まだ存在しないjobを指定しない。 |
| copy source/input/script | 承認済みcopy wrapperのaccepted_inputsとrender_scriptによる固定期待値、親保存prepared/readiness SHA、remoteのplan/accepted-inputs/stage.shを結合する。copy sourceを現在のsourceから自己承認しない。 |
| origin | 承認済みstaging readerの `read_staged_provenance(destination)` の実返値をそのまま使用する。全rawを読む `read_staged` はloginで呼ばない。 |
| copy seal/metadata | 上記readerがplan/summary/seal、元計画・全分母、copy receipt、copy F0を結んだ後、その同じ実bytesのSHAと解決先を保存する。読み始めと読取後に再照合する。 |
| phase prepared | 親が行ったW prepareの保存stdout/receiptと、その返却plan pathから回収した実prepared bytes。SHAとscript/resourceを既存control.checkedへ照合し、返値だけを未照合で転記しない。 |
| phase receipt | W executeの保存stdout/receiptとremote submission.json。preparedに実job_idだけを追加した内容、prepared SHAとreceipt SHAを照合する。 |

## 初回readiness R0

親のcopy qsub receiptが未取得、copyがR/Q/E、F非zero、元sampling非F0、seal欠損、入力変更のいずれかならR0を保存せず停止する。
Wとaccepted copy wrapperのsourceを外部SHAで検査してから、その固定bytesを実行する。
remoteでは先にaccepted preimport/source census/実origin/native/Pythonを照合し、それから既存control/stagingをimportする。
copy現在F0と元sampling265259現在F0、capacity265264現在F0を選択fieldだけで確認し、copy readerの前後でも同じPBS記録であることを確認する。
PBS保存fieldsは `job_state,Exit_status,run_count,Submit_arguments,Resource_List,exec_host` だけで、Variable_Listは保存しない。

R0のJSONは次の実測項目だけを持つ。

- `schema:1, case:2, target_index:0`。
- `origin` は実metadata-only reader返値の全体。
- `pbs` は265259、265264、実copy job IDをkeyとする上記6 fields。
- `files` は下表の各絶対pathをkeyにした `{"sha256":実SHA,"resolved":実解決先}`。
- `phases:{}`。

| root | R0で固定するファイル |
|---|---|
| control-v2/runs/copy-2-0-v1 | plan.json、summary.json、execution-intent.json、submission-intent.json、submission.json、stage.sh |
| v11/runs/staged-production-2-0-v1/.staging | plan.json、summary.json、seal.json |
| low-noise-v2/runs/production-2-0 | manifest.json、low-noise.sh、submission.json |
| low-analysis-v3/runs/capacity-2-0 | stability supplementのpins全4件：analysis-capacity.sh、execution-intent.json、submission-intent.json、submission.json |

表の `v11` は `/home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11`、`control-v2` は同baseの `20261018-tile-low-staging-control-v2` を表す。
他二つは同baseの `20261018-tile-low-noise-v2` と `20261018-tile-low-analysis-v3` であり、実装ではWの固定定数を使用する。
コピー後metadataは一回読み取ったbytesをparseしてhashに結び、保存直前にも全hashと解決先を再検査する。
R0は新規 `D/low_noise_staged_2_0_readiness_r00.json` などへ排他保存し、転送した場合は転送元bytes/転送先bytesのSHA一致を確認する。
親は保存された実SHAを別の取得証拠へ固定し、以後 `--readiness-sha256` にその値を明示する。
raw traces、anchors、npzの走査やcopy再実行はこの工程に含めない。

## 正確な実行順

共通呼出しは次の形であり、`$readyPath` と `$readySha` には直前に固定した実値だけを入れる。

```powershell
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' output/submit_low_noise_staged_phase_once.py --action prepare --phase analysis --index 0 --readiness $readyPath --readiness-sha256 $readySha
```

1. R0でanalysis index0のprepareを一度行い、返却plan/scriptの実bytesを検証する。
2. 既存R0を上書きせずR1を作り、`phases["analysis:0"]={"prepared_sha256":実prepared SHA}` だけを追加する。
3. R1で同phase/indexの `--action dry-run` を一度行い、bash -n・実argv/resourceを確認する。
4. 同じR1で親が空きを判断して `--action execute` を一度行う。
5. execute返却と実submission.jsonを照合後、R2に同phaseの `receipt_sha256` を追加しprepared SHAを維持する。
6. 親の通常監視で実Fを確認してから、R2で `--action completion` を一度行い、controlの終端結果を別の新規証拠として保存する。
7. 実partition manifestに複数indexがある場合は全indexへ同じ手順を適用するが、固定capacity2-0の正式profileは現在index0の1 partitionである。
8. trace-capacityはindexを指定せず、prepare→prepared pin追加→dry-run→execute→receipt pin追加→F後completionの同じ順で進める。
9. trace-capacityのcompletionがstatus successでF0の場合だけ、prepared/receipt両pinを持つreadinessでtrace-fullのprepareを行う。
10. trace-fullも同じ一回手順を進め、全analysisとfull trace auditが成功終端するまでcollectionをprepareしない。
11. 全analysisとtrace-fullの両pinを固定したreadinessでcollectionをprepareし、collectionのprepared pin、次に実receipt pinだけを後続版へ追加する。
12. collectionのdry-run→execute→F0後completionを行い、成功保存された全rows/evidenceだけを後段へ渡す。

analysisとtrace-capacityはcopy成功後なら依存上は並行可能だが、実行は常に共有lock・queuedを含め最大2node・一回qsubのguardを通す。
phase追加時のR1/R2等の番号は例示であり、実際には全条件の更新順で単調に増やして既存版を残す。
phasesの値には `prepared_sha256` と必要時の `receipt_sha256` 以外を入れず、plan pathやjob IDは別の取得証拠に保存する。
baseのorigin/files/pbsを変更せず、既存phase pinsも書き換えず、必要なkeyだけを追加する。
collection prepare後は、そのcollection keyへのpin追加以外に他phase pinsを変更しない。
resourceは基礎解析96 workers/48GiB/1h30にcopy実測由来の既存headroomが追加されるため、実prepare返値を見るまで最終walltimeを記入しない。
collectionの1CPU32GiB24hは初期上限であり完了予測ではない。

## 証拠名と停止条件

Wのlocal出力prefixはanalysis index0なら `D/low_noise_staged_2_0_analysis_0_{action}_v1`、trace-capacityなら `D/low_noise_staged_2_0_trace-capacity_{action}_v1`、他phaseも同じ規則である。
各prefixに `_intent.json,_script.py,_stdout.txt,_stderr.txt,_receipt.json` が排他保存される。
prepareのremote stdoutにはplan/prepared_sha256/script_sha256/resourceがあり、executeにはsubmitted/prepared_sha256/receipt_sha256がある。
local receiptのoutput_sha256とstdoutのbytesを照合し、その後remote実ファイルの同一bytesを回収・確認してreadiness次版へ追加する。
既存local prefixがある場合は再実行しないため、未終端の状態でcompletion actionを試さず、軽い通常PBS監視でFを確認してから一度だけ呼ぶ。
曖昧応答、timeout、partial prepare、guard失敗、recorded audit failureでは全証拠を残して停止し、勝手に版番号やrootを変えて再投入しない。

## 最小readiness builderの提案（未実装）

新規候補 `output/build_low_noise_staged_readiness.py` は `initial` と `extend` の二操作だけを持ち、既存Wは変更しない。
initialは外部SHA付きの親copy準備/投入証拠を必須入力とし、上記accepted source gates→現在F0→metadata-only reader→hash/解決先の前後一致→R0排他保存だけを行う。
extendは外部SHA付きの前readiness、対象phase/index、Wの成功local invocation receipt/stdout、対応remote preparedまたはsubmissionの実bytesを要求する。
同一bytesのpinをparseに使い、preparedは既存control.checked、receiptは既存control.receipt、completionを使う遷移は既存control.read_completionで照合し、collectionだけはWの既存専用check/receipt/completion関数を再利用する。
extendはbaseと既存phase pinsをそのまま保持し、対象phaseの新prepared pinまたはreceipt pinだけを追加して、差分一覧と新ファイルSHAを別証拠へ保存する。
builderのsource自体も独立受入後に外部SHAを固定し、raw reader、plan作成、prepare、qsub、既存root/source変更を呼べないAPIに限定する。
未終端copy、job取り違え、source自己承認、import shadow、同bytes別path、metadata読取中変更、未承認phase更新、曖昧invoke、既存出力への上書きを軽量受入で拒否する。
現時点ではこのbuilderは仕様案だけであり、正式readinessはまだ作っていない。
