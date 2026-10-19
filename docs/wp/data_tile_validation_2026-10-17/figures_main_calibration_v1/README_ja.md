# 主校正比較図の保存物

[PNG](main_calibration_comparison.png)と[SVG](main_calibration_comparison.svg)は、固定ZH/rejection条件における相対RMSEとMC点基準の区間被覆を示す。
英語ラベルのstandalone図で、日本語の解釈と制約は[caption](caption_ja.md)に保存した。
この設定は公開既定の1 chainとは異なり、推奨設定の確立や名目被覆の保証を示さない。
[CSV](figure_data.csv)は4case×3誤差法の12行、[JSON](figure_data.json)は同じ値と設定・reference・分母・入力/source SHA256・環境を保持する。
[検査記録](validation.json)はCSV/JSON一致、入力hashの再照合、画像目視QAと全artifact hashを記録する。

元のauthoritative概要と受理済みaudited/precision summaryを読み、保存値の照合と表示単位の変換のみを行った。
元data、報告文書、科学moduleは変更せず、新しいsampling・bootstrap・decoder・ACF・raw trace走査も行っていない。
描画処理はWindows Python 3.11とmatplotlibで約3.2秒だった。

再生成例は以下で、出力先には未使用のdirectoryを指定する。

```powershell
& 'A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe' docs/wp/data_tile_validation_2026-10-17/figures_main_calibration_v1/regenerate.py --output output/main_calibration_figure_reproduction
```

再生成scriptは既存図の上書きを拒否する。
元dataを別の場所に配置した場合は `--data <data_tile_validation_2026-10-17>` を追加する。
目視QAの追加実行記録は再生成scriptの自動出力に含めない。

`docs/wp/` の日本語報告へのリンク案は以下とし、本作業では報告本文へ挿入していない。

```markdown
![主校正の固定ZH/rejection条件における相対RMSEとMC点基準の被覆](data_tile_validation_2026-10-17/figures_main_calibration_v1/main_calibration_comparison.png)

[図の日本語caption・適用限界](data_tile_validation_2026-10-17/figures_main_calibration_v1/caption_ja.md) · [SVG](data_tile_validation_2026-10-17/figures_main_calibration_v1/main_calibration_comparison.svg) · [数値CSV](data_tile_validation_2026-10-17/figures_main_calibration_v1/figure_data.csv)
```
