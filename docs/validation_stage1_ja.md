# 最初の bit-flip 到達点の検証記録

2026-09-30、Python 3.11.9 / Windows、NumPy 2.4.6 / pytest 9.1.1。
現在の実装はさらに拡張されている。この記録は保存した `0.1.0.dev0` wheel の履歴である。

- core-only の隔離環境: **43 passed, 3 skipped**。PyMatching / ldpc / Stim / SciPy 不在を確認。
- optional decoder 環境: **46 passed**。PyMatching 2.4.0、ldpc 2.4.1。
- 両方でsource treeのpythonpathを無効にし、venvのsite-packagesからのimportを確認。
- 3-bit repetition例: exact P_L=0.15625、MC=0.1624、Wilson95%=[0.155301176,0.169758100]。
  exact E[w|F]=2.1、MCMC=2.092。JSON往復で全保存状態が一致。
- wheelの8個のPythonソースが同時点のsourceとbyte単位一致。
- wheel SHA256: `08dd8cf8a850beebdbc07b78d9715efd90b5ecc3f43f805656756500db158b49`。

チェック対象は詳細釣合い、一般相関ノイズのMH、独自failure共通性、棄却保持、seed、
端点・無効入力、外部decoder出力意味など。大きい符号の混合や性能を保証する検証ではない。
remote CI は未実行。現在版の検証は `validation_initial_ja.md` を参照。
