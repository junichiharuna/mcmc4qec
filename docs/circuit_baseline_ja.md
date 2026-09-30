# 回路レベル baseline の小仕様

## 状態と確率

物理的な Stim ノイズ命令の各 target group を一つの location とする。
各 location は無故障 `0` または一つの Pauli fault ラベルを取り、同じ location に二つの fault は置けない。
初期対象のノイズ命令は `X_ERROR`、`Y_ERROR`、`Z_ERROR`、`DEPOLARIZE1`、`DEPOLARIZE2` とする。
二量子ビットの alphabet は `IX` から `ZZ` までの非恒等 Pauli 15 種を一つの排他的カテゴリとして扱う。
入力回路に書かれたノイズ確率は location 列挙にだけ使い、計算する分布は明示した location 別の条件付き alphabet 確率と指定した `p` で決める。
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

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests -k circuit -q` は 13 passed、155 deselected、13.46 秒だった。
`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests -q` は 168 passed、45.11 秒だった。
repetition d=3 の 1 ラウンドと 2 ラウンドでは、最初のデータノイズ位置三つに制限した `4^3=64` 配置を全列挙し、`p=0.1` の失敗率が解析値 `2p/3=0.066666...` と一致した。
小回路の `2×4=8` 配置ではノイズ正規化、排他的 support、提案確率の正規化と対称性、失敗集合上の詳細釣合いを検証した。
repetition d=3 の配置を既存 `sample_faulty` と `estimate_logical_error` に渡し、物理 `circuit_single` 提案が選択されること、全保存標本が同じ failure 定義を満たすことを確認した。
rotated surface d=3 の 6 ラウンド回路は 368 個の物理 location、48 個の detector と一つの中点 observable を持った。
中点前のデータ `X` fault は中点 observable を反転し、中点後の同じ fault は反転しなかった。
`p=0.01` の独立 Stim 直接試行 5,000 回では 442 回失敗し、失敗率は 0.0884 だった。
同じ decoder を使う物理配置の `direct_mc` 700 回では 74 回失敗し、失敗率は 0.105714、Wilson 95% 区間は `[0.085049, 0.130683]` で Stim 直接試行の値を含んだ。
`examples/circuit_baseline.py` は 368 location、48 detector、500 試行の失敗率 0.0900 と Wilson 95% 区間 `[0.067943, 0.118309]` を出力した。
論文の図表の再現は主張しない。

## 対応範囲

物理配置上の単一 location 提案と一般 MH を対象とする。
Z-OBF、cluster exchange、stabilizer flip は対象外。
任意の非 Clifford 回路、相関する location 間ノイズ、排他的でない同一 location の複数 fault、`PAULI_CHANNEL_1/2` と `CORRELATED_ERROR` の入力回路は未対応。
Stim と PyMatching がない環境では回路テストを skip する。
