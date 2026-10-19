# 全数監査の実行準備

## 2026-10-18 15:33 JSTの到達点

主4条件のsamplingとanalysis archiveは全て回収し、全member/identity/payload/hashと受入済みworker/scriptの結合を検証した。
最後のanalysis case0は265231、sampling case2は265232がともにF・exit 0で終了した。
根拠は`data_tile_validation_2026-10-17/production_analysis_recovery_case0_20261018-v2-tile-case0-analysis-recovery.json`と`sampling_case2_collection_stage_binding_v1.json`にある。
full trace監査も全4条件・各768群で完了し、`main_trace_audit_completion_v1.json`に保存した。
現在の全payloadとBAR row、保存監査、reference/anchorを結合する最終再集計runnerはv10へ配置し、Linux46件の関連受入を完了した。
case1の265236はF・exit 0で終了し成果物照合中、case3の265238は実行中、case0/2は入力証拠と固定planを準備済みで未投入である。
混合一覧は最終再集計の監査reportを入力にして後続実行し、保存診断の集計と診断値の独立再計算を区別する。

## 2026-10-18 15:00 JSTの実行状況

主4条件のsamplingとBAR解析が全て正常終了し、controllerのfinished記録とPID不在を確認した。
case0 sampling回収265219もF・exit 0で終了した。
全86,208 artifact・258,630ファイル、7,866,545,400 bytesのarchiveを回収し、全member照合と固定stageへのworker/script結合を完了した。
証拠は`data_tile_validation_2026-10-17/sampling_case0_collection_stage_binding_v1.json`に保存した。
sampling case2とanalysis case0の回収は未投入であり、主4条件のtrace数値監査も未実施である。

seed全数照合265220と、事前固定16条件の重み層別reference265221をqsubし、計2ノードで実行中である。
重み層別referenceの実投入は`weight_reference_submission_stdout_v1.txt`、直前の独立照合は`weight_reference_pre_submission_recheck_v1.json`に記録した。
主trace監査のcapacityはsampling完了に依存し、analysis archive回収の完了には依存しないため、空きslotで進める。

## 2026-10-18 14:43 JSTの回収進行

case2解析archiveも転送と全2,315 member・768 artifactの整合性検証が完了した。
archiveは4,477,986,977 bytes、SHA256は`3431a5a84aa13ca0773ed8ebd92dab34feb3840b357496a7e614264183707410`である。
`data_tile_validation_2026-10-17/production_analysis_recovery_case2_20261018-v2-tile-case2-analysis-recovery.json`と`analysis_export_case2_collection_observation_v1.json`に回収・PBS正常終了・accepted stageへの結合と時刻差の注記を保存した。
これでcase1/2/3の解析archiveが揃ったが、数値再解析と全trace監査の成功を意味しない。

## 2026-10-18 14:40 JSTの回収進行

case3解析archiveの転送と全2,315 member・768 artifactの整合性検証が完了した。
archiveは3,087,175,636 bytes、SHA256は`d213d22dbbf34c52790b3955c9731ffc75901f5727edc857e124a728ca0089e1`である。
証拠は`data_tile_validation_2026-10-17/production_analysis_recovery_case3_20261018-v2-tile-case3-analysis-recovery.json`に保存した。
case2解析回収265218のF・exit 0・wall 3分33秒を確認後、collectを開始した。

sampling回収case0/2のstage・helper・脚本と元samplingの正常終了を別担当が再照合し、`sampling_export_stages_readonly_check_v1.json`に保存した。
case0 sampling回収は、追加投入予定なしの証拠と全pins/8ledger/stage hash/global要求ノード数1以下を各投入直前に確認する同じ手順で、265219としてqsubした。
1ノード・1 CPU・4 GB・1時間要求で、既存科学解析と合わせ最大2ノードとする。
正常終了後のsampling v2 collectに加え、downloadしたworkerとexport.shを固定stageの既知hashに照合して証拠保存する。
これは自己申告worker hashだけへの依存を避ける回収時の追加検査であり、固定helperや稼働sourceは変更しない。
265219の正常終了・collect・追加検査は投入時点で未実施である。

## 2026-10-18 14:35 JSTの回収進行

case1の265216は正常終了し、1,943,166,818 bytesのarchiveを転送して全2,315 member・768 artifactの整合性検証に成功した。
archive SHA256は`19ccf9223b94a8e1178bafbb460ca21d94c1256be77ad5b6fa9f49084f944b2f`である。
回収証拠は`data_tile_validation_2026-10-17/production_analysis_recovery_case1_20261018-v2-tile-case1-analysis-recovery.json`に保存した。
worker時刻とPBS時刻にずれが見られるため、絶対時刻から所要時間を合成せず、原本・単調時計elapsed・PBS wall timeを別々に保持する。
数値再解析・全trace監査はこの回収検証に含まない。

case3とcase2のexportにも各投入直前の全8ledger・pins・stage hash・追加投入予定なし・global要求ノード数1以下の同じ確認を適用し、排他的intentの後にqsubを一度ずつ実行した。
case3は265217で正常終了・wall 2分36秒、collectは担当が実施中である。
case2は265218として投入し、PBS照合と正常終了後のcollectを別担当へ分担した。
対応する`analysis_export_case{2,3}_submission_script_v1.py`と`analysis_export_case{2,3}_submission_stdout_v1.txt`が各投入時の証拠である。
この記録は以下のstage時点の未投入記録を更新するもので、同じintentを持つ回収jobを再投入しない。

## 2026-10-18 14:30 JSTの回収投入

全8件の固定投入ledgerが存在し、controllerに未投入のstageがないことを独立確認した。
固定controller source・config・processとの結合、86 pins、controllerが作成した7組のintent/receiptとledgerの一致を確認した。
sample case3はcontroller開始前の投入でintent/receiptを持たないが、既存ledgerにより再投入を拒否する対象である。
実snapshotの選択は`wait(existing_jobs)`で、absentを含まない48状態の選択もwaitまたはfinishedのみだった。
証拠は`data_tile_validation_2026-10-17/production_controller_submission_exhaustion_v1.json`に保存した。

stage記録の「controller terminal必須」は競合を避けるための保守的な運用条件だった。
今回のcase1 exportでは、その条件を「全8件の固定ledgerとpinsを再照合し、追加投入予定がなく、qsub直前のglobal要求ノード数が1以下」に置き換えた。
稼働controller・科学計算bundle・設定は変更していない。
親担当が全根拠とstageのworker/script hashを再照合し、排他的なsubmission intentを保存してqsubを一度だけ実行した。
回収jobは265216で、1ノード・1 CPU・4 GB・1時間要求の実稼働を確認し、265212と合わせて計2ノードを維持した。
投入証拠は`analysis_export_case1_submission_stdout_v1.txt`、実行した検査・投入スクリプトは`analysis_export_case1_submission_script_v1.py`に保存した。
この変更を他の回収や未投入stageのあるcontrollerへ無条件に適用せず、各投入直前に同じ根拠とglobalノード数を確認する。
265216の正常終了・collect・archive検証は投入時点では未完了である。

## 2026-10-18 13:50 JSTの回収準備状況

tile288 bit-flipの解析265214がPBS F・exit 0となったため、固定v2 helperで`20261018-v2-tile-case1-analysis-recovery`へ回収脚本をstageした。
対象は2,315ファイル・2,492,080,765 bytesで、gateは0.370秒、stageは9.284秒だった。
script SHA256は`50d31a62cc0a0f682760449ced764fdefc61434e6003e899c765b0e18422787c`で、bash構文とCRLFなしを確認した。
証拠は`data_tile_validation_2026-10-17/production_analysis_export_stage_case1_20261018-v2-tile-case1-analysis-recovery.json`と`production_analysis_export_script_validation_case1_v2.json`にある。
既にstage済みなので同じrootへのstageを繰り返さない。
controllerと主BAR2 jobが稼働中のため、回収qsub・圧縮・collectは未実施である。
controller終端とqueued込み最大2ノードを直前確認してから、stage記録の脚本をqsubし、正常終了後にcollectする。

## 低ノイズtrace監査

`tile_low_noise_trace_audit_run.py`を追加し、同じproductionの全768群または事前固定した8群の資源計測subsetを監査できるようにした。
全rung・chainのcompact配列を検査し、初期状態と保存checkpointを同じ固定decoderで再復号する。
groupごとにcodeとProblemを一度だけ構築する。
全物理状態の再復号、全乱数軌道の再生、独立decoder検証を行ったとは扱わない。
sampling失敗は分母に保持し、missing・corrupt・監査例外は別の監査失敗として記録する。
全group終了後にpayload hashと完成sampling証拠を再照合する。
Windowsの13受入は3.99秒で成功し、独立レビューでも13件が成功した。
資源実測に基づく要求量の選択と専用qsub submitterも追加したが、実capacity・本番全監査は未実施である。

## 重み層別reference監査

`tile_weight_reference_audit_run.py`は元referenceの全16条件を各1task・16workerで監査し、条件を分割・再定義しない。
全raw draw・count・hashとsummaryを照合し、各chunkの先頭16個と末尾だけを再復号する。
監査成功とreference区間取得を区別し、失敗chunkによりreferenceが未取得でも予定条件を除外しない。
各conditionのwall time・CPU time・RSS、全phase時間を保存する。
`raw_artifact_bytes`は元artifactのbyte数であり、複数回のreadを含む実デバイスI/O量ではない。
初回は1ノード・96 CPU・340 GiB・24時間を上限とし、計測済み資源見積りや終了保証とは扱わない。

`submit_tile_weight_reference_audit.py`は元referenceの生成jobがqstatで終端Fであることを確認し、qsubを一度だけ呼ぶ。
元jobが記録済み失敗条件を持つ場合も監査するため、生成jobの終了コード0は要求しない。
queued込み最大2ノード、controller競合拒否、共有lock、source・package・Python・script・planの直前再照合を適用する。
曖昧なqsub応答ではintentとlockを保持し、自動再投入しない。
submitterのWindows受入は22 passed・11.38秒で、独立レビューでも同じ22件が成功した。

## 終端証拠の独立レビューと修正

WSS runnerの独立レビューで、成功taskの後にsourceが変わるとsummary保存前に停止する経路と、先に監査したraw chunk・個別summaryをphase終了時に再照合しない経路が見つかった。
成功16taskを保持したままsource・raw chunk・個別summaryを変更する3受入を追加し、旧挙動で失敗することを確認してから修正した。
成功reportの全入力hashをphase終了時に再照合し、異常を`phase_failures`へ集約する。
全条件の記録を保存し、`terminal_binding_valid=False`・`all_conditions_audited=False`としてsummary保存後に非zero終了する。
追加の終端read費用は`phase_wall_seconds`に含む。
修正後のWSS runnerは13 passed・39.05秒で、独立レビューによる差分確認も完了した。
新3 fileのWindows受入は個別に13・13・22件が成功し、core環境ではoptional依存がないため3 skipped・0.15秒、終了コード5となった。
実行記録と最終source hashは`data_tile_validation_2026-10-17/full_audit_windows_acceptance_v1.json`に保存した。
これらは小fixtureと投入を置き換えた受入であり、実PBSや本番全数監査の成功を示すものではない。

## Linux配置と受入

新規bundle `20261018-tile-low-analysis-v7`で、low-noise trace監査13件・WSS監査13件・qsub wrapper22件の計48件が成功した。
各fileのpytest時間は1.33秒・18.44秒・0.92秒で、固定Linux native profileと全比較項目が一致した。
旧core全29ファイルと既存driverを保持し、稼働production bundleと共有venvを変更していない。
archive SHA256は`2ec34d089befc889906a5f5fb1a9e1f15fb618f20c4313cb2c6e97970527527e`である。
ログ、source binding、環境証跡は`data_tile_validation_2026-10-17/low_analysis_linux_acceptance_v7.txt`、`low_analysis_source_binding_v7.json`、`low_analysis_linux_provenance_v7.json`に保存した。
元reference本番と低ノイズsamplingが未完了のため、実artifactを使う監査planの作成、資源実測、本番全数監査とqsub投入は未実施である。

## 再現手順

各runnerは、元の本番samplingまたはreferenceが完了し、対応するnative環境と証拠が揃ってからplanを作る。
元referenceを読み取り専用として、独立した出力先を使う。

```bash
export PYTHONPATH="$PWD/src:$PWD/cluster_scripts"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
venv/bin/python cluster_scripts/tile_weight_reference_audit_run.py plan \
  --root "$PWD/runs/reference-audit" --reference-root /absolute/path/to/reference
venv/bin/python cluster_scripts/submit_tile_weight_reference_audit.py \
  --bundle "$PWD" --root "$PWD/runs/reference-audit" \
  --reference-root /absolute/path/to/reference
```

2つ目のコマンドはdry-runであり、controller停止とqueued込み2ノード以内を確認できる状態で`--execute`を加えるとqsub投入する。
低ノイズtraceの資源計測planは次のコマンドで作る。

```bash
venv/bin/python cluster_scripts/tile_low_noise_trace_audit_run.py plan \
  --root "$PWD/runs/low-trace-audit-capacity" \
  --source-root /absolute/path/to/low-noise-production --capacity --workers 8
```

低ノイズのsampling capacityとは異なり、本番productionの全chain・全rungを持つ最初2 replicateを使う。
実qsub、全reference監査、低ノイズ全数trace監査と資源実測は未実施である。

## 低ノイズtrace監査の資源計画と投入

`tile_low_noise_trace_audit_resources.py`は、productionの最初2 replicate・8群を8 workerで監査した実測を要求する。
sampling失敗を含むcapacityでは再復号が省略され、正常な全群監査の所要時間を過小評価し得るため、full用の資源profileとして拒否する。
最大worker RSSの1.5倍と8 GiBの余裕から、340 GiB以内に入るworker数を最大96で選ぶ。
最大group時間と全768群のworker波数に、phase時間から最大group時間を引いた余剰の96倍を加えて所要時間を外挿する。
phase余剰には終了時の全入力再hashが含まれ、要求時間は外挿の2倍と600秒を加えて30分単位で切り上げる。
24時間または340 GiBを超える場合は投入せず、別途partition設計が必要となる。
8 workerの測定は96 worker時のI/O競合を測っておらず、2倍係数も完了保証ではない。
CPU時間は最大group CPU時間から別の量として保存し、walltimeと混同しない。

保存済みmeasurement・group監査・元traceのhash、全task/checkpoint件数、native・PBS・submission証拠を再照合する。
`prepare_full`は仮のworker数で資源を選択し、選択したworker数のfull planで再検証した後、新規rootへ保存する。
返す資源の`full_manifest`とworker数は保存済みplanに一致し、既存planを書き換えない。
`submit_tile_low_noise_trace_audit.py`は元sample・anchor jobの終端F、queued込み2ノード、controller停止、共有lockとqsub一回の規則を適用する。
capacityは1ノード・96 CPU・340 GiB・24時間を初回上限とするが、worker数は8に固定する。

前節のcapacity plan作成後、次でdry-runを作り、実投入時に`--execute`を加える。

```bash
venv/bin/python cluster_scripts/submit_tile_low_noise_trace_audit.py \
  --bundle "$PWD" --root "$PWD/runs/low-trace-audit-capacity" \
  --source-root /absolute/path/to/low-noise-production
```

capacityの完了後、次の順で新しいfull planとdry-runを作る。

```bash
venv/bin/python cluster_scripts/tile_low_noise_trace_audit_resources.py plan-full \
  --root "$PWD/runs/low-trace-audit-full" \
  --source-root /absolute/path/to/low-noise-production \
  --capacity-root "$PWD/runs/low-trace-audit-capacity"
venv/bin/python cluster_scripts/submit_tile_low_noise_trace_audit.py \
  --bundle "$PWD" --root "$PWD/runs/low-trace-audit-full" \
  --source-root /absolute/path/to/low-noise-production \
  --capacity-root "$PWD/runs/low-trace-audit-capacity"
```

Windows受入は資源計画20 passed・12.18秒、submitter33 passed・29.96秒で、独立レビューも行った。
後者には保存済みcapacity artifactから実reader・`prepare_full`・資源再検証・bundle照合・dry-runまでの結合と、measurement payload変更時の拒否を含む。
native・PBS・計測時間はfixtureなので、この受入を本番capacity実行や資源外挿の実証とは扱わない。
core環境はoptional依存のguardで2 skipped・0.15秒、pytest終了コード5となった。
Windowsの記録と最終source hashは`data_tile_validation_2026-10-17/low_trace_resource_windows_acceptance_v1.json`に保存した。
新規bundle `20261018-tile-low-analysis-v8`ではLinux53件が成功し、資源計画2.30秒・submitter2.84秒、厳密native profileは従来と一致した。
archive SHA256は`c5e709babb1d4aefeb5a00619b1d4391e6eb7976806fdf646e8535454d858702`である。
旧core29ファイルとv7の継承入力を保持し、受入後のローカルsourceもarchiveと一致した。
Linuxログ・環境・hashは`data_tile_validation_2026-10-17/low_analysis_linux_acceptance_v8.txt`、`low_analysis_linux_provenance_v8.json`、`low_analysis_source_binding_v8.json`に保存した。

## 解析と全数監査の最終照合

主校正には[主校正adapter](../../cluster_scripts/tile_audited_results.py)、低ノイズには[低ノイズadapter](../../cluster_scripts/tile_low_noise_audited_collection.py)を追加した。
いずれも全192 replicate・768 groupと予定taskを照合し、記録済みsampling失敗を分母から除外しない。
本番の全payload読取りはクラスタで行い、qsub・queued込み最大2ノードの制約を維持する。
現時点では実本番の全数照合を実行していない。

主校正の`read_results`はproduction root、full trace audit root、sampling・analysis・anchor・referenceのarchive検証と科学監査JSONを受け取り、保存rowsとsummaryの全cohort算術を再現する。
保存BAR比と共分散から点推定・標準誤差・区間を再確認するが、BAR solveやbootstrapを再実行しない。
既存analysisには解析時に消費したtrace・anchor hashがなく、`historical_consumed_input_hashes_recorded=False`として残す。
後付けのcurrent/archive入力と監査の一致を、解析当時の入力hash証明とは呼ばない。
CLIは`--root`、`--audit-root`、`--case`、`--sampling-verification`、`--analysis-verification`、`--anchor-verification`、`--anchor-audit`、`--reference-verification`、`--reference-audit`、`--output`を取り、PBS_JOBIDと新規outputを要求する。
必要な各JSONと確認範囲は[主校正仕様](tile_audited_results_spec_2026-10-18_ja.md)に記載した。

低ノイズの`read_audited_collection(sampling_root, audit_root)`は`(plan, rows, evidence)`を返す。
既存collectionを最後まで消費し、解析が保存した全sample markerとfull監査の入力marker、現在のpayload hashを結合する。
native環境も再probeし、192 anchorについては解析消費markerと現在artifactの整合性を確認する。
anchor MCの再実行、全物理状態の再復号、reference監査はこのAPIに含めない。
reference比較には既存comparisonを使い、同じcollection digestを最終証拠へ結び付ける。
APIと受入の境界は[低ノイズ仕様](tile_low_noise_audited_collection_spec_2026-10-18_ja.md)に記載した。

Windows受入は主17 passed・43.23秒、低ノイズ10 passed・33.83秒で、別担当の独立レビューを完了した。
小さい実保存artifactと明示した全数制御fixtureを組み合わせた受入であり、本番全artifactの通し検証ではない。
optional依存なしのcoreでは2 skipped・0.24秒だった。
記録は[Windows受入証拠](data_tile_validation_2026-10-17/audited_results_windows_acceptance_v1.json)にある。
旧coreを保持した独立bundle `20261018-tile-low-analysis-v9`でも主17件・13.32秒、低ノイズ10件・5.59秒が成功し、厳密native照合で差分はなかった。
archive SHA256は`9db7e16db4f23c6e7504d2a7a4c1b17cc428d5e1673a762e3cb962bb6a3d4e95`である。
Linuxの[受入ログ](data_tile_validation_2026-10-17/low_analysis_linux_acceptance_v9.txt)、[環境証拠](data_tile_validation_2026-10-17/low_analysis_linux_provenance_v9.json)、[source照合](data_tile_validation_2026-10-17/low_analysis_source_binding_v9.json)を保存し、既存production bundle・venvは変更していない。

## 主BAR解析artifactの回収

解析結果の回収には[固定helper v2](data_tile_validation_2026-10-17/recover_completed_tile_analysis_v2.py)を使用する。
小仕様は[回収仕様 v2](data_tile_validation_2026-10-17/analysis_recovery_helper_spec_v2_ja.md)に保存した。
元analysis jobのPBS終端・終了コード0・投入脚本との結合を確認し、全768群、正式summary、rows、固定manifest/context/referenceを保持する。
圧縮はPBS内の1 CPU・4 GiB・1時間上限で行い、全入力hashの前後一致とarchive hashを記録する。
要求時間は初期上限であり、完了時間の実測予測ではない。
回収時にはexport jobの終端と、stage時に固定したworker/script hash、archiveの全payloadを照合する。
独立レビューでstageへのhash結合不足を修正し、自己整合した変更worker/scriptとexport記録の組も拒否する受入を追加した。
最終source SHA256は`b303aaf1d915443da4f99b13405c51bcc0f6dba9a2ec0771421c8ff500506d05`である。

合成受入はWindowsで27 passed・2.80秒、独立したLinux受入rootで27 passed・0.23秒だった。
Linuxの実PBS脚本テンプレートに対する`bash -n`も成功し、受入後のhelper/test/verifierのhashは固定値と一致した。
根拠は[Windows受入](data_tile_validation_2026-10-17/analysis_recovery_helper_acceptance_v2.json)、[Linux受入](data_tile_validation_2026-10-17/analysis_recovery_linux_acceptance_v2.json)、[Linux環境・hash・脚本構文](data_tile_validation_2026-10-17/analysis_recovery_linux_validation_v2.json)にある。
これは合成artifactの検証であり、本番圧縮・collect・qsubは未実施である。
その後12:06 JSTにcase3の元解析PBS F・exit 0を確認して、新root `20261018-v2-tile-case3-analysis-recovery`へstageを実施した。
対象は2,315ファイル・3,890,389,474 bytesで、gate 0.379秒、stage全体9.328秒、固定source hash一致、bash構文成功を記録した。
証拠は`production_analysis_export_gate_case3_20261018-v2-tile-case3-analysis-recovery.json`、対応する`stage`記録、`production_analysis_export_script_validation_case3_v2.json`に保存した。
以下のstageコマンドは実施済みなので同じtagで再実行せず、controller終端後のqsubから続行する。
回収の整合性検証は科学的な再復号や混合・被覆の監査を代替しない。

以下はリポジトリ直下で行うcase3の例で、元analysis jobが完了した後にだけstageを行う。
別caseには`--case`を変更し、既存rootと重複する場合は新しいtagを使う。

```powershell
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" docs/wp/data_tile_validation_2026-10-17/recover_completed_tile_analysis_v2.py --case 3 --action stage --tag 20261018-v2
```

stageはqsubを呼ばない。
既存controllerの終端とqueuedを含め最大2ノードをlogin側で確認し、stageが表示する`qsub`を1回実行する。
実投入の記録を保存し、export jobの終了コード0を確認した後に、同じcase/tagで`--action collect`を行う。
stage証拠はcollectで必須の入力なので、削除や上書きをしない。
