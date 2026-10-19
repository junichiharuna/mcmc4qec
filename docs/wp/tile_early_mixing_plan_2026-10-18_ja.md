# 完了済みtile288 traceの早期混合診断

実行前にcase `[1,3]`、kernel `[0,1]`、initialization `[0,1]`、replicate `[0,1]` の直積16 groupsを固定する。
各groupは最終rung、8 chains、burn-in 6000、保存12000 stepを用いる。
case3のlogical初期化は既存driverのreplicate 0がX、replicate 1がZとなる選択をそのまま含める。
本番計画、seed、decoder prior、稼働bundleを変更しない。
weight、syndrome weight、全logical bit（case1は8、case3は16）のIAT・ESS・split R-hat、sector遷移数・unique数、条件付きweight平均・IAT標準誤差を既存 `calibration.diagnostic_record` で求める。
観測量224群と128 traceが対象であり、BAR推定・reference比較・被覆校正は実施しない。
本番manifestと `tile_bar_study.make_plan()`、source/runtime、native profile、artifact identity/hash、task metadataを確認する。
既存 `audit_tile_traces.audit_trace` により全compact配列と保存checkpointを検査する。
再復号対象はinitial128状態とcheckpoint2432状態であり、元の全物理traceの再復号ではない。
失敗、破損、未取得、診断未定義を明示して16 groupsの予定分母を保持する。
最初にcase3・kernel0・initialization0・replicate0の1 groupだけを時間pilotとして実行する。
2倍の全16 group外挿が45秒未満なら残りを単一processで実施できる。
超える場合は診断値を見ずに事前固定順序の1 groupずつ実施し、各commandを60秒以内とする。
pilotから総費用が軽量範囲を超えると判断される場合は実測値を報告して停止する。
今回の値は早期診断であり、本校正の代替、収束の証明、低ノイズ精度の保証、decoder間の性能順位には用いない。
