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
- [x] 2026-10-01 09:08 JST K 独立レビュー記録（f30ef57、停止級指摘なし）。
- [x] 2026-10-01 09:13 JST K 指摘への対応・main 統合（c550cdf）・全 suite（330 passed / 5 skipped、149.98秒）。
- [x] 2026-10-01 08:54 JST N 実装・等価性検証・実測・完了メモ（db1f88c、独立レビューは未完了）。
- [x] 2026-10-01 09:20 JST N 独立レビュー記録（f1c0173、停止級指摘なし）。
- [x] 2026-10-01 09:20 JST N 指摘への対応・main 統合・全 suite（345 passed / 5 skipped、122.42秒）。
- [x] 2026-10-01 09:08 JST L 実装・詳細釣合い検証・実測・完了メモ（606fc7b、共有manifest失敗はmain統合時に対応）。
- [x] 2026-10-01 09:20 JST L 独立レビュー記録（80d9c9b、混合の実遷移テスト追加を要する）。
- [x] 2026-10-01 09:28 JST L 指摘への対応（f8a407d）・N後rebase・等価性再検証・main統合（a7fc5e6）・全suite（354 passed / 5 skipped、144.72秒）。
- [x] 2026-10-01 09:13 JST M 真値比較・20 seed 以上・各仮説と感度・被覆試験・指針・完了メモ（81a5591、8e221a4、独立レビュー待ち）。
- [x] 2026-10-01 09:28 JST M 独立レビュー記録（a1fc8e8、停止級指摘なし）。
- [x] 2026-10-01 09:30 JST M 指摘への対応・main統合（5825af4）・全suite（355 passed / 5 skipped、148.14秒）。
- [x] 2026-10-01 09:43 JST O 公開APIと公開メソッドの注釈・py.typed・型検査・完了メモ（93171ec、通常24file成功、strict252件を記録）。
- [x] 2026-10-01 09:43 JST O 独立レビュー記録（f238866、指摘修正後に承認）。
- [x] 2026-10-01 09:43 JST O 指摘への対応・統合済みmainへのrebase・型検査・main統合（b7eac06）・全suite（358 passed / 5 skipped、146.28秒）。

## Phase 2

- [x] 2026-10-01 09:43 JST 公開API・英日README・API文書・例一覧・pyproject・CIを統合し版をdev4にする。
- [x] 2026-10-01 09:48 JST Mの指針をpl_curveとnotebook02へ反映し、installed wheelで4notebookの既定出力を再生成する。
- [x] 2026-10-01 09:43 JST verify_wheel.pyを新例・型情報に対応させる（20例、24 Python file、空py.typed）。
- [x] 2026-10-01 09:43 JST 統合後全suiteと時間予算を確認する（146.28秒、追加5file37.117秒、最大file25.186秒）。
- [x] 2026-10-01 09:48 JST 新規core venvへwheel導入・全suite（258 passed / 71 skipped、56.23秒）・verify_wheel core成功。
- [x] 2026-10-01 09:50 JST 新規optional venvへwheel導入・全suite（358 passed / 5 skipped、142.24秒）・verify_wheel optional成功。
- [x] 2026-10-01 09:50 JST CHANGELOG・AGENTSを更新しIMPLEMENTATION_STATUSへ追記する。
- [x] 2026-10-01 09:55 JST 検証済みmain c1c6fb9をorigin/mainへpushし、remote CI run36798208073の全5job成功を確認する。
- [x] 2026-10-01 09:55 JST git cherryが空・祖先・clean・解決済みパスを確認し、統合済み5worktreeとwp/k〜wp/oを削除する。
- [x] 2026-10-01 09:55 JST 研究repo clean・既存handoff本文不変・公開既定と65API・各WPの完了証拠を監査する。
- [x] 2026-10-01 09:55 JST final_report_dev4_ja.mdを指定形式で作成し、全項目の完了を記録する（この記録と同じ最終コミットに保存）。

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

## 2026-10-01 09:05 JST 継続時の監査

前ターンはK/N完了確認、L/O起動、記録コミットがありprogressと判定した。
再開時main `7e1dba6` はclean、L/M/Oはツールでrunningと確認した。
Mは `81a5591` に成果を保存して完了返却したため、その枠で `/root/review_k`（gpt-6-sol/high）を起動した。
K共有文書・例manifest用のpatchを `output/dev4-k-integration.patch` に準備し、git apply --checkが成功した。
Lは `db1db3c` に保存したが、mainの監査で新例のPNG/CSVfallbackが未実装と分かり担当へ追加を依頼した。
Mのsamples_short/longはbootstrap block長も自動で6/11へ変化しており、基準8を固定した一要因比較を追加する必要がある。
Mへのidle送信はagent thread limitで拒否されたため、空き枠後にこの指摘を担当へfollowupし、benchmarkと根拠表を修正する。
K独立review、Lの図追加、O注釈は進行中で、N/M/L/Oの独立reviewは未実施。

2026-10-01 09:08 JST、K独立レビューは `f30ef57` に保存され停止級指摘なし。
LのPNG/CSVfallback対応は `606fc7b` で完了し、空いた枠で `/root/review_n`（gpt-6-sol/xhigh）を起動した。
Kレビュー担当の完了後、M担当をfollowup起動し、block8固定のsample数感度を追加する。

2026-10-01 09:13 JST、Kをmainへ統合後の全suiteは330 passed / 5 skipped、149.98秒で成功した。
N独立レビューでは18構成153件の支持・提案・軌道比較などが成功し、文書を作成中。
Lレビューでは既存の混合テストが合成提案へのMHを調べており、実装のcomponent別MH遷移を明示した受入テストを追加する必要がある。
64状態と異種alphabet32状態の両定式化の差は丸め誤差に留まり、現時点で実装の不具合を意味しない。
Mはblock8固定のsample数比較を再実測し、200保存は6/8被覆・平均幅0.08113、1200保存は7/8・0.05299となった。
旧自動block6/11の結果は参考行として残し、訂正を8e221a4へ保存した。
Oの公開利用例に対するmainのmypy試験は7件失敗し、list入力の狭すぎる注釈とNoiseProtocolのパラメータ不整合を確認した。
O担当へ修正と利用者側mypy受入試験を依頼し、最終rebase前の修正を進める。

2026-10-01 09:20 JST、Nを統合し全suite345 passed / 5 skipped、122.42秒で成功した。
L担当は統合済みmainへrebaseし、独立レビューで必要とされた実遷移テストと高速経路の再検証を進めている。
M独立レビューは `/root/review_m`（gpt-6-sol/high）で開始した。

2026-10-01 09:28 JST、Lは実成分別MH・固定乱数sampler・全提案分岐・支持境界の永続テストを追加し、対象59件46.06秒、新規file9件28.48秒で成功した。
main共有文書と例manifestを反映してLを統合し、全suite354 passed / 5 skipped、144.72秒で成功した。
M独立レビューはCSV照合と追加seedの被覆試験を含めて統合可と判断し、5825af4で統合した。
pl_curveとnotebook02の説明を改めたが、既定notebook出力の再生成は最終wheelで行う。
M後の全suiteを実行中である。
O独立レビュー `/root/review_o`（gpt-6-sol/high）は、診断の配列・sequence入力、alphabetを省略する独自binary model、独自parameter型、list出力decoderの注釈の不整合を指摘した。
O担当はこれらを修正し、K/N/L/M統合済み5825af4へrebaseして新規APIとmoduleの型検査を行う。

2026-10-01 09:30 JST、M後の全suiteは355 passed / 5 skipped、148.14秒で成功した。
最初の未完了項目はOの公開注釈と最終rebaseであり、独立レビューと担当修正を継続している。

2026-10-01 09:43 JST、Oの最終指摘であるNumPy booleanのfailure戻り値も修正し、独立レビューで承認された。
O統合とdev4版情報、型検査CI、wheelのpy.typed検証をb7eac06へ保存し、source全suite358 passed / 5 skipped、146.28秒で成功した。
新規core/optional venvへdev4 wheelを導入し、coreのverify_wheelは7.28秒で成功した。
optionalのinstalled packageに対する利用者コードのmypy検査も成功した。
両wheel環境の全suite、optional quick検証、既定notebook再生成、remote CI、後片付けと最終報告は継続中である。

2026-10-01 09:50 JST、ローカルのsourceと両wheel環境の全suite、quick例、文書コード、notebook再生成が全て成功した。
optional wheelの研究live照合は5 passed / 15 deselected、1.00秒だった。
mainの通常mypyも24file成功、strict252errors/20fileを再確認した。
push直前にorigin/mainが開始時c6cff92のままであることを確認し、mainだけをpushしてCIを確認する。

2026-10-01 09:55 JST、main c1c6fb9のActions run36798208073は全5job成功した。
remote coreはPython3.11/3.12とも258 passed / 71 skipped、optionalは356 passed / 7 skippedで、型検査専用jobは通常mypy24filesと型テスト3件を通した。
各作業枝がmainの祖先でgit cherryが空、全worktreeがcleanと確認し、安全な解決済み対象パスで5worktreeと枝を削除した。
研究repoのHEADとclean状態、handoff既存本文のprefix一致、CITATION不変、LICENSE非追加、公開既定と65名のAPI維持を監査した。
最終報告はfinal_report_dev4_ja.mdに集約し、未達目標と未実施範囲も記載した。
