# 低ノイズ完了8条件：長い設定の結果と利用上の限界

低ノイズ12条件のうち、完了済み8条件の事前固定した長い16設定ずつ、計128設定をまとめた。
tile72の6条件とtile288 bit-flipの2条件を含み、各設定の分母は独立seed192件である。
これは保存済みの独立算術reviewの比較であり、新たなsampling・decoder・BAR・bootstrap・WSSの計算ではない。
実行中の残り4条件と低ノイズ独立計時を含む最終報告は未完了である。

## 比較範囲

各条件でZH/ZHS、logical_basis/logical_combination、block32/128/1024とcross_chainの全16組を維持した。
burn-inは6,000、ladderはfineで、tile72 bit-flipは16chain・60,000保存、その他は8chain・12,000保存である。
条件間の計算予算が異なるため、同じ費用に対する符号やnoiseの性能比較とは扱わない。
各reviewのcase・target・p・352設定・67,584行・192件分母、元JSONとCSV、input hashを照合した。
既存の[6条件比較](low_long_six_comparison_result_2026-10-20_ja.md)の96設定と全数値が一致し、その結果は変更していない。

## Reference区間との重なり

下表はBAR区間と有限reference区間が交差した件数である。
各セルは4組のkernel・初期化における最小値〜最大値を示し、分母は設定ごとに192である。
4組を独立なseed集合として合算していない。

| 符号・noise | p | block32 | block128 | block1024 | cross_chain |
| --- | ---: | ---: | ---: | ---: | ---: |
| tile72 bit-flip | .01 | 172–176 | 177–184 | 180–186 | 183–185 |
| tile72 bit-flip | .003 | 158–161 | 172–176 | 179–182 | 181–182 |
| tile72 bit-flip | .001 | 143–154 | 159–167 | 174–180 | 175–180 |
| tile288 bit-flip | .01 | 192 | 192 | 192 | 192 |
| tile288 bit-flip | .003 | 192 | 192 | 192 | 192 |
| tile72 depolarizing | .01 | 145–161 | 165–180 | 171–184 | 171–182 |
| tile72 depolarizing | .003 | 126–137 | 151–163 | 172–181 | 170–179 |
| tile72 depolarizing | .001 | 108–123 | 144–152 | 173–174 | 174–181 |

referenceは重み層別MCの各層のClopper–Pearson区間をBonferroniで合成し、省略質量上界を含めた99.9%区間であり、真値ではない。
重なり件数を真値の95%被覆と呼ばない。
tile288 bit-flipではreferenceがp=.01で約[3.342e-8, 1.038e-5]、p=.003で約[2.232e-13, 1.259e-7]と広く、192/192の重なりを精度達成と解釈できない。
丸め前の全8referenceを[比較JSON](data_tile_validation_2026-10-17/low_long_eight_comparison_v1/comparison.json)に保持した。

## 混合診断とreference全体の包含

下表は各条件の全16設定での件数範囲である。
診断未定義や警告を含むseedも192件の分母に保持した。

| 符号・noise | p | reference区間全体の包含 /192 | 診断flag /192 | 診断未定義 /192 | 区間未取得 /192 |
| --- | ---: | ---: | ---: | ---: | ---: |
| tile72 bit-flip | .01 | 168–185 | 0 | 0 | 0 |
| tile72 bit-flip | .003 | 158–182 | 192 | 0 | 0 |
| tile72 bit-flip | .001 | 143–180 | 192 | 0 | 0 |
| tile288 bit-flip | .01 | 0 | 192 | 54–68 | 0 |
| tile288 bit-flip | .003 | 0 | 192 | 191–192 | 0 |
| tile72 depolarizing | .01 | 134–180 | 192 | 0 | 0 |
| tile72 depolarizing | .003 | 123–180 | 192 | 139–152 | 0 |
| tile72 depolarizing | .001 | 108–181 | 192 | 192 | 0 |

tile288のreference全体包含0件も、真値の被覆0件という意味ではない。
広いreferenceに由来する判定の幅と、MCMC混合診断の問題を分けて評価する必要がある。
tile72 bit-flip p=.01以外では全seedに診断flagがあり、誤差法を変更して区間の重なりが増えても混合改善とは扱わない。
32組のcondition・kernel・初期化について、4誤差法間で点推定のrelative bias/RMSE範囲と診断件数が同一であることを確認した。
診断flagが0の条件でも、収束・全失敗支持の連結性・名目95%被覆の証明にはならない。

tile288の2条件では長い全16設定で20%・10%の経験的精度gateを通っていない。
有限referenceの区間全域に対する相対RMSE範囲と適用限界は、[p=.01の結果](low_c1t0_recovered_result_2026-10-21_ja.md)と[p=.003の結果](low_c1t1_recovered_result_2026-10-22_ja.md)に示す。
校正済み推奨設定や直接MCに対する速度優位は主張せず、公開既定を変更しない。

## 検証・保存物・再現

[小仕様](low_long_eight_comparison_spec_2026-10-22_ja.md)、未実装時の失敗受入、実装、実データ確認の順に進めた。
最初の実データ処理は、後から追加されたreviewの出力一覧にsampling.jsonとrows.jsonlも含まれるため、出力directory作成前に停止した。
そのsourceを保存し、実在する二つの出力schemaだけを許可するテストを追加した。
今回消費したreview JSONと2種の集計CSVをhash照合し、raw rowsを再hashまたは再計算したとは扱わない。
元の独立算術reviewとその検証範囲は変更していない。

保存したsourceを対象とする16テストが成功し、同じ再現sourceから別directoryへ実行した2種の数値CSVはbyte単位で一致した。
今回の実行環境はWindows・Python 3.11.9で、Linuxでのこの集約scriptの実行は未実施である。

- [全128設定CSV](data_tile_validation_2026-10-17/low_long_eight_comparison_v1/long_settings.csv)：bias/RMSE範囲、診断、区間取得、全体包含・交差を保持する。
- [方法別32行CSV](data_tile_validation_2026-10-17/low_long_eight_comparison_v1/method_ranges.csv)：各4組の範囲とnull設定数を保持する。
- [manifest](data_tile_validation_2026-10-17/low_long_eight_comparison_v1/manifest.json)：集計と再現sourceを束ね、SHA256は `0a038a4263e5daec91401aad8eefbc26bcc0ded451ffc22506b622319bf2d9e5` である。
- [独立した再実行照合とテスト記録](data_tile_validation_2026-10-17/low_long_eight_verification_v1/verification.json)：SHA256は `ef164506159087178709a77e6805ab20ae8254f3955356d6a3fa1b607c67d564` である。

元reviewを保持したrepositoryで、未使用の出力directoryへ再現する。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B docs/wp/data_tile_validation_2026-10-17/low_long_eight_comparison_v1/reproduction/eight_comparison.py --repository A:/dev/mcmc4qec --output output/low_long_eight_replay_new
```

この集約で正式完了条件数は増えず、低ノイズは8/12条件のままである。
主4条件の結果、decoderの再現性・prior感度・支持の性質・利用例は[中間報告](tile_validation_report_2026-10-18_ja.md)を、稼働中の残作業は[現在の状態](PROJECT_STATUS_2026-10-22_ja.md)を参照する。
