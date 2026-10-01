# WP-M 担当指示

## 1. 前提と制約

- ライブラリのリポジトリは `C:\dev\mcmc4qec`（研究室 PC）または `A:\dev\mcmc4qec`（自宅 PC）。以下 `LIB` と書く。
- 研究リポジトリ RIMC は `C:\dev\RIMC` または `A:\dev\RIMC`。以下 `RESEARCH` と書く。**読み取り専用**で、1 ファイルも変更しない。runner の既定（Z+PT）も変えない。`git status` が clean のまま終わること。
- 出発点は main `c6cff92` 以降（0.1.0.dev3）。全 suite は optional 依存込みで 314 passed / 4 skipped（約 4 分）、installed wheel の core 環境は 231 passed / 61 skipped。
- Python は 3.11 の絶対パスを使う（`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe`）。`python3` は使わない。
- 計算は軽いものだけ。1 テストファイルは 60 秒以内、全 suite の増分は 60 秒以内で全 suite 5 分以内を保つ。感度評価とベンチマークは 1 本 10 分以内とし、`benchmarks/` に置いてテストからは呼ばない。クラスタ投入、巨大 sweep、長時間ジョブはしない。
- ライセンスの選択と追加、PyPI 等への publish、リポジトリの公開化、著者の所属・DOI などの引用情報の確定は**しない**。
- 公開既定 Z 0.7 / H 0.3 / cluster_k=2 / 1 chain / lazy 0.05 は変えない。既存の公開 API の既定引数と返り値の意味も変えない。追加は後方互換な keyword 引数か新しい名前で行う。
- 日本語文書は 1 文 1 行で書く（文の途中で改行しない）。README（英語）、`examples/README.md`、docstring、コメントは英語。
- 数値の一致、性能、テスト成功は実行して確認してから書く。未実行のものは「未実施」と明記する。
- 着手前に次を読む。`LIB/README.md`、`LIB/AGENTS.md`、`LIB/docs/api_en.md`、`LIB/docs/tutorial_en.md`、`LIB/docs/wp/final_report_examples_ja.md`、`LIB/docs/performance_ja.md`、`LIB/docs/convergence_ja.md`、`LIB/docs/circuit_baseline_ja.md`、`LIB/docs/crossval_research_ja.md`、`LIB/docs/handoff/IMPLEMENTATION_STATUS.md`、`LIB/docs/wp/verify_wheel.py`、`LIB/.github/workflows/tests.yml`、担当する `src/mcmc4qec/` のモジュールと対応する `tests/`。

## 2. モデル構成と並列運用

### 2.1 役割

- **メイン（astra）**: 全体の指揮、Phase 0 の準備、ブランチの統合、共有ファイルの編集、最終検証と報告。自分で大きな実装はしない。
- **サブエージェント（gpt-sol）**: WP ごとに 1 体を同時に起動する（5 体）。各 WP 内でさらに独立な部分があれば最大 2 体まで追加してよい。同時実行の上限は 8 体。
- **レビュー担当（gpt-sol）**: 各 WP が完了したら、別のサブエージェントに差分を敵対的にレビューさせる（詳細釣合い、正規化、提案比、境界条件、テストが本当に主張を検証しているか、文書が実行結果と一致しているか）。指摘は WP 担当が対応し、メインが最終判断する。

### 2.1.1 reasoning effort

| 役 | effort | 理由 |
| --- | --- | --- |
| メイン（astra） | high | 毎反復で呼ばれる指揮・統合・裁定の役 |
| gpt-sol WP-K / L / M / N | high | 検査行列の取り違え、提案比、詳細釣合い、推定量の bias など、間違えると数値が静かにずれる作業 |
| gpt-sol WP-O | medium | 型注釈は判断より作業量 |
| レビュー担当（WP-L と WP-N の差分） | xhigh | 1 回きりで、提案分布と高速経路の等価性の穴を探す仕事 |
| レビュー担当（WP-K / M / O の差分） | high | |

役ごとに effort を変えられない環境では全体を high にする。その場合、レビュー担当への指示文に「詳細釣合いと正規化は数値で反証を試みる」と明記して xhigh の代わりにする。

### 2.2 作業の分離

- WP ごとに git worktree を作る。`git worktree add ../mcmc4qec-wt/<wp> -b wp/<wp>`（`<wp>` は `k`〜`o`）。作業は worktree 内だけで行う。
- 共有ファイル `src/mcmc4qec/__init__.py`、`pyproject.toml`、`CHANGELOG.md`、`README.md`、`README_ja.md`、`AGENTS.md`、`docs/api_en.md`、`examples/README.md`、`.github/workflows/tests.yml` は WP 担当が直接編集しない。追加したい公開名、README の表の行、`examples/README.md` の行、CI の変更は完了メモに書き、メインが統合時に反映する。
- `src/mcmc4qec/sampling.py`、`kernels.py`、`fastpath.py` は WP-L と WP-N の両方が触る。衝突を避けるため、WP-N は新規モジュール `src/mcmc4qec/faststep.py` に専用経路を書き、`sampling.py` への接続は関数 1 つの呼び出し追加に留める。WP-L は `fastpath.py` の拡張と `sampling.py` の kernel 検査の緩和に留める。どちらも変更した行を完了メモに列挙する。
- 各 WP は担当ファイルの外を編集しない。どうしても必要なら完了メモに理由と最小 diff を書いてメインに委ねる。
- WP は完了時に `docs/wp/<WP>_ja.md` を書く。内容は、実装したこと、実行した検証（コマンドと結果の数値）、未実施、メインへの依頼（公開名の追加、README 行、CI 変更など）。
- コミットは worktree のブランチに自由に行う。メッセージは英語で 1 行要約。push はメインが最終検証後に main だけ行う。ほかの remote 操作はしない。

### 2.3 統合の順序

メインは K → N → L → M → O の順に main へ merge する。
WP-L は WP-N の merge 後に main に rebase してから merge し、高速経路と回路カーネルの等価性テストを rebase 後にもう一度通す。
WP-O は最後に rebase し、統合後の全モジュールに対して型検査を通す。
各 merge の後に `python -m pytest tests -q` を通す。全部の merge が終わったら Phase 2 の検証を行う。

## 3. 科学的な注意（全 WP 共通、レビューで必ず確認する）

1. **検査行列の取り違え。** bit flip（X 誤り）は `hz` で検出し `lz` で論理を読み、stabilizer flip には `hx` の行を使う。phase flip（Z 誤り）はその双対で、`hx` で検出し `lx` で論理を読み、stabilizer flip には `hz` の行を使う。テストは self-dual でない符号（asymmetric toric、BB72、Hamming HGP）で両者の違いが出ることを確かめる。
2. **提案の可逆性。** 新しい提案は、全状態・全近傍で順向きと逆向きの提案確率を列挙し、MH 受理と合わせて失敗集合上の詳細釣合いを数値で確かめる。既約性と周期性は詳細釣合いとは別に述べる。
3. **高速経路の等価性。** 高速経路は参照経路と同じ提案分布、同じ受理確率、同じ seed で同じ軌道を与えなければならない。異なる乱数消費で軌道が変わる変更は不可とする。
4. **棄却と lazy を chain に残す。** 混合確率を暗黙に再正規化しない。既存の `Result` の trace の意味を変えない。
5. **区間の解釈。** BAR の区間と direct MC の区間の非交差は、どちらが正しいかを決めずに真値（exact）と比べる。被覆率は反復 seed で数え、1 回の実行で主張しない。seed や設定を調整して被覆を「作らない」。
6. **診断は証明ではない。** ESS、split R-hat、`evaluate_convergence` の 4 条件が良くても収束・エルゴード性・正しさの証明ではない。出力と文書にその旨を残す。
7. **研究結果の再現を主張しない。** 論文は「in preparation」とだけ書く。回路 baseline の拡張でも arXiv:2509.13678 の図表の再現とは書かない。
8. **条件付き chain は `P_L` を推定しない。** 例と文書で `sample_faulty` の状態頻度から絶対 `P_L` を出さない。


### WP-M BAR と direct MC の区間非交差の原因調査と感度評価

目的。dev3 で toric d=3、p=0.22 の BAR 曲線が独立 direct MC の区間と交差しなかった（`docs/wp/final_report_examples_ja.md` 第 5 節）。原因を特定し、chain 長・初期状態・ladder の刻み・block 長への感度と、反復 seed での被覆率を記録して、利用者向けの設定指針を出す。

担当ファイル。`benchmarks/bar_sensitivity.py`、`tests/test_bar_coverage.py`、`docs/bar_sensitivity_ja.md`、`docs/wp/M_ja.md`。`src/mcmc4qec/estimation.py` の変更は、原因が実装の誤りだった場合に限り、最小 diff とテストを完了メモに書いてメインに委ねる。

作業内容。

1. 再現。`examples/workflows/pl_curve.py` の既定設定で非交差を再現し、同じ問題（toric d=3 bit flip、MWPM）を `exact` で列挙して真値を出す。BAR と direct MC のどちらが真値を外しているかを、まず 1 回の実行で確認し、次に 20 seed 以上で被覆率として数える。
2. 仮説を分けて検証する。少なくとも次を扱う。(a) block bootstrap の block 長が IAT より短く区間が狭すぎる。(b) anchor の direct MC を再利用しているため anchor 点の誤差が全 rung に伝播する。(c) 隣接 rung の support の重なりが小さく BAR の分散が大きい。(d) burn-in 不足や初期状態の偏り。(e) p=0.22 は d=3 の閾値をはるかに超えており失敗集合が状態空間の大半を占めるため、条件付き分布の性質が低 p 側と異なる。各仮説について、変えた設定と結果の表を作る。
3. 感度評価。samples、burn_in、block 長（IAT の倍数で指定）、ladder の刻み、初期状態（`minimum_weight_initial_state`、`random_logical_sector_initial_state`、`maximum_weight_initial_state`）を 1 つずつ動かし、被覆率と区間幅を表にする。1 本 10 分以内に収まる範囲で行い、外の設定は「未実施」と書く。
4. 利用者向けの指針。block 長・ladder の刻み・samples の目安を `docs/bar_sensitivity_ja.md` に書き、`examples/workflows/pl_curve.py` と `notebooks/02_pl_curve_with_bar.ipynb` の説明文の修正案を完了メモに書く（実物の修正はメインが行う）。
5. `tests/test_bar_coverage.py`。列挙できる小問題（repetition や Steane など）で、10 seed 程度の反復により BAR 区間の exact 被覆率が名目に対して極端に低くないことを確かめる。60 秒以内。閾値は緩く取り、テストが seed に敏感にならないようにする。
6. 原因が実装の誤り（例えば block bootstrap や BAR の分散の式）であれば、最小 diff と再現テストを完了メモに書く。原因が統計的な限界であれば、その旨と検出方法を書く。

受入条件。真値との比較表、仮説ごとの表、感度の表、被覆率の表、指針、`tests/test_bar_coverage.py`。原因を 1 つに絞れない場合は候補と各根拠を書く。

依存。なし。`src/` は変更しない。

## 6. 例と benchmark の共通規約

`examples/` の新しいスクリプトは `docs/dev_request_2026-09-30_examples.md` 第 3 節の規約に従う。
`argparse` で `--quick`、`--seed`、`--out` を受け付け、既定の出力先は `tempfile.gettempdir()/mcmc4qec/<script-stem>`、図は Agg backend の PNG で matplotlib が無ければ CSV に落とし、最終行に `SUMMARY <json>` を出す。
`--quick` は 10 秒以内、既定は 2 分以内とし、冒頭の docstring に目的、必要な extras、実行時間の目安、第 3 節のどの注意が関係するかを書く。
新しい例は `examples/README.md` の表に載せる必要があり、その行の案（目的、extras、実測時間、出力の読み方）を完了メモに書く。`tests/test_docs_manifest.py` が統合後に通ることをメインが確かめる。

| パス | WP | extras | 内容 | SUMMARY のキー |
| --- | --- | --- | --- | --- |
| `examples/phase_flip_asymmetric.py` | K | `codes`, `matching` | asymmetric toric の bit flip と phase flip の `P_L` を direct MC（可能なら exact）で比較 | `code`, `p`, `pl_bit_flip`, `pl_phase_flip`, `interval_bit_flip`, `interval_phase_flip`, `exact_available` |
| `examples/circuit_zanella.py` | L | `stim`, `matching` | surface d=3 logical idle で `circuit_single` と Z+OBF の `E[w\|faulty]`、受理率、IAT を比較 | `distance`, `p`, `kernels`, `conditional_weight`, `acceptance`, `iat`, `direct_mc_conditional_weight` |
| `benchmarks/bar_sensitivity.py` | M | `codes`, `matching` | toric d=3 の BAR と direct MC の被覆率と感度（テストから呼ばない） | なし（CSV 出力） |
| `benchmarks/bench_circuit_step.py` | L | `stim`, `matching` | 回路モデルの kernel 別 step/s | なし |
| `benchmarks/bench_step.py` | N | `codes`, `matching`, `bposd` | 既存。専用経路と研究 runner の比較を追加 | なし |


## この環境での運用

作業先は `A:/dev/mcmc4qec-wt/m`、main は編集しない。
研究側は `A:/dev/RIMC` を読み取り専用で参照し、import 時は PYTHONDONTWRITEBYTECODE=1 を設定する。
指定 Python 3.11 を使用し、実行前に依頼書第1節の文書と担当モジュール・テストを読む。
科学的変更は小仕様を完了メモに先に書き、受入テスト、実装の順に進める。
共有ファイルと PROGRESS_dev4_ja.md はメインだけが編集する。
担当外の変更案は完了メモへ書き、実ファイルは変更しない。
完了前に英語要約でコミットし、Co-Authored-By: OpenAI Codex <noreply@openai.com> と Claude-Session: not applicable (Codex dev4 goal 01a0f4a8-d12b-7c93-b47d-6b85b6c7bba9) をフッターに付ける。
push はしない。
同時実行枠の制約から追加サブエージェントは起動せず、独立レビューはメインが別担当に依頼する。
