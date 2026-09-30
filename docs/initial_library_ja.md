# 初期ライブラリ: 三種のノイズ・BAR・Stim DEM

2026-09-30。仕様 v0.2 の bit-flip 基盤から、三種のノイズと推定・接続へ進めた実装記録。
[第1段階](stage1_ja.md) は以前の到達点として保存する。
この文書は公開済み、物理回路再現済み、全仕様完了という宣言ではない。

## 状態と実験の定義

| 対象 | 状態・確率 | decoder 入力と論理 observable |
| --- | --- | --- |
| Bit-flip | 二値。位置別の `p * scales[i]` を指定可能 | `hz @ e` / `lz @ e` |
| Depolarising | 各量子ビットが I/X/Y/Z の一カテゴリ。確率は 1−p, p/3, p/3, p/3 | syndrome は X・Z sector の順、observable も同順 |
| Phenomenological | 時刻順のデータ fault、その後に時刻順の測定 fault。データは bit-flip または Pauli | 全ラウンドの history / difference。observable は最終累積データ誤り |
| Stim DEM | 一つの `error` 機構につき一つの独立 Bernoulli 変数 | 固定 H/L による detector / observable |

行列演算は mod 2。Pauli label は I=0, X=1, Y=2, Z=3 で、Y の X/Z 同時作用を保持する。
Depolarising の syndrome は `[hz @ X, hx @ Z]`、observable は `[lz @ X, lx @ Z]`。
独立 sector decoder を選ぶことと、生成するノイズを独立 X/Z に置き換えることは別である。

`PhenomenologicalModel(code, rounds, initial_boundary=..., final_boundary=...,
representation=..., data_noise=...)` では時間境界と表現を必須指定する。

- `initial_boundary="clean"` のみ対応し、初期 syndrome はゼロ。
- 各 round は新しいデータ誤りを加えてから測定する。
- `final_boundary="perfect"` は最後の round の測定 fault を除く。追加 round は作らない。
- `final_boundary="noisy"` は最後にも測定 fault を持つ。
- `history` と `difference` はともに `(rounds, n_checks)`。差分の最初は clean 初期値から取る。
- `PhenomenologicalNoise` の座標は `{"data": p_data, "measurement": p_measurement}`。
  測定 fault 座標がゼロ個でも両キーを明示する。

失敗確率はこの境界付き実験全体の確率であり、1 round 当たりへの換算はしない。
decoder に最後の静的 syndrome だけを渡して履歴を捨てる接続は、ここで定義した実験の一般的な
代替にはならない。利用者の decoder は入力表現と論理出力順に適合する必要がある。

## カーネルと実行条件

公開既定は Z 0.7、H 0.3、cluster size 2、1 chain、PT なし。
別の lazy 確率 0.05 を先に適用するので一歩ごとの Z/H/lazy は 0.665/0.285/0.05。
混合確率を暗黙に正規化せず、展開設定を保存する。
棄却と自己ループも一歩に数え、採否によらず thinning する。移動した状態だけの保存はしない。

OBF は binary では一 bit 反転、一般カテゴリでは単一位置のラベル置換。
Z は全単一位置近傍を一般 `log_prob` で評価し、逆向き提案の正規化も MH 比に含める。
これは小規模に検証しやすい参照実装で、大規模性能は保証しない。

H は単一状態内の occupied / empty 位置交換で、Pauli では occupied の relabel も持つ。
異なる alphabet を持つ状態は同 alphabet の群を一様選択し、その群内で更新する。
保存する重みは非ゼロ label の個数であり、整数 label の和ではない。
重み保存だけでは一般ノイズの密度保存にならないので MH 判定を行う。
静的 CSS の bit/Pauli stabilizer flip は任意に使えるが、独自 failure も再評価する。
Phenomenological に静的 stabilizer 更新は提供しない。

診断量は非ゼロ座標数に対する IAT・ESS・split R-hat。
特に phenomenological ではデータと測定の非ゼロ座標を数えた観測量であり、
論理状態や全 fault 構造を網羅する診断ではない。
詳細釣合い、自己ループ、良好な診断から、全失敗集合への到達可能性や収束は導けない。

## BAR の標準経路と近似経路

`estimate_logical_error(problem, ladder, anchor=..., ...)` は先頭座標の anchor に
隣接 normalizer 比を積み、各座標の絶対失敗確率を返す。
`bennett_log_ratio` は両側の標本で評価した `log rho_B − log rho_A` を使う。
iid の重み式に限定せず、各ノイズの正規化 `log_prob` を使う。
ladder は scalar または明示的な parameter dict の列で、隣接座標は異なる必要がある。

標準 `mode="fixed_failure"` は全 rung で同じ decoder object と failure predicate を使う。
anchor は `exact` または固定試行数の `direct_mc` Result とし、先頭の座標、model、noise、
decoder、failure の metadata が一致することを検査する。
ゼロ観測の MC anchor と真に空の exact failure は拒否する。
正の exact 確率が浮動小数点で underflow した場合は有限の `log_estimate` から接続できる。
全試行失敗の MC anchor も log-delta 分散を信頼できないため拒否し、
exact または追加の独立試行を要求する。各 rung は別の乱数系列で sampling する。

`mode="p_dependent_decoder_approx"` だけが `decoder_factory(prior)` を受け付ける。
`decoder_priors` は rung ごとに必須、`approximation_reason` も必須とし、sampling p と別に保存する。
この経路は変わる failure 集合を補正せず、density-only BAR を明示的な近似として実行する。
既知の研究上の選択を禁止するものでも、厳密化するものでもない。

小さい反例をテストに含める。1 bit、先頭 p=0.9 の failure が {1}、次の p=0.5 の failure が
{0} なら、それぞれの条件付き分布は一点である。density-only BAR は anchor 0.9 から
`0.9 × sqrt[(0.5/0.9)(0.5/0.1)] = 1.5` を返す一方、次の真の失敗率は 0.5。
これは標本不足によらない近似バイアスである。1 を超える点推定は clip せず警告し、区間は欠測にする。

両側に観測された support overlap がなければ `OverlapError`。
有限標本で観測された overlap は分布全体の十分な overlap を保証せず、小さい値に警告を付ける。

## 不確実性と再現性

MCMC の不確実性は各 chain 内の circular block bootstrap で評価する。
各 rung の再標本化 index をその左右の隣接比に共有し、隣接比の共分散を保存する。
既定 block 長は保存標本数の三乗根程度。`bootstrap_block_length` で長さへの感度を調べられる。
相関を無視した iid 標準誤差を MCMC に流用しない。

exact anchor の分散はゼロ、direct MC anchor は二項比率の log-delta 近似を用いる。
anchor と MCMC が独立であることを仮定するが、metadata だけでは独立性を証明できない。
MC の失敗数が少ない場合、delta 近似は信頼できない。
block 長より長い相関、未混合による偏り、近似 BAR の偏りは区間に含まれない。
bootstrap の一部で overlap が失われた場合、成功 draw に条件付けて SE を出すことはせず、
MCMC 区間を欠測にする。`bootstrap_replicates=0` は明示的に MCMC 区間を無効にする。

`EstimationResult` は ladder 全体の点推定・log 推定・隣接 log 比・区間・log SE・
共分散・overlap・rung 診断と metadata を保持し、JSON 往復に対応する。
出力確率が underflow した場合も有限の log 推定を保持し、表現不能の区間を欠測にする。
表示された float の 0 を真の率 0 と解釈しない。
通常 Result もカテゴリ状態を含む JSON 往復に対応する。
乱数設定、全 config、モデル hash、decoder 設定、研究参照 commit と新規コードの provenance を分ける。
任意の callable の実装を JSON から再構成するものではない。

## Decoder と Stim の接続範囲

既存 decoder の wrapper は logical observable / physical correction を必須の明示指定で分ける。
補正には論理写像が必要であり、長さによる推測をしない。BP-OSD は generic wrapper を使える。
PyMatching の相関設定は構築と decode で一致させる。既存 object の provenance は利用者の責任も伴う。

`from_stim_dem` は各 `error` instruction 全体を一機構として取り込み、`^` の各片を独立変数にしない。
固定 DEM の exact / MC / MCMC は `p=None` を使う。
ladder では明示的 `probabilities(p)` または `dem_factory(p)` と family identifier が必要。
factory の機構 signatures、順序、H/L が変われば拒否する。
probabilities callback は既に固定された機構それぞれへの確率を返す契約である。

`matching_from_dem` は未分解 hyperedge を黙って欠落させず、各分解片の graphlike 性を検査する。
`from_stim_circuit` は `decompose_errors` と `approximate_disjoint_errors` を記録し、
後者を失敗時の再試行で勝手に有効化しない。
この経路は DEM の分布を扱い、物理的な同一 gate の排他 fault カテゴリ分布とは区別する。
Stim から変換できたことだけで元の物理回路と全条件で同じモデルとは主張しない。

## 残る作業と公開条件

物理 circuit location ごとの排他 fault、追加・削除・置換 baseline、論文の 2d round と
前半 d round の補正範囲を一致させた実験、続く Z/H 拡張は次段階である。
回路 stabilizer flip は当面対象外。研究 runner の互換 wrapper と既定変更も今回含めない。
大きい符号での速度改善や混合時間保証、重い sweep は行っていない。

正式配布名、公開先、license、第三者権利、正式引用情報は未確定。
現在の `rimc` は仮称であり、CITATION は著者情報を推測しない暫定版。
公開 repo 作成、push、package publish を実施したとは扱わない。
テスト件数と実行環境は実際の検証記録に示し、CI 定義追加とホスト上の実行成功を区別する。
