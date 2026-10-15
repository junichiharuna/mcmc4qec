# mcmc4qec

mcmc4qec は、量子誤り訂正の論理誤り率を推定する Python ライブラリです。
直接モンテカルロ法では観測しにくいまれな失敗を、失敗条件付き MCMC と Bennett acceptance ratio（BAR）による splitting で推定します。
小さな問題の全列挙や直接モンテカルロ法にも対応し、自作の符号・ノイズモデル・デコーダーを使えます。

現在は検証中の **pre-alpha 版**で、パッケージとしての一般公開はまだ行っていません。

[English](README.md) · [チュートリアル](docs/tutorial_ja.md) · [API 文書（英語）](docs/api_en.md) · [実行例一覧](examples/README.md)

## インストールと実行例

リポジトリのディレクトリで、符号の生成と PyMatching に必要なパッケージをまとめてインストールします。

```sh
python -m pip install -e ".[codes,matching]"
```

距離 3 の toric 符号に独立なビット反転を加え、MWPM デコーダーで復号したときの論理誤り率を推定します。
`ladder` に並べたノイズ強度 `0.2 → 0.15 → 0.1` に沿って計算し、各点の推定値と誤差区間を表示します。

```python
import mcmc4qec as qec

code = qec.make_toric_code(3)
noise = qec.IndependentBitFlip(code.n)
decoder = qec.mwpm_decoder(code)
problem = qec.Problem(code.bit_flip_model(), noise, decoder)

# Physical bit-flip probabilities, from the anchor to the target.
ladder = [0.2, 0.15, 0.1]
result = qec.estimate_logical_error(problem, ladder)

for p, estimate, interval in zip(ladder, result.estimates, result.intervals):
    print(f"p={p}: P_L={estimate:.6g}, interval={interval}")
```

最初のノイズ強度での基準値は自動計算され、統計誤差も標準で返ります。
`config`・`anchor`・`seed` は必要に応じて指定できます。
符号の中身、ladder の仕組み、計算条件の変更、結果の読み方は、[この例を解説するチュートリアル](docs/tutorial_ja.md)へ進んでください。

## 対応機能と追加パッケージ

| 分野 | 対応内容 |
| --- | --- |
| 符号 | toric、surface、asymmetric toric、Hamming HGP、BB72/108/144、Steane、連接 Steane |
| ノイズ | ビット反転、位相反転、脱分極、現象論的なデータ・測定誤り、Stim DEM、物理回路の故障 |
| デコーダー | PyMatching、BP-OSD、自作デコーダー |
| 計算手法 | 全列挙 `exact`、直接 MC `direct_mc`、BAR `estimate_logical_error`、失敗条件付き MCMC `sample_faulty` |

依存パッケージは、符号生成用の `codes`、デコーダー用の `matching`・`bposd`、Stim 用の `stim` を選んで追加できます。
作図には `plot`、notebook の実行には `notebooks` を使います。
追加パッケージなしで試す場合は、`python -m pip install -e .` でインストールし、`python examples/steane_exact.py --quick` を実行してください。

## 次に読む

| 目的 | 案内 |
| --- | --- |
| 最初の例を理解し、設定や診断を調整する | [チュートリアル](docs/tutorial_ja.md) |
| 自分の符号・ノイズ・デコーダーを使う | [部品を差し替える例](docs/tutorial_ja.md#自分の-css-行列を使う) |
| 別の符号やノイズで計算する・notebook を使う | [実行例と依存パッケージの一覧](examples/README.md) |
| 引数・返り値・数式を確認する | [API 文書（英語）](docs/api_en.md) |

## 利用上の注意

実行例の既定設定は、研究に必要な精度を保証するものではありません。
通常の BAR では、正の基準値、ノイズ強度を通じて共通のデコーダーと失敗条件、隣接する分布のサンプルの重なりが必要です。
`sample_faulty` のサンプルだけから、論理誤り率そのものは求められません。

統計誤差や良好な MCMC 診断値だけで、収束や区間の名目被覆率が保証されるわけではありません。
検証の条件と限界は、[BAR の感度検証](docs/bar_sensitivity_ja.md)、[性能記録](docs/performance_ja.md)、[回路モデルの検証記録](docs/circuit_baseline_ja.md)を参照してください。

## ライセンスと引用

コードのライセンスは [MIT License](LICENSE)、引用情報は [CITATION.cff](CITATION.cff) にあります。
関連論文は準備中で、所属・DOI・リリースの詳細は未確定です。
開発や貢献の手順は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。
この日本語版と英語版に相違がある場合は、英語版を優先してください。
