# 低ノイズBARと重み層別referenceの接続検証

## 実装と検証範囲

`submit_tile_low_noise_analysis_partitions.py` は実測capacityから作ったpartition planに対して、partition別の投入記録を保存してqsubを一度だけ呼ぶ。
queuedを含む最大2ノード、稼働controllerとの競合拒否、共通lock、source・core package・Python・PBS scriptの照合を行う。
投入記録は`analysis-submissions/{index}`へ保存し、実行先の`analysis-partitions/{index}`と分ける。
曖昧なqsub応答ではintentとlockを保持し、自動再投入しない。
実測capacityと本番samplingが未完了のため、本番partition planと実qsubは未実施である。

`audit_tile_weight_reference.py` の`audit_saved_condition(root, index)`は、固定入力・source/runtime・native profile・PBS実行記録とsummaryを照合し、指定したreference条件を監査する。
全成功chunkのraw drawをseedまたは列挙rankから再生成し、artifact hash・count・集計値を照合する。
各成功chunkの先頭16個と末尾の重複しない位置を事前固定のcheckpointとして同じdecoderで再復号する。
記録済みfailed chunkを予定試行数から除外せず、reference未取得として保持する。
監査終了時にpayloadとsourceのhashを再照合し、監査中の変更を拒否する。
全ラベルの再復号、独立decoderによる検証、全16条件の監査完了は主張しない。

`tile_low_noise_reference_comparison.py` はcollectionのiteratorを最後まで消費し、全設定の全replicateを検査してから、同一case・固定priorのreferenceを一度だけ監査する。
decoder設定・runtime・native profileが異なる場合は比較しない。
省略weightの質量上界を含むreference区間を使い、部分和を全論理誤り率の点推定へ置き換えない。
bias・RMSEのreference区間に対する範囲、reference区間全体を含む被覆と交差し得る被覆を保存する。
未取得区間・失敗・未定義診断も予定replicateの分母に残す。
referenceが未取得なら全設定を保持したままreference依存の評価を未取得にする。
数値評価の依存moduleを含むsource hashを開始時と終了時に照合して記録する。
cohortの経験的RMSE範囲を母集団RMSEの信頼区間と扱わず、名目被覆も保証しない。

## 受入と独立レビュー

Windowsでsubmitter 28件、reference監査9件、比較27件が成功した。
初回3 fileは63 passed・21.47秒で、独立レビューで見つかった数値依存sourceの証跡不足を修正した後、比較27件が1.97秒で成功した。
core環境ではoptional依存のguardにより3 skipped・0.30秒、pytest終了コード5となり、科学計算の成功件数には含めない。
結果と最終source hashは`data_tile_validation_2026-10-17/low_reference_windows_acceptance_v2.json`に保存した。
submitterとreference監査の独立レビューでは阻害する欠陥は見つからず、比較のsource証跡の指摘には受入テストと実装を追加した。
saved比較の受入はreaderとauditorをfixtureに置き換えた結合境界の検査であり、実データの全数比較を実施したものではない。

## Linux配置

旧core packageと既存driverを保持した新規bundle `20261018-tile-low-analysis-v6`で、28・9・27件の計64件が成功した。
各fileのpytest時間は1.20秒・6.89秒・0.53秒で、既存Linux native profileと全比較項目が一致した。
archive SHA256は`c2c5d013953924e147e5caab6721fcdb319d5b589cb6233f9f6110a128956595`である。
ログ・入力source hash・環境証跡は`data_tile_validation_2026-10-17/low_analysis_linux_acceptance_v6.txt`、`low_analysis_acceptance_manifest_v6.json`、`low_analysis_native_comparison_v6.json`に保存した。
数値依存の版は`low_analysis_linux_provenance_v6.json`にも記録し、WSSのbeta分位点を計算するSciPyは1.17.1だった。
先行v5ではtestから参照するfixture moduleの梱包漏れで1件が失敗したため、v5を保持し、test依存も収録する別v6で修正を検証した。
科学実装と旧native profileはこの梱包修正で変更していない。
稼働中のproduction bundleとvenvも変更していない。

## 再現手順と未完了事項

本番collectionと重み層別referenceが完了した後、同一native環境を持つPBS job内で次のCLIを使う。
環境変数`OMP_NUM_THREADS`・`OPENBLAS_NUM_THREADS`・`MKL_NUM_THREADS`・`NUMEXPR_NUM_THREADS`は全て1とする。

```bash
venv/bin/python cluster_scripts/tile_low_noise_reference_comparison.py \
  --root /absolute/path/to/low-noise-run \
  --reference-root /absolute/path/to/weight-reference-run \
  --output /absolute/path/to/new-comparison.json
```

既存出力は上書きせず、新しい出力先を指定する。
比較CLIの資源計測とqsub wrapper、重み層別reference本番、低ノイズsampling・BAR本番、実reference比較は未実施である。
全checkpoint監査やreferenceの再読込費用を本計測で確認してから資源を決め、重い監査をlogin nodeで実行しない。
既存productionとcontrollerは変更せず、これらの追加受入ではqsub・commit・pushを行っていない。
