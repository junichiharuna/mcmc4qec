# mcmc4qec 開発依頼書：dev5（BAR 区間の被覆と論文との整合、速度と性能の公開記述）（Codex goal 用）

作成日 2026-10-01。対象リポジトリは `junichiharuna/mcmc4qec`（private）。
この文書を Codex の goal としてそのまま渡す。メインモデルは astra、サブエージェントは gpt-sol を使う。
前回までの依頼書 `docs/dev_request_2026-09-30.md`（WP-A〜E）、`docs/dev_request_2026-09-30_examples.md`（WP-F〜J）、`docs/dev_request_2026-10-01.md`（WP-K〜O）と同じ運用で進める。
今回の WP は P と Q と呼び、`docs/wp/P_ja.md` のように前回までの名前と衝突しないようにする。
進捗は `docs/wp/PROGRESS_dev5_ja.md` のチェックリストで管理し、中断と再開はこのファイルを起点にする。

## 0. 依頼の要約

dev4（0.1.0.dev4）で、公開前に確認すべき科学的な問題が 2 つ残った。

1. **BAR 区間の被覆不足。** `examples/workflows/pl_curve.py` の既定設定（toric d=3、ladder `[0.30, 0.26, 0.22]`、4 chain、保存 600、burn-in 180、block bootstrap の block 8）で、p=0.22 の BAR 95% 区間が exact 真値 0.6027 を含んだのは 20 seed 中 13 だった（`docs/bar_sensitivity_ja.md`）。block を長くしても seed 2026 の点推定は真値を外したままで、分散の過小評価だけでは説明できない。論文（`RESEARCH/paper/main.tex`）は誤差棒を block bootstrap ではなく独立 chain 間のばらつきから取り、K=50 chain、burn-in 5·IAT、p は 1e-1 以下で評価している。ライブラリの既定と論文の手順の違いが被覆不足の原因かどうかを切り分け、ライブラリの既定と公開文書を論文の主張と矛盾しない形にする（WP-P）。
2. **速度と性能の記述。** 専用経路（dev4 の WP-N）の後も研究 runner より toric d=5 で 3.2 倍、d=7 で 2.5 倍、BB72 で 2.0 倍遅い（`docs/performance_ja.md`）。公開には支障ないが、README に性能の記述がない。残る差を詰め、README に実測に基づく性能の節を加える（WP-Q）。

成果物は次の 4 つ。

1. main に統合された実装・テスト・文書（全 tests 緑、wheel を別環境に入れて例が動く、remote CI 全 job 成功）。
2. 各 WP の完了メモとレビュー記録（日本語、`docs/wp/P_ja.md`、`Q_ja.md`、`P_review_ja.md`、`Q_review_ja.md`）。
3. 更新された `pyproject.toml`（version `0.1.0.dev5`）、`CHANGELOG.md`、`AGENTS.md`、`README.md` / `README_ja.md`、`docs/api_en.md`、`examples/README.md`、`docs/handoff/IMPLEMENTATION_STATUS.md` の追記。
4. 最終報告（日本語、`docs/wp/final_report_dev5_ja.md`）。実行した検証だけを合格として書く。

## 1. 前提と制約

- ライブラリのリポジトリは `C:\dev\mcmc4qec`（研究室 PC）または `A:\dev\mcmc4qec`（自宅 PC）。以下 `LIB` と書く。
- 研究リポジトリ RIMC は `C:\dev\RIMC` または `A:\dev\RIMC`。以下 `RESEARCH` と書く。**読み取り専用**で、1 ファイルも変更しない。論文 `RESEARCH/paper/main.tex` も変更しない。runner の既定（Z+PT）も変えない。`git status` が clean のまま終わること。
- 出発点は main の最新（0.1.0.dev4、MIT ライセンス追加と研究パスの直書き除去の後）。全 suite は optional 依存込みで約 358 passed（約 2.5 分）。
- Python は 3.11 の絶対パスを使う（`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe`）。`python3` は使わない。
- 研究コードを読み取り専用で import する benchmark と照合テストは、環境変数 `RIMC_RESEARCH_ROOT`（benchmark は `MCMC4QEC_RESEARCH` も可）に `RESEARCH` を設定して動かす。例・テスト・benchmark に研究リポジトリの絶対パスを直書きしない。
- 計算は軽いものだけ。1 テストファイルは 60 秒以内、全 suite の増分は 60 秒以内で全 suite 5 分以内を保つ。被覆評価とベンチマークは 1 本 10 分以内とし、`benchmarks/` に置いてテストからは呼ばない。クラスタ投入、巨大 sweep、長時間ジョブはしない。
- PyPI 等への publish、リポジトリの公開化、著者の所属・DOI の確定は**しない**。ライセンスは MIT で確定済みなので変更しない。
- 公開既定 Z 0.7 / H 0.3 / cluster_k=2 / 1 chain / lazy 0.05 は変えない。既存の公開 API の既定引数と返り値の意味も変えない。追加は後方互換な keyword 引数か新しい名前で行う。`estimate_logical_error` の既定の誤差評価法を変える提案は、根拠の表とともに完了メモに書き、所有者判断に回す。
- 日本語文書は 1 文 1 行で書く（文の途中で改行しない）。README（英語）、`examples/README.md`、docstring、コメントは英語。
- 数値の一致、性能、テスト成功は実行して確認してから書く。未実行のものは「未実施」と明記する。
- 着手前に次を読む。`LIB/README.md`、`LIB/AGENTS.md`、`LIB/docs/api_en.md`、`LIB/docs/bar_sensitivity_ja.md`、`LIB/docs/performance_ja.md`、`LIB/docs/convergence_ja.md`、`LIB/docs/crossval_research_ja.md`、`LIB/docs/wp/final_report_dev4_ja.md`、`LIB/docs/wp/M_ja.md`、`LIB/docs/wp/N_ja.md`、`LIB/src/mcmc4qec/estimation.py`、`LIB/src/mcmc4qec/faststep.py`、`LIB/src/mcmc4qec/convergence.py`、`LIB/benchmarks/`、`RESEARCH/paper/main.tex` の Setup 節と Appendix の conventions 節（burn-in 5·IAT、K=50 chain、cross-chain standard error、収束規則）と splitting の節（BAR の式 eq:bar、Fermi 関数、ladder）、`RESEARCH/src/splitting_pl.py`。

## 2. モデル構成と並列運用

### 2.1 役割

- **メイン（astra）**: 全体の指揮、Phase 0 の準備、ブランチの統合、共有ファイルの編集、最終検証と報告。自分で大きな実装はしない。
- **サブエージェント（gpt-sol）**: WP ごとに 1 体を同時に起動する（2 体）。WP-P は被覆評価の計算（benchmark 実行）と実装（誤差評価法の追加）を分けて最大 2 体追加してよい。同時実行の上限は 6 体。
- **レビュー担当（gpt-sol）**: 各 WP が完了したら、別のサブエージェントに差分を敵対的にレビューさせる。WP-P では、被覆率の表が seed や設定の選び直しで作られていないこと、論文の手順の再現が論文の記述と一致していること、bias と分散の切り分けが数値で支持されていることを確かめる。WP-Q では高速経路の等価性と README の数値が実行記録と一致することを確かめる。指摘は WP 担当が対応し、メインが最終判断する。

### 2.1.1 reasoning effort

| 役 | effort | 理由 |
| --- | --- | --- |
| メイン（astra） | high | 指揮・統合・裁定 |
| gpt-sol WP-P | high | 推定量の bias と分散の切り分け、論文との整合は間違えると公開文書の主張がずれる |
| gpt-sol WP-Q | high | 高速経路は同一 seed 同一軌道を保つ必要がある |
| レビュー担当（WP-P） | xhigh | 統計的な主張の穴を探す 1 回きりの仕事 |
| レビュー担当（WP-Q） | high | |

役ごとに effort を変えられない環境では全体を high にする。

### 2.2 作業の分離

- WP ごとに git worktree を作る。`git worktree add ../mcmc4qec-wt/<wp> -b wp/<wp>`（`<wp>` は `p`、`q`）。作業は worktree 内だけで行う。
- 共有ファイル `src/mcmc4qec/__init__.py`、`pyproject.toml`、`CHANGELOG.md`、`README.md`、`README_ja.md`、`AGENTS.md`、`docs/api_en.md`、`examples/README.md`、`.github/workflows/tests.yml` は WP 担当が直接編集しない。追加したい公開名、README の節の案、行の案は完了メモに書き、メインが統合時に反映する。
- WP-P は `estimation.py` と `benchmarks/bar_sensitivity.py`、WP-Q は `faststep.py`・`kernels.py`・`decode_cache.py`・`benchmarks/bench_step.py` を担当し、互いのファイルに触らない。
- WP は完了時に `docs/wp/<WP>_ja.md` を書く。内容は、実装したこと、実行した検証（コマンドと結果の数値）、未実施、メインへの依頼。
- コミットは worktree のブランチに自由に行う。メッセージは英語で 1 行要約。push はメインが最終検証後に main だけ行う。

### 2.3 統合の順序

メインは Q → P の順に main へ merge する。
WP-P の被覆評価は chain を多く長く走らせるので、WP-Q の高速経路が入った main で最終の数値を取り直し、Q の merge 前に取った数値は「Q 前」と注記して残す。
各 merge の後に `python -m pytest tests -q` を通す。

## 3. 科学的な注意（全 WP 共通、レビューで必ず確認する）

1. **被覆は反復 seed で数える。** 1 回の実行で主張しない。seed や設定を選び直して被覆を「作らない」。被覆率には二項の Wilson 区間を併記し、名目との差を過大に解釈しない。
2. **bias と分散を分けて書く。** 区間が真値を外す原因は、(a) 点推定の bias（chain が短い、burn-in 不足、混合不良、BAR の self-consistent 解の収束）と、(b) 区間幅の過小評価（block 長、chain 数、anchor の分散の扱い）の 2 種類がある。どちらがどれだけ効いているかを、同じ軌道に対する異なる誤差評価と、chain 長を伸ばしたときの点推定の収束で切り分ける。
3. **論文の手順を再現するときは論文の記述に従う。** K=50 chain、burn-in 5·IAT（IAT は反復 Geyer 推定、収束しなければ trace の半分で打ち切り）、誤差棒は chain 平均の間のばらつき、収束規則（後半と前の 1/4 が 3σ 以内、2 つの初期化が 3σ 以内）。ライブラリの既定（4 chain、固定 burn-in、block bootstrap、Z+H）との違いを表にする。研究 runner の既定が Z+PT であることも区別して書く。
4. **p の領域を区別する。** 論文は p ≤ 1e-1 で評価しており、p=0.22 の toric d=3（失敗確率 0.6）は論文が主張の対象にしていない領域である。論文の領域（exact が取れる d=3 で p=0.10 以下の ladder）と、dev4 で問題が出た領域の両方で被覆を測り、どちらで何が起きるかを分けて書く。
5. **BAR の式と研究コードとの一致。** `bennett_log_ratio` が論文の eq:bar（Fermi 関数 h(t)=1/(1+t)）と `RESEARCH/src/splitting_pl.py` の解と一致することは既存の照合テストにある。被覆の議論を始める前に、その照合が現在の main でも通ることを確認する。
6. **診断は証明ではない。** 収束規則を満たしても収束・エルゴード性・正しさの証明ではない。出力と文書にその旨を残す。
7. **高速経路の等価性。** 速度改善は参照経路と同じ提案分布、同じ受理確率、同じ seed で同じ軌道（状態列、受理列、lazy 列、kernel 選択列、乱数消費）を保つ。棄却と lazy は chain に残す。
8. **研究結果の再現を主張しない。** 論文は「in preparation」とだけ書く。論文の図表の再現とは書かない。

## 4. Phase 0（メインが最初に行う、30 分以内）

1. `LIB` の main が `origin/main` と一致し、作業ツリーが clean で、全 suite が通ることを確認する（件数と秒数を記録）。
2. `RIMC_RESEARCH_ROOT` を設定して `python -m pytest tests/test_crossval_research.py -q` を実行し、研究コードとの照合（BAR を含む）が通ることを確認する。
3. `docs/wp/PROGRESS_dev5_ja.md` を作る。Phase 0、各 WP の実装・レビュー・対応、Phase 2 の各項目を 1 行 1 項目のチェックリストにし、項目が終わるたびに `[x]` と日時を書く。
4. `docs/wp/` に、この文書の WP 節をもとに各 WP の指示文をサブエージェントに渡す。
5. worktree を 2 つ作り、2 体を同時に起動する。

## 5. 作業パッケージ

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

## 6. 例と benchmark の共通規約

`examples/` と `benchmarks/` の新しいスクリプトは `docs/dev_request_2026-09-30_examples.md` 第 3 節の規約に従う。
`argparse` で `--quick`、`--seed`、`--out` を受け付け、既定の出力先は `tempfile.gettempdir()/mcmc4qec/<script-stem>`、研究リポジトリへの書き込みは `RIMC_RESEARCH_ROOT` と `RESEARCH_ROOT` の環境変数で保護し、絶対パスを直書きしない。
`benchmarks/bar_paper_protocol.py` は CSV（seed ごとの点推定・区間・被覆、構成ごとの要約）を出力し、テストからは呼ばない。

## 7. Phase 2（メインが統合後に行う）

1. Q → P の順に main へ merge する。各 merge の後に `python -m pytest tests -q` を通し、所要時間を記録する。
2. WP-P の最終の被覆表を Q 統合後の main で取り直し、`docs/bar_sensitivity_ja.md` と `docs/paper_consistency_ja.md` を確定する。
3. 完了メモの依頼に従い、`__init__.py`（公開名の追加があれば）、`docs/api_en.md`（`uncertainty` 引数）、README 両言語（Performance 節、BAR の制約段落）、`examples/README.md`、`examples/workflows/pl_curve.py` と notebook 02 の説明を反映し、notebook は `notebooks/regenerate.py` で再生成する。version は `0.1.0.dev5` にする。
4. `docs/wp/verify_wheel.py` と CI が新しい記述で通ることを確認する。
5. 新しい venv を 2 つ作り、core のみと optional 依存で wheel を install し、`pytest --override-ini pythonpath= tests -q` と `verify_wheel.py core|optional` を実行する。
6. `CHANGELOG.md` に 0.1.0.dev5 の変更を書く。`AGENTS.md` の Project と File layout を更新する。`docs/handoff/IMPLEMENTATION_STATUS.md` に今回の結果を追記する（既存の記述は書き換えない）。
7. main を `origin/main` に push し、GitHub Actions の全 job の結果を確認して報告に含める。
8. 使い終わった worktree と `wp/p`、`wp/q` ブランチは、main に内容が入っていることを `git cherry` で確かめてから削除する。
9. 最終報告 `docs/wp/final_report_dev5_ja.md` を書き、`docs/wp/PROGRESS_dev5_ja.md` の全項目を `[x]` にする。

## 8. 最終報告の形式

`docs/wp/final_report_dev5_ja.md` に、日本語、1 文 1 行で次の順に書く。

1. 到達点を 5 行以内で。
2. WP ごとの表。列は、実装、実行した検証（コマンドと結果）、未実施、レビューで出た指摘と対応。
3. 数値の表。WP-P の bias と分散の切り分け、4 構成 × 2 領域の被覆、WP-Q のベンチマーク（2 回以上）。
4. 論文との整合表の要点。ライブラリの既定が論文の手順と違う点と、その扱い（文書化した、既定変更を提案した、未対応）。
5. 統合後の tests 件数と時間、wheel 検証、CI の結果。
6. 所有者の判断待ち事項（`estimate_logical_error` の既定の誤差評価法と chain 数、`pl_curve.py` の既定、公開先、所属・DOI）と次の依頼候補。

## 9. 参照

- 公開文書。`LIB/README.md`、`LIB/README_ja.md`、`LIB/docs/api_en.md`、`LIB/docs/tutorial_en.md`、`LIB/examples/README.md`
- dev4 の記録。`LIB/docs/wp/final_report_dev4_ja.md`、`LIB/docs/bar_sensitivity_ja.md`、`LIB/docs/performance_ja.md`、`LIB/docs/wp/M_ja.md`、`LIB/docs/wp/N_ja.md`
- 前回までの依頼書。`LIB/docs/dev_request_2026-09-30.md`、`LIB/docs/dev_request_2026-09-30_examples.md`、`LIB/docs/dev_request_2026-10-01.md`
- 研究側（読み取り専用）。`RESEARCH/paper/main.tex`（Setup 節、Appendix の conventions 節、splitting 節、results 節）、`RESEARCH/src/splitting_pl.py`、`RESEARCH/src/runners.py`、`RESEARCH/src/metrics.py`、`RESEARCH/compare/convergence_flags.py`
- Bennett の方法。C. H. Bennett, J. Comput. Phys. 22, 245 (1976)。Bravyi and Vargo, Phys. Rev. A 88, 062308 (2013)
