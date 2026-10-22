# 回復済み低ノイズ2条件の独立算術レビュー

2026-10-20に、tile72 bit-flipのp=.01（C0T0）とp=.003（C0T1）について、保存済みBAR推定値と区間から集計を独立に再計算した。
[小仕様](low_recovered_arithmetic_review_spec_2026-10-20_ja.md)に従い、失敗する配置受入、隔離実装、回帰検証、実データ取得とレビューの順に実施した。
各条件の全67,584行・352設定・192 seedを使用し、診断flag・診断未定義・区間未取得を理由とする分母からの除外は0である。

| 条件 | 照合した値 | 保存reportとの差の最大絶対値 | 取得・算術レビューの実測時間 |
|---|---:|---:|---:|
| C0T0、p=.01 | 11,968 | 1.734723475976807e-18 | 23.334秒 |
| C0T1、p=.003 | 11,968 | 6.938893903907228e-18 | 26.307秒 |

整数・件数は厳密に照合し、浮動小数点は相対許容差1e-10・絶対許容差0で照合した。
上表の時間は転送と集計の処理時間であり、samplingやBAR推定の計算時間ではない。
標準libraryを用いる既存算術の6関数・classについてASTの一致を確認し、入力配置の検証だけを拡張した。
追加経路を含む受入・回帰はWindowsで52 passed・1.38秒、Linuxで52 passed・0.22秒だった。
元sampling planと回復先rowsのpath・hashを元reportの全体およびpartition evidenceへ結び、別々の元jobと回復jobのidentityを保持した。

## 長い設定での区間への感度

固定抜粋はfine ladder、16 chain、burn-in 6,000、保存60,000である。
ZH/ZHS、logical_basis/logical_combination、block長32/128/1024およびcross_chainの全16設定を含む。
従来の結果文書にあるblock長1024とcross_chainの8設定の抜粋とは範囲が異なる。

| 条件 | reference区間全体を含む件数 /192 | reference区間と重なる件数 /192 | 診断flag /192 | 診断未定義 /192 |
|---|---:|---:|---:|---:|
| C0T0、16設定の範囲 | 168–185 | 172–186 | 0 | 0 |
| C0T1、16設定の範囲 | 158–182 | 158–182 | 192 | 0 |

referenceは層別samplingに基づく99.9%区間と省略質量の上界を用いており、厳密な真値ではない。
表の2種類の件数は有限reference区間に対する包含・重なりであり、真値の被覆件数を直接観測したものではない。
長い設定でも誤差法・block長への感度があり、C0T1では全seedに診断flagが残る。
算術の一致は、混合、推定精度、名目95%被覆の保証にはならない。
raw trace、復号label、WSSラベル、BAR推定、bootstrapを再実行したレビューではない。

## 保存物と再現

[保存manifest](data_tile_validation_2026-10-17/low_recovered_arithmetic_extension_v1/manifest.json)はsource・受入・失敗ログ・Linux実行記録・集計CSVなど41ファイルと、別保存の大きなrowsファイル2個を束ねる。
2026-10-20の報告作成時に全43ファイルのbyte数とSHA-256を再照合した。
manifestのSHA-256は `b59f08e74acbc10a4ec5c71a8235028914ed65db57ba8c932639ee0733fad27d` である。

- C0T0：[受理記録](data_tile_validation_2026-10-17/low_recovered_arithmetic_case0_target0_v1/receipt.json)、[レビュー](data_tile_validation_2026-10-17/low_recovered_arithmetic_case0_target0_v1/arithmetic/review.json)、[全設定CSV](data_tile_validation_2026-10-17/low_recovered_arithmetic_case0_target0_v1/arithmetic/all_settings.csv)。
- C0T1：[受理記録](data_tile_validation_2026-10-17/low_recovered_arithmetic_case0_target1_v1/receipt.json)、[レビュー](data_tile_validation_2026-10-17/low_recovered_arithmetic_case0_target1_v1/arithmetic/review.json)、[全設定CSV](data_tile_validation_2026-10-17/low_recovered_arithmetic_case0_target1_v1/arithmetic/all_settings.csv)。
- [実行後の環境観測](data_tile_validation_2026-10-17/low_recovered_arithmetic_environment_20261020_v1.json)：Windows、Python 3.11.9、算術依存は標準libraryのみ。

環境観測はレビュー完了後の記録であり、実行中の環境封印と同一視しない。
この環境ファイルは上記41ファイルのmanifest外に保存し、SHA-256は `e0ef5e086e2ab3ed5afd19ed1dd9de36b268fa4c13d2184ef62a39e65ff5d957` である。
隔離source `output/low_recovered_arithmetic_extension_v1/review_low_final_arithmetic.py` のCLIは `--reader recovered` と、`--report`、`--report-sha256`、`--plan`、`--plan-remote-path`、`--rows`、`--rows-remote-path`、`--output` を受け取る。
各条件の `intent.json` と `inputs/collection.json` に元report、plan、rowsのpathとhashを保存している。
保存済み入力から算術を再実行する際は、元remote pathをそのまま指定し、存在しない新しい出力directoryを指定する。
取得とレビューをまとめた `run_actual_reviews_v1.py` は排他的な一回実行用であり、既存の回収先へ再実行しない。

この追加確認は完了済み2条件の根拠を補強するもので、低ノイズの正式比較の完了数は5/12条件のままである。
公開候補、稼働中のpipeline、公開既定は変更していない。
