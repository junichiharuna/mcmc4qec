# mcmc4qec

mcmc4qec は、量子誤り訂正の論理誤り率を推定する Python ライブラリです。
論理誤りがまれにしか起きない条件では、直接モンテカルロ法で十分な回数の失敗を観測するのに時間がかかります。
mcmc4qec は、失敗を観測しやすいノイズ強度で求めた確率を基準に、ノイズ強度を段階的に下げながら論理誤り率を推定します。
この計算には、失敗条件付き MCMC と Bennett acceptance ratio（BAR）を用いた splitting を使います。

小さな問題の全列挙や直接モンテカルロ法にも対応し、組み込みの CSS 符号に加えて、自作の符号・ノイズモデル・デコーダーを使えます。
現在は検証中の **pre-alpha 版**で、パッケージとしての一般公開はまだ行っていません。

[English](README.md) · [API 文書](docs/api_en.md) · [チュートリアル](docs/tutorial_en.md) · [実行例一覧](examples/README.md)

## インストールと実行例

リポジトリのディレクトリで、符号の生成と PyMatching に必要なパッケージをまとめてインストールします。

```sh
python -m pip install -e ".[codes,matching]"
```

次の例では、距離 3 の toric 符号に独立なビット反転を加え、MWPM デコーダーで復号したときの論理誤り率を推定します。
物理的なビット反転率を `0.2 → 0.15 → 0.1` と変え、それぞれの推定値と誤差区間を表示します。

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

出力の各行には、ビット反転率 `p`、論理誤り率 `P_L` の推定値、その誤差区間が並びます。
この例は動作を確認するための設定です。
研究に使う際は、サンプル数や診断結果を確認して計算条件を調整してください。

## 実行例の仕組み

### 符号・ノイズ・デコーダー

`make_toric_code(3)` が返す `code` には、符号を定義する行列が入っています。
上の例では、次の属性を参照できます。

| 属性 | 内容 | この例での値・形状 |
| --- | --- | --- |
| `code.n` | 物理量子ビット数 | `18` |
| `code.hx`・`code.hz` | X・Z 検査行列 | それぞれ `(9, 18)` |
| `code.lx`・`code.lz` | X・Z 論理演算子を表す行列 | それぞれ `(2, 18)` |

`code.bit_flip_model()` は、ビット反転からシンドロームと論理観測量を求めるモデルを作ります。
この計算では、それぞれ `hz` と `lz` を使います。
`noise` は誤りの確率分布を定め、`decoder` はシンドロームから論理観測量を予測します。
`Problem` はこのモデル・ノイズ・デコーダーをまとめ、実際の論理観測量と予測が一致するかで復号の成否を判定します。
行列やデコーダーを自分で定義する方法は、[CSS 符号のチュートリアル](docs/tutorial_en.md#your-css-matrices)で説明しています。

### ノイズ強度の列と基準値

`ladder` は、推定に使うノイズ強度を順に並べたものです。
上の例では、まず `p=0.2` の論理誤り率を基準値（**anchor**）として自動計算します。
次に、隣り合うノイズ強度での論理誤り率の比を BAR で求め、`p=0.15`、`p=0.1` の推定値につなげます。

基準値は、状態数が小さければ全列挙、それ以外は直接モンテカルロ法で計算します。
`anchor` を渡して、別途求めた基準値を使うこともできます。
サンプル数などは `config` で変更でき、同じ設定で結果を再現したい場合は `seed=73` のように指定します。
いずれも省略可能です。
具体的な既定値と指定方法は、[API 文書の設定例](docs/api_en.md#automatic-bar-anchor)を参照してください。

## 結果と統計誤差

統計誤差は、追加の設定をしなくても推定値と一緒に返します。
上の BAR の例では、`result.estimates` と `result.intervals` が `ladder` と同じ順に並びます。

| 手法 | 推定値 | 統計誤差 |
| --- | --- | --- |
| 直接 MC | `estimate` | 95% Wilson 区間 `interval` |
| BAR | `estimates` | ノイズ強度ごとの `intervals` と `log_standard_errors` |
| 失敗条件付き MCMC | `conditional_weight` | 重み平均の標準誤差 `conditional_weight_standard_error`（自己相関を考慮） |

BAR の誤差評価には、既定でブロック・ブートストラップを使います。
2 本以上の独立した連鎖を使う場合は、`uncertainty="cross_chain"` で連鎖間のばらつきから誤差を評価する方法も選べます。
算出できない誤差は `None` となり、誤差ゼロを意味しません。

### MCMC の診断

失敗条件付き MCMC では、積分自己相関時間（IAT）、有効サンプルサイズ（ESS）、Gelman–Rubin 統計量（古典的な split R-hat）、連鎖間の標準誤差、提案の受理状況も `result.diagnostics` に返します。
短い連鎖や観測量が一定の連鎖では、有用な診断値が得られない場合があります。

`sample_faulty` または `estimate_logical_error` に `diagnostics=True` を指定すると、自己相関の配列、ブロック長ごとの誤差評価、条件付き観測量の平均に対するブートストラップ区間を追加します。
これらは観測量の平均を調べるための診断で、BAR の論理誤り率の誤差区間とは別のものです。
診断結果は数値として返され、`to_json()` で保存できます。
詳細診断を有効にしても、サンプル列や BAR の推定値・区間は変わりません。

結果の取得方法は[診断のチュートリアル](docs/tutorial_en.md#initialization-cache-and-diagnostics)、`DiagnosticsConfig` による設定や保存済みデータの解析は [API 文書](docs/api_en.md#default-statistical-errors-and-optional-detailed-diagnostics)を参照してください。

## 対応機能と実行例

組み込みの符号は、toric、surface、asymmetric toric、Hamming HGP、BB72/108/144、Steane、連接 Steane です。
ノイズモデルには、ビット反転、位相反転、脱分極ノイズ、データと測定の誤りを扱う現象論的モデル、Stim の検出器誤りモデル（DEM）、物理回路の故障モデルがあります。
デコーダーは PyMatching と BP-OSD に接続できます。

### 目的に合う実行例を選ぶ

| 目的 | API | 実行例 |
| --- | --- | --- |
| 小さな問題を全列挙する・直接 MC で計算する | `exact`、`direct_mc` | [Steane 符号での比較](examples/steane_exact.py) |
| 複数のノイズ強度で論理誤り率を推定する | `estimate_logical_error` | [toric 符号の BAR 曲線](examples/workflows/pl_curve.py)、[BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| 失敗した場合の誤り分布を調べる | `sample_faulty` | [条件付き重みの比較](examples/workflows/conditional_weight.py)、[複数の連鎖による診断](examples/workflows/convergence_check.py) |
| 自分の符号・ノイズ・デコーダーを使う | `Problem` と各部品のインターフェース | [CSS 符号](examples/templates/byo_css_bitflip.py)・[ノイズ](examples/templates/byo_noise.py)・[デコーダー](examples/templates/byo_decoder.py)のひな形 |
| 検出器誤りや物理回路の故障をサンプリングする | DEM・回路モデル | [Stim DEM](examples/stim_dem.py)、[物理回路の基本例](examples/circuit_baseline.py) |

`sample_faulty` は、失敗が起きたという条件のもとでサンプリングします。
得られた状態の出現頻度だけから、論理誤り率 `P_L` は求められません。
すべてのスクリプトと notebook、出力の読み方は[実行例一覧](examples/README.md)にまとめています。

### 追加パッケージ

必要な機能に応じて、依存パッケージのグループ（extra）を追加します。
冒頭のインストール例では、`codes` と `matching` を選んでいます。

| extra | 用途 |
| --- | --- |
| `codes` | toric、surface、asymmetric toric、Hamming HGP、BB の符号生成 |
| `matching` | PyMatching デコーダー |
| `bposd` | BP-OSD デコーダー |
| `stim` | Stim DEM と回路の例 |
| `plot` | ワークフローの結果を PNG で作図（CSV 出力も利用可能） |
| `notebooks` | notebook の実行と作図 |

追加パッケージなしで試す場合は、`python -m pip install -e .` でインストールし、`python examples/steane_exact.py --quick` を実行してください。
自作の部品が満たすべき条件や MCMC の更新手法は [API 文書](docs/api_en.md)、回路モデル固有の設定は[回路のチュートリアル](docs/tutorial_en.md#physical-circuit-faults)で説明しています。

## 適用条件と検証状況

通常の BAR 計算では、正の失敗確率を持つ基準値を使い、すべてのノイズ強度でデコーダーと失敗条件を共通にする必要があります。
隣り合う分布のサンプルに十分な重なりがあることも重要です。
必要な重なりが観測されない場合は `OverlapError` が発生します。
ノイズ強度に応じてデコーダーを変える近似モードについては、[API 文書](docs/api_en.md)を参照してください。

統計誤差の評価だけでは、探索が不十分な MCMC による偏りは捉えきれません。
ESS や R-hat が良好でも、収束、エルゴード性、計算の正しさ、区間の名目被覆率が保証されるわけではありません。
短い実験で確認した誤差区間の限界は[BAR の感度検証](docs/bar_sensitivity_ja.md)、実行時間と測定条件は[性能記録](docs/performance_ja.md)に記録しています。
DEM と物理回路では、扱うノイズモデルが異なります。
物理回路モデルの対応範囲と検証結果は、[回路モデルの検証記録](docs/circuit_baseline_ja.md)を参照してください。

## ライセンスと引用

コードのライセンスは [MIT License](LICENSE)、引用情報は [CITATION.cff](CITATION.cff) にあります。
関連論文は準備中で、所属・DOI・リリースの詳細は未確定です。
開発や貢献の手順は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。
この日本語版と英語版に相違がある場合は、英語版を優先してください。
