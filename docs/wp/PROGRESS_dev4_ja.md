# dev4 進捗

依頼の一次資料は `docs/dev_request_2026-10-01.md` とする。
再開時はこのチェックリストの最初の未完了項目から、実ファイル・git・実行結果を確認する。
完了日時は JST で記録する。

## Phase 0

- [ ] main と origin/main の一致、研究リポジトリの clean 状態、基準全 suite の件数・秒数を確認する。
- [x] 2026-10-01 進捗表を作成する。
- [x] 2026-10-01 共通制約と各 WP の担当・受入条件を含む指示文を保存する。
- [ ] K〜O の独立 worktree を作成し、担当を起動する。

## WP と統合（K → N → L → M → O）

- [ ] K 実装・受入検証・完了メモ。
- [ ] K 独立レビュー記録。
- [ ] K 指摘への対応・main 統合・全 suite。
- [ ] N 実装・等価性検証・実測・完了メモ。
- [ ] N 独立レビュー記録。
- [ ] N 指摘への対応・main 統合・全 suite。
- [ ] L 実装・詳細釣合い検証・実測・完了メモ。
- [ ] L 独立レビュー記録。
- [ ] L 指摘への対応・N 統合後への rebase・等価性再検証・main 統合・全 suite。
- [ ] M 真値比較・20 seed 以上・各仮説と感度・被覆試験・指針・完了メモ。
- [ ] M 独立レビュー記録。
- [ ] M 指摘への対応・main 統合・全 suite。
- [ ] O 公開 API と公開メソッドの注釈・py.typed・型検査・完了メモ。
- [ ] O 独立レビュー記録。
- [ ] O 指摘への対応・統合済み main への rebase・型検査・main 統合・全 suite。

## Phase 2

- [ ] 公開 API・英日 README・API 文書・例一覧・pyproject・CI を統合し版を dev4 にする。
- [ ] M の指針を pl_curve と notebook 02 の説明へ反映し notebook を再生成する。
- [ ] verify_wheel.py を新例・型情報に対応させる。
- [ ] 統合後全 suite と時間予算（各ファイル60秒、増分60秒、全体300秒）を確認する。
- [ ] 新規 core venv に wheel を導入し全 suite と verify_wheel.py core を実行する。
- [ ] 新規 optional venv に wheel を導入し全 suite と verify_wheel.py optional を実行する。
- [ ] CHANGELOG・AGENTS を更新し IMPLEMENTATION_STATUS に追記する。
- [ ] 検証済み main を origin/main へ push し remote CI 全 job の成功を確認する。
- [ ] git cherry と clean 状態を確認して統合済み worktree と wp/k〜wp/o を削除する。
- [ ] 研究リポジトリの clean 状態と依頼全項目の完了証拠を監査する。
- [ ] final_report_dev4_ja.md を指定形式で作成し全項目の完了を記録・コミットする。

## 実行記録と再開情報

2026-10-01、開始時の main と origin/main は `c6cff9232cff3046d4643d2adbb95baba02d9a9b` で一致した。
依頼書のみ未追跡で、実装の既存変更はなかった。
`A:/dev/RIMC` の `git status --short` は空だった。
基準試験は指定 Python 3.11 の `-m pytest tests -q --junitxml=output/dev4-phase0.xml` で実行中。
環境上の同時実行上限はメインを含め4体であり、依頼書の5担当同時起動は3担当ずつの段階起動に置き換える。
サブエージェントの `gpt-sol` 指定は利用可能な `gpt-6-sol` を使用し、WP-K/L/M/N は high、WP-O は medium、L/N のレビューは xhigh とする。
main のモデルはセッションで設定されたものを使用し、このツールからは変更できない。
