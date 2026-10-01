# WP-O 型注釈と PEP 561 マーカー

## 実装

`mcmc4qec.__all__` の公開名 65 件について、関数、コンストラクタ、戻り値の公開メソッドに引数と返り値の型注釈を追加した。
`Model`、`Noise`、`Decoder` の Protocol に状態ベクトル、NumPy generator、メタデータの型を明示した。
`Noise` と `Problem` は確率パラメータの型変数を共有し、`IndependentBitFlip` のようなスカラー専用ノイズも構造的に適合させた。
失敗条件の呼び出しとメタデータは `FailurePredicate` Protocol で表した。
`Problem` と各モデル・ノイズ・デコーダーの公開メソッド、`Result` と `EstimationResult` の JSON 往復にも注釈を追加した。
公開 `Result` と `EstimationResult` のメタデータ、診断、受理統計の辞書にもキー型を付けた。
モデルの `alphabets` は `Problem` が省略時に二値へ補うため Protocol 上で必須にせず、配列風の戻り値を許した。
`diagnose` は `Result` の iterable、`evaluate_convergence` は両集団に iterable または数値配列を受け付ける注釈にした。
`exact`、`direct_mc`、`sample_faulty` は `Problem` と確率引数を同じ型変数で結び、利用者定義ノイズのパラメータを型検査できる。
`estimate_logical_error` の ladder は実行時の `_coordinate` が数値または辞書に限定するため、その制約を維持した。
optional パッケージから構築した既存デコーダーオブジェクトはサードパーティの `decode` 契約が実行時に確認されるため、受け口のみ `Any` とし、`predict` の出力は `np.ndarray` とした。
空の `src/mcmc4qec/py.typed` を追加した。
既定引数、例外条件、提案確率、サンプリング処理は変更していない。

## 検証

K・N・L・M 統合後の rebase を行い、`A:\dev\mcmc4qec\.venv-dev4-source\Scripts\python.exe -m mypy --ignore-missing-imports src/mcmc4qec` は 24 ファイルで成功した。
`CSSCode.phase_flip_model()`、`mwpm_decoder(errors="Z")`、`bposd_decoder(errors="Z")`、新しい `faststep.py` の公開メソッドにも注釈を付けた。
`A:\dev\mcmc4qec\.venv-dev4-source\Scripts\python.exe -m pytest tests/test_typing.py -q` は利用者コードの mypy 成功・不正な確率引数の検出も含めて 3 passed だった。
ネストしたリストの CSS 行列、リストを返す decoder callback と直接実装した Decoder、リストのノイズ scales、`Problem` の構造的なノイズ適合を利用者コードで確認した。
`alphabets` を持たないカスタム二値モデル、タプルを確率パラメータとするカスタムノイズ、`Result` のタプル入力、数値配列の収束診断も利用者側 mypy で確認した。
不正なスカラー確率引数が `Problem.log_prob` と三つのサンプリング関数で検出されることも確認した。
`PhysicalFaultProposal.propose` の戻り値 `Proposal`、Stim DEM ファクトリの戻り値クラス、新しい `FastStepper` も公開署名検査の対象に加えた。
`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_typing.py -q` は mypy 不在時に 1 passed / 2 skipped であり、公開署名を常に検査できた。
同じ Python 3.11 の `-m pytest tests -q` は初回注釈後に 311 passed / 6 skipped、117.31 秒だった。
利用者コード検査を追加した後の `-m pytest tests/test_public_api.py tests/test_independent.py tests/test_pipeline.py tests/test_typing.py -q` は 20 passed / 2 skipped、24.57 秒だった。
最終 rebase 後の `-m pytest tests/test_phase_flip.py tests/test_faststep.py tests/test_circuit_kernels.py tests/test_typing.py -q` は 41 passed / 2 skipped、33.75 秒だった。
`tests/test_typing.py` は mypy が無い環境では型検査だけを skip し、公開署名の注釈漏れは常に検査する。
`--strict --ignore-missing-imports` では 252 errors が残り、内訳は `no-untyped-call` 139、`no-untyped-def` 56、`no-any-return` 27、`type-arg` 16、`attr-defined` 5、`operator` 3、`var-annotated` 2、`arg-type` 1、`call-overload` 1、`index` 1、`type-var` 1 だった。
`type-arg` の残りは `Problem` の内部参照でパラメータ型を省いた箇所などである。
主因は非公開の計算ヘルパーと、その呼び出し元の完全 strict 化を今回の公開 API 注釈の範囲に含めていないことである。
残りに NumPy の型推論と `ldpc`、`bposd`、`stim`、`pymatching` の不十分な型情報が含まれるため、通常の mypy では `--ignore-missing-imports` を用い、公開ラッパー自身の署名を検査する。
`docs/api_en.md` の decoder `errors` 引数と phase flip の記述は実装・注釈と一致した。
同文書の `p` はスカラーまたは辞書と説明するが、通常サンプリングはカスタム Noise の JSON 互換パラメータも受け付ける一方、BAR ladder はスカラーまたは辞書に限定するため、メインで説明を分ける必要がある。

## メインへの依頼

`pyproject.toml` に `[tool.setuptools.package-data]` として `mcmc4qec = ["py.typed"]` を追加し、wheel にマーカーを同梱する。
`[tool.mypy]` に `python_version = "3.11"`、`ignore_missing_imports = true`、`files = ["src/mcmc4qec"]` を加え、CI の Python 3.11 型検査 job で mypy を install して `python -m mypy src/mcmc4qec` と `python -m pytest tests/test_typing.py -q` を実行する。
`docs/api_en.md` の確率パラメータ説明を通常サンプリングと BAR ladder で分ける。

## 未実施

最終 rebase 後の全 suite はメインが実行するため、この WP では未実施である。
上記の 311 passed / 6 skipped は統合前の初回注釈時の実測である。
`--strict` の全項目解消と optional ライブラリの外部 stub 作成は未実施である。
