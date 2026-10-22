# 明示割当て条件の保存BAR行による独立算術レビュー

C1T0以降の明示assignmentを持つ条件について、最終report回収後に全768群・67,584行・352設定・各192 seedの集計を独立に照合する。
既存の標準library算術 `assess`・`Comparison`・設定列挙はsourceのbyteを変えずに再利用し、追加は保存行の読取経路と実行要求の照合に限定する。
既存C0T2 readerと実行中のsource・manifest・成果物は変更しない。

実行要求は外部hashで固定したreport・transfer planと、明示したremote入力rootを持つ。
context・assignment・各archiveをtransfer plan、context、最終reportのaudited evidenceへ結び付ける。
assignmentのcase・target indexと全batchの割当てが、重複・欠落なく768群を覆うことを検査する。
ZIP memberの重複を拒否し、読み出すanalysis JSONのbyte数・hashをarchive manifestと照合する。
元sampling planは固定reference archiveから読み出し、reportの元remote pathのbyte hashとproduction digestへ結ぶ。
各groupに予定88設定が一度ずつ存在し、符号・noise・p・kernel・初期化・replicateが元planと一致することを確認する。
区間未取得・診断未定義・診断flag・数値失敗を分母から除外しない。
完全な保存行を再構成できない場合は拒否し、部分集合を完了結果として保存しない。

読取前後に外部pinとarchive hashを再照合し、未使用出力先へ排他的に保存する。
整数・bool・件数は厳密、浮動小数点は既存算術の相対許容差1e-10・絶対許容差0で照合する。
全設定CSV、事前固定した長い16設定CSV、保存行、入力hash、実行環境、実行時間、再現sourceと照合結果を保存する。
この作業は保存推定値の算術確認であり、sampling・復号・BAR・bootstrap・raw trace・WSS labelの再計算ではない。
有限referenceとの整合を真値精度・混合・母RMSE・名目95%被覆の保証とは扱わない。
小さい配置fixtureの受入を先に作成し、reader実装後に実データの回収を待って照合する。
