# ユーザー指定による中断と再開メモ

2026-09-30 12:05 JST、ユーザーの「一旦 中断。あとでさいかいできるようにしといて」に従って作業を停止した。
ユーザーが再開を指示するまで実装、テスト、統合、push を再開しない。
今回の checkpoint は未完了成果の保存であり、WP の受入完了や goal 達成を意味しない。

## 再開の起点

`AGENTS.md`、`docs/dev_request_2026-09-30.md`、このメモ、各 worktree の `docs/wp/` と git log/status を確認する。
元の達成条件と停止条件は変更していない。
ユーザーは著者を `junichi haruna` と明示確定しており、この点の再確認は不要である。
ライセンス、公開化、publish、既定値の変更は引き続き行わない。
goal の取得時点で累積実行時間は 1337 秒で、8 時間停止条件には達していない。

## 保存されたブランチ

| 場所 | branch / 中断時 HEAD | 状態と次の作業 |
| --- | --- | --- |
| `C:/dev/mcmc4qec` | main / `9ef1636`（この中断メモの commit 前） | 共通基盤、独立論理基底指定、provenance、docstrings、codes extra を実装済みで、WP 本体は未統合。 |
| `C:/dev/mcmc4qec-wt/a` | wp/a / `98e74e0` | 実装と数値照合記録を checkpoint 保存し、独立レビューは未開始。 |
| `C:/dev/mcmc4qec-wt/b` | wp/b / `c7e992b` | 実装と第1回レビュー対応済みで、main 統合待ち。 |
| `C:/dev/mcmc4qec-wt/c` | wp/c / `a64d89b` | 回路実装、テスト、例、メモを checkpoint 保存し、独立レビューは未開始。 |
| `C:/dev/mcmc4qec-wt/d` | wp/d / `d95e7ea` | 文書・CI・citation と第1回レビュー対応済みで、統合後の API/docstring 再監査が必要。 |
| `C:/dev/mcmc4qec-wt/e` | wp/e / `2cdef82` | 第1回レビュー指摘の修正途中を checkpoint 保存し、修正後の検証と第2回レビューが必要。 |

すべての worktree を残しており、削除、reset、stash はしていない。
A/C/E の checkpoint commit は修正完了や試験成功を保証しない。
A の `docs/wp/A_ja.md` は中断時に存在しないため、再開時に復元・作成する。
A の数値と研究テスト対応表は `docs/crossval_research_ja.md` に保存されているが、記載と現在のテスト実体の照合は未了である。

## main に入っている変更

`81aece0` は toric/surface の Phase 0 基盤で、当初 14 件の追加テストが成功した。
`e8a488b` は `CSSCode(..., logical_basis="independent")` で、既定 paired 検証を維持し、研究 BB/Hamming の可逆だが非単位な交差行列を明示的に許す。
`f5323c1` は decoder の予測座標も同時変換すべきというレビュー指摘への対応、再帰的 package source hash、公開 docstring 補完である。
main `f5323c1` の全テストは実行して 164 passed、40.40 秒だった。
`916612b` は `[codes]` optional extra（ldpc と bposd）および既存 private repo の URL/keywords/classifiers 追加である。
`9ef1636` は D が提出した追加 docstring patch の適用で、compileall は成功したが、その後の main 全 suite は未実施である。
version はまだ `0.1.0.dev1` で、CHANGELOG の WP 更新も未実施である。

## レビューと統合時の注意

統合順は依頼書どおり A → B → E → D → C とし、各 merge 後に全 suite を実行する。
A/D/E には main の論理基底変更の cherry-pick があり、D には codes extra の cherry-pick もあるため、同一内容を重複して適用しない。
D の `docs/wp/D_docstrings.patch` は既に main `9ef1636` へ適用済みであり、再適用しない。
B の `sampling.py` は fastpath/cache 接続、C の同ファイルはメイン担当が追加した `KernelConfig.circuit_single` 接続を含むため、両変更を保って merge する。
C は明示的な circuit_single=1 と他の重みゼロを要求し、既定の Z/H では回路を実行しない。
公開名追加は未実施で、各 WP のメモに従って `__init__.py` と `docs/api_en.md` に反映し、`__all__` 突合テストを追加する。

B の第1回レビューは `docs/wp/B_review_ja.md` にあり、不正 decoder 出力 `[0.5]` が uint8 cast で黙認される不具合を修正した。
B の最終独立検証報告は 169 passed、29.13 秒で、3 ノイズの提案確率差は最大 1.11e-16、詳細釣合い差は 0 だった。
研究速度 2 倍以内は未達だが、依頼書が認める代替条件の profile 原因と次の手は記録済みである。
D の第1回レビューは `docs/wp/D_review_ja.md` にあり、README の依存不足と toric d=5 に exact を使う例を修正した。
D の CFF validate と installed wheel 検証は成功報告があるが、全 WP 統合後の検証の代わりにはならない。
E の第1回レビューは `docs/wp/E_review_ja.md` にあり、ゼロ分母で非零差を未判定にする問題、direct MC 分散なしの四条件合格、負相関 IAT、二盆地試験と独立基底試験の不足を指摘した。
E には差があれば fail、direct MC 分散未提供時は条件(iv)を None、負相関の扱いと実際の二盆地 Markov 例を修正するよう指示済みで、checkpoint の変更はまだ最終確認していない。
A と C の正式な受入レビューは未実施である。
C の補助調査では中点 MPP と rec 参照補正、全 2d ラウンドからの中点 observable 予測を検証したが、これは C 全体の正式レビューとは別である。
いずれの WP も第2回レビュー失敗という停止条件にはまだ達していない。

## 検証環境と残る達成条件

指定 Python は `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` である。
main に `.venv-dev2-core` と `.venv-dev2-optional` を新設し、前者に NumPy/pytest、後者にそれらと PyMatching/ldpc/bposd/Stim を導入済みである。
この 2 環境には最終 wheel はまだ install しておらず、Phase 2 の検証は未実施である。
統合後に dev2 へ version を上げ、wheel を build/install し、`-I -m pytest --override-ini pythonpath= tests -q` と依存に適した examples を両環境で実行する。
README/tutorial のコードブロック、CFF、公開 API/docstrings、wheel と source の一致も統合後に再確認する。
CHANGELOG と IMPLEMENTATION_STATUS の完成追記、main の push、GitHub Actions の実結果確認、依頼書 §6 の `docs/wp/final_report_ja.md` は未完了である。
remote は `junichiharuna/mcmc4qec`、private、default branch main と読み取りで確認済みである。
push はまだ一度も行っていない。

## 停止確認

実行中だった WP-A/B/C/D/E とレビュー担当に interrupt を送り、補助担当を含め新規作業を停止した。
中断後のプロセス確認では、この作業に対応する Python/pytest/cffconvert プロセスは見つからなかった。
`C:/dev/RIMC` の git status は clean であり、研究リポジトリを変更していない。
再開時は実際のプロセスと git 状態を再確認し、古いメモだけから試験を再起動しない。

## 2026-09-30 14:02 JST 再開

ユーザーの「再開して」により中断指定は解除された。
main と五つの worktree の HEAD、完了メモ、レビュー記録、研究リポジトリの clean 状態を確認して再開した。
A/C の完成確認、E の第1回レビュー修正を担当へ戻し、C の正式な第1回レビューと D の追加 API 文書整備を開始した。
中断前の checkpoint を完成扱いにはせず、各受入条件を確認してから指定順に統合する。

## 再開後の現在地

上の中断時一覧は過去時点の記録である。
再開後に全WPをmainへ統合し、dev2最終wheelのcore/optional試験と全実行例を確認した。
以後の状態とCI結果は `final_report_ja.md` と `validation_dev2_ja.md` を参照する。
