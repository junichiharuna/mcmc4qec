# Labo PCの全設定照合の完了

2026年10月20日、Labo PCで事前指定したC0T0 group `(0,0,0,0,0)` の全設定照合が終了した。
dispatcherの終了コード0と実terminal記録を確認してから、5つのraw artifactを回収した。
転送前後のremote hashと転送先hashが一致し、保存値の比較をlocalでも繰り返した。

88設定・1536 diagnostics・1536 ACF配列を、元環境で保存した同一groupの結果と照合した。
浮動小数点の許容差は事前固定のrtol=1e-10・atol=1e-12であり、離散値・flag・NaN/None位置は一致した。
decoder factoryの呼出しは0で、元samplingの重み・syndrome weight・sector・anchorを使う後処理の照合である。
実行時間は6764.777349秒であるが、速度比較を目的とした統制benchmarkではない。

最終providerの受入処理でも、固定reference archiveの全member、source・runtime・変換規則・intent・markerを照合し、88設定の保存値を再比較して受入を確認した。
結果は [最終provider向け照合記録](data_portable_bar_2026-10-19/labo-final-provider-replay-gate-v1.json) と [回収記録](data_portable_bar_2026-10-19/labo-full-parity-collection-v1/verification.json) に保存した。
今回のterminal記録SHA-256は `a80ca25b6b43ad6d7f5a493da7eefdbc224d4baf109e73f0889c5f4bafcd57f7`、completion artifact SHA-256は `5b9852be4efc601cb81c7e0c5842802290258e4cee1286debac030fe375ac0e1` である。

DGXとLabo PCの両方で事前指定groupの全設定照合を完了した。
このgroupは検証専用であり、C0T2の768群には追加しない。
全cohortの後処理一致・BARの精度や95%被覆を保証したとは扱わず、元trace監査と独立referenceとの最終比較を引き続き必要とする。
異なるOSでdecoderの失敗判定が一致するという主張でもない。

再現入口は `output/collect_portable_bar_full_parity_v1.py labo` と `output/verify_portable_parity_gate_saved_v1.py labo` である。
いずれも既存出力を上書きしないため、同じ受入記録への再実行は行わない。
実行ログは `output/portable_bar_labo_full_parity_collection_v1.log` と `output/portable_bar_labo_final_replay_gate_v1.log` に保存した。
