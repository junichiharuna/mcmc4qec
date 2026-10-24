# 低ノイズの途中結果をexperimental版でどう扱うか

[英語の利用案内](../tile_validation_interim_en.md)にも、以下の検証範囲・再現条件・適用限界をまとめた。

2026-10-23時点の完了済み11条件について、[9条件の比較](low_long_nine_comparison_result_2026-10-22_ja.md)、[tile288 depolarizing p=0.01の個別報告](low_c3t0_result_2026-10-23_ja.md)、[p=0.003の個別報告](low_c3t1_result_2026-10-23_ja.md)から利用上の判断を整理する。
残るtile288 depolarizingのp=0.001、全12条件の設定選択、独立計時、最終報告は未完了である。
本稿は既存結果の読み方であり、全12条件の正式比較や新しい推奨設定の選定ではない。

## 最初に再現する対象

完了分では、tile72 bit-flipのp=0.01が、保存済みの低ノイズ検証手順を再現する最初の対象候補になる。
事前固定した長い16設定では、各192 seedの点推定・区間を取得し、診断flagと診断未定義は0件、経験的な相対RMSE 10%・20%のgateは全設定で通過した。
これは16 chain・burn-in 6,000・保存60,000・fine ladderの結果であり、公開既定の1 chainや短い利用例へ外挿しない。
reference区間との交差は誤差法・kernel・初期化で異なり、名目95%被覆や全支持の連結性を保証した結果ではない。
全条件での速度比較もまだないため、BARが直接MCより速いという推奨には使わない。

## 低いpやtile288へ広げるとき

残る完了10条件では、比較した長い16設定の全192 seedに診断flagがあった。
未収束や診断未定義を理由にseedを除外せず、点推定・区間と診断を一緒に確認する。
block長やcross_chainへの変更で区間の重なりが増えても、同じ点推定とtraceの混合が改善したとは扱わない。
tile288の広い重み層別reference区間と192/192で重なる場合も、真値の95%被覆や精度達成の証拠にはならない。
tile288 depolarizing p=0.01・0.003の長い16設定は全て経験的な相対RMSE 10%・20%のgate未達であり、校正済み設定として推奨しない。
partialな重み層別推定値やreference区間の中点を真値へ置き換えない。

## 再現時に固定するもの

目標pに合わせたBP-OSDをladder全体で固定し、decoderのnative binary・thread設定・保存済みfixtureを含む生成環境を揃える。
別OSで同じ版番号のdecoderを使うだけでは失敗集合の一致を保証できず、確認済みの環境間差は[中間報告](tile_validation_report_2026-10-18_ja.md)第3節にある。
BP-LSD・BeliefFind・Union-Findの実装受入は、このBP-OSDによるBAR校正の結果をそれらのdecoderへ移す根拠にならない。
公開既定は維持し、追加decoderの科学的校正は未完了として記録する。

## 今回の確認範囲

[9条件の144行CSV](data_tile_validation_2026-10-17/low_long_nine_comparison_v1/long_settings.csv)と[C3T0の16行CSV](data_tile_validation_2026-10-17/c3t0_reconnected_final_downstream_handoff_v2/c3t0/review/fixed_long_slice.csv)を、既存manifestのhash・sizeと照合した。
各行の分母192、点推定192、区間未取得0、上記の診断flagとprecision gateを実データで確認した。
CSVのSHA256はそれぞれ `cb513674e658d9d4b21850f9f5890ad7542e9765bcdae7a7222ac168d137fc07` と `89174153ce382db9f8a7373f9b70bfe0ee0c3aaab76d75dd950da600b5a61af2` である。
新しいsampling・復号・BAR・bootstrap・reference計算やraw traceの再監査は行っていない。

21:27の追記ではC3T1の全352設定と長い16設定のCSV・reviewを既存manifestと照合し、各192分母、区間未取得0、診断flag・未定義各192、precision gate未達を確認した。
再現scriptと入力hashは[C3T1利用判断の観測](data_tile_validation_2026-10-17/c3t1_usage_observation_20261023_v1/observation.json)に保存した。
