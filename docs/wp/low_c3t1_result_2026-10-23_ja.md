# tile288 depolarizing p=0.003の条件別結果

2026-10-23に最終集約・回収・集計値の照合・比較用入力の準備が完了した。
今回の設定群はexperimentalな再現・調査用として保存し、校正済みの推奨設定にはしない。
全12条件の正式比較と独立計時は未実施である。

## 結果と適用限界

全352設定について各192反復、計67,584行を保持した。
点推定は各192件、区間未取得は各0件である。
全設定で診断flag・診断未定義が各192件あり、事前固定した長い16設定も同じだった。
全352設定で経験的な相対RMSE 10%・20%のgateは `empirical_above_target` だった。
これは保存済みの有限referenceと反復結果を用いる判定であり、母集団RMSEの証明や真値の確定ではない。
未定義診断・未収束を理由に反復を分母から除外していない。
区間を取得できたことだけでは混合・精度・名目95%被覆の保証にならない。

重み層別referenceのfull point estimateは未取得である。
partial estimateは約2.071e-15だが、これを真値や全重みの点推定へ置き換えない。
保存された99.9% reference区間は約[7.964e-20, 8.723e-7]で、各層のClopper–Pearson区間、Bonferroni補正、未評価質量の上界を含む。
この広い区間との整合だけから精度や95%被覆を認定しない。
BP-OSDの固定prior・実行環境などの前提は[途中結果の利用案内](low_noise_interim_usage_2026-10-23_ja.md)に従い、別decoderへ結果を外挿しない。

## 完了の根拠と再現

集約jobはqsub投入記録に対応し、終了コード0、実walltime3時間45分37秒だった。
回収した13ファイルのhash照合後、後続処理が11,968個の集計値を照合し、最大絶対差は約5.170e-26だった。
この照合は集計算術の確認であり、全traceの再監査やMCMCの収束証明ではない。
[集計値レビュー](data_tile_validation_2026-10-17/control_newline_recovery_v1/planned8h_final_c3t1_downstream_handoff_v2/c3t1/review/review.json)と同階層のCSV・manifest・reproductionに原結果と再現scriptを保存した。
今回の文書用集計は[観測記録](data_tile_validation_2026-10-17/c3t1_usage_observation_20261023_v1/observation.json)に保存し、CSVとreviewのsize・SHA256を既存manifestと照合した。
同階層の `observe.py --root <repository> --output <new-directory>` で文書用集計を再現できる。
このscriptは既存CSVを数え直すだけで、新しいsampling・復号・BAR・bootstrap・reference計算は行わない。
全12条件比較用candidateの準備は完了したが、candidateの存在を科学的な精度合格とは扱わない。
