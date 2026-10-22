# 公開候補の状態確認とRelease本文の訂正

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
