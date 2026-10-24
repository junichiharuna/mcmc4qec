# experimental版のGitHub公開結果

所有者の指示により、2026年10月24日09:38:58 JSTに[0.1.0.dev5 experimental Release](https://github.com/junichiharuna/mcmc4qec/releases/tag/v0.1.0.dev5)を公開した。
[リポジトリ](https://github.com/junichiharuna/mcmc4qec)はpublicで、Releaseはdraftではなくprereleaseである。
09:39:40 JSTに認証なしのGitHub APIで公開状態・main・tag・Releaseを確認した。
PyPIへの公開は行っていない。

## 公開対象と履歴

mainとtag `v0.1.0.dev5`の対象commitは`c27ca896a1025c74975bc45322798eea2e0409b0`である。
annotated tagのobjectは`601f70c1f0b8cb65cb69b9310914be8ce57a71f8`である。
所有者の承認に従い、直近2コミットへ再導入された既知の識別子を置換し、公開状態と日付を修正した。
変更前のmainとtagを明示した`--force-with-lease`とatomic pushで反映した。
パッケージ本体・テスト・pyproject.toml・LICENSE・Release変換scriptは変更前のmainと一致する。
過去の証跡に記載されたSHA256は非公開で保持する原本を指し、識別子を置換した公開コピーのSHA256とは区別する。
既知の識別子の照合を、あらゆる秘密情報が存在しない証明とは扱わない。

稼働中の数値計算を維持するため、反映は隔離したリポジトリで行った。
計算用作業ツリーのHEADと固定済み入力は旧履歴のままであり、未コミット差分も保持している。
この作業ツリーから旧履歴をmergeまたはpushしない。
後続の通常開発へ戻る際は、未コミット差分と計算入力を保全したうえで公開済み履歴へ同期する。

## 配布物と確認

Releaseにはsource ZIP・wheel・SHA256SUMS・manifest・Release本文の5ファイルを添付した。
source ZIPは対象commitの全1,170ファイルと一致し、wheelのパッケージ33ファイル・README metadata・LICENSEもsourceと一致する。
GitHubのasset digestを全5ファイルで照合し、wheelと他の小さい添付ファイルは認証なしでdownloadしてSHA256を再確認した。
source ZIPの公開download自体は再実行せず、GitHub側のdigestとサイズを照合した。

| 配布物 | SHA256 |
|---|---|
| source ZIP | `ea6b535789f584d138391f209bc8d17ae97d0d84929e1e93e0fd170f53407487` |
| wheel | `98a70792c8e9a51a131c0ff6117180d7b28eccd7f00ef5f144566f6ca7c093ed` |

新規core環境へのwheel installとverify_wheel coreは成功し、verifyは8.877秒だった。
Release本文と文書manifestの検査は8 passed、0.67秒だった。
公開対象commitの[main CI](https://github.com/junichiharuna/mcmc4qec/actions/runs/40045588733)と[tag CI](https://github.com/junichiharuna/mcmc4qec/actions/runs/40045588818)はいずれもsuccessであり、mainの全12jobの成功を確認した。
[公開照合記録](data_tile_validation_2026-10-17/publication_20261024_v1/published.json)と[配布物検証記録](data_tile_validation_2026-10-17/publication_20261024_v1/verified.json)を保存した。
照合scriptは同じdirectoryの`verify_public.py`に保存し、元の実行directoryは`output/publish_experimental_20261024/`である。

## 継続事項

所有者からZenodoのGitHub連携済みとの回答を受けてReleaseを作成した。
Zenodoの記録作成・DOI・metadataの一致はまだ確認しておらず、CITATION.cffへDOIは追記していない。
2026-10-24 11:20:32 JSTに認証なしのZenodo records APIへ`q=mcmc4qec&size=10`を問い合わせ、HTTP 200・検索結果0件を確認した。
応答原本は`output/publish_experimental_20261024/zenodo-check-20261024-112033.json`に保存した。
公開検索での未検出だけから、連携設定・webhook・処理失敗・pre-releaseの扱いを原因として断定しない。
個別Releaseの処理状態を調べる際は、[Zenodoの公式手順](https://help.zenodo.org/docs/github/archive-software/github-upload/)に従いGitHub連携画面の対象ReleaseとErrorsを確認する。
DOI生成を促す目的で公開済みtag・Release・prerelease属性を変更する操作は行っていない。
11:48 JSTにはGitHub APIのリポジトリwebhook一覧が0件だったことを確認し、`output/publish_experimental_20261024/zenodo-hook-check-20261024-114812.json`へ記録した。
この一覧だけではZenodo側の連携・処理状態は確定せず、ブラウザ接続もTransport closedで利用できなかったため、所有者へZenodo設定画面の対象Releaseの状態またはErrorsの文面を問い合わせた。
その回答待ちはクラスタ計算の継続を妨げない。
低ノイズ校正・独立計時・日本語最終報告は継続する。
最後のtile288 depolarizing・p=0.001はPC解析・回収を完了したが、索引作成と後続集約は公開時点で未完了である。
公開は混合・精度・名目95%被覆や計算速度の一般保証を意味しない。
