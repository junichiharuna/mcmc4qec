# 低ノイズ本番BAR解析のpartition実行

合成capacityの `measured_profile` が返す資源計画と、本番sampling manifestの完全一致を要求する。
全768群を一意なpartitionへ割り当て、群内のchain・rung・設定を分割しない。
解析本体・bootstrap seed・source/runtime・sampling/native evidenceは既存 `tile_low_noise_analysis.py` を共有する。
計画は `partition_analysis_manifest.json` に保存する。
旧全群runnerとの競合を防ぐため、rootの `analysis-execution-intent.json` をmode=partitionedのrouting予約として排他的に確保する。
この予約はPBS実行済みを示す証拠ではない。

各partitionの実行はPBS_JOBID、固定thread環境、資源計画のworker数、独立native preflightを要求する。
partitionごとの排他的intent・native evidence・summaryを `analysis-partitions/{index}/` に保存する。
各groupの生解析artifactは既存形式の `root/analysis/` に保存し、既存artifactを含むpartitionを自動再実行しない。
qsubと同時最大2ノードの投入管理は別submitterが担当する。

collectは全partitionの完了証拠、全768群の一意性、各groupのJSON/NPZ checksum、全予定rowの設定座標と入力marker bindingを検査する。
欠落partition・欠落group・hash不整合は未完了または破損として停止する。
記録済みsampling failure、診断未定義、flagged、区間未取得は全て分母と出力に残す。
出力は `partition-collection/rows.jsonl` と `summary.json` とし、summaryにproduction・analysis・partition manifestのdigestとrowsのSHA256を保存する。
`undefined_diagnostics` と `flagged_rows` は該当する設定行数であり、個別observable診断の件数ではない。
`read_collection(root)` は `(production_plan, rows_iterator, collection_summary)` を返し、iteratorを最後まで消費すると全partition・group・rowとの再照合が完了する。
入力traceのmarker hashとidentityは再確認するが、入力NPZの再ハッシュ・全状態再復号・統計的正しさの保証とは区別する。
その独立trace監査は別工程で行う。

受入は全群の分割、重複・欠落・異manifest拒否、PBSとworker固定、再実行拒否、各設定行の完全性、hash binding、失敗行を残したJSONL集計を軽量fixtureで検証する。
実際の科学計算・qsubは受入では実行しない。

2026-10-18のWindows Python 3.11受入は40件が3.07秒で成功した。
Linux受入と実PBS partition解析はこの時点では未実施である。
