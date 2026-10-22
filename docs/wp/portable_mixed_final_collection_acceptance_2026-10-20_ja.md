# portable最終report回収の受入結果

[小仕様](portable_mixed_final_collection_spec_2026-10-20_ja.md)に従い、正常終端したC0T2最終reportの回収helperを追加した。
固定wrapperのsource、config、入力metadata、実qstat、terminal・completion・execution・reportの対応を検査し、転送前後のsnapshotとlocalの13ファイルを照合する。
helperはqsub、最終reader、decoder、Monte Carloを実行しない。
失敗時はintentと部分結果を残し、同じ出力先へ自動再試行しない。

受入テストを先に追加し、未実装によるimport失敗を確認してから実装した。
最初の実装ではWindows fixtureのパスとPOSIXの比較により9件が失敗し、remote POSIX pathをWindows側でも同じ表記で照合する処理とfixtureのshell引用を直した。
次の実行では破損reportの欠けたkeyがKeyErrorとなる1件が残り、明示したidentity検査のValueErrorとして拒否するようにした。
これらの失敗ログも保存した。

最終Windows検証は26 passed・22.67秒、クラスタLinux検証は26 passed・15.34秒だった。
正常回収、実行中・失敗・再実行job、script/resource不一致、異なるterminal/report/config、欠けたfile、転送破損、snapshot変化、既存出力保護を検査した。
SSH先でsourceを読み込む形態、誤ったremote root、reportの読込み前のサイズ制限、実行host不一致も検査した。
qstatとSCPはfixtureで置き換えており、本番の科学計算や最終report回収の成功ではない。

source・テスト・小仕様・各段階のログを [10ファイルの保存manifest](data_portable_bar_2026-10-19/final_collection_sources_v1/manifest.json) に保存した。
manifest SHA-256は `416c3388b752399a9a4295ee039590145351e5f1e9b1be598cb9b6da9ba3454e` である。
クラスタ検証先は `/home/user/workspace/mcmc4qec/20261020-portable-final-collection-v1`、配置archive SHA-256は `dc71a6121740361d95f5badb30a29df8393b53a1f3c42066093d4cfa46046b56` である。
[配置receipt](data_portable_bar_2026-10-19/final-collection-stage-receipt-v1.json) と [Linuxテストログ](data_portable_bar_2026-10-19/final-collection-linux-tests-v1.log) を保存した。
既存のmixed-controls配置と現在の計算sourceは変更していない。

再現時は保存manifestの相対pathへ復元し、外部依存として固定したmixed_execution_controls_sources_v1のmanifestも照合する。
テスト入口は `python -m pytest output/test_portable_mixed_final_collection_v1.py -q` である。
最終wrapperのcompleteが正常に終了してから、その実job root、固定config hash、実terminal.jsonのhashを指定する。
terminalのhashを推測したり、compute段階のcompletion.jsonをterminal.jsonの代わりに使ったりしない。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B output/portable_mixed_final_collection_v1.py --remote-root $finalJobRoot --config-sha256 $finalConfigPin --terminal-sha256 $finalTerminalPin --destination $newCollectionDirectory
```

成功時のreceiptはaccepted=trueとremote_snapshot_unchanged=true、report_sha256、全13ファイルのsizeとhashを含む。
最終reportのlocal pathは新規回収directory内のartifacts/final-report.jsonであり、このreceiptの実report_sha256を [要約入口](low_noise_report_summary_acceptance_2026-10-20_ja.md) に渡す。
本番の全群最終reportは未取得であり、今回のhelperによる本番回収も未実施である。
