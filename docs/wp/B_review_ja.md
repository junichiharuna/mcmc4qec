# WP-B 第1回独立レビュー

2026-09-30 に `81aece0` からの WP-B 差分、`docs/wp/B_ja.md`、`docs/performance_ja.md`、研究側 `C:\dev\RIMC\src\runners.py` を確認した。
研究リポジトリは `PYTHONDONTWRITEBYTECODE=1` で読み取り専用 import し、終了時の `git status --short` は空だった。

## 指摘と対応

| 重大度 | 箇所 | 再現と影響 | 対応 |
| --- | --- | --- | --- |
| 高・修正済み | `src/mcmc4qec/decode_cache.py:43`、初版 `563be58` | `BinaryLinearModel([[1]], [[1]])`、`IndependentBitFlip(1)`、`predict` が `[0.5]` を返す独自 decoder、`p=.2`、`initial_state=[1]` を与えると、`Problem.is_faulty([1])` は `ValueError: prediction must be binary` だが、初版の `sample_faulty` は非法値を `uint8(0)` にして成功した。 | cache 挿入前に `binary(..., ndim=1)` で検証する修正と回帰テストを確認した。 |
| 中・受入で許容された未達 | `docs/performance_ja.md`、`benchmarks/bench_step.py` | 研究 runner 比の実測時間は toric d=5 で 17.57 倍、d=7 で 15.65 倍、BB72 で 5.95 倍であり、2 倍以内には届かなかった。 | `Problem.state` と `categorical` の反復検証を主因とする profile および次の専用経路案が記録されている。 |
| 低・比較解釈 | `benchmarks/bench_step.py`、`docs/performance_ja.md` | ライブラリは全状態、受理統計、診断と `Result` を生成し、研究 runner は重み履歴と重み分布を返すため、時間比は同一出力契約の純粋な kernel 速度比ではない。 | 文書はライブラリ側に `Result` と診断が含まれることを明示しており、残余の比較条件差として扱う。 |

## 独立検証

`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_fastpath.py -q` は最終修正後 13 件成功した。
`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests -q` は最終修正後 169 件成功した。
`output/wp_b_review_probe.py` は bit-flip の 4 状態、depolarising の 16 状態、phenomenological の 8 状態を、ゼロ support を含む複数の確率で全列挙した。
提案分布の高速経路と参照経路の最大絶対差は `1.11e-16`、各分布の正規化誤差は `1e-14` 未満、failure 集合内の詳細釣合いの最大絶対差は `0` だった。
独自 failure predicate `bool(state[0])` を使い、OBF 0.2 / Z 0.5 / H 0.3、`cluster_k=1`、`cache_cap=1`、100 標本、同一 seed で fastpath 有無と cache 有無の 4 構成を比較したところ、3 種のノイズすべてで状態軌道と受理統計が一致した。
`FailureEvaluator.syndrome` は bit-flip、depolarising、phenomenological の全状態・全 1 座標近傍について全面計算との一致を受入テストで確認した。
toric d=5 の純 Z 200 step、`p=.01`、`seed=731` では同じ軌道を保って高速経路無効が 1.067 秒、有効が 0.0741 秒で、約 14.4 倍の改善を実測した。
`benchmarks/bench_step.py --steps 1000 --profile` の独立再実行では研究側との時間比は d=5 が 17.99、d=7 が 18.14、BB72 が 6.52 で、cProfile の累積時間上位は `Problem.state` と `categorical` だった。

## 受入項目の判定

独立積ノイズの O(n) 近傍算術、厳密な型判定と任意ノイズへの非適用、syndrome 差分、研究 `cache_cap` の 10 step ごとの `len(cache)>cap` による全消去と LRU・凍結の追加、全状態・全近傍の等価性、同 seed 軌道、既存 suite は確認済みである。
研究速度 2 倍以内は未達だが、依頼書が代替として求める profile に基づく原因と次の手は記録済みである。
研究 runner との同 seed 軌道照合は WP-B の受入要件ではなく、乱数呼び出し順が異なるため未実施である。
