# 復旧collectorから元環境trace監査への明示接続

## 対象

C1T0の旧collector265356の時間切れを保存したまま、別collectorの正常終端後にcapacity監査・全trace監査へ接続する。
元sampling、復旧collector、既存の監査計算、checkpointと分母の規則を変更しない。
既に投入待ちの復旧controlはhash固定のまま保持し、新しい監査controlは別directoryに置く。

## 復旧完了のauthority

旧context・復旧config・control sourceを外部hashで固定し、旧失敗jobの実qstatと保存済み14ファイルを元guardで再確認する。
新collectorの実qstatがF・exit 0・run_count 1であることと、復旧workerの開始・終了・summary・新ledger・保存terminalの一致を必須にする。
後段のread-only検査ではcompleteを再実行せず、正常completeで作成されたterminalを読む。
新collectorの復旧bindingがconfig・contextと同じであることも検査する。
authorityには旧新job、復旧config、復旧worker証跡、保存terminal、guardと新監査controlのhashを含める。
authority変更は同じ監査の継続ではなく停止条件とする。

## 監査と資源の接続

既存の分離audit backendを別namespaceで合成し、planに明示的な復旧authorityを加える。
prepare・read_plan・実行submission検査・terminal検査でauthorityと元sampling rootを再確認する。
実際のtrace読取・checkpoint再復号・並列group処理は元関数を使う。
capacity資源計算・全監査のworker選択も元関数のbytecodeと別globalsを使い、復旧backendを明示的に渡す。
元moduleのglobalsを書き換えない。

## qsubと実行入口

元qsub関数の変更はworker invocationとledgerへの復旧authority追加に限定する。
元の共有lock、待機中を含む最大2ノード、全upstream jobの終端確認、直前の再検査、曖昧応答時のintentとlock保持を維持する。
workerは外部hashで固定した新configを検査し、元venvのPythonからのみ科学監査を起動する。
既存監査rootへ再実行せず、capacity・fullはそれぞれ新しいrootを使う。
本番のcapacity plan作成・qsubは復旧collectorの正常complete後に限り、現時点の投入待ちを成功扱いしない。

## 受入

合成metadataで復旧authorityの混入・run_count・旧guard変更・worker/ledgerの不一致を拒否する。
backend合成では元計算bytecodeと元moduleの不変、capacity/fullの分母保持、通常readerによる拒否を確認する。
qsubはfixtureに置き換え、最大2ノード・二重投入・曖昧応答・source変更の停止を検査する。
実trace監査の完了はこれらのfixture受入から推論しない。

## 受入結果と配置

Windowsのauthority/backendは15 passed・8.08秒、qsub制御は16 passed・22.26秒、bootstrapは7 passed・0.72秒、追加terminal受入は7 passed・0.53秒だった。
最初の試験では固定hashの転記とWindows fixtureのshell引用に2件の失敗があり、転記・fixtureを修正して該当試験を通した。
科学計算、元source、旧復旧controlは変更していない。
Linuxの統合受入は45 passed・12.07秒であり、fixtureでは実qsub・実監査を呼んでいない。
[実配置記録](data_tile_validation_2026-10-17/recovery_trace_execution_native_v1/accepted.json) は、新controlのhash、元復旧config、実旧jobの終了状態と保存成果物のguardを確認した。
これはbootstrapの実入力確認であり、新collectorの正常完了authorityはまだ未取得である。
新controlは `/home/user/workspace/mcmc4qec/20261020-recovery-trace-execution-v1/output/recovery_trace_audit_v1` に配置した。
config SHA-256は `c1fded776101ec8ff167d0652ceb431cc730d218655ef7222a4a49152d0ac898` である。
capacity rootは元bundleの `runs/partitioned-trace-capacity-1-0-retry-v1`、full rootは `runs/partitioned-trace-full-1-0-retry-v1` に固定し、どちらもまだ作成していない。
本番plan・preflight・qsub・監査・completeは未実施である。
新旧control・元監査source・受入ログ・native配置記録・snapshot v4は [44ファイルのmanifest](data_tile_validation_2026-10-17/recovery_trace_execution_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `c44b41aa5a26b400ba20f16367ae95d2c14e5cd51d686f37c746cabbc1a7d4b8` であり、実科学監査の完了を表す記録ではない。

## 使用条件付きの実行手順

以下を一括実行せず、各段階の実job・出力・source hashを記録してから次へ進む。
復旧collectorの投入は既存のlocal PID3092の監視が担当しており、手動で重複投入しない。
実復旧jobがF・exit 0・run_count 1となった後、そのqstat JSONを保存し、元の `recovery_worker.py complete` を元config SHAで一度だけ実行して正常terminalを受理する。
旧265356の失敗を正常終端へ書き換えない。
復旧completeの後、元venv入口と新controlを次のように指定する。

```bash
task_python=/home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v11/venv/bin/python
audit_control=/home/user/workspace/mcmc4qec/20261020-recovery-trace-execution-v1/output/recovery_trace_audit_v1
audit_pin=c1fded776101ec8ff167d0652ceb431cc730d218655ef7222a4a49152d0ac898
"$task_python" -B "$audit_control/worker.py" plan --phase capacity --config "$audit_control/config.json" --config-sha256 "$audit_pin"
"$task_python" -B "$audit_control/worker.py" preflight --phase capacity --config "$audit_control/config.json" --config-sha256 "$audit_pin"
```

新authorityの実検査が成功し、C0T2最終reportの既存投入監視が投入済みとなり、実qstatで要求ノード数が2未満であることを確認してから次を一度だけ実行する。
workerのsubmitは元と同じ共有lockの下でqsubを使い、2ノード制約を直前に再検査する。

```bash
"$task_python" -B "$audit_control/worker.py" submit --phase capacity --config "$audit_control/config.json" --config-sha256 "$audit_pin"
```

capacityの実F・exit 0・run_count 1を確認後に `complete --phase capacity`、続いて `plan --phase full` と `preflight --phase full` を各一度だけ実行する。
fullのresourceは実capacityの検証済み測定から選び、容量不足や時間超過を固定値で無理に回避しない。
fullも空き枠を確認して `submit --phase full` でqsubし、正常終了後に `complete --phase full` でterminalを受理する。
completeが残したterminalや失敗記録がある場合は重複実行せず、実状態を調べる。
最終BAR reportへの復旧backend選択と独立readerの接続は、これらの監査入口とは別に未完了である。
