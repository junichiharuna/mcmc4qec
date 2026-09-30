# WP-B 性能実装・検証記録

2026-09-30 実施。

## 小仕様と実装

独立積ノイズの単一座標変更では、変わった座標の確率比だけから Z の近傍重みを計算する。
高速経路の自動適用は組み込み `IndependentBitFlip`、`DepolarizingNoise`、`PhenomenologicalNoise` の厳密な型に限り、派生クラスや任意 noise は一般 `log_prob` 経路を使う。
現在状態が support 外なら参照経路へ戻り、ゼロ確率の近傍は重みゼロとする。
Z の近傍確率は全候補の局所対数比から算出し、逆向きの正規化定数も候補状態で同じ方法で算出する。
cache は完全な syndrome の shape と bytes をキーに、decoder の論理予測をコピーして保存する。
`cache_policy="research_clear"` は研究 runner と同じく 10 ステップの区切りで `len(cache)>cache_cap` なら全消去する。
依頼書にある LRU または凍結という `cache_cap` の前提は研究実装とは異なり、周期消去が実際の研究意味である。
研究対応を明示するため `research_clear` を既定とし、追加で厳密な上限を守る `lru` と `freeze` を選べるようにした。
`research_clear` の上限は区切りまで超過しうる soft cap であり、`cache_cap=None` は無制限である。
failure 評価では `BinaryLinearModel` と `DepolarizingModel` の単一座標変更だけ syndrome を列の XOR で更新し、他は model の全面評価へ戻す。
論理 observable と独自 failure predicate は候補ごとに評価し、stabilizer 不変性は仮定しない。

`sampling.py` の変更箇所は `KernelConfig.zanella_fastpath`、`SamplingConfig.cache_cap/cache_policy`、Z インスタンスの設定、decoder cache と failure 評価器の接続、10 ステップごとの cache 境界、結果 metadata の cache 設定、公開 API docstring の追記に限る。
メインが追加すべき公開名は `CachedDecoder` と `FailureEvaluator` の必要性を判断後に追加し、低水準の `product_neighbor_distribution` は公開しない。

## 実行した検証

`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_fastpath.py -q` は 8 件成功し、0.54 秒だった。
小規模の bit-flip、depolarising、phenomenological の全状態・全近傍で高速経路と参照経路の提案確率と MH 受理確率を比較した。
同じ seed の bit-flip chain 200 標本では状態軌道と受理統計が完全に一致した。
派生 noise の参照経路への戻り、ゼロ support、cache 方針、syndrome 差分と全面計算の一致も確認した。
`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests -q` は 164 件成功し、再実行では 43.51 秒だった。
`$env:PYTHONDONTWRITEBYTECODE='1'; C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe benchmarks/bench_step.py --steps 10000` は最終コードで 15.54 秒で完了した。
ベンチマーク詳細と 2 倍未達の profile は [性能記録](../performance_ja.md) に記載した。
`git -C C:\dev\RIMC status --short` は出力なしで、研究 repo は変更していない。

## 未実施・限界

研究 runner とライブラリの RNG 呼び出し順は異なるため、研究 runner との同一 seed 軌道の照合は未実施であり、同一 seed 軌道の検証対象はライブラリ内の参照経路と高速経路である。
cache を有効にした外部 decoder の可変内部状態や非決定性は対象外である。
研究速度の 2 倍以内は未達であり、profile の次段階は汎用状態検証を経路内で繰り返さない専用の厳密検証済み状態表現を設計することになる。
