# 回復済みBARの保存rowによる独立算術レビュー

完了済みC0T0/C0T1の保存済み推定値・区間から、各192 seed・352設定のbias、RMSE、被覆件数、診断・欠測件数を独立した標準libraryの算術で再計算する。
既存 `review_low_final_arithmetic.py` の算術をそのまま使い、入力配置の照合だけを隔離版へ拡張する。
既存のpartitioned/staged経路は同じsampling root内の `partition-collection/rows.jsonl` を扱う。
新しいrecovered経路は明示指定し、元sampling planの絶対pathと、別の回復root内の `collection/rows.jsonl` をそれぞれ元reportのevidenceへ結ぶ。
reader名をpathから推測せず、異なる保存場所を同一rootへ読み替えない。

今回のrecovered経路は、元reportが `recovery_used=true`、全cohortのtrace監査済み、normal partitionなし、回復partitionが0の1個だけ、768群・192 anchor・67,584 rowを満たす場合に限る。
元解析jobと回復jobを別identityとして保持し、回復partitionの正常終端確認を要求する。
planとrowsのhashおよび解決先は、全体evidenceと回復partitionのevidenceの両方に一致させる。
相対path、親directory移動、hashの欠落・不一致、別のrow集合、複数partition、未完了cohortを拒否する。
転送は既存のscp処理を再利用し、固定report・helper・取得bytesを前後で検査して排他保存する。

数値算術、全192 seedの分母、未取得区間、未定義診断の扱い、固定long設定の記述的な抜粋は変更しない。
新たなsampling、decoder実行、BAR/bootstrap推定、raw traceやWSSラベルの再監査は行わない。
この一致を精度、混合、名目95%被覆の保証とは扱わない。
小さい配置fixtureによる失敗する受入、隔離版の実装、既存算術・転送回帰、実2条件の取得と算術レビューの順に進める。
