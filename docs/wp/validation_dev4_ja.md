# dev4 検証記録

## Phase 0

2026-10-01、main とローカル追跡参照 origin/main は `c6cff9232cff3046d4643d2adbb95baba02d9a9b` で一致した。
研究リポジトリ `A:/dev/RIMC` は `69efcfcc86af3bf24ca977a098dab0f348601aff`、`git status --short` は空だった。
依頼書だけが未追跡で、既存実装に未コミット変更はなかった。
依頼書・進捗表・担当指示を `b8fde01` に保存した。

| 環境 | コマンド | 結果 | pytest 秒 |
| --- | --- | --- | ---: |
| 指定 Python 3.11 | `python -m pytest tests -q --junitxml=output/dev4-phase0.xml` | 310 passed / 5 skipped | 119.00 |
| Python 3.11 source venv（notebook込み） | `python -m pytest tests -q --junitxml=output/dev4-phase0-full.xml` | 314 passed / 4 skipped | 166.23 |

上の Python は `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` の絶対パスで実行した。
skip は研究 checkout を明示指定していない照合4件と、nbformat/nbclient がないための notebook モジュール全体1件だった。
前回の314 passed / 4 skippedとの差は notebook4件が収集されなかったためであり、今回の310件だけでは notebook の成功を主張しない。
指定 Python 3.11 から `--system-site-packages` で `.venv-dev4-source` を作り、nbclient 0.11.0、nbformat 5.11.1、build 1.6.1、mypy 2.3.1 をその隔離環境へ導入した。
既存のグローバル環境のパッケージは変更していない。
同環境の絶対パス `A:/dev/mcmc4qec/.venv-dev4-source/Scripts/python.exe` で notebook を含む基準全 suite が成功した。
Windows の ZeroMQ が補助 selector thread を利用する警告が1件出たが、notebook4件は成功した。
この source 検証環境は既存依存を共有するため、Phase 2 の core/optional installed-wheel 用に要求された新規 venv とは別物である。

## 追加の基準確認

`RIMC_RESEARCH_ROOT=A:/dev/RIMC` と `PYTHONDONTWRITEBYTECODE=1` を設定し、指定 Python の `-m pytest tests/test_crossval_research.py -q -k live_research --junitxml=output/dev4-phase0-live.xml` は4 passed / 15 deselected、1.25秒だった。
`.venv-dev4-source/Scripts/python.exe -m mypy --ignore-missing-imports src/mcmc4qec` は23 source filesで成功した。
同じ環境の `-m mypy --strict --ignore-missing-imports src/mcmc4qec` は21 filesで533 errorsとなり、詳細は `output/dev4-phase0-mypy-strict.txt` に保存した。
未注釈の関数が多いため、通常設定の成功だけを公開 API の注釈完了とは扱わない。

## K の共有高速経路修正

K 担当の小仕様と受入テストを先に確認し、main が `tests/test_phase_flip.py::test_phenomenological_phase_flip_check_history_and_fastpath` を K worktree で実行した。
phase flip のデータ確率行が期待 `[0.8,0.2]` に対して `[0.8,0.0666667]` となり、1 failed、0.51秒だった。
main 管理の `fastpath.py` の alphabet 選択を depolarizing のみ4、それ以外2に変更し、main `23bd178`、K 枝への同内容 cherry-pick `3609478` に保存した。
K worktree の同 node と `tests/test_fastpath.py` は14 passed、2.81秒だった。
K の実装全体と独立レビューは後述の統合時点で完了した。

## 統合・wheel・CI

各 WP のレビュー後に K → N → L → M → O の順に統合し、各段階の全 suite と時間をここへ追記する。

| 統合 | source venv コマンド | 結果 | 秒 |
| --- | --- | --- | ---: |
| K、main `c550cdf` | `python -m pytest tests -q --junitxml=output/dev4-after-k.xml` | 330 passed / 5 skipped | 149.98 |
| N | `python -m pytest tests -q --junitxml=output/dev4-after-n.xml` | 345 passed / 5 skipped | 122.42 |
| L、main `a7fc5e6` | `python -m pytest tests -q --junitxml=output/dev4-after-l.xml` | 354 passed / 5 skipped | 144.72 |

K後のskipは研究checkout未指定の照合5件で、Windows ZeroMQの補助selector警告1件が出た。
installed wheelとremote CIは未実施。

## 基準のファイル別時間

基準全 suite の JUnit testcase 時間を classname ごとに加算した上位は次のとおり。

| ファイル相当の classname | 秒 |
| --- | ---: |
| `tests.test_examples_workflows` | 29.469 |
| `tests.test_independent` | 17.770 |
| `tests.test_notebooks` | 17.076 |
| `tests.test_pipeline` | 14.543 |
| `tests.test_decoders` | 14.362 |
| `tests.test_acceptance` | 13.963 |

これは各テストのsetup/call/teardown時間の合計であり、pytest全体の収集・起動費用を含む経過時間とは区別する。
統合後の増分は同じ依存環境と同時期の比較実行も用いて判定する。
