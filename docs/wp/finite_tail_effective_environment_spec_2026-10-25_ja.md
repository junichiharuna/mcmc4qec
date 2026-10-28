# 有限tailのreport IPC環境を実CLIで受理するPBS worker

## 固定境界

既存v3 base configを `effective.validate_base` で元adapterの全検査へ通し、変更しない。
元parent environment、basis、parallel mergeのbridge・runnerと受理証跡を維持する。
固定IPC overlay sourceからreportの運用差分だけを導出し、新規workspace直下directoryの `cluster_scripts/tile_low_noise_timing_evaluation_report.py` と `report-environment.json` を作成する。
report environmentの変更は `source_sha256`・`resolved_sources`・`import_origins`・`import_prepend` の4項目だけとし、元sourceとenvironmentへ上書きしない。
固定report entrypointのSHA-256は `8fc3f81a53e9d18771c0c484a6173823d0075dd7a9548d4d7c18b03b57e9ddc2` とする。
固定IPC sourceのSHA-256は `b570297a9e7cd290f6c6f929f684a4623ea9626b1098e4a10e0fc39d4e062d3c` とする。

## Request

requestはschema 1、purpose `finite_tail_effective_environment_request` とする。
必須項目は `worker`・`effective_source`・`ipc_source`・`base_config`・`report_entrypoint`・`pure_acceptance`・`pure_terminal` の完全なpath/SHA-256 pin、および `output_root`・`ipc_timeout_seconds`・`native_timeout_seconds` とする。
baseのparent/basis/report pinは検証済みbaseから取得し、requestで別指定できない。
timeoutはboolを除く1〜14100秒の整数に固定し、4時間PBSの初期予算内で選ぶ。
予算の十分性や実行性能は計測前に保証しない。
pure受入は別PBS suiteの成功receiptとF・exit0・run_count1のterminal pin、および現在のqstatの同条件を必要とする。
pure receiptはpurpose `finite_tail_effective_pure_acceptance`、`success=true`、整数 `tests_failed=0`、正整数 `tests_passed`、`pbs_job_id`、絶対pathをkey・SHA-256をvalueとする `sources` mapを持つ。
pure suiteのsource mapには実worker、effective、IPCのpinが含まれなければならず、map中の全sourceを再検査する。

## Native受入

Linux・非optimized Python・PBS_JOBIDを必須とする。
新environmentのPythonを `-B -i <実report_job.py> --help` で起動し、stdinからprobeを与える。
実script directory、argv、Python、PYTHONPATH、entrypoint source、bootstrapの定義元を検査する。
元entrypointの `bootstrap(new_environment)` と実wrapperの `science(new_environment)` を実行し、全import originを比較する。
wrapper自身のreport＋parent再帰的local import closure検査を使い、reportのsource mapだけとの独立比較で代用しない。
`partition_check`、merge reader、report.inputs、計算、prepare、submitは実行しない。
stdout/stderrを新規rootに保存し、成功markerがちょうど1個で完全一致した場合だけ受理する。
失敗時には成功receiptを作らず、保存済みログとfailure.jsonを保持する。

## 出力とterminalの責任

acceptance purposeは `finite_tail_effective_environment_acceptance` とし、`base_config`・`parent_environment`・`basis`・`report_environment`・`report_source`・`ipc_source`・`ipc_timeout_seconds`・`acceptance_pbs_job_id` を記録する。
成功時は `approved_delta_verified`・`native_bootstrap_verified` をtrue、`scientific_configuration_changed` をfalseとする。
prepared-receiptにも新config構築に必要な同じpinとenvironment acceptance pinを保存する。
worker実行中の受理はPBS terminal成功を意味せず、呼出し側が終了後のF・exit0・run_count1を新configへ別途固定する。
ローカルcode/test/science実行、qsub、remote変更は本workerの作成時点では未実施である。
