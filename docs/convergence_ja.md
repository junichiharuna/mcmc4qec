# 複数 chain の診断と収束判定

`diagnose` は一つまたは複数の `Result` の `states` を連結し、状態ごとの非 identity 座標数を観測量として評価する。
各 `Result` の標本数は同じでなければならず、異なる run の chain は独立 seed で生成されている必要がある。
chain 間標準誤差は chain 平均の標本標準偏差を chain 本数の平方根で割り、各 chain の IAT と ESS、split R-hat、kernel ごとの全提案数・採択数・移動数と採択率を返す。
IAT は Geyer の初期正値ペア推定で、定数 chain、標本数 8 未満、または推定値が正でない場合は定義しない。
負の自己相関では IAT が 1 より小さく ESS が標本数より大きくなることがあり、1 への切り上げは行わない。
採択率は `sampling.py` と同じく burn-in と lazy step を含む全 step の集計値であり、個々の chain の kernel 採択率ではない。

`evaluate_convergence` は `Result`、`Result` の列、または `[chain, sample]` の数値配列を受け、同じ観測量の四条件を返す。
`other_initialization` は意図的に異なる初期状態から始めた別の chain 群を指定する。
`direct_variance` は独立な direct MC で求めた条件付き観測量の分散であり、direct MC の平均値の分散を渡してはいけない。
`direct_variance` がないときは第四条件を未判定とし、四条件全体を合格にしない。
この場合、研究論文の一次判定に相当する chain 内分散による比較は `within_chain_dispersion` に参考値として返す。
chain 内分散による比較は共有された捕捉領域を検出しにくく、独立 direct MC 分散による第四条件の代わりにはしない。

| 条件 | 判定式と既定閾値 | 検出できるもの | 検出できないもの |
| --- | --- | --- | --- |
| 標準誤差のスケーリング | `sd(N) / [sd(N/4) sqrt((N/4)/N)] <= 1.5` | chain 間の固定差や緩和中の集団 | 全 chain が同じ盆地へ緩和する場合 |
| 定常到達 | 最後の半分と直前四半分の平均差が `3 × SE(N) sqrt(6)` 以下 | burn-in 後にも残る遅いドリフト | 全 chain が共通の誤った定常領域にいる場合 |
| 異なる初期状態 | 二群の平均差が `3 × sqrt(SE_a² + SE_b²)` 以下 | 初期値によって別の盆地に捕捉される場合 | 両初期値が同じ盆地へ入る場合 |
| 分散と IAT | chain 間の標準偏差が `sqrt(W mean(IAT)/N)` の 3 倍以下 | IAT が chain 間散らばりを過小評価する場合 | 全 chain に共通のバイアス、過大な IAT 推定 |

第四条件の `W` は独立 direct MC による条件付き観測量の分散であり、論文の内部分散を使った一次判定とは区別する。
標準誤差のスケーリングには最初の `N/16` を使わず、初期値からの過渡に引きずられにくい `N/4` を使う。
定常到達判定は `N/4` までを捨て、区間 `N/4..N/2` と `N/2..N` を比較する。
最後の条件は研究側の `compare/convergence_flags.py` と同じ上側の閾値のみを判定し、比が小さい場合は失敗としない。
各条件の `ok` は真、偽、または資料不足による `None` であり、一つでも偽なら全体は偽、偽がなく `None` があれば全体は `None` になる。
分母がゼロで差または最終散らばりが正なら比率を無限大として不合格とし、差もゼロなら識別不能として `None` にする。
四条件がすべて真でも収束、エルゴード性、無偏性、正しさは証明されず、この警告は必ず返す。
独立な参照値が得られる領域では平均値そのものも direct MC または厳密列挙と比較する。

`minimum_weight_coset_representative(logical, stabilizers)` は `logical` と X 型または Z 型スタビライザー行の GF(2) 線形和の中で、ハミング重みが厳密に最小の代表を求める。
独立なスタビライザー行が 12 本以下なら全列挙し、それを超える場合は SciPy MILP が最適性を証明した解だけを採用する。
MILP は相対 gap をゼロに指定し、得た整数重みと双対下界の差が半整数未満であることも確認する。
時間切れや最適性未証明の場合は例外を投げ、近似解を最小と呼ばない。
`logical_representatives(code, sector="x")` は各論理基底行のコセットを別々に最小化するため、論理 X 行同士を混ぜて別の基底にしない。
`minimum_weight_initial_state` と `maximum_weight_initial_state` は、この最小化済み基底行の中でそれぞれ最軽量と最重量のものを選ぶ。
`random_logical_sector_initial_state` は非零の観測量ビット列を一様に選び、そのセクターの最小重み代表を求める。
`observable_sector_initial_state` は `lx @ lz.T` の交差行列を GF(2) 上で解くため、独立だが paired でない論理基底でも観測量ビットの指定を正しく扱う。
返る配列は `(n,)` の binary 状態であり、`sample_faulty(..., initial_state=state)` または各 chain 用の `(chains,n)` 配列として直接渡せる。
任意の decoder、独自 failure predicate、p の support については `sample_faulty` が受入時に検証する。
この初期化は静的 CSS の bit-flip セクターを対象とし、depolarising や回路故障のカテゴリ状態には適用しない。

```python
short = minimum_weight_initial_state(code)
long = maximum_weight_initial_state(code)
starts = np.stack([short, long])
result = sample_faulty(problem, p, config=SamplingConfig(chains=2), initial_state=starts)
report = diagnose(result)
```

研究側の主張は `compare/convergence_flags.py`、`src/metrics.py`、`paper/main.tex` の Setup、および `docs/meetings/2026-09-17_minutes.md` を参照して実装したものであり、論文の全数値を独立に再現したという意味ではない。
