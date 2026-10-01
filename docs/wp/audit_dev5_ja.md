# dev5 要件と証拠の対応

依頼書 `../dev_request_2026-10-01_bar_speed.md` に対し、完了時に確認する証拠を先に定める。
この表の「未確認」は未達を意味し、担当の完了宣言や過去の成功だけでは置き換えない。
実行ログとCSVは原本を保持し、報告表を確定するときに行数、seed、設定、集計値を照合する。
現時点の基準検証は `validation_dev5_ja.md` に記録済みである。

| 要件 | 完了を示す証拠 | 状態 |
| --- | --- | --- |
| Phase 0のmain/origin一致、clean、全suite | 開始時のgit出力、承認済み前提コミット、JUnit | 確認済み：`22a8e9c`、`phase0_full.xml`、362 passed / 151.22秒 |
| BAR式と研究値の照合 | 論文269–281行、研究関数、現行テストの実行結果と比較対象の説明 | Pメモにlive研究との差2.43e-13、Pレビューで式・方向一致、凍結値テスト20 passedを区別して記録 |
| Qの小仕様と試験先行 | Qメモの仕様、受入試験追加と実行記録、実装差分 | Qメモと当時の進捗ログを確認、git上は同一commitで時系列の独立証明にはならない |
| Qの局所確率表・cache・候補処理 | 実装差分、正規化回数・検証境界・適用条件 | Q_review承認、正規化最大1回、miss検証/hitコピー/毎回shape比較、実型gate保持 |
| Qの全小状態・全近傍等価性 | 提案確率、順逆比、MH受理確率、support境界の列挙試験 | ForcedChoice試験と独立136近傍列挙が成功、逆分布全再計算との差0 |
| Qのtoric d3/categorical同seed等価性 | 状態列・受理列・lazy列・kernel列・乱数消費の比較試験 | 関連45件5.96秒、toric prefix1–24とcategorical列挙、Q_reviewに検査範囲を記録 |
| Qの計測3符号×2回以上 | 同設定のCSV/ログ、seed、CPU/OS/Python/依存版、step/sと比 | `output/dev5/q/bench-step-dev5-final/results.csv` 6行を独立監査、READMEの丸め一致 |
| Qの未達原因 | 時間比が2を超えた符号のprofileと残る原因 | d5 2.71–2.72、d7 2.58–2.62で未達、attempt/propose/cache/adapterのprofileをQメモとperformanceに記録 |
| Qの利用者向け説明 | Qメモの英日README案、計測時点の明示、研究なしCLIの実行 | 両READMEへ反映、研究なしCLI成功、例6本の既定/quick計測を一覧に反映 |
| Qの独立レビューと指摘対応 | 別agentのQ_review、指摘ごとの修正差分と再検証 | `/root/q_review` が `ac48cd9` で承認、高・中の要修正指摘なし |
| Q merge後の全suite | mainのmerge commitとJUnit件数・時間 | `8d00cf8`、`q_merged.xml`、366 passed / 153.24秒（基準+2.02秒） |
| Pのcross_chain API | keyword追加、2 chain未満/不正値の拒否、method記録、独立anchor分散 | Pレビューと受入6件4.87秒、JSON往復を含む、統合後source372件と両wheel全suite成功 |
| Pの標準誤差の理論値 | 合成独立chainに対する既知の分散と共有rung共分散の受入試験 | 合成0.5/sqrt(3)と負の共分散を独立テストで確認 |
| Pの点推定と既定互換性 | 同seedで誤差法間の点推定一致、既定結果とRNG系列の互換試験 | 同seed点推定一致、Pレビューで既定経路/seed生成順の保持、統合後source/両wheel全suite成功 |
| Pの小問題反復被覆 | 列挙可能な問題、事前固定した約10 seed、緩い閾値のテスト | seed0–9、2bit exact問題、10件中5件以上の回帰が成功 |
| Pの反復Geyer burn-in | 反復停止則、半trace fallback、研究コードと論文との差の明示 | P_reviewが研究1D個別cutと照合、合成cut6と半traceの受入成功、最終数値は後続 |
| Pの四収束規則 | scaling/late drift/multistart/dispersionの実判定と未判定処理 | P_reviewで適用traceを監査、正式M未判定と補助四条件を区別、数値はladder全rungのAND |
| Pの保存数600/2400/9600 | 同じ2026–2045の各seed値、exactとの差、平均bias/散らばり/幅 | data_dev5/lengthに全60行と対応差、exact換算、分散分解を保存、独立reviewerが全列と派生量を1e-12以内で再現 |
| Pのbias/分散の識別 | 同一軌道の2誤差法、N依存、必要なburn-in/4・16・50 chain感度 | N依存で散らばり縮小、9600のexact換算偏差1.1SEで持続bias未確定、追加感度未発動の判断を独立reviewerが支持、同軌道2法比較は後続 |
| Pの4構成×2領域 | 全構成20 seed以上、各CSVと被覆/Wilson/平均幅/平均偏差/収束合格数 | 全12cohort・240行と修正版集計/派生をdata_dev5に保存、独立reviewerが全行・全派生フィールドを再計算一致 |
| Pの低p exact/MC anchor | 同じ軌道に対する両anchor、独立seedとanchor分散の記録 | 全4構成の両anchorで比・cut・診断列が一致し、点推定/区間/分散・対応被覆差を独立監査 |
| Pの論文整合表 | chain数、burn-in、誤差棒、kernel、初期化、収束、ladder、p領域、BAR、anchorを論文行番号付きで対応 | paper_consistencyに全項目あり、P_reviewで式・cut・四規則・kernel等を照合、最終数値の反映は後続 |
| Pの利用者向け指針 | 測定範囲と限界、短いchainの警告、既定変更は所有者判断として提案 | P文書5d14d5dに全表と指針、有限cohort/不等長cut/少数chainの限界、既定維持と所有者判断を記録、最終reviewは後続 |
| Pの独立レビューと対応 | 別agentのP_review、seed選択なし、論文手順一致、統計主張の反証確認 | 未確認 |
| P merge後の全suite | Q→Pの順のmain履歴とJUnit | P merge `82c003a`、版更新後 `05c7005`、`p_merged.xml` 372 passed /156.56秒 |
| Q統合後mainでP最終計測 | コミットと設定を記録した最終CSV、Q前の数値を明確に区別 | 未確認 |
| benchmarkの共通CLI | --quick/--seed/--out、temp既定、envで指定した研究root保護 | Q_reviewで研究なしCLI/出力拒否、Pのquick/seed実行成功、mainのBAR2本×env2種は全てmkdir前拒否 |
| 共有文書と例の反映 | API、README両言語、examples一覧、pl_curve、notebook02の実差分 | 方法の仮定と性能を反映、pl_curve/notebook02説明更新、例・notebook実行成功、科学表の結論は後続 |
| version・notebook再生成 | pyproject 0.1.0.dev5、import/metadata一致、regenerate.pyの実行結果 | dev5 wheelで4本既定regen成功、25.17秒実行合計、verify_wheelのversion/source一致成功 |
| wheel core | 新規隔離venv、installed import、全pytest、verify_wheel.py core | 269 passed /69 skipped /64.00秒、verify_wheel core成功、24source fileとREADME一致 |
| wheel optional | 新規隔離venv、installed import、全pytest、verify_wheel.py optional | 367 passed /5 skipped /155.69秒、verify_wheel optional成功、全20例/4quick notebook/文書コード成功 |
| 実行時間制約 | suite<300秒・基準151.22秒からの増分<60秒・各file<60秒、各benchmark<600秒 | source156.56秒・増分5.34秒・core64.00秒・optional155.69秒・全file最大26.652秒、被覆8invocation最大410.15秒、長さ9600は事前固定2分割483.39/469.81秒（合計953.19秒） |
| CHANGELOG/AGENTS/handoff追記 | 0.1.0.dev5の実装/実測を反映、handoff既存本文のprefix一致 | 未確認 |
| main pushと全remote CI | origin/mainの対象SHA、Actionsの全5job成功、jobログ | 未確認 |
| worktree/branch cleanup | git cherryの未統合差分なし、削除対象の安全確認、削除後inventory | 未確認 |
| 研究repo不変 | 開始時HEAD `69efcfc` と一致、git status空、意図しない生成物なし | 21:15再確認でHEAD一致・status空、終了時再確認は後続 |
| 公開既定・ライセンス・引用制約 | KernelConfig/SamplingConfig/API既定の差分、LICENSE不変、未承認引用項目の非変更 | 21:15時点でsampling/kernels/LICENSE/CITATIONは22a8e9c以降差分なし、BARはkeyword追加のみで既定維持、終了時再確認は後続 |
| 最終報告・進捗・コミット | 指定6節、実測表、未実施/所有者判断、全チェックの根拠、clean main | 未確認 |

最終報告を書く前に、未確認の行を実証済みの証拠へ更新する。
達成を保証できない科学的目標は実測結果と限界として記録し、要求された実験や検証そのものの欠落と区別する。
