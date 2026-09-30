# WP-C 第1回独立レビュー

対象は `wp/c` の checkpoint `a64d89b` とレビュー時の未コミット変更、`docs/wp/C_ja.md`、`docs/circuit_baseline_ja.md`、開発依頼書の WP-C 受入条件である。
実装コードは変更していない。

## 指摘

1. **高：2 ラウンド repetition exact が 2 ラウンド全体を列挙していない。**
`tests/test_circuit_pipeline.py:17-20` は最初の `DEPOLARIZE1` 命令の 3 target だけを採用し、`tests/test_circuit_model.py:83-84` の 1 ラウンド側も同じ 3 location だけを使う。
2 ラウンド回路の全データ location は 6 個であり、現テストでは後半のデータ fault が常にゼロになる。
同じ回路で全 6 location を列挙すると `4^6=4096` 配置、`p=0.1`、zero decoder の exact は `0.12444444444444515` になり、記録値 `0.06666666666666667` とは異なる。
全 6 location と DEM から作った PyMatching decoder の exact は `0.025156828532236022` であり、同じ Stim 回路の直接 20,000 試行は `0.0248` だった。
全 6 location と復号器を使う exact、および独立 Stim 直接試行との照合を受入テストに追加し、完了メモの限定された値を区別する必要がある。

2. **中：同一チャネル内で location ごとに異なる物理分布を指定できない。**
`src/mcmc4qec/circuit/model.py:187-218` の `CircuitFaultNoise` は条件付き fault 確率と故障率 `p` を channel 名の辞書から引くため、同じ `DEPOLARIZE1` に属する二つの location に異なる `q_i` や `p_i` を渡せない。
`docs/circuit_baseline_ja.md` の location `i` ごとの積分布という小仕様と異なり、回路固有の非一様な物理故障率を再現できない。
location ごとの明示値を受ける API と、同一 channel で異なる `q_i,p_i` を使う正規化、sampling、MH 詳細釣合いテストを追加する必要がある。

3. **低：条件付き fault 確率の和が 1 から外れても受理する。**
`src/mcmc4qec/circuit/model.py:198` の `math.isclose` は既定の相対許容誤差 `1e-9` を使う。
`q=[0.2,0.3,0.5000000005]` は和が `1.0000000005` だがコンストラクタに受理され、内部でも再正規化されないことを再現した。
`rel_tol=0, abs_tol=1e-12` として、許容値の境界をテストで固定する必要がある。

## 確認した範囲

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_model.py tests/test_circuit_proposal.py tests/test_circuit_surface.py tests/test_circuit_pipeline.py -q` は `13 passed in 90.97s` だった。
実行時は `PYTHONDONTWRITEBYTECODE=1` と `PYTHONPATH=src` を指定した。
4 ファイルの合計時間のみ測定し、各ファイルが 60 秒以内かは未測定である。
小回路では非一様 `q` の追加、削除、置換の順逆提案確率と失敗集合内の詳細釣合いをテストが確認している。
ランダムな複数 fault の XOR 合成を直接 Stim 挿入と比較するテストと、中点前後の fault の observable 差を確認するテストがある。
Stim と PyMatching を import 不可能にした状態でも `mcmc4qec.circuit` の import が成功した。
回路 `circuit_single` の選択、非回路からの拒否、棄却を含む保存標本、`estimate_logical_error` の接続を既存テストとコードで確認した。
全 suite、installed wheel、d>3 の統計検証、論文図表との一致はこのレビューでは未実施である。

[一次資料の第 III・IV 節](https://arxiv.org/html/2509.13678v2) は物理 gate と排他的 fault の配置、`2d` 回の noisy extraction と最初の `d` 回への訂正を記述している。
一般 MH の置換受理 `min(1,q_new/q_old)` と論文の `q_new` の差は文書に説明されており、どちらも対称な順逆提案の下で詳細釣合いを満たす。
中点 `MPP` の位置、追加された測定記録をまたぐ `rec` offset、最終測定を detector 境界に使う構成は、第 III・IV 節の目的と整合する範囲で確認した。

## 追加の独立照合

Stim が生成した通常の rotated surface d=3、6 noisy rounds 回路と中点 `MPP` を挿入した回路で、`CircuitFaultModel.from_stim_circuit` による全単一 fault 効果を比較した。
両回路は物理 location が各 368 個、detector が各 48 個で、location の channel と target の順序は全件一致した。
両モデルの detector 効果行列 `H` は 368 列すべて完全一致し、不一致列は 0 本だった。
この独立実測は中点への測定追加と後続 `rec` offset 補正が元の detector 効果を保つことを確認するが、論理 observable の定義を独立に証明するものではない。
実行時は指定の Python 3.11、`PYTHONDONTWRITEBYTECODE=1`、`PYTHONPATH=src` を使い、約 47 秒を要した。

## 第2回独立レビューと判定

修正コミット `782da6c` を主対象とし、境界反例への追加修正コミット `021bca7` まで確認した。
コードは編集せず、レビュー記録だけを追記した。

第1回の高指摘は解消した。
`tests/test_circuit_pipeline.py` は 2 ラウンドの全 6 データ location、`4^6=4096` 配置を列挙し、zero decoder の解析値 `0.1244444444` と PyMatching decoder の exact 値 `0.02515682853` を確認する。
同一 Stim 回路と decoder の直接 20,000 試行の失敗率は担当の固定 seed で `0.0255`、独立 probe の別 seed で `0.0248` であり、exact 値と統計的に整合した。
1 ラウンドは全 3 データ location の `4^3=64` 配置を列挙している。

第1回の中指摘は解消した。
`CircuitFaultNoise` は同一 channel 内の各 location に別の条件付き `q_i` と `location_rates` の `p_i` を受け、テストは全配置の正規化、sampling、失敗集合内の一般 MH 詳細釣合いを確認する。
独立 probe では location rates `[0.15,0.2]` から `[0.1,0.1]` への BAR 接続が動き、anchor exact `0.1`、target exact `0.05` に対し、120標本の推定値 `0.05067420990092076` を得た。
この短い BAR 実測は API 接続の確認であり、一般の混合や推定精度の保証ではない。

第1回の低指摘は解消した。
条件付き fault 確率の和は `rel_tol=0, abs_tol=1e-12` で検査され、和 `1.0000000005` を拒否する回帰試験が通った。

第2回で新たに見つけた高指摘も解消した。
修正前は Stim の有効な `M(0.2)` を物理 location に含めずに構築でき、無故障配置の `simulate_state` が反復で `0` と `1` に揺れる反例があった。
`021bca7` は確率引数付きの測定命令を effect cache の前に確実に拒否し、`M(0.2)` と `MPP(0.2)` の回帰試験を追加した。

第2回で新たに見つけた中指摘も解消した。
修正前は一命令の `X_ERROR(0.1) 0 0` の二つの独立 target group を同値の `FaultLocation` として重複拒否していた。
`021bca7` は `target_group_index` で二つを区別し、独立 probe で exact `0.18000000000000005` と Stim DEM の `error(0.18) D0 L0` の一致を確認した。

指定の Python 3.11 と `PYTHONDONTWRITEBYTECODE=1` で `tests/test_circuit_model.py`、`tests/test_circuit_proposal.py`、`tests/test_circuit_pipeline.py` は `18 passed in 4.18s` だった。
同じ条件で `tests/test_circuit_surface.py` は `2 passed in 20.13s` だった。
4 ファイルはいずれも 1 ファイル 60 秒以内の制約を満たす。
全 suite、installed wheel、遠隔 CI、論文図表との数値再現は第2回レビューで未実施であり、全 suite の最終合否はメイン統合後の検証待ちである。

WP-C の依頼範囲にある物理分布、単一 fault 効果と XOR、一般 MH、repetition exact、surface d=3 の direct MC 照合、既存 sampling/BAR 接続について、修正後に未解消の受入阻害事項は見つからなかった。
残る制約は文書どおりであり、非 Clifford、相関 location、排他的でない同一 location の複数 fault、未対応 Stim ノイズ命令、Z-OBF と cluster exchange と stabilizer flip の回路対応は対象外である。
