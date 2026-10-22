# C0T2の保存BAR行による独立算術レビュー

tile72 bit-flip p=.001の受理済み最終reportに対応する38 archive・768 groupの保存BAR行を読み、352設定×192 seedの集計を独立に再計算する。
既存の標準libraryによる独立算術 `assess`・`Comparison` をbyte単位で同じsourceから使用し、公開sampling・BAR・bootstrapを再実行しない。
変更は保存行の読取経路に限定し、既存の回復済み条件用readerを変更しない。

固定report、転送plan、contextを外部hashで照合する。
各archiveのSHA-256をreport中のaudited evidence・転送plan・contextの3つへ結び、読取前後で再照合する。
ZIP全memberの重複を拒否し、読み出すanalysis JSONのbyte数・hashをarchive内manifestと照合する。
元sampling manifestは保存exportから抽出し、元remote pathのreport evidenceにあるbyte hashとproduction digestを照合する。
38 batchのgroup割当てが全768群を重複・欠落なく覆い、各groupの88設定が予定と一致することを確認する。
行の符号・noise・p・kernel・初期化・replicateを確認し、設定ごとのseedが0〜191を一度ずつ含むことを独立算術側でも検査する。
診断flag・未定義・区間未取得・数値推定失敗を分母から除外しない。
archiveまたはgroupが欠落し、保存行を完全に再構成できない場合はレビューを拒否し、部分集合を完了結果として保存しない。

整数・bool・件数は厳密に、浮動小数点は既存レビューと同じ相対許容差1e-10・絶対許容差0でreportと比較する。
有限referenceの99.9%区間と省略質量上界をそのまま使い、真値・母RMSE・名目被覆の保証へ置き換えない。
全設定CSV、長い16設定CSV、入力hash、行数、照合数、最大差、環境、再現sourceを保存する。
この作業は保存推定値の算術確認であり、raw trace、復号label、ACF、WSS label、独立reference自体の再検証ではない。
新しいsampling、qsub、GPU計算は行わない。

## 完了記録

初回読取のkernel mappingの扱いを受入追加後に修正し、追加経路の受入10件が成功した。
修正後の実行は38 archive・768 group・67,584行を完了し、352設定の11,968値でreportとの差は0だった。
詳細、失敗記録、適用限界と再現手順は[結果文書](low_c0t2_arithmetic_review_result_2026-10-20_ja.md)に保存した。
