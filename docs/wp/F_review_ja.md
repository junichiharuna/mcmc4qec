# WP-F 独立レビュー

## 判定

新規4例と既存6例のCLI改修は、科学上の前提と実行契約について受入可能である。
BB72例の冒頭にあった `Diagnostics prove no mixing.` は診断の意味を誤って伝えるため修正を依頼し、`967d4cd` で `Diagnostics do not prove convergence or mixing.` に直ったことを確認した。
未解決の重大指摘はない。

## 科学上の確認

BB72例はBP-OSDを固定prior 0.08で一度構築し、評価するpも0.08であることを表示する。
depolarising例はI/X/Y/Zのカテゴリ雑音を保持し、X/Z独立sectorの合成をdecoderの選択として明示する。
phenomenological例は `PhenomenologicalModel(representation='difference', initial_boundary='clean', final_boundary='perfect')` の単一fault効果を列挙し、round-majorで平坦化した全ラウンドの差分をmatchingに渡す。
最終ラウンドはperfect測定なのでmeasurement fault座標を持たず、表示する失敗率は全Tラウンド実験の絶対確率である。
Steane例は全128状態から8 syndromeの最小重み訂正を決定的な順序で選び、同じdecoderをexact、direct MC、exact anchor付きBARに使う。
条件付きchainの重み平均と絶対 `P_L` は別の量として表示され、絶対 `P_L` の出所はexact、direct MC、BARに限られる。
回路例は物理single-fault kernelだけを指定し、Z/H/stabilizerの混合確率をゼロと明示する。
既存6例の主要なモデル、失敗定義、評価p、既定の標本数は維持され、CLI用のseed派生とquick縮小が追加された。

## 実行と境界

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_examples_real.py -q` は11 passed、18.70秒だった。
テストは全10例をquickで子process実行し、最終SUMMARYのkey集合と保存JSONを確認するが、統計的な数値の固定値はassertしない。
installed dev3 wheelの `steane_exact.py --quick --seed 20260930` を `-I` で再実行し、BAR区間のexact被覆は1/3で、3 rungそれぞれの真偽が表示されることを確認した。
完了メモの既定2/3、quick1/3と探索seed2での3/3は区別されており、全seedでの被覆保証として書かれていない。
研究リポジトリの指定root配下への `--out` を拒否するテストがあり、通常の出力先はOSの一時ディレクトリである。
toric系例に必要なextrasは `matching` と `codes` であり、mainの依頼書は `bd613e8` で実際の依存に合わせて修正済みである。
全suiteと全例の既定設定の再実行はこのレビューでは未実施であり、実測表はWP-F完了メモの記録として扱う。

## mainの回路構築修正 `aae4b0c` の確認

`src/mcmc4qec/circuit/model.py` の差分は理想命令の連続区間をprivate属性に保持し、各fault配置の注入時に元のnoise命令位置へfaultを足す変更である。
公開関数の引数、location列挙、カテゴリ雑音の確率、decoderとfailureの定義は差分で変更されていない。
重複target、2量子ビットfault、locationの選択を含む80配置の注入順序テストを確認した。
`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_model.py tests/test_circuit_pipeline.py tests/test_circuit_proposal.py tests/test_circuit_surface.py -q` は22 passed、9.44秒だった。
全2588列のH/L一致とquickの12.431秒から1.441秒への短縮はmainの実測記録にあるが、このレビューで独立再計測は未実施である。
