# WP-O 型注釈と PEP 561 マーカー

## 実装

`mcmc4qec.__all__` の公開名 65 件について、関数、コンストラクタ、戻り値の公開メソッドに引数と返り値の型注釈を追加した。
`Model`、`Noise`、`Decoder` の Protocol に状態ベクトル、NumPy generator、メタデータの型を明示した。
`Problem` と各モデル・ノイズ・デコーダーの公開メソッド、`Result` と `EstimationResult` の JSON 往復にも注釈を追加した。
optional パッケージから構築した既存デコーダーオブジェクトはサードパーティの `decode` 契約が実行時に確認されるため、受け口のみ `Any` とし、`predict` の出力は `np.ndarray` とした。
空の `src/mcmc4qec/py.typed` を追加した。
既定引数、例外条件、提案確率、サンプリング処理は変更していない。

## 検証

`A:\dev\mcmc4qec\.venv-dev4-source\Scripts\python.exe -m mypy --ignore-missing-imports src/mcmc4qec` は 23 ファイルで成功した。
`A:\dev\mcmc4qec\.venv-dev4-source\Scripts\python.exe -m pytest tests/test_typing.py -q` は 2 passed だった。
`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_typing.py -q` は 1 passed / 1 skipped であり、mypy 不在時にも公開署名を検査できた。
同じ Python 3.11 の `-m pytest tests -q` は 311 passed / 6 skipped、117.31 秒だった。
`tests/test_typing.py` は mypy が無い環境では型検査だけを skip し、公開署名の注釈漏れは常に検査する。
`--strict --ignore-missing-imports` では 234 errors が残り、内訳は `no-untyped-call` 135、`no-untyped-def` 54、`no-any-return` 26、`type-arg` 6、`attr-defined` 5、`operator` 3、`var-annotated` 2、`arg-type` 1、`call-overload` 1、`type-var` 1 だった。
主因は非公開の計算ヘルパーと、その呼び出し元の完全 strict 化を今回の公開 API 注釈の範囲に含めていないことである。
残りに NumPy の型推論と `ldpc`、`bposd`、`stim`、`pymatching` の不十分な型情報が含まれるため、通常の mypy では `--ignore-missing-imports` を用い、公開ラッパー自身の署名を検査する。
`docs/api_en.md` は主に意味と代表引数を記載し、列挙した個々の Python 署名との矛盾は現時点で見つからなかった。

## メインへの依頼

`pyproject.toml` に `[tool.setuptools.package-data]` として `mcmc4qec = ["py.typed"]` を追加し、wheel にマーカーを同梱する。
`[tool.mypy]` に `python_version = "3.11"`、`ignore_missing_imports = true`、`files = ["src/mcmc4qec"]` を加え、CI の Python 3.11 型検査 job で mypy を install して `python -m mypy src/mcmc4qec` と `python -m pytest tests/test_typing.py -q` を実行する。
統合後の K、N、L の新しい公開 API と新規モジュールについては、O の rebase 後に注釈と検査を追加する。

## 未実施

統合後 rebase と、その後の mypy・全 suite はまだ未実施である。
`--strict` の全項目解消と optional ライブラリの外部 stub 作成は未実施である。
