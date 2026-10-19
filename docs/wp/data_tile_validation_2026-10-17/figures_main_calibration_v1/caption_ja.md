# 図：主校正の固定条件比較

ZH/rejection・最大予定chain・burn-in 6000・最長保存trace・fine ladderに固定した記述的比較で、結果を見て選んだ最良設定ではない。
tile72 bit-flipは16 chain・60,000保存点、残る3caseは8 chain・12,000保存点を用い、いずれも全192 replicateを分母に残す。
左は有限な独立直接MCの点推定を基準にした経験的相対RMSEであり、誤差法3種類のBAR点推定が共通なためcaseごとに1本を描く。
右は同じMC点推定を含むBARの95%区間数で、点の横に分子/192を表示する。
95%の破線は名目目標であり、真値に対する95%被覆の保証ではない。
図の被覆はreferenceの99.9%区間全体を含む数や、その区間と交差する数とは異なる。
例えばtile72 bit-flipのcross_chainはMC点包含186/192、reference区間全域包含148/192、交差190/192である。
これら3種類の数、reference区間内で変わる相対RMSE範囲、被覆の記述的Wilson区間はCSV/JSONに区別して保存し、図の点や棒の誤差線としては表示しない。
有限referenceと192 replicateの標本変動が残り、誤差法間は同じtraceを共有するので独立な3実験ではない。
表示条件のBAR診断flagはcase順に0/192、192/192、191/192、192/192であり、被覆改善を混合問題の解消と扱わず、flagが0でも収束や既約性の証明とはしない。
全表示行で点推定192/192、区間未取得0だが、それを科学的精度の保証としない。
authoritative概要JSONと元の受理済みaudited/precision summaryを条件identityとhashで照合し、表示単位への変換だけを行った。
新しい科学計算、bootstrap、ACF、raw trace読込、decoder実行は行っていない。

再生成はこのdirectoryの `regenerate.py --output <新しいdirectory>` を実行し、元dataの場所が異なる場合は `--data <data_tile_validation_2026-10-17>` を指定する。
既存成果物の上書きは拒否する。
元入力・概要生成source・描画sourceのSHA256、実行環境、図の全数値は `figure_data.json` と `figure_data.csv` に保存した。
