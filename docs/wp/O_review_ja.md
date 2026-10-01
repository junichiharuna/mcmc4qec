# WP-O 独立レビュー

## 判定

WP-O の統合前レビューは承認する。
K・N・L・M 統合後の `wp/o` HEAD `93171ec` を `5825af4` と比較し、公開型の主要な利用例と実行時の意味を確認した。

## 指摘と対応

初回の型注釈では、ネストしたリストの CSS 行列、リストを返す decoder callback、スカラー専用 `IndependentBitFlip` と `Noise` Protocol の組み合わせが利用者側 mypy で失敗したため、owner が `ArrayLike` と `Noise`・`Problem` の型変数を導入した。
`Model` の `alphabets` を省いた二値モデル、リストを返す独自 decoder とノイズ、タプルの独自確率パラメータ、`Result` の iterable、数値配列の収束診断、リストの初期状態も、実行時に許す入力に合わせて注釈を修正した。
`CallableFailure` と直接実装した failure predicate では、実行時に許す NumPy の `np.bool_` を mypy が拒んだため、返り値の型を広げて利用者コード検査を加えた。
`Result` と `EstimationResult` の公開辞書フィールドには文字列キー型を追加した。
型検査用の独自ノイズ例は、サンプル生成と対数確率が一致する Bernoulli 分布に修正した。
これらの指摘に未対応の阻害事項は残っていない。

## 独立した検証

`mcmc4qec.__all__` は重複のない 65 名だった。
公開関数、公開クラスのコンストラクタと公開メソッド、返り値として現れる `Proposal`、Stim DEM 型、内部 `FastStepper` の署名は `tests/test_typing.py` の検査対象に入っている。
source 環境と optional 環境の両方で `python -m mypy --ignore-missing-imports src/mcmc4qec` は 24 ファイル成功した。
source 環境の `python -m pytest tests/test_typing.py -q` は 3 passed で、独立に作成した `CallableFailure(lambda s, p, t: np.any(p != t), identifier="mismatch")` の利用者ファイルも mypy で成功した。
`python -m pytest tests/test_phase_flip.py tests/test_faststep.py tests/test_circuit_kernels.py tests/test_typing.py -q` は `ffa3abb` 時点で 43 passed、34.28 秒だった。
最後の `93171ec` は型注釈と型検査用例だけの変更で、focused tests の再実行は行わず `tests/test_typing.py` を再実行した。
`python -m mypy --strict --ignore-missing-imports src/mcmc4qec` には 20 ファイルで 252 errors が残り、`docs/wp/O_ja.md` の件数と内訳に一致した。
残数の主因は非公開ヘルパーの未注釈とその呼び出しであり、公開 API を対象とした通常の型検査は成功した。

## 実行時の差分

`5825af4` との関数 AST 比較では、注釈と型検査専用 `cast` を除く差分は局所変数の型宣言と `problem.model.stabilizers` から `getattr(problem.model, "stabilizers")` への書き換えだけだった。
後者は同じ必須属性を取得し、欠落時の例外を補う変更もないため、通常の実行経路、既定値、提案確率、受理判定の意味は変わらない。
統合後の全 suite と wheel・CI はメインの検証対象であり、このレビューでは未実施である。
