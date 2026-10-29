# Experimental版のリリースノート

mcmc4qec 0.1.0.dev5のリリースノートである。
2026-10-24付のexperimental版の配布先はGitHubとし、PyPI公開は後に行う。
実施済みの確認とその限界は末尾の公開準備記録に記す。

直接MC、失敗条件付きMCMC、BAR splittingによる論理誤り率推定を提供する。
今回の版では既存BP-OSD・matching接続に加え、tile符号の構成とBP-LSD・BeliefFind・単独Union-Findを含む。
[API](api_en.md)、[チュートリアル](tutorial_ja.md)、[実行例一覧](../examples/README.md)から利用できる。

## checkoutからの利用

Python 3.11以降の仮想環境を用意し、リポジトリ直下で実行する。

```sh
python -m pip install '.[bposd,codes]' 'ldpc==2.4.1'
python examples/decoder_comparison.py --code steane --quick
python examples/decoder_comparison.py --code tile72 --quick
python examples/workflows/tile_capacity_fixed_prior.py --help
```

短い例は接続方法の確認用であり、その標本数で研究精度を保証しない。
optional decoderなしのcoreは`python -m pip install .`で導入できる。

## この版に含まれるデータ

ソースsnapshotにはコード、文書、一部の検証表・報告、テストに必要なdata fixtureを含む。
全raw traceと重み層別samplingの全データは含まない。
これらは別途保存しており、完全なデータセットの公開download先はまだ確定していない。
Zenodoのdataset記録には、識別子を置換した独立計時のraw payload（49実行root、約6 GB）、weight-stratified referenceとその監査、受理済みselection、最終reportと証拠記録、pinされたscriptと環境記録、校正cohortの各runの小さなsummaryを、それぞれのSHA-256 manifestとともに収める予定である。
校正cohortの完全なraw trace（約223 GiB）はこの記録には大きすぎるため、著者のクラスタと手元に保管し、要請に応じて提供する。
運用手順書と証跡記録は著者のcluster環境のものである。
公開前にユーザー名とホスト名を置換したため、証跡に記録されたSHA-256はリポジトリ外に保管した置換前の原本を指す。
参照するtransport archiveの一部もこのソースsnapshotには含まれない。
インストール確認には実行例を使い、報告した科学計測の完全な独立再解析には対応するraw dataと実行bundleが必要である。

## 対応範囲と制限

- BP-LSDはorder 0に対応し、正orderを拒否する。
  zero syndromeではmetadataに記録した恒等補正規則を使う。
- BeliefFindはinversionが既定である。
  peelingは列重み1または2のgraphlike行列に限り、tileをそのまま渡せない。
- 単独Union-Findは非重み付きで、検証済みの`ldpc==2.4.1`と`bits_per_step=1`だけを受け付ける。
  UF系はいずれも次数0の列を拒否する。
- BARの全rungとreferenceでdecoderのprior・設定・native環境を固定する。
  depolarizingではjoint Pauli noiseを保持し、sector priorを`2*p/3`としても物理ノイズを独立sectorに置き換えない。
- BP-OSDは試験したtile288 depolarizingの1状態でWindows/Linuxの失敗判定が異なった。
  package版の一致だけでは環境間で同じfailure集合を保証しない。
- tileの主4条件の検証、低ノイズ校正、独立計時（48手法行、各192反復）は完了した（[2026-10-29の更新](tile_validation_interim_en.md)、英語）。
  BAR区間の被覆不足（192反復中151〜176）と計時での混合診断の未取得があり、名目95%被覆は一般には保証しない。
  BARが直接MCより安いことが支持されるのはtile72符号の `p ≤ 0.003` に限られ（精度正規化費用で2〜35倍）、`p = 0.01` では直接MCのほうが安い。
- 新decoderの接続と小符号の受入は確認済みだが、BARの精度・被覆・速度順位は未校正である。

根拠と適用限界は[tile報告](wp/tile_validation_report_2026-10-18_ja.md)、[検証状況](wp/tile_validation_status_2026-10-17_ja.md)、[decoder検証](wp/basic_decoders_validation_2026-10-18_ja.md)に記録する。
[公開準備記録](wp/experimental_release_readiness_2026-10-19_ja.md)では成功した確認と未完了・時間上限に達した確認を区別する。

長期検証はexperimental公開後も継続する。
診断未定義・区間未取得・未収束も集計の分母から除外しない。
独立referenceのない領域の設定間整合性を精度や被覆の保証とは扱わない。
