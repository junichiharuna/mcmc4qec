# チュートリアル：最初の推定から独自モデルの導入まで

[README](../README_ja.md) · [English](tutorial_en.md) · [API リファレンス](api_en.md)

README の toric 符号の例を実行し、符号の中身と推定結果を確認します。
続いてサンプリングや診断の設定を調整し、最後に自分の符号・ノイズ・デコーダーに置き換えます。
最初の例には `codes` と `matching` の追加パッケージが必要です。
後半の小さなモデルを自分で定義する例は、追加パッケージなしで実行できます。
各 Python コードブロックは単独で実行できます。

## toric 符号の論理誤り率を推定する

リポジトリのディレクトリで、符号の生成と PyMatching に必要なパッケージをまとめてインストールします。

```sh
python -m pip install -e ".[codes,matching]"
```

この例では、距離 3 の toric 符号に独立なビット反転が生じたときの論理誤り率を、MWPM デコーダーを使って推定します。
物理的なビット反転率を `0.2 → 0.15 → 0.1` とたどり、それぞれの推定値と誤差区間を表示します。

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

出力の各行は、物理的なビット反転率 `p`、論理誤り率の推定値 `P_L`、その誤差区間を表します。
この設定は、まず動作を試すためのものです。
研究に使う際は、サンプル数と診断結果を確認し、設定を調整してください。

## 例の構成を理解する

### 符号・ノイズ・デコーダー

`make_toric_code(3)` が返す `code` には、符号を定義する行列が入っています。
この例で使う属性は次のとおりです。

| 属性 | 意味 | この例での値・形状 |
| --- | --- | --- |
| `code.n` | 物理量子ビット数 | `18` |
| `code.hx`, `code.hz` | X と Z の検査行列 | それぞれ `(9, 18)` |
| `code.lx`, `code.lz` | X と Z の論理演算子行列 | それぞれ `(2, 18)` |

`code.bit_flip_model()` は、ビット反転誤りをシンドロームと論理観測量へ写すモデルを、それぞれ `hz` と `lz` を使って構築します。
`noise` は誤りの分布を与え、`decoder` はシンドロームから論理観測量を予測します。
`Problem` はモデル・ノイズ・デコーダーを組み合わせ、予測した論理観測量と実際の値が一致するかどうかで復号の成否を判定します。
自分の行列やデコーダーを定義するには、[自分の CSS 行列を使う](#自分の-css-行列を使う)を参照してください。

### ノイズ強度の列と基準値

`ladder` は推定に使うノイズ強度の列です。
この例では、まず `p=0.2` の論理誤り率を基準値（**anchor**）として求めます。
続いて BAR が隣り合うノイズ強度の間の確率比を推定し、`p=0.15` と `p=0.1` の推定値を求めます。

anchor は、状態空間が小さければ全列挙、それ以外では直接モンテカルロ法で計算します。
別に計算した基準値を使う場合は、`anchor` に渡します。
サンプル数などの設定は `config` で調整でき、同じ設定で再現するには `seed=73` のように整数を指定します。
いずれの引数も省略できます。
既定値と設定方法は、[API の設定例](api_en.md#automatic-bar-anchor)を参照してください。

## 既定設定で BAR を使う

`config` や `anchor` の指定は必須ではありません。
既定の `SamplingConfig()` では、各ラダー段で burn-in を 100 ステップ行った後に 1,000 サンプルを保存します。
連鎖は 1 本、間引き間隔（thinning）は 1、Z/H の重みは 0.7/0.3、`cluster_k=2`、状態をそのまま保持する確率（lazy）は 0.05 です。
設定を調整するには `SamplingConfig` を渡してください。
これらの既定値は研究に必要な精度を保証せず、物理回路モデルでは適切なカーネル設定も必要です。

最初の段の anchor は、各座標のアルファベットサイズの積が 4,096 以下なら全列挙で、それ以外なら試行回数を 10,000 回に固定した直接 MC で計算します。
たとえば `qec.estimate_logical_error(problem, ladder, anchor_max_states=0, anchor_trials=20000, seed=73)` とすると、20,000 試行の MC anchor を使います。
anchor 用の独立した乱数生成器と不確かさは記録され、不確かさは結果に伝播します。
小さな問題なら代わりに `anchor=qec.exact(problem, ladder[0])` を渡せますし、互換性のある独立な `qec.direct_mc` の結果を使うこともできます。

MC anchor の失敗数がゼロ、または全試行が失敗した場合は `ValueError` になります。
試行回数を増やすか、最初のノイズ強度を変えるか、有効な anchor を指定してください。
自動計算では、失敗が現れるまで試行回数を延長することはありません。
区間を解釈する前に、警告と `result.metadata["anchor"]` を確認し、混合と設定への感度を調べてください。
検証条件と計算設定の記録は、[anchor の自動計算の設定](api_en.md#automatic-bar-anchor)を参照してください。

サンプリング量を変えるには、たとえば上の toric の呼び出しに `config=qec.SamplingConfig(samples=2000, burn_in=200, chains=4)` を渡します。
この数値は設定方法を示す例であり、十分な実行長を示すものではありません。
実行長と初期状態を変えて結果を比較し、以下の診断も確認してください。

## 推定値と統計誤差を読む

統計誤差は、追加の設定をしなくても推定値と一緒に返されます。
BAR の例では、`result.estimates` と `result.intervals` は `ladder` と同じ順序です。

| 手法 | 推定値 | 統計誤差 |
| --- | --- | --- |
| 直接 MC | `estimate` | 95% Wilson 区間 `interval` |
| BAR | `estimates` | 各ノイズ強度の `intervals` と `log_standard_errors` |
| 失敗条件付き MCMC | `conditional_weight` | `conditional_weight_standard_error`：自己相関を考慮した平均重みの標準誤差 |

BAR は既定でブロック・ブートストラップ を使います。
独立した連鎖 が 2 本以上ある場合は、`uncertainty="cross_chain"` により、連鎖間の変動から不確かさを推定できます。
求められない誤差はゼロではなく `None` です。

標準の BAR では、ラダー全体で同じデコーダーと失敗定義を使い、正の anchor と、隣接する分布間で観測された重なりを必要とします。
必要な重なりが観測されなければ `OverlapError` になります。
`p_dependent_decoder_approx` モードは失敗集合の変化を無視し、誤差区間にもそのバイアスを含めません。
使う前に [API リファレンス](api_en.md)を確認してください。

## 初期化・キャッシュ・診断

短い実行で診断を確認できるよう、次の例では単純な失敗条件を持つ 2 ビットのモデルを使います。
`sample_faulty` は失敗を条件とした分布からサンプリングするため、その頻度だけでは絶対的な論理誤り率を求められません。

統計誤差は、推定値と一緒に返されます。
条件付き MCMC は、重みの平均と、積分自己相関時間（IAT）に基づくモンテカルロ標準誤差（MCSE）を返します。
診断には、有効サンプルサイズ（ESS）や Gelman–Rubin 統計量（古典的な split R-hat）も含まれます。
自己相関関数（ACF）の配列、ブロッキング法、ブートストラップ法の結果を追加するには `diagnostics=True` を使い、計算量を制限するには `DiagnosticsConfig` を渡します。

```python
from mcmc4qec import (BinaryLinearModel, CallableDecoder, DiagnosticsConfig,
                      IndependentBitFlip, KernelConfig, Problem, SamplingConfig,
                      diagnostic_report, sample_faulty)

# Failure is x[0] == 1; x[1] remains a variable conditional observable.
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
print("ACF:", report["acf"])
print("Batch-mean SE scan:", report["blocking"])
print("Bootstrap mean intervals:", report["bootstrap"]["blocks"])

# Alternative observables can be analyzed afterwards without resampling.
last_bit = diagnostic_report(run, observable=lambda state: float(state[-1]),
    observable_name="last bit", config=DiagnosticsConfig(bootstrap_replicates=0))
print("Last-bit mean and MCSE:", last_bit["mean"], last_bit["iat_mcse"])
```

`diagnostics` を省略すると追加の解析を省きますが、重み平均の MCSE は返されます。
BAR では、同じキーワードにより各段のレポートが `result.diagnostics[i]["trace_analysis"]` に追加されます。
これは条件付き観測量の誤差であり、論理誤り率の誤差は引き続き `result.intervals` と `result.log_standard_errors` に入ります。
詳細解析には専用の乱数生成器を使うため、サンプリングした状態や BAR の不確かさには影響しません。
`None` は利用できないことを表し、誤差ゼロを意味しません。
区間を解釈する前に、ブロック長への感度、短い連鎖や観測量が一定の連鎖、警告を確認してください。
詳細は [API の数式とフィールド](api_en.md#default-statistical-errors-and-optional-detailed-diagnostics)を参照してください。

`minimum_weight_initial_state(code)` と `maximum_weight_initial_state(code)` は、符号の論理基底の剰余類（coset） の最小重み代表から状態を選びます。
`observable_sector_initial_state(code, bits)` は、論理基底が独立な場合でも特定の非ゼロ観測量セクターを指定でき、`random_logical_sector_initial_state(code, seed=...)` は非ゼロセクターを選びます。
これらは初期状態の候補です。
`sample_faulty` の `initial_state` に渡す前に、その状態がノイズモデルで正の確率を持ち、実際に使うデコーダーと判定関数で失敗することを確認してください。
スタビライザーのランクが大きい場合は SciPy MILP を使い、`time_limit` 内に最適性が証明される必要があります。

復号を繰り返す場合、`SamplingConfig(cache_cap=1000, cache_policy="lru")` は厳密な LRU キャッシュを適用します。
`"freeze"` は上限に達すると追加を止め、`"research_clear"` は 10 ステップごとにソフト上限を確認します。
`KernelConfig(zanella_fastpath=True)` は、対応する独立なノイズの目標分布を変えずに高速化します。
`diagnose` は複数の連鎖 を要約できますが、重み系列が一見良好でも、混合の十分な証拠にはなりません。
`evaluate_convergence` は、連鎖の長さを変えたときの挙動、後半の定常性、異なる初期状態の集団、独立な直接 MC で推定した**条件付き観測量の分散**と IAT の関係を確認します。
その分散や 2 つ目の初期状態の集団がなければ、対応する確認項目は未解決のままです。

ESS や R-hat が良好でも、収束・エルゴード性・正しさ・区間の名目被覆率を証明するものではありません。
ブロック・ブートストラップ も cross-chain による不確かさも、混合が不十分な連鎖 に共通するバイアスは捉えられません。
[BAR の感度調査](bar_sensitivity_ja.md)には、短い実験で見つかった制約を記録しています。

## 自分の CSS 行列を使う

以下の例では、有限の状態空間と決定論的な失敗定義を保ちながら、`Problem` の構成要素を個別に置き換えます。
サンプリング前に全列挙で結果を確認できるよう、小さなモデルを使います。

同じ列数を持つ二値行列 `hx`、`hz`、`lx`、`lz` を指定します。
既定では、論理演算子の行は完全な対をなす基底である必要があります。
つまり、GF(2) 上で `hx @ hz.T = 0`、スタビライザーと論理演算子の交換子はゼロ、`lx @ lz.T` は単位行列です。
論理基底を意図的に独立な順序で使う場合は `logical_basis="independent"` を指定してください。
この場合、基底間のペアリング行列は可逆である必要があり、入力した行の基底は変換されません。
`CSSCode` はこれらの条件を検証し、満たさない場合は `ValueError` を送出します。
ビット反転モデルでは、`hz` が X 誤りを測定し、`lz` が論理観測量へ写します。

```python
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, IndependentBitFlip, Problem, exact

code = CSSCode(hx=np.zeros((0, 3), dtype=int),
               hz=[[1, 1, 0], [0, 1, 1]],
               lx=[[1, 1, 1]], lz=[[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="my-repetition3-logical-decoder-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
print(exact(problem, 0.25).estimate)  # 0.15625
```

`CallableDecoder` は物理量子ビット上の訂正パターンではなく、予測した**論理観測量**を返します。
標準の BAR ラダーでは、同じデコーダーと失敗判定関数を使ってください。

## 静的 CSS 符号の位相反転

二値の Z 誤りを扱う `code.phase_flip_model()` は、X 検査行列（`hx`）でシンドロームを測定し、`lx` で論理観測量を読み取り、Z スタビライザーの行（`hz`）を使います。
同じ `IndependentBitFlip(code.n)` が、Z 誤りに対する Bernoulli 積分布を表します。
たとえば、次の 3 量子ビット CSS 符号は X 誤りを訂正できますが、Z 誤りを検出する X 検査は持ちません。

```python
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, IndependentBitFlip, Problem, exact

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
z_decoder = CallableDecoder(lambda syndrome: [0], identifier="zero-z-v1")
problem = Problem(code.phase_flip_model(), IndependentBitFlip(code.n), z_decoder)
print(exact(problem, 0.25).estimate)  # 0.4375
```

追加パッケージの PyMatching を使う `mwpm_decoder(code, errors="Z")` は、`hx` からデコーダーを構築し、物理量子ビット上の訂正パターンを `lx` で写します。
`bposd_decoder(code, p, errors="Z", **kw)` も、固定した BP-OSD の事前分布で同じ写像を使います。
どちらも既定は `errors="X"` で、従来の `hz`/`lz` デコーダーを維持します。
toric 符号の形状が長方形であるだけでは、X/Z それぞれの総失敗率が異なるとはいえません。
可能なら全列挙で比較し、それ以外ではモンテカルロの不確かさを報告してください。
有限回の反復測定では、`PhenomenologicalModel(..., data_noise="phase_flip")` が二値の Z データ fault とノイズのある X 検査を使います。
その `PhenomenologicalNoise` には、実験全体に対する確率 `{"data": ..., "measurement": ...}` の明示的な指定が引き続き必要です。

## 自分のノイズモデルを定義する

独自のノイズオブジェクトは、`n`、対応する `alphabets`、`sample(p, rng)`、`log_prob(state, p)`、JSON 互換の `metadata()` を持ちます。
`log_prob` は、パラメーター `p` の下での**状態全体**の正規化された対数確率です。
確率がゼロになる状態では負の無限大を返してください。
`sample` も同じ分布から標本を生成する必要があります。
この例では、ラダーのパラメーターをスカラーのまま保ち、量子ビットごとに異なる 3 つのノイズ強度を使います。

```python
import math
import numpy as np
from mcmc4qec import CSSCode, CallableDecoder, Problem, exact

class UnequalBitFlip:
    n = 3
    alphabets = (2, 2, 2)
    scales = np.array([0.5, 1.0, 1.5])

    def sample(self, p, rng):
        rates = p * self.scales
        if np.any((rates < 0) | (rates > 1)):
            raise ValueError("rates must be in [0, 1]")
        return (rng.random(self.n) < rates).astype(np.uint8)

    def log_prob(self, state, p):
        rates = p * self.scales
        if np.any((rates < 0) | (rates > 1)):
            raise ValueError("rates must be in [0, 1]")
        state = np.asarray(state)
        if state.shape != (self.n,) or np.any((state != 0) & (state != 1)):
            raise ValueError("invalid state")
        probabilities = np.where(state, rates, 1 - rates)
        return float(np.log(probabilities).sum()) if np.all(probabilities > 0) else -math.inf

    def metadata(self):
        return {"identifier": "unequal-bit-flip-v1", "scales": self.scales.tolist()}

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
decoder = CallableDecoder(lambda s: [int(tuple(s) == (1, 0))],
                          identifier="my-repetition3-logical-decoder-v1")
print(exact(Problem(code.bit_flip_model(), UnequalBitFlip(), decoder), 0.25).estimate)
```

相関ノイズでは、状態の真の同時確率を計算してください。
独立な周辺分布で置き換えると、目標分布と BAR の確率比の両方が変わります。
サンプリング前に、小さな例を列挙して正規化を確認してください。

## 訂正パターンを返すデコーダーを使う

既存オブジェクトの `decode(syndrome)` は、論理観測量ではなく物理量子ビット上の訂正パターンを返す場合があります。
`output_kind="correction"` と宣言し、`logical_map`（`L`）を明示的に指定してください。
アダプターは `L @ correction % 2` を計算します。
以下の決定論的なテーブルは外部デコーダーの代わりであり、設定済みの BP-OSD オブジェクトに置き換えられます。

```python
import numpy as np
from mcmc4qec import CSSCode, IndependentBitFlip, Problem, exact
from mcmc4qec.adapters import DecoderAdapter

class CorrectionDecoder:
    corrections = {(0, 0): (0, 0, 0), (1, 0): (1, 0, 0),
                   (1, 1): (0, 1, 0), (0, 1): (0, 0, 1)}

    def decode(self, syndrome):
        return self.corrections[tuple(syndrome)]

code = CSSCode(np.zeros((0, 3), dtype=int), [[1, 1, 0], [0, 1, 1]],
               [[1, 1, 1]], [[1, 0, 0]])
adapter = DecoderAdapter(CorrectionDecoder(), output_kind="correction",
                         logical_map=code.lz, identifier="my-correction-decoder-v1")
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), adapter)
print(exact(problem, 0.25).estimate)  # 0.15625
```

論理観測量の予測を直接返すデコーダーでは、`output_kind="observable"` を使い、`logical_map` は省略します。
`settings` は来歴のために設定を記録しますが、ラップしたデコーダー自体を設定するものではありません。
実行中はデコーダーの振る舞いを固定してください。
反復測定のデコーダーは、選択した表現のシンドローム履歴全体、または差分表現全体を受け取る必要があります。
独自の失敗判定関数は `(state, predicted, truth)` を受け取り、真偽値を返す必要があります。
全列挙、直接 MC、条件付き MCMC は同じ判定関数を使います。
スタビライザー反転で判定結果が変わらないとは仮定しないでください。

## 組み込みの符号とデコーダー

HGP ベースのファクトリと PyMatching を使うには、`python -m pip install -e ".[codes,matching]"` でインストールします。
これらの符号にも、同じ `Problem` の契約が適用されます。

```python
from mcmc4qec import IndependentBitFlip, Problem, direct_mc
from mcmc4qec.codes import make_toric_code
from mcmc4qec.decoders import mwpm_decoder

code = make_toric_code(3)
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
print(direct_mc(problem, 0.1, trials=100, seed=3).estimate)
```

ほかにも toric、surface、asymmetric toric、Hamming HGP、BB72/108/144、連接 Steane のファクトリがあります。
一部は `logical_basis="independent"` により、独立に並べられた論理演算子の行を維持します。
`lx[i]` が観測量 `i` だけを反転すると仮定せず、与えられた基底として扱ってください。
`bposd_decoder(code, p, **kw)` は、構築時にチャネルの事前分布を固定します。
脱分極ノイズ用のセクターデコーダーの構築関数は、両方の論理セクターをモデルの順序で返します。
一方、`DepolarizingNoise` は、結合した I/X/Y/Z ラベルを通じて相関する X/Z 成分を引き続きサンプリングします。

## 物理回路の故障を扱う

`stim_noise_locations(circuit)` は、対応する 1 量子ビットおよび 2 量子ビットの Pauli ノイズのターゲット群を列挙します。
`CircuitFaultModel` は、選んだ各 location に、fault なし、またはいずれか 1 つの fault ラベルという排他的なカテゴリを割り当てます。
`CircuitFaultNoise` は明示的な location ごとの確率を使い、`uniform_fault_noise(model)` は一様な設定を簡単に作るための選択肢です。
回路に元から含まれるノイズ確率は物理的な尤度では無視され、指定する fault 確率と一致する必要はありません。
`surface_logical_idle_problem(distance=3, decoder_p=0.01, basis="Z")` は、2d ラウンドの rotated surface 符号に中間時点の観測量を設けた baseline を、PyMatching デコーダー付きで構築します。
DEM はそのデコーダーの構築に使いますが、サンプリングする状態は物理 location での選択のままです。
実行可能な直接 MC の例は `examples/circuit_baseline.py` を参照してください。

回路の条件付き MCMC は、`KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)` による物理的な単一 fault の移動と、`KernelConfig(zanella=0.7, single=0.3, cluster=0, stabilizer=0)` による Z+OBF、およびこれらの混合に対応します。
H には `circuit_groups` の明示的な指定が必要で、回路の stabilizer 移動には引き続き対応していません。
回路ビルダーは、決定論的な Clifford detector 回路上の指定された Pauli ノイズ命令に対応しますが、非 Pauli fault や location 間の相関は扱いません。
条件付き重み、受理率、IAT は[カーネルの比較](../examples/circuit_zanella.py)を参照してください。
これらの条件付きサンプルは、絶対的な `P_L` を推定するものではありません。

`circuit_groups` の各要素は、`model.locations` の location インデックスからなる空でない群です。
群は互いに素で、同じ群のすべての location はチャネルと順序付き fault アルファベットが同じでなければなりません。
アルファベットのサイズが同じだけでは不十分です。
location 1 と 2 がこの契約を満たす場合、`KernelConfig(single=.2, zanella=.4, circuit_single=.2, cluster=.2, cluster_k=1, circuit_groups=((1, 2),))` で 4 種類の移動を混合できます。
指定しなかった location は H では変わりません。
群は状態と独立に一様に選ばれ、実行できない再配置の分岐は自己ループとして残し、混合確率は再正規化しません。
H は群ごとの占有数を保存し、単独では一般に可約です。
ほかの移動と混合しても、それだけで任意の失敗集合の連結性が証明されるわけではありません。
この提案は、`mcmc4qec.circuit` の `PhysicalClusterExchange` としても利用できます。

`zanella_fastpath=True` の場合、組み込みクラスそのものの回路モデルとノイズの組に標準の失敗判定関数を使うと、物理的な detector/observable 効果テーブルを再利用し、変更された location だけを更新します。
独自のサブクラスや失敗判定関数では、汎用の処理経路を使います。
`python benchmarks/bench_circuit_step.py --steps 100 --compare-delta` は、共通の失敗状態から専用経路と汎用経路を比較し、保存した軌道と受理数を検証します。

DEM と物理回路のサンプリングは異なるノイズモデルを使っており、どちらの例も公表された回路の結果の再現を示すものではありません。
検証したケースと制約は、[回路の検証記録](circuit_baseline_ja.md)を参照してください。
