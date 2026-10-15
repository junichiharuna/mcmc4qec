# mcmc4qec
mcmc4qec は、CSS 量子符号の論理誤り率を推定する Python ライブラリです。
全状態の列挙による厳密計算、直接モンテカルロ法、基準となる確率を与えて推定する BAR splitting に対応しています。
指定した失敗条件を満たす誤りをサンプリングする際には、OBF、Zanella（Z）、クラスター交換（H）、スタビライザー反転のカーネルを設定できます。

自作の符号やノイズ分布、デコーダー、失敗条件も使えます。
ノイズ分布は正規化され、デコーダーは同じ入力に対して常に同じ結果を返す必要があります。
公開 API には型注釈と `py.typed` があり、IDE や型検査器で利用できます。
受け付ける入力や自作の部品が満たすべき条件は、[API 文書](docs/api_en.md)を参照してください。

現在は開発初期の pre-alpha 版で、検証を進めています。
この文書は[英語版 README](README.md)の日本語訳です。
内容に相違がある場合は英語版を優先してください。

## インストールと最初の実行

基本機能だけを使う例は、リポジトリのディレクトリで `python -m pip install -e .` を実行すれば動かせます。
以下の toric 符号の例には追加の依存パッケージが必要なので、`python -m pip install -e ".[codes,matching]"` でインストールしてください。
現在の `make_toric_code` には、追加依存のグループ `codes` が必要です。

| extra | 用途 |
| --- | --- |
| `codes` | toric、surface、asymmetric toric、Hamming HGP、BB の符号ファクトリ |
| `matching` | PyMatching デコーダー |
| `bposd` | BP-OSD デコーダーの依存 |
| `stim` | Stim DEM と回路の例 |
| `plot` | workflow スクリプトの任意の PNG 図で、未導入時も CSV は利用可能 |
| `notebooks` | Jupyter notebook の実行と作図 |

複数のグループをまとめてインストールする場合は、`python -m pip install -e ".[codes,matching,bposd,stim,plot,notebooks]"` を使います。

PyMatching 2.4 は matplotlib 本体に依存します。
ワークフローの実行例は、描画用の pyplot が使えない場合にも結果を CSV に保存しますが、デコーダーに必要な依存パッケージは省略できません。
各ファイルに必要なパッケージは、[実行例一覧](examples/README.md)を参照してください。

```python
import numpy as np
from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig, direct_mc, sample_faulty
from mcmc4qec.adapters import matching_from_check_matrix
from mcmc4qec.codes import make_toric_code

code = make_toric_code(5)
decoder = matching_from_check_matrix(code.hz, logical_map=code.lz,
                                     identifier="toric-d5-mwpm")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
p = 0.1
mc = direct_mc(problem, p, trials=2_000, seed=11)
chain = sample_faulty(problem, p, config=SamplingConfig(samples=100, burn_in=20), seed=12)
print("Direct MC P_L and 95% Wilson interval:", mc.estimate, mc.interval)
print("Direct MC E[weight | faulty]:", mc.conditional_weight)
print("Z+H E[weight | faulty] and MCSE:", chain.conditional_weight,
      chain.conditional_weight_standard_error)
```

条件付き MCMC のマルコフ連鎖は、失敗集合の**内部**をサンプリングします。
そのため、得られた状態の出現頻度だけから、失敗する確率そのものを表す `P_L` は推定できません。
既定では Z と H の重みをそれぞれ 0.7 と 0.3、`cluster_k=2` とし、1 本の連鎖を生成します。
これらの移動とは別に、確率 0.05 で状態をそのまま保持します（lazy step）。
提案が棄却されたステップや lazy step も、同じ状態が続くサンプルとして記録します。
完全な実行例は [examples/toric_pymatching.py](examples/toric_pymatching.py) にあります。

BAR 法では、ノイズ強度の列（ladder）に沿って `P_L(p)` を推定します。
その際、最初の点での論理誤り率を基準値（anchor）として与えます。
次の例は全状態を列挙できる小さな符号を使い、この基準値を厳密に計算します。

```python
import numpy as np
from mcmc4qec import (CSSCode, CallableDecoder, IndependentBitFlip, KernelConfig,
                      Problem, SamplingConfig, estimate_logical_error, exact)

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="repetition3-minimum-weight-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(3), decoder)
ladder = [0.4, 0.25, 0.1]
result = estimate_logical_error(problem, ladder, anchor=exact(problem, ladder[0]),
                                config=SamplingConfig(samples=200, burn_in=30,
                                    kernels=KernelConfig(cluster_k=1)), seed=73)
print(result.estimates, result.intervals)
```

3 ビットの `Problem` を含む完全な実行例は [examples/bar_ladder.py](examples/bar_ladder.py) にあります。
通常の BAR 計算では、列の各点（rung）で同じデコーダーと失敗条件を使います。
直接モンテカルロ法で基準値を求める場合は、1 回以上の失敗を観測する必要があります。
隣接する分布のサンプルに、確率が正となる領域の重なりが観測されなければ、`OverlapError` が発生します。

## 統計誤差とMCMC診断

統計誤差は、追加の設定をしなくても推定値と一緒に返します。

| 手法 | 推定値と統計誤差 |
| --- | --- |
| direct MC | 論理誤り確率の `estimate` と95% Wilson区間 `interval` |
| BAR | rungごとの `estimates`・`intervals`・`log_standard_errors` |
| 条件付きMCMC | 重み平均 `conditional_weight` と、IATに基づく平均のMonte Carlo標準誤差（MCSE）`conditional_weight_standard_error` |

条件付き MCMC では、各連鎖の積分自己相関時間（IAT）と有効サンプルサイズ（ESS）、連鎖を前後に分けて計算する古典的な Gelman–Rubin 統計量（split R-hat）も返します。
これらの値に加え、連鎖間のばらつきから求めた標準誤差や提案の受理状況を、`result.diagnostics` から取得できます。

自己相関関数（ACF）の配列、ブロック長を変えた誤差の比較、ブートストラップ区間を計算する詳細診断は**オプション**です。
`diagnostics=True` で有効にでき、計算量を調整する場合は `DiagnosticsConfig` を指定します。

```python
from mcmc4qec import (BinaryLinearModel, CallableDecoder, DiagnosticsConfig,
                      IndependentBitFlip, KernelConfig, Problem, SamplingConfig,
                      sample_faulty)

# Core-only example: failure is x[0] == 1; x[1] still fluctuates.
problem = Problem(BinaryLinearModel([[1, 1]], [[1, 0]]), IndependentBitFlip(2),
                  CallableDecoder(lambda syndrome: [0], identifier="zero-v1"))
run = sample_faulty(problem, 0.3, seed=41,
    config=SamplingConfig(samples=128, burn_in=32, chains=4,
                          kernels=KernelConfig(cluster_k=1)),
    diagnostics=DiagnosticsConfig(max_lag=32, block_sizes=(1, 4, 16, 32),
                                  bootstrap_replicates=100, seed=7))
print("Conditional mean and MCSE:", run.conditional_weight,
      run.conditional_weight_standard_error)
report = run.diagnostics["trace_analysis"]
print("Classical split R-hat:", report["rhat"])
print("Chain IAT / ESS:", report["chain_iat"], report["chain_ess"])
print("Blocking SE scan:", report["blocking"])
print("Bootstrap mean intervals:", report["bootstrap"]["blocks"])
```

`diagnostics` を省略すると詳細診断は行いませんが、平均のモンテカルロ標準誤差（MCSE）は返されます。
詳細診断のうち、ブートストラップだけを省く場合は `DiagnosticsConfig(bootstrap_replicates=0)` を指定します。
`report["acf"]` には各連鎖の ACF とラグ（サンプル間の隔たり）が入り、ラグとブロック長は保存したサンプルの個数で数えます。

診断結果は JSON に変換できる数値や配列として返され、描画用のパッケージがなくても `run.to_json()` で保存できます。
`estimate_logical_error` も同じオプションを受け付け、ノイズ強度の各点について `result.diagnostics[i]["trace_analysis"]` に結果を格納します。

詳細診断には別の乱数生成器を使うため、有効にしてもサンプル列や BAR の推定値・区間は変わりません。
ここで追加するブートストラップ区間は**失敗を条件とした観測量の平均**に対するもので、論理誤り確率そのものの区間とは異なります。
誤差を算出できない場合は `None` が返されますが、この値は誤差がゼロであることを意味しません。
短い連鎖や観測量が一定の連鎖では、有用な情報が得られない場合があります。

この実装の split R-hat は、順位正規化や折り畳みを用いる版とは異なります。
診断値が良好でも、また区間が狭くても、収束や区間の名目の被覆率が保証されるわけではありません。
保存済みの Result や独自の観測量を調べるには `diagnostic_report`、数値の時系列を直接調べるには `analyze_traces` を使えます。
詳しくは[API の式と設定](docs/api_en.md#default-statistical-errors-and-optional-detailed-diagnostics)と[後処理の例](docs/tutorial_en.md#initialization-cache-and-diagnostics)を参照してください。

## 性能

組み込みの線形モデルや物理回路モデルを、対応する積ノイズと標準の失敗判定で使う場合には、専用の更新処理で高速化します。
積ノイズは、独立な成分からなるノイズです。
モデルなどを独自に継承したクラスや、独自の失敗判定を使う場合は、汎用の更新処理を使います。

2026-10-15 に、Windows 11 Pro、Python 3.11.9、AMD Ryzen 5 3600 の環境で、以下の処理速度を 2 回測定しました。
条件は p=0.01、10000 ステップ、Z の重み 0.7、H の重み 0.3、`cluster_k=2`、連鎖 1 本、`lazy=0` です。

| 符号 | ライブラリ step/s | 研究runner step/s | ライブラリ/研究の時間比 |
| --- | ---: | ---: | ---: |
| Toric d=5 | 12,026–12,281 | 23,000–23,028 | 1.87–1.91倍 |
| Toric d=7 | 10,381–10,477 | 20,147–20,162 | 1.92–1.94倍 |
| BB72 | 6,113–6,157 | 7,914–8,186 | 1.29–1.33倍 |

この条件での toric 符号の測定では、2 回とも「研究コードの実行時間の 2 倍以内」という目標を満たしました。
ライブラリ側の測定時間には結果と診断の作成を含みますが、デコーダーの構築時間は両者とも含みません。
2 回とも乱数の seed に 731 を使っており、測っているのは実行時間のばらつきです。
独立なサンプルを使った推定精度の評価ではありません。
変更前後の比較やデコーダーの設定、測定の限界は、[性能記録](docs/performance_ja.md)を参照してください。

測定は `python benchmarks/bench_step.py --steps 10000 --repeats 2 --seed 731` で実行できます。
研究コードと比較するには、`RIMC_RESEARCH_ROOT`（または `MCMC4QEC_RESEARCH`）に、読み取り専用で参照する研究リポジトリのパスを設定してください。
どちらも設定しない場合は、ライブラリ側だけを測定します。
実行には `codes` と `matching` が必要で、`--quick` と `--out` も指定できます。
既定では一時ディレクトリに CSV を保存します。
速度は機器や負荷によって変わり、この測定から混合の良さや推定精度は保証できません。

## 目的別の入口

| 目的 | 最初の資料 |
| --- | --- |
| 絶対 `P_L` を推定する | [Steane の exact・MC・BAR 比較](examples/steane_exact.py)、[toric の BAR 曲線](examples/workflows/pl_curve.py)、[BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| 失敗条件付き分布を調べる | [条件付き重みの比較](examples/workflows/conditional_weight.py)、[複数 chain の診断](examples/workflows/convergence_check.py)、[診断 notebook](notebooks/03_conditional_sampling_and_diagnostics.ipynb) |
| 自分の符号、ノイズ、デコーダーを持ち込む | [CSS 雛形](examples/templates/byo_css_bitflip.py)、[ノイズ雛形](examples/templates/byo_noise.py)、[デコーダー雛形](examples/templates/byo_decoder.py)、[持ち込み notebook](notebooks/04_bring_your_own.ipynb) |
| detector または物理回路 fault を扱う | [Stim DEM 雛形](examples/templates/byo_stim_dem.py)、[DEM 例](examples/stim_dem.py)、[物理回路 baseline](examples/circuit_baseline.py) |

手順を追って試したい場合は、[クイックスタートの notebook](notebooks/01_quickstart.ipynb)を開いてください。
[実行例一覧](examples/README.md)には、すべてのスクリプトと notebook に必要なパッケージ、および出力の読み方を載せています。
自作の部品を使う際の条件や手順は、[API 文書](docs/api_en.md)と[チュートリアル](docs/tutorial_en.md)を参照してください。

| ノイズと状態 | OBF / Z / H | stabilizer flip | デコーダー接続 |
| --- | --- | --- | --- |
| 静的 CSS bit-flip | 対応 | 任意 | PyMatching または決定的な自作デコーダー、`DecoderAdapter` 経由の BP-OSD |
| 静的 CSS phase-flip | 対応 | 任意 | `errors="Z"` の PyMatching・BP-OSD が `hx`/`lx` を使用 |
| 静的 CSS depolarising | 結合した I/X/Y/Z ラベルで対応 | 任意 | 完全な論理予測が必要で、sector 合成はデコーダー側の選択 |
| データと測定の phenomenological fault | 対応 | 非対応 | 選択した syndrome history または difference 表現を受け取るデコーダー |
| Stim detector error model | 潜在 mechanism bit 上で対応 | 非対応 | graphlike DEM に対する matching、または自作デコーダー |
| 物理 Stim 回路 location | OBF・Z・物理単一 fault、明示 location 群の H に対応 | 非対応 | PyMatching を用いる中点 surface logical-idle baseline |

`exact` は小さな離散状態空間の全状態を列挙し、`direct_mc` は指定した回数のモンテカルロ試行を行います。
`sample_faulty` は失敗を条件とする分布からサンプリングし、`estimate_logical_error` は基準値と隣接する点の BAR 比から論理誤り率を求めます。

符号を生成する関数として、toric、surface、asymmetric toric、Hamming HGP、BB72、BB108、BB144、Steane、連接 Steane を用意しています。
このうち、現在の toric、surface、asymmetric toric、Hamming HGP、BB の生成関数には `codes` が必要です。
デコーダーの構築関数は、ビット反転と位相反転（`errors="Z"`）に対する MWPM・BP-OSD に対応しています。
脱分極ノイズでは、セクターごとに復号する構成を明示的に選べます。

`SamplingConfig(cache_cap=..., cache_policy=...)` で復号結果のキャッシュ容量を制限でき、`KernelConfig(zanella_fastpath=True)` で対応する積ノイズの高速化処理を使えます。
複数の連鎖をまとめた診断、CSS 符号の剰余類に基づく厳密な初期化の補助機能、4 条件を調べる `evaluate_convergence` もあります。
4 条件すべてを判定するには、独立な直接モンテカルロ計算で求めた条件付き分散が必要です。
判定が良好でも、混合や計算の正しさが証明されるわけではありません。

物理回路の基本実装では、対応する Stim のノイズ発生箇所ごとに、互いに排他的な故障ラベルをサンプリングします。
1 箇所の故障を変更する提案には `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)`、Z と OBF の混合には `KernelConfig(zanella=0.7, single=0.3, cluster=0, stabilizer=0)` を指定します。
H も使う場合は、ノイズチャネルと故障ラベルの並びが一致する箇所のインデックスをまとめ、グループ間で重複しないように `circuit_groups` に指定します。
H は各グループで故障がある箇所の数を保存するため、H 単独の連鎖は一般に既約ではありません。
回路にはスタビライザー反転を使えず、既定の Z+H 設定を使う場合もグループの指定が必要です。

組み込み回路モデルと標準の失敗判定を使う場合は、故障の効果を差分で更新します。
独自の失敗判定を使う場合は、汎用の評価処理を使います。
surface 符号の論理アイドル回路の例では、ノイズを含む 2d ラウンドのうち、最初の d ラウンドを終えた時点の観測量を評価します。
検出器誤りモデル（DEM）はデコーダーの構築に使い、サンプリングは回路上の物理的な故障箇所について行います。
詳しくは[物理回路の基本例](examples/circuit_baseline.py)と[カーネルの比較](examples/circuit_zanella.py)を参照してください。

ESS や split R-hat が良好でも、収束、エルゴード性、計算の正しさが証明されるわけではありません。
重みの時系列に問題が見えなくても、連鎖が状態空間の一部に閉じ込められていることがあります。
`p_dependent_decoder_approx` モードの BAR 計算は、失敗集合の変化を無視する近似であり、それによる偏りは区間推定に含まれません。
確率が正となる状態の範囲や初期化の制約、サンプルで観測された分布の重なり、標本数、ブロック長にも推定結果は左右されます。

DEM のサンプリングが、あらゆる物理回路ノイズモデルを再現すると示したわけではありません。
物理回路の基本実装についても、公開された図表の再現を示したものではありません。

BAR の誤差評価には、既定でブロック・ブートストラップを使います。
`uncertainty="cross_chain"` を指定すると、独立した連鎖の間のばらつきから誤差を評価します。
この方法には 2 本以上の連鎖が必要ですが、全サンプルをまとめて求める点推定値は変わりません。
どちらの方法も、短い連鎖や混合が不十分な連鎖に共通する偏りは評価できません。
論文で扱う観測量平均の実験から BAR 区間の被覆率が確立されたわけではなく、診断を通過しても 95% の被覆は保証されません。
短い実行例の結果を精度の高い推定として使う前に、[BAR の感度検証](docs/bar_sensitivity_ja.md)と[API の仮定](docs/api_en.md)を確認してください。

関連論文は準備中です。
ソフトウェアの引用に用いる著者名は、所有者の指定により `junichi haruna` としています。
所属、DOI、公開日、公開の詳細は未確定です。
[CITATION.cff](CITATION.cff) と [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。
コードのライセンスは [MIT License](LICENSE) ですが、パッケージとしての一般公開はまだ行っていません。
