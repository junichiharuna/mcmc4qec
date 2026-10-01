# mcmc4qec
英語版の [README.md](README.md) が一次版であり、食い違う場合は英語版に従ってください。
CSS 量子符号の論理誤り率を exact 列挙、直接モンテカルロ法、anchor 付き BAR splitting で推定します。
OBF、Zanella（Z）、cluster exchange（H）、stabilizer のカーネルを設定して、失敗条件付きの誤りをサンプリングします。

公開APIにはIDEと型検査器向けの型注釈と`py.typed`を含みます。
対応する入力と独自部品の契約は[API文書](docs/api_en.md)を参照してください。
自作の符号、正規化されたノイズ分布、決定的なデコーダー、失敗条件を持ち込めます。

この pre-alpha パッケージは検証中です。

## インストールと最初の実行

core の例には、ローカル checkout で `python -m pip install -e .` を実行します。
以下の toric 符号の例には `python -m pip install -e ".[codes,matching]"` が必要で、現在の `make_toric_code` には `codes` extra の依存が必要です。

| extra | 用途 |
| --- | --- |
| `codes` | toric、surface、asymmetric toric、Hamming HGP、BB の符号ファクトリ |
| `matching` | PyMatching デコーダー |
| `bposd` | BP-OSD デコーダーの依存 |
| `stim` | Stim DEM と回路の例 |
| `plot` | workflow スクリプトの任意の PNG 図で、未導入時も CSV は利用可能 |
| `notebooks` | Jupyter notebook の実行と作図 |

複数をまとめて入れる場合は `python -m pip install -e ".[codes,matching,bposd,stim,plot,notebooks]"` を使います。

PyMatching 2.4 は matplotlib 本体に依存します。
workflow の CSV 保存経路は描画用 pyplot が使えない場合に対応し、デコーダーの依存を取り除くものではありません。
各ファイルの依存は [実行例一覧](examples/README.md) を参照してください。

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
print("Z+H E[weight | faulty]:", np.count_nonzero(chain.states, axis=-1).mean())
```

条件付き chain は失敗集合の**内部**の量を調べるもので、状態頻度から絶対 `P_L` は推定できません。
既定は Z の重み 0.7、H の重み 0.3、`cluster_k=2`、1 chain、別枠の lazy 確率 0.05 です。
棄却と lazy step も trace に残ります。
完全な例は [examples/toric_pymatching.py](examples/toric_pymatching.py) にあります。

anchor 付き BAR ladder は複数の確率にわたる `P_L(p)` を推定します。
次の短い例は列挙可能な小さい符号を使い、最初の rung を exact で anchor します。

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

3 ビットの `Problem` を含む完全な ladder は [examples/bar_ladder.py](examples/bar_ladder.py) にあります。
standard ladder では同じデコーダーと failure 定義を全 rung で使います。
MC anchor には 1 回以上の失敗観測が必要です。
観測された support の重なりがない場合は `OverlapError` が発生します。

## 性能

専用stepは、組み込みの線形モデルと積ノイズの実型の組み合わせで、標準の論理failureを使う場合に適用されます。
独自派生型やfailure predicateでは汎用経路を使います。

2026-10-01にWindows 11 Pro、Python 3.11.9、AMD Ryzen 5 3600で、p=0.01、10000 step、Z/H=0.7/0.3、`cluster_k=2`、1 chain、`lazy=0`を2回測定しました。

| 符号 | ライブラリ step/s | 研究runner step/s | ライブラリ/研究の時間比 |
| --- | ---: | ---: | ---: |
| Toric d=5 | 8,386–8,553 | 22,825–23,202 | 2.71–2.72倍 |
| Toric d=7 | 7,322–7,605 | 19,149–19,629 | 2.58–2.62倍 |
| BB72 | 4,826–4,932 | 7,742–7,962 | 1.57–1.65倍 |

この参照実装は、今回の処理では研究runnerより時間がかかります。
ライブラリ側は結果と診断の作成を含み、両者ともdecoder構築時間を除きます。
2回ともseed 731を使い、時間のばらつきを測ったもので、独立標本による精度評価ではありません。
decoderの設定と残る処理時間の内訳は[性能記録](docs/performance_ja.md)を参照してください。

`python benchmarks/bench_step.py --steps 10000 --repeats 2 --seed 731`で実行できます。
比較する場合は`RIMC_RESEARCH_ROOT`（または`MCMC4QEC_RESEARCH`）に読み取り専用の研究checkoutを設定し、どちらも設定しなければライブラリ側だけを測ります。
`codes`と`matching` extrasが必要で、`--quick`と`--out`を指定でき、既定では一時ディレクトリにCSVを書きます。
速度は機器と負荷で変動し、混合や推定精度を保証しません。

## 目的別の入口

| 目的 | 最初の資料 |
| --- | --- |
| 絶対 `P_L` を推定する | [Steane の exact・MC・BAR 比較](examples/steane_exact.py)、[toric の BAR 曲線](examples/workflows/pl_curve.py)、[BAR notebook](notebooks/02_pl_curve_with_bar.ipynb) |
| 失敗条件付き分布を調べる | [条件付き重みの比較](examples/workflows/conditional_weight.py)、[複数 chain の診断](examples/workflows/convergence_check.py)、[診断 notebook](notebooks/03_conditional_sampling_and_diagnostics.ipynb) |
| 自分の符号、ノイズ、デコーダーを持ち込む | [CSS 雛形](examples/templates/byo_css_bitflip.py)、[ノイズ雛形](examples/templates/byo_noise.py)、[デコーダー雛形](examples/templates/byo_decoder.py)、[持ち込み notebook](notebooks/04_bring_your_own.ipynb) |
| detector または物理回路 fault を扱う | [Stim DEM 雛形](examples/templates/byo_stim_dem.py)、[DEM 例](examples/stim_dem.py)、[物理回路 baseline](examples/circuit_baseline.py) |

最初に手順を追う場合は [quickstart notebook](notebooks/01_quickstart.ipynb) を開いてください。
[実行例一覧](examples/README.md) には全スクリプトと notebook の依存、出力の読み方を載せています。
部品の契約は [API 文書](docs/api_en.md) と [持ち込みチュートリアル](docs/tutorial_en.md) を参照してください。

| ノイズと状態 | OBF / Z / H | stabilizer flip | デコーダー接続 |
| --- | --- | --- | --- |
| 静的 CSS bit-flip | 対応 | 任意 | PyMatching または決定的な自作デコーダー、`DecoderAdapter` 経由の BP-OSD |
| 静的 CSS phase-flip | 対応 | 任意 | `errors="Z"` の PyMatching・BP-OSD が `hx`/`lx` を使用 |
| 静的 CSS depolarising | 結合した I/X/Y/Z ラベルで対応 | 任意 | 完全な論理予測が必要で、sector 合成はデコーダー側の選択 |
| データと測定の phenomenological fault | 対応 | 非対応 | 選択した syndrome history または difference 表現を受け取るデコーダー |
| Stim detector error model | 潜在 mechanism bit 上で対応 | 非対応 | graphlike DEM に対する matching、または自作デコーダー |
| 物理 Stim 回路 location | OBF・Z・物理単一 fault カーネルに対応、H は非対応 | 非対応 | PyMatching を用いる中点 surface logical-idle baseline |

`exact` は小さいカテゴリ状態空間を列挙し、`direct_mc` は試行数を固定した MC を実行します。
`sample_faulty` は失敗条件付き分布をサンプリングし、`estimate_logical_error` は anchor と隣接 rung の BAR 比を使います。

符号ファクトリには toric、surface、asymmetric toric、Hamming HGP、BB72/108/144、Steane、連接 Steane があります。
現行の toric、surface、asymmetric toric、Hamming HGP、BB のファクトリには `codes` extra が必要です。
デコーダー構築関数は bit-flip と phase-flip（`errors="Z"`）の MWPM・BP-OSD、および depolarising ノイズに対する明示的な sector 復号を扱います。
`SamplingConfig(cache_cap=..., cache_policy=...)` は決定的な復号結果の cache を制限し、`KernelConfig(zanella_fastpath=True)` は該当する product-noise の経路を使います。
診断には複数 chain の要約、exact CSS coset 初期化補助、4 条件の `evaluate_convergence` があります。
完全な判定には独立な直接 MC による条件付き分散が必要で、判定が良くても混合や正しさは証明されません。

物理回路 baseline は対応する Stim noise location の排他的な fault label をサンプリングします。
物理単一 fault には `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)`、Z+OBF には `KernelConfig(zanella=0.7, single=0.3, cluster=0, stabilizer=0)` を選びます。
この3種の混合に対応し、H と stabilizer は非対応のため、既定の Z+H カーネルは使えません。
surface logical-idle 例は 2d 回の noisy round の最初の d 回の後の中点 observable を評価します。
DEM はデコーダー構築に使い、サンプリングは物理 location 上で行います。
詳しくは [物理回路 baseline](examples/circuit_baseline.py) と [カーネルの比較](examples/circuit_zanella.py) を参照してください。

ESS や split R-hat などの診断は収束、エルゴード性、正しさの証明にはなりません。
重み trace が健全に見えても chain が閉じ込められることがあります。
`p_dependent_decoder_approx` の BAR mode は failure 集合の変化を明示的に無視し、その区間にこの bias は含まれません。
モデルの support と初期化の限界、観測 overlap、有限標本、block 長も推定を制限します。
DEM サンプリングはすべての物理回路ノイズモデルとの同等性を示しません。
回路 baseline は公開図表の再現を示すものではありません。

関連論文は in preparation です。
ソフトウェア引用情報の著者名 `junichi haruna` は所有者の指定で確定していますが、所属、DOI、公開日、公開の詳細は未確定です。
[CITATION.cff](CITATION.cff) と [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。
コードは [MIT License](LICENSE) で配布しますが、このリポジトリは公開パッケージとして publish されていません。
