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

### WP-P BAR 区間の被覆と論文との整合

目的。dev4 の被覆不足（20 seed 中 13）の原因を bias と分散に切り分け、論文の手順（cross-chain の誤差棒、5·IAT burn-in、多数 chain）をライブラリで再現して被覆を測り、ライブラリの既定と公開文書を論文の主張と矛盾しない形にする。

担当ファイル。`src/mcmc4qec/estimation.py`（誤差評価法の追加のみ）、`src/mcmc4qec/diagnostics.py`（反復 Geyer IAT が無ければ追加）、`benchmarks/bar_sensitivity.py`（拡張）、`benchmarks/bar_paper_protocol.py`（新規）、`tests/test_bar_uncertainty.py`、`docs/bar_sensitivity_ja.md`（追記）、`docs/paper_consistency_ja.md`（新規）、`docs/wp/P_ja.md`。`examples/workflows/pl_curve.py` と `notebooks/02_pl_curve_with_bar.ipynb` の変更案は完了メモに書く（反映はメイン）。

作業内容。

1. **BAR の照合の再確認。** `RIMC_RESEARCH_ROOT` を設定した `tests/test_crossval_research.py` の BAR 照合と、`bennett_log_ratio` の Fermi 関数の形が論文 eq:bar と一致することを確認し、結果を完了メモに書く。不一致があればここで止めてメインに報告する。
2. **bias と分散の切り分け（dev4 の領域、toric d=3、p=0.22）。** 同じ seed 2026 と基準 20 seed で、保存数を 600 → 2400 → 9600（10 分以内の範囲）と伸ばしたときの点推定と exact の差の推移を表にする。差が 1/sqrt(N) で縮むなら分散、縮まないなら bias と判断し、bias の場合は burn-in（固定 180、5·IAT、trace の半分）と chain 数（4、16、50）のどちらが効くかを調べる。
3. **誤差評価法の追加。** `estimate_logical_error` に `uncertainty="block_bootstrap"`（既定、現状のまま）と `uncertainty="cross_chain"` を追加する。`cross_chain` は、各 chain を独立な実現とみなし、chain ごとに BAR の log ratio（または各 rung の chain 平均から作る統計量）を求め、chain 間のばらつきから標準誤差を出す。論文の cross-chain standard error の定義（Appendix の eq:chain-se）に合わせ、anchor の log 分散は従来どおり独立に加える。chain 数が 2 未満なら `ValueError`。返り値の `uncertainty_method` にどちらを使ったかを残す。既定の挙動と既存テストの数値は変えない。
4. **論文の手順の再現（benchmarks/bar_paper_protocol.py）。** toric d=3（exact が取れる）で、論文の領域の ladder（例えば `[0.10, 0.07, 0.05, 0.03]`、exact anchor と MC anchor の両方）と dev4 の領域の ladder `[0.30, 0.26, 0.22]` に対し、次の 4 構成で被覆を 20 seed 以上で測る。(i) 現行既定（4 chain、burn-in 180、block bootstrap）。(ii) 現行既定の chain を cross_chain 誤差に替えたもの。(iii) 論文手順（K=50 chain、burn-in 5·IAT、cross_chain、収束規則の判定を併記）。(iv) (iii) の chain 数を 16 に減らしたもの。各構成で、被覆率と Wilson 区間、平均区間幅、点推定の平均と exact の差、収束規則の合格数を表にする。全体で 10 分を超える構成は保存数を減らし、その旨を書く。
5. **論文との整合表（docs/paper_consistency_ja.md）。** 論文の Setup、conventions、splitting、results の各節から、ライブラリの機能・既定・文書に関係する主張を抜き出し（行番号つき）、それぞれについて「ライブラリの既定と同じ／違う（どう違う）／ライブラリでは未検証」を書く。少なくとも、chain 数、burn-in の規則、誤差棒の方法、カーネルの既定（Z+H と Z+PT）、初期状態、収束規則、ladder の刻み、評価した p の領域、BAR の式、anchor の方法を含める。論文を変えない。
6. **利用者向けの指針の更新。** `docs/bar_sensitivity_ja.md` に今回の表を追記し、「どの設定なら名目に近い被覆になったか」「どの領域では短い chain では足りないか」を書く。README の制約段落（BAR の区間の仮定）と `examples/workflows/pl_curve.py` の docstring・出力メッセージ・notebook 02 の説明の修正案を完了メモに書く。既定設定を変える提案（例えば chain 数や cross_chain の既定化）は、根拠の表とともに所有者判断に回す。
7. **テスト（tests/test_bar_uncertainty.py）。** (a) 合成の独立 chain（既知の分散）で `cross_chain` の標準誤差が理論値と一致する。(b) `cross_chain` と `block_bootstrap` が同じ点推定を返す。(c) chain 数 1 で `cross_chain` が `ValueError`。(d) 列挙できる小問題で 10 seed 程度の反復により `cross_chain` の区間被覆が極端に低くないこと（60 秒以内、閾値は緩く）。(e) `uncertainty` の不正値で `ValueError`。

受入条件。照合の再確認、bias と分散の切り分け表、4 構成 × 2 領域の被覆表、`docs/paper_consistency_ja.md`、テスト (a)〜(e)、既存テストの数値が変わらないこと。原因を 1 つに絞れない場合は候補と各根拠を書く。

依存。最終の数値は WP-Q の merge 後の main で取り直す（第 2.3 節）。


