# 公開候補の状態確認とRelease本文の訂正

その後、公開状態の誤記と追加文書への識別子再導入を修正する[隔離したレビュー用snapshot](publication_review_snapshot_2026-10-23_ja.md)を用意した。
これは未コミットで既存tagとは異なる候補であり、以下のtag対応済み成果物と区別する。

2026年10月23日06:27〜06:29 JSTにGitHubの状態と準備済み配布物を照合した。
リポジトリはPRIVATEで、GitHub Releaseは0件である。
remote mainは `55cd5998f48d670d8636c630d397ed2b56b86a1a`、tag `v0.1.0.dev5` の参照先は引き続き `e7e5239f977fa6162e58570726100e3fcd717afa` である。
mainはtagから文書159ファイルを更新した1commitだけ先行し、package sourceの変更はなかった。
mainの [tests run39778387464](https://github.com/junichiharuna/mcmc4qec/actions/runs/39778387464) はsuccessだった。

10月22日に用意したRelease本文には「2026-10-22にGitHubで公開済み」と書かれていたが、実際の公開状態と一致しなかった。
旧成果物を保持し、未公開の候補であること、対応するtagとcommitを明記した新しい本文を作成した。
識別子の置換についても「公開前」ではなく「この候補snapshot内」と表現を修正した。
固定済みsource ZIPとwheelは再buildせず、同じbytesを新しい成果物directoryへ複製した。
tagに固定した7本の文書リンクがsource ZIP内のファイルを参照することを確認した。
相対リンクが残っていないことと、checksum manifestを再照合した。
packageが変わらないため、今回package suiteは再実行していない。
元のsource snapshotに含まれる過去のRelease本文は履歴として保持し、今回の訂正は添付用本文に適用した。

新しい添付候補は `output/publication_candidate_20261023_v1/artifacts/` にある。

| 成果物 | SHA256 |
|---|---|
| wheel | `801ebeb2bd84a00f0d43b05588c2ec2b2c4309041c971086b1287018a7fd3e6a` |
| source ZIP | `55acbb8c2042ba726f07fc2b3136d3a565093fe9531484e8bb598bcb10aeb3b2` |
| 訂正したRelease本文 | `e195f0ed1d9f24df657a94c816c2da671559b239829380fc42df59c304173779` |

[検証記録](data_tile_validation_2026-10-17/publication_candidate_20261023_v1/prepared.json) のSHA256は `888586fca9ac9ceb0ffa1796d525bd70237d9ab4e95d1dde5561bbb70ead3905` である。
同directoryに再現scriptとremote照会結果を保存した。
commit・push・public化・Release作成・PyPI公開は行っていない。
全raw datasetの公開用変換と公開先の確定は未完了であり、短い利用例を科学的精度の保証とは扱わない。

## 数値計算の確認

06:26 JSTのqstatでjob265462のsamplingがR、96 CPU・1要求node、経過4時間22分59秒だった。
p=0.003のDGX batch18は実PIDの終了とcompletionを確認し、serial driver PID45416は回収段階で実稼働していた。
これは全33バッチの19番目であり、全解析の完了ではない。
laboは最後のbatch4のPID6732が実稼働し、completionはまだなかった。
全12条件の入力inventoryは10/12のままで、残る2条件と独立計時・最終報告は未完了である。

## 09:08 JST頃のremote更新確認

[remote再照会と配布物照合](data_tile_validation_2026-10-17/publication_remote_observation_20261023_v2/observation.json) を保存した。
remote mainは `98222e1daf80e4387a5fd588729052baee923515` に進んでおり、前回確認したmainから1commit・31ファイルの差分があった。
差分は報告script1ファイルと文書30ファイルで、src配下のpackage変更はなかった。
報告scriptのremoteバイト列は現worktreeと一致した。
[CI run39866529525](https://github.com/junichiharuna/mcmc4qec/actions/runs/39866529525) は12job全てsuccessである。
tagの参照先は変わらず、準備したwheel・source ZIP・Release本文の3件ともSHA256SUMSと一致した。
Release本文は主4条件の完了と低ノイズ校正・計時の未完了を区別し、全raw datasetが同梱されないことと新decoderの科学的校正が未完了であることを明示していた。
今回の確認に伴う配布物の再buildや本文変更は不要だった。
リポジトリは引き続きPRIVATE・Release0件であり、この再照会でも公開操作・commit・pushは行っていない。
最初の比較API読取りはUTF-8をcp932として読むローカルdecodeで失敗したため、bytesとして読み直して成功した。

## 14:46 JSTの再確認

[再照会記録](data_tile_validation_2026-10-17/publication_remote_observation_20261023_v3/observation.json)で、remote main・tag objectが09:08の観測から変わらず、mainの最新tests run39866529525もcompleted・successであることを確認した。
リポジトリはPRIVATE、Releaseは0件のままである。
package配下のgit statusは空で、配布候補3ファイルの実際のSHA256とサイズは既存manifestと一致した。
package変更がないため、buildやpackage suiteの再実行は行っていない。
午後に追加した稼働観測や利用上の日本語メモは現worktreeの記録であり、固定済みsource ZIPへ追加したものではない。
公開操作・commit・pushは行っていない。

## 16:32 JSTの公開状態と残る所有者判断

GitHub APIの再照会でもリポジトリはPRIVATE、Release一覧は空、最新tests run39866529525はhead `98222e1daf80e4387a5fd588729052baee923515` でcompleted・successだった。
この再照会では配布物の再buildや再hashはしていない。
[公開手順書](publication_runbook_2026-10-22_ja.md)はpublic化を所有者の指示時だけ行い、別日の公開では公開日を含む文書・引用情報の更新とtag更新を行うよう定めている。
また、ZenodoのGitHub連携を所有者側でONにしてからReleaseを作成する順序を指定している。
このセッションでは公開日・tagの更新、Zenodo連携の確認、public化、Release作成を実施していない。
したがって「公開候補の成果物が準備済み」と「公開直前の全手順が完了済み」は同一ではない。
現行AGENTS.mdにある2026-10-22のpublic化済みという記述は、このAPI観測と一致せず、実際の公開状態の根拠にしない。
既存の配布候補と稼働中の科学計算入力は保持し、公開操作のために計算中のsourceを上書きしない。
