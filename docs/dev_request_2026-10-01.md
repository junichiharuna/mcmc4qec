# mcmc4qec 開発依頼書：dev4（phase flip、回路レベル Z/OBF、BAR 感度、速度、型）（Codex goal 用）

作成日 2026-10-01。対象リポジトリは `junichiharuna/mcmc4qec`（private）。
この文書を Codex の goal としてそのまま渡す。メインモデルは astra、サブエージェントは gpt-sol を使う。
前回までの依頼書 `docs/dev_request_2026-09-30.md`（WP-A〜E）と `docs/dev_request_2026-09-30_examples.md`（WP-F〜J）と同じ運用で進める。
今回の WP は K〜O と呼び、`docs/wp/K_ja.md` のように前回までの名前と衝突しないようにする。
進捗は `docs/wp/PROGRESS_dev4_ja.md` のチェックリストで管理し、中断と再開はこのファイルを起点にする。

## 0. 依頼の要約

`mcmc4qec` 0.1.0.dev3 は、機能・検証・実行例・文書がそろい、remote CI も通っている。
dev3 の最終報告 `docs/wp/final_report_examples_ja.md` 第 6 節に残された次の候補と、所有者が追加で求める 2 機能を、この依頼で埋める。

1. code capacity の静的 phase flip（Z 誤り）を bit flip と対称に扱えるようにする（WP-K、新機能）。
2. 物理回路 fault の状態空間で OBF と Zanella を使えるようにする（WP-L、新機能）。現状は `circuit_single` の単一 location 提案しか許していない。
3. BAR 区間と独立 direct MC 区間が非交差になる例（toric d=3、p=0.22）の原因調査と、chain 長・初期状態・ladder・block 長の感度評価、反復 seed による被覆評価（WP-M、研究検証）。
4. 研究 runner との速度差の解消（WP-N、性能）。dev2 の計測では toric d=5 で 17.9 倍、d=7 で 22.5 倍、BB72 で 6.5 倍遅い。
5. 型注釈と `py.typed`（WP-O、公開準備）。

成果物は次の 4 つ。

1. main に統合された実装・テスト・例・文書（全 tests 緑、wheel を別環境に入れて例が動く、remote CI 全 job 成功）。
2. 各 WP の完了メモとレビュー記録（日本語、`docs/wp/K_ja.md`〜`O_ja.md` と `K_review_ja.md`〜`O_review_ja.md`）。
3. 更新された `pyproject.toml`（version `0.1.0.dev4`）、`CHANGELOG.md`、`AGENTS.md`、`README.md` / `README_ja.md`、`docs/api_en.md`、`examples/README.md`、CI、`docs/handoff/IMPLEMENTATION_STATUS.md` の追記。
4. 最終報告（日本語、`docs/wp/final_report_dev4_ja.md`）。実行した検証だけを合格として書く。

## 1. 前提と制約

- ライブラリのリポジトリは `C:\dev\mcmc4qec`（研究室 PC）または `A:\dev\mcmc4qec`（自宅 PC）。以下 `LIB` と書く。
- 研究リポジトリ RIMC は `C:\dev\RIMC` または `A:\dev\RIMC`。以下 `RESEARCH` と書く。**読み取り専用**で、1 ファイルも変更しない。runner の既定（Z+PT）も変えない。`git status` が clean のまま終わること。
- 出発点は main `c6cff92` 以降（0.1.0.dev3）。全 suite は optional 依存込みで 314 passed / 4 skipped（約 4 分）、installed wheel の core 環境は 231 passed / 61 skipped。
- Python は 3.11 の絶対パスを使う（`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe`）。`python3` は使わない。
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

## 4. Phase 0（メインが最初に行う、30 分以内）

1. `LIB` の main が `origin/main` と一致し、全 suite が通ることを確認する（件数と秒数を記録）。
2. `docs/wp/PROGRESS_dev4_ja.md` を作る。内容は Phase 0、各 WP の実装・レビュー・対応、Phase 2 の各項目を 1 行 1 項目のチェックリストにしたもので、項目が終わるたびに `[x]` と日時を書く。中断からの再開はこのファイルの最初の未完了項目から行う。
3. `docs/wp/` に、この文書の WP 節をもとに各 WP の指示文をサブエージェントに渡す。指示文には、担当ファイル、受入条件、制約（第 1 節）、科学的な注意（第 3 節）、完了メモの書式を含める。
4. worktree を 5 つ作り、5 体を同時に起動する。

## 5. 作業パッケージ

### WP-K code capacity の静的 phase flip

目的。Z 誤りの code capacity モデルを、bit flip と同じ API で扱えるようにする。self-dual でない符号では X と Z の論理誤り率が異なるので、利用者が両方を出せる必要がある。

担当ファイル。`src/mcmc4qec/core.py`（`CSSCode.phase_flip_model` の追加のみ）、`src/mcmc4qec/decoders.py`、`src/mcmc4qec/models.py`（`PhenomenologicalModel` の `data_noise`）、`src/mcmc4qec/noise_categorical.py`（phenomenological の phase flip 対応が要る場合）、`tests/test_phase_flip.py`、`tests/test_crossval_research.py`（追加のみ）、`examples/phase_flip_asymmetric.py`、`docs/wp/K_ja.md`、`docs/tutorial_en.md`（phase flip の節を追加）。

作業内容。

1. `CSSCode.phase_flip_model()` を追加する。`BinaryLinearModel(hx, lx, stabilizers=hz, identifier="css-phase-flip")` を返す。docstring に、状態は Z 誤りの support、syndrome は X 検査、論理は `lx` で読むこと、ノイズには既存の `IndependentBitFlip(n)` をそのまま使う（分布は同じ 2 値 product）ことを書く。
2. `mwpm_decoder(code, *, errors="X")` と `bposd_decoder(code, p, *, errors="X", **kw)` に `errors="Z"` を追加する。`"Z"` では `hx` と `lx` で構築し、identifier を `mwpm-css-z` / `bposd-css-z` にする。既定 `"X"` の挙動と identifier は変えない。`depolarizing_*` は既に両セクターを持つので触らない。
3. `PhenomenologicalModel(data_noise="phase_flip")` を追加する。データ誤りは `phase_flip_model()`、検査は `hx` 側だけを使う。`n_checks`、`alphabets`、`metadata` を整合させ、`PhenomenologicalNoise` と `fastpath._probability_rows` が新しい値で正しく動くことを確かめる。
4. `initial_states.py` の `sector="z"` が phase flip の初期状態として使えることをテストで確認する（実装変更は不要のはず。必要なら完了メモに）。
5. テスト。(a) 任意の `CSSCode` で `phase_flip_model()` の syndrome・observables・stabilizer 行が、双対符号 `CSSCode(hz, hx, lz, lx)` の `bit_flip_model()` と一致する。(b) toric d=3 では exact の `P_L` と `E[w|faulty]` が bit flip と phase flip で一致し、asymmetric toric（d1≠d2）と Hamming HGP では一致しない。(c) asymmetric toric の phase flip の exact が、双対符号の bit flip の exact と一致する。(d) `errors="Z"` の MWPM が小符号の全 syndrome で `RESEARCH/src/css_code.py` の `make_depolarizing_mwpm_decoder` の Z 側（`pymatching.Matching(code.hx)`）と同じ論理予測を返す（読み取り専用 import、無ければ skip）。(e) Z+H の phase flip chain が exact の `E[w|faulty]` と区間で整合する（小符号）。(f) `errors` の不正値、`data_noise` の不正値で `ValueError`。
6. 例 `examples/phase_flip_asymmetric.py`。asymmetric toric（例えば d1=3, d2=5）で bit flip と phase flip の `P_L` を direct MC と（可能なら）exact で並べ、両者が異なることを示す。第 6 節の CLI 規約に従う。
7. `docs/tutorial_en.md` に phase flip の節を追加する。README の対応表の行案（Static CSS phase-flip）と `docs/api_en.md` の追記案は完了メモに書く。

受入条件。テスト (a)〜(f) が通ること、例が既定と `--quick` で動くこと（実測時間）、既存テストが全部通ること、公開 API の既定の挙動が変わらないこと（`tests/test_public_api.py` と既存の identifier を確認）。

依存。なし。

### WP-L 物理回路 fault の状態空間での OBF と Zanella

目的。dev2 の回路 baseline は `PhysicalFaultProposal`（`circuit_single`）だけを許し、Z/H/stabilizer を禁止している。物理配置を保ったまま OBF と Zanella を使えるようにし、研究側の Z 系カーネルを回路レベルに広げる。

担当ファイル。`src/mcmc4qec/sampling.py`（`KernelConfig` の検査の緩和のみ）、`src/mcmc4qec/fastpath.py`（`CircuitFaultNoise` 対応）、`src/mcmc4qec/circuit/`（必要なら syndrome の差分更新）、`tests/test_circuit_kernels.py`、`examples/circuit_zanella.py`、`benchmarks/bench_circuit_step.py`、`docs/wp/L_ja.md`、`docs/circuit_baseline_ja.md`（対応範囲の更新）。

作業内容。

1. `sampling.py` の検査を緩め、`CircuitFaultModel` で `single`、`zanella`、`circuit_single` の任意の混合を許す。`cluster` と `stabilizer` は引き続き回路モデルでは `ValueError` にする（理由を docstring に書く）。既存の `KernelConfig(circuit_single=1, ...)` の挙動と identifier は変えない。
2. 既存の `OBF` と `Zanella` が `model.alphabets` を通じて可変長 alphabet の categorical 状態に既に対応していることを確認し、回路モデルで参照経路（`problem.log_prob` の全近傍評価）が正しく動くことをテストする。
3. `fastpath._probability_rows` を `CircuitFaultNoise` に拡張する。location ごとの条件付き確率と location 別の故障率から、行ごとに alphabet 長が異なる確率表（最大 alphabet 長で zero padding）を作る。padding が近傍として選ばれないことをテストする。`CircuitFaultNoise.probabilities(p)` の返り値の意味（実験全体の確率）を確認してから使う。
4. 候補の failure 判定は、可能なら単一 location の変更に対する効果ベクトル 2 本の XOR で syndrome と observable を差分更新する。実装した場合は全再計算との一致をテストする。
5. テスト。(a) repetition d=3 の 1 ラウンド（`4^3=64` 配置）で、OBF と Zanella のそれぞれと、両者の混合について、全状態・全近傍の提案確率を列挙し、失敗集合上の詳細釣合いを数値で確かめる。(b) 同じ問題で、fastpath あり／なしの Zanella の提案分布が一致し、同じ seed で同じ軌道になる。(c) alphabet 長が全 location で等しいときは `OBF` と `PhysicalFaultProposal` の提案分布が一致し、異なるときは一致しないことを列挙で示す。(d) location ごとに異なる条件付き確率と故障率を与えた小回路で fastpath と参照経路が一致する。(e) surface d=3 logical idle（`surface_logical_idle_problem`）で Z 0.7 / OBF 0.3 の chain の `E[w|faulty]` を `direct_mc` の条件付き重みと比べ、区間の重なりを記録する（時間予算内の短い chain。断定はしない）。(f) `cluster` や `stabilizer` を回路モデルに与えると `ValueError`。
6. `benchmarks/bench_circuit_step.py`。surface d=3 で `circuit_single` のみ、Zanella のみ、Z+OBF の step/s と受理率を比べて `docs/circuit_baseline_ja.md` に表で書く。
7. 例 `examples/circuit_zanella.py`。surface d=3 で `circuit_single` と Z+OBF の chain を同じ seed 系列で走らせ、`E[w|faulty]`、受理率、IAT を並べる。第 6 節の CLI 規約に従う。
8. README の対応表の行案（Physical Stim circuit locations の列を OBF / Z 対応に更新、cluster と stabilizer は unavailable のまま）と `docs/api_en.md` の追記案を完了メモに書く。

受入条件。テスト (a)〜(f) が通ること、ベンチマーク表、例が既定と `--quick` で動くこと（実測時間）、既存の回路テストと全 suite が通ること。cluster exchange の回路対応は今回の対象外とし、完了メモに設計上の論点（location の group 化、alphabet 長の違い）だけを書く。

依存。WP-N の merge 後に rebase して再検証する（第 2.3 節）。開発中は main の参照経路に対して書く。

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

### WP-N 研究 runner との速度差の解消

目的。dev2 の計測（`docs/performance_ja.md`）では、ライブラリの Z+H は研究 runner より toric d=5 で 17.9 倍、d=7 で 22.5 倍、BB72 で 6.5 倍遅い。プロファイルは `Problem.state` の再検証、`categorical` の再変換、Z の順逆分布の二重計算、failure 評価が主因と示している。研究側の 2 倍以内を目標にする。

担当ファイル。`src/mcmc4qec/faststep.py`（新規）、`src/mcmc4qec/sampling.py`（接続 1 箇所）、`src/mcmc4qec/kernels.py`（必要最小限）、`src/mcmc4qec/core.py`（検証済み状態の内部表現が要る場合、公開 API を変えない範囲）、`tests/test_faststep.py`、`benchmarks/bench_step.py`（更新）、`docs/wp/N_ja.md`、`docs/performance_ja.md`（追記）。

作業内容。

1. `docs/performance_ja.md` の「次の改善」に従い、専用ステップ経路を作る。(a) 検証済み状態を内部で区別し、`Problem.state` と `categorical` の再検証を 1 ステップ 1 回に減らす。(b) Zanella の順向き分布と逆向き確率を同じ局所確率表から作り、`log_prob` の全評価を避ける。(c) 線形 syndrome と observable を受理時に差分で維持し、候補の failure 判定は 1 座標の XOR で行う。(d) decode cache を経路に組み込む。
2. 適用条件は型か明示フラグで判定する。適用できるのは product ノイズ（`IndependentBitFlip`、`DepolarizingNoise`、`PhenomenologicalNoise`）と線形モデル（`BinaryLinearModel`、`DepolarizingModel`、`PhenomenologicalModel`）の組み合わせに限り、任意 callable のノイズ・モデル・failure predicate には適用しない。適用外は既存の参照経路に落とす。
3. 等価性テスト。小問題で参照経路と専用経路の提案分布・受理確率を全状態・全近傍で比較し、同じ seed で同じ軌道（状態列、受理列、lazy 列、kernel 選択列）になることを確かめる。`Result` の trace、`move_rates`、provenance が同じ意味を持つことも確かめる。
4. `benchmarks/bench_step.py` を更新し、toric d=5、d=7、BB72 の p=1e-2 で研究 runner（`RESEARCH/src/runners.py` の `run_rimc_mixed`、読み取り専用 import）と比較する。結果を `docs/performance_ja.md` に追記する。
5. 2 倍以内に届かない場合は、cProfile の結果と残る原因、次の手を書く。届いた場合も同じ表を書く。

受入条件。等価性テストが通ること、ベンチマーク表、既存テストが全部通ること、公開 API の既定の挙動が変わらないこと。

依存。なし。WP-L と同じファイルに触るので第 2.2 節の分離規則を守る。

### WP-O 型注釈と `py.typed`

目的。利用者が IDE と型検査器で API を使えるように、公開 API の型を明示する。

担当ファイル。`src/mcmc4qec/` 全モジュール（注釈の追加のみ、実行時の挙動を変えない）、`src/mcmc4qec/py.typed`（新規、空）、`tests/test_typing.py`、`docs/wp/O_ja.md`。`pyproject.toml` の変更案（`package-data` に `py.typed`、`[tool.mypy]`）と CI の job 追加案は完了メモに書く。

作業内容。

1. 公開 API（`__all__` の 65 名と、それらの返り値が持つ公開メソッド）に引数と返り値の型注釈を付ける。`Model` / `Noise` / `Decoder` の Protocol は既存の契約に合わせて注釈を整える。
2. `mypy` を `src/mcmc4qec` に対して通す。まず `--ignore-missing-imports` で通し、`--strict` で残る項目は数と理由を完了メモに書く。`pymatching`、`ldpc`、`stim` の stub がない場合の扱いを決める。
3. `tests/test_typing.py`。`mypy` が入っていれば `src` に対して実行して成功を確かめ、無ければ skip。60 秒以内。
4. 注釈の追加で実行時の挙動（引数の検証、例外、既定値）を変えない。変更が要ると気づいた点は完了メモに書く。

受入条件。`mypy --ignore-missing-imports src/mcmc4qec` の成功、`tests/test_typing.py`、全 suite 成功、`docs/api_en.md` の署名と注釈の一致（食い違いは完了メモに）。

依存。他の WP の merge 後に rebase して再実行する（第 2.3 節）。

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

## 7. Phase 2（メインが統合後に行う）

1. K → N → L → M → O の順に main へ merge する。L と O は merge 前に rebase して等価性テストと型検査をもう一度通す。各 merge の後に `python -m pytest tests -q` を通し、所要時間を記録する。
2. 完了メモの依頼に従い、`__init__.py` の公開名、`docs/api_en.md`、README 両言語の対応表、`examples/README.md` の行、`pyproject.toml`（`py.typed`、`[tool.mypy]`）、CI（型検査 job、新しい例の `--quick` 実行）を反映する。version は `0.1.0.dev4` にする。
3. WP-M の指針に従い、`examples/workflows/pl_curve.py` と `notebooks/02_pl_curve_with_bar.ipynb` の説明文を直し、notebook は `notebooks/regenerate.py` で再生成する。
4. `docs/wp/verify_wheel.py` を新しい例に合わせて更新する。
5. 新しい venv を 2 つ作り、core のみと optional 依存（`matching, bposd, codes, stim, plot, notebooks`）で wheel を install し、`pytest --override-ini pythonpath= tests -q` と `verify_wheel.py core|optional` を実行する。
6. `CHANGELOG.md` に 0.1.0.dev4 の変更を書く。`AGENTS.md` の Project と File layout を更新する（tests の件数と時間、新モジュール、新しい例）。`docs/handoff/IMPLEMENTATION_STATUS.md` に今回の結果を追記する（既存の記述は書き換えない）。
7. main を `origin/main` に push し、GitHub Actions の全 job の結果を確認して報告に含める。
8. 使い終わった worktree と `wp/k`〜`wp/o` ブランチは、main に内容が入っていることを `git cherry` で確かめてから削除する。
9. 最終報告 `docs/wp/final_report_dev4_ja.md` を書き、`docs/wp/PROGRESS_dev4_ja.md` の全項目を `[x]` にする。

## 8. 最終報告の形式

`docs/wp/final_report_dev4_ja.md` に、日本語、1 文 1 行で次の順に書く。

1. 到達点を 5 行以内で。
2. WP ごとの表。列は、実装、実行した検証（コマンドと結果）、未実施、レビューで出た指摘と対応。
3. 数値の表。WP-K の bit flip と phase flip の比較、WP-L の詳細釣合いとベンチマーク、WP-M の被覆率と感度、WP-N のベンチマーク、WP-O の型検査の結果。
4. 統合後の tests 件数と時間、wheel 検証、CI の結果。
5. 見つかったライブラリの不具合と、その扱い（直した、未対応）。
6. 所有者の判断待ち事項（ライセンス、著者情報、公開先、WP-M の指針を既定値に反映するか、cluster exchange の回路対応）と次の依頼候補。

## 9. 参照

- 公開文書。`LIB/README.md`、`LIB/README_ja.md`、`LIB/docs/api_en.md`、`LIB/docs/tutorial_en.md`、`LIB/examples/README.md`
- dev2 / dev3 の記録。`LIB/docs/wp/final_report_ja.md`、`LIB/docs/wp/final_report_examples_ja.md`、`LIB/docs/performance_ja.md`、`LIB/docs/convergence_ja.md`、`LIB/docs/crossval_research_ja.md`、`LIB/docs/circuit_baseline_ja.md`
- 検証の仕組み。`LIB/docs/wp/verify_wheel.py`、`LIB/.github/workflows/tests.yml`、`LIB/notebooks/regenerate.py`
- 前回までの依頼書。`LIB/docs/dev_request_2026-09-30.md`、`LIB/docs/dev_request_2026-09-30_examples.md`
- 研究側（読み取り専用）。`RESEARCH/src/css_code.py`（`make_depolarizing_mwpm_decoder` の Z 側）、`RESEARCH/src/runners.py`（`run_rimc_mixed`）、`RESEARCH/src/kernels.py`、`RESEARCH/paper/main.tex` の Setup 節
- 回路レベル splitting。Rare Event Simulation of Quantum Error-Correcting Circuits, arXiv:2509.13678v2
