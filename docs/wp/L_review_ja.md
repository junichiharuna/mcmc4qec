# WP-L 独立レビュー：物理回路 fault の OBF と Zanella

## 判定

実装の確率行と提案比に反例は見つからなかったが、混合カーネルの受入テストを補強してから統合することを求める。
このレビューは `wp/l` の `606fc7b` と基点 `b8fde01` の差分を対象とし、WP-N 統合後の rebase と再検証は対象外である。

## 統合前に対応を求める点

`tests/test_circuit_kernels.py` の `Mixture.probability` は OBF と Zanella の提案確率を足してから一つの MH 受理率を計算するが、`sample_faulty` は先にカーネルを選び、選んだカーネル固有の提案比で受理する。
したがって `_flow` の混合検査は実サンプラーの遷移を直接検証せず、`q` と逆方向の `q` から作った MH 流量の代数的な等式を再確認している。
今回の `CircuitFaultNoise` は location 間で独立なので、列挙した repetition 64 状態と異種 alphabet・異種故障率の 32 状態では両計算法の遷移値が丸め誤差内で一致し、現実装の違反は観測されなかった。
その一致は現行テストの実遷移検査の代わりにはならない。
各成分の `q_k(a,b) min(1, π(b)q_k(b,a)/(π(a)q_k(a,b)))` を混合重みで合算し、failure gate、棄却による対角成分、lazy を加えた全遷移行列について行和と失敗集合上の詳細釣合いを検査することを求める。
`propose` が `probability` と同じ候補・提案比を返すことも、64 状態の各 flat index と `circuit_single` の location・ラベルの各分岐で検査してほしい。
固定した乱数列で `sample_faulty` の各カーネル選択、受理、failure 棄却、lazy を強制し、保存状態と受理集計が遷移行列の各成分に対応することも検査してほしい。
これにより提案 API だけが正しく、sampler の実際の分岐が誤る場合を検出できる。

## 独立に確認した結果

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_kernels.py tests/test_circuit_pipeline.py tests/test_fastpath.py -q` は 24 passed、37.08 秒だった。
repetition 64 状態では OBF、参照 Zanella、`PhysicalFaultProposal` の提案行和の最大誤差はそれぞれ 0、`2.22e-16`、0 だった。
同じ 64 状態の全分岐で `propose` の候補に対する `probability` は正で、返された対数提案比との最大誤差は OBF 0、参照 Zanella `4.44e-16`、fastpath Zanella `4.44e-16`、`circuit_single` 0 だった。
OBF 0.3 と Zanella 0.7 を成分ごとに MH 受理した失敗集合の遷移行列では、行和の最大誤差は `2.22e-16`、詳細釣合い流量の最大差は `1.09e-19` だった。
この問題の失敗集合は 32 状態で、正の遷移による連結成分は一つ、自己ループの最小確率は `0.264` だった。
したがってこの列挙例の制限 chain は既約かつ非周期的だが、一般の回路問題へは外挿しない。
異種 alphabet 2・4・4 と location 別故障率 `.1, .2, .3` の 32 状態でも、成分別混合と集約提案 MH の最大差は `2.22e-16`、成分別混合の詳細釣合い流量の最大差は `8.68e-19` だった。
確率 0 のラベルと故障率 0・1 を含む別の 2・4・4 の小回路では、3 個の支持内状態に対して fastpath と参照 Zanella の最大差は 0 で、15 個の支持外近傍に割り当てた確率も 0 だった。
この境界ケースは現行テストにないため、zero padding と support の受入テストに追加する価値がある。
`CircuitFaultNoise.probabilities(p)` は complete experiment の location 別 categorical 行を返し、`_probability_rows` のゼロ埋めは `model.alphabets` に基づく近傍列挙の対象にならないことを確認した。
同一 seed の fastpath と参照経路の状態列・受理集計は既存テストで一致した。
回路に cluster または stabilizer を混ぜると `ValueError` になり、独自 failure predicate の stabilizer 不変性は仮定していない。
`tests/test_circuit_pipeline.py` の 1 行変更は、許可される `single` 混合から禁止される `cluster` 混合へ旧拒否条件を移すために必要な最小変更である。

## 例、測定、文書

`examples/circuit_zanella.py --quick` は約 4.00 秒で成功し、所定の七つの `SUMMARY` キー、CSV、PNG を出力した。
matplotlib を import 不可にした実行は約 3.77 秒で成功し、CSV と同じ `SUMMARY` キーを出力した。
`benchmarks/bench_circuit_step.py --steps 150` の再実行値は `circuit_single` が 179.57 step/s・受理率 .0333、Zanella が 57.41 step/s・.7533、Z+OBF が 68.82 step/s・.5333 だった。
文書の step/s との違いは短い時間測定の変動範囲として扱い、受理率は再現した。
benchmark は kernel ごとに異なる seed で失敗初期状態を探す時間も `sample_faulty` の計測に含むため、純粋な一ステップ計算量の比較に使う際は共通の supported faulty 初期状態を指定し、初期化時間を分けて記録する方がよい。
`docs/circuit_baseline_ja.md` は direct MC と条件付き chain の区間非交差、低 ESS、および精度を主張できないことを明記しており、非交差を隠す seed 調整は見られない。
回路の syndrome と observable の差分更新は任意項目として未実装と明記され、全再計算が使われる。
全 suite は WP-L 完了メモで `examples/README.md` の未更新による 1 失敗と報告されており、共有文書反映後の全 suite と installed wheel はこのレビューでは未実施である。
研究リポジトリ `A:/dev/RIMC` の `git status --short` は空だった。

## メインへの引き継ぎ

担当者に成分別 MH と実際の sampler 分岐を検証するテストの追加を依頼する。
WP-N の main 統合後に WP-L を rebase し、同一 seed の fastpath・参照経路等価性、回路テスト、全 suite を再実行する。

## 担当者の対応記録

WP-N 統合済み main `527548b` への rebase は競合なく完了した。
レビューが求めた成分別 MH、failure 棄却、lazy、対角自己遷移の 64 状態遷移行列検査を `tests/test_circuit_kernels.py` に追加した。
全 flat 近傍の OBF と Zanella、および物理提案の全 location・ラベル分岐で `propose` の候補と逆順比を `probability` に照合した。
固定乱数の実サンプラーで各 kernel 選択、failure 棄却、受理、lazy、保存状態と受理集計を検査した。
境界の故障率 0・1 と確率 0 ラベルの支持外近傍もテストへ追加した。
WP-N の専用 `faststep` が回路モデルを対象外と判定することを確認した。
レビュー指摘を受けて benchmark は共通の supported faulty 初期状態を探索し、その探索時間を step/s の測定から外すよう変更し、旧値と新値の両方を `docs/circuit_baseline_ja.md` と完了メモに残した。
rebase 後の対象 7 ファイルは 59 passed、47.27 秒で、新しい回路カーネルテスト単体は 9 passed、28.48 秒だった。
混合遷移行列の対角を rejection と lazy から直接計算する最終修正後の対象 7 ファイルも 59 passed、46.06 秒だった。
共有 manifest 更新後の全 suite はメイン担当であり、この記録時点では未実施である。
