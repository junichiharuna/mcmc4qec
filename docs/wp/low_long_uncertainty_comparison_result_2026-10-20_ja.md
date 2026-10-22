# 完了済み低ノイズ5条件：長い設定の誤差法比較

2026-10-20に、保存済み独立算術レビュー5条件から、各16設定・計80設定を欠落なく抽出した。
以下は同じ条件内での誤差法への感度であり、全12条件の校正完了やnoise間の同一計算予算の比較ではない。
[小仕様と修正理由](low_long_uncertainty_comparison_spec_2026-10-20_ja.md)に、対象範囲と未取得値の扱いを記録した。
入力を前後でhash照合し、各条件352設定・67,584行・192 seedのレビューと、既存の長い16設定のJSON/CSV一致を確認した。

## 保存設定と比較範囲

| 対象 | chain数 | burn-in | 保存数 | ladder |
|---|---:|---:|---:|---|
| tile72 bit-flip、p=.01/.003 | 16 | 6,000 | 60,000 | fine |
| tile72 depolarizing、p=.01/.003/.001 | 8 | 6,000 | 12,000 | fine |

初回は全条件を16 chain・保存60,000とする仮定が入力検査で拒否され、出力作成前に停止した。
保存済みC2の設定を確認して明示的な条件別予算へ修正し、縮小受入を追加した。
修正後の受入は7 passed・0.62秒で、5条件の実データ処理も完了した。
各方法の範囲はZH/ZHSとlogical_basis/logical_combinationの4組の最小値・最大値であり、4組を独立seed群としてプールしていない。

## Reference区間との重なり

各セルの分母は設定ごとに192である。
科学比較用referenceは層別samplingの99.9%区間と省略質量上界を含む有限標本の参照であり、厳密な真値ではない。
表はBAR区間とreference区間が重なる件数であり、真値の95%被覆を直接観測した件数とは区別する。

![tile72低ノイズ5条件の誤差法比較。各点は192 seedの区間とreferenceの重なり件数で、診断状態と計算予算を条件別に表示する。](data_tile_validation_2026-10-17/low_long_uncertainty_plot_v2/uncertainty_comparison.png)

[PDF](data_tile_validation_2026-10-17/low_long_uncertainty_plot_v2/uncertainty_comparison.pdf)と[SVG](data_tile_validation_2026-10-17/low_long_uncertainty_plot_v2/uncertainty_comparison.svg)も保存した。
描画した全80点を元CSVと照合し、PNGの表示を目視確認した記録は[描画検証](data_tile_validation_2026-10-17/low_long_uncertainty_plot_v2/verification.json)にある。
誤差法間では同じtraceを用い、線は方法間の対応を示すもので、追加の独立実験や信頼区間を表さない。

| noise | p | block 32 | block 128 | block 1024 | cross_chain |
|---|---:|---:|---:|---:|---:|
| bit-flip | .01 | 172–176 | 177–184 | 180–186 | 183–185 |
| bit-flip | .003 | 158–161 | 172–176 | 179–182 | 181–182 |
| depolarizing | .01 | 145–161 | 165–180 | 171–184 | 171–182 |
| depolarizing | .003 | 126–137 | 151–163 | 172–181 | 170–179 |
| depolarizing | .001 | 108–123 | 144–152 | 173–174 | 174–181 |

Reference区間全体をBAR区間が含む、より厳しい件数は次のとおりである。

| noise | p | block 32 | block 128 | block 1024 | cross_chain |
|---|---:|---:|---:|---:|---:|
| bit-flip | .01 | 168–174 | 177–182 | 178–185 | 181–185 |
| bit-flip | .003 | 158–161 | 172–176 | 179–182 | 181–182 |
| depolarizing | .01 | 134–153 | 155–173 | 168–180 | 166–177 |
| depolarizing | .003 | 123–134 | 151–163 | 172–180 | 169–179 |
| depolarizing | .001 | 108–123 | 144–152 | 173–174 | 174–181 |

## 区間取得と混合診断を分ける

| noise | p | 診断flag /192 | 診断未定義 /192 | 区間未取得 /192 |
|---|---:|---:|---:|---:|
| bit-flip | .01 | 0 | 0 | 0 |
| bit-flip | .003 | 192 | 0 | 0 |
| depolarizing | .01 | 192 | 0 | 0 |
| depolarizing | .003 | 192 | 139–152 | 0 |
| depolarizing | .001 | 192 | 192 | 0 |

全80設定で区間は取得されているが、それは混合診断が定義可能または良好であることを意味しない。
各condition・kernel・初期化の20組について、4種類の誤差法のrelative bias範囲・relative RMSE範囲・診断flag・診断未定義・区間未取得が同一であることを照合した。
したがって、区間が広がってreferenceとの重なりが増えたことを、点推定の改善や混合の改善とは解釈しない。
bit-flip p=.01でも診断flagが0のままblock長32の重なり件数は172–176/192であり、診断だけを区間校正の根拠にできない。
depolarizing p=.001では、取得できた区間の平均幅はblock長32で約9.75e-7〜9.99e-7、cross_chainで約2.10e-6〜2.26e-6だった。
平均幅は区間を取得できたseedだけを対象とする指標であり、未取得がある場合に被覆の分母を縮めるためには用いない。

## 設定選択への含意と残作業

これらの条件では小さいblockの区間をそのまま研究精度の根拠にすることは支持されず、block長とcross_chainへの感度を報告する必要がある。
一方で、観測した重なり件数が多い方法を同じcohortから事後選択し、校正済みの推奨設定とすることもできない。
独立seedでの評価、混合の改善、残るtile288など7条件、同精度到達時間の比較を継続する。
今回の記述的比較に基づく公開既定の変更は行わない。

## 保存物と再現

- [全80設定CSV](data_tile_validation_2026-10-17/low_long_uncertainty_comparison_v1/long_settings.csv)は各設定の値を保持する。
- [方法別20行CSV](data_tile_validation_2026-10-17/low_long_uncertainty_comparison_v1/method_ranges.csv)は条件別予算、各指標の範囲、null設定数を保持する。
- [比較記録](data_tile_validation_2026-10-17/low_long_uncertainty_comparison_v1/comparison.json)は入力15ファイルとsourceのhashを保持する。
- [保存manifest](data_tile_validation_2026-10-17/low_long_uncertainty_comparison_v1/manifest.json)は9ファイルを束ね、SHA-256は `354554fc70c71bc68d3d4cc6ed8d40d684d94f480c9e244dcbf5debd70960838` である。

元の5レビューとCSVを保持したrepositoryを指定し、未使用の出力directoryへ次のように再現する。
算術処理はPython標準libraryのみを使用し、source・受入・失敗と成功のログは上記directory内の `reproduction/` に保存している。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B docs/wp/data_tile_validation_2026-10-17/low_long_uncertainty_comparison_v1/reproduction/comparison.py --repository A:/dev/mcmc4qec --output output/low_long_uncertainty_comparison_replay
```

出力には実際の実行sourceの絶対pathを記録するため、sourceの配置先を変えた再現ではprovenanceのpath表現が変わる。
実データでの集計を行った環境はWindows・Python 3.11.9であり、この追加集計のLinux実行は未実施である。
保存したsourceから別出力先へ再実行し、2つのCSVのhash一致、保存9ファイル、本文15表行と元集計の一致を[再現照合記録](data_tile_validation_2026-10-17/low_long_uncertainty_comparison_replay_receipt_20261020_v1.json)に保存した。
図の再現にはMatplotlibを用い、実行版3.11.0とsource・入力・出力hashを[描画記録](data_tile_validation_2026-10-17/low_long_uncertainty_plot_v2/render.json)に保存した。
図の描画は数値集計とは別処理であり、新しい推定や誤差計算を行わない。

```powershell
& $taskPython -B docs/wp/data_tile_validation_2026-10-17/low_long_uncertainty_plot_v2/plot_low_long_uncertainty_v1.py --input docs/wp/data_tile_validation_2026-10-17/low_long_uncertainty_comparison_v1 --output output/low_long_uncertainty_plot_replay
```
