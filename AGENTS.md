# AGENTS.md — mcmc4qec

Think in English, interact with the user in Japanese.

## Project

`mcmc4qec` は、量子誤り訂正の論理誤り率を希少事象サンプリングで求めるための Python ライブラリ。研究リポジトリ RIMC（`junichiharuna/RIMC`、論文 "Trustworthy rare-event splitting for general quantum codes"）から再利用できる中核を切り出し、他の研究者が自分の符号・ノイズ・デコーダーを持ち込めるようにするのが目的。
状態は 0.1.0.dev2 の pre-alpha（2026-09-30 に旧仮称 `rimc` から改名）。CSS 符号上の bit-flip、depolarising、phenomenological の三種のノイズ、OBF / Zanella（Z）/ cluster exchange（H）/ stabilizer flip のカーネル、exact 列挙、direct MC、失敗条件付き MCMC、BAR による splitting、PyMatching / BP-OSD / Stim DEM の接続が入っている。公開既定は Z 0.7 / H 0.3 / cluster_k=2 / 1 chain。
dev2（2026-09-30 の開発依頼 WP-A〜E、全て main に統合済み）で、実符号ファクトリ（toric / surface / asymmetric toric / Hamming HGP / BB72・108・144 / Steane / 連接 Steane）と MWPM・BP-OSD デコーダー構築、研究コードとの数値照合、product-noise の Zanella 高速化と decode キャッシュ、複数 chain 診断と収束チェック、exact coset 初期化、物理回路 fault baseline、英語の API / チュートリアル文書が入った。公開 API は 65 名。remote CI（Python 3.11 / 3.12 × core / optional の 4 job）は成功済み。
残る課題は研究 runner との速度差、実符号での混合診断と BAR ladder / block 長の感度評価、回路 baseline の拡張と物理配置を保った Z/H 提案、型注釈と `py.typed`。所有者判断待ちの事項と次の依頼候補は `docs/wp/final_report_ja.md` 第 5・6 節、経緯は `docs/handoff/IMPLEMENTATION_STATUS.md` の追記にある。

## File layout

- `src/mcmc4qec/` — パッケージ本体（import 名 `mcmc4qec`）。`core.py`（Model / Noise / Decoder / FailurePredicate の契約、`CSSCode`、`Problem`）、`noise.py`・`noise_categorical.py`（bit-flip、Pauli カテゴリ、phenomenological のノイズ）、`models.py`（depolarising と spacetime モデル）、`kernels.py`（OBF / Z / H / stabilizer、一般 MH）、`sampling.py`（`exact`、`direct_mc`、`sample_faulty`、config と seed 系列）、`estimation.py`（BAR、`estimate_logical_error`、block bootstrap）、`diagnostics.py`（IAT / ESS / split R-hat）、`results.py`（JSON 往復する Result と provenance）、`adapters.py`・`adapter_composition.py`（PyMatching / BP-OSD の wrapper、sector と履歴の合成）、`stim_dem.py`（DEM からのモデル構成）、`codes.py`（符号ファクトリ）、`decoders.py`（MWPM / BP-OSD / sector 復号の構築）、`fastpath.py`・`decode_cache.py`（product-noise の Zanella 高速経路と decode キャッシュ）、`convergence.py`（複数 chain 診断と `evaluate_convergence`）、`initial_states.py`（exact coset 初期化）、`circuit/`（物理回路 fault の `model.py`・`proposal.py`・`baselines.py`）
- `tests/` — pytest。optional 依存込みで 268 passed / 4 skipped、全 suite は約 45〜80 秒（2026-09-30 時点）。小規模列挙で正規化・提案比・詳細釣合い・失敗条件を検証するのが流儀
- `examples/` — `bit_flip.py`、`three_noise.py`、`bar_ladder.py`（core のみで動く）、`toric_pymatching.py`、`stim_dem.py`、`circuit_baseline.py`（optional 依存が要る）
- `examples/workflows/` — BAR 曲線、条件付き重み、複数 chain 診断、p 依存 decoder の研究ワークフロー
- `examples/templates/` — 符号・ノイズ・decoder・Stim DEM の持ち込み用テンプレートと実行前検査
- `notebooks/` — 実行済みの英語チュートリアル4本と `regenerate.py`（既定出力の再生成、CI用quick実行）
- `README_ja.md` — 英語版READMEと同じ構成の日本語案内（英語版が一次版）、`examples/README.md` — 実行例・notebookの一覧と実測時間
- `benchmarks/bench_step.py` — 1 ステップの速度計測
- `docs/` — `api_en.md`・`tutorial_en.md`（英語の公開文書）と日本語の設計・検証記録。`initial_library_ja.md`（設計と制約）、`stage1_ja.md`・`validation_stage1_ja.md`・`validation_initial_ja.md`（dev0 / dev1 時点）、`crossval_research_ja.md`・`performance_ja.md`・`convergence_ja.md`・`circuit_baseline_ja.md`（dev2 の各分野）、`dev_request_2026-09-30.md`（開発依頼書）、`wp/`（WP-A〜E の完了メモとレビュー、`integration_ja.md`、`validation_dev2_ja.md`、`final_report_ja.md`）
- `docs/handoff/` — 2026-09-30 の Codex からの引き継ぎ。`HANDOFF.md`、`IMPLEMENTATION_PLAN.md`、`IMPLEMENTATION_STATUS.md`、`spec/RIMC_ライブラリ仕様書_v0.1.md`（ファイル名は v0.1、本文は v0.2。仕様の一次資料）
- `.github/workflows/tests.yml` — installed wheel を Python 3.11 / 3.12 で試す CI（core のみ、optional 依存あり）。push で走り、2026-09-30 の run 36675225072 で全 4 job 成功
- `pyproject.toml`、`CHANGELOG.md`、`CITATION.cff`（著者名 `junichi haruna` はユーザー指定で確定、所属・DOI・リリース情報は未確定）、`CONTRIBUTING.md`
- `build/`、`dist/`、`output/`、`.venv*/`、`*.egg-info/` は gitignore

## Run

- Python 3.11 を絶対パスで使う（`C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe`）。`python3` は Windows Store のスタブなので使わない
- テスト：`python -m pytest tests -q`（`pyproject.toml` の `pythonpath = ["src"]` で source を読む）
- installed wheel の検証：`python -m build --wheel` → 別 venv に install → `python -m pytest --override-ini pythonpath= tests -q`
- optional 依存：`pymatching>=2.4,<3`、`ldpc>=2.4,<3`、`stim>=1.16,<2`。無い環境では該当テストが skip される
- 計算は軽いものだけ。1 テストファイル 60 秒以内、全 suite 5 分以内。重い sweep やクラスタジョブはこのリポジトリではやらない

## Conventions

- 科学的な変更は「小さい仕様 → 受入テスト → 実装」の順。提案・密度・状態表現を触るときは、列挙できる例で正規化、support、順向き / 逆向き提案確率、詳細釣合い、共有 failure 定義を確認する。既約性と周期性は詳細釣合いとは別に調べる
- 棄却を含む全ステップを chain に残す。混合確率を暗黙に再正規化しない。decoder 出力の意味を型や長さから推測しない。独自 failure predicate の stabilizer 不変性を仮定しない。相関ノイズを独立セクターで置き換えない。近似（p 依存 decoder の BAR など）は結果に明示して記録する
- 診断が良くても収束・エルゴード性・正しさの証明にはならない。warnings にその旨を残す
- 日本語文書は 1 文 1 行（文の途中で改行しない）。README と docstring は英語
- 数値の一致、性能、テスト成功は実行して確認してから書く。未実行は「未実施」と書く
- Claude Code の Bash ツールはヒアドキュメント中のバックスラッシュを壊す。バックスラッシュを含むファイルは Write / Edit ツールで書く
- Commit / push はユーザーに頼まれたときだけ。コミットメッセージ末尾に `Co-Authored-By` と `Claude-Session` のフッターを付ける

## Do not

- 研究リポジトリ RIMC（`C:\dev\RIMC` または `A:\dev\RIMC`）を変更しない。読み取り専用で参照する。研究側の runner の既定（Z+PT）も変えない
- LICENSE を追加しない、PyPI 等に publish しない、リポジトリを public にしない、著者の所属・DOI などの引用情報を確定しない。これらは所有者（春名）が決める
- `docs/handoff/` の引き継ぎ文書と仕様書を書き換えない（過去時点の記録として保持）。更新は `IMPLEMENTATION_STATUS.md` に追記する
- 引き継ぎ文書や仕様に書かれた研究上の主張を、独立に検証した事実として扱わない
