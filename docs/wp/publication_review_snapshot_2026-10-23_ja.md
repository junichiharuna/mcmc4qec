# 公開状態の訂正と識別子置換を含むレビュー用snapshot

GitHubの実照会はPRIVATE・Release0件である一方、README・リリースノート等は2026-10-22に公開済みと記載していた。
また、既存tag後の追加文書に、置換済みだった利用者名・利用者パス・クラスタhost接頭辞が再導入されていた。
調査したクラスタ利用者名の一致は既存tagでは0ファイル、現行mainでは28ファイル、特定のWindows利用者パスはそれぞれ0・14ファイルだった。
これらは既知の識別子に限定した照合であり、あらゆる機密情報が存在しないという検査ではない。

## 隔離した変更と成果物

計算中の作業ツリーを保持し、main `98222e1daf80e4387a5fd588729052baee923515` から `output/publication_readiness_20261023_v2/checkout/` にdetached worktreeを作成した。
9文書で公開済みの断定を外し、公開日が未確定な間は日付を仮定しない文面とした。
`CITATION.cff` の未確認の公開日を外したが、所有者が確定した著者・ORCID・所属と版番号は保持し、DOIは追加していない。
公開手順書には、実際の公開日・対象commit・配布物の対応と、既存tag変更を所有者の指示に従うことを記した。

公開用コピーの44文書では既知の識別子を置換し、各ファイルの置換前後のSHA256と置換件数を `privacy_transform.json` に保存した。
原本の科学計算入力・稼働中driver・既存tag・Git履歴・remoteは変更していない。
過去の証跡内に残るhashは原本を指すものであり、置換後コピーのhashではないことを明記した。
Git差分には置換前の文字列を含むため、`review.patch` はローカルの確認用で、配布archiveに同梱していない。

成果物は `output/publication_readiness_20261023_v2/artifacts/` にある。

| 成果物 | SHA256 |
|---|---|
| レビュー用source ZIP | `baf29fd76dddde4012fb54a684128192e10d350e0f3c6b757abd820824435377` |
| wheel | `3cbea84af72471788fde7c0970fcf349f92c8636fc5709f0b5a2090a6b6c4d1e` |
| Release本文 | `ebf8aa28ee2333c834681fd1b93e3b2ad2de9d9f83fe76f421747c44f7a93ecf` |

このsnapshotは未コミットであり、既存 `v0.1.0.dev5` の内容と同一とは扱わない。
既存tagに対応する従来の配布候補も保持している。

## 実施した検証

source ZIPの全1,170ファイルを隔離checkoutのbytesと照合し、build・検証後も内容が変わっていないことを確認した。
パッケージ本体33ファイル、pyproject.toml、LICENSE、テストとRelease変換scriptは基準commitから変更していない。
wheel内の33ファイル、README metadata、LICENSEが新しいsourceと一致した。
新しいcore環境にwheelをinstallし、installed package・core quick例・READMEとtutorialのcoreコード例を含むverify_wheel coreが8.924秒で成功した。
Release本文変換の既存2 testは0.38秒で成功し、生成本文に相対リンクが残っていないことを確認した。
optional suiteと全数値検証は今回再実行していない。

初回buildはsystem Pythonにbuildモジュールがなく停止した。
そのログを保持し、既存のPython 3.11配布物作成環境でbuildだけを実行した後、新規core環境でinstallと検証を行った。
[source・実行ログ・成果物manifest](data_tile_validation_2026-10-17/publication_review_snapshot_20261023_v2/manifest.json)を保存した。

## 公開まで残ること

現行remoteの追加commitにも識別子が残るため、最新treeだけの置換で公開リポジトリの履歴まで修正したとは扱えない。
公開用コピーの統合、公開日、既存tagの更新、履歴の扱い、Zenodo連携と公開操作は未実施である。
force pushや履歴更新を行う場合は、所有者の判断と他の作業環境との調整を要する。
このレビュー用snapshotを、公開済み成果物や科学的校正の完了として報告しない。

このコピーをGitHubへ反映する際に直近2コミットの識別子も置換して履歴を更新するか、修正案だけ保存するか、別の作業環境で反映するかを所有者へ確認している。
この確認にはpublic化やRelease作成を含めておらず、未回答の間は履歴更新・commit・pushを実施しない。
独立した数値解析・回収・集約は回答を待たず継続する。
