# 公開本文と環境差の追加証拠

公開候補固定後のBP-OSD環境差を、[英語追記](../platform_validation_addendum_en.md)と[日本語追記](../platform_validation_addendum_ja.md)に整理した。
公開候補915ファイル、source ZIP、wheelは従来の固定hashと一致することを再確認した。
sourceを再構成せず、今回の16条件・1048576対の証拠を独立した追加ZIPとして準備した。

追加ZIPは`mcmc4qec-0.1.0.dev5-platform-validation-20261019.zip`、20450647 byte、1057 memberである。
SHA256は`75f09fcab4b58f62e590107ff970fc66ac8cd14dc1caa5226d8194530bbe7872`である。
日英説明、事前仕様、受入テスト、driver、全paired物理状態・sector・failure label、環境、集計スクリプトを含む。
tile研究全体の全raw dataを含むものではない。
全archive memberのbyte一致と相対文書リンクを確認し、6種類のcredential text patternに一致する箇所は0だった。
この限定pattern検査を包括的なsecurity auditとは扱わない。

追加ZIPを新規ディレクトリへ展開し、元の集計JSONを参照用に保持した上で、同梱スクリプトを再実行した。
全16条件・1048576対の集計JSONが元結果と全項目一致した。
元のsource ZIPとwheelのSHA256も照合した。
これは配布物からの再解析確認であり、同じデータに対する区間被覆を独立に実証したという意味ではない。

## 公開時に使う準備物

追加説明を含む本文draftは`output/experimental_release_20261019/release_body_preview_with_platform_v1.md`である。
従来の本文を保持し、source固定後の追加結果であることと、判定不一致率・LER差・BAR被覆の区別を日英で追記した。
追加ZIPへのURLは予定tag向けであり、tag・assetの公開前にアクセス可能と確認したものではない。

最終commitとそのremote CIの成功確認後は、`render_release_body_with_supplement.py --commit <40桁SHA> --ci-url <対象run URL> --output <新規本文path>`を使う。
base rendererはcommit treeと固定候補treeの一致を要求し、追加rendererは検証済みZIPのhashを照合する。
CI成功の確認、tag、Release、visibility操作はrendererに含まない。

upload用の準備ディレクトリは`output/experimental_release_20261019/assets_with_platform_v1/`である。
source ZIP・wheel・追加ZIP・3成果物をまとめた単一`SHA256SUMS`の4ファイルを揃えた。
個別ディレクトリの同名`SHA256SUMS`を重複uploadしない。
combined checksum fileのSHA256は`bc0742e0b089cb701b81662fb3aa073a090cb8f0479e58a8dfc8d8d1acd1da37`である。
commit・push・remote CI・tag・Release・公開操作はこの準備では実施していない。
packaging・再解析確認・本文生成・asset組立のsourceとreceiptは[保存manifest](data_experimental_release_2026-10-19/platform_supplement_preparation_v1/manifest.json)に対応付けた。
