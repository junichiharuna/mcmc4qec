# experimental候補のremote CI完了

公開候補の最新commitは`47ef1b6ad957a93dae3bbd6cf1d79fab86457e96`である。
[対象commitのGitHub Actions](https://github.com/junichiharuna/mcmc4qec/actions/runs/39267489093)は全12 jobが成功した。
これはソフトウェアの検証結果であり、未完了の混合・bias・被覆の校正を保証しない。

最初のcommit `0d509c5`ではoptional testが5分の制限に達し、run `39266127357`は失敗した。
Python 3.11の失敗stepのlogにtimeoutが明記され、途中までのテストにfailureは表示されていなかったが、全件成功とは扱わなかった。
制限を延ばしたりテストを省いたりせず、optionalの全test moduleを名前順に4分割した。
各Python版の全2313 nodeについて、分割前後の収集集合が欠落・重複なく一致することをローカルで検証した。
remoteから全8 shardのinventoryとJUnitを回収し、各版で全146ファイル、全2313 caseを実行し、caseの重複とfailure・errorがないことも確認した。
この修正は`.github/workflows/tests.yml`だけであり、package、数値計算コード、科学データ、既定設定を変更していない。

| 検証 | Python 3.11 | Python 3.12 |
| --- | --- | --- |
| installed core | 696 passed / 252 skipped | 696 passed / 252 skipped |
| installed optional全shard合計 | 2306 passed / 7 skipped | 2306 passed / 7 skipped |
| core test所要時間 | 34.02秒 | 39.34秒 |
| optional shard所要時間の範囲 | 65.79–110.30秒 | 56.71–139.55秒 |

文書のstrict buildとリンク確認、32 sourceのstrict型検査と型テスト3件も成功した。
各Python版で全quick examples・notebookのverify stepも成功した。
各test stepは5分以内に完了した。
optionalは分割jobの所要時間であり、その合計を1 jobのwall timeや科学計算の速度と解釈しない。
失敗した初回CIの記録と、成功した全jobのlog・metadata・JUnit・照合結果を`data_experimental_release_2026-10-19/`に保存した。
成功記録の入口は`remote_ci_success_v2/verification.json`である。

## 更新した配布物

最新treeは`7e37df175f902cc8ac14f0a80e324415e9437ff6`である。
Git blobと対応する全915ファイルを照合したexportは`output/experimental_release_20261019/git_export_v5/`である。
manifestは`data_experimental_release_2026-10-19/git_export_v5.json`に保存した。
旧候補との差はCI workflowの1ファイルだけである。
配布用source ZIPの全916 memberを照合し、source ZIPのSHA256は`4989821b8e0c4b1b85febd23f656d91956d2b817f237124b263faab3d5e432f4`となった。
wheelのSHA256は`e8d38a6fba00d8c9c4eaaf0cb7f160575c2bb745c46bf003dc549aa76d60e45a`、環境差検証ZIPは`75f09fcab4b58f62e590107ff970fc66ac8cd14dc1caa5226d8194530bbe7872`であり、検証済み配布物から変更していない。
最新の配布物3件と単一の`SHA256SUMS`を`output/experimental_release_20261019/assets_with_platform_v2/`へ配置した。
CI成功commitを指す日英release本文は`output/experimental_release_20261019/release_body_final_v2.md`に生成した。
source ZIP・wheel・追加検証ZIPの作成は、GitHubへのuploadやrelease公開を意味しない。
tag、release、visibilityの変更は未実施である。

再現用のCI修正・照合・配布物更新スクリプトは`data_experimental_release_2026-10-19/ci_revision_sources_v1/`に保存する。
