# mcmc4qec ドキュメント

[English](index.md)

mcmc4qec は、量子誤り訂正の論理誤り率を推定する Python ライブラリです。
符号・ノイズ分布・デコーダーを指定し、全列挙、直接モンテカルロ法、または失敗条件付き MCMC と Bennett acceptance ratio（BAR）による splitting で計算します。
現在は pre-alpha 版で、API の整備と数値検証を進めています。

## まず一通り計算する

[チュートリアル](tutorial_ja.md)では、距離 3 の toric 符号と MWPM デコーダーによる推定から始めます。
ノイズ強度の列と基準確率の役割、サンプル数の設定、返された誤差の意味を確認し、最後に自作の符号やノイズへ置き換えます。
Python 3.11 以降を使い、取得したリポジトリのルートでインストールしてください。

```sh
python -m pip install -e ".[codes,matching]"
```

追加パッケージを使わずに試す場合は、`python -m pip install -e .` でインストールし、[小さな CSS 符号の例](tutorial_ja.md#自分の-css-行列を使う)から始められます。
概要と短い実行例は [README](../README_ja.md) にあります。

## 目的に合わせて読む

| 知りたいこと | 読む文書 |
| --- | --- |
| 最初の推定を手順と理由まで理解する | [チュートリアル](tutorial_ja.md) |
| 手法を選ぶ、誤差を調べる、別のノイズを使う | [目的別ガイド](guide_ja.md) |
| 前提条件・既定値・統計量の定義を確認する | [API の契約と統計上の取り決め（英語）](api_en.md) |
| 引数・返り値・クラスのメソッドを調べる | [サンプリング API](reference/sampling.md)、[結果と診断の API](reference/results.md) |
| スクリプトや notebook を動かす | [実行例一覧（英語）](../examples/README.md) |
| 数値結果の検証記録を読む | [リリースノートと検証記録](experimental_release_notes_ja.md) |
| tileの現時点の結果と未完了の検証を確認する | [tile検証報告](wp/tile_validation_report_2026-10-18_ja.md)、[検証状況](wp/tile_validation_status_2026-10-17_ja.md) |

API リファレンスの引数・型・docstring は、現在のソースから生成します。
推定法の前提は引数の一覧だけでは分からないので、API の契約を説明した文書も併せて参照してください。
過去の開発記録や測定データはリポジトリに残し、必要な箇所からリンクしています。

## 手元で読む・ビルドする

Markdown 文書はリポジトリ上でも読めます。
検索付きのサイトを手元で開くには、リポジトリのルートで次を実行します。

```sh
python -m pip install -e ".[docs]"
python -m mkdocs serve
```

MkDocs が表示したローカルアドレス（通常は `http://127.0.0.1:8000`）をブラウザーで開いてください。
`python -m mkdocs build --strict` でリンクを検査しながら静的 HTML を生成でき、結果は `output/docs-site/` に保存されます。
文書を編集するときは [Contributing の説明](../CONTRIBUTING.md#documentation)も参照してください。

ライセンスは [MIT](../LICENSE) です。
引用情報は [CITATION.cff](../CITATION.cff) にあります。
