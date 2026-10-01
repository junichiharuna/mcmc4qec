# dev4 進捗

依頼の一次資料は `docs/dev_request_2026-10-01.md` とする。
再開時はこのチェックリストの最初の未完了項目から、実ファイル・git・実行結果を確認する。
完了日時は JST で記録する。

## Phase 0

- [x] 2026-10-01 main と origin/main の一致、研究リポジトリの clean 状態、基準全 suite の件数・秒数を確認する。
- [x] 2026-10-01 進捗表を作成する。
- [x] 2026-10-01 共通制約と各 WP の担当・受入条件を含む指示文を保存する。
- [x] 2026-10-01 08:59 JST K〜O の独立 worktree を作成し、担当を起動する（環境の4枠制約により段階起動）。

## WP と統合（K → N → L → M → O）

- [x] 2026-10-01 08:59 JST K 実装・受入検証・完了メモ（f9b7b93、依頼のX/Z等号・不等号の反例とexact状態数制約を明記）。
- [ ] K 独立レビュー記録。
- [ ] K 指摘への対応・main 統合・全 suite。
- [x] 2026-10-01 08:54 JST N 実装・等価性検証・実測・完了メモ（db1f88c、独立レビューは未完了）。
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
基準試験は指定 Python 3.11 の `-m pytest tests -q --junitxml=output/dev4-phase0.xml` で310 passed / 5 skipped、119.00秒だった。
環境上の同時実行上限はメインを含め4体であり、依頼書の5担当同時起動は3担当ずつの段階起動に置き換える。
サブエージェントの `gpt-sol` 指定は利用可能な `gpt-6-sol` を使用し、WP-K/L/M/N は high、WP-O は medium、L/N のレビューは xhigh とする。
main のモデルはセッションで設定されたものを使用し、このツールからは変更できない。

2026-10-01、準備を `b8fde01` にコミットし、`A:/dev/mcmc4qec-wt/k`〜`o` と `wp/k`〜`wp/o` を作成した。
K、N、M を先行起動し、L、O は空き枠ができたら起動する。

基準全 suite の件数差は notebook 依存不足による collection skip と確認した。
分離した `.venv-dev4-source` に検証依存を導入し、notebookを含む追加基準試験は314 passed / 4 skipped、166.23秒で成功した。
研究live照合4件は1.25秒で成功し、型検査の通常設定は23 source filesで成功、strictは533 errorsであった。
詳細は `validation_dev4_ja.md` と `output/dev4-phase0*.xml` に記録する。

2026-10-01 08:45 JST、K の受入失敗を確認後、main 管理の fastpath.py の phase flip 確率行選択を `23bd178` で修正した。
K worktree に `3609478` として反映し、関連14テストは2.81秒で成功した。
現在の担当IDは `/root/wp_k`、`/root/wp_n`、`/root/wp_m` で、いずれも作業中。
LとOの起動、K〜Oの完了・レビュー・統合、Phase 2 は未完了であり、最終報告はまだ作成しない。

## 2026-10-01 08:53 JST 継続時の確認

前ターンは基準検証・共有 fastpath 修正・記録コミットがあり、progress と判定する。
再開時の main は `5a5cf5c` で clean、3担当はツール上 running と確認した。
K は `7da19dd` に実装を中間保存し、完了メモと追加実測・区間比較を継続している。
N は初回全 suite の321 passed / 5 skippedを報告したが、main の事前確認で時空間ノイズのlog density集計順序と実step比較の検証不足を見つけ、対応中。
M の20seed baselineは349.11秒で完了し、p=0.22のexact真値約0.60266に対する被覆はBAR13/20、独立MC20/20と報告された。
Mは各仮説・感度実験と根拠表を作成中であり、この中間報告を最終受入とは扱わない。
新規 `.venv-dev4-core` と `.venv-dev4-optional` を指定Python3.11から作成し、pytest（optionalにはmypyも）を導入した。
両環境への最終wheel導入と検証は未実施。

2026-10-01 08:54 JST、N は `db1f88c` で完了メモと実装を確定し、worktree clean を確認した。
事前指摘のlog密度集計順序と実attempt/RNG比較を修正した上で、追加テスト15件が2.98秒で成功した。
Nの独立レビューとK後のmain統合は未実施。
空いた枠で `/root/wp_l` を gpt-6-sol/high として起動し、Lの独立worktreeで回路カーネルを実装する。
Oは次の空き枠で起動する。

2026-10-01 08:59 JST、K は `f9b7b93` で実装・メモを確定し、worktree clean を確認した。
Kの最終受入fileは16 passed / 8.98秒、関連7fileは116 passed / 28.09秒との実行記録を保持する。
KとNの独立レビューはまだ行っておらず、mainへも未統合である。
空いた枠で `/root/wp_o` を gpt-6-sol/medium として起動した。
現在の稼働担当は `/root/wp_l`、`/root/wp_m`、`/root/wp_o` である。
次の最初の未完了項目はK独立レビューであり、空き枠ができたら別担当をhighで起動する。
Nレビューはxhighで行い、LはN統合後、OはK/N/L/M統合後にrebaseと再検証を行う。
optional wheel用venvへの依存導入も成功したが、mcmc4qec本体のwheelはまだ導入していない。
