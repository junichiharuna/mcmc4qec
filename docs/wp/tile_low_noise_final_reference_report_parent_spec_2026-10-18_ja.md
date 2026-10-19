# 低ノイズ最終 audited WSS 比較 report：親 PBS 入口の小仕様

2026-10-18 時点の調査案であり、実装、正式 input、remote 操作、qsub は未実施である。
新しい科学関数や既存 source の変更は行わず、受理済み collection reader、保存 WSS 監査、既存 `compare_rows` を結合する親 wrapper だけを対象とする。
実装対象案は `output/submit_low_noise_final_report_once.py` と `output/test_submit_low_noise_final_report_once.py` の2ファイルで、汎用 scheduler や新 cluster scientific module は作らない。

## 調査結果

| 既存入口 | 利用できる部分 | selector の final report として不足する部分 |
|---|---|---|
| `tile_low_noise_audited_collection.py:119 read_audited_collection` | single の全768 group・192 anchor、保存 trace audit と current hash の結合 | 保存 report を生成する `run` / CLI がない。 |
| `tile_low_noise_staging_control.py:263 collect` | staged の control receipt / 実 PBS 終端、staging seal、上記 single reader の結合 | 戻り値は plan / rows / evidence であり WSS report を作らない。 |
| `output/submit_low_noise_staged_phase_once.py:388 collection_compute` | `partitions.collect` と `control.collect`、sampling.json / rows.jsonl / evidence.json、親 receipt と完了証拠 | WSS を読まず `reference_audit` と `compare_rows` の結果を作らない。 |
| `tile_low_noise_reference_comparison.py:66 run` | `compare_rows` と WSS raw audit | trace audit が結合されず、`audited_collection` / `current_trace_payloads_rehashed` がない。`source_sha256` が basename mapping で、selector の絶対 path 契約とも一致しない。数値関数の `native_decoder_revalidated=False` も `True` に上書きするので、そのまま selector の全 key 算術比較を通す入口ではない。 |
| `tile_low_noise_partitioned_collection.py:122 run` | partitioned の trace audit 結合と数値比較を保存 | partitioned 専用で single / staged に使用できない。`audit_saved_condition` を再実行し、保存済み16条件 WSS audit と結果が canonical exact に同じかをこの入口自身は確認しない。 |

`tile_low_noise_timing_selection.py:157 load_complete` は全12条件について `final_report.reference_audit` が対応する保存 WSS report と canonical exact に等しいことを要求する。
同 reader は `audited_collection` の再取得結果との exact equality、数値全 key、絶対 source closure、実 final job と元 phase の PBS census も検証する。
従って既存 CLI だけでは全12条件を一貫した final report に変換できず、最小親入口が必要である。
partitioned の既存 `run` が新しく作る WSS report と保存 report の一致は条件が揃えばあり得るが、その経路を既検証の保存監査接続として扱わない。

## 条件と出力単位

固定座標は case 0..3 × target 0..2 の全12で、各座標の reader は `single` / `partitioned` / `staged` のいずれかを明示する。
現在の staged case2 target0 を含み、他の case2 target も実際に受理した provenance に応じて明示する。
1 job は1座標の final report のみを生成し、別座標の未完了を理由に完成済み座標の処理を待たせない。
全12の固定 registry は保持し、未完了・失敗の座標を消さず、selector を正式に実行できるのは全12の成功報告受理後だけとする。
各座標は352設定 × 192 replicate = 67,584行、768 group、192 anchor を維持し、全12では811,008行となる。
352設定は `description.expected_conditions(plan)` の全順序、192 replicate は既存 `summarize_rows` / `compare_rows` により検証し、定数だけで受理しない。
失敗・未収束・診断未定義・区間無しは元の行と分母に残し、監査破損・入力欠落は「不適格な設定」に読み替えず report 生成失敗として保持する。

## 軽量 prepare と compute の境界

親 prepare は固定 registry の該当1座標、外部 hash pins、保存 manifest / summary / collection completion / receipt / script / terminal / source / Python / native binary と resource decision を読む。
prepare は NPZ、rows.jsonl 全行、trace/chunk raw、audit report の巨大 `input_sha256` 全走査、`read_audited_collection`、`reference_run.read_plan`、`selector.load_complete` を呼ばない。
保存 collection の completion record と report artifact の既知 digest を固定し、collection 自体を新規に作り直さない。
同名 report・intent・receipt・実行 marker がある root は再利用せず、新 control root は各入力 root と分離して排他作成する。
元 sampling、staging destination、audit、reference、既存 source / venv / profile を変更・移動・削除しない。
prepare の成功は current raw 受理や科学的成功を意味しない。

compute は実 PBS job / Resource_List / run_count=1 / host / argv / script / 親 intent・receipt を照合してから科学 module を利用する。
単一 thread と同じ固定 Linux Python invocation / PYTHONPATH / actual import origin を維持する。
heavy reader と current raw hash は compute 内だけで実行する。

## compute の結合手順

1. 親 prepared / script / source / runtime / input metadata の開始 snapshot を読み、保存済み collection completion と元 PBS 終端を結合する。
2. 明示 reader を呼ぶ。
   single は `single.read_audited_collection(root,audit_root)`、partitioned は `partitioned.read_audited_collection(root,audit_root)`、staged は `control.collect(root,audit_root,staging_control_pins)` とする。
   戻り値 evidence は変更せず report に格納し、旧 collection の sampling / rows / evidence 保存物がある場合は canonical equality と保存 digest も確認する。
3. 保存 reference audit の manifest / summary / execution-intent / native / 親 receipt・script / PBS を固定し、全16条件が順序通り `ok`、failed=0、terminal binding valid、phase failure無しであることを selector と同じ契約で確認する。
   全16 condition artifact の marker・payload・summary join を検査し、各保存 report を `reference_run.report_binding` に通す。
   これは保存監査の整合検査であり、新しい WSS draws の生成やラベル全復号ではない。
4. `comparison.compatible_condition(plan,reference_context)` で case / prior に一致する唯一の index を選ぶ。
   当該保存 `record['report']` を改変せず `reference_audit` に使い、`audit.verify_unchanged` と `Evidence` でその consumed input hashes / source と現在の raw bytes を結ぶ。
   全16の監査成功を確認する一方、この job で current raw を再hashする対象は該当 condition の consumed map と共有 metadata であることを明記する。
   `audit.audit_saved_condition` は呼ばず、既受理 WSS 監査の regeneration / checkpoint 再監査も繰り返さない。
5. `comparison.compare_rows(plan,rows,saved_reference['condition'])` の既存数値処理を実行する。
   full `[L,U]`、切捨て tail、不明の bias / RMSE / coverage をそのまま保持し、reference midpoint を真値にしない。
6. evidence の全 consumed file について current hash / resolved target、全 metadata / source / runtime / native と upstream terminal の安定性を再照合する。
   output target を開始時から固定し、mkdir の前後にも入力 root 外・非symlink・排他を確認してから report を1回だけ保存する。
   全消費ファイルの hash は実際に検査した bytes に結び、read→別bytesのhash の競合を許容しない。
7. report hash / input snapshot / source / clocks / peak RSS / 実行 host / job の completion marker を保存する。
   compute 内 marker を PBS `F` と同一視しない。

既存 `reference_run.read_plan → audit.read_evidence` と audited collection reader は小 native fixture probe を行う。
この fresh probe が実行された範囲を wrapper completion に記録し、`compare_rows` の既存数値 key を都合よく上書きしない。
保存 trace の ACF / IAT / BAR / bootstrap は再計算せず、NPZ展開、保存数値の集計、current raw の複数回 hash、staged の seal 前後検査は残る。

## report と selector 互換契約

`compare_rows` の返却値を基礎に、`manifest=c.digest(plan)`、`audited_collection=evidence`、`reference_audit=saved_report`、`source_sha256`、`pbs_job_id`、`hostname`、`current_trace_payloads_rehashed=True`、`raw_reference_audited=True` を付加する。
`native_decoder_revalidated` など数値返却 key は変更せず、selector が特別扱いする `raw_reference_audited` だけを監査結合後に変更する。
`source_sha256` は絶対 path mapping とし、少なくとも `comparison.source_hashes()` の各 basename を comparison 実 directory に結ぶ全 key を含め、実際に利用した reader / control / wrapper / runtime source も固定する。
旧 source の path を新 bundle の path へ書き換えず、同一bytesでも actual origin の変更は拒否する。
既存保存 WSS report の context / PBS / source path / consumed hashes はそのまま保持する。
親 submission の `manifest` は selector 契約に合わせて sampling plan digest とし、別 field の `prepared_sha256` に wrapper prepared record を結ぶ。
`command=['qsub',actual_script]`、script hash、実 argv、resource、親一回投入 intent / receipt / job を偽装せず保存する。

## 外部 completion と PBS census

親 completion 読取は実 job の `F / exit0 / run_count1 / Resource_List / Submit_arguments / exec_host` を前後に取得し、固定 prepared resource / script / 親 receipt と照合する。
report hash、completion marker、source / runtime / input metadata の同一性も確認した後でのみ final report を accepted とする。
recorded sampling failures を含む元 job の exit0/1 は既存 phase 契約で確認し、report job 自身の成功 exit0 と区別する。
失敗した report job の部分出力は incomplete として保持し、自動再実行しない。

selector 用 `terminal_receipt.Jobs` は `load_complete:245–283` が組み立てる exact job set と完全一致させる。
元 sample / anchor job、partitioned sampling と collector、analysis 各partition、full trace audit、元 WSS、WSS audit、final report、および実際に `partition-collection/summary.json` に記録された別 collector job を含む。
staged の元 sample / anchor ledger は元 absolute source root の receipt を使用する。
copy や staged parent collection の job が selector の set に現れない場合、それらを selector 用 exact `Jobs` に勝手に追加せず、別の親 provenance terminal evidence と control / seal 証拠に保存する。
特に旧 single collection summary に存在しない PBS field を追加して、新しい job が旧 collector を実行したように見せない。
新 report が本当に selector に受理されることは、受入 fixture で final PBS `F` 後の `selector.load_complete` 実入口に通して検証する。

## 親一回投入と資源

既存共有 `tile-low-noise-submission.lock`、controller finished 証拠と実 PID 不在、queued を含め最大2 nodes、qsub 直前再確認を維持する。
remote / local intent は排他、qsub は1回、曖昧応答では intent / lock を保持し再試行しない。
qsub は親のみが実行する。
各条件の処理は直列 reader なので1node・1CPU・1workerを基本とし、memory / walltime は該当 collection 実測、保存 file / byte / row metadata、追加 WSS hash と数値再集計の scope差を記録した親 decision に固定する。
staged case2 target0 は copy / seal の追加hashと collection 実測を利用し、synthetic BAR capacity を report I/O 時間へ流用しない。
現段階では実測に基づく資源値が未確定であり、1node340GiB24hを使用する場合も政策上限であって完走保証とは書かない。
親が resource decision を確定するまでは executable ready としない。

## 軽量受入案

- single / partitioned / staged をそれぞれ明示選択し、既存 reader の保存 evidence を無改変で結合する。
- 保存16条件 WSS audit の一部欠落・失敗・順序差・marker改変・prior違い・source/path差・raw consumed hash差を拒否する。
- `audit_saved_condition` / ACF / BAR / sampling / collection再作成 を monkeypatch で禁止し、既存 compare_rows だけを数値処理として通す。
- 全352設定 / 192 replicate の欠落・重複を拒否し、失敗・未収束・診断未定義・区間無しは分母に残す。
- final report の全数値 key / exact保存WSS report / absolute numerical source closure / final PBS receipt を `selector.load_complete` へ接続し、3種類の reader と staged 元 absolute receipt を確認する。
- metadata prepare は raw・全rows・native probeを呼ばず、compute は PBS guard 前に heavy reader を呼ばない。
- current bytes / resolved target / output parent retarget / source / native / runtime / PBS終端変化を拒否する。
- copy と staged collector を別 provenance に保持しつつ selector 用 exact terminal census に余計な job を入れない。
- qsub mock で queued2nodes / controller / lock競合 / 重複intent / 曖昧応答を拒否し、1回投入と記録保存を確認する。

受入は小 artifact fixture と数値 fixture のみで1file60秒以内とし、正式データ全走査や qsub は行わない。
