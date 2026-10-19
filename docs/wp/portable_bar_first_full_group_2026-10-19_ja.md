# 移植後の最初の全window結果

DGXのbatch 0で完了したC0T2 group `(0,2,0,0,10)` を、batch全体の回収前に読み取り専用で検証した。
完了groupを観測した時点で最初に確認できたものを使い、良い推定値や診断値で選択していない。
この確認は引継ぎcontrollerのcollectorを実行せず、batch全体を受理するものでもない。

全88設定・診断2328件・ACF2328配列について、元sourceとexport manifest、各入力payloadとmarker、task metadata、設定の順序、結果hashと診断の対応を確認した。
decoderを再構築せず、数値推定・ACFの再計算も行っていない。
samplingの記録済み失敗と区間未取得はともに0だった。
診断flagは88行すべてにあり、未定義診断を含む行は48行だった。
flagや未定義の行を除外しない。
この1 groupから混合、bias、RMSE、95%被覆の結論を出さず、事前に固定した全192 replicateの結果と独立referenceを待つ。

このgroupの記録された処理時間は1698.55秒だった。
これは追加の速度benchmarkではなく本処理の実測であり、異なる条件のcluster jobとの速度順位に使わない。
他groupと両PCのbatch全体の完了は別に確認する。

検証receiptは [dgx-first-full-group-validation-v1.json](data_portable_bar_2026-10-19/dgx-first-full-group-validation-v1.json) に保存した。
生結果はDGXの `/home/other/workspace/mcmc4qec/20261019-experimental-platform-v2/portable-bar-full-batch0-v1/result/groups/0-2-0-0-10/` にあり、batch終端後の既定の回収対象に含める。
analysis JSONのSHA256は `af4299fe72740fcaacbb63b19131c40d7fff5caa6227e68cff2d06130caddce5`、marker SHA256は `9e2333989ccb1d54dc0643f5b372a32fda8c6709741c2df6e9d5b5744a72d263` である。
検証scriptは `output/validate_first_portable_group_v1.py` に置き、保存済みreceiptの上書きを拒否する。
batch全体の正式な回収とsampling監査・referenceとの結合は引き続き未完了である。
