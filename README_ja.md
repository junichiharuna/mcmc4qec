# mcmc4qec

mcmc4qec は、量子誤り訂正の論理誤り率を推定する Python ライブラリです。
直接モンテカルロ法では観測に時間がかかる、まれな失敗も推定の対象としています。
CSS 符号に対する全状態の列挙、直接モンテカルロ法、基準値を用いた Bennett acceptance ratio（BAR）splitting に対応し、自作の符号・ノイズモデル・デコーダーも使えます。

現在は検証中の **pre-alpha 版**で、パッケージとしての一般公開はまだ行っていません。
この文書は日本語の案内です。
内容に相違がある場合は、英語版を優先してください。
[English](README.md) · [API 文書](docs/api_en.md) · [チュートリアル](docs/tutorial_en.md) · [実行例一覧](examples/README.md)

## まず試す

リポジトリのディレクトリで、基本パッケージをインストールします。

```sh
python -m pip install -e .
```

次の例では、3 量子ビットの繰り返し符号について、3 通りのビット反転率で論理誤り率を推定します。
BAR splitting は、あるノイズ強度での論理誤り率を基準値（**anchor**）とし、ノイズ強度の列（**ladder**）に沿って他の点の論理誤り率を求める方法です。
ここでは `p=0.4` の基準値を全状態の列挙で計算します。
追加の依存パッケージは不要です。

```python
import numpy as np
from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip, KernelConfig,
                      Problem, SamplingConfig, estimate_logical_error, exact)

code = CSSCode(hx=np.zeros((0, 3), dtype=int),
               hz=[[1, 1, 0], [0, 1, 1]],
               lx=[[1, 1, 1]], lz=[[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="repetition3-minimum-weight-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
ladder = [0.4, 0.25, 0.1]
result = estimate_logical_error(
    problem, ladder, anchor=exact(problem, ladder[0]),
    config=SamplingConfig(samples=200, burn_in=30,
                          kernels=KernelConfig(cluster_k=1)), seed=73)
for p, estimate, interval in zip(ladder, result.estimates, result.intervals):
    print(f"p={p}: P_L={estimate:.6g}, interval={interval}")
```

出力の各行には、ノイズ強度、論理誤り率 `P_L` の推定値、誤差区間が並びます。
サンプル数や `cluster_k=1` はこの小さな例のための設定であり、研究に必要な精度を保証するものではありません。
`CallableDecoder` は論理観測量の予測値を返します。
行列とデコーダーの規約は、[CSS 符号のチュートリアル](docs/tutorial_en.md#your-css-matrices)で説明しています。
厳密計算・直接 MC・BAR を比較して試すには、`python examples/steane_exact.py --quick` を実行するか、[入門 notebook](notebooks/01_quickstart.ipynb)を開いてください。

## 目的に合う実行例を選ぶ

求めたい量に応じて、使う関数と実行例を選びます。
特に `sample_faulty` は、**失敗が起きたという条件のもとで**サンプリングする関数です。
得られた状態の出現頻度だけから、失敗する確率そのものを表す `P_L` は求められません。

| 目的 | API | 実行例 |
| --- | --- | --- |
| 小さな問題を全列挙する・直接 MC で計算する | `exact`、`direct_mc` | [Steane 符号での比較](examples/steane_exact.py) |
| 複数のノイズ強度で BAR により `P_L` を推定する | `estimate_logical_error` | [toric 符号の BAR 曲線](examples/workflows/pl_curve.py)、[BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| 失敗した場合の誤り分布を調べる | `sample_faulty` | [条件付き重みの比較](examples/workflows/conditional_weight.py)、[複数の連鎖による診断](examples/workflows/convergence_check.py) |
| 自分の符号・ノイズ・デコーダーを使う | `Problem` と各部品のインターフェース | [CSS 符号のひな形](examples/templates/byo_css_bitflip.py)、[ノイズのひな形](examples/templates/byo_noise.py)、[デコーダーのひな形](examples/templates/byo_decoder.py) |
| 検出器誤りや物理回路の故障をサンプリングする | DEM・回路モデル | [Stim DEM](examples/stim_dem.py)、[物理回路の基本例](examples/circuit_baseline.py) |

[実行例一覧](examples/README.md)には、すべてのスクリプトと notebook、必要な依存パッケージ、出力の読み方をまとめています。

## 対応するモデルと追加パッケージ

符号の生成関数は、toric、surface、asymmetric toric、Hamming HGP、BB72/108/144、Steane、連接 Steane に対応しています。
ノイズモデルには、ビット反転、位相反転、I/X/Y/Z をまとめて扱う脱分極ノイズ、データと測定の誤りを扱う現象論的モデル、Stim の検出器誤りモデル（DEM）、物理回路の故障モデルがあります。
デコーダーは PyMatching と BP-OSD に接続できます。
自作の部品を使う場合は、ノイズの正規化やデコーダーの決定性など、[API の契約](docs/api_en.md)を満たす必要があります。

必要な機能に応じて、依存パッケージのグループ（extra）を追加します。
例えば [toric 符号を MWPM で復号する例](examples/toric_pymatching.py)には、`python -m pip install -e ".[codes,matching]"` を使います。

| extra | 用途 |
| --- | --- |
| `codes` | toric、surface、asymmetric toric、Hamming HGP、BB の符号生成 |
| `matching` | PyMatching デコーダー |
| `bposd` | BP-OSD デコーダー |
| `stim` | Stim DEM と回路の例 |
| `plot` | ワークフローの結果を PNG で作図（CSV 出力も利用可能） |
| `notebooks` | notebook の実行と作図 |

MCMC の更新には、1 ビット反転（OBF）、Zanella（Z）、クラスター交換（H）、静的 CSS モデルでのスタビライザー反転を使えます。
既定値は Z/H の重みが 0.7/0.3、`cluster_k=2`、連鎖が 1 本、状態をそのまま保持する確率（lazy）が 0.05 です。
棄却されたステップや lazy step もサンプル列に残します。
物理回路モデルでは、H に使う故障箇所のグループを明示するなど、回路用の設定が必要です。
対応する組み合わせと制約は、[回路のチュートリアル](docs/tutorial_en.md#physical-circuit-faults)を参照してください。

## 推定値・統計誤差・診断の読み方

統計誤差は、追加の設定をしなくても推定値と一緒に返します。

| 手法 | 推定値 | 統計誤差 |
| --- | --- | --- |
| 直接 MC | `estimate` | 95% Wilson 区間 `interval` |
| BAR | `estimates` | ノイズ強度ごとの `intervals` と `log_standard_errors` |
| 条件付き MCMC | `conditional_weight` | `conditional_weight_standard_error`：IAT に基づく重み平均のモンテカルロ標準誤差 |

条件付き MCMC では、積分自己相関時間（IAT）、有効サンプルサイズ（ESS）、古典的な Gelman–Rubin 統計量の split R-hat、連鎖間の標準誤差、提案の受理状況も `result.diagnostics` に返します。
算出できない誤差は `None` となり、誤差ゼロを意味しません。
短い連鎖や観測量が一定の連鎖では、有用な診断値が得られない場合があります。

### 詳細な診断を追加する

`sample_faulty` または `estimate_logical_error` に `diagnostics=True` を指定すると、自己相関の配列、ブロック長ごとの誤差評価、条件付き観測量の平均に対するブートストラップ区間を追加します。
ラグ、ブロック長、ブートストラップの反復数は `DiagnosticsConfig` で調整できます。
診断結果は数値として返され、`to_json()` で保存できるため、描画用パッケージは不要です。
詳細診断には別の乱数生成器を使い、サンプル列や BAR の推定値・区間は変えません。

実行例と結果の取得方法は、[診断のチュートリアル](docs/tutorial_en.md#initialization-cache-and-diagnostics)、[診断 notebook](notebooks/03_conditional_sampling_and_diagnostics.ipynb)、[API の式と設定](docs/api_en.md#default-statistical-errors-and-optional-detailed-diagnostics)を参照してください。
API 文書では、`diagnostic_report` と `analyze_traces` を使って保存済みの結果や独自の観測量を解析する方法も説明しています。

## 検証状況と利用上の注意

通常の BAR 計算では、正の失敗確率を持つ基準値を与え、すべてのノイズ強度で同じデコーダーと失敗条件を使います。
隣接する分布のサンプルに、確率が正となる領域の重なりが観測されなければ、`OverlapError` が発生します。
`p_dependent_decoder_approx` は失敗集合の変化を無視する近似であり、それによる偏りは誤差区間に含まれません。

BAR の誤差評価には、既定でブロック・ブートストラップを使います。
`uncertainty="cross_chain"` を指定すると、全サンプルから求める点推定値を保ったまま、2 本以上の独立した連鎖のばらつきから誤差を評価します。
どちらも、混合が不十分な連鎖に共通する偏りは評価できません。
ESS や R-hat が良好でも、収束、エルゴード性、計算の正しさ、区間の名目被覆率は保証されません。
短い実験における被覆率の限界は、[BAR の感度検証](docs/bar_sensitivity_ja.md)に記録しています。
また、DEM と物理回路の基本実装ではノイズモデルが異なり、いずれも公開された回路の計算結果を再現すると示したものではありません。

実行時間は、[性能記録](docs/performance_ja.md)と[ベンチマーク](benchmarks/bench_step.py)を参照してください。
2026-10-15 の toric d=5・d=7 の測定では、その条件で研究コードの実行時間の 2 倍以内という目標を達成しました。
同じ seed による実行時間の反復測定であり、他の条件での性能やサンプリング精度を保証するものではありません。

## ライセンスと引用

コードのライセンスは [MIT License](LICENSE) です。
引用情報は [CITATION.cff](CITATION.cff) にあります。
関連論文は準備中で、所属・DOI・リリースの詳細は未確定です。
開発や貢献の手順は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。
