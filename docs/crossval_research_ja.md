# 研究コードとの数値照合（2026-09-30）

研究リポジトリ `C:/dev/RIMC` の参照 commit は `69efcfcc86af3bf24ca977a098dab0f348601aff` であり、読み取り専用で使用した。
研究側を import するコマンドでは `PYTHONDONTWRITEBYTECODE=1` を設定し、研究側の `git status --porcelain=v1` は出力なしだった。
以下の実測は Python 3.11.9、NumPy 2.4.6、PyMatching 2.4.0、ldpc 2.4.1、bposd 2.1 で行った。

## 再実行手順と保存範囲

`docs/wp/A_reproduce.py` に以下の Problem 構築、seed、試行数、初期状態、統計式を固定した。
研究 decoder の直接比較は `RIMC_RESEARCH_ROOT` に読み取り専用 checkout のパスを指定した `tests/test_crossval_research.py` でも実行でき、環境変数がない通常 suite では skip する。
次のコマンドはリポジトリ直下の PowerShell で指定 Python 3.11 を使う例である。

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:RIMC_RESEARCH_ROOT = 'C:\dev\RIMC'
& 'C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe' -m pytest tests/test_crossval_research.py -q
& 'C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe' docs/wp/A_reproduce.py decoders --research-root C:\dev\RIMC
& 'C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe' docs/wp/A_reproduce.py exact --research-root C:\dev\RIMC --output output/wp-a/exact.json
& 'C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe' docs/wp/A_reproduce.py direct --code toric5 --output output/wp-a/direct-toric5.json
& 'C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe' docs/wp/A_reproduce.py direct --code bb72 --output output/wp-a/direct-bb72.json
& 'C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe' docs/wp/A_reproduce.py zh --code toric5 --output output/wp-a/zh-toric5.json
& 'C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe' docs/wp/A_reproduce.py zh --code bb72 --output output/wp-a/zh-bb72.json
```

`--output` は指定時だけ全 `Result` JSON を保存し、その際は実在する研究 checkout の指定を必須とし、その内部への出力を拒否する。
中断前の元実行では全 `Result` JSON を保存していないため、下記の数値表は実行ログの要約であり生結果の再読取値ではない。
再現スクリプトの `decoders` と `direct --code bb72 --smoke`、`zh --code toric5 --smoke` は追加後に軽量動作確認したが、長い exact、100000 trial direct MC、3000標本 Z+H の再実行は行っていない。
`exact` は `code.bit_flip_model()`、`IndependentBitFlip(code.n)`、`mwpm_decoder(code)` を `Problem` に組み込み、`p=0.01` の全状態を列挙する。
`direct` は toric d=5 で MWPM、BB72 で prior `p=0.01` の研究既定 BP-OSD を使い、固定 seed 20260930 の100000試行を行う。
`zh` は同じ Problem で Z 0.7、H 0.3、`cluster_k=2`、`lazy=0.05`、burn-in 500、保存3000、thin 1、1 chain とし、toric では `lx[0]`、BB72 では最小重みの `lx` 行を初期状態にする。
`zh` の参考区間は保存状態の Hamming 重みの標本標準偏差を診断 ESS の平方根で割り、平均から ±1.96 倍した値である。

## 符号行列

研究側の `css_code.py` と `subset_sampling.py` のファクトリを実行し、各 `hx/hz/lx/lz` の shape と連続した raw bytes を SHA-256 で固定した。
`tests/test_crossval_research.py` の 12 構成すべてで同じ digest を得て、4 行列の各要素と行順が一致した。
研究側は `int8`、ライブラリは `uint8` であり、二値要素の raw bytes は一致するが dtype は一致しない。

| 構成 | n | k | d の根拠 | 行列 bytes |
| --- | ---: | ---: | --- | --- |
| toric d=2,3,5 | 8,18,50 | 各2 | d=2,3 は X/Z の小重み列挙、d=5 は研究ラベル | 一致 |
| surface d=2,3 | 5,13 | 各1 | X/Z の小重み列挙 | 一致 |
| asymmetric toric (3,5) | 30 | 2 | X 側のみ重み3未満を列挙、Z 側は未証明 | 一致 |
| HGP Hamming | 58 | 16 | 重み3の X 論理代表を確認、下界は未証明 | 一致 |
| BB72 | 72 | 12 | 重み6の X 論理代表を確認、下界は未証明 | 一致 |
| BB108 | 108 | 8 | 研究ラベルは10、確認した X 論理行の最小重みは12、距離10は未証明 | 一致 |
| BB144 | 144 | 12 | 重み12の X 論理代表を確認、下界は未証明 | 一致 |
| Steane | 7 | 1 | X 側の重み3未満を列挙、自己双対性から Z 側も同じ | 一致 |
| concatenated Steane level 2 | 49 | 1 | 重み9の X 論理代表を確認、下界は未証明 | 一致 |

全構成で `n-rank(hx)-rank(hz)=k`、`hx @ hz.T=0`、論理行列の交差行列が GF(2) 可逆であることを確認した。
HGP Hamming と BB72/108/144 の交差行列は単位行列ではないため、ファクトリは明示的な `logical_basis="independent"` を使い、行列を変換しない。

## Decoder の全 syndrome 照合

toric d=3 で実現可能な 256 個の syndrome に対して研究側 `make_mwpm_decoder`、`make_bposd_decoder`、`make_depolarizing_mwpm_decoder`、`make_depolarizing_bposd_decoder` を直接呼んだ。
depolarising 用二種の直接比較では同じ syndrome を X/Z 両 sector に与え、独立 sector のテストでは各 sector の全 syndrome を別々に照合した。
物理補正を同じ `lz` または `lx` に掛けた論理予測とライブラリの返値を比べ、直接比較した各四種の不一致は 0/256 件だった。
BP-OSD の prior は `p=0.05`、`max_iter=100`、`bp_method="min_sum"`、`osd_method="osd_cs"`、`osd_order=10` とした。
toric d=3 の研究 syndrome table の 256 行との MWPM 論理予測不一致も 0 件だった。
PyMatching は列次数が2を超える HGP/BB の check matrix をそのまま受け取れないため、MWPM wrapper は明示的に拒否する。
ldpc 2.4.1 は Windows 上で Steane 等の nullity より大きい `osd_order=10` を与えると native heap crash を起こしたため、wrapper はその入力を ValueError にする。

## exact と direct MC

toric d=3 の exact は `mcmc4qec.sampling.exact` を全 `2^18` 状態に適用し、研究 `compare/exact_ew.py` の同じ syndrome table と失敗条件で比較した。

| p | 方法 | P_L | E[w\|faulty] | 実行時間 |
| ---: | --- | ---: | ---: | ---: |
| 0.01 | ライブラリ exact | 0.0020442815656133238 | 2.261042002778366 | 44.19 秒 |
| 0.01 | 研究 exact_ew_d3 | 0.0020442815655904952 | 2.2610420028036122 | この比較では未計測 |

差は `P_L` が約 2.28e-14、条件付き平均が約 2.52e-11 で、浮動小数の集計順序による範囲である。
direct MC は `mcmc4qec.direct_mc` を固定試行数 100000、seed 20260930、p=0.01 で実行した。
CSV は `cluster_results/direct_mc_ew.csv` の該当二行を参照し、独立な大規模実行結果を再生成したとは主張しない。

| 符号と decoder | 研究 CSV P_L / E[w\|F] | ライブラリ失敗数 / P_L | ライブラリ 95% Wilson 区間 | ライブラリ E[w\|F] | 秒 | 判定 |
| --- | --- | --- | --- | ---: | ---: | --- |
| toric d=5 / MWPM | 0.0001419507468 / 3.784 | 14 / 0.00014 | [0.0000834003, 0.0002350020] | 4.0000 | 21.95 | CSV P_L は区間内、平均差は失敗14件の標本誤差と両立 |
| BB72 / BP-OSD | 0.0018106462377 / 3.706 | 166 / 0.00166 | [0.0014261085, 0.0019321771] | 3.74699 | 23.52 | CSV P_L は区間内、平均差は失敗166件の標本誤差と両立 |

条件付き平均の比較では CSV の分散推定値 `vw=0.694038` と `0.648888` を使用すると、ライブラリ側の参考標準誤差はそれぞれ約 0.223 と 0.0625 である。
この参考標準誤差は CSV 分散を代入したもので、ライブラリ試料から独立に推定した値ではない。

## Z+H と direct MC の比較

両符号とも `p=0.01`、Z 0.7、H 0.3、`cluster_k=2`、1 chain、burn-in 500、保存 3000、seed 20260930、既定 `lazy=0.05` とした。
初期状態は toric d=5 で `lx[0]`、BB72 で `lx` の最小重み行を seed を見ずに選んだ。
各区間は標本分散を診断の IAT から計算した ESS で割る参考的な正規近似であり、厳密な被覆確率や混合の証明ではない。

| 符号 | Z+H E[w\|F] | 参考95%区間 | ESS | 秒 | 研究 CSV E[w\|F] | CSV 値が区間内か |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| toric d=5 | 3.77733 | [3.55680, 3.99787] | 52.60 | 15.21 | 3.784 | はい |
| BB72 | 3.57433 | [3.38725, 3.76142] | 65.56 | 18.74 | 3.706 | はい |

toric d=5 ではノイズからの初期化を 10000 回試みて失敗したため、事前に定めた論理行を明示的な初期状態として再実行した。
短い単一 chain の区間が参照値を含むことは、収束、エルゴード性、正しさの証明にならない。

## 研究テストの意味論対応

指定された研究テスト八ファイルの `test_` 関数は合計 102 件である。
WP-A の新規受入テストは 58 parameterized case であり、Phase 0 の14 case を加えた担当三ファイルの収集数は72件だった。
研究 runner の旧既定、PT/hot replica、CSV 後処理と新 API の契約が異なるため、102 件を名前だけ置換して全移植したとは扱わない。

| 研究ファイル | 元件数 | 新 API で検証した意味論 | 移植不能または残る範囲 |
| --- | ---: | --- | --- |
| `test_css_code.py` | 13 | `tests/test_codes.py` の形状・可換性・距離、`tests/test_decoders.py` の全 syndrome・sector 判定 | 研究 `int8` とライブラリ `uint8` の dtype 同一試験は非移植、plain BP decoder は WP-A の公開範囲外 |
| `test_balancing.py` | 4 | `tests/test_categorical_kernels.py` と `tests/test_acceptance.py` の sqrt 提案正規化・詳細釣合い | Barker balancing は新 API 未対応、30000 step 混合経験試験は非移植 |
| `test_depolarizing_cluster.py` | 6 | `tests/test_categorical_kernels.py` の Pauli 提案確率・詳細釣合いと `tests/test_pipeline.py` の direct MC 対照 | 研究 runner の返値構造に依存する試験は非移植 |
| `test_rimc_mixed.py` | 27 | `tests/test_acceptance.py` と `tests/test_independent.py` の混合確率、軌道、拒否保存、cluster 不変量 | 旧 Z+PT 既定、replica 交換、hot replica、返値構造は新 API の対象外 |
| `test_splitting_pl.py` | 6 | `tests/test_crossval_research.py` に同じ合成 weight trace で研究 BAR 値を移植し、`tests/test_estimation.py` で ladder と anchor を検証 | 百万標本の経験試験は軽量制約により非移植 |
| `test_metrics.py` | 8 | `tests/test_acceptance.py` の IAT/ESS 利用と `tests/test_estimation.py` の不確かさを確認 | `running_mean` と `doubling_converged` は現 API 未対応、WP-E の対象 |
| `test_diagnostics.py` | 8 | `tests/test_acceptance.py` の定数 chain・R-hat 未定義警告を確認 | 研究の独立 `split_rhat` API と値の完全移植は WP-E の対象 |
| `test_postprocess.py` | 30 | `tests/test_independent.py` の棄却を含む trace と `tests/test_estimation.py` の block bootstrap を確認 | 自動 burn-in、後処理 thin、cross-chain SE は現 API 未対応、WP-E の対象 |

研究と同じ合成 trace の BAR log ratio は研究 `-1.2130084485394683`、ライブラリ `-1.213008448539711` で、差は約 2.43e-13 だった。
