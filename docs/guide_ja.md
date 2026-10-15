# 目的別ガイド

[English](guide_en.md) · [チュートリアル](tutorial_ja.md)

まず、求めたい量と、状態が表す実験を決めます。
同じ符号距離でも、1 ラウンドの論理誤り率、有限回の測定を含む実験の失敗確率、物理回路全体の失敗確率は別の量です。
ここでは目的に応じて、実行例と API の前提を説明した文書を案内します。

## 確率を求める・失敗の性質を調べる

| 目的 | 手法 | 最初に試す例 |
| --- | --- | --- |
| 小さなモデルを全状態で検証する | `exact` | [Steane 符号の全列挙](../examples/steane_exact.py) |
| 決めた試行数で失敗を観測できる領域の確率を求める | `direct_mc` | [ビット反転での比較](../examples/bit_flip.py) |
| 復号に失敗したときの典型的な誤りを調べる | `sample_faulty` | [条件付き重み](../examples/workflows/conditional_weight.py) |
| ノイズ強度の列を使い、よりまれな失敗の確率を求める | `estimate_logical_error` | [BAR による曲線](../examples/workflows/pl_curve.py) |

自作モデルを大きくする前に、小さな場合を全列挙で検証してください。
失敗が十分に観測できる領域では、独立な直接モンテカルロ計算とも比較できます。
失敗した状態だけから絶対的な失敗確率は決まらず、BAR には隣り合う点の確率比に加えて基準確率が必要です。
この関係は[チュートリアル](tutorial_ja.md)で説明します。

## 実験と追加パッケージを選ぶ

追加パッケージは、リポジトリのルートで `python -m pip install -e ".[codes,matching]"` のように指定します。
基本インストールには NumPy が含まれ、小さな自作モデルの例を実行できます。

| 実験 | モデルとノイズ | 実行例 | 追加パッケージ |
| --- | --- | --- | --- |
| CSS 符号の X 誤り | `code.bit_flip_model()`、`IndependentBitFlip` | [toric 符号のビット反転](../examples/toric_pymatching.py) | `codes,matching` |
| CSS 符号の Z 誤り | `code.phase_flip_model()`、`IndependentBitFlip` | [X/Z の比較](../examples/phase_flip_asymmetric.py) | `codes,matching` |
| Pauli 誤りの同時分布 | `DepolarizingModel`、`DepolarizingNoise` | [toric 符号の脱分極ノイズ](../examples/toric_depolarizing.py) | `codes,matching` |
| データ誤りと測定誤り | `PhenomenologicalModel`、`PhenomenologicalNoise` | [繰り返し測定](../examples/phenomenological_toric.py) | `codes,matching` |
| 潜在的な検出器誤り機構 | `from_stim_dem` または `from_stim_circuit` | [Stim DEM](../examples/stim_dem.py) | `stim` |
| 物理回路の各 location の fault | `CircuitFaultModel`、`CircuitFaultNoise` | [回路の基準例](../examples/circuit_baseline.py) | `stim,matching` |
| 固定事前分布のデコーダーを使う BB 符号 | 符号ファクトリ、ビット反転モデル、BP-OSD | [BB72](../examples/bb72_bposd.py) | `codes` |

Pauli ノイズでは、デコーダーが X と Z を別々に処理する場合も、Y 誤りに由来する両成分の相関を保ってサンプリングします。
phenomenological モデルの結果は、設定した実験全体の確率であり、1 ラウンド当たりの率ではありません。
Stim DEM の状態は潜在的な誤り機構を表し、物理回路の状態は各 location で排他的に選ばれる fault の種類を表します。
確率を比較する前に、実験に合う状態表現を選んでください。

## 誤差と混合を調べる

最初に結果の警告、基準確率の計算方法、サンプリング設定を確認します。
次に連鎖の挙動を比べ、実行長・初期状態・ブロック長を変えたときの感度を調べます。
通常の BAR では、ノイズ強度の列全体で失敗条件とデコーダーを固定します。

| 確認する内容 | 参照先 | 分かること |
| --- | --- | --- |
| 絶対確率の誤差 | MC の `interval`、BAR の `intervals` と `log_standard_errors` | 確率推定量の標本誤差 |
| 条件付き平均の誤差 | `conditional_weight_standard_error` | 失敗時の非恒等座標数の平均に対する MCSE |
| ACF・IAT・ESS・split R-hat | `diagnostics=True` または `DiagnosticsConfig` | 指定した観測量で見える相関や連鎖間の不一致 |
| ブロック長への感度 | 詳細な `trace_analysis` レポート | 観測量平均の誤差がブロック長によりどう変わるか |
| 異なる初期状態群からの比較 | [収束確認の例](../examples/workflows/convergence_check.py) | 初期状態間の不一致や、判定に不足している情報 |

診断出力の読み方は[チュートリアル](tutorial_ja.md)で説明します。
統計量の式と、BAR と観測量のブートストラップ計算の違いは [API 文書](api_en.md#default-statistical-errors-and-optional-detailed-diagnostics)を参照してください。
良好な診断値だけで収束や名目通りの区間被覆は保証できず、全連鎖に共通する偏りはブロックブートストラップでも連鎖間の変動でも検出できない場合があります。

## 自分の構成要素を使う

一度に一つずつ置き換え、全列挙できる有限状態の例で検証します。
テンプレートには編集箇所とサンプリング前の確認処理があります。

| 構成要素 | 確認する契約 | テンプレート |
| --- | --- | --- |
| CSS 行列 | 二値性・次元・可換性・論理基底の対応 | [CSS 符号のビット反転](../examples/templates/byo_css_bitflip.py) |
| ノイズ分布 | 全状態上で正規化された `log_prob` と、同じ分布のサンプラー | [独自ノイズ](../examples/templates/byo_noise.py) |
| デコーダー | 決定論的な出力と、訂正パターンか論理観測量かの明示 | [独自デコーダー](../examples/templates/byo_decoder.py) |
| Stim 回路から変換した DEM | 誤り機構の台と論理観測量への対応 | [Stim DEM の接続](../examples/templates/byo_stim_dem.py) |

[自作 CSS 符号のチュートリアル](tutorial_ja.md#自分の-css-行列を使う)では、これらの契約を小さな例で確認します。
ノイズ強度によってデコーダーの事前分布を変える場合は、近似 BAR モードを選ぶ前に [p 依存デコーダーの例](../examples/workflows/p_dependent_decoder.py)を参照してください。
その誤差区間には、失敗集合が変わることによる偏りは含まれません。

## 一通り動く実行例を試す

リポジトリのルートで、まず短い設定を試せます。

```sh
python examples/steane_exact.py --quick --seed 7 --out output/steane
```

各実行例は `--quick`、`--seed`、`--out` を受け取り、最後に `SUMMARY` から始まる JSON を出力します。
[実行例一覧](../examples/README.md)に、各出力の意味、追加依存、実測時間をまとめています。
`--quick` で処理の流れを確認した後、調べたい問題に合わせて試行数や実行長を決め、妥当性を検証してください。
