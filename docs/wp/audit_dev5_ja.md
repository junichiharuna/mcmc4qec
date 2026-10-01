# dev5 要件と証拠の対応

依頼書 `../dev_request_2026-10-01_bar_speed.md` に対し、完了時に確認する証拠を先に定める。
この表の「未確認」は未達を意味し、担当の完了宣言や過去の成功だけでは置き換えない。
実行ログとCSVは原本を保持し、報告表を確定するときに行数、seed、設定、集計値を照合する。
現時点の基準検証は `validation_dev5_ja.md` に記録済みである。

| 要件 | 完了を示す証拠 | 状態 |
| --- | --- | --- |
| Phase 0のmain/origin一致、clean、全suite | 開始時のgit出力、承認済み前提コミット、JUnit | 確認済み：`22a8e9c`、`phase0_full.xml`、362 passed / 151.22秒 |
| BAR式と研究値の照合 | 論文269–281行、研究関数、現行テストの実行結果と比較対象の説明 | 基準テスト20 passed、式の確認済み、Pの記録確定待ち |
| Qの小仕様と試験先行 | Qメモの仕様、受入試験追加と実行記録、実装差分 | Q worktreeの仕様/試験を確認、担当19 passed / 5.48秒、最終レビュー待ち |
| Qの局所確率表・cache・候補処理 | 実装差分、正規化回数・検証境界・適用条件 | 未確認 |
| Qの全小状態・全近傍等価性 | 提案確率、順逆比、MH受理確率、support境界の列挙試験 | 未確認 |
| Qのtoric d3/categorical同seed等価性 | 状態列・受理列・lazy列・kernel列・乱数消費の比較試験 | 未確認 |
| Qの計測3符号×2回以上 | 同設定のCSV/ログ、seed、CPU/OS/Python/依存版、step/sと比 | 未確認 |
| Qの未達原因 | 時間比が2を超えた符号のprofileと残る原因 | 未確認 |
| Qの利用者向け説明 | Qメモの英日README案、計測時点の明示、研究なしCLIの実行 | 未確認 |
| Qの独立レビューと指摘対応 | 別agentのQ_review、指摘ごとの修正差分と再検証 | 未確認 |
| Q merge後の全suite | mainのmerge commitとJUnit件数・時間 | 未確認 |
| Pのcross_chain API | keyword追加、2 chain未満/不正値の拒否、method記録、独立anchor分散 | 未確認 |
| Pの標準誤差の理論値 | 合成独立chainに対する既知の分散と共有rung共分散の受入試験 | 未確認 |
| Pの点推定と既定互換性 | 同seedで誤差法間の点推定一致、既定結果とRNG系列の互換試験 | 未確認 |
| Pの小問題反復被覆 | 列挙可能な問題、事前固定した約10 seed、緩い閾値のテスト | 未確認 |
| Pの反復Geyer burn-in | 反復停止則、半trace fallback、研究コードと論文との差の明示 | 未確認 |
| Pの四収束規則 | scaling/late drift/multistart/dispersionの実判定と未判定処理 | 未確認 |
| Pの保存数600/2400/9600 | 同じ2026–2045の各seed値、exactとの差、平均bias/散らばり/幅 | 未確認 |
| Pのbias/分散の識別 | 同一軌道の2誤差法、N依存、必要なburn-in/4・16・50 chain感度 | 未確認 |
| Pの4構成×2領域 | 全構成20 seed以上、各CSVと被覆/Wilson/平均幅/平均偏差/収束合格数 | 未確認 |
| Pの低p exact/MC anchor | 同じ軌道に対する両anchor、独立seedとanchor分散の記録 | 未確認 |
| Pの論文整合表 | chain数、burn-in、誤差棒、kernel、初期化、収束、ladder、p領域、BAR、anchorを論文行番号付きで対応 | 未確認 |
| Pの利用者向け指針 | 測定範囲と限界、短いchainの警告、既定変更は所有者判断として提案 | 未確認 |
| Pの独立レビューと対応 | 別agentのP_review、seed選択なし、論文手順一致、統計主張の反証確認 | 未確認 |
| P merge後の全suite | Q→Pの順のmain履歴とJUnit | 未確認 |
| Q統合後mainでP最終計測 | コミットと設定を記録した最終CSV、Q前の数値を明確に区別 | 未確認 |
| benchmarkの共通CLI | --quick/--seed/--out、temp既定、envで指定した研究root保護 | 未確認 |
| 共有文書と例の反映 | API、README両言語、examples一覧、pl_curve、notebook02の実差分 | 未確認 |
| version・notebook再生成 | pyproject 0.1.0.dev5、import/metadata一致、regenerate.pyの実行結果 | 未確認 |
| wheel core | 新規隔離venv、installed import、全pytest、verify_wheel.py core | 未確認 |
| wheel optional | 新規隔離venv、installed import、全pytest、verify_wheel.py optional | 未確認 |
| 実行時間制約 | suite<300秒・基準151.22秒からの増分<60秒・各file<60秒、各benchmark<600秒 | 基準file最大25.344秒、変更後は未確認 |
| CHANGELOG/AGENTS/handoff追記 | 0.1.0.dev5の実装/実測を反映、handoff既存本文のprefix一致 | 未確認 |
| main pushと全remote CI | origin/mainの対象SHA、Actionsの全5job成功、jobログ | 未確認 |
| worktree/branch cleanup | git cherryの未統合差分なし、削除対象の安全確認、削除後inventory | 未確認 |
| 研究repo不変 | 開始時HEAD `69efcfc` と一致、git status空、意図しない生成物なし | Phase 0終了時確認済み、終了時は未確認 |
| 公開既定・ライセンス・引用制約 | KernelConfig/SamplingConfig/API既定の差分、LICENSE不変、未承認引用項目の非変更 | 未確認 |
| 最終報告・進捗・コミット | 指定6節、実測表、未実施/所有者判断、全チェックの根拠、clean main | 未確認 |

最終報告を書く前に、未確認の行を実証済みの証拠へ更新する。
達成を保証できない科学的目標は実測結果と限界として記録し、要求された実験や検証そのものの欠落と区別する。
