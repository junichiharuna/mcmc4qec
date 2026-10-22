# 公開履歴更新後のsource ZIPとwheelの再作成

remote mainとtag `v0.1.0.dev5` が指す `e7e5239f977fa6162e58570726100e3fcd717afa` を別checkoutへ取得し、計算用の旧作業ツリーを変更せず配布物を作成した。
source ZIPの全984ファイルをGit blobと照合し、その展開物からwheelをbuildした。
wheel内のパッケージ33ファイル、README metadata、MIT licenseが展開sourceと一致することを確認した。
検証後もsource全ファイルの内容とcloneのclean状態を確認した。

初回の `git archive` はWindowsの改行変換により328ファイルがGit blobと不一致となり、そのarchiveと途中状態をv1として保持した。
v2ではコマンド単位で `core.autocrlf=false` と `core.eol=lf` を指定し、global設定を変えずに一致を確認した。
wheelの初回metadata確認も、BytesParserがUTF-8本文をASCIIとして扱うため失敗した。
UTF-8としてdecodeした本文をParserで読む確認へ直し、build済みの同じwheelがREADMEと一致することを確認した。
この修正によるpackage sourceやwheelの再buildは行っていない。

新しいcore環境へのwheel installは成功し、`verify_wheel.py core` は8.287秒で成功した。
同検証はinstalled packageの読み込み、sourceとの内容一致、core quick例、READMEとtutorialのcoreコード例を含む。
Release本文変換のテストは2 passed・0.09秒だった。
optional suiteは今回再実行しておらず、同commitのremote CI成功と過去の科学的検証は別の証拠として扱う。
古いplatform supplementの再梱包や全raw datasetの公開用変換は未実施である。

成果物は `output/publication_candidate_20261022_v2/artifacts/` に保存した。

| ファイル | サイズ | SHA256 |
| --- | ---: | --- |
| `mcmc4qec-0.1.0.dev5-source-20261022.zip` | 33,207,302 bytes | `55acbb8c2042ba726f07fc2b3136d3a565093fe9531484e8bb598bcb10aeb3b2` |
| `mcmc4qec-0.1.0.dev5-py3-none-any.whl` | 93,202 bytes | `801ebeb2bd84a00f0d43b05588c2ec2b2c4309041c971086b1287018a7fd3e6a` |
| `release_body.md` | 4,773 bytes | `7328ce20a0d03cd4505cb0b67f6ac78c3ee6d9aa36df92c1ea314ab22b230cba` |
| `SHA256SUMS.txt` | — | `cccf09789b0c3a1bce9671f5fb6fb78106fdec3d7f169777d26eca943de4b0b1` |

[作成・検証記録とスクリプト](data_tile_validation_2026-10-17/publication_candidate_20261022_v2/)を保存した。
prepared receiptのSHA256は `f7e6b1c525bc510b5b6d6048dfbd95f65f8d068e43a47fdced3b53f3b4e1de98` である。
21:35 JSTのGitHub実照会でリポジトリはPRIVATE、tag objectは `b5dec868994de3d8763523a2941c1df27d1143dd` のままだった。
本作業ではcommit・push・public化・Release作成・PyPI公開を行っていない。
低ノイズ検証の完了や名目95%被覆を追加認定したものではない。
