# WP-B 性能比較

2026-09-30 に Windows、Python 3.11.9、NumPy 2.4.6、PyMatching 2.4.0、ldpc 2.4.1 で実測した。
コマンドは `$env:PYTHONDONTWRITEBYTECODE='1'; C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe benchmarks/bench_step.py --steps 10000` である。
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
