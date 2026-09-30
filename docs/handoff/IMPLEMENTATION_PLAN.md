# 実装計画（作業用）

仕様 v0.2 を基準に独立ディレクトリ `rimc-library` へ実装する。
研究 clone と A:/dev/RIMC は変更しない。commit/push/publish は行わない。

1. 受入テストを先に置く。小規模有限状態で確率、境界、失敗集合、詳細釣合いを検証。
2. 明示的なカテゴリ状態空間、CSS/spacetime、正規化 noise、decoder 契約。
3. 対称 OBF、平方根平衡 Z、同一状態内 H、静的 stabilizer と MH。
4. exact / fixed-budget direct MC / conditional MCMC / BAR / 診断 / JSON metadata。
5. 外部 decoder wrapper と相関を保持する Stim DEM 接続。
6. wheel の別環境導入、例、文書、CI、制約と検証結果を記録。

ユーザー回答:「初期段階から、段階的にやってって」。まず静的 bit-flip 基盤を独立した
検証済みの到達点にする。depolarising/phenomenological/BAR/Stim/回路は後続段階。
ユーザーの追加指示により、adapter、独立検証、文書・例を3サブエージェントへ分担。
phenomenological は clean initial / perfect または noisy final を必須指定。
全ノイズで latent state は flat categorical vector、decoder input は model が構成。
カーネルの汎用実装は correctness reference とし、大規模性能を主張しない。

実施結果: bit-flip基盤dev0をwheel検証後、三種のノイズ/BAR/DEMへdev1として拡張。
source・optional付きwheelは142 tests passed、core-only wheelは130 passed / 7 skipped。
最新進捗はIMPLEMENTATION_STATUS.md、数値検証はrimc-library/docs/validation_initial_ja.md。
