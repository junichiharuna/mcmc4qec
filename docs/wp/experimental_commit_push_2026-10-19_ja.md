# experimental公開候補のcommit・push

2026-10-19のユーザー依頼に従い、固定済みの公開候補をmainへcommit・pushした。
対象commitは`0d509c57dc871fb01bf8f14f1efaf7586fe8219b`で、remoteの`refs/heads/main`との一致を実照合した。
treeは`7ae747cc7fda60095d73d119dc0d0eb6648aea9d`で、検証済み915ファイルの候補と一致する。
先行するtile実装commit `d78377e0f965f6aacc8a5e5b610c9153ebff9c3b`もremoteに含まれる。

ステージ前にmanifestのworktree hashと固定exportのhashを全件照合した。
通常の`git add`では既存ファイルの改行属性変更が一部再評価されずtreeが一致しなかったため、選定済みpathspecだけを`git add --renormalize`で再評価した。
その後のtree一致を確認してからcommitした。
whitespace検査は保存済み実行ログの行末空白と7ファイルの末尾空行を報告した。
検証済み候補とhashに結び付いた生ログを維持し、この機会の整形は行っていない。
GitHubは70.77 MBの`mixing_comparison_four_case_v1/cohorts.json`について推奨サイズ超過のwarningを返したが、pushは成功した。

[対象commitのCI](https://github.com/junichiharuna/mcmc4qec/actions/runs/39266127357)は起動済みである。
23:08 JSTの観測ではdocumentationとtypingが成功し、core・optionalのPython 3.11／3.12は実行中だった。
この時点では全job成功とは扱わない。
別commitのCI成功を代用しない。
pushの照合記録は`data_experimental_release_2026-10-19/commit_push_receipt_v1.json`に保存した。

固定後に追加したPC間の比較資料とportable BARの継続計算記録は、この915ファイルのcommitには含めていない。
追加の環境差検証は別配布物として準備済みであり、詳細は[追加資料の記録](experimental_platform_supplement_2026-10-19_ja.md)にある。
tag作成、release作成、repositoryのvisibility変更は未実施である。
未完了の数値検証とその実行中processを、commit・pushによって完了扱いにしていない。
