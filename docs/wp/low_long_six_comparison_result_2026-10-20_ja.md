# tile72低ノイズ6条件：長い設定の誤差法比較

完了したtile72のbit-flip/depolarizing各3条件について、事前固定の長い16設定ずつ、計96設定を比較した。
[従来の5条件比較](low_long_uncertainty_comparison_result_2026-10-20_ja.md)の80設定を変更せず、bit-flip p=.001の16設定を追加した。
旧5条件は保存BAR行の独立算術レビューに基づくが、新しいp=.001は[受理済み最終report](low_c0t2_recovered_result_2026-10-20_ja.md)からの集計値抽出である。
今回の追補でp=.001の保存BAR行の独立算術レビューを実施したわけではない。
23:55 JSTの追加確認では、[C0T2の全保存BAR行の独立算術レビュー](low_c0t2_arithmetic_review_result_2026-10-20_ja.md)を完了し、reportの11,968値と本比較の長い16設定の432値が最大差0で一致した。
この比較を作成した時点の抽出source・図表・provenanceは保持し、独立確認の証跡を別成果物として追加した。

## 固定範囲と検証

| 対象 | chain数 | burn-in | 保存数 | ladder |
|---|---:|---:|---:|---|
| bit-flip、p=.01/.003/.001 | 16 | 6,000 | 60,000 | fine |
| depolarizing、p=.01/.003/.001 | 8 | 6,000 | 12,000 | fine |

各条件でZH/ZHS、logical_basis/logical_combination、block長32/128/1024とcross_chainの全16組を含む。
各設定の分母は192であり、診断flag・未定義・区間未取得を理由にseedを除外していない。
noise間では計算予算が異なるため、図は同一費用での性能比較ではない。
[小仕様](low_long_six_comparison_spec_2026-10-20_ja.md)、未実装時の失敗受入、実装後9 passed・0.56秒、実データ処理の順に進めた。
元の比較処理はbyte単位で同一のsourceを使い、旧5条件のCSV全80設定が変更されていないことを検査した。
保存した再現sourceからの再実行でも、96設定CSVと24方法群CSVがbyte単位で一致した。
実行環境はWindows・Python 3.11.9であり、この追補のLinux実行は未実施である。

## Reference区間との重なり

![tile72低ノイズ6条件。各点は全192 seedでのBAR区間と有限reference区間の重なり件数を示し、各panelに計算予算と診断状態を記載する。](data_tile_validation_2026-10-17/low_long_six_plot_v1/uncertainty_comparison.png)

[PDF](data_tile_validation_2026-10-17/low_long_six_plot_v1/uncertainty_comparison.pdf)と[SVG](data_tile_validation_2026-10-17/low_long_six_plot_v1/uncertainty_comparison.svg)も保存した。
描画した全96点をCSVと照合し、PNGで文字・凡例・6 panelの表示を確認した。
線は同じtraceを使う誤差法間の対応を示し、独立実験や信頼区間を示さない。

| noise | p | block 32 | block 128 | block 1024 | cross_chain |
|---|---:|---:|---:|---:|---:|
| bit-flip | .01 | 172–176 | 177–184 | 180–186 | 183–185 |
| bit-flip | .003 | 158–161 | 172–176 | 179–182 | 181–182 |
| bit-flip | .001 | 143–154 | 159–167 | 174–180 | 175–180 |
| depolarizing | .01 | 145–161 | 165–180 | 171–184 | 171–182 |
| depolarizing | .003 | 126–137 | 151–163 | 172–181 | 170–179 |
| depolarizing | .001 | 108–123 | 144–152 | 173–174 | 174–181 |

各セルは4組のkernel・初期化の最小値〜最大値で、分母は設定ごとに192である。
referenceはWSSの99.9%区間と省略質量の上界を含む有限標本の参照であり、厳密な真値ではない。
したがって、表の重なり件数を真値の95%被覆件数と同一視しない。
追加したbit-flip p=.001では、reference区間全体をBAR区間が含む件数も表と同じだった。
他の5条件の全体包含件数は[既存比較](low_long_uncertainty_comparison_result_2026-10-20_ja.md)および今回のCSVに保持した。

## 点推定と混合診断

| noise | p | 診断flag /192 | 診断未定義 /192 | 区間未取得 /192 |
|---|---:|---:|---:|---:|
| bit-flip | .01 | 0 | 0 | 0 |
| bit-flip | .003 | 192 | 0 | 0 |
| bit-flip | .001 | 192 | 0 | 0 |
| depolarizing | .01 | 192 | 0 | 0 |
| depolarizing | .003 | 192 | 139–152 | 0 |
| depolarizing | .001 | 192 | 192 | 0 |

全96設定で区間は得られたが、bit-flip p=.01以外は全seedに診断flagが残る。
24組のcondition・kernel・初期化について、4誤差法のrelative bias範囲・relative RMSE範囲・点推定取得数・診断flag・未定義・high R-hat・low ESSの一致を確認した。
誤差法によってreferenceとの重なりが増えても、点推定や混合が改善したことにはならない。
追加条件のrelative biasとRMSEは[条件別結果](low_c0t2_recovered_result_2026-10-20_ja.md)と[96設定CSV](data_tile_validation_2026-10-17/low_long_six_comparison_v1/long_settings.csv)を参照できる。
今回の結果から誤差法を事後選択し、校正済みの推奨設定とは扱わない。
公開既定を変更せず、tile288の残る6条件と低ノイズでの独立計時を継続する。

## 保存物と再現

- [比較記録](data_tile_validation_2026-10-17/low_long_six_comparison_v1/comparison.json)に入力hash・環境・集計由来・限界を保存した。
- [方法別24行CSV](data_tile_validation_2026-10-17/low_long_six_comparison_v1/method_ranges.csv)に条件別予算、指標の範囲、null設定数を保存した。
- [manifest](data_tile_validation_2026-10-17/low_long_six_comparison_v1/manifest.json)は集計・source・試験ログと5条件の再現結果を束ね、SHA-256は `02010ad2a1335b50c5eeb39f05761453f75c94f06a347f2f69e4ca8885e643c4` である。
- [照合記録](data_tile_validation_2026-10-17/low_long_six_plot_v1/verification.json)に旧値の保持、CSV再現一致、全描画点と目視確認を保存した。

元のreviewと回収reportを保持したrepositoryから、未使用の出力directoryへ再現する。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B docs/wp/data_tile_validation_2026-10-17/low_long_six_comparison_v1/reproduction/six_comparison.py --repository A:/dev/mcmc4qec --output output/low_long_six_comparison_replay_new
```

再現処理は保存集計の抽出と比較であり、sampling・decoder・BAR・bootstrap・WSSの再実行ではない。
sourceの配置先が異なる場合は記録中の絶対pathが変わるが、数値CSVは一致する。
