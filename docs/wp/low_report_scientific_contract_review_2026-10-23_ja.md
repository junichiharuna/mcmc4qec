# 低ノイズ最終報告の集計規則の追加レビュー

2026-10-23に、クラスタへ配備した報告環境の5 module・8関数について、固定環境のSHA256と実ファイル、読み直したローカル関数のASTが一致することを確認した。
対象は `assess_cohort`、`assess_rows`、`cost_ratios`、`report_text`、`assess_bounds`、`assess_condition`、`cost_summary`、`summarize_condition` である。
証拠と実際の配備source、再確認scriptは [レビュー記録](data_tile_validation_2026-10-17/low_report_scientific_contract_review_20261023_v1/observation.json) と [分母の追加照合](data_tile_validation_2026-10-17/low_report_scientific_contract_review_20261023_v1/denominator.json) に保存した。
今回は読み取り専用の実装レビューであり、追加の数値計算や本番報告の再検証ではない。

確認した規則は以下の通りである。

- 全12条件×2精度目標の24組合せについて、MCとBARの両方の状態を保持する。
- 完了cohortは事前の全192 seedを要求し、欠落・重複を拒否する。
- 区間未取得を被覆の分母192から除かず、未収束flagで標本を除外しない。
- 点推定が欠ける場合は全cohortのbias・RMSEと精度合格を与えず、失敗とその費用を残す。
- 独立referenceがない場合はreference被覆・bias・RMSEをnullとし、精度分類を `reference_unavailable` にする。
- WSSのpartial sumを真値にせず、reference区間全体に対するbias・RMSEの範囲を使い、点referenceを報告しない。
- 計算時間の欠測があるclockは全cohortの平均と費用比を与えず、利用可能分だけの平均を別項目に残す。
- 時間比はMCとBARの両方が経験的な点推定RMSE条件を満たした場合だけ計算する。

時間比の精度条件と、区間被覆・混合診断は別である。
点推定が全件得られている場合、区間未取得があっても点推定RMSEに対する時間比が得られることがあるため、その値を区間精度の比較と読まない。
独立BAR計時では混合診断を収集しておらず、内部のflagged・undefinedは全192件の未観測placeholderであり、実測の診断不合格件数ではない。
報告本文とJSONはこの区別を明示しており、主校正の実測混合診断と併読する必要がある。
有限referenceの不確実性、条件間の同時保証がないこと、hostやpartition差を補正しないことも記載されている。
この範囲では分母を成功標本に縮める処理やreferenceなしで精度を認定する処理は見つからず、稼働中のsourceは変更していない。
実データを使う全12条件の報告生成、回収物の照合、最終結論のレビューは未完了である。
