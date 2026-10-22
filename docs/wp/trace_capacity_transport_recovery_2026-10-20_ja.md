# C0T2 trace capacity受理の接続失敗回復

2026-10-20 08:33 JSTの受理処理は、SSH接続確立前の接続timeoutによりexit 255となった。
job 265346自体はF・Exit_status 0・run_count 1であり、再計算・再投入は行わない。
08:35 JST前後の再観測では、remoteのterminal.jsonとparent-completion.jsonはいずれも存在しない。

回復はこの失敗に限定した一回の操作とする。
元の失敗receipt、intent、script、stdout、stderrをhash付きで別directoryへ保存し、元pathから移動した履歴を残す。
科学入力と固定readerは変更せず、同じ受理処理を一回だけ呼ぶ。
元の失敗を成功に書き換えるのではなく、失敗記録を独立に保存した上で現行入口が参照するpathに新しい試行を記録する。
失敗receiptがexit 255、accepted=false、空stdout、接続timeoutのstderrであり、保存scriptと入力hashが一致することを実行前に検査する。
remoteの二つの終端記録がないことを改めて検査し、どちらかが存在すれば停止する。
archive済み・新たな失敗・不明な観測結果の場合に自動反復しない。
受入テストでは異なる終了値、stdout、stderr、入力変更、remote記録ありを拒否する。

回復は正常に完了し、計算の再投入なしでcapacityの受理を得た。
失敗した5ファイルは [失敗試行の保存directory](data_tile_validation_2026-10-17/c0t2_capacity_completion_transport_failure_v1/) に元のbytesのまま保持した。
同directoryに回復intent・結果、実行source、受入テストsource、9 passed・0.76秒のテストログ、実行ログを保存した。
新しい受理receipt SHA-256は `a9e2e0dff7914aa9215166bb7b349b35a6f763a6e680c92dabe4b85daf363818` であり、remote completion SHA-256は `500dd92ca778fe1cb1d158895e2e2d36645c2bb99c1067df055dbd27321df2ac` である。
capacityは2 seed・8群の検査であり、全192 seedの監査完了とは扱わない。
この受理を入力にfull trace監査のprepareを開始し、元の受理入口とそのsource hashは変更していない。
