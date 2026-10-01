# WP-B 性能比較

2026-09-30 に Windows、Python 3.11.9、NumPy 2.4.6、PyMatching 2.4.0、ldpc 2.4.1 で実測した。
コマンドは `$env:PYTHONDONTWRITEBYTECODE='1'; %USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe benchmarks/bench_step.py --steps 10000` である。
研究側は `C:\dev\RIMC\src` を `sys.path` に加えて読み取り専用 import し、`run_rimc_mixed` を `p_zanella=0.7, p_cluster=0.3, cluster_k=2, n_replicas=1, steps_per_swap=10` で実行した。
ライブラリ側は `KernelConfig(zanella=0.7, cluster=0.3, cluster_k=2, lazy=0)` とし、両者とも p=0.01、開始状態 `lx[0]`、10000 ステップとした。
toric では双方 PyMatching を、BB72 では双方同じ引数の BP-OSD を使用した。
BB72 の研究 `lx/lz` は完全な対ではないため、ライブラリ側は同一の `hz/lz/hx` を `BinaryLinearModel` に渡し、研究側の failure 定義と揃えた。
時間にはデコーダー構築を含まず、ライブラリ側には `Result` 作成と診断が含まれる。

| 符号 | ライブラリ秒 | 研究秒 | ライブラリ step/s | 研究 step/s | 時間比 |
| --- | ---: | ---: | ---: | ---: | ---: |
| toric d=5 | 3.950001 | 0.221087 | 2531.6 | 45231.0 | 17.87 |
| toric d=7 | 5.091820 | 0.226044 | 1963.9 | 44239.2 | 22.53 |
| BB72 | 4.521356 | 0.700546 | 2211.7 | 14274.6 | 6.45 |

2 倍以内の受入目標は 3 符号とも未達である。
別の連続実行では順に時間比 17.57、15.65、5.95 だったため、短時間計測と同時実行負荷で数値は変動する。
`--steps 1000 --profile` の cProfile では toric d=5 のライブラリ実行 0.538 秒のうち、`Problem.state` の累積時間が 0.286 秒、`categorical` が 0.249 秒、Z の `propose` が 0.234 秒、Z の逆向き `probability` が 0.131 秒、`FailureEvaluator.evaluate` が 0.106 秒だった。
toric d=7 でも `Problem.state` が 0.300 秒、`categorical` が 0.263 秒で同じ傾向だった。
これらは呼び出し関係によって重複する累積時間なので合計しない。
研究 runner はビット状態・syndrome・weight を保持し、専用ステップで更新する一方、ライブラリの汎用経路は候補や確率の各評価で状態全体を繰り返し検証する。
次の改善は検証済み状態を内部で区別して再検証を省き、Z の順逆分布を同一の局所確率表から作り、線形 syndrome と observable を受理時に維持する専用経路を追加することである。
その際も全状態・全近傍の提案比、詳細釣合い、独自 failure の再評価と同一 seed 軌道を受入条件として維持する。

## WP-N 専用ステップの計測（2026-10-01）

Windows の Python 3.11 で `$env:PYTHONDONTWRITEBYTECODE='1'; %USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe benchmarks/bench_step.py --steps 10000` を実行した。
研究側 `A:/dev/RIMC/src` は読み取り専用で import し、開始状態、p=0.01、Z/H 比、cluster_k、decoder、cache 設定は上記と同じである。
`bench_step.py` の時間は decoder 構築を除き、ライブラリ側には診断と Result 構築が入る。

| 符号 | 専用経路 秒 | 研究 秒 | 専用経路 step/s | 研究 step/s | 時間比 |
| --- | ---: | ---: | ---: | ---: | ---: |
| toric d=5 | 1.546216 | 0.482388 | 6467.4 | 20730.2 | 3.21 |
| toric d=7 | 1.869962 | 0.755353 | 5347.7 | 13238.9 | 2.48 |
| BB72 | 2.867081 | 1.472265 | 3487.9 | 6792.3 | 1.95 |

BB72 は目標の 2 倍以内に入ったが、toric d=5 と d=7 は未達である。
前回の計測と PC 負荷や研究側時間が違うので、時間比の改善を厳密な速度倍率とは扱わない。
`--steps 1000 --profile` の cProfile では、toric d=5 の専用経路 0.276 秒のうち `FastStepper.attempt` 累積 0.232 秒、`propose` 0.100 秒、`CachedDecoder.predict` 0.049 秒、Z の `_distribution` 0.029 秒だった。
toric d=7 では同じ順に 0.245、0.100、0.066、0.028 秒であり、累積時間は呼び出し関係により重複する。
BB72 では decoder adapter の `predict` が 0.176 秒を占め、全体 0.426 秒の主因だった。
残る差は Python 側の候補処理と decoder adapter の出力検証、Z の局所分布正規化に集中し、次には確率表と検証済み decoder 出力を内部で一貫して保持する実装を、同 seed 軌道を維持する受入試験付きで検討する。
専用経路は組み込みの線形モデルと対応する積ノイズ、標準 failure の実型組み合わせだけに適用し、独自 failure や派生型は参照経路に戻す。

## WP-Q 局所表と decoder cache の更新（2026-10-01）

Windows 11 Pro build 22631、Python 3.11.9、AMD Ryzen 5 3600 6-Core Processor で、`$env:PYTHONDONTWRITEBYTECODE='1'; $env:RIMC_RESEARCH_ROOT='A:\dev\RIMC'; A:\dev\mcmc4qec\.venv-dev5-source\Scripts\python.exe benchmarks/bench_step.py --steps 10000 --seed 731 --repeats 2` を実行した。
各行は p=0.01、Z/H=0.7/0.3、cluster_k=2、lazy=0、1 chain、開始状態 `lx[0]`、同じ decoder 構築条件である。
ライブラリの秒数には `Result` と診断の作成が入るが、両者とも decoder 構築の時間は含めない。
2 回は同じ seed と設定の逐次反復であり、独立 seed の統計ではなく短時間の実行ばらつきを示す。

| 符号 | ライブラリ step/s 1回目 / 2回目 | 研究 step/s 1回目 / 2回目 | 時間比 1回目 / 2回目 | ライブラリ秒 1回目 / 2回目 |
| --- | ---: | ---: | ---: | ---: |
| toric d=5 | 8386.0 / 8553.4 | 22824.9 / 23202.2 | 2.722 / 2.713 | 1.1925 / 1.1691 |
| toric d=7 | 7322.0 / 7604.6 | 19148.8 / 19628.9 | 2.615 / 2.581 | 1.3657 / 1.3150 |
| BB72 | 4825.5 / 4931.7 | 7962.4 / 7741.7 | 1.650 / 1.570 | 2.0723 / 2.0277 |

toric d=5 と d=7 は研究 runner の 2 倍以内という目標に届かず、BB72 は届いた。
型注釈の最終修正前に同条件で行った別の 2 回では時間比が d=5 で 2.592/2.546、d=7 で 2.468/2.469、BB72 で 1.604/1.553 であり、上表は最終コードの値である。
型注釈の修正は proposal と受理の計算を変えないが、短い逐次計測のばらつきとして両結果を記録する。
`--steps 1000 --seed 731 --profile` の cProfile では、d=5 のライブラリ全体 0.186 秒のうち `FastStepper.attempt` の累積 0.153 秒、`propose` 0.062 秒、`CachedDecoder.predict` 0.033 秒、adapter の `predict` 0.028 秒だった。
d=7 は同じ順に全体 0.208 秒、0.164 秒、0.060 秒、0.047 秒、0.041 秒だった。
この累積時間は呼び出し関係で重複するため合計しない。
toric の残差は候補生成・全密度総和・failure 判定を含む Python 側の step 処理と、cache miss の decoder adapter 検証に分布する。
BB72 の同じ profile では全体 0.323 秒のうち adapter `predict` が 0.153 秒で、BP-OSD の decode と予測変換が依然として主因だった。
今回の専用経路は現状態の局所 log 比と Z 分布を保持し、各 attempt の正規化を最大 1 回にし、組み込み decoder cache の検証済み出力を hit で再検証しない。
全密度の座標順の総和、適用する実型 gate、公開既定、棄却と lazy の保存は維持した。
1000 step の profile は速度比較の正式な表とは別の原因探索であり、研究 runner との出力契約も異なる。
