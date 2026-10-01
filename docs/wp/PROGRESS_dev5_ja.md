# dev5 進捗

依頼書は `docs/dev_request_2026-10-01_bar_speed.md` とする。
再開時はこのファイルの最初の未完了項目を確認し、実測と差分を根拠に進める。
日時は JST で記す。

## Phase 0

- [x] 2026-10-01 開始時の main と origin/main の一致、研究 repo の clean 状態を確認する（両 main は `9e1b28c`、研究 HEAD は `69efcfc`）。
- [x] 2026-10-01 開始時の既存変更の扱いを確定する（ユーザーが MIT・パス除去等を前提変更としてコミットすることを承認）。
- [x] 2026-10-01 20:00 前提変更を `22a8e9c` に保存し、全 source suite は362 passed / 151.22秒、tracked差分なしを確認する（新規計画文書のみ未追跡）。
- [x] 2026-10-01 研究 live 照合を再実行する（20 passed、1.97 秒、`output/dev5/phase0_crossval.xml`）。
- [x] 2026-10-01 20:00 必読資料を確認し、P/Q指示文と受入条件を準備する（`P_instructions_ja.md`、`Q_instructions_ja.md`）。
- [x] 2026-10-01 20:01 P/Q worktreeを作成し、gpt-6-sol/highの担当2体を起動する（利用可能なsolモデルを指定）。

## WP-Q（先に統合）

- [x] 2026-10-01 20:07 小仕様と受入試験をQ worktreeに追加する（全小状態・全近傍、toric同seed/RNG、正規化回数、cache境界；担当実行19 passed / 5.48秒、main統合・独立レビューは後続）。
- [x] 2026-10-01 20:20 局所確率表、decoder cache、候補処理をQ worktreeに実装し、型修正後の関連45件が成功する（正式レビュー・main全suiteは後続）。
- [x] 2026-10-01 20:20 最終runtimeで3符号各2回を再計測し、profileとREADME案、例6本の既定/quickの実測をQメモに記録する。
- [x] 2026-10-01 20:26 別担当 `/root/q_review` が敵対的レビューを実施し `Q_review_ja.md` を `ac48cd9` に保存する。
- [x] 2026-10-01 20:26 高・中の要修正指摘なし、独立136近傍の列挙と関連45件成功を確認し、残る全suiteを統合gateに残す。
- [x] 2026-10-01 20:30 Q を `8d00cf8` で main に merge し、全source suite 366 passed / 153.24秒を確認する（研究照合を含む、`q_merged.xml`）。

## WP-P

- [x] 2026-10-01 20:33 論文BAR式と研究実装の方向を独立レビューで確認し、Pメモに小仕様・live研究値との差2.43e-13を記録する。
- [x] 2026-10-01 20:33 cross_chainと受入(a)〜(e)、anchor分散、JSON往復、反復cutを実装し、独立6件4.87秒を確認する（統合後全suiteは別gate）。
- [ ] 反復 Geyer burn-in と論文の四収束規則を備えた benchmark を実装する。
- [ ] 600/2400/9600 の同じ20 seed と seed2026で bias/分散を切り分け、必要なら burn-in と4/16/50 chainを比較する。
- [ ] 4構成×2領域、低p exact/MC anchor、20 seed以上のCSVと被覆/Wilson/幅/bias/収束数を記録する。
- [ ] 論文の行番号付き整合表、利用者指針、例/notebook案、P完了メモを作成する。
- [ ] 別担当が敵対的レビューを実施し `P_review_ja.md` を作成する。
- [ ] レビュー指摘へ対応し、担当試験を完了する。
- [ ] P を Q 統合済み main に merge し、全 source suite の件数・時間を記録する。

## Phase 2

- [ ] Q/P 統合後 main で P の最終計測を再実行し、CSV・表と整合文書を確定する。
- [ ] API文書、README両言語、examples一覧、pl_curveとnotebook02の説明を反映する。
- [ ] versionを0.1.0.dev5にし、notebooks/regenerate.pyでnotebookを再生成する。
- [ ] verify_wheel.pyとCI設定の新内容への対応を確認する。
- [ ] 新規core venvにwheelをinstallし、全pytestとverify_wheel.py coreを通す。
- [ ] 新規optional venvにwheelをinstallし、全pytestとverify_wheel.py optionalを通す。
- [ ] 全suite5分以内・増分60秒以内・各file60秒以内を確認する。
- [ ] CHANGELOG、AGENTS、IMPLEMENTATION_STATUS追記を更新する。
- [ ] 最終検証済みmainをpushし、remote CI全job成功を確認する。
- [ ] git cherryで統合を確認し、P/Q worktreeとbranchを削除する。
- [ ] 研究repoの不変・clean、既存handoff本文保持、公開既定とライセンスの保持を確認する。
- [ ] 全要件を実物と実行記録で監査し、final_report_dev5_ja.mdを書き、進捗全項目を完了にしてコミットする。

## 開始記録と再開情報

開始時は74 tracked fileの変更に加え、未追跡のLICENSEとdev5依頼書があった。
依頼書の出発点に必要な変更としてユーザーに確認し、2026-10-01にコミット承認を得た。
過去handoffのパス置換も開始時点の既存変更であり、dev5中はこの承認済み前提の本文を変更しない。
全source suiteは指定Python3.11、`PYTHONDONTWRITEBYTECODE=1`、`RIMC_RESEARCH_ROOT`を設定して実行し、JUnit出力は `output/dev5/phase0_source.xml` とする。
初回は356 passed / 3 skipped / 136.41秒で、不足依存を指定Python由来の `.venv-dev5-source` に追加し、再実行は362 passed / 151.22秒、skipなしだった。
完全な基準実行のJUnitは `output/dev5/phase0_full.xml`、詳細は `validation_dev5_ja.md` に記録した。
研究live照合は同環境の `python -m pytest tests/test_crossval_research.py -q` で20件成功した。
論文は観測量平均のcross-chain SEを定義し、full BARのend-to-end評価は未実施と記載しているため、BARへの誤差伝播を論文の検証済み結論とは扱わない。

## 稼働中の担当

WP-Qは `/root/wp_q`、worktreeは `A:/dev/mcmc4qec-wt/q`、branchは `wp/q` である。
WP-Pは `/root/wp_p`、worktreeは `A:/dev/mcmc4qec-wt/p`、branchは `wp/p` である。
両worktreeの出発点は `f2799a1` である。
再開時はagentの現況とgit差分を確認し、既存agentが稼働中なら重複起動しない。
Pは実装と軽量試験を先行し、最終の20seed被覆表はQ統合後mainで測定する。
計測競合を避けるため、各担当はbenchmark実行前にメインへ連絡する。
メインの次の未完了項目はQの小仕様・受入試験の確認であり、その後に独立レビュー、Q統合、P統合の順で進める。

## 2026-10-01 20:07 の再開記録

前turnはPhase 0の検証とコミットにより進捗があり、今回は最初の未完了だったQの小仕様・受入試験を実物で確認した。
cache miss試験でCallableDecoder自身が先に不正値を拒否する問題と、非Z受理後のZで正規化が2回になる構造を指摘し、Q担当がraw decoder fixtureと表の保持更新へ修正した。
Qの受入試験は担当実行で19 passed / 5.48秒であり、変更後の全suiteと独立レビューはまだ未実施である。
要件全体の完了監査に使う対応表を `audit_dev5_ja.md` に作成した。
指定Pythonから `.venv-dev5-core` と `.venv-dev5-optional` を新規作成し、coreはpytest/mypyのみ導入、packageとoptional依存が不在であることを確認した。
optional環境はpyprojectの依存とextrasの導入を完了し、両環境とも `pip check` は成功した。
optional環境の全extras存在とpackage不在を確認し、最終dev5 wheelは両環境とも未導入である。
補助agent `/root/p_protocol_check` が読み取り専用で論文と実runnerのburn-in・四条件を照合し、P担当へ結果を渡す。
メインの次の未完了項目はQ実装の確定である。
P補助照合により各chain別burn cutと四条件の適用traceを修正する必要が判明し、修正点を `validation_dev5_ja.md` に保存した。
Qの正式速度計測CSV6行をmainでも確認し、toricの比はd5で2.55–2.59、d7で約2.47、BB72で1.55–1.60であり、toricの2倍目標は未達とする。
Qの既存例再計測と正式レビューは未完で、Pの修正版quick終了後にQの計測時間帯を確保する。
API文書にPの追加keywordと仮定の説明を先行反映し、P統合時に最終実装との一致を改めて確認する。

## 2026-10-01 20:20 の更新

Q全suiteは359 passed /5 skipped/2 failed、162.55秒で、mypy型推論の2件を修正した後、typing/faststep/adaptersの45件が6.55秒で成功した。
Qの全小状態・全近傍試験は新しい逆向き分布の実経路も強制choiceで比較するよう拡張済みである。
型修正で実行時castを加えたため最終runtimeの比較を再測定し、正式な時間比はd5で2.71–2.72、d7で2.58–2.62、BB72で1.57–1.65とした。
先行計測の数値は最終表と区別してQメモに保持する。
mainのREADME両言語に最終6行に基づくPerformance節を追加し、公開既定と異なるbenchmarkのlazy=0、同seed反復、結果・診断込みの時間であることを明記した。
Pはlive研究BARの差2.43e-13と修正版benchmark/API照合を実施済みだが、最終被覆表は未実施である。
メインの次の未完了項目はQの独立レビューである。

## 2026-10-01 20:26 の更新

Qの独立レビューは承認で、p=0/1と部分的に決定的な座標を含む136近傍の順逆分布、詳細釣合いを検査した。
独立レビューの関連45件は5.96秒で成功し、生CSV6行と英日README表の丸め一致を確認した。
Qの生CSV、profile、例の出力と独立プローブをmainの `output/dev5/q/` に複写して保持した。
例一覧の6行をQの実測値へ更新し、未測定の行と区別した。
Pは実装レビュー用 `75c1fcc` を作成し、`/root/p_review` をgpt-6-sol/xhighで起動した。
Pの正式数値表は未実施のまま、まず実装・論文手順・固定cohort集計をレビューし、数値表の追検証は後続とする。
メインの次の未完了項目はQ mergeと全source suiteである。

## 2026-10-01 20:30 の更新

Q統合後の全source suiteは366 passed / 153.24秒で、基準151.22秒からの増分は2.02秒だった。
JUnitは `output/dev5/q_merged.xml` とし、既知のWindows zmq警告1件以外に失敗やskipはなかった。
Pレビューはcross-chainの実装とAPI説明に大きな問題を認めず、truth CSVの検証不足を指摘した。
P担当は未検証のtruth-file経路を撤去し、集計時にchecked cacheの問題・source digestと真値を再検証するよう `eb2586a` で修正した。
Pの独立受入6件は4.87秒で成功し、最終数値の前にtruth cacheと直接exactの照合、および実行時間pilotを行う。
mainのAPIとREADMEにはcross-chainの仮定と限界を反映したが、正式被覆表と結論はまだ未実施である。
メインの次の未完了項目はPのBAR式・小仕様の記録確認である。
