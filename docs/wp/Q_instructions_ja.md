依頼書 `docs/dev_request_2026-10-01_bar_speed.md` 全体と AGENTS.md を読み、以下の担当 WP を遂行する。
思考は英語、報告と日本語文書は日本語1文1行、コードコメント/docstringは英語とする。
作業は指定 worktree のみで行い、共有ファイルと研究repoを変更しない。
メインは共有文書・version・統合・wheel・CIを担当する。
担当は小仕様、受入試験、実装の順に進め、完了メモに実コマンド、結果、未実施、メインへの依頼を残す。
commitは許可され、pushは禁止する。
commitには `Co-Authored-By: OpenAI Codex <noreply@openai.com>` と `Claude-Session: not applicable (Codex dev5 goal 01a0f6fd-6d4c-7f30-ae0e-8cdd470e778a)` を付ける。
Pythonは指定3.11またはそこから作成した `A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe` の絶対パスを使う。
研究参照時は `PYTHONDONTWRITEBYTECODE=1` と `RIMC_RESEARCH_ROOT` を設定し、研究rootは環境で与え、ファイルに絶対パスを直書きしない。
重い計測はメインに連絡してから実行し、他の計測との競合を避ける。
上限は各test file60秒、suite5分、benchmark invocation10分とする。
Pの最終計測はQ統合後mainで取り直すため、Q前の大規模な最終表の計測は控え、実装・軽量試験・計測仕様を先に固める。
追加のagentはメインの空き枠確認前には起動しない（環境の同時実行上限は4体）。
論文は観測量平均のcross-chain SEを定義しており、full BAR end-to-endの数値実験は未実施と記すため、BAR誤差伝播はその定義に沿ったライブラリ側の適用として説明する。
現行論文のproduction kernelはZ+Hであり、研究runnerのAPI既定Z+PTと区別する。
Pの同一軌道上での誤差法比較は実際に同じ保存軌道を再利用し、短いseedの結果を見て設定を選び直さない。
長い保存数・多数chainでは必要に応じてseedを事前に固定した分割invocationを使い、全seed結果を欠落なく集計する。
残差の1/sqrt(N)らしさだけでbiasの有無を証明しない。
研究側のminimum/maximum logical basisがtoric d=3では同一になる点を明示し、多初期値規則を未検査のまま合格にしない。
Pはestimation/diagnostics/bar benchmarks、Qはfaststep/kernels/decode_cache/adapters/bench_stepに限定する。

### WP-Q 速度差の残りと性能の公開記述

目的。研究 runner との差を toric でも 2 倍以内に近づけ、README に実測に基づく性能の節を加える。

担当ファイル。`src/mcmc4qec/faststep.py`、`src/mcmc4qec/kernels.py`（必要最小限）、`src/mcmc4qec/decode_cache.py`、`src/mcmc4qec/adapters.py`（decoder 出力の検証を 1 回にする場合）、`benchmarks/bench_step.py`、`tests/test_faststep.py`（追加）、`docs/performance_ja.md`（追記）、`docs/wp/Q_ja.md`。

作業内容。

1. `docs/performance_ja.md` の WP-N 節の profile に従い、残る主因を潰す。(a) 局所確率表を状態と一緒に内部で保持し、Z の順向き分布と逆向き確率の正規化を 1 ステップ 1 回にする。(b) decoder adapter の出力検証を cache hit では省き、miss のときだけ行う（BB72 の主因）。(c) `FastStepper.attempt` 内の Python レベルの候補処理を減らす。適用条件（組み込みの線形モデルと積ノイズ、標準 failure）は変えない。
2. 等価性テストを維持・追加する。参照経路と専用経路の提案分布・受理確率を全状態・全近傍で比較し、同じ seed で同じ軌道と同じ乱数消費になることを、toric d=3 と小さい categorical 問題で確認する。
3. `benchmarks/bench_step.py` で toric d=5、d=7、BB72 の p=1e-2 を研究 runner と比較し、`docs/performance_ja.md` に追記する。同じ条件で 2 回以上測り、ばらつきを書く。2 倍以内に届かない符号は profile と残る原因を書く。
4. README の「Performance」節の案を完了メモに書く。内容は、専用経路の適用条件、toric d=5 / d=7 / BB72 の step/s の実測（Windows、Python 3.11、CPU 名）、研究 runner との比（参照実装であり研究 runner より遅いこと）、`benchmarks/bench_step.py` の実行方法（`RIMC_RESEARCH_ROOT` が必要で、研究コードが無い環境ではライブラリ側だけ測ること）、数値は環境で変わること。`README_ja.md` の同じ節の案も書く。`examples/README.md` の実測時間の列が dev4 の値のままで良いか確認し、変わった例は再測定値を書く。

受入条件。等価性テストが通ること、ベンチマーク表（2 回以上）、README 節の案、既存テストが全部通ること、公開 API の既定の挙動が変わらないこと。

依存。なし。


