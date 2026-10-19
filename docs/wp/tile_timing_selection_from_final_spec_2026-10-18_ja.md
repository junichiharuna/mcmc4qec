# 監査済み最終集計から独立BAR計時候補への接続

選択規則と数値処理は既存 `tile_select_timing.choose` と `POLICY` をそのまま使う。
全4case・各352条件・192 replicateの監査済み最終集計を入力とし、未取得・診断未定義・区間未取得を除外する新規規則は追加しない。
新規 `tile_timing_selection_from_final.run(cases, output)` の cases は case、recovered_root、recovery_sha256 を持つ4要素とする。
recovery_sha256 は独立回収検証で受理した recovery.json のSHA256を実行前に指定する。
CLIは `--config` でこのlistを読み、`--output` の既存ファイルを拒否する。

回収proofの固定hash、全memberの安全な相対path・一意性・SHA256、予定source/input hashと保存物の一致を確認する。
回収proofを自己認証せず、引数で固定されたhashに対する整合性検査として扱う。
case別final manifest、submission intent/ledger、PBS F/exit0・script、execution intent、終端summaryと全phaseのrequest/outcome/measurement/output hashを結ぶ。
全phase成功・terminal binding成功を要求し、監査・比較・precision・weight・depolarizing strataの欠落を拒否する。
各phaseのsourceとmanifest内source closureを現在の同名sourceに照合し、保存済みproduction/analysis/referenceの結合を確認する。
precisionの全conditionの絶対誤差metricsが同じcaseのaudited reportと一致することを確認する。
4case間でproduction manifest、analysis context、reference hashが一致することを要求する。
既存chooseに保存precision reportを渡し、選択recordsは元の出力を保持する。
選択JSONには回収proof・final manifest/summary・audited/precision・adapter sourceのhashと継承した検証範囲を追加する。
入力/source hashは読取り前後で再確認する。

この接続は保存済みの全件監査とprecision集計を再利用する。
raw rowsや巨大traceの再走査、BAR bootstrap再計算、fresh native probe、全状態再復号は行わない。
過去のconsumed input hash、母RMSE、名目95%被覆、最速または推奨設定の保証は追加しない。
候補生成は少量の保存JSONとsourceの検査であり、計時manifestの作成とqsub投入は別段階である。
受入は小さい回収形式fixtureで全4case・8選択結果、固定hash改変、case/phase欠落、PBS失敗、source/input/metrics取り違え、出力上書き拒否を検査する。
本番成果物の読取りと候補生成は受入・独立レビューの後に行う。
