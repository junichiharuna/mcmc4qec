# tile72 depolarizing p=.001：全行の診断件数

正式受理・hash照合済みの集約行から、全352設定・各192 seedの診断件数を独立に数えた。
全67,584行で設定とseedの重複・欠落、boolean型、点推定と区間の有限性を確認した。
診断未定義・警告・失敗・区間未取得を分母から除外せず、各設定の分母を192に固定した。
ここで数えたflagは保存済みのseed単位の集約指標であり、各chainや全観測量が一律に未定義という意味ではない。
これは保存行の集計であり、IATやR-hatの再計算、decoder再実行、raw traceの再監査ではない。
最終比較ジョブ265315の出力とはまだ照合しておらず、正式比較の完了数は増やさない。

最大予定8 chains・burn-in 6000・保存12000・fine ladderの事前固定16設定を以下に示す。

| kernel | 初期状態 | 誤差法 | block | 点推定 | 区間取得 | flag | 未定義 | high R-hat | low ESS |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ZH | logical_basis | block | 32 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZH | logical_basis | block | 128 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZH | logical_basis | block | 1024 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZH | logical_basis | cross_chain | None | 192 | 192 | 192 | 192 | 192 | 192 |
| ZH | logical_combination | block | 32 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZH | logical_combination | block | 128 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZH | logical_combination | block | 1024 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZH | logical_combination | cross_chain | None | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_basis | block | 32 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_basis | block | 128 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_basis | block | 1024 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_basis | cross_chain | None | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_combination | block | 32 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_combination | block | 128 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_combination | block | 1024 | 192 | 192 | 192 | 192 | 192 | 192 |
| ZHS | logical_combination | cross_chain | None | 192 | 192 | 192 | 192 | 192 | 192 |

全設定の集計は`all_settings.csv`、固定比較は`fixed_long_slice.csv`に保存した。
bias・RMSE・被覆・同精度時間の評価は、この件数だけからは行わない。
最終報告受理後に、同じ入力hashを用いた全設定・全seedの統計量と照合する。
