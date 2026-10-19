# 低ノイズ独立計時 selector 第1段階

既存の independent timing 仕様の第1段階だけを実装する。
所有ファイルは `cluster_scripts/tile_low_noise_timing_selection.py` と対応する test、本書であり、既存 driver を変更しない。
新 seed、予算、sampling、capacity、submitter、時間比は作らない。

`identities()` は case 0..3、target index 0..2、epsilon index 0..1（.2,.1）の順の24行を返す。
`select_condition(plan, rows, condition)` は既存 `compare_rows` を用いる純数値入口であり、保存証拠を監査したとは主張しない。
全192点と全予定設定を必須とし、欠損点・区間なし・診断undefined・flagを残す。
各 epsilon について正の full reference interval と width 必要条件を先に判定し、全域相対RMSEの既存分類 `empirical_within_target` だけを候補とする。
候補順位は rung数×chains×(burn+samples)、cross_chain優先、block小、ZH優先、logical_basis優先、canonical condition の順とする。
全候補の assessment と分類件数を残し、selected は独立評価候補であって推奨ではない。
全行の `speed_ratio` は null とする。

保存入口 `run(input_path, expected_sha256, output)` は外部SHAで固定された12条件の input manifest を読む。
入力には source closure と case/target ごとの pending または complete、complete の場合は sampling/audit/reference/reference-audit roots、single/partitioned/staged reader の選択、最終 audited comparison report、必要metadataの外部pin、終端PBS receiptを指定する。
12条件のうち一つでも pending なら全24行を `selection_pending` で保存し、raw scan と候補選択はしない。
pending は明示的未完了だけを表し、complete と宣言した入力の欠損・不一致は validation failure として停止する。
全completeの実読取はPBS・固定single-thread環境だけで行う。
既存 full audited collection reader と WSS auditの固定report bindingを再利用し、最終reportの数値を全raw rowsから再計算して照合する。
WSS監査は全16条件の成功終端と対象conditionの保存artifactを結び、対象reference raw hashを再照合する。
sampling/anchors、全analysis partition、full trace audit、最終collection、元WSS、WSS監査の実job集合を入力側のterminal bindingsと完全一致させる。
各jobのledger、manifest、script hash、PBS F/exit、Submit_argumentsを確認し、既存readerが確認しないcollector自身の終端も省略しない。
元sampling/referenceの記録済み失敗は全分母に残し、監査・解析・collectionの異常終了は成功に変換しない。
staged inputは `tile_low_noise_staging_control.collect` を通し、entryの `staging_control_pins` に全analysis/full auditのprepared/receipt SHAを要求する。
この入口は既存seal readerと全control completionの資源・host・run_countの既存検証を再利用する。
selector共通の終端照合自体はF/exit・job/script/manifestを対象とし、旧single入口の全job資源やrun_countを新たに独立認証するものではない。
資源・hostが揃った独立計時の比較は後段であり、本段階のnull比を変更しない。
外部pinの不足、native/runtime/prior不一致、source変更、読取中のhash/解決先変更は選択を停止し、科学的ineligibleに変換しない。
outputは入力root外へ排他作成し、既存結果を上書きしない。
保存済みselectionを将来のreferenceで更新せず、新しい外部pinと別outputを作る。
独立配置ではselector、v11共有module、staging-v1、control-v2の実import解決先を維持する。
source closureはfunction-local importを含むASTから実import先を解決し、絶対解決pathとSHAの組を入力manifestへ固定する。
同じbytesでも別pathへの差替えは既存pinと一致せず拒否する。
既存bundleへ新moduleを書き込んだり、旧sourceの解決先を新bundleのcopyへ変更したりしない。

受入は小さい数値fixtureとmetadata reader境界mockを分離し、mockを本番raw監査と表現しない。
24行、全192分母、width等号/不可能/zero/missing、全候補順位、欠損/undefined保持、pin改変・終端不一致・読取中変更・既存output拒否を検査する。
本番データの選択とqsubは実施しない。
