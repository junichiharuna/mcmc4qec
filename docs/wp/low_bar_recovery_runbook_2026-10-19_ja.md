# C0T0 BAR時間切れ時の復旧・最終比較・回収手順

この手順は、元BAR job 265324が実際にwalltimeで終了した場合に限る。
元jobが実行中の間はobserveだけを行い、停止・再投入しない。
元jobが正常終了した場合は[通常の最終比較手順](low_partition_final_runbook_2026-10-19_ja.md)と[trace SSH timeoutの受理経路](trace_timeout_completion_spec_2026-10-19_ja.md)を用いる。
現在の復旧report資源設計は、1 partitionで全768 group・192 seedを扱うC0T0に対応し、複数partitionへ流用しない。
実装と検証の詳細・各source hashは[復旧仕様と検証記録](low_bar_timeout_recovery_spec_2026-10-19_ja.md)を参照する。

## 実行前

作業directoryはA:\dev\mcmc4qecとし、Python 3.11を絶対パスで使う。
各コマンドは自動ループにせず、前段の受理receiptと実PBS状態を確認してから実行する。
クラスタ投入はqsubのみで、待機中を含む自分の要求node数の合計を最大2に制限する。
RIMC、元sampling、元BAR、reference、固定した公開候補は変更しない。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython output/control_low_bar_recovery_v1.py observe
```

## 元BARがwalltimeで終了した場合

実PBSのF・非zero終了・run_count 1、元script・資源とPBSのwalltime超過メッセージの一致をprepareが要求する。
一般のエラーやSSH timeoutだけでは復旧を開始しない。

```powershell
& $taskPython output/control_low_bar_recovery_v1.py prepare
& $taskPython output/control_low_bar_recovery_v1.py preflight
# 前段の受理と空き枠を確認してから一度だけ実行する。
& $taskPython output/control_low_bar_recovery_v1.py execute
```

復旧jobは別rootで既存の正常なgroupを再利用し、未完成groupだけを同じ計画とseedで計算する。
復旧の12時間は要求walltime上限であり、完了予定ではない。
実行中はobserveで同じjobを追跡する。
復旧jobの正常終了後にだけ、次の完了受理を行う。

```powershell
& $taskPython output/complete_low_bar_recovery_once.py
```

## 復旧結果とtrace・referenceの最終比較

復旧completionと、受理済みtrace job 265326のreconciled completionが必要である。
prepareが各入力と現在のnative環境・実PBSを照合し、観測RSSからmemoryを設定する。
初回reportは1 CPU・1 worker・1 node、walltime上限24時間であり、実測済みの所要時間ではない。

```powershell
& $taskPython output/control_low_bar_recovery_report_v1.py prepare
& $taskPython output/control_low_bar_recovery_report_v1.py preflight
# 前段の受理と空き枠を確認してから一度だけ実行する。
& $taskPython output/control_low_bar_recovery_report_v1.py execute
& $taskPython output/control_low_bar_recovery_report_v1.py observe
```

実report jobが正常終了した後、352設定・192 seed・67584行のscopeと実行記録を受理し、reportを回収する。

```powershell
& $taskPython output/complete_low_bar_recovery_report_once.py
& $taskPython output/collect_low_bar_recovery_report_once.py
```

回収先はdocs/wp/data_tile_validation_2026-10-17/low_bar_recovery_report_collection_v1/である。
artifacts/report.jsonにreport、同directoryに12個の実行metadata/log、親directoryに転送前後のsnapshot・intent・receiptを保存する。
accepted=Trueと全13ファイルのhash一致を確認してから、正式比較の集計と日本語報告へ反映する。
回収はreportと実行記録だけであり、全raw datasetの回収や数値再計算ではない。

## 失敗・通信切断時

既存のreceipt・途中のファイル・共有lockを削除して同じ操作を再実行しない。
SSH timeoutをjob終了とみなさず、同じjob IDとremoteのsubmission/guard/terminalを調べる。
qsub応答が不明な場合は、実際には投入済みの可能性があるため、成否が確定するまで再投入しない。
必要な照合・再回収は別の記録として設計し、元の失敗記録を保持する。

## 検証範囲

各helperの受入テスト、配置済みreport helperのLinux import・bash構文、読み取り専用observeは確認済みである。
この復旧経路での実計算・実report投入・実terminal受理・実回収は、手順書作成時点では未実施である。
失敗・未収束・診断未定義・区間未取得を分母から除かず、独立referenceのない範囲の整合性を精度や95%被覆の保証として扱わない。
