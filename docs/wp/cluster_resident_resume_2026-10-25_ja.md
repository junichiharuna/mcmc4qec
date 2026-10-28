# ローカルPC再起動後のクラスタ処理確認

## 2026-10-25 20:18 JSTの後続計時確認手順

censusと全12条件の比較は受理済みで、独立計時の先頭MC/BAR各192反復は正式finish受理・回収まで完了した。
次の精度条件ではMC265729・BAR265731の予備計時が各2/2・F/0となり、MCの正式capacity finish265733が実PBSでRであることを20:18 JSTに確認した。
現在の数値結果と未完了工程は[状態文書](PROJECT_STATUS_2026-10-24_ja.md)を参照し、下の時刻付き旧記録を現在状態と取り違えない。
再起動後は既存observerで同じcontrollerを読取り確認し、観測エラーだけを理由にcontrollerやjobを再起動しない。

台帳128件の上限に達した場合などに直近の処理を確認するため、原observerを保持する別名の小metadata監視も用意した。

```powershell
& "$env:LOCALAPPDATA/Programs/Python/Python311/python.exe" -B output/finite_tail_resume_controller_v1/observe_window.py --launch-name parallel-flow-v13-launch --per-role 4
```

この補助スクリプトは各固定roleの直近4台帳だけを読み、process identity・config pin・error/completedの確認を維持する。
現flow1回の試行で候補23件から10件を観測し、原observer不変とPBS照会の完備を確認した。
128件超・4096 entry超過・missing・timeout等の分岐は実試験しておらず、詳細とsource/観測pinは[運用メモ](../../output/finite_tail_resume_controller_v1/OBSERVE_WINDOW_ja.md)に保存した。
window外は未観測、照会失敗や履歴消失は不明であり、job終了やcontroller停止と解釈しない。
capacity/mainの実科学jobはこの一覧で網羅しないため、journalの `independent-execution/state-latest.json` に記録されたjob IDと実qstatを併用する。
この補助の追加で稼働中controller・driver・source・config・policyは変更せず、ローカルPCへの実行依存も追加していない。

SSH応答の一時的なJSON解析エラーを記録する場合は、任意の別名診断コマンドを使える。

```powershell
& "$env:LOCALAPPDATA/Programs/Python/Python311/python.exe" -B output/finite_tail_resume_controller_v1/observe_window_diagnostic.py --launch-name parallel-flow-v13-launch --per-role 4
```

元observerとremote CODEを固定したまま受信byte長・hashを記録し、失敗応答だけを合計4 MiB以内でローカル原本保存する。
2026-10-26のread-only観測1回で成功経路、process identity一致、元3source不変を確認したが、失敗原本保存・timeout・上限超過は未試験である。
観測失敗をjob停止や再投入の根拠とせず、詳細とsource/受信/観測pinは[診断版運用メモ](../../output/finite_tail_resume_controller_v1/OBSERVE_WINDOW_DIAGNOSTIC_ja.md)を参照する。

## 2026-10-25 10:39 JSTのcensus本体確認先

投入前検証265702はF/0・run_count=1・14分44秒で終了し、全件census本体265703がR・run_count=1となった。
本体jobは内側censusのsubmission台帳に記録され、既存observerの有限action一覧に直接は出ないため、`qstat -xf -F json 265703` を併せて照会する。
台帳とscriptは `$HOME/workspace/mcmc4qec/20261025-census-operational-bundle-v13/runs/all12-parallel-independent-timing-seed-census-v13/` の `submission.json`・`submission-intent.json`・`census.sh` である。
submissionのSHA-256は `ed32834f1397e9920cfa59cfe32430dbb35056fa8afae52b6739d1ab2ca91942`、intentは `d6904e380b3a61c7843c80a81d70dc562cbab4505760455d538612edcc43429a` で、private原本bytesを指す。
10:39の観測ではR・walltime26秒で、`execution-intent.json`・`completion.json`・`failure.json` は未作成だった。
初期入力検証を含むjobの開始と、全件照合の完了は区別する。
controller確認は既存observerを使い、同じPID・job IDを照会して、観測失敗だけを理由に再起動・再投入しない。
全件census・独立計時・最終reportは未完了で、ローカル接続を維持する必要はない。

## 2026-10-25 10:24 JSTの次工程

v13の初回準備265700はF/0・run_count=1・walltime10分15秒で、controllerの準備roleもreturncode=0となった。
次の有限action265702はR・run_count=1であり、全件census本体を投入する前の再検証を行っている。
controllerのPID1598334・start ticks770092111の一致と生存、errorなしを保持し、再起動・再投入しない。
確認方法とconfig/source pinsは下の10:13節を使い、observerが列挙する最新action台帳とfresh qstatを照合する。
本番manifestのstatus=readyや予備1,000件のcollision=0を、全件4,208,002件の検証完了と扱わない。
[v13復旧差分の保存](finite_flow_v13_delta_snapshot_acceptance_2026-10-25_ja.md)は265701で完了したが、その265700観測は10:19:22 JSTのR状態までであり、後続の科学完了証拠は未収録である。

## 2026-10-25 10:13 JSTの現行v13確認先

本番後処理を再開し、別SSHでPID1598334・start ticks770092111・command一致、生存とerrorなし、初回qsub265700のR・run_count=1を確認した。
旧v12は停止したまま保持し、元12worker・merge・acceptanceを再実行していない。
現行controllerとqsub処理はSSHから切り離されており、ローカルPCを再起動してもクラスタ側で継続できる。
再開後は `output/finite_tail_resume_controller_v1/observe_actual.py` で現process・journal・有限actionのsubmissionとfresh qstatを読取り照合する。
このobserverは計算や再投入を行わず、時刻付きの小観測原本を同ディレクトリに保存する。
観測timeoutや一時的なqstat失敗だけで停止と判断せず、同じPID・job IDを再照会する。
`start_actual.py --execute` は既に実施済みで、繰り返さない。
全件census・独立計時・最終reportの完了は未確認であり、初回R観測を完了とは扱わない。

以下のパスの基準はクラスタ `$HOME/workspace/mcmc4qec`、hashはprivate原本bytesである。

| 現行原本 | パス・値 |
|---|---|
| controller設定 | `20261025-low-parallel-controller-v13/flow-config.json`、SHA-256 `e68ac4d738c21c6d79ddf71a22f0dd8aa35456c4325507fccf48ca2cf547c0fa` |
| controller source | `20261024-c3t2-index-relocation-v1/pipeline-submissions/operational-census-resume-fixtures-v2/sources/controller.py`、SHA-256 `4776f3a588c244edb627e227d11e9c276618ab965f9da221b50f4024e5f102a7` |
| 起動記録 | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v13-launch/started.json`、SHA-256 `4998f2edb0fa2de629a13c2c8ad431616ec0c3b5ccc368aa340fead7adb74d9e` |
| journal | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v13` |
| login readiness | `20261024-c3t2-index-relocation-v1/pipeline-submissions/finite-tail-resume-login-readiness-v1/results/accepted.json`、SHA-256 `0ada6ff87b7b715244df8b64640e13c8427edb4be8ab79bb0861e7edf83dc039` |
| 初回action台帳 | `20261025-finite-tail-actions-v13/low_timing_partition_census_wait_v1/00001-prepare-role/pbs/submission.json`、job265700、SHA-256 `63eea59e9208709e30f2f271f7ae5fec9c9266b2fddce57352c490d9731e3075` |

初回のprocess・qstat同時観測はlocal `output/finite_tail_resume_controller_v1/observation-1792890801372002200.json`、SHA-256 `63d1e8765fa6500adca6719191236a39d766b632792bd1b8f3ebfb193cf8d86b` に保存した。
以下の未再開記述は当時の履歴である。

## 復旧fixture成功後の確認先

資源設定28項目の265685と準備処理23項目の265686はF/0・run_count=1である。
本番は未再開で、新実環境の組立・実接続受入と、空きノードへの本番投入先移行を準備している。
旧controller・失敗rootは再利用せず、元12workerと比較結果も再投入しない。
最新の試験原本はlocal `output/operational_census_acceptance_v1/`、進捗は[状態文書](PROJECT_STATUS_2026-10-24_ja.md)と[運用受入記録](census_operational_pbs_staging_2026-10-25_ja.md)を参照する。
新controllerの読取り確認用に `output/finite_tail_resume_controller_v1/observe_actual.py` を用意し、初回は起動先未作成を確認した。
`start_actual.py` は実接続nativeの成功原本と実qstat終端を要求する起動用処理であり、現時点では実行していない。

## 2026-10-25の測定終了後の再開準備

測定265678はF/0・run_count=1・walltime5分56秒で終了し、実測候補16 GiB・45分と旧判定のmemory超過を保存した。
計測receiptの `production_authorized=false` は変更せず、全件census未実施として扱う。
本番には親子processと追加metadata検証の余裕を持たせる1 CPU・96 GiB・4時間の別運用policyを準備中で、旧v12は再起動しない。
tail専用再開処理は独立25 fixtureが成功したが、最終環境・policyとの実接続受入と本番起動はまだ行っていない。
現時点の一次資料は[状態文書](PROJECT_STATUS_2026-10-24_ja.md)と[計測原本の投入・受入記録](census_measurement_submission_2026-10-25_ja.md)であり、以下のR観測は当時の記録である。

## 2026-10-25 09:37 JSTの測定専用ジョブ

本番v12を再起動せず、受入21件が成功した計測専用helperをqsub265678で起動し、R・run_count=1を確認した。
計測stageは `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/census-resource-measurement-actual-v1` で、実request・資源・source pinsは[投入記録](census_measurement_submission_2026-10-25_ja.md)にある。
再開時はまずクラスタ上の `qstat -xf -F json 265678` と小さい計測receiptを照合し、不明な照会や長い実行だけを理由に再投入しない。
測定成功と本番資源承認は別であり、実測が揃うまで本censusの新規投入や旧v12の再起動を行わない。
元の比較結果・handoff・失敗rootは保持し、以下の09:29の本番停止状態は引き続き有効である。

## 2026-10-25 09:29 JSTの停止状態と再開時の確認

有限tail265675はF/1・run_count=1・walltime13分32秒・CPU時間13分24秒・PBS記録mem15,084,044KBで終了し、v12 controllerのPID1432966は不在である。
内側censusの1,000件pilotはcollision=0で終わったが、資源計測値の保存前に `measured census exceeds two-hour / four-GiB ceiling` で拒否された。
時間・メモリの個別超過と実predictionは未確定で、先行bundle検証を含むpeak selfRSSの影響を調査しており、PBS記録memとの同一視はしない。
小証跡はlocal `output/low_parallel_flow_v11/census-failure-readonly.json` にあり、censusの `planning-failure.json` は `root_reusable:false`、catalog・manifest・prepare受理記録は未作成である。
科学bundle1,757,600,835 bytesとconfig、元12worker・merge265660・acceptance265661・比較受理・handoffの原本を保持する。
09:29:23 JSTの独立観測はlocal `output/census_tail_incident_v1/inspection.json`、SHA-256 `1aa10c7641b4dde288aaa84e44e5a1eea5a77206f029b45a9ae3de84d12075e0` に保存し、PID不在と元comparison・handoffのhash不変を確認した。
v12 journalの `error.json` 原本SHA-256は `173828cfb14e48aac2e2a52aa3208266f886c129595c3168be692b91e50b21e7` で、09:28:01 JST終了・`automatic_retry:false` を記録する。
これらのhashは識別子を含むprivate原本bytesを指し、追跡文書への原本文面の転記は行わない。
再起動後は最新のPBS終端・v12 error・census失敗記録を読取り照合し、旧controllerや同じcensus rootをそのまま再実行しない。
既存SSH設定からの終端照会は `qstat -xf -F json 265675 265676` とし、旧12worker・merge・acceptanceを再投入せず、journalやlockも削除しない。
資源計測保存と新計画を準備中であり、自動再試行・独立計時・最終報告は未完了、全体ETAは未定である。
ローカルPCを維持しても停止処理は進まず、再起動してもクラスタの原本と停止記録は保持される。
[v12復旧差分保存](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)265676のF/0・10 fixture・source参照94件・metadata109件のprivate保存は、この準備失敗とは別に完了済みである。
以下の09:15の起動pin・読取り経路は停止したv12の照合用に保持し、生存を前提とする再起動手順とは扱わない。

## 2026-10-25 09:15 JSTの現行v12確認先

跨host stat照合の限定observer・tail修正を受入後、v12 controllerをクラスタ内でSSH接続から切り離して起動した。
09:14:10 JSTの別SSH観測でPID1432966・start ticks769736422・全command一致、生存・errors空、元12terminalの採用を確認した。
元12worker・merge265660・acceptance265661は再実行せず、旧v11のerrorと元completion・hash・sourceを保持する。
ローカルPCやSSH接続を維持する必要はなく、再起動後は起動を繰り返さず現行observerの読取り確認から再開する。

以下のパスはクラスタworkspace `$HOME/workspace/mcmc4qec` からの相対パスであり、SHA-256はprivate原本bytesを指す。

| 現行記録 | パス・固定値 |
|---|---|
| flow config | `20261025-low-parallel-controller-v12/flow-config.json`、`083a22ca37fe46eb31f2f1034554f76aeffa77e77c273e33627e14e67318838e` |
| flow source | `20261024-c3t2-index-relocation-v1/output/low_parallel_flow_v11/flow.py`、`c08c21a859fccaaef227ed603f9aaf76a5403d0f7892e1a528dbaedaf27d088b` |
| journal / launch | `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v12` / 同階層 `parallel-flow-v12-launch` |
| launch started / process SHA | `aab0c28c442b3ae702264d9bba57ad3850a123ab6dfb19154dac0ae73517d932` / `74f1fddf3fb257a36d0ac8444ac5fcf5872dc5b1048ffac4d61a8a04fca2d6b9` |
| native265673 accepted SHA | `3a6a0b7ffc96d544d21fb035c6b17c81229459c7d1ec6ee453ed870c3240fbdd` |
| tail config | `20261025-finite-tail-cross-host-v2/config.json`、`873a2c5cbde9693e7007b17a5b40ceac028ceb9533f78b428446489e133a6d3b` |
| observer authority | `20261025-merge-acceptance-observer-v1/observer-authority.json`、`dd83c9b81d4aef3059ee2789b15bebf5b9673f13274f934d928a8bd48414a786` |
| observer ready SHA | `e498798f93748a0a9e07b04c520b04daba4b8c1b78f84b4e91e5f59cfdad5d21` |
| tail ready SHA | `9db38edad846a9f1321a4a4f102d7b402662856716611e7505f26e9eb56c54b6` |

source配置名v11と実controller設定・journal v12を区別する。
確認はPython 3.11で `output/low_parallel_flow_v11/observe_actual.py` を実行する読取り経路を使い、`identity.live`、PID・start ticks・全command、errors、journalの進行を照合する。
localの `output/low_parallel_flow_v11/actual-observation.json` と `start-actual-executed.stdout` が小さい観測・起動証拠である。
その後の小証跡本文でcomparisonの `all_twelve_processed=true`、元merge265660・acceptance265661、handoffの `partition_started=true`・`flow_completed=true`・`cluster_controller=true` を確認した。
comparisonのSHA-256は `53470c42aa0bc554c0401ccfadebd93866edf55eadd5a3b3eebd623d1b597db2`、継承したv9名のhandoffは `83bc44cf948494283a07b517a65e55f3a0b75e69929ae1d4ff39f7d583ce754b` で、内容は新v12 configへ対応する。
local `output/low_parallel_flow_v11/first-tail.json` の09:15:07 JST観測で、初回の有限tail265675はR・walltime48秒・CPU時間46秒だった。
jobは `20261025-finite-tail-actions-v9/low_timing_partition_census_wait_v1/00001-prepare-role/pbs/` のqsub記録に対応し、census準備の完了や独立計時・最終reportの完了とは扱わない。
再開時は同jobの最新PBS状態と現行journalを照合し、準備jobを独立計時の実施済み結果へ読み替えない。
handoffとtailの未使用出力先は明示migrationの下で継承し、元merge-parallel-v2とacceptanceの完了原本は変更しない。
`start_actual.py`、旧controller、`run.py --role final-report` を手動実行せず、journalやlockを削除しない。
native265673・tail265674とlogin roundtripの限定範囲は[独立レビュー](cross_host_artifact_stat_review_2026-10-25_ja.md)にあり、後段の実科学処理の完走とは区別する。
goalと最終報告は未完了、全体ETAは未定で、以下の旧停止・旧PIDの確認手順は履歴として保持する。

## 2026-10-25 08:49 JSTの停止状態と確認先

本番merge265660はF/0・run_count=1・walltime1時間58分44秒・CPU時間3時間19分30秒、acceptance265661はF/0・run_count=1・walltime2分37秒・CPU時間2分31秒である。
acceptance completionの `original_accept_terminal_executed=true` とPBS内のselection生成を確認したが、controllerの統合受理・handoffは終わっていない。
v11 controllerは `acceptance.observe` の `check_artifact_stat` で `Previously PBS-verified artifact stat changed` を検出して停止し、PID1145733は不在である。
error原本はクラスタworkspace相対 `20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v11/error.json` にあり、`finished_unix=1792885604.099464`・`automatic_retry=false` を保持する。
独立した小metadata検査では4artifact全てでdeviceだけがPBS側46・controller側2049と異なり、inode・size・mtime_ns・ctime_ns・modeは一致、canonicalな通常file・非symlinkだった。
共有filesystemのhost-localな `st_dev` を比較したことが停止原因で、artifact内容の再読込み・再hashによる確認とは区別する。
検査原本はlocal `output/acceptance_stat_incident_v1/inspection.json` にあり、元proofを保持するobserver移行は準備中で、本番再開は未確認である。

再起動後はこの停止記録と[最新状態](PROJECT_STATUS_2026-10-24_ja.md)から再開し、旧controllerの生存を前提とする下記observerの失敗をworker失敗や再投入の根拠にしない。
既存SSH設定からクラスタへ接続した後の読取り照会は `qstat -xf -F json 265660 265661 265662` で行い、元12worker・merge・acceptanceを再投入しない。
`start_actual.py`、旧controller、tailの `--role final-report` は手動実行せず、journalやlockを削除しない。
現時点で常駐処理が自動継続しているとは扱わず、ローカルPCの再起動でも停止状態とクラスタ原本は保持される。

保存265662はF/0・run_count=1・walltime2秒で8fixtureと[v11差分採取](finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md)に成功し、07:13時点の「未投入」は履歴となった。
private source参照474件・metadata109件を保存したが、merge科学result・後続科学proof・可変journalの保存は対象外である。
独立計時・最終報告・goalは未完了で、全体ETAは未定とする。
以下の旧稼働・起動コマンドの記録は当時の履歴であり、停止済みv11をそのまま再起動する手順ではない。

## 2026-10-25 07:13 JSTの確認と追加の保存待ち

本番集約265660のR・run_count=1と、以下のv11 controllerの生存・起動識別情報一致・errorなしを確認した。
この時点では集約後の受理・独立計時・最終報告へ到達していない。
追加のv11制御差分保存は[準備記録](finite_flow_v11_delta_snapshot_preparation_2026-10-25_ja.md)に再開先を保存し、まだqsubしていない。
保存用ready.jsonは`$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v11-control-delta-v1/ready.json`、SHA-256は`c5fa82913f2a9b1dc4360761c5cafbbcbe0037749b4707539b050ed8378f827f`である。
集約の実終端と後続jobの資源使用を照合し、準備記録の固定stageから既存gate経由で投入する。
保存準備の完了をsnapshot取得済みとは扱わず、既存の本番controllerは再起動しない。

## 2026-10-25 06:45 JSTの現行v11確認先

後段worker受理のalias修正と新mergeへの接続を受入後、v11 controllerを起動した。
現在のPIDは1145733、start ticksは768839164、journalは`pipeline-state/parallel-flow-v11`、launchは`pipeline-state/parallel-flow-v11-launch`である。
configは`$HOME/workspace/mcmc4qec/20261025-low-parallel-controller-v11/flow-config.json`、SHA-256は`63b8b4d149fdbb56c043fb053e75bfabc73b0b38ea16b88b7dbbd820734d0f4b`である。
controller sourceは`output/low_parallel_flow_v10/flow.py`であり、sourceとjournalの番号を区別する。
読取り確認はPython 3.11で`output/low_parallel_flow_v10/observe_actual.py`を実行し、本番集約は`ssh cluster 'qstat -xf -F json 265660'`で確認する。
rootと独立担当の別SSHで起動識別情報一致・errorなし・12terminal採用を確認した。
集約265660はR・8CPU・32GiBで、06:45のwalltimeは26秒、CPU時間は47秒だった。
新mergeは`20261025-low-parallel-front-v6/merge-parallel-v2`、requestは`merge-parallel-request-v3`を使い、旧265651の記録は保持する。
新tail設定は`20261025-finite-tail-merge-relocation-v1/config.json`で、SHA-256は`970850291825f1af351b81a29f652e7c5deba027edeb6dfea32674cf483d90e8`である。
未使用のtail出力先とhandoff予定先は明示authorityの下で継承し、旧controllerの失敗記録は上書きしない。
以下の旧v9・v10停止や起動の記録は履歴であり、旧controllerを再実行しない。

## 2026-10-25 06:30 JSTの再停止

集約265651は起動後6秒でF/1となり、v10 controllerも停止した。
PID1082214は不在であり、以下の06:29時点の生存確認は履歴である。
エラーは元workerの深い受理経路にある`selector closure differs from environment`で、記録は`20261025-low-parallel-front-v6/merge-parallel-v1/`と`pipeline-state/parallel-flow-v10/error.json`へ保持する。
旧controllerや同じ集約出力先を再実行せず、[状態文書](PROJECT_STATUS_2026-10-24_ja.md)の最新の復旧状況から再開する。
12件の元workerは正常終了した結果を保持し、再投入しない。

## 2026-10-25 06:29 JSTの再開後の確認先

修正・引継ぎ受入後に新v10 controllerを起動し、全12件の既存終端を採用した。
現在のPIDは1082214、start ticksは768745045、journalは`pipeline-state/parallel-flow-v10`、launchは`pipeline-state/parallel-flow-v10-launch`である。
configは`$HOME/workspace/mcmc4qec/20261025-low-parallel-controller-v10/flow-config.json`で、SHA-256は`1263c2ed2264a19c69b0a29c692cf9277fb402d1d94f578364b73b94ab1046da`である。
controller sourceは`output/low_parallel_flow_v9/flow.py`であり、sourceの番号とjournalの番号を混同しない。
本番集約ジョブ265651はqsubで投入され、R・8CPU・32GiBを確認した。
ローカルの読取り専用確認はPython 3.11で`output/low_parallel_flow_v9/observe_actual.py`を実行し、集約は`ssh cluster 'qstat -xf -F json 265651'`で確認する。
このobserverはrootと独立担当の別SSHで実行し、PID・起動識別情報一致を確認済みである。
旧v9のerrorと部分requestは保持し、workerを再投入せず、新requestは`20261025-low-parallel-front-v6/merge-parallel-request-v2`へ生成した。
未使用だった元v9予定のfuture handoffとtail出力先は明示migrationで継承し、既存の失敗記録を上書きしない。
以下の旧停止・起動記録は履歴であり、旧observerや旧controllerをそのまま再実行しない。

## 2026-10-25 06:16 JSTの停止状態

全12workerはF/0で終端を回収したが、v9 controllerは集約準備で`Parent scientific selector closure differs`を検出して終了した。
PID898820は不在で、集約のprepared・submitted記録は未作成である。
以下の04時18分時点の起動記録は履歴として保持し、旧v9をそのまま再起動しない。
既存の生存必須の読取り確認は`/proc/898820/stat`不在で失敗するため、その失敗をworkerの失敗や再投入の根拠にしない。
エラー原本は`pipeline-state/parallel-flow-v9/error.json`に保持し、復旧内容と新しい確認対象は[状態文書](PROJECT_STATUS_2026-10-24_ja.md)の最新節で確認する。
完了済みworkerの計算結果を保持し、明示された別名パスと実体パスの対応を厳密に検証する復旧を準備中である。

## 復旧履歴

index0のジョブ265564は10月25日02時01分52秒JSTに要求壁時間1時間5分を超えて終了コード-29となり、旧v5 controllerはerrorを記録して停止した。
旧journalと他11件を保持し、index0だけを4時間予算の新ジョブ265605へ置き換えた。
front-v6の実preparedと全12件のnative preflightはPBS265602・265603で成功し、serial合流用のshadow constructorも265604で成功した。
serial controllerは起動せず、並列hash合流と更新したtail検証を使うfresh v8設定へ切り替えた。
並列hash flowの63テストは265607、8 CPUのmerge統合fixtureは265608、実配置CLIとnative bootstrapは265609で成功した。
本番全入力によるmergeと更新tailの本番実行は未実施である。
旧v5 journal、未起動のserial設定、未使用v7 tail設定は履歴として保存し、再起動しない。
旧v5のPID449524とstart ticks766989397は停止したprocessの履歴であり、現行の確認対象ではない。
旧v8は02時49分JSTに起動し、初回は5件F/0・7件処理中だった。
04時18分17秒JSTに旧v8のPID657240・start ticks767430511・command一致、sleep待機・子processなし・残る3workerがR・merge未作成を確認してSIGTERMで停止し、process不在を確認した。
最初の停止試行はpidfd APIがないため無変更で終了し、次の確認後の停止記録とともに保持した。
worker・旧journalは変更せず、受入済みの有限PBS action構成へ切り替えた。

|旧v8の固定記録（履歴のみ）|workspace相対パスまたはSHA-256|
|---|---|
|config|`20261025-low-parallel-controller-v8/flow-config.json`、`6130af78e5924a299e044195e584b7419affedeecdda393f7842de1bb19c0e43`|
|journal / launch|`20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v8` / 同階層の`parallel-flow-v8-launch`|
|launch started / process|`c46677b90d3415d4e996a5604e356ebff3013ed2ac09c66837117b03c2fac4f4` / `d53c83951741545861ccccd5acacc203a715b2f43c9d8f5f7caea825a1c33cdb`|
|native受入|`20261024-c3t2-index-relocation-v1/pipeline-submissions/parallel-flow-native-v8/accepted.json`、`a7afb7a65c38428d87efe6eb8e69e02951217a3cbc38c87588bc3ee3cebdd08a`|
|tail config|`20261025-low-parallel-tail-config-v8/tail-config.json`、`e91b41145b18198161bf8f877af176b9512f943ec9ac52d56dcfc08cf553bb5f`|
|main evidence配置対応|`20261025-low-parallel-controller-v8/main-evidence-binding.json`、`312ef838495349f2238b340f502de6ccb1f350b6eaf6fde3182c8e9f99c0ebf0`|

旧v8を再起動せず、旧tailの `--role final-report` を手動実行しない。

## 現在の状態と再起動の扱い

2026年10月25日04時18分JSTに、比較worker全12件の実投入記録と最新PBS状態を照合し、新v9 controllerをクラスタ内でSSH接続から切り離して起動した。
04時18分38秒JSTの別SSH接続で新PID898820・start ticks767964369・commandの一致と生存、旧controller不在を確認した。
ローカルPCやそのSSH接続を維持する必要はない。
再起動後は起動を繰り返さず、以下の読取り確認から再開する。
indices 0〜8の9件はF/exit 0として元preparedに結合したterminalを新journalへ採用し、indices 9・10・11の3件は実行中だった。
error記録は空、最終completedは未作成であり、後段の実科学payloadはまだ実行していない。
9件についてもworker結果の深い受理検証は後続のPBS処理で行うため、全12条件の正式比較完了とは扱わない。
小さい切替証跡はlocal `output/low_parallel_flow_v8/` の `cutover-stop-v2.stdout`・`start-actual-executed.stdout`・`post-start-observation.json` にあり、原本の切替journalは `pipeline-state/parallel-flow-v9-cutover/` に保存している。

## 固定された実行記録

クラスタのworkspaceを`$HOME/workspace/mcmc4qec`、controller配置先をその下の`20261024-c3t2-index-relocation-v1`とする。
ここに記載した`$HOME`はクラスタ側で展開し、Windows側の同名変数で置き換えない。
接続先は既存のSSH設定にある`<cluster-alias>`を使用する。
実配置の2物理ノードはdispatch policyの`allowed_vnodes`で確認し、ここでは論理名A・Bと呼ぶ。
上限は2物理ノード×96 CPUであり、2ジョブではない。

|項目|値またはworkspace相対パス|
|---|---|
|controller PID|898820|
|Linux process start ticks|767964369|
|実config|`20261025-low-parallel-controller-v9/flow-config.json`|
|config SHA-256|`5b44a838edcf35f9d02d119c323530ef17bab880aeb8c29e74ff3fe81c4748ed`|
|実flow source|`20261024-c3t2-index-relocation-v1/output/low_parallel_flow_v8/flow.py`|
|flow source SHA-256|`58ada8dedaf393d01f501a9615ee7e920146c6596989b20c1b0f67b47a21e138`|
|controller journal|`20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v9`|
|launch journal|`20261024-c3t2-index-relocation-v1/pipeline-state/parallel-flow-v9-launch`|
|launch started.json SHA-256|`ff09c182ad53930668b8cd2a1d2a157b3ec459795702ced6b3ee9cc8386189ef`|
|launch process.json SHA-256|`2f670a0d080b822ad7c7c81210e29af0b0fbf9a36a0b9aa4cfdfcab2144ebb5c`|
|worker準備記録|`20261025-low-parallel-front-v6/prepared-receipt.json`|
|worker準備記録 SHA-256|`22eedcbfb42b9ef6ce3d286b539630491efeb80fd0317287fb31fc6ca8c3e058`|
|dispatch policy|`20261025-low-parallel-dispatch-policy-v6/policy.json`|
|policy SHA-256|`fc459112f26fc1aaa3def3712b2ba406211118350e233040248afe92a7d34d09`|
|native constructor受入|`20261024-c3t2-index-relocation-v1/pipeline-submissions/parallel-flow-native-v9/accepted.json`|
|native受入 SHA-256|`1c95d2ed0ab6095cf2ef903f0fb18865a408f2e1b74387758791c83d2d0ad96d`|
|新index0投入ledger|`20261025-low-parallel-front-v6/workers/0/submission.json`|
|新index0投入ledger SHA-256|`d8a3ce2346c87d142cc595911ade65f55c5654f6c17c407667430979580e4cac`|
|finite outer config|`20261025-finite-tail-outer-v9/config.json`|
|outer config SHA-256|`f4dc8a4b9ff57cbe2c1f6e8867fd2d31b4b1b6c09be57a812c353681a7cbf114`|
|outer entrypoint|`20261024-c3t2-index-relocation-v1/output/finite_tail_outer_v1/run.py`|
|outer entrypoint SHA-256|`18db7c4201e9a44241abda91b480f8188ed011116f51168cb428580f24b32aa9`|
|effective tail config|`20261025-low-parallel-tail-config-v9/tail-config.json`|
|effective tail config SHA-256|`eed3366d1be6737a2ab283d2bd5db3370c10c3c8c164f8010dc48734e466119c`|
|finite action job root|`20261025-finite-tail-actions-v9`|
|tail journal|`20261024-c3t2-index-relocation-v1/pipeline-state/parallel-tail-v9`|
|merge root|`20261025-low-parallel-front-v6/merge-parallel-v1`|
|merge終端受理job root|`20261025-low-merge-terminal-acceptance-v1`|
|finite outer基準policy|`20261025-low-parallel-dispatch-policy-v4/policy.json`、`ac2333a854caae961e620fd76a9e286b0840e11330df9088158c17ad58b895a9`|
|finite action資源|1 CPU・96 GiB・walltime上限4時間。完了時刻の予測ではない。|

directory名の `low_parallel_flow_v8` はsourceの配置名であり、実controller config・journalのv9と区別する。
flowが呼ぶtailはfinite outerであり、そのeffective configが元の科学処理とreport環境を結ぶ。
outerとeffectiveの `journal_root`・`handoff_path`・`merge_root` が一致することを、下記の小さい固定config読取りで照合する。

実worker番号は次表のとおりで、PBSの完全なIDとpreparedの対応は各投入ledgerを一次資料とする。
保持11件のpreparedと投入ledgerは実際のfront-v4/v5に残し、新manifestで書き換えていない。

|index|実ジョブ番号|preparedの所在|04時18分38秒時点|
|---:|---:|---|---|
|0|265605|front-v6/workers/0|F/0・terminal採用済み|
|1|265566|front-v4/workers/1|F/0・terminal回収済み|
|2|265586|front-v5/workers/2|F/0・terminal回収済み|
|3|265587|front-v5/workers/3|F/0・terminal採用済み|
|4|265588|front-v5/workers/4|F/0・terminal採用済み|
|5|265589|front-v5/workers/5|F/0・terminal採用済み|
|6|265571|front-v4/workers/6|F/0・terminal回収済み|
|7|265572|front-v4/workers/7|F/0・terminal回収済み|
|8|265573|front-v4/workers/8|F/0・terminal回収済み|
|9|265590|front-v5/workers/9|R|
|10|265591|front-v5/workers/10|R|
|11|265592|front-v5/workers/11|R|

表のfront-v4/v5/v6はworkspace直下の`20261025-low-parallel-front-v4`、`20261025-low-parallel-front-v5`、`20261025-low-parallel-front-v6`を指す。
旧失敗ジョブと旧controller設定は履歴として保存し、再起動の対象にしない。

## 読取り確認手順

Windows側で次を実行してクラスタのシェルへ入る。

```text
ssh <cluster-alias>
```

以下は接続後のクラスタ側Linuxシェルで実行する。
小さいJSON、process情報、PBS状態の読取りだけを行い、sampling、raw全件読込み、解析、計時は実行しない。
科学計算や重いテストを追加する場合は、実ジョブ状態と資源ゲートを確認し、必ず`qsub`を通す。

```bash
TASK_PY="$HOME/workspace/mcmc4qec/20261018-tile-low-timing-stage2-v1/venv/bin/python"
"$TASK_PY" -B - <<'PY'
import hashlib, json, subprocess
from pathlib import Path

work = Path.home() / 'workspace/mcmc4qec'
root = work / '20261024-c3t2-index-relocation-v1'
launch = root / 'pipeline-state/parallel-flow-v9-launch'
journal = root / 'pipeline-state/parallel-flow-v9'
limit = 4 * 1024 * 1024
def raw(path):
    with Path(path).open('rb') as stream:
        value = stream.read(limit + 1)
    assert len(value) <= limit, 'small-file limit exceeded'
    return value
def read(path):
    return json.loads(raw(path))
def check(path, digest):
    assert hashlib.sha256(raw(path)).hexdigest() == digest, Path(path).name
def pinned(descriptor):
    check(descriptor['path'], descriptor['sha256'])
    return read(descriptor['path'])

check(launch / 'started.json', 'ff09c182ad53930668b8cd2a1d2a157b3ec459795702ced6b3ee9cc8386189ef')
check(launch / 'process.json', '2f670a0d080b822ad7c7c81210e29af0b0fbf9a36a0b9aa4cfdfcab2144ebb5c')
started = read(launch / 'started.json')
assert started['pid'] == 898820 and str(started['start_ticks']) == '767964369'
assert started['config']['sha256'] == '5b44a838edcf35f9d02d119c323530ef17bab880aeb8c29e74ff3fe81c4748ed'
config = pinned(started['config'])
check(Path(started['controller']['path']), started['controller']['sha256'])
outer = pinned(config['tail']['config'])
check(config['tail']['runner']['path'], config['tail']['runner']['sha256'])
effective = pinned(outer['effective_config'])
for name in ('journal_root', 'handoff_path', 'merge_root'):
    assert outer[name] == effective[name], name
assert outer['handoff_path'] == str(journal / 'tail-handoff/completed.json')
assert outer['journal_root'] == str(root / 'pipeline-state/parallel-tail-v9')
assert outer['job_root'] == str(work / '20261025-finite-tail-actions-v9')
assert config['journal'] == str(journal)
assert outer['merge_root'] == config['merge_root']
print('v9 flow / finite tail placement pins match')
proc = Path('/proc') / str(started['pid'])
try:
    stat = (proc / 'stat').read_text().split(') ', 1)[1].split()
    command = [v.decode() for v in (proc / 'cmdline').read_bytes().split(b'\0')[:-1]]
    print('controller', dict(pid=started['pid'], live=stat[0] != 'Z',
        start_matches=stat[19] == str(started['start_ticks']),
        command_matches=command == started['command']))
except FileNotFoundError:
    print('controller process absent: inspect completed/error; do not restart')
for p in (journal / 'error.json', launch / 'error.json', launch / 'stderr.log'):
    if p.exists() and p.stat().st_size:
        print('ERROR', p.name, 'bytes', p.stat().st_size)
print('finished terminal journals', sorted(p.name for p in journal.glob('worker-*-finished.json')))
print('final completion exists', (journal / 'completed.json').exists())
jobs = ['265605', '265566', '265586', '265587', '265588', '265589',
        '265571', '265572', '265573', '265590', '265591', '265592']
response = subprocess.run(['qstat', '-xf', '-F', 'json', *jobs],
    capture_output=True, text=True, timeout=30)
if response.returncode:
    print('PBS observation unknown:', response.returncode, response.stderr)
else:
    rows = json.loads(response.stdout)['Jobs']
    assert {key.split('.')[0] for key in rows} == set(jobs)
    for key, row in rows.items():
        print(key.split('.')[0], row['job_state'], row.get('Exit_status'),
              row.get('run_count'), row.get('resources_used', {}).get('walltime'))
PY
```

正常な常駐状態では`live`、`start_matches`、`command_matches`がすべてtrueとなる。
PIDだけの一致は再利用の可能性があるため、生存確認として不十分である。
30秒timeout、PBS照会失敗、JSON不正、履歴消失は不明状態であり、未投入や失敗と推定して再投入しない。
controllerは不明な観測で再投入せず、次の照会を待つ。
errorがある場合は実行中workerを保持し、config・ledger・PBS実状態を照合してから修復方針を決める。
`start_actual.py`やworker投入コマンドを再実行せず、既存journalやlockを削除しない。

## 完了の判定

全12件のF/0だけでは最終完了ではない。
controllerは全12terminalをそろえ、mergeの結果受理、選択結果のseal、独立計時、報告生成・回収を順に進める。
最終確認ではcontroller journalの`completed.json`、tailのreport完了記録、`report.json`と`report_ja.md`のhash照合まで必要となる。
controllerが終了していても`completed.json`がなければ、正常完了とは判定しない。
controller journalの`completed.json`ができた後、次の小証跡の読取り確認をクラスタ側で行える。
旧tailや新finite outerの `run.py --role final-report` を手動起動しない。
新finite outerの同roleもPBS actionを投入し得るため、単なる状態照会コマンドではない。

```bash
TASK_PY="$HOME/workspace/mcmc4qec/20261018-tile-low-timing-stage2-v1/venv/bin/python"
"$TASK_PY" -B - <<'PY'
import hashlib, json
from pathlib import Path
root = Path.home() / 'workspace/mcmc4qec/20261024-c3t2-index-relocation-v1'
flow = root / 'pipeline-state/parallel-flow-v9'
tail = root / 'pipeline-state/parallel-tail-v9'
def small(path):
    with Path(path).open('rb') as stream:
        value = stream.read(4 * 1024 * 1024 + 1)
    assert len(value) <= 4 * 1024 * 1024, 'small-file limit exceeded'
    return value
def pinned(pin):
    value = small(pin['path'])
    assert hashlib.sha256(value).hexdigest() == pin['sha256']
    return json.loads(value)
if not (flow / 'completed.json').exists():
    print('Not complete; do not start a second controller or final-report action')
else:
    done = json.loads(small(flow / 'completed.json'))
    assert done['all_stages_completed'] is True
    comparison = pinned(done['comparison'])
    assert comparison['all_twelve_processed'] is True
    receipt = json.loads(small(tail / 'finite-final-report.json'))
    completion = pinned(receipt['completion'])
    assert completion['result']['value'] == done['final_report']
    print('Small completion pins agree; review the bound PBS and report evidence')
PY
```

この確認は小さいcompleted・comparison・有限action completionのpinと内容の対応だけを読み、大きいreportやrawを再hashしない。
元source・環境・実PBS終端・報告完了フラグ・回収済みJSONと日本語Markdownのhash検証は、結合された有限PBS actionの証拠で確認する。
小証跡の一致だけで全工程を再検証済みとはせず、controllerの全工程完了記録と実PBS・報告証拠を照合してから完了を報告する。
数値結果の整合性は独立referenceがない領域の精度保証や名目95%被覆の保証にはならない。

## 実施済み確認と未実施範囲

並列hash対応flowの63テストはPBS265607、更新tailのnative受入はPBS265614、実preparedを用いたshadow constructorはPBS265615で成功した。
shadow constructorはtick・投入・科学計算を行っていない。
実controllerの起動とSSH切断後の生存・初回巡回は確認済みである。
その後の265642は実outer設定組立、265643は全6role各2経路とfinal-reportの13constructor、265644は実flow constructorでF/0を確認した。
これらのconstructorは本番の科学payloadを実行せず、切替後の9terminal採用と実controller生存も全12条件の科学的受理とは区別する。
本書作成時点ではmerge、独立計時、最終報告の本番完了は未確認であり、本書の最終報告確認コマンドもまだ実行していない。
切替後に本書の最初の読取り確認コマンドをそのままクラスタで実行し、flow・outer・effective設定のpinと配置一致、controller生存・起動識別子一致、9件F/0・3件R・全run_count=1を確認した。
確認対象コードのhashと終了コード0、標準出力・標準エラーはlocal `output/low_parallel_flow_v8/documented-readonly-check.*` に保存し、この実行ではジョブ投入・科学payload読込・ローカル計算を行っていない。
