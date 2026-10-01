# mcmc4qec 開発依頼書：実行例・notebook・README（Codex goal 用）

作成日 2026-09-30。対象リポジトリは `junichiharuna/mcmc4qec`（private）。
この文書を Codex の goal としてそのまま渡す。メインモデルは astra、サブエージェントは gpt-sol を使う。
前回の依頼書 `docs/dev_request_2026-09-30.md`（WP-A〜E、完了済み）と同じ運用で進める。今回の WP は F〜J と呼び、前回の `docs/wp/A_ja.md` などと名前が衝突しないようにする。

## 0. 依頼の要約

`mcmc4qec` 0.1.0.dev2 は機能と検証がそろったが、利用者が最初に触る実行例と文書が薄い。
現在の `examples/` は 6 本で、半分は 2〜3 量子ビットの玩具符号である。notebook と日本語 README はなく、持ち込み用の雛形もない。
この依頼では、ライブラリ本体（`src/`）には手を入れず、次の 4 種類の利用者向け資料と、それらを案内する README を追加する。

1. 実符号の実行例（WP-F）。BB72、depolarising、phenomenological、Steane など、現在の例では見えない場面。
2. 研究の典型ワークフロー（WP-G）。`P_L(p)` 曲線、`E[w|faulty]` の比較、複数 chain の収束チェック、p 依存デコーダーの扱い。
3. 持ち込み用テンプレート（WP-H）。利用者が自分の符号・ノイズ・デコーダーを差し込むだけで動く雛形。
4. Jupyter notebook（WP-I）。説明と図を含むチュートリアル。
5. README（WP-J）。トップ README（英語）の拡充、`README_ja.md` の新規作成、`examples/README.md` の新規作成。

成果物は次の 4 つ。

1. main に統合された例・テンプレート・notebook・README と、それらが動くことを確かめるテスト（全 tests 緑、wheel を別環境に入れて例が動く）。
2. 各 WP の完了メモとレビュー記録（日本語、`docs/wp/F_ja.md`〜`J_ja.md` と `F_review_ja.md`〜`J_review_ja.md`）。
3. 更新された `pyproject.toml`（optional extras）、CI、`docs/wp/verify_wheel.py`、CHANGELOG、`docs/handoff/IMPLEMENTATION_STATUS.md` の追記。
4. 最終報告（日本語、`docs/wp/final_report_examples_ja.md`）。実行した検証だけを合格として書く。

## 1. 前提と制約

- ライブラリのリポジトリは `C:\dev\mcmc4qec`（研究室 PC）または `A:\dev\mcmc4qec`（自宅 PC）。以下 `LIB` と書く。
- 研究リポジトリ RIMC は `C:\dev\RIMC` または `A:\dev\RIMC`。以下 `RESEARCH` と書く。**読み取り専用**で、1 ファイルも変更しない。例・notebook・テストが `RESEARCH` に書き込まないこと。
- 出発点は main `e00738e` 以降（0.1.0.dev2）。全 suite は optional 依存込みで 268 passed / 4 skipped（約 45〜80 秒）、installed wheel の core 環境は 208 passed / 43 skipped。
- Python は 3.11 の絶対パスを使う（`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe`）。`python3` は使わない。
- **`src/mcmc4qec/` は変更しない。** 公開 API も増やさない。例を書く途中でライブラリの不具合や足りない API を見つけたら、再現手順と最小 diff の案を完了メモに書いてメインに委ねる。メインは、テスト付きの小さい修正で済む場合に限りこの依頼の中で直してよく、そうでなければ未対応として最終報告に回す。
- ライセンスの選択と追加、PyPI 等への publish、リポジトリの公開化、著者の所属・DOI などの引用情報の確定は**しない**。
- 日本語文書（`README_ja.md` を含む）は 1 文 1 行で書く（文の途中で改行しない）。README（英語）、`examples/README.md`、コード中のコメントと docstring、notebook の説明文は英語。
- 数値の一致、実行時間、テスト成功は実行して確認してから書く。未実行のものは「未実施」と明記する。
- 着手前に次を読む。`LIB/README.md`、`LIB/AGENTS.md`、`LIB/docs/api_en.md`、`LIB/docs/tutorial_en.md`、`LIB/docs/wp/final_report_ja.md`、`LIB/docs/performance_ja.md`、`LIB/docs/convergence_ja.md`、`LIB/docs/crossval_research_ja.md`、`LIB/docs/circuit_baseline_ja.md`、`LIB/docs/wp/verify_wheel.py`、既存の `LIB/examples/*.py`、`.github/workflows/tests.yml`。

## 2. 科学的な注意（全 WP 共通、レビューで必ず確認する）

例と文書は利用者がそのまま真似するので、ここを誤ると誤った使い方が広まる。次を全 WP の受入条件に含める。

1. **条件付き chain は `P_L` を推定しない。** `sample_faulty` の状態頻度から絶対 `P_L` を出す例、そう読める出力や説明を書かない。`P_L` は `exact`、`direct_mc`、`estimate_logical_error`（BAR と anchor）だけから出す。
2. **p 依存デコーダーの罠。** `bposd_decoder(code, p)`、`depolarizing_bposd_decoder(code, p)`、回路 problem の `decoder_p` は p に依存する。BAR ladder では、(a) デコーダーを固定の p で 1 回だけ作り全 rung で使い回す（README の standard ladder の規則）か、(b) `p_dependent_decoder_approx` を明示的に選び、その区間に p 依存の bias が含まれないことを出力と説明に書く、のどちらかにする。どちらを選んだかを例の冒頭の docstring に書く。
3. **anchor。** MC anchor は失敗を 1 回以上観測していなければならない。`exact` で anchor を取れる例では exact を使い、MC anchor を使う例では観測失敗数を出力する。
4. **overlap。** 隣接 rung の support が重ならないと `OverlapError` になるのは意図した挙動である。ladder の刻みを粗くしすぎた場合の挙動を、少なくとも 1 つの例（WP-G の `pl_curve.py`）で説明する。
5. **診断は証明ではない。** ESS、split R-hat、`evaluate_convergence` の 4 条件が良くても収束・エルゴード性・正しさの証明ではない。出力と説明にその旨を残す。`evaluate_convergence` の完全な判定には独立な direct MC の条件付き分散が要ることも書く。
6. **研究結果の再現を主張しない。** 研究論文の設定をなぞる例でも「論文の図の再現」とは書かない。論文は「in preparation」とだけ書く。
7. **物理回路の baseline では Z/H/stabilizer を使わない。** `KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)` を明示する。

## 3. 例の共通規約とマニフェスト

### 3.1 CLI とファイル出力

すべての実行スクリプト（`examples/` 以下の `.py`）は次を満たす。

- `argparse` で `--quick`、`--seed INT`、`--out DIR` を受け付ける。`--quick` は CI とテスト用の縮小設定で、既定設定と同じコード経路を通す。
- `--out` の既定は `tempfile.gettempdir()/mcmc4qec/<script-stem>`。ファイルを書く場合は出力先を 1 行で表示する。リポジトリ内や `RESEARCH` を既定の出力先にしない。
- 図は matplotlib の Agg backend で PNG に保存する。matplotlib が無い環境では図を省き、同じ数値を CSV で保存して、図を省いた旨を 1 行表示する。
- 最終行に `SUMMARY <json>` を 1 行出力する。JSON のキーは第 3.3 節のマニフェストに従い、テストはこの行の存在とキーの集合だけを確かめる。
- 乱数は `--seed` から `spawn_seeds` などで派生させ、ほかに隠れた乱数源を持たない。
- 冒頭の docstring に、目的、必要な extras、既定と `--quick` の実行時間の目安、第 2 節のどの注意が関係するかを書く。

### 3.2 実行時間の予算

`docs/performance_ja.md` の実測では、ライブラリの Z+H は toric d=5 で約 2500 step/s、BB72（BP-OSD）で約 2200 step/s である。これを前提に設定を決める。

- `--quick`：1 本 10 秒以内（研究室 PC、optional 依存あり）。
- 既定：1 本 2 分以内。notebook は 1 本 3 分以内。
- テストは `--quick` だけを実行する。新しいテストファイルは 1 本 60 秒以内とし、全 suite の増分は 90 秒以内、全 suite は 5 分以内を保つ。
- 各 WP は、自分の例の既定と `--quick` の実測時間を完了メモに表で書く。

### 3.3 マニフェスト（ファイル名はここで固定する）

WP-J はこの表だけを頼りに README を並行して書くので、各 WP はファイル名・extras・SUMMARY のキーを勝手に変えない。変更が必要な場合は完了メモに書き、メインが表と README の両方を更新する。

| パス | WP | extras | 内容 | SUMMARY のキー |
| --- | --- | --- | --- | --- |
| `examples/bb72_bposd.py` | F | `codes` | BB72 bit-flip、固定 p で作った BP-OSD。direct MC の `P_L` と `E[w\|faulty]`、Z+H の `E[w\|faulty]` | `code, p, pl, pl_interval, ew_direct, ew_chain` |
| `examples/toric_depolarizing.py` | F | `matching`, `codes` | toric d=3/5 の depolarising、`depolarizing_mwpm_decoder`。direct MC と Z+H、X/Y/Z 重みの内訳 | `code, p, pl, pl_interval, ew_direct, ew_chain` |
| `examples/phenomenological_toric.py` | F | `matching`, `codes` | toric d=3 の phenomenological（データとmeasurement の誤り、T ラウンド）。`HistoryDecoder` と時空間 check 行列上の matching | `code, rounds, p, pl, pl_interval` |
| `examples/steane_exact.py` | F | なし | Steane 符号。列挙で作った最小重み lookup デコーダー、exact・direct MC・BAR（exact anchor）を全 rung で exact と比較 | `code, ladder, exact, bar, bar_intervals` |
| `examples/workflows/pl_curve.py` | G | `matching`, `codes`（図は `plot`） | toric d=3,5 の `P_L(p)` を BAR で。MC anchor、確認用の direct MC 点、ladder 設計と `OverlapError` の説明。CSV と PNG | `codes, ladder, estimates, intervals, checks` |
| `examples/workflows/conditional_weight.py` | G | `matching`, `codes`（図は `plot`） | 複数の p で `E[w\|faulty]` を Z+H と direct MC で比較。chain 頻度が `P_L` でない理由を出力で示す | `code, ps, ew_direct, ew_chain` |
| `examples/workflows/convergence_check.py` | G | `matching`, `codes` | 最小重み・ランダム論理セクター・最大重みの初期状態から複数 chain、`evaluate_convergence` に direct MC の分散を渡し 4 条件と warnings を表示 | `code, p, checks, verdict, warnings` |
| `examples/workflows/p_dependent_decoder.py` | G | `codes` | BB72 + BP-OSD で、固定 p デコーダーの standard ladder と `p_dependent_decoder_approx` を並べ、違いと bias の注意を示す | `code, ladder, fixed, approx` |
| `examples/templates/byo_css_bitflip.py` | H | なし | 利用者の `hx, hz, lx, lz` と自作デコーダーで exact / direct MC / 条件付き chain / BAR まで通す雛形 | `n, k, checks_passed, pl` |
| `examples/templates/byo_noise.py` | H | なし | 自作の正規化ノイズ（`log_prob` の契約）。小さい n で全列挙による正規化チェックをしてから使う雛形 | `n, normalization, pl` |
| `examples/templates/byo_decoder.py` | H | なし | 既存のデコーダーオブジェクトを `DecoderAdapter` / `CallableDecoder` で包む雛形。output の意味と論理写像を明示し、全 syndrome で整合チェック | `n, output_kind, checks_passed, pl` |
| `examples/templates/byo_stim_dem.py` | H | `stim`, `matching` | 利用者の `stim.Circuit` から DEM、`from_stim_dem`、`matching_from_dem` で direct MC と条件付き chain まで通す雛形 | `detectors, mechanisms, pl` |
| `notebooks/01_quickstart.ipynb` | I | `notebooks`, `matching`, `codes` | インストールから toric d=5 の direct MC と Z+H まで | — |
| `notebooks/02_pl_curve_with_bar.ipynb` | I | `notebooks`, `matching`, `codes` | BAR ladder の考え方と `P_L(p)` 曲線、anchor と overlap | — |
| `notebooks/03_conditional_sampling_and_diagnostics.ipynb` | I | `notebooks`, `matching`, `codes` | 条件付き分布、カーネル設定、trace の読み方、複数 chain と `evaluate_convergence` | — |
| `notebooks/04_bring_your_own.ipynb` | I | `notebooks` | 自作の符号・ノイズ・デコーダーの持ち込み（core のみで動く範囲） | — |

既存の 6 本（`bit_flip.py`、`three_noise.py`、`bar_ladder.py`、`toric_pymatching.py`、`stim_dem.py`、`circuit_baseline.py`）は残す。第 3.1 節の CLI 規約に合わせる改修は WP-F が行う（出力内容と数値の意味は変えない）。

新しい extras はメインが `pyproject.toml` に追加する案とする。`plot = ["matplotlib>=3.7,<4"]`、`notebooks = ["nbclient>=0.9,<1", "nbformat>=5.9,<6", "ipykernel>=6,<8", "matplotlib>=3.7,<4"]`。バージョン範囲はメインが手元で入れて確かめてから確定する。

## 4. モデル構成と並列運用

### 4.1 役割

- **メイン（astra）**: 全体の指揮、Phase 0、統合、共有ファイルの編集、最終検証と報告。自分で大きな作業はしない。
- **サブエージェント（gpt-sol）**: WP-F〜J に 1 体ずつ、5 体を同時に起動する。WP 内で独立な部分があれば最大 2 体まで追加してよい。同時実行の上限は 8 体。
- **レビュー担当（gpt-sol）**: 各 WP の完了後、別のサブエージェントが差分を敵対的にレビューする。第 2 節の 7 項目、第 3 節の規約、例の出力や説明が主張していることが実際の計算で支えられているか、テストが本当にそれを確かめているかを見る。結果は `docs/wp/<X>_review_ja.md` に書く。指摘は WP 担当が対応し、メインが最終判断する。

### 4.2 reasoning effort

| 役 | effort | 理由 |
| --- | --- | --- |
| メイン（astra） | high | 統合と裁定、マニフェストとの整合 |
| gpt-sol WP-F / G | high | 実符号・BAR・収束判定の使い方を誤ると、誤用が例として広まる |
| gpt-sol WP-H | high | 雛形のチェック（正規化、デコーダー出力の意味）が甘いと利用者の誤りを見逃す |
| gpt-sol WP-I / J | medium | 文書と notebook は作業量が中心 |
| レビュー担当（F / G / H） | high | 第 2 節の違反は数値で反証を試みる |
| レビュー担当（I / J） | medium | |

役ごとに effort を変えられない環境では全体を high にする。

### 4.3 作業の分離

- WP ごとに git worktree を作る。`git worktree add ../mcmc4qec-wt/<x> -b wp/<x>`（`<x>` は `f`〜`j`）。作業は worktree 内だけで行う。
- 共有ファイル `pyproject.toml`、`CHANGELOG.md`、`.github/workflows/tests.yml`、`docs/wp/verify_wheel.py`、`src/` 以下はメインだけが編集する。WP 担当は必要な変更を完了メモに書く。
- 各 WP の担当ファイルは次の通り。これ以外を編集しない。
  - WP-F：`examples/*.py`（新規 4 本と既存 6 本の CLI 改修）、`tests/test_examples_real.py`、`docs/wp/F_ja.md`。
  - WP-G：`examples/workflows/`、`tests/test_examples_workflows.py`、`docs/wp/G_ja.md`。
  - WP-H：`examples/templates/`、`tests/test_examples_templates.py`、`docs/wp/H_ja.md`。
  - WP-I：`notebooks/`、`tests/test_notebooks.py`、`docs/wp/I_ja.md`。
  - WP-J：`README.md`、`README_ja.md`、`examples/README.md`、`tests/test_docs_manifest.py`、`docs/wp/J_ja.md`。
- 完了メモ `docs/wp/<X>_ja.md` の内容は、作ったもの、実行した検証（コマンドと結果の数値、実行時間の表）、未実施、メインへの依頼（extras、CI、verify_wheel、ライブラリの不具合）。
- コミットは worktree のブランチに自由に行う。メッセージは英語で 1 行要約。push はメインが最終検証後に main だけ行う。

### 4.4 テストの方針

- 例のテストは `subprocess` で `sys.executable <script> --quick --seed <固定> --out <tmp_path>` を実行し、終了コード 0、`SUMMARY` 行の存在、マニフェスト通りのキー集合、出力ファイル（CSV / PNG）の存在だけを確かめる。
- 固定 seed の数値そのものは assert しない。CI は ubuntu、開発は Windows で、PyMatching の tie-break や NumPy のバージョンによって数値が変わりうるためである。
- 数値を assert してよいのは exact の参照値がある場合だけで、その場合も「区間が exact を含む」のような統計的に意味のある形にし、失敗確率が十分小さい設定にする（`steane_exact.py` など）。
- optional 依存が無い環境では、該当テストを `pytest.importorskip` で skip する。core 環境で走るもの（extras なし）は skip しない。

## 5. Phase 0（メインが最初に行う、30 分以内）

1. `LIB` の main が clean で `origin/main` と一致し、この依頼書と更新済みの `AGENTS.md` を含むことを確認する。含まない場合は作業を始めずに所有者へ報告する。
2. 全 suite を実行し、件数と時間を記録する（期待値 268 passed / 4 skipped 前後）。
3. `docs/wp/verify_wheel.py` が `examples/*.py` を直下だけ glob し、`README.md` と `docs/tutorial_en.md` の python ブロックを実行していることを確認する。この依頼の統合後にどう拡張するか（サブディレクトリ、`--quick`、`README_ja.md` の扱い）を決め、WP-J に伝える。
4. 各 WP の指示文を作る。担当ファイル、受入条件、第 1〜3 節の制約、マニフェスト、完了メモの書式を含める。
5. 5 体を同時に起動する。

## 6. 作業パッケージ

### WP-F 実符号の実行例

目的。玩具符号ではなく、研究で使う符号とノイズでライブラリが動く様子を見せる。

作業内容。

1. マニフェストの 4 本を作る。組み込みの符号ファクトリとデコーダー構築関数（`make_bb_code_72`、`make_toric_code`、`make_steane_code`、`bposd_decoder`、`depolarizing_mwpm_decoder` など）を使い、手書きの行列は使わない。
2. `bb72_bposd.py` は BP-OSD を固定の p で 1 回だけ作る。その p と、評価する p が一致するかどうかを出力に明記する。
3. `toric_depolarizing.py` は X / Y / Z の重みの内訳を出力し、sector の合成はデコーダーの選択であること（README の対応表の記述）をコメントで説明する。
4. `phenomenological_toric.py` は、組み込みの phenomenological デコーダーが無いため、公開 API（`PhenomenologicalModel`、`PhenomenologicalNoise`、`HistoryDecoder`、`matching_from_check_matrix`）だけで時空間の matching デコーダーを組む。組めない、または組んだデコーダーの意味（どの syndrome 履歴・差分表現を読むか）を正しく説明できない場合は、この例を作らずに理由を完了メモに書き、マニフェストからの削除をメインに依頼する。
5. `steane_exact.py` は 7 量子ビットの全 syndrome を列挙して最小重み lookup デコーダーを作り、`exact` の値を参照にして direct MC と BAR（exact anchor）の区間が exact を含むかを rung ごとに出力する。
6. 既存 6 本を第 3.1 節の CLI 規約に合わせる。出力内容と数値の意味は変えない。README や tutorial に貼られているコードとの対応が崩れる場合は完了メモに書く。

受入条件。10 本すべてが既定と `--quick` で動くこと（実測時間の表）、`tests/test_examples_real.py`、第 2 節の該当項目、steane の区間が exact を含むことの確認（何 rung 中何 rung か）。

依存。なし。

### WP-G 研究の典型ワークフロー

目的。研究者が論文用の数値を作るときの一連の手順を、短く動く形で示す。

作業内容。

1. `pl_curve.py`。p に依存しない MWPM デコーダーで toric d=3,5 の `P_L(p)` を BAR で出す。最大の p で direct MC anchor を取り、観測失敗数を出力する。確認用に direct MC でも測れる p の点を並べ、BAR の区間と direct MC の区間を表と図で比べる。ladder の刻み方（隣接 rung の重なり）の目安を docstring に書き、刻みを粗くした設定で `OverlapError` が出ることを `--demo-overlap` オプションで示す。
2. `conditional_weight.py`。複数の p で `E[w|faulty]` を Z+H と direct MC で比べ、図と CSV に出す。chain の状態頻度が `P_L` にならないことを 1 段落のコメントと出力 1 行で示す。
3. `convergence_check.py`。`minimum_weight_initial_state`、`random_logical_sector_initial_state`、`maximum_weight_initial_state` から chain を起動し、`evaluate_convergence` に `other_initialization` と独立な direct MC の条件付き分散を渡す。4 条件それぞれの結果と warnings を表示し、各条件が何を検知でき何を検知できないかを `docs/convergence_ja.md` に沿って英語で短く説明する。
4. `p_dependent_decoder.py`。BB72 + BP-OSD で、固定 p デコーダーの standard ladder と `p_dependent_decoder_approx` の両方を実行し、推定値と区間を並べる。approx の区間に p 依存の bias が含まれないことを出力に明記する。どちらが正しいかは主張しない。
5. 研究側の設定をなぞる場合は `RESEARCH/paper/main.tex` の Setup 節を読み取り専用で参照してよいが、再現は主張しない。

受入条件。4 本が既定と `--quick` で動くこと（実測時間の表）、matplotlib がある場合の PNG と無い場合の CSV の両方の動作確認、`tests/test_examples_workflows.py`、第 2 節の 1〜5 の遵守。

依存。なし。

### WP-H 持ち込み用テンプレート

目的。利用者が自分の部品を差し込み、誤りがあれば実行前に気づける雛形を用意する。

作業内容。

1. マニフェストの 4 本を作る。各ファイルは `# >>> EDIT HERE` と `# <<< END EDIT` で囲んだ編集箇所を持ち、編集箇所の外は触らなくても動くようにする。既定値として小さい動く例を入れておく。
2. 編集箇所の後に、サンプリングの前に走る検査を置く。検査は少なくとも次を含む。`hx @ hz.T = 0`、論理演算子の可換関係と独立性、ノイズの正規化（小さい n なら全列挙、大きい n なら「未検査」と表示）、デコーダーの出力の形と意味（全 syndrome または無作為な syndrome で、論理写像を通した予測が 0/1 の長さ k の列になること）、failure predicate の決定性。検査に落ちたら、何が違うかを 1 行で示して止まる。
3. 検査はテンプレート内の関数として書き、ライブラリには追加しない。汎用化すべき検査があれば、公開 API の案として完了メモに書く。
4. 独自 failure predicate を使う場合に stabilizer 不変性を仮定しないこと、stabilizer flip カーネルを使うなら利用者がそれを確かめる責任があることを、該当箇所のコメントに書く。
5. `tests/test_examples_templates.py` では、既定のままの実行に加えて、わざと壊した入力（可換でない `hx, hz`、正規化されないノイズ、長さの違うデコーダー出力）で検査が止まることを確かめる。壊し方はテスト側で環境変数や引数を通して与え、テンプレート本体に壊れた例を置かない。

受入条件。4 本の実行と実測時間、壊した入力での停止テスト、`docs/tutorial_en.md` との記述の整合（食い違いがあれば完了メモに）。

依存。なし。

### WP-I Jupyter notebook

目的。説明と図を見ながら読めるチュートリアルを用意する。

方針。

- notebook は `examples/` を import しない（`examples/` は wheel に入らない）。各 notebook は自己完結で、使う設定値はマニフェストの対応する例と揃える。
- 先頭のパラメータセルで `QUICK = os.environ.get("MCMC4QEC_QUICK") == "1"` を読み、CI では縮小設定で実行する。
- 実行済みの出力（図を含む）をコミットする。1 notebook 3 MB 以内とし、図は PNG で dpi を抑える。出力は `notebooks/regenerate.py` で、既定設定の全 notebook を上から順に実行し直して保存できるようにする。
- CI とテストは notebook を実行するだけで、コミット済みの出力との差分は取らない（Windows と ubuntu で数値が変わりうるため）。
- 本文の説明は英語。第 2 節の注意を該当するセルの説明に含める。

作業内容。マニフェストの 4 本、`notebooks/regenerate.py`、`tests/test_notebooks.py`（`nbclient` が無ければ skip、`MCMC4QEC_QUICK=1` で全 notebook を実行、1 本 60 秒以内）。

受入条件。4 本が既定設定で 3 分以内、quick で 60 秒以内に通ること（実測）、サイズ、出力を消した状態から `regenerate.py` で再生成できること。

依存。なし。

### WP-J README

目的。初めて来た人が、目的に合った例・notebook・テンプレートにたどり着けるようにする。

作業内容。

1. トップ `README.md`（英語、一次版）を拡充する。既存の冒頭 3 行、quick-start の 2 つのコードブロック、対応表、制約の記述は残し、次を加える。インストールと extras の一覧（`plot`、`notebooks` を含む）、「目的別の入口」（`P_L` を出したい、条件付き分布を調べたい、自分の符号を持ち込みたい、回路レベル）から該当する例・notebook・テンプレートへのリンク、`examples/README.md` と `notebooks/` への案内。README 全体は長くしすぎず、詳細は `examples/README.md` と `docs/` に回す。
2. `README_ja.md` を新規作成する。英語版と同じ構成・同じ主張の日本語版で、1 文 1 行。冒頭に「英語版が一次版であり、食い違う場合は英語版に従う」と書く。コードブロックは英語版と一字一句同じにする。
3. `examples/README.md` を新規作成する。マニフェストの全ファイルを、目的、extras、既定と `--quick` の実行時間、出力の読み方、第 2 節のどの注意が関係するかの表で並べる。既存 6 本も含める。実行時間は各 WP の実測値が出たらメインが埋める（WP-J は列だけ用意する）。
4. `tests/test_docs_manifest.py` を作る。`examples/` 以下と `notebooks/` 以下の全 `.py` / `.ipynb` が `examples/README.md` に載っていること、逆に載っているものが存在すること、`README.md`、`README_ja.md`、`examples/README.md` の相対リンクが解決すること、`README_ja.md` の python コードブロックが `README.md` と同一であることを確かめる。
5. 研究論文は「in preparation」、引用情報・ライセンス・公開は未確定のまま書く。

受入条件。`test_docs_manifest.py` が統合後に通ること、README のコードブロックが installed wheel で動くこと（`verify_wheel.py` 経由、メインが実行）、英語版と日本語版の構成の一致。

依存。他の WP の実物には依存せず、マニフェストに対して書く。統合は最後に行い、そこで実物との食い違いを直す。

## 7. Phase 2（メインが統合後に行う）

1. H → F → G → I → J の順に main へ merge する。各 merge の後に `python -m pytest tests -q` を通す。
2. 完了メモの依頼に従い、`pyproject.toml` に extras（`plot`、`notebooks`）を追加する。version は `0.1.0.dev3` にする。
3. `.github/workflows/tests.yml` を更新する。core job は extras 不要の例を `--quick` で、optional job は全例を `--quick` で実行し、`MCMC4QEC_QUICK=1` で notebook を実行する（notebook 用の extras を optional job に入れる）。
4. `docs/wp/verify_wheel.py` を更新する。サブディレクトリの例を含め、例は `--quick` で実行する。README の python ブロックは英語版だけを実行し、`README_ja.md` は同一性テストで担保する。
5. `examples/README.md` の実行時間の列を各 WP の実測値で埋める。
6. 新しい venv を 2 つ作り、core のみと optional 依存（`matching, bposd, codes, stim, plot, notebooks`）で wheel を install し、`pytest --override-ini pythonpath= tests -q` と `verify_wheel.py core|optional` を実行する。
7. `CHANGELOG.md` に 0.1.0.dev3 の変更を書く。`AGENTS.md` の File layout に `examples/workflows/`、`examples/templates/`、`notebooks/`、`README_ja.md` を追記する。`docs/handoff/IMPLEMENTATION_STATUS.md` に今回の結果を追記する（既存の記述は書き換えない）。
8. main を `origin/main` に push し、GitHub Actions の全 job の結果を確認して報告に含める。
9. 使い終わった worktree と `wp/f`〜`wp/j` ブランチは、main に内容が入っていることを `git cherry` で確かめてから削除する。

## 8. 最終報告の形式

`docs/wp/final_report_examples_ja.md` に、日本語、1 文 1 行で次の順に書く。

1. 到達点を 5 行以内で。
2. WP ごとの表。列は、作ったもの、実行した検証（コマンドと結果）、未実施、レビューの指摘と対応。
3. 全例と notebook の実行時間の表（既定と quick）。
4. 統合後の tests 件数と時間、wheel 検証、CI の結果。
5. 見つかったライブラリの不具合や足りない API と、その扱い（直した、未対応）。
6. 所有者の判断待ち事項と次の依頼候補。

## 9. 参照

- 公開文書。`LIB/README.md`、`LIB/docs/api_en.md`、`LIB/docs/tutorial_en.md`
- dev2 の記録。`LIB/docs/wp/final_report_ja.md`、`LIB/docs/wp/validation_dev2_ja.md`、`LIB/docs/performance_ja.md`、`LIB/docs/convergence_ja.md`、`LIB/docs/crossval_research_ja.md`、`LIB/docs/circuit_baseline_ja.md`
- 検証の仕組み。`LIB/docs/wp/verify_wheel.py`、`LIB/.github/workflows/tests.yml`
- 前回の依頼書。`LIB/docs/dev_request_2026-09-30.md`
- 研究側（読み取り専用）。`RESEARCH/paper/main.tex` の Setup 節
