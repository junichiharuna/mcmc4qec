# 回路レベル baseline の小仕様

## 状態と確率

物理的な Stim ノイズ命令の各 target group を一つの location とする。
同じ命令内に同一 qubit または qubit pair が繰り返されても、`target_group_index` で区別した独立 location とする。
各 location は無故障 `0` または一つの Pauli fault ラベルを取り、同じ location に二つの fault は置けない。
利用者は `CircuitFaultModel.from_stim_circuit(..., location_rule=...)` で物理 location の列挙規則を渡せる。
列挙規則が選ばなかったノイズ命令は基準回路から除去され、その location の故障率はゼロとなる。
初期対象のノイズ命令は `X_ERROR`、`Y_ERROR`、`Z_ERROR`、`DEPOLARIZE1`、`DEPOLARIZE2` とする。
確率引数付きの `M`、`MR`、`MPP` などは測定結果を乱数で反転するため、決定的な効果行列の対象外として構築時に拒否する。
二量子ビットの alphabet は `IX` から `ZZ` までの非恒等 Pauli 15 種を一つの排他的カテゴリとして扱う。
入力回路に書かれたノイズ確率は location 列挙にだけ使い、計算する分布は明示した条件付き alphabet 確率と指定した `p` で決める。
`CircuitFaultNoise` はチャネル名別の確率辞書のほか、各 location に対応する確率ベクトル列を受け付ける。
`p` は共通の scalar、チャネル名別の辞書、または `{"location_rates": [...]}` で各 location に異なる値を指定できる。
location `i` の無故障確率は `1-p_i`、fault `f` の確率は `p_i q_i(f)` とし、`q_i` の和は 1 を要求して暗黙の再正規化をしない。
全配置の確率は location 間の積であり、`p` は指定回路で行う実験全体の物理 location 故障率である。

## Stim 効果と復号

ノイズ命令を取り除いた回路へ選んだ Pauli fault を元の位置に確定的に挿入する。
各単一 fault の detector と observable の効果を Stim で求め、任意配置は効果の GF(2) XOR で合成する。
線形性の適用範囲は決定的な detector と observable を持つ Clifford 回路に限定し、直接挿入シミュレーションでランダム配置を照合する。
論理失敗は同じ `Problem` に指定された decoder 予測と真の observable の不一致として定義する。

## 提案

物理 location を一様に選び、その location の非零 fault ラベルを一様に選ぶ。
空なら追加し、選んだラベルが現在と同じなら削除し、異なれば置換する。
各非自己遷移の順向き提案確率と逆向き提案確率はいずれも `1/(location 数 × 当該 location の fault 数)` であり、一般 MH 受理には密度比を使う。
詳細釣合いは failure 集合を含む小回路の全配置で検証する。
論文第 III 節の追加の受理値 `p_i q_i(f)/(1-p_i)` は一般 MH 値の `min(1, p_i q_i(f)/(1-p_i))` と同じ低故障率領域で一致する。
論文第 III 節の削除の受理値 `1` は `p_i q_i(f) <= 1-p_i` の場合に一般 MH 値 `min(1, (1-p_i)/(p_i q_i(f)))` と一致する。
論文第 III 節の置換の受理値 `q_i(f_new)` は一般 MH 値 `min(1, q_i(f_new)/q_i(f_old))` と通常は異なる。
置換の論文値は逆向きで `q_i(f_old)` を使うため詳細釣合い比は満たすが、一般 MH より棄却が多い。
例えば三つの等確率 fault なら論文の置換受理は `1/3`、この実装の一般 MH 受理は `1` となる。
一般 MH の各場合で提案の順向き・逆向き確率をコードと全状態テストで照合した。
詳細釣合いは定常分布の必要な関係を示すが、失敗集合上の既約性や周期性を証明しない。

## 基準問題

repetition d=3 の 1〜2 ラウンドで物理 fault 配置を全列挙する。
rotated surface d=3 の 6 ラウンドで中点に理想的な論理 Pauli 測定を挿入し、その値を前半 3 ラウンドの logical idle の真値とする。
後半 3 ラウンドの noisy detector 情報も PyMatching decoder に渡すが、後半のデータ fault 自体は中点 observable を変えない。
通常の Stim memory 実験の最終時刻 observable をこの中点 observable に流用しない。
生成回路の最終 `M` または `MX` の測定記録から論理演算子の支持量子ビットを逆引きする。
第 `d` ラウンド後の `TICK` 境界に理想 `MPP` を挿入し、終端の `OBSERVABLE_INCLUDE` を中点の `MPP` 記録へ移す。
追加された測定記録より前を参照する後続 `DETECTOR` の `rec` offset を一つ補正し、後半ラウンドの detector の意味を保つ。
中点 `MPP` はノイズ location に含めず、測定値を decoder 入力に直接渡さない。
入力状態は準備した論理 Pauli の固有状態に Pauli fault が作用したものなので、理想 `MPP` の固有値は各配置で決定的であり、測定 backaction が後続の論理履歴を変えない。
`decompose_errors=True` を明示した Stim DEM から PyMatching decoder を構築するが、物理配置の確率を独立 DEM bit に置き換えない。
decoder は DEM の graphlike 分解を用いる近似を含み得るため、同じ decoder を物理配置 MC と Stim 直接試行の両側で共有して照合する。

## 実行した検証

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_model.py -q` は 10 passed、0.32 秒だった。
`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_pipeline.py -q` は 5 passed、3.39 秒だった。
`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_proposal.py -q` は 3 passed、0.25 秒だった。
`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_surface.py -q` は 2 passed、20.64 秒だった。
`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_model.py tests/test_circuit_pipeline.py tests/test_circuit_proposal.py tests/test_circuit_surface.py -q` は 20 passed、25.53 秒だった。
全 suite の旧版 168 passed、45.11 秒という結果は第1回レビューへの修正前のものである。
修正後の全 suite は約 296 秒で 5 分の上限に近づいたため、完走前に停止した。
全 suite の最終合否は未確認であり、B の高速経路を統合した main で再検証する。
repetition d=3 の 1 ラウンドではデータノイズ 3 location の `4^3=64` 配置を全列挙し、zero decoder の `p=0.1` の失敗率が解析値 `2p/3=0.066666...` と一致した。
repetition d=3 の 2 ラウンドではデータノイズ全 6 location の `4^6=4096` 配置を全列挙し、zero decoder の `p=0.1` の失敗率が解析値 `0.1244444444` と一致した。
同じ 2 ラウンド問題で Stim DEM から PyMatching decoder を構築すると、exact の失敗率は `0.02515682853` となり、独立 Stim 直接 20,000 試行の `510/20000=0.0255` と照合した。
同一 `DEPOLARIZE1` チャネルの二つの location に異なる条件付き確率と故障率を与え、全配置の正規化、sampling、詳細釣合いを検証した。
同じ `X_ERROR` 命令内の重複 target `0 0` は二つの独立 location として区別し、両方が `X` の配置では効果が相殺され、`p=0.1` の exact 失敗率が `2p(1-p)=0.18` となることを検証した。
確率付きの `M(0.2)` と `MPP(0.2)` を構築時に拒否する回帰試験を実施した。
小回路の `2×4=8` 配置ではノイズ正規化、排他的 support、提案確率の正規化と対称性、失敗集合上の詳細釣合いを検証した。
repetition d=3 の配置を既存 `sample_faulty` と `estimate_logical_error` に渡し、物理 `circuit_single` 提案が選択されること、全保存標本が同じ failure 定義を満たすことを確認した。
rotated surface d=3 の 6 ラウンド回路は 368 個の物理 location、48 個の detector と一つの中点 observable を持った。
中点前のデータ `X` fault は中点 observable を反転し、中点後の同じ fault は反転しなかった。
`p=0.01` の独立 Stim 直接試行 5,000 回では 442 回失敗し、失敗率は 0.0884 だった。
同じ decoder を使う物理配置の `direct_mc` 700 回では 74 回失敗し、失敗率は 0.105714、Wilson 95% 区間は `[0.085049, 0.130683]` で Stim 直接試行の値を含んだ。
`examples/circuit_baseline.py` は 368 location、48 detector、500 試行の失敗率 0.0900 と Wilson 95% 区間 `[0.067943, 0.118309]` を出力した。
論文の図表の再現は主張しない。

## 対応範囲

物理配置上の単一 location 提案、OBF、Zanella とそれらの任意の混合を一般 MH で扱う。
OBF は全 location の非零ラベル候補から一様に選び、`circuit_single` は location を一様に選んでからその非零ラベルを選ぶため、alphabet 長が異なると提案分布が異なる。
Zanella の product-noise fastpath は `CircuitFaultNoise.probabilities(p)` の実験全体に対する location 別確率行を使い、最大 alphabet 長までゼロ埋めするが、埋めたラベルは近傍に含まれない。
回路での `cluster exchange` は物理的な location 群の定義と異なる alphabet 長の扱いが未設計のため対象外とする。
回路の `stabilizer flip` も静的な stabilizer XOR 表現がないため対象外とする。
任意の非 Clifford 回路、相関する location 間ノイズ、排他的でない同一 location の複数 fault、`PAULI_CHANNEL_1/2` と `CORRELATED_ERROR` の入力回路は未対応。
Stim と PyMatching がない環境では回路テストを skip する。
optional 依存を入れていない core venv では Stim と PyMatching が見つからない状態で `mcmc4qec.circuit` と `sampling.KernelConfig` の import が成功した。

## WP-L の検証と短い速度測定

repetition d=3 の 1 ラウンドで `4^3=64` 配置を列挙し、OBF、Zanella、両者の混合について全配置の提案正規化と失敗集合上の詳細釣合いを確認した。
同じ配置で Zanella fastpath と参照経路の近傍分布を照合し、混合 sampler の同一 seed の保存状態列と受理集計が一致した。
異なる alphabet 長と location ごとの条件付き確率・故障率を持つ小回路でも全配置の fastpath と参照経路を照合した。
これらの確認は失敗集合上の既約性や周期性を証明しない。
surface d=3、`p=0.03`、独立 300 試行では 108 個の失敗から `E[w|faulty]=12.093±0.556` の通常近似区間を得た。
Z 0.7 / OBF 0.3 の 300 標本、burn-in 100 の chain では `E[w|faulty]=9.440±1.555`、診断 ESS は 7.674 で、二つの区間は重ならなかった。
この通常近似区間は厳密な被覆保証ではなく、低い ESS と非交差のため混合不足などを疑う必要があり、推定精度を主張しない。

| surface d=3、`p=0.02`、150 step、各 kernel で初期状態を探索 | step/s | 受理率 |
| --- | ---: | ---: |
| `circuit_single` | 173.50 | 0.0333 |
| Zanella | 55.67 | 0.7533 |
| Z 0.7 / OBF 0.3 | 62.56 | 0.5333 |

上の表は最初の実測であり、回路構築時間を除く一方、各 kernel ごとの失敗初期状態の探索時間を `sample_faulty` に含んでいた。

| surface d=3、`p=0.02`、150 step、共通の失敗初期状態 | step/s | 受理率 |
| --- | ---: | ---: |
| `circuit_single` | 176.95 | 0.0067 |
| Zanella | 52.63 | 0.6600 |
| Z 0.7 / OBF 0.3 | 63.23 | 0.6467 |

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe benchmarks/bench_circuit_step.py --steps 150` を WP-N 統合後に再実行した値である。
共通の supported faulty 初期状態は 6 試行、0.056 秒で得られ、その探索時間を表の step/s から除いた。
各 kernel の `sample_faulty` 呼び出し時間には構成、provenance、診断を含むため、純粋な一ステップ計算量だけの比較ではない。
受理率と step/s は異なる seed と短い chain の観測値であり、混合品質や論理誤り率の優劣を示さない。
