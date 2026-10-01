# WP-L 完了メモ：物理回路 fault 状態での OBF と Zanella

## 実装

`KernelConfig` の回路モデル検査を緩和し、`single`、`zanella`、`circuit_single` の任意の混合を許した。
`cluster` と `stabilizer` は回路モデルに対応する物理 location 群と静的 stabilizer XOR 表現がないため、引き続き `ValueError` とした。
既存の `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0)` の挙動と `physical_fault` identifier は変更していない。
`fastpath._probability_rows` は正確な `CircuitFaultNoise` 型に限って `probabilities(p)` の location 別確率行を最大 alphabet 長までゼロ埋めして返す。
`CircuitFaultNoise.probabilities(p)` は実験全体の各物理 location に対する categorical 確率であり、論理誤り率ではない。
近傍列挙は `model.alphabets` を使うので、ゼロ埋めしたカテゴリを選ばない。
候補の syndrome と observable の回路専用差分更新は未実装とした。
既存の `FailureEvaluator` が回路モデルを全再計算する正しい参照経路を使い、今回は可変 alphabet と確率比の検証を優先した。
独自 failure predicate に対して stabilizer 不変性を仮定する変更はしていない。

## 受入検証

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_kernels.py -q -s --durations=10` は 6 passed、26.14 秒で、最長テストは 17.50 秒だった。
PNG と区間記録の修正後、`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_kernels.py tests/test_circuit_pipeline.py tests/test_fastpath.py -q` は 24 passed、37.83 秒だった。
repetition d=3 の 1 ラウンドの `4^3=64` 配置を使い、OBF、Zanella 参照経路、Z 0.7 / OBF 0.3 の全状態について提案正規化を検査した。
同じ配置の失敗集合上の全一座標近傍で順向きと逆向きの提案確率および MH 受理を計算し、詳細釣合いを照合した。
同じ問題の全配置で Zanella fastpath と参照経路の提案分布を `1e-14` の絶対許容差で照合し、同じ seed の混合 sampler の状態列と kernel 別受理集計が完全一致した。
全 location の alphabet 長が等しい場合だけ OBF と `PhysicalFaultProposal` の全遷移確率が一致し、長さ 2 と 4 の混在時は異なることを列挙で確かめた。
異なる conditional fault 確率と location 故障率を持つ alphabet 長 2・4・4 の小回路で、確率行の数値、zero padding、全配置の fastpath と参照経路の分布を照合した。
回路モデルで `cluster` または `stabilizer` を選ぶと、独自 failure predicate を指定しても `ValueError` となることを検査した。
surface d=3、`p=0.03` の独立 300 試行では 108 失敗、条件付き重みの通常近似区間は `12.093±0.556` だった。
Z 0.7 / OBF 0.3 の 300 標本と burn-in 100 の chain は `9.440±1.555`、診断 ESS は 7.674 で、二つの区間は重ならなかった。
通常近似区間と短い chain の比較に被覆保証はなく、非交差と低い ESS は混合不足などを疑う根拠となるが、どちらの推定値が正しいかは決められない。
診断は収束・エルゴード性・正しさの証明ではない。

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe examples/circuit_zanella.py --quick` は `PYTHONPATH=src` で成功し、PNG 追加後の再実行で 3.89 秒だった。
同じ既定実行は `PYTHONPATH=src` で成功し、PNG 追加後の再実行で 13.79 秒だった。
どちらも CSV と Agg backend の PNG および所定キーの `SUMMARY` を出力し、条件付き chain から絶対 `P_L` を推定していない。
`pymatching` import 後に `sys.modules["matplotlib"]=None` として `runpy` で quick を実行した場合も 3.50 秒で成功し、PNG を省略して CSV と同じキーの `SUMMARY` を出力した。

| surface d=3、`p=0.02`、150 step | step/s | 受理率 |
| --- | ---: | ---: |
| `circuit_single` | 173.50 | 0.0333 |
| Zanella | 55.67 | 0.7533 |
| Z 0.7 / OBF 0.3 | 62.56 | 0.5333 |

`PYTHONPATH=src C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe benchmarks/bench_circuit_step.py --steps 150` は Windows PowerShell の環境変数設定で実行し、全体で 7.77 秒だった。
各 step/s は回路構築後の `sample_faulty` 実行時間から計算し、受理率は異なる seed の短い chain の観測値である。
物理 location の提案間で受理率が異なっても、混合品質の優劣を示さない。

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests -q` は 315 passed、5 skipped、1 failed、153.32 秒だった。
唯一の失敗は `tests/test_docs_manifest.py::test_example_index_matches_every_python_file_and_notebook` が新しい `examples/circuit_zanella.py` の `examples/README.md` 行を要求したためである。
共有 README の更新後の全 suite と installed wheel 検証は未実施であり、メインの統合検証を要する。
研究リポジトリ `A:/dev/RIMC` の `git status --short` は空で、読み取り専用を保った。

## メインへの統合依頼

`examples/README.md` に `circuit_zanella.py` の行を追加する。
行案は目的「surface d=3 の物理 `circuit_single` と Z+OBF の条件付き重み・受理率・IAT 比較」、extras「`stim, matching`、図は `plot`」、既定と quick の実測時間は本メモの再実行値、出力「PNG と CSV の条件付き重みは絶対 `P_L` でない」、注意「1、2、5、6」とする。
`README.md` と `README_ja.md` の対応表の Physical Stim circuit locations 行を OBF、Zanella、`circuit_single` 対応に更新し、cluster と stabilizer は unavailable のままとする。
`docs/api_en.md` の `KernelConfig` 説明に、回路モデルでは `single`、`zanella`、`circuit_single` の混合を許し、cluster と stabilizer を拒否することを追記する。
既存 `examples/circuit_baseline.py` の冒頭 docstring は Z が使えないという旧仕様なので、文書だけを修正する。
`.github/workflows/tests.yml` の optional job で `examples/circuit_zanella.py --quick` を実行し、`docs/wp/verify_wheel.py` の optional 例にも追加する。
共有ファイルは本ブランチで編集していない。
旧仕様の拒否を期待する `tests/test_circuit_pipeline.py::test_circuit_rejects_unsupported_kernel_mixes` は、今回許可された `single` 混合から引き続き禁止される `cluster` 混合へ最小変更した。
このテストファイルは担当一覧外だが、受入条件と全 suite の整合のため変更が必要であり、メインのレビューを求める。
`sampling.py` の変更は `KernelConfig` docstring と `sample_faulty` の回路 kernel 検査だけで、`fastpath.py` の変更は `CircuitFaultNoise` 確率行分岐だけである。
WP-N の main 統合後にこのブランチを rebase し、同一 seed の等価性テストを再実行する必要がある。
回路向け cluster exchange を将来設計するなら、物理 location の group 化と group 間で異なる alphabet 長の proposal 比を定義してから、有限配置で正規化と詳細釣合いを調べる必要がある。
