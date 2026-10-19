# BAR計時manifestとseed全数監査の接続

## 小仕様

`submit_tile_seed_audit.prepare(bundle, root, *, bar_timing_manifests=())` とplan用CLIの反復可能な `--bar-timing-manifest` を追加する。
省略時は従来の監査対象とCLI commandを保つ。
指定したmanifestと同じディレクトリの `settings.json` をbundle内の実パスへ解決し、両者のSHA256を監査planへ保存する。
入力は `tile_bar_time_benchmark.make_plan(settings, capacity=..., case=...)` と完全一致することを要求する。
これにより本計時stage140の192 replicate、capacity stage141の96 replicateと、全caseの条件の元indexを既存生成APIで固定する。
unmetしかないcaseのmanifestも、空taskを持つ計画として受け入れる。
同内容manifestの別名指定、同stageで対象caseが重なるmanifest、同pathの重複指定を拒否する。
case未指定manifestは全4caseを占有するため、同stageのcase別manifestとの混在を拒否する。
追加manifest群は同一settingsの全8条件に結び付け、stage140は全4case、stage141は選択済条件のあるcaseだけを過不足なく含める。
部分集合の入力は拒否し、unmet-only caseのcapacityは要求しない。
全条件unmetの場合は `bar_timing_coverage.zero_planned_seed_stages=[141]` を保存し、catalogのstage141予約は消さない。
prepareはcatalogへ指定manifestを明示的に渡し、runは固定された各pathをauditorの `--bar-timing-manifest` へ渡す。
read_planはmanifestとsettingsの欠落、hash変化、bundle外へのescape、重複、既存科学APIによる再構築不一致、catalog証拠との結合不一致を拒否する。
追加入力のhashを既存bundle bindingへ含め、pilotと全数監査の前後で同じ入力を検証する。
plan以外のCLIで追加manifestを指定する操作は拒否し、固定済みplanの入力を後から変更しない。

## 保存済み監査の再利用限界

既存 `data_tile_validation_2026-10-17/seed_census_evidence_v1/REPORT_ja.md` は3,855,274件の全数検査と、SQLiteがTemporaryDirectoryによって終了時に削除されたことを記録している。
保存された件数・衝突統計・stream SHA256は元集合と追加集合のmembership照合に使える索引ではない。
既存監査の完了証拠は保持するが、stage140/141との非衝突はそこから推定しない。
新旧集合の全数censusを新しい監査planで再実行する必要がある。
全数censusはqsubでのみ実行し、既存freeze bundleは変更しない。
この変更では小さいfixtureの受入テストのみ実行し、実manifest生成、remote操作、qsub、全数censusは未実施とする。

## 受入条件

省略時の既存テスト、catalogへの明示転送、実行CLIへの複数入力転送、manifestとsettingsのhash結合が通る。
欠落、改変、escape、重複、再構築不一致、catalog証拠不一致を拒否する。
stage140/141の同caseは許可し、同stageのcase重複と全case指定との重なりを拒否する。
stageごとのcase不足、異なるsettingsの混在を拒否し、全unmetの0予定seed証拠と未生成予約を分けて保存する。
全case条件配列をcase別に切り詰めず、空taskのunmet-only caseも保持する。
