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
- [x] 2026-10-01 20:47 反復Geyer burn-in・四規則・checked cache・固定cohort集計を `259cd6b` までに実装し、両anchorの公開API照合とpaper50の単独実行一致を確認する。
- [x] 2026-10-01 21:24 600/2400/9600の全60行とseed2026、対応差、exact-anchor換算と分散分解を記録する（長いchainの持続biasは未確定、追加burn/chain感度は実施せず、独立監査は後続）。
- [ ] 4構成×2領域、低p exact/MC anchor、20 seed以上のCSVと被覆/Wilson/幅/bias/収束数を記録する。
- [ ] 論文の行番号付き整合表、利用者指針、例/notebook案、P完了メモを作成する。
- [ ] 別担当が敵対的レビューを実施し `P_review_ja.md` を作成する。
- [ ] レビュー指摘へ対応し、担当試験を完了する。
- [x] 2026-10-01 20:52 Pを `82c003a` でmainにmergeし、版更新 `05c7005` 後の全source suite 372 passed /156.56秒を確認する（最終科学CSVのレビューは後続）。

## Phase 2

- [ ] Q/P 統合後 main で P の最終計測を再実行し、CSV・表と整合文書を確定する。
- [ ] API文書、README両言語、examples一覧、pl_curveとnotebook02の説明を反映する。
- [x] 2026-10-01 20:55 versionを0.1.0.dev5へ更新し、installed optional wheelの `notebooks/regenerate.py` で4本を再生成する（実行時間合計25.17秒）。
- [x] 2026-10-01 20:55 既存verify_wheelとCIの自動version/全pytest/全例経路が新APIを扱うことを確認し、local core/optionalのverify_wheelが成功する（remote CI実行は後続）。
- [x] 2026-10-01 20:56 新規core venvのinstalled wheelで全pytest 269 passed /69 skipped /64.00秒とverify_wheel coreの成功を確認する。
- [x] 2026-10-01 21:00 新規optional venvのinstalled wheelで全pytest 367 passed /5 skipped /155.69秒とverify_wheel optionalの成功を確認する。
- [x] 2026-10-01 21:00 source156.56秒・増分5.34秒、core64.00秒、optional155.69秒、file別最大26.652秒で全制限内を確認する。
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

## 2026-10-01 20:41 の更新

Pの最終被覆設定を `measurement_plan_dev5_ja.md` に保存し、既定2法は保存600・固定burn180、paper16/50は全250step・個別5 IAT、全群で補助初期値比較あり、全2026–2045とした。
paper群の長さは最悪の予備実行24.03秒/seedから選び、正式な20seed被覆結果はまだ得ていない。
9600保存の長さ比較は予備46.50秒/seedのため、同じ20seedを前半10・後半10に固定分割する。
長さ比較の合計見積930秒と各invocation約465秒を区別し、全20seed合計が600秒以内とは扱わない。
Pは低pのMC/exact anchorを同じ保存軌道から出力する拡張を検証中で、benchmarkレビューの確定後にmainへ統合する。
Qの生CSVは `docs/wp/data_dev5/q_step.csv` にもコミットし、第三者がREADME表を再計算できるようにした。
メインの次の未完了項目はPのbenchmark実装の確定である。

## 2026-10-01 20:47 の更新

Pのbenchmark実装は `259cd6b` で凍結し、独立レビューの追補文書を待ってmainへ統合する。
低pのMC/exact anchorは同一軌道とBAR比・MCMC分散を再利用し、独立したCSVに出力する。
paper50・全250・補助比較ありの両anchor実行は19.84秒で、単独MCと全列一致、単独exactとCSV bytes一致だった。
独立レビューによるdefault_blockの両anchor/API quick照合は3.55秒で成功した。
真値cacheと直接exactの差はp=0.22で1.01e-14、p=0.03で6.27e-14で、失敗196608/全262144状態を確認した。
最初の未完了は20seedの長さ比較であり、その前提としてP統合・version更新・全suite・最終source digestのcache生成を先行する。

## 2026-10-01 20:57 の再開情報

runtimeの最終コミットは `05c7005`、source SHA-256は `50f47ab86aadb8ddc25142c696ce6cfbce631a8cf8357cbbca8ca33d397f56d5` であり、以後は文書とnotebook出力だけを更新した。
最終truth cacheは `output/dev5/p_final/truth_cache.json` に再列挙し、pilotと全重みcountsが一致した。
測定前のmanifestとコマンド・実時間ログは `output/dev5/p_final/measurement_plan.json` と `run_log.jsonl` にある。
保存600の正式20seedは82.72秒の外側計測で完了し、BAR被覆13/20、独立MC20/20、平均偏差-0.0119139、seed間SD0.0256099だった。
この段階では長さ依存やbiasの結論を出さず、最初の未完了として2400と9600の全seed比較を残す。
WP-P担当は `/root/wp_p` が継続し、計算はmainをcwd、PYTHONPATHをmain/srcにして行い、文書追補はwp/pで行う。
mainはcore wheel gateを通過し、optional wheelの全pytestをsession27208で実行中である。
optionalの全pytestと追加のpl_curve時間確認が終わったら、Pへ長さ2400/9600および12cohortの計算枠を戻す。
notebook4本の既定出力は `baaa26a` に保存し、verify_wheel optionalの全20例・全4quick notebookと文書コードは成功済みである。
Pの実装レビューは完了しているが、最終科学CSVの敵対的監査は同じ `/root/p_review` へfollowupして行う必要がある。

## 2026-10-01 21:00 の更新

optional wheelの全pytestは367 passed /5 skipped /155.69秒で、研究envを指定しないlive研究照合5件がskipされた。
optionalのfile別最大はcircuit kernelsの26.121秒で、source/core/optionalの全gateが時間制限内だった。
既定説明を更新したpl_curveもseed7で再計測し、既定10.993秒・quick2.460秒、両方exit0で、例一覧へ反映した。
Pへ科学計算枠を戻し、保存2400・9600の固定20seedと12cohortをmainで継続する。
mainの現在の残件は最終数値表と独立監査、文書の結論・handoff追記・最終AGENTS更新、push/CI、worktree cleanup、全要件監査と最終報告である。

## 2026-10-01 21:06 の再開情報

保存2400の正式20seedは262.07秒で完了し、BAR平均0.6014329672、平均偏差-0.0012295975、seed間SD0.0122816999、平均偏差のSE0.0027462716、BAR/MC被覆とも20/20だった。
P担当は固定済みの9600保存を2026–2035、2036–2045の2回に分け、現在は前半を計測している。
最初の未完了項目はこの長さ比較の完成と解釈で、9600の両sliceが終わるまで追加設定を結果から選び直さない。
defaultの初期化はnoise.sampleをfailureで棄却するので、独立bit-flipと決定的MWPMでは条件付きtargetから開始することをコードと独立レビューで確認した。
従ってdefault群の差を初期burn不足と断定せず、非線形BARの有限標本bias、有限相関、少数chainの散らばりを区別する。
paper群は固定論理状態からの開始なので、初期過渡の可能性は別に残る。
この考察のレビュー追補はwp/pの `ed726d7` にあり、mainへは数値文書と一緒に後からmergeする。
MC anchor1500試行は全長さで固定されるため、SDが1/sqrt(N)で下がり続けるとは限らない。
主表はMC anchorを維持し、同じ全20seedの `bar_estimate/anchor_estimate` とcacheのp=0.30 exact値から作るexact-anchor換算点推定およびlog比SDを、再samplingなしの補助派生量として評価する。
以後のsource変更は予定せず、科学表が揃ったら `/root/p_review` をfollowupして全seed・設定・Wilson・paired差・結論を監査する。
Pの実験はmainで行うが、担当の文書とレビューの編集・commitは `A:/dev/mcmc4qec-wt/p` に限定する。

## 2026-10-01 21:11 の更新

前turnではQ/P統合、sourceと両wheel・例・notebookの検証を完了しており、単なる状態再掲ではなく実装と検証の進捗があった。
本turnは最初の未完了項目の長さ比較から再開し、9600前半の同じ実行が稼働中であることを確認した。
担当のsession12374はroot側から参照できないため再起動せず、CIMで21:05:02開始の該当benchmarkのPID2448/18612を確認した。
21:10:54にもPID18612は存在し、担当側の同sessionのpollも継続中だった。
最終truth cacheを `docs/wp/data_dev5/truth_cache.json` に複写し、実行用cacheとのSHA-256一致 `e23c43c9022bb5dbbe5820009165f81ff30b73ff32018c62cc5b08d028c92f63` を確認した。
監査表に残っていたPの全suite待ち表記を実行済みのsource/両wheel結果へ更新し、未完の長さ・被覆表とは区別した。

## 2026-10-01 21:17 の更新

保存9600の前半2026–2035はexit0、benchmark内483.03秒・外側483.39秒で完了し、事前固定した後半2036–2045へ進んだ。
中間10seedの被覆数から結論を作らず、全20seedの集計を待つ。
21:15の読み取り監査では研究HEADとclean状態が維持され、承認済み前提22a8e9c以降のsampling、kernels、LICENSE、CITATION、handoff本文に差分はなかった。
AGENTSのlocal wheel検証を実施済みの状態へ更新し、科学計測とremote CIの未完と区別した。
同じ独立P reviewerへ、最終数値前の統計的解釈の確認を依頼した。
最初の未完了項目は長さ比較60行の完成とbias/分散の解釈であり、12cohortの正式計測はその後に続ける。

## 2026-10-01 21:24 の更新

保存9600の後半は外側469.81秒で完了し、長さ比較の3群各20seed・合計60行の固定seed、設定、真値cacheを集計で確認した。
MC anchor主表の保存600/2400/9600の平均偏差は-0.0119139/-0.0012296/-0.0032513、seed間SDは0.0256099/0.0122817/0.0069659、BAR被覆は13/20・20/20・20/20だった。
seed2026の点推定は0.534471/0.590558/0.593408、真値は0.602662565であり、単一seedの偏差だけでbiasの有無を判断しない。
exact anchorへ換算した補助点推定の平均偏差は-0.0104788/+0.0002744/-0.0017374で、9600の残差は約1.1 SEだった。
長さを伸ばすと散らばりが縮むが、20seedだけでは非線形BARの有限標本biasと偶然の偏差を確定的に分離できず、追加burn/chain感度は現時点では実施しない。
MC anchorとBAR比の9600における標本相関は-0.5912で、この有限cohortの負の共分散が観測SDを理論anchor SD床約0.010より小さくすることを分散恒等式で確認した。
全CSV、派生統計と再計算スクリプト、事前manifestを `docs/wp/data_dev5/` へ保存し、同じ独立reviewerへ数値と追加感度を省く判断の監査を依頼した。
最初の未完了項目は4構成×2領域・低p両anchorの12cohortであり、担当が固定順の8invocationを開始する。

## 2026-10-01 21:29 の更新

前turnは長さ比較全60行と派生分析を `f30de91` へ保存した実進捗であり、今回は最初の未完了の12cohortから再開した。
dev4 default_blockは91.75秒で13/20、default_crossは82.59秒で18/20、paper16は98.29秒で17/20となり、全て20seedのinvocationが完了した。
ここでの秒数は外側実測で、benchmark内の出力秒数とは区別する。
defaultの2法は全20seedの点推定・BAR比・cut・各診断列が一致し、平均区間幅はblockの0.06257からcrossの0.09698へ増えた。
残るpaper50と低p両anchorが未完であり、この中間値だけで設定を選び直したり、優劣を確定したりしない。
長さ比較の独立監査はP branchの `2edaa85` に保存され、追加感度未発動の判断を支持しつつbias原因の除外ではないことを記録した。
mainの検証記録と監査表へ監査結果を反映し、P worktreeの予備出力39ファイルも `output/dev5/p_pilots/` に保持した。
担当はdev4 paper50を継続し、その後に事前固定した低pの4構成・両anchorを測定する。

## 2026-10-01 21:36 の更新

前turnは長さ比較の独立監査と3cohortの確認を `0988c5c` へコミットし、今回は同じdev4 paper50のプロセスが稼働中であることをCIMで確認して継続した。
dev4 paper50はbenchmark内271.11秒で完了し、被覆19/20、平均偏差+0.006660、平均幅0.06555だった。
paper16とpaper50はそれぞれ全20seedで少なくとも1chainが半trace capに達し、正式四条件の合格0、未判定11/18、補助四条件合格11/18だった。
これでdev4の4cohort・80行が揃い、`docs/wp/data_dev5/protocol/raw/` に保存した。
低pのdefault_block両anchorは外側125.03秒で完了し、MC anchorの被覆18/20・平均幅0.004355、exact anchorは14/20・平均幅0.001848だった。
この2cohort・40行も保存し、全20組のBAR比・cut・各診断列がanchor間で一致することを確認した。
MC anchorの追加分散が区間幅に寄与するため、MCでの被覆数だけでBAR側の不確かさ評価が十分とは判断しない。
最初の未完了は残り6cohortであり、低p default_cross両anchorを21:35:14開始の同一プロセスで計測中である。
最終の12cohort集計と独立科学レビュー、P文書の統合、remote CI以降のgateは引き続き未完了である。

## 2026-10-01 21:39 の更新

前turnは6cohort・120行を `254514a` に保存した実進捗であり、今回は同じ低p default_crossの稼働を確認して再開した。
低p default_crossの両anchorはbenchmark内111.20秒で完了し、MC anchorは18/20・平均幅0.004714、exact anchorは15/20・平均幅0.002422だった。
この2cohortもtracked dataへ保存し、全8cohort・160行まで完了した。
同じ低pのblock法はMC18/20・exact14/20であり、4chainの誤差法切替だけで十分な被覆改善が得られたとは結論しない。
`docs/api_en.md` に2chainは計算下限で精度推奨ではなく、少数chainでの分散推定とlog尺度1.96 SEの正規近似の限界を追記した。
最終科学計測のPython・主要依存版・CPU/OS・source/研究commitを `docs/wp/data_dev5/measurement_environment.json` に記録した。
最初の未完了は低p paper16/50の両anchor計4cohortで、担当がpaper16を継続している。

## 2026-10-01 21:42 の更新

前turnは8cohortの保存とAPIの小標本近似説明を `b35e109` にコミットした実進捗であり、今回は低p paper16の同じプロセスから再開した。
低p paper16の両anchorは外側139.22秒で完了し、MC20/20・平均幅0.004648・平均偏差-0.0003000、exact19/20・平均幅0.002493・平均偏差-0.0001233だった。
両anchor共通でcap有20/20、正式四条件未判定12/20、補助四条件合格12/20だった。
この40行を保存し、tracked dataは10cohort・200行となった。
残る低p paper50の両anchorは21:40:01開始のPID12188/21988で稼働していることを確認し、重複起動せず継続する。
独立P reviewerへ既存200行の監査を先行依頼し、最後の40行が到着したら全12組・240行の完全性と最終文書を追確認する。
P authorは派生統計とPメモ・論文整合表・利用者指針、reviewerはP_reviewだけをそれぞれP worktreeで編集する。
最初の未完了は引き続き12cohortの完成であり、最終科学レビューと文書統合より先にCIや完了報告へ進まない。
