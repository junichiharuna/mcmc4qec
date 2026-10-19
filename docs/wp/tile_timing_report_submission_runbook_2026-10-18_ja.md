# 主ノイズ正式計時報告の親用実行手順

本書は手順書であり、正式request・外部受理pinの作成、remote操作、qsub、正式集計は本書の保存では行っていない。
既存の[Linux配置とconfig契約](tile_timing_report_linux_handoff_2026-10-18_ja.md)と[投入仕様](tile_timing_report_submission_spec_2026-10-18_ja.md)を補足する。
対象は主4caseの全8精度条件・各192 replicateで、低noise独立計時を含めない。

## 1. 全4caseの証拠を揃えてprepareする

元MCとBAR全4caseについて、本計時のsummary・全artifact・独立回収proof・verification・transfer・正式PBS terminalが揃うまでprepareしない。
現在のcase0〜2の証拠索引は[中間報告の計時節](tile_validation_report_2026-10-18_ja.md#6-低noiseと計算効率)と[進捗文書](tile_validation_status_2026-10-17_ja.md)を参照し、case3の未取得値は本書では埋めない。
既存の[formal config template](data_tile_validation_2026-10-17/timing_report_formal_config_template_v2.json)を別ファイルへ複製し、全pinを独立受理済みhashと実remote pathから設定してから `template_only` を除く。
template自体、smoke plan、capacityのproof、未終了jobの値を正式入力にしない。
追加の証拠は新しい専用保存先へ配置し、既存bundleの受理済み入力を上書きしない。

以下の `CONFIG` と `REQUEST` は全証拠が揃った後に親が決める実pathであり、ここでは未設定である。
`REQUEST` は固定bundleの `runs/` 直下の新規directoryとし、元5cohortと重ならないことを確認する。

```bash
BASE=/home/user/workspace/mcmc4qec
PY="$BASE/20261017-tile-production-v1/venv/bin/python"
BUNDLE="$BASE/20261018-tile-timing-report-v2"
HELPER="$BASE/20261018-tile-timing-report-tools-v1/prepare_final_timing_report_v1.py"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
"$PY" "$HELPER" prepare --bundle "$BUNDLE" --config "$CONFIG" --root "$REQUEST"
```

prepareはmetadataの固定と再構築だけを行い、全payload走査・decoder実行・qsubは行わない。
出力は `preparation.json`、`ready.json`、`config.json`、`plan.json`、`execution_driver.py`、`report.sh` の6ファイルである。
資源は1 node・1 CPU・16 GiB・2時間で、実測による完了保証ではない。

## 2. 外部accepted readinessを固定する

親が6ファイルと準備記録を回収し、既存helper・source closure・Python/native・全入力pin・全4case完了状態との一致を確認してから、次のschemaのlocal JSONを別名で保存する。
現在読めたhashを根拠なしに受理済みとせず、独立回収時のproofと正式prepareの照合記録を受理根拠にする。
accepted JSON自身のSHA256も外部の受理記録に保存し、wrapperへpathとそのSHA256を渡す。
このJSONや追加のreadiness fileをrequest directory内に置くと6ファイルのfreshness検査に反するため、request外に保存する。

| field | 必須値・由来 |
|---|---|
| `schema`, `purpose` | `1`, `main_timing_report_submission` |
| `root` | 受理したremote requestの絶対POSIX path、固定bundleの `runs/` 配下 |
| `bundle` | `/home/user/workspace/mcmc4qec/20261018-tile-timing-report-v2` |
| `helper` | `/home/user/workspace/mcmc4qec/20261018-tile-timing-report-tools-v1/prepare_final_timing_report_v1.py` |
| `python` | `/home/user/workspace/mcmc4qec/20261017-tile-production-v1/venv/bin/python`、symlink解決後のsystem Pythonへ置き換えない |
| `resource` | `{"cpus":1,"memory_gb":16,"requested_nodes":1,"max_nodes":2,"walltime":"02:00:00","wall_seconds":7200}` |
| `formal_complete_candidates`, `qsub_executed` | `true`, `false` |
| `request_files` | 上記6 basenameだけをkeyとする、回収・照合済みbytesの小文字SHA256辞書 |
| `preparation` | 受理した `preparation.json` のJSON内容をそのまま保持する |
| `terminal_snapshot` | 元MC＋BAR4caseの実job IDをkeyとする、下記6fieldの辞書 |
| `controller` | 下記固定rootと、受理済みcontroller fileの絶対POSIX path→SHA256辞書 |

`preparation` の必須内容は `root`、`ready_sha256`、`manifest`、`resource`、`command=['qsub',REQUEST+'/report.sh']`、`script_sha256`、`qsub_executed=false`、`parent_must_write_submission_intent_and_receipt=true` である。
`ready_sha256` と `script_sha256` はそれぞれ `request_files` の `ready.json` と `report.sh` に一致させる。
`terminal_snapshot` の各jobは `job_state`、`Exit_status`、`Submit_arguments`、`Resource_List`、`exec_host`、`run_count` の6fieldを保存する。
`Resource_List` は受理した辞書全体を保持し、requested resourceだけを抜き出した新しい辞書へ置き換えない。
F・run_count=1を要求し、exit0と保存済みtask failureに整合するexit1の区別は既存adapterの契約に従う。
これらは元結果のsaved terminalおよび投入直前の新qstat snapshotと照合される。

`controller.root` は `/home/user/workspace/mcmc4qec/20261017-tile-coordinator-v1/runs/controller` である。
`controller.files` はそのroot配下の受理済みfileだけとし、`status.json` と `process.json` を必ず含める。
statusの固定SHA256は `e29ff982bd0ab71f0df991f3ceace8873b7e3509229f01a877252731f2c7e936` で、processの値は既存のcontroller完了証拠から照合し、本書で新しい値を推定しない。
wrapperはfinished判定、旧PIDの消滅、live controller不在も確認する。

## 3. dry-run、preflight、一回だけのexecute

Windows親側はlocalのacceptance pathを `Path`、その内容のremote pathを `PurePosixPath` として扱うv2受理sourceを使う。
旧source `072d2359…` はWindowsでremote rootを誤拒否するため、この手順の実投入には使わず履歴として保持する。
使用する最終source/test hashはv2受入記録に照合し、既存request helper `ccc8ff52…` と科学adapter `0b6c393f…` は変更しない。
以下の `$Accepted` と `$AcceptedSha` は第2段階で受理したlocal path/hashであり、ここでは未設定である。

```powershell
$Py = "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe"
& $Py output/submit_final_timing_report_once.py --acceptance $Accepted --acceptance-sha256 $AcceptedSha
& $Py output/submit_final_timing_report_once.py --acceptance $Accepted --acceptance-sha256 $AcceptedSha --preflight
```

既定はremote接続なしのdry-runで、preflightはremote metadata・元5job terminal・controller・schedulerの読取だけを行う。
slot_availableがfalseならqsubせず、最大2nodeの枠が空くまで親が状態を確認する。
正式executeは親が以下を一度だけ実行する。

```powershell
& $Py output/submit_final_timing_report_once.py --acceptance $Accepted --acceptance-sha256 $AcceptedSha --execute
```

共有lock内でsource/native/inputと元5job終端を照合し、intent保存直後にもcontroller・queuedを含むnode数・script・intent実体・lock所有を再確認して、固定 `qsub REQUEST/report.sh` を一度だけ呼ぶ。
localには `main_timing_report_{preflight,execute}_once_v1_*`、remoteには `submission_intent.json`、`submission.json`、`parent_submission_receipt.json` を排他保存する。
localの `once_v1` は固定証拠prefix名であり、v2 sourceの使用時も自動変更しない。
timeout・非zero・応答不正・通信断では受理状態不明として止まり、lock/intent/receiptを消さず、同じ実行の自動再試行や新prefixへの逃避をしない。
sourceやintentの変更、既存証拠による拒否も手動照合へ戻り、gateを緩めて通さない。

## 4. report jobの終端を回収する

親がreceiptの実job IDを指定して `qstat -x -f -F json JOB_ID` の正式終端を保存する。
そのF/exit、実script、1 node・1 CPU・16 GiB・2時間の実要求、execution-intentのPBS ID、親intent/ledgerのhash、completionとreportのhashを結合する。
回収対象は6準備ファイル、全投入証拠、`execution-intent.json`、`completion.json`、stdout/stderr、正式terminal、および `results/` 全体である。
成功時は `results/report.json` と `report_ja.md` の8行・各192分母・有限referenceの判定・欠損/失敗保持を確認し、全転送hashを保存する。
失敗時は `validation_failure.json`、failed completion、未生成artifactをそのまま記録し、正常終了や区間取得を精度達成へ読み替えない。
MCの4 within・2 above・2 reference_sensitive、選択時の診断flagと独立計時の診断未取得を保持し、両手法が固定精度gateを通らない条件の時間比をnullとする。
元計測・report処理・PBS経過時間を混同せず、このmain報告の完了で低noise独立計時を完了扱いしない。
