# 回路効果差分・明示群Hの独立レビュー

2026-10-15に未コミット変更と小仕様を独立にレビューした。
実装コードは変更していない。
対象範囲で修正必須の問題は見つからなかった。

## 確認事項

物理locationの排他的カテゴリ表現は維持され、差分効果は旧ラベルと新ラベルのtable参照をXORする。
専用stepは組み込みmodel/noiseの厳密な型一致かつ既定failureだけに限定され、派生型と独自failureは一般経路へ戻る。
明示群は空群・重複・範囲外を拒否し、群内のchannelと順序付きfault alphabetの一致を要求する。
群外locationはHで変更せず、群選択とrelocation/relabel枝は状態に応じて再正規化しない。
既存ClusterExchangeを再使用することで、実行できない枝と同じラベルへの再ラベルを含む自己遷移確率が集計される。
非一様location率・条件付きfault率・零supportは完全な密度と共有failureのMH判定で処理される。
Hだけでは群ごとの占有数が保存されて一般に可約であり、有限例のH+OBFの連結性とlazyの自己遷移は詳細釣合いとは別に検証される。
この有限例の連結性を実符号の失敗集合全体へ一般化しない。

## 実行確認

`A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe`を用い、`PYTHONDONTWRITEBYTECODE=1`で各作業ディレクトリ自身のsourceを参照した。
回路worktreeの`tests/test_circuit_delta_cluster.py tests/test_circuit_kernels.py tests/test_faststep.py`は42 passed、32.13秒だった。
mainへの統合後の`tests/test_circuit_delta_cluster.py`は14 passed、3.39秒だった。
この受入テストは小さい全状態の効果差分・提案正規化・順逆確率・失敗条件付き詳細釣合いと、同seedの全保存状態・受理統計・最終RNG状態を検証する。
mainのZ逆分布をfailure候補のみに遅延する変更は、回路physical/Hの提案分岐と干渉せず、上記統合後テストも成功した。
全suiteと独立の速度測定は未実施であり、実装メモの速度数値を本レビューで再測定したとは扱わない。
実符号での混合改善・被覆校正・一般の既約性は今回の検証対象外である。
