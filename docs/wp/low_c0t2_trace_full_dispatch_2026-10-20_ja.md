# tile72 bit-flip p=.001の全trace監査

対象sampling productionは `8093838b22f74cad6ed113b5af8c185034b2585cfc4d0d7b374f150d9654b396` であり、元クラスタのdecoder環境で保存済みtraceを監査する。
全192 seed・768群を対象とし、compact記録を検査して保存された初期状態とcheckpointを復号し直す。
全stepの物理状態の再復号、乱数軌道の完全再生、独立decoder実装による正しさの証明とは区別する。

capacity job 265346はF・Exit_status 0・run_count 1であり、8群の監査失敗とsampling失敗はいずれも0だった。
最初の受理SSH接続失敗は [回復記録](trace_capacity_transport_recovery_2026-10-20_ja.md) に保存し、計算の再投入なしで受理した。
capacityの受理SHA-256は `500dd92ca778fe1cb1d158895e2e2d36645c2bb99c1067df055dbd27321df2ac` である。

全監査のprepareは正常終了し、prepared SHA-256は `20d8d409972a29b037ee11f33c6200b6516c21a7093526fce8aea8a1b6de12be` である。
job script SHA-256は `b081559d126605eccc837fb1765d7539e19d62dc876f4bd62015c558dc972c6f` である。
資源は1ノード・96 CPU/worker・83 GB・walltime上限1時間であり、予備計測からの所要時間外挿は約1116秒である。
8 workerの予備計測は96 workerでのI/O競合を測っておらず、この外挿を終了時刻の保証とは扱わない。
元の固定submission readerを変更せず、SSH観測時間だけを240秒から900秒へ広げる既存のtransport関数を使用する。
観測延長はジョブのwalltime変更や自動再投入ではなく、同じ一回のSSH実行を長く観測するための設定である。
投入には共有lockと待機中を含む最大2ノードの確認を適用し、qsubを使用する。

prepare・preflight・executeの記録は `data_tile_validation_2026-10-17/low_partition_trace_full_0_2_*_once_v1_*` に保存する。
最初のpreflight transport入口は `output/run_low_c0t2_trace_full_transport_v1.py` であり、使用済みのactionを再実行しない。
全監査の後は [C0T2最終評価runbook](portable_bar_c0t2_final_runbook_2026-10-20_ja.md) に従って全群回収と独立referenceを結合する。
最初のpreflightはSSH connection resetでexit 255・空stdoutとなり、その失敗記録を上書きせず保持した。
固定readerのexecute=false経路は読み取り専用であることを確認し、別の観測 `observe_c0t2_trace_full_preflight_v2.py` を実行した。
新しい観測はaccepted=true・slot_available=true・qsub_executed=falseで成功し、元のprepared SHAと全入力を再照合した。
再観測のreceiptは `low_c0t2_trace_full_preflight_observation_v2_receipt.json` にあり、最初の失敗receiptのhashも含む。
executeは `run_low_c0t2_trace_full_execute_v2.py` により、keepalive間隔20秒・応答欠落許容6回・SSH観測上限900秒で開始した。
この入口は新しい観測のreceipt・実stdout・hashを検査し、固定submission readerのexecuteを一度だけ呼ぶ。
transport設定は `low_c0t2_trace_full_execute_transport_v2.json` に保存し、両sourceも同じdata directoryに保存した。
ジョブの二重投入防止、共有lock、直前の実ノード数確認は元の固定readerが行う。
executeはaccepted=true・ambiguous=falseで終了し、job `265348.node-PRISM` を得た。
execute receipt SHA-256は `69e9fd5bf77175bf52c9fd3151f3e3fe9907cd69a3ae735b779f7302d2d24e99` である。
08:55:08 JSTの実qstatでは265348がQ、tile288生成265343がRであり、それぞれ1ノードの要求で待機中を含む上限2ノードを維持した。
265348の実script・CPU・memory・walltimeは固定prepareと一致した。
full監査の正常終端と結果受理は未完了であり、同じexecuteを再実行しない。
09時過ぎの実qstatでは引き続きQであり、scheduler commentは `Not Running: Insufficient amount of resource: ncpus`、開始時刻の見積りはnullだった。
14:48 JSTの実qstatで265348のRを確認し、14:53 JST前後も実行中だった。
同時にtile288 bit-flip p=.01のcollector265356がRであり、最大2ノードを維持した。
full監査の正常終端と結果受理は引き続き未実施である。
その後、実qstatで14:55:16 JSTのF・exit 0・run_count 1、walltime8分20秒を確認した。
結果受理は `output/run_low_c0t2_trace_full_completion_v1.py` で一度だけ開始し、本追記時点では応答を待っている。
固定completion readerを変更せず、既存のkeepaliveと900秒のSSH観測上限を使用する。
transport設定とsource hashは `data_tile_validation_2026-10-17/low_c0t2_trace_full_completion_transport_v1.json` に保存した。
既にcompletion intentとscriptが存在するため、同じ操作を再実行しない。
jobの正常終端とcompletion readerによる受理は区別する。
completion readerはその後accepted=true・returncode 0で終了し、job265348の正常終端を受理した。
completion receipt SHA-256は `fe900965d68d477b05a4aa9afbccd73aa5144f98c88e161fb89c68c6188d49d7`、remote completion SHA-256は `42ea16543e1498bb263856d84330a526c19f46b0a0be8786d8c6a88782d0b136` である。
記録された範囲は768群・192 replicate・184,320 planned task、failed_sampling 0、redecoded checkpoint 12,349,440である。
終端受理では全measurement artifactと監査groupのdone markerを再hashした。
監査group payload、現在の全raw trace、全物理状態の再復号をこの終端受理で行ったとは扱わず、対応する3つのflagはfalseを維持した。
最終PBS collectorで監査payloadと現在のraw traceを検証する条件は残っている。
資源外挿の約1116秒に待機時間を含めず、開始前から確定的な終了時刻を提示しない。
