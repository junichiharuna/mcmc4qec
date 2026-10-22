# 低ノイズ完了9条件：長い設定の比較

完了済み9条件の事前固定した長い16設定ずつ、計144設定を集約した。
各設定の分母は192 seedで、未収束・診断未定義・区間未取得を理由とした除外はない。
[旧8条件の比較](low_long_eight_comparison_result_2026-10-22_ja.md)の全128設定は由来欄を含めて一致し、tile288 bit-flip p=0.001の16設定を追加した。
この処理は保存reviewの比較であり、sampling・decoder・BAR・bootstrap・WSSの再実行ではない。

各条件でZH/ZHS、logical_basis/logical_combination、block32/128/1024とcross_chainを比較する。
burn-inは6,000、ladderはfine、tile72 bit-flipは16chain・60,000保存、その他は8chain・12,000保存である。
条件間の計算予算が異なるため、同費用での性能比較ではない。

## Reference区間との重なり

各セルは4組のkernel・初期化における交差件数の範囲で、分母は設定ごとに192である。
同じseed群を使う4組を合算していない。

| 符号・noise | p | block32 | block128 | block1024 | cross_chain |
| --- | ---: | ---: | ---: | ---: | ---: |
| tile72 bit-flip | 0.01 | 172–176 | 177–184 | 180–186 | 183–185 |
| tile72 bit-flip | 0.003 | 158–161 | 172–176 | 179–182 | 181–182 |
| tile72 bit-flip | 0.001 | 143–154 | 159–167 | 174–180 | 175–180 |
| tile288 bit-flip | 0.01 | 192 | 192 | 192 | 192 |
| tile288 bit-flip | 0.003 | 192 | 192 | 192 | 192 |
| tile288 bit-flip | 0.001 | 192 | 192 | 192 | 192 |
| tile72 depolarizing | 0.01 | 145–161 | 165–180 | 171–184 | 171–182 |
| tile72 depolarizing | 0.003 | 126–137 | 151–163 | 172–181 | 170–179 |
| tile72 depolarizing | 0.001 | 108–123 | 144–152 | 173–174 | 174–181 |

referenceは重み層別MCのClopper–Pearson区間をBonferroniで合成し、省略質量上界を含めた99.9%区間である。
referenceは真値ではなく、この交差件数は真値の95%被覆ではない。
追加したtile288 bit-flip p=0.001のreferenceは約[6.310e-15, 1.741e-9]と広く、192/192の重なりから精度達成を判断できない。

## 診断とreference全体の包含

各セルは同じ条件の全16設定における件数範囲である。

| 符号・noise | p | reference全体包含 /192 | 診断flag /192 | 診断未定義 /192 | 区間未取得 /192 |
| --- | ---: | ---: | ---: | ---: | ---: |
| tile72 bit-flip | 0.01 | 168–185 | 0 | 0 | 0 |
| tile72 bit-flip | 0.003 | 158–182 | 192 | 0 | 0 |
| tile72 bit-flip | 0.001 | 143–180 | 192 | 0 | 0 |
| tile288 bit-flip | 0.01 | 0 | 192 | 54–68 | 0 |
| tile288 bit-flip | 0.003 | 0 | 192 | 191–192 | 0 |
| tile288 bit-flip | 0.001 | 0 | 192 | 192 | 0 |
| tile72 depolarizing | 0.01 | 134–180 | 192 | 0 | 0 |
| tile72 depolarizing | 0.003 | 123–180 | 192 | 139–152 | 0 |
| tile72 depolarizing | 0.001 | 108–181 | 192 | 192 | 0 |

reference全体包含0件も、真値の被覆0件という意味ではない。
tile72 bit-flip p=0.01以外では全seedに診断flagがあり、誤差法の変更による区間の重なりの増加を混合改善と扱わない。
36組のcondition・kernel・初期化について、4誤差法間で点推定のbias/RMSE範囲と診断件数が不変であることを確認した。
診断flagが0でも収束・支持の連結性・名目95%被覆の証明ではない。
追加条件の精度gate未達と独立算術確認の範囲は[個別報告](low_c1t2_result_2026-10-22_ja.md)を参照する。
校正済み推奨設定や直接MCへの速度優位は主張せず、公開既定を維持する。

## 保存物と再現

[小仕様](low_long_nine_comparison_spec_2026-10-22_ja.md)、未実装時の受入失敗、実装、20テスト成功、実データ処理の順に進めた。
保存sourceに対しても20テストが成功し、別directoryへの再実行で2種のCSVがbyte単位で一致した。
実行環境はWindows Python 3.11.9で、Linuxでの今回の集約script実行は未実施である。

- [全144設定CSV](data_tile_validation_2026-10-17/low_long_nine_comparison_v1/long_settings.csv)
- [方法別36行CSV](data_tile_validation_2026-10-17/low_long_nine_comparison_v1/method_ranges.csv)
- [全referenceと入力hash](data_tile_validation_2026-10-17/low_long_nine_comparison_v1/comparison.json)
- [manifest](data_tile_validation_2026-10-17/low_long_nine_comparison_v1/manifest.json)
- [再実行照合・テスト記録](data_tile_validation_2026-10-17/low_long_nine_verification_v1/verification.json)

manifestのSHA256は `3614825b59f113b8f371276c76fb005db0234ec0eba03a9f89800955b881cdc6` である。
再実行照合のSHA256は `9c055b959fa64e0557f151bcccb9d70ab3e70fc8730b555cb545b433bc6850f7` である。
元reviewを保持したrepositoryで、未使用の出力directoryを指定して再現する。

```powershell
$taskPython = 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe'
& $taskPython -B docs/wp/data_tile_validation_2026-10-17/low_long_nine_comparison_v1/reproduction/nine_comparison.py --repository A:/dev/mcmc4qec --output output/low_long_nine_replay_new
```

低ノイズ検証の完了数は9/12条件である。
残るtile288 depolarizingの3条件、全12条件の設定選択・独立計時・最終報告は未完了である。
