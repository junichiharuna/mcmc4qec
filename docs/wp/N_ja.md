# WP-N 小仕様と完了記録

## 小仕様（実装前）

専用ステップはモデルとノイズの実型が指定された組み込み型の組み合わせであり、標準の論理 observable 不一致を failure とする場合だけ使う。
`KernelConfig.zanella_fastpath=False` は参照経路を選ぶため、同じ seed の比較に使える。
初期状態は公開 `Problem.state` で一度検証し、以降の内部状態は提案から得た `uint8` のコピーとして保持する。
Z の近傍順序、確率計算式、`rng.choice` の呼び出し、MH 用 `rng.random` の条件を参照経路と揃える。
OBF、H、stabilizer の乱数呼び出しも同じ順序と引数を維持し、lazy と kernel 混合は従来の外側ループに残す。
支持のない候補は failure を評価せず棄却し、棄却と lazy は保存列に残す。
候補の syndrome と observable は線形効果の XOR で求め、受理時だけ保持値を更新する。
独自 failure、派生クラス、任意ノイズやモデルは参照経路に戻す。
受入試験は小さい状態空間の全状態・全近傍の提案確率と MH 受理確率、支持境界、同 seed の状態・acceptance・provenance、適用外 fallback を検査する。

## 実装と検証

`faststep.py` に積ノイズの局所確率表、Z 分布の現状態 cache、線形 syndrome と observable の差分更新、内部の検証済み状態の管理を実装した。
`sampling.py` は kernel 選択後の専用経路呼び出しを追加し、lazy、kernel 混合、保存 trace、Result の構築は既存経路を使う。
decode cache は従来の `CachedDecoder` を同じ境界タイミングで通す。
`test_faststep.py` は全小状態・全近傍の Z 提案と MH 確率、全 faulty 状態での実 attempt と参照 attempt の受理・状態・RNG 状態、同 seed の全 RNG 呼び出し列と Result、支持境界と派生型の fallback、2 round depolarizing phenomenological history を検査した。
`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_faststep.py -q` は最後の fallback テスト追加後に 15 passed、2.98 秒だった。
実装差分に対する `C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests -q` は 325 passed / 5 skipped、124.52 秒だった。
全 suite 後に fallback の受入テストだけを追加し、そのファイル単独の再実行で成功した。
研究 runner 比較のコマンドと数値、cProfile と残る原因は `docs/performance_ja.md` の WP-N 節に記録した。

## 統合依頼と残件

公開 API 名、README 行、CI の変更は不要である。
`sampling.py` の変更は `FailureEvaluator` 作成後の `make_faststep` 呼び出しと、ステップ内の参照経路との分岐だけである。
`kernels.py`、`fastpath.py`、`core.py` は変更していない。
研究 runner の 2 倍以内は toric d=5/7 で未達であり、残る主因と次の案を性能文書に記した。
wheel と remote CI はメイン統合後の検証事項として未実施である。
