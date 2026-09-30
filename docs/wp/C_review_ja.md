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
