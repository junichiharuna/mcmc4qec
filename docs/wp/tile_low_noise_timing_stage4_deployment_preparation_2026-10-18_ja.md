# 低ノイズ独立計時 stage4：Linux 配置と読取費用

2026-10-18 の独立受入 v2（61 passed、21.36 秒、SHA256 `82308458c296a396f1e88ae0518214f2ae88c08da0bf6b783e9af165c125087f`）を固定する。
科学 source、既存 selector / stage2 / stage3 / census bridge / analysis bundle は変更しない。
配置前の最小 manifest は `data_tile_validation_2026-10-17/low_noise_timing_stage4_deployment_preparation_v1.json`、実行 helper は `output/deploy_low_noise_timing_stage4_v1.py` とする。
これは正式な計時 input、selector 実行 descriptor、PBS script、qsub を作る手順ではない。

## 実際の読取経路

行番号は受理した `tile_low_noise_timing_evaluation_report.py` SHA256 `2975f7e8d08f7fd8137b4c3a9b3245b1af8a8bd409b2206facc8b369326beb78` に対応する。

| 入口と参照先 | 保存証拠の利用 | 現在実施する計算・検査 |
|---|---|---|
| report `run:607 → inputs:321 → plans.validate_plans:190 → make_plans:145 → _validate_selection:89` | 全24行、保存候補の assessment、固定 seed / 計画 | `selector.choose:89` で保存候補を再選択し同一性を確認する。`selector.run:287` / `load_complete:157` / `select_condition:132` は呼ばない。 |
| report `selector_evidence:67` | 親 prepared / intent / receipt / script / execution / completion / terminal と保存 selection report | source / runtime / Python / native binding の bytes と実 PBS を確認する。selector 自体の再実行と fresh native probe は行わない。 |
| report `reference_evidence:199` | 16条件の audit report / summary / marker / consumed hashes、生成・監査 PBS と source | 保存 strata から `bounded.compare_condition:81` で12目標の full `[L,U]` を再集計する。`full=True` では consumed raw 全件の current hash と filename census を確認する。WSS の draw や全状態の復号は再実行しない。 |
| report `load_method:414 → load_execution:397 → execution.completed:557 → _completion:474` | capacity と各 partition の正式 summary、task clock、PBS、native、seed、保存 payload verification | `artifact_records:396 → validate_record:327` で compact 配列全体の dtype / shape / 値域、始点・終点 checkpoint の論理失敗を再確認し current bytes を照合する。 |
| execution `validate_record:327` | 保存 BAR 推定値・区間・費用 | initial / final を再復号するが、全物理状態を replay しない。`run_task:112` 内の `c.estimate_window:184` は呼ばず、ACF / bootstrap / BAR solve を再実行しない。 |
| report `assess_cohort:467 → bounded.assess_bounds:22` と `cost_ratios:506` | 固定192分母、保存推定値・区間・時計 | bounded bias / RMSE / coverage と clock 別の条件付き mean MC / mean BAR を数値再集計する。欠落点・失敗・区間無しも保持する。 |
| report `census_evidence:105 → bridge_noop_state:136` | 新 allocation ゼロの bridge manifest と baseline 56 namespace の保存証拠 | 固定 bridge 環境の subprocess で `state_only(read_plan(root))` のみ行う。pilot / census_stream / submit / seal は呼ばず、新60 namespace 監査成功とも扱わない。 |

stage4 は `read_audited_collection` を呼ばず、その import closure を source binding に含めるだけである。
`execution.inputs:296` の `native.platform_inputs:22` は保存 profile / fixture JSON と digest を読み、native probe は実行しない。
別途 Linux 配置受入では小さい固定 native fixture probe を一度実行し既存 profile と比較するが、これは正式 stage4 run の動作とは区別する。

## 費用と限界

report `run` は開始時と終端に `inputs` を検査し、その間に full reference と各完了 execution を読む。
`Evidence.track` / `finish`、完了 reader 自身の終端検査、外側 proof への採用により raw bytes の hash は複数回読む。
no-op bridge の subprocess 前後にも外側 `proof.finish` があり、終端時には既に採用した WSS raw も再hash対象になる。
従って「ACF を再計算しない」は「metadata だけで一定時間に終わる」を意味しない。
全 compact 配列検査と checkpoint 復号、全 current hash の I/O 費用は残り、現時点で本番所要時間・RSS の実測保証はない。
これらは既受理証拠と現在の bytes を結ぶための検査であり、今回新 reader や科学 source の最適化は追加しない。
保存された stage3 capacity 計測はこの報告全体の費用を測ったものではない。

## 最小配置手順

新 root 候補は `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-stage4-v1` とし、既存 root は上書きしない。
新 source / test / spec、固定 deployment manifest、入口 runner、受入 runner のみを配置する。
stage3 accepted の `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-stage2-v1/venv/bin/python` と `PYTHONPATH` の値を完全に維持する。
入口 runner は `sys.path` に新 report source と既存 bridge source の directory だけを追加し、旧 module の actual import origin を全て照合する。
これは `execution.current_runtime:454` の固定 `PYTHONPATH` 契約を維持するためであり、旧 source のコピーや alias の置換はしない。
core package は旧 v11 baseline の保存 manifest を使い、現在の Windows package を Linux 側へコピーしない。
配置 helper は排他新 root、全 tar member と digest、source / Python / native / runtime の前後一致を確認する。
軽量受入は61件を60秒 timeout で実行し、PBS 等は fixture の境界であり本番投入の証明ではないことを記録する。
結果、native profile、stdout / stderr と配置 manifest は新しい `low_noise_timing_stage4_v1_*` 証拠へ回収する。
正式 input、selector 実行、cohort 実行、全本番 raw 走査と qsub はこの配置受入の範囲外である。

## 配置結果

初回 v1 は受入 runner が stage3 の actual import alias と resolved source closure を比較したため、テスト開始前に停止した。
旧 source の変更はなく、v1 root と失敗証拠 `low_noise_timing_stage4_deployment_v1.json` は保持した。
配置検査のみを accepted `actual_source_sha256` との比較へ修正し、新 root `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-stage4-v2` へ配置した。
v2 は Linux 61 passed、skip 0、pytest 10.77秒（subprocess 全体11.06秒）で、固定 native fixture の比較差分は0だった。
全85 source / package files と旧入力の前後 hash、Python、runtime、native binary、actual import origin の一致を確認した。
source は独立受入済み `2975f7…` のままで、既存 stage2 / selector / stage3 / bridge / v11 は変更していない。
正式な環境 binding は `data_tile_validation_2026-10-17/low_noise_timing_stage4_source_binding_v2.json`、配置記録は `low_noise_timing_stage4_deployment_v2.json` に保存した。
正式 entry は新 root の `report-entry.py` で、stage3 と同じ Python / PYTHONPATH を用い、追加 import path は manifest に固定する。
正式 input / selector 実行 / stage4 本番報告 / 本番 raw 全走査 / qsub は未実施である。
