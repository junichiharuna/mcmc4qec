# 低ノイズ完了8条件の長い設定をまとめる小仕様

完了済みtile72の6条件とtile288 bit-flipの2条件について、保存BAR行からの独立算術reviewを入力として、事前固定した長い16設定ずつの比較表を作る。
元review・CSV・sourceのhashを固定し、case・target・p・352設定・67,584行・各192 replicateを確認する。
各条件の長い16設定はZH/ZHS、logical_basis/logical_combination、block32/128/1024とcross_chainの直積を過不足なく含む。
予算はtile72 bit-flipで16chain・60,000保存、それ以外で8chain・12,000保存とし、全てburn-in6,000・fine ladderを維持する。
条件間で同一費用を仮定しない。

各設定の元数値を保持した128行CSVと、4組のkernel・初期化を方法別にまとめた32行CSVを出力する。
同じcondition・kernel・初期化では、4誤差法間で点推定のbias/RMSE範囲と混合診断件数が同一であることを検査する。
欠落、重複、分母変更、別条件、入力hash不一致、誤差法間の点推定変更を拒否する。
未収束・診断未定義・区間未取得・指標nullは保持し、seedや設定を除外して集計しない。
元の6条件比較CSVとも同じ設定・指標を全数照合し、由来を示す欄の追記を数値変更と混同しない。

reference区間の全体包含と重なりを別列に示し、真値の95%被覆と呼ばない。
広いreference区間の影響を分かるようにし、点referenceへの置換や推奨設定の選択を追加しない。
この集約は保存reviewの比較であり、sampling、decoder、BAR、bootstrap、raw trace、WSSの再実行ではない。
元8条件の独立算術確認を今回新たに実施したとは記載しない。
残る4低ノイズ条件、全12条件の設定選択、独立計時、最終報告は未完了のまま明示する。

小さな受入で上記の拒否と診断未定義の保持を確認してから実装し、固定実データで処理する。
保存した再現sourceから別directoryに再実行し、数値CSVのbyte一致を確認する。
