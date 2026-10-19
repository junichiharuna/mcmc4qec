# main 独立計時の報告 adapter 小仕様案

本書は [独立レビュー](tile_timing_comparison_scope_review_2026-10-18_ja.md) の main 報告案を具体化した実装前仕様である。
現段階では仕様だけを保存し、計時・sampling・qsub・既存 source の変更は行わない。
対象は p*=.03 の tile72 と p*=.05 の tile288、bit-flip/depolarizing の 4 case × epsilon=.2/.1 の固定 8 行である。
既存候補、閾値、全 192 replicate、stage121/140、reference、判定数式を変更しない。

## 実装範囲と API 案

新規 `cluster_scripts/tile_timing_evaluation_report.py` と `tests/test_tile_timing_evaluation_report.py` を追加する。
既存 `tile_timing_metrics`・`tile_precision_assessment`・`tile_summary`・計時 driver は変更しない。
`prepare(config_path, output_plan)` は metadata と外部 pin を検査し、入力・source・予定条件の固定 plan を排他的に保存する。
`run(plan_path, output_root)` は PBS 内で全 payload の照合と数値報告を行い、新しい出力 root に `report.json` と日本語表を保存する。
軽い `render(report_path, output_path)` は既存 report の hash を確認して日本語表示だけを作り、再集計しない。
比較用 qsub の resource/submitter 自体は別工程とし、この仕様で追加の計時や新しい scheduler policy を作らない。

config は固定 selected settings の path/hash、選択回収証拠の外部 pin、MC root と accepted 回収/正式 terminal の path/hash、case 別 BAR root/状態証拠、reference summary/audit の path/hash、受理済 seed census の path/hash を持つ。
reference と settings の外部 pin は当 reader が今読んだ値から自己生成せず、受理済み回収記録から渡す。
各 BAR case の予定 root は manifest/settings に結び、未実行・未完了・完了を operator の自由な数値だけで選別しない。
未実行は execution intent・task・summary が存在しないことと固定 plan を確認し、実行中・中断は存在する実行証拠に対応した未完了として保存する。
未完了の raw task 全監査を本 adapter で実装しない場合、observed task/point 数は unknown とし、planned_replicates=192 を維持する。
元 job が存在しないことを確認できない状態を、未実行 0 件や科学的失敗 192 件へ変換しない。

## 完了入力の結合

既存 `tile_timing_comparison.load_cohort` の固定 plan・metadata・payload 検査を再利用する。
加えて submission intent/ledger、qsub script、実 execution intent/native、正式 PBS terminal の job ID・host・resource と同じ実行を検証する。
全予定 task が正しく保存されている場合に限り、記録された task failure を含む非 zero 終端を `completed_with_recorded_task_failures` と区別して受け入れる。
非 zero 終端を単純除外せず、反対に missing artifact・kill・worker crash・未終端を記録済み sampling failure に読み替えない。
全成功を主張する summary と非 zero 終端が矛盾する場合は完了扱いしない。
MC 1536 task、BAR は選択された各条件 192 task の固定 census を確認し、未選択条件に task がある場合は拒否する。
model/failure/decoder prior、native input/binary/profile、seed、trial/trace/chain/anchor の実 metadata を固定計画と照合する。
既存有限 native probe と seed census の成功を、全 decoder 状態・乱数 stream 独立性の証明とは表示しない。

source は比較 adapter、数値 helper、そのローカル import closure、固定 package/runtime を含めて開始前と公開前に照合する。
読み込んだ全 JSON/NPZ、marker、receipt、script は lexical path・解決先・hash を記録し、終端で再確認する。
選択 proof や native 入力の解決先が同じ bytes の別ファイルへ変わった場合も拒否する。
既存 root、既存 report、受理済み証拠を上書きしない。
終端照合が失敗した場合は成功 report を公開せず、失敗理由を別の診断記録に保存する。

## 固定 8 行の数値と状態

各行は case、epsilon、prior、選択 condition、planned_replicates、選択と評価の別々の欄を持つ。
selection 欄には候補の全 192 校正点・区間・診断 flag 数、bias/RMSE/被覆、候補数、順位規則、入力 digest をそのまま保存する。
evaluation 欄は MC/BAR ごとの status、全 cohort counts、点・区間欠損、記録された failure、reference 区間に対する bias/RMSE 範囲と点での補助量、被覆の point/entire/possible を保存する。
独立 BAR の mixing diagnostics は not_collected、MC は not_applicable とし、校正の診断を独立評価へコピーしない。
既存 metrics 内部の BAR flagged/undefined=192 は診断未取得の保守的 placeholder と明記し、実測された R-hat/ESS failure 192 件として表示しない。
内部数値の改変を避けるため既存 helper の出力はそのまま保存し、別の `diagnostic_observation` 欄と日本語表で意味を分離する。

点推定の相対 RMSE gate は既存 `metrics.compare` と同じとする。
両手法が全 192 点を持ち、finite reference 区間全域で empirical_within_target のときだけ、全 task 平均費用の MC/BAR 比を clock ごとに出す。
区間未取得は分母に残るが、点 RMSE gate と区間被覆を混同しない。
above/reference_sensitive/incomplete_points/reference_zero_boundary/numerical_range では比を null と理由付きで保存する。
全 point が取得されても wall または CPU の欠測があれば、その clock の比だけを null とする。
失敗 task の消費時間を落とさず、取得例だけの平均は available_only と表示する。
BAR 未実施・未完了・選択未達でも予定行を消さず、比を null と状態理由を残す。
現在の MC 再集計で gate を通らなかった 4 条件を、BAR 結果到着後に閾値・seed・行の選別で通すことは禁止する。

## 時間と推論の範囲

task wall、process CPU、construction/anchor/initialization/sampling/compact/analysis、job phase、PBS wall を別欄にする。
MC は全 8 条件を一つの pool、BAR は case ごとの pool であること、workers、host、node/CPU/memory、thread/native/package を保存する。
pool phase wall は条件や replicate 数で按分せず、CPU と wall を混ぜた比も出さない。
CPU model/frequency/affinity/NUMA/当時の負荷など未記録の条件は unknown とする。
host が異なる場合にも同一 native profile だけから同等性能を推測しない。
比は記録された環境での未補正 task 費用比であり、固定 epsilon 以下を経験的に満たす設定の記述量とする。
母時間比・最速設定・最小 time-to-accuracy・母 RMSE・名目被覆を保証しない。
同じ有限 reference が選択・MC予算・評価に共用されること、99.9%が全条件の同時保証ではないことを明記する。
本 report は main 専用であり、低ノイズの同精度計時は未評価欄へ明記する。

## 小さい受入案

1. 固定 8 行を模す全 192 replicate の数値 fixture で、MC above/reference_sensitive と BAR within の組合せでも比が null であることを確認する。
2. 両者 within、費用欠測、failed、区間のみ欠測、未実施、未完了、選択未達を分け、分母・理由・available_only が正しく残ることを確認する。
3. 校正 flagged=192 と独立 BAR not_collected を区別し、独立診断を良好・失敗の実測値として捏造しないことを確認する。
4. mean(MC)/mean(BAR) を用い、mean(MC/BAR) や phase 按分を用いないことを確認する。
5. 外部 settings/reference pin、task/seed/model、正式 terminal、qsub script、native、resource の異なる fixture を拒否する。
6. known recorded-task-failure 終端では全 counts/cost を残し、同じ非 zero でも missing artifact・成功 summary 矛盾は完了にしないことを確認する。
7. payload/marker/source/receipt の途中変更と同 hash の path retarget で、成功 report が公開されないことを確認する。
8. host/CPU情報の不足を unknown と表示し、同一 hardware を自動認定しないことを確認する。
9. 保存済み MC summary の軽量 fixture または既存 JSON を読み、上記 4 within・2 above・2 reference_sensitive と全8行の欠落なしを再現する。
10. fresh output・排他作成・PBS guard と完全な source closure を確認し、元 artifact や計時 source を変更しない。

各 test file は 60 秒以内とし、実 payload 全走査は軽量受入へ含めない。
数値 helper の再実装、比の bootstrap CI、追加 MC、候補再選択、新 sampling、qsub はこの実装範囲に含めない。
