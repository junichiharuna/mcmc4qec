# 分割workerの証跡・値・設定選択規則の結合：受入結果

[小仕様](low_timing_partition_merge_spec_2026-10-22_ja.md)に従い、workerのPBS証跡確認と値結合、既存の計時選択規則の検証を接続した。
各workerのpreparedを独立pinで指定し、共有manifest・資源計画・環境・terminal descriptor・qsub応答・実PBS・native file・raw入力hashを結合して検証する。
workerのjob IDと結合job IDを分離し、全12条件・24行・12 binding・全352設定・各192 replicateの範囲を維持する。

実choose・値結合・PBS証跡検証・計時plan検証を使った19 testが47.41秒で成功した。
[保存source](data_tile_validation_2026-10-17/low_timing_partition_merge_acceptance_v1/)からの再実行も19 passed・48.91秒だった。
受入manifestのSHA256は `c2a4be3a11759455a0d9d0ce46983511373b758b81fc7e83d680b451ae4ecbf8` である。
raw reader・source探索・native環境は明示したdoubleまたは人工fixtureであり、実traceの再解析や実PBSジョブの受理ではない。
受入では欠落・重複・順序変更・qsub異常応答・PBS未終了と非ゼロ終了・rankとbindingの破損・分母変更・入力変更を拒否した。
全24行の値と状態がworker出力の固定順序の連結と一致し、診断未定義の192件分母を保持することも確認した。

出力は `low_noise_partition_verified_merge` であり、worker証跡と選択規則の検証が成功したことだけを表す。
選択候補の `production_selection_validated` はfalseのままで、既存の計時planへ直接渡すと拒否されることを受入で確認した。
選択規則の再構成には一時的なprivate copyだけを使い、これを正式結果として保存しない。
結合job自身の実PBS開始・終了前・正常終了の照合、再hash費用を含む資源計画、qsub投入、正常終了後の候補受理、後続censusへの接続は未完了である。
この受入によって低ノイズ9/12条件という完了数、名目95%被覆、計算効率の評価を更新しない。
