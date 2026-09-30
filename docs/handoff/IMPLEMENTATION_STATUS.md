# RIMC ライブラリ: 引き継ぎ後の進捗

2026-09-30。元の HANDOFF.md は過去時点の記録として保持。
ユーザーの「引き継いで」「初期段階から、段階的にやってって」で再開し、
「サブエージェント使って並列」の追加指示に基づき3エージェントへ分担した。

## 到達点

独立パッケージ rimc-library/ で bit-flip 基盤を検証後、depolarising、phenomenological、
BAR、Stim DEMへ段階的に拡張。現在版は 0.1.0.dev1。全仕様・公開準備の完成宣言ではない。

- CSS/有限カテゴリ状態・正規化ノイズ・decoder・独自failureの共通契約。
- I/X/Y/Zの同時分布、clean開始とperfect/noisy終端を明示する時空間モデル。
- OBF/Z/H/静的stabilizer。MHは全密度と提案比、独自failureを再評価。
- Z .7/H .3/k2/1 replicaを既定化。別のlazy .05と展開後設定も保存。
- exact/directMC/conditional MCMC、seed系列、JSON、行列hash・source hash・診断。
- 極小のexact確率を対数で保持し、underflowを空失敗集合と区別。
- 一般log_probによるBAR、固定failureとp依存decoderの明示近似mode、block bootstrap。
- PyMatching/BP-OSD object wrapper、sector分割、履歴全体の明示変換。
- Stim DEMの各error機構と^相関保持、p族の機構順序・署名・H/L検証。
- 英語README/例、日文設計・制約、wheel型CI定義、暫定引用情報。

設計・制約: rimc-library/docs/initial_library_ja.md。
最新検証: rimc-library/docs/validation_initial_ja.md。
最初のbit-flip版の検証: rimc-library/docs/validation_stage1_ja.md。

## パスと実行

- package: C:/Users/user/Documents/Codex/2026-09-30/task/rimc-library
- source: rimc-library/src/rimc/、tests: rimc-library/tests/
- current wheel: rimc-library/dist/rimc-0.1.0.dev1-py3-none-any.whl
- 最初の到達点のwheel: rimc-library/dist/rimc-0.1.0.dev0-py3-none-any.whl
- core-only installed environment: rimc-library/.venv-core/
- optional-decoder installed environment: rimc-library/.venv-decoders/
- spec: 既存 spec/RIMC_ライブラリ仕様書_v0.1.md（本文v0.2）
- Python: C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe

source test: python -m pytest tests/ -q
installed-wheel test: .venv-core/Scripts/python.exe -I -m pytest --override-ini pythonpath= tests/ -q
bit-flip / 三種ノイズ / DEM の例は examples/。

新packageはGit初期化していない。研究cloneと A:/dev/RIMC は変更しない。
commit/push/publish、重いMC sweep、clusterジョブ、global依存インストールは行っていない。

## 次段階・残る境界

1. 研究runnerの引数/返値を維持する互換wrapperと既存tests全体の移植は未実施。
   既存研究runnerは変更せず、新APIを独立検証した。旧既定Z+PTはそのまま。
2. 現実的サイズの性能と混合特性、BAR block長/ladder/anchorへの感度は今後の研究課題。
   短いsmoke例の近似区間は厳密値を外れることもあり、有限標本一致を保証と扱わない。
3. 物理回路の排他fault baseline、論文の2d round/前半d補正を合わせた比較、Z/H拡張は未実装。
   DEM接続から論文回路の再現成功とは主張しない。回路stabilizerは対象外。
4. 正式名称、license、公開先、第三者権利、正式著者情報は未決。
   CITATIONはdraft。remote CIは定義のみで未実行。公開承認は受けていない。

## 継続時の注意

Zは一般log densityを全近傍で評価する参照実装で、大規模性能を主張しない。
確率的decoderは対象外。モデルに束縛されたnoiseの取り違えはmetadata比較で拒否する。
任意callableの実装・識別子を利用者が保持する。結果だけからcallableを再構成しない。
新コードのsource_commitは未commitのためnull。package_source_sha256と研究参照commitは別保存。
MCMCは条件付き分布であり、単独で絶対P_Lを求めない。BAR近似modeのbiasは区間に含まれない。

## 2026-09-30 開発依頼書の実行開始後の追記

上記は 2026-09-30 午前時点の引き継ぎ記録として保持する。
現在は `C:/dev/mcmc4qec` の開発依頼書に従い、WP-A〜E を別 worktree で進めている。
開始時の main と origin/main は `93ebb5932db99debe6f77c783510396402c23823` で一致し、既存 142 テストは 54.09 秒で成功した。
Phase 0 の toric / surface ファクトリと受入試験を main に追加した。
研究の非単位な論理交差行列を保つため、従来の paired 既定に加えて明示的な independent 基底指定を実装し、独立レビューの指摘を修正した。
回路サブパッケージを含む再帰的ソース hash と公開契約の docstring を補った。
main `f5323c1` の全 suite は 164 passed、40.40 秒だった。
ユーザーが著者を `junichi haruna` と明示し、WP-D で CFF 検証成功の報告を受けた。
各 WP の実装・独立レビュー・main 統合、dev2 wheel の別環境検証、version 更新、push、remote CI、最終報告は未完了である。
研究リポジトリ `C:/dev/RIMC` は変更せず、直近の git status も clean だった。
今回の検証と判断の詳細は `docs/wp/phase0_ja.md` と `docs/wp/integration_ja.md` に記録した。

## 2026-09-30 12:05 JST ユーザー指定の中断

ユーザーが一旦中断して後日再開できるようにすることを指示したため、実装と並列担当を停止した。
未完了の A/C/E を各 worktree の checkpoint commit に保存し、B/D の既存成果とレビュー記録も保持した。
再開の起点、各 HEAD、未完了レビュー、merge の注意点と残る達成条件は `docs/wp/RESUME_ja.md` に記録した。
ユーザーの再開指示までは作業を再開しない。
main への WP 統合、dev2 最終 wheel 検証、push、remote CI、最終報告は未完了である。
