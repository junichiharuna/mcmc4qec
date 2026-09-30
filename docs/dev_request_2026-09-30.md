# mcmc4qec 開発依頼書（Codex goal 用）

作成日 2026-09-30。対象リポジトリは `junichiharuna/mcmc4qec`（private）。
この文書を Codex の goal としてそのまま渡す。メインモデルは astra、サブエージェントは gpt-sol を使う。

## 0. 依頼の要約

`mcmc4qec` を「QEC 研究者が自分の符号・ノイズ・デコーダーで使える MCMC ライブラリ」として初期公開できる状態まで進める。
現状は 0.1.0.dev1 で、三種のノイズ（bit-flip、depolarising、phenomenological）、OBF/Z/H/stabilizer flip、exact/direct MC/条件付き MCMC、BAR、PyMatching/BP-OSD/Stim DEM 接続が実装済みで 142 tests が通っている。
ただし例は 2 量子ビットの玩具符号だけで、実符号のファクトリ、研究コードとの数値照合、性能、複数 chain 診断、回路レベル baseline、公開文書が欠けている。
この依頼では、その欠けを 5 つの作業パッケージ（WP）に分け、可能な限り並列に埋める。

成果物は次の 4 つ。

1. main ブランチに統合された実装とテスト（全 tests 緑、wheel を別環境に入れて例が動く）。
2. 各 WP の検証記録（日本語、`docs/wp/` 配下）。
3. 更新された README（英語）、`docs/handoff/IMPLEMENTATION_STATUS.md`、CHANGELOG。
4. 最終報告（日本語）。実行した検証だけを合格として書く。

## 1. 前提と制約

- ライブラリのリポジトリは `C:\dev\mcmc4qec`（研究室 PC）または `A:\dev\mcmc4qec`（自宅 PC、未 clone なら `git clone git@github.com:junichiharuna/mcmc4qec.git`）。以下 `LIB` と書く。
- 研究リポジトリ RIMC は `C:\dev\RIMC` または `A:\dev\RIMC` にある。以下 `RESEARCH` と書く。**読み取り専用**で、1 ファイルも変更しない。`git status` が clean のまま終わること。
- Python は 3.11 の絶対パスを使う（`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe`）。`python3` は使わない。
- 計算は軽いものだけ。1 テストファイルは 60 秒以内、全 suite は 5 分以内、ベンチマークは 1 本 10 分以内。クラスタ投入、巨大 sweep、長時間ジョブはしない。
- ライセンスの選択と追加、PyPI 等への publish、リポジトリの公開化、著者情報の確定は**しない**。これらは所有者が決める。
- 日本語文書は 1 文 1 行で書く（文の途中で改行しない）。README と docstring は英語。
- 数値の一致、性能改善、テスト成功は実行して確認してから書く。未実行のものは「未実施」と明記する。
- 仕様の一次資料は `LIB/docs/handoff/spec/RIMC_ライブラリ仕様書_v0.1.md`（本文は v0.2）。設計方針は `LIB/docs/initial_library_ja.md`、直近の検証は `LIB/docs/validation_initial_ja.md`、前回の引き継ぎは `LIB/docs/handoff/HANDOFF.md` と `IMPLEMENTATION_STATUS.md`。着手前に全部読む。

## 2. モデル構成と並列運用

### 2.1 役割

- **メイン（astra）**: 全体の指揮、Phase 0 の準備、ブランチの統合、共有ファイルの編集、最終検証と報告。自分で大きな実装はしない。
- **サブエージェント（gpt-sol）**: WP ごとに 1 体を同時に起動する（5 体）。各 WP 内でさらに独立な部分があれば最大 2 体まで追加してよい。同時実行の上限は 8 体。
- **レビュー担当（gpt-sol）**: 各 WP が完了したら、別のサブエージェントに差分を敵対的にレビューさせる（詳細釣合い、正規化、境界条件、テストが本当に主張を検証しているか）。指摘は WP 担当が対応し、メインが最終判断する。

### 2.1.1 reasoning effort

| 役 | effort | 理由 |
| --- | --- | --- |
| メイン（astra） | high | 毎反復で呼ばれる指揮・統合・裁定の役。xhigh は反復あたりの時間が伸びて全体が遅くなり、medium は merge 時の判断が雑になる |
| gpt-sol WP-A / B / C / E | high | 詳細釣合い、提案比、回路モデルの線形合成など、間違えると数値が静かにずれる作業 |
| gpt-sol WP-D | medium | 文書と CI は判断より作業量で、high にしても質が上がりにくい |
| レビュー担当（WP-B と WP-C の差分） | xhigh | 1 回きりで、数学的な穴を探す仕事。ここだけ重くする |
| レビュー担当（WP-A / D / E の差分） | high | |

役ごとに effort を変えられない環境では全体を high にする。その場合、レビュー担当への指示文に「詳細釣合いと正規化は数値で反証を試みる」と明記して xhigh の代わりにする。

### 2.2 作業の分離

- WP ごとに git worktree を作る。`git worktree add ../mcmc4qec-wt/<wp> -b wp/<wp>`。作業は worktree 内だけで行う。
- 共有ファイル `src/mcmc4qec/__init__.py`、`pyproject.toml`、`CHANGELOG.md`、`README.md` は WP 担当が直接編集しない。追加したい公開名や記述は WP の完了メモに書き、メインが統合時に反映する（README だけは WP-D が担当）。
- 各 WP は担当ファイルの外を編集しない。どうしても必要なら完了メモに理由と最小 diff を書いてメインに委ねる。
- WP は完了時に `docs/wp/<wp>_ja.md` を書く。内容は、実装したこと、実行した検証（コマンドと結果の数値）、未実施、メインへの依頼（公開名の追加など）。
- コミットは worktree のブランチに自由に行う。メッセージは英語で 1 行要約。push はメインが最終検証後に main だけ行う。ほかの remote 操作はしない。

### 2.3 統合の順序

メインは A → B → E → D → C の順に main へ merge する。
各 merge の後に `python -m pytest tests -q` を通す。全部の merge が終わったら Phase 2 の検証を行う。

## 3. Phase 0（メインが最初に行う、30 分以内）

1. `LIB` の main が `origin/main` と一致し、142 tests が通ることを確認する。
2. `src/mcmc4qec/codes.py` を新規作成し、`RESEARCH/src/css_code.py` の `make_toric_code(d)` と `make_surface_code(d)` だけを `mcmc4qec.CSSCode` を返す形で移植する。`[[n,k,d]]` と `hx @ hz.T = 0` を確認する最小テスト `tests/test_codes.py` を付ける。これは WP-A/B/D の共通の足場になる。
3. `docs/wp/` を作り、この文書の WP 節をもとに各 WP の指示文をサブエージェントに渡す。指示文には、担当ファイル、受入条件、制約（第 1 節）、完了メモの書式を含める。
4. 5 体を同時に起動する。

## 4. 作業パッケージ

### WP-A 実符号ファクトリと研究コードとの数値照合

目的。公開ライブラリが論文と同じ符号で動くことを示し、研究コードと数値が合うことを確認する。

担当ファイル。`src/mcmc4qec/codes.py`（Phase 0 の続き）、`src/mcmc4qec/decoders.py`（新規）、`tests/test_codes.py`、`tests/test_decoders.py`、`tests/test_crossval_research.py`、`docs/wp/A_ja.md`、`docs/crossval_research_ja.md`。

作業内容。

1. `RESEARCH/src/css_code.py` から次を移植する。`make_asymmetric_toric_code(d1,d2)`、`make_hgp_hamming()`、`make_bb_code(...)` と `make_bb_code_72/144`（BB[[108,8,10]] も研究コードにあれば含める）、`make_steane_code()`、`make_concatenated_steane_code(levels)`。研究コードの行列と byte 単位で一致することをテストで確認する。
2. `decoders.py` に、既存の `PyMatchingAdapter` と generic wrapper を使って `mwpm_decoder(code)`、`bposd_decoder(code, p, **kw)`、depolarising 用の sector 版を作る。研究コードの `make_mwpm_decoder`、`make_bposd_decoder`、`make_depolarizing_mwpm_decoder` と、同じ syndrome に同じ補正（または同じ論理予測）を返すことを、小さい符号の全 syndrome で照合する。
3. 数値照合を 3 段階で行い、結果を `docs/crossval_research_ja.md` に表で記録する。
   - toric d=3 の exact `E[w|faulty]` と `P_L` を `mcmc4qec.exact` で計算し、`RESEARCH/compare/exact_ew.py` の値と一致させる（同じ MWPM、同じ failure 定義）。
   - `RESEARCH/cluster_results/direct_mc_ew.csv` のうち数十秒で再現できる行（小さい符号、p が 1e-2 以上）を選び、`mcmc4qec.direct_mc` の `P_L` と `E[w]` が誤差の範囲で一致することを確認する。
   - toric d=5 と BB72 の p=1e-2 で Z+H（Z 0.7 / H 0.3 / k=2）の `E[w|faulty]` が exact または direct MC と一致することを確認する。chain は短くてよいが、区間が真値を含むかを記録する。
4. 研究 tests のうちライブラリの意味論に対応するものを新 API に移植する。対象は `test_css_code.py`、`test_balancing.py`、`test_depolarizing_cluster.py`、`test_rimc_mixed.py`（振る舞いの等価物）、`test_splitting_pl.py`（同じ合成トレースに対する BAR の値）、`test_metrics.py`、`test_diagnostics.py`、`test_postprocess.py`。移植できないものは理由を表にする。

受入条件。全符号の `[[n,k,d]]` と可換性のテスト、研究行列との一致テスト、exact 一致、direct MC 一致（何行を何秒で）、Z+H の一致、移植テストの一覧と件数。

依存。Phase 0 の `codes.py`。ほかの WP には依存しない。

### WP-B 性能。product ノイズの高速経路とデコード cache

目的。現在の Z カーネルは全近傍を一般 `log_prob` で評価する参照実装で、実符号では遅い。研究コードと同程度の速度を出す。

担当ファイル。`src/mcmc4qec/kernels.py`、`src/mcmc4qec/fastpath.py`（新規）、`src/mcmc4qec/decode_cache.py`（新規）、`tests/test_fastpath.py`、`benchmarks/`（新規）、`docs/wp/B_ja.md`、`docs/performance_ja.md`。`sampling.py` は必要最小限の接続だけ変更し、変更箇所を完了メモに列挙する。

作業内容。

1. ノイズが座標ごとの独立積（`IndependentBitFlip`、`DepolarizingNoise`、phenomenological の独立座標）である場合、単一座標更新の密度比は閉じた式で出る。Z の近傍重み `sqrt(pi(y)/pi(x))` を全近傍について O(n) の算術で計算し、`log_prob` の全評価を避ける高速経路を作る。ノイズが product であることは型か明示フラグで判定し、任意 callable ノイズには適用しない。
2. syndrome から補正（または論理予測）への cache を作る。上限 `cache_cap` を持ち、上限到達時の方針（LRU または凍結）を設定に残す。研究コードの `cache_cap` と同じ意味にする。
3. 提案候補の failure 判定は、可能なら syndrome の差分更新（1 座標の反転なら `hz` の 1 列の XOR）で行う。
4. 高速経路と参照経路が同じ遷移確率を与えることをテストする。小規模問題で両経路の受理確率を全状態・全近傍で比較し、同じ seed で同じ軌道になることも確認する。
5. `benchmarks/bench_step.py` を作り、toric d=5、d=7、BB72 の p=1e-2 で 1 秒あたりのステップ数を、`RESEARCH/src/runners.py` の `run_rimc_mixed`（`p_zanella=0.7, p_cluster=0.3, n_replicas=1`）と比較する。研究コードは `sys.path` に `RESEARCH/src` を足して import するだけで、ファイルは変更しない。結果を `docs/performance_ja.md` に表で書く。

受入条件。等価性テストが通ること。ベンチマークで研究コードの 2 倍以内の時間か、届かない場合はプロファイルに基づく原因と次の手を記録すること。既存 142 tests が全部通ること。

依存。Phase 0 の toric ファクトリ。BB72 は WP-A の完成を待たず、ベンチマーク内で研究コードの `make_bb_code_72` を読み取り専用 import して使ってよい。

### WP-C 回路レベル baseline（arXiv:2509.13678 の独立実装）

目的。仕様の次段階である回路レベル splitting の baseline を、Stim DEM ではなく物理的な (location, fault) 配置で実装し、小規模で検証する。

担当ファイル。`src/mcmc4qec/circuit/`（新規サブパッケージ）、`tests/test_circuit_*.py`、`examples/circuit_baseline.py`、`docs/wp/C_ja.md`、`docs/circuit_baseline_ja.md`。

作業内容。

1. `CircuitFaultModel` を作る。入力は `stim.Circuit` と、ノイズを置く location の列挙規則。各 location は「無故障」または排他的な fault alphabet の 1 つを取る。配置の `log_prob` は location ごとの積で、alphabet の確率は明示引数で与える。
2. 配置から detector と observable への写像は、単一 fault の効果ベクトルを Stim で 1 回ずつ求め、Clifford 回路での GF(2) 線形性で XOR 合成する。合成の正しさは、ランダム配置を Stim で直接シミュレートした結果と照合するテストで確認する。
3. 論文第 III 節の提案（location を一様に選び、空なら追加、同じ fault なら削除、異なる fault なら置換）を実装する。受理は一般の MH 比で書き、論文の受理規則と一致するか、しない場合は差を `docs/circuit_baseline_ja.md` に書く。詳細釣合いは列挙可能な小回路で数値検証する。
4. 基準問題を 2 段階で用意する。第 1 段階は repetition code d=3 の 1〜2 ラウンドで、全配置を列挙して exact と照合する。第 2 段階は rotated surface code d=3、2d ラウンドの noisy syndrome extraction、前半 d ラウンドだけ補正する logical idle で、PyMatching（DEM から構築）を decoder とし、direct MC で失敗が十分観測できる p で `P_L` を比較する。論文の図表の再現は主張しない。
5. 既存の `sample_faulty`、`direct_mc`、`estimate_logical_error` からこのモデルが使えるように `Model`/`Noise` 契約に合わせる。合わない点は完了メモに書く。

受入条件。線形合成の照合テスト、詳細釣合いテスト、repetition code の exact 一致、surface d=3 の direct MC との一致（区間つき）、対応範囲と未対応（Z-OBF、cluster exchange、stabilizer flip は対象外）の明記。

依存。なし。`stim` と `pymatching` は optional 依存として扱い、無い環境では tests を skip する。

### WP-D 公開準備。README、API 文書、CI、パッケージ metadata

目的。初めて見る QEC 研究者が 10 分で使い始められる文書と、公開チェックの残項目を整える。

担当ファイル。`README.md`、`docs/api_en.md`（新規）、`docs/tutorial_en.md`（新規）、`CONTRIBUTING.md`、`CITATION.cff`、`.github/workflows/tests.yml`、`examples/toric_pymatching.py`（新規）、`examples/bar_ladder.py`（新規）、`docs/wp/D_ja.md`。`pyproject.toml` と `CHANGELOG.md` の変更案は完了メモに書く。

作業内容。

1. README を書き直す。冒頭 3 行で何ができるかを言い、次に toric d=5 と PyMatching で direct MC と Z+H を比べる 20 行以内の例、次に BAR ladder で `P_L(p)` を出す例、次に対応表（ノイズ × カーネル × decoder）、最後に制約（診断は収束の証明ではない、近似 BAR、未対応範囲）。研究論文への言及は「論文準備中」とし、引用情報は所有者確認待ちと書く。
2. 全公開シンボルの docstring を点検し、引数、返り値、例外、単位（実験全体の確率か 1 ラウンド当たりか）を揃える。`docs/api_en.md` に公開 API を一覧化する。
3. `docs/tutorial_en.md` に、独自符号（利用者の `hx, hz, lx, lz`）、独自ノイズ（`log_prob` の契約）、独自 decoder（output_kind と論理写像 L）の持ち込み方を、それぞれ動く最小例つきで書く。
4. `CITATION.cff` を schema-valid にする。著者名や DOI が未確定の項目は placeholder ではなく省略し、コメントで未確定と書く。`cffconvert --validate` が通ること。
5. CI を点検する。Python 3.11 と 3.12 の両方で installed wheel の tests が走ること、optional 依存ありの job が走ること。手元で `python -m build --wheel` と別 venv での `pytest --override-ini pythonpath= tests -q` を実行し、結果を記録する。remote CI の実行結果は、メインが push した後に確認する。
6. `pyproject.toml` に urls、keywords、classifiers、`py.typed` の追加案を書く。version は `0.1.0.dev2` に上げる案とする。

受入条件。README の例が installed wheel で動くこと（実行ログ）、api_en に漏れがないこと（`__all__` との突合テスト）、CITATION の validate 成功、wheel の別環境 tests 成功。

依存。Phase 0 の toric ファクトリ。WP-A の BB 符号が間に合えば README の対応表に載せる。

### WP-E 複数 chain の診断と収束判定

目的。論文で使っている収束判定（4 条件）と初期状態の取り方をライブラリの機能にする。

担当ファイル。`src/mcmc4qec/diagnostics.py`、`src/mcmc4qec/convergence.py`（新規）、`src/mcmc4qec/initial_states.py`（新規）、`tests/test_convergence.py`、`tests/test_initial_states.py`、`docs/wp/E_ja.md`、`docs/convergence_ja.md`。

作業内容。

1. `diagnose` を複数 `Result` に拡張する。chain 間の split R-hat、cross-chain 標準誤差（各 chain 平均を 1 標本として分散を取る）、各 chain の IAT と ESS、kernel ごとの受理率。
2. `convergence.py` に、`RESEARCH/compare/convergence_flags.py` と論文の Setup 節にある 4 条件を移植する。(i) 標本数を増やしたときの標準誤差の 1/sqrt(N) スケーリング、(ii) 定常到達（`RESEARCH/src/metrics.py` の `doubling_converged` 相当）、(iii) 異なる初期状態の chain 群の一致、(iv) direct MC の分散との比較による自己相関時間の過小評価検知。各条件は何を検知でき何を検知できないかを docstring と `docs/convergence_ja.md` に書く。全条件を満たしても収束の証明にはならない旨を返り値の warnings に必ず含める。
3. `initial_states.py` に、論文で使う初期化を実装する。最小重みの論理演算子代表（各論理量子ビットのコセット内で最小重みを選ぶ。RIMC の 2026-09-17 の議事録にある通り、インデックス 0 をそのまま使わない）、ランダムな論理セクター、最大重み側の初期状態。`sample_faulty` の `initial_state` に渡せる形にする。
4. 合成 chain（既知の自己相関を持つ AR(1) など）と、意図的に 2 つの盆地を持つ玩具問題で、各条件が期待通りに fail/pass することをテストする。

受入条件。合成データでの各条件のテスト、最小重み代表がコセット内で本当に最小であることの小符号での全列挙テスト、`docs/convergence_ja.md`。

依存。なし。`sampling.py` は変更しない。`initial_state` の受け渡しに変更が要る場合はメインに依頼する。

## 5. Phase 2（メインが統合後に行う）

1. 全 merge 後に `python -m pytest tests -q` を通す。所要時間を記録する。
2. 新しい venv を 2 つ作り、core のみと optional 依存ありで wheel を install し、`pytest --override-ini pythonpath= tests -q` と全 examples を実行する。
3. 各 WP の完了メモに書かれた公開名を `__init__.py` に反映し、`docs/api_en.md` との突合テストを通す。
4. `CHANGELOG.md` に WP ごとの変更を書く。version を `0.1.0.dev2` にする。
5. `docs/handoff/IMPLEMENTATION_STATUS.md` を現状に更新する。前回の内容は「2026-09-30 午前時点」として残す。
6. main を `origin/main` に push し、GitHub Actions の結果を確認して報告に含める。
7. 最終報告を書く。

## 6. 最終報告の形式

日本語、1 文 1 行。次の順に書く。

1. 到達点を 5 行以内で。
2. WP ごとの表。列は、実装、実行した検証（コマンドと結果）、未実施、レビューで出た指摘と対応。
3. 数値照合の表（WP-A）とベンチマークの表（WP-B）。
4. 統合後の tests 件数、wheel 検証、CI の結果。
5. 所有者の判断待ち事項。ライセンス、著者情報、公開先、Z+H の既定値の確定、phenomenological 境界の既定、その他。
6. 次の依頼候補。

## 7. 参照

- 仕様 v0.2。`LIB/docs/handoff/spec/RIMC_ライブラリ仕様書_v0.1.md`
- 設計と検証。`LIB/docs/initial_library_ja.md`、`LIB/docs/validation_initial_ja.md`、`LIB/docs/stage1_ja.md`
- 前回引き継ぎ。`LIB/docs/handoff/HANDOFF.md`、`LIB/docs/handoff/IMPLEMENTATION_STATUS.md`
- 研究コード（読み取り専用）。`RESEARCH/src/css_code.py`、`runners.py`、`kernels.py`、`splitting_pl.py`、`postprocess.py`、`metrics.py`、`diagnostics.py`、`RESEARCH/compare/exact_ew.py`、`convergence_flags.py`、`RESEARCH/cluster_results/direct_mc_ew.csv`、`RESEARCH/tests/`
- 論文（研究リポジトリ内）。`RESEARCH/paper/main.tex` の Setup 節（収束判定 4 条件、初期状態、Z+H の設定）
- 回路レベル splitting。Rare Event Simulation of Quantum Error-Correcting Circuits, arXiv:2509.13678v2
- 議事録。`RESEARCH/docs/meetings/2026-09-17_minutes.md`（論理 X の最小重み代表、用語）
