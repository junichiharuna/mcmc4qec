# Goalの完了条件と確認済み範囲

2026年10月23日時点ではgoalは未完了である。
experimental版の利用開始に必要な公開候補の準備と、継続中の数値検証を分けて判定する。
計算が正常終了することと、精度・混合・名目95%被覆が成立することも区別する。

| 要件 | 現在の判定 | 根拠と残作業 |
|---|---|---|
| tile72/288の符号構築・code-capacity・論理失敗定義 | 実装・受入記録あり | [tile中間報告](tile_validation_report_2026-10-18_ja.md)第2節と構造監査に4組合せを保存。距離や全失敗支持の連結性の独立証明とは扱わない。 |
| BP-LSD・BeliefFind・Union-Find | 実装・受入記録あり | [decoder検証](basic_decoders_validation_2026-10-18_ja.md)と[利用例](basic_decoders_usage_2026-10-18_ja.md)。今回46入力の保存済み受入との一致を再確認。新decoderのBAR被覆・速度順位は未校正。 |
| 公開候補のテスト・配布物・利用例・日英文書 | 準備済み | [最新候補](publication_candidate_status_2026-10-23_ja.md)にsource ZIP・wheel・訂正したRelease本文とhashを保存。現在のpackage 33ファイルはwheelと一致。最新mainのCIもsuccess。 |
| GitHubで実際に公開 | 未実施 | PRIVATE・Release0件。候補の準備完了を公開済みとは記載しない。PyPI公開は後続事項。 |
| decoder再現性・prior感度 | 有限な検査と限界の報告済み | [環境間差](tile_decoder_platform_2026-10-17_ja.md)と[prior感度](tile_decoder_prior_effect_2026-10-18_ja.md)。固定prior・native環境でfailure集合を保ち、全入力での決定性を証明したとは扱わない。 |
| 主4条件の混合・BAR校正・直接MC・重み層別reference | 計測と報告済み | [中間報告](tile_validation_report_2026-10-18_ja.md)に各192seed・全352設定と混合比較、有限referenceの不確実性を保存。未定義診断・未取得を分母から除外しない。 |
| 主4条件の独立計時 | 計測と報告済み | [計時の独立レビュー](data_tile_validation_2026-10-17/main_timing_scientific_review_v1/report_ja.md)。全192分母保持の記録を今回読み直した。速度優位の一般保証ではない。 |
| 低ノイズ12条件 | 10/12条件まで入力が揃った | 残るtile288 depolarizingのp=0.003・0.001を計算・解析中。全12条件が揃う前に部分集合で正式比較を終えない。 |
| 低ノイズの全条件比較・独立計時 | 未実施 | 条件別の最終結果を待つ。資源判定に従う通常経路と分割経路、seed集計、計時の待受を接続済み。 |
| 日本語の最終報告・推奨設定の根拠と限界 | 未完了 | [最終報告までの接続](low_partition_report_result_2026-10-23_ja.md)は完了したが、本番結果の回収・内容照合・結論のレビューが残る。 |
| 生データ・環境・再現手順の保存 | 完了分を保存、継続中 | 計測ごとの固定manifest・hash・seed・実行証拠を保存。最終データ束は未完成。全raw datasetの公開用変換と公開先も別途残る。 |
| qsub・最大2node・複数計算機の活用 | 継続運用中 | クラスタはqsub・共有lock・待機を含む要求node数の上限2。labo・DGXの割当済み解析と後続待受を継続し、観測timeoutだけでは再投入しない。 |

## 今回実際に再確認したこと

wheel内のpackage 33ファイルと現在のsource、基本decoderの受入対象46ファイルをbyte単位で照合した。
tile72/288・bit/depolarizingの構造監査4記録が存在し、paired logical basisと未証明事項の記載を確認した。
直接MC referenceの保存summaryは監査記録のSHA256と一致し、監査記録の試行数は81,788,928、chunk数は1,248である。
主4条件のtrace監査記録は各768群・192replicateで、合計件数の整合を確認した。
これらは現在のsourceと保存証拠の照合であり、生traceの再監査・native decoderの再試験・新たな科学的検証ではない。
結果と再現scriptは [照合記録](data_tile_validation_2026-10-17/goal_evidence_20261023_v2/observation.json) に保存した。
そのSHA256は `9da117f9b1429036089a5c648370e2a5f3e31fd6f8e7d96baa9110c6846c5c2c` である。

goal完了の判断には、残る2条件の正式回収、全12条件の比較、独立計時または事前規則に基づく実行不能・対象なしの記録、最終報告と再現情報の照合が必要である。
検証の結果として精度gate未達や非推奨となる設定が残っても、それを隠さず結論へ反映する。
設定間の整合だけから、独立referenceのない領域の精度や被覆を保証しない。
