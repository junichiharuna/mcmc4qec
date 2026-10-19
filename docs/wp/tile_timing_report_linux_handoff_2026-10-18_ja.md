# main 独立計時報告の Linux 配置と正式実行手順

正式な報告用 bundle は `/home/user/workspace/mcmc4qec/20261018-tile-timing-report-v2` である。
v1 は受入自体が成功したが、配置 builder が submitter の依存 `submit.py` と `submit_tile_capacity.py` を含めていなかったため正式集計には使わない。
v1 の source・archive・証跡を保持し、承認済み同一 bytes の依存を加えた fresh v2 を配置した。
既存の科学 driver、元計時 root、既存 bundle は変更していない。

## 固定した実装と検証

新 adapter の SHA256 は `0b6c393f0b77237110cee090dc7a464c247e3b83df55174760ff971f7efcdf98`、test は `7d08ad358af20293469c2d12371148cd437e55c842f205b5f1fd418470745df4` である。
Windows の作成者受入は 35 passed / 22.03 秒、独立再受入は同 35 件 / 26.78 秒と改変再現 2 件 / 10.39 秒だった。
Linux v2 は 35 passed、pytest を含む subprocess 計時は 6.09 秒だった。
各 file 60 秒・全体 5 分以内の軽量受入であり、本番の全 task payload 走査は実施していない。
独立レビューの詳細は `data_tile_validation_2026-10-17/tile_timing_evaluation_report_independent_review_v2_ja.md` にある。

v2 archive SHA256 は `2e1e62a7c879a0ac419b0c4314702f0d4058c78b0701cab9213cfe3f8def3027`、121 files / 831970 bytes である。
accepted v11 と timing-comparison-v1 の既存 closure を使い、accepted core 29 files をそのまま維持した。
現在の Windows workspace にある追加 decoder package 差分は Linux bundle にコピーしていない。
固定 native fixture の Linux profile は全照合項目で既存 profile と一致した。
Windows native profile との不一致は既存どおり保存し、別環境を同じ decoder 実行と扱っていない。
`output/deploy_timing_report_v2.py`、`data_tile_validation_2026-10-17/timing_report_deployment_v2.json`、同 `timing_report_linux_provenance_v2.json` に再現手順・元 archive・source・環境・native hash がある。

## 実 metadata だけの smoke

`output/prepare_timing_report_smoke_v2.py` は本物の MC 完了 root と BAR case0 完了 root を読み、固定 settings/reference/census・外部回収 inventory・正式 PBS receipt を結合して `prepare` を実行した。
処理時間は 0.694 秒で、明示 closure roots と全 26 cluster module の実 import 先・hash を保存した。
runtime/native 入力から旧 driver の固定 manifest を再構築する経路も通した。
main case0 は `265263.node-PRISM`、MC は `265237.node-PRISM` に結び付く。
全 payload 読込・状態再復号・native probe の追加実行・qsub はこの smoke では行わない。

smoke root は bundle 内 `runs/metadata-only-smoke-v1` であり、正式集計 plan ではない。
残り 3 case は意図して欠如させた保存 root を使い、`not_prepared` はこの smoke で未観測という意味である。
本物の case1/2/3 の scheduler 状態や、未投入・未完了を推定したものではない。
`data_tile_validation_2026-10-17/timing_report_smoke-provenance_v2.json` の SHA256 は `91e2b927aad199f7c69b4bc46c020e1339e78c7db61625b1b254dfbe3e1a5095` である。
その `formal_plan` と `formal_results` は false である。

## 正式 config の作成条件

正式集計は MC と main 全 4 case の完了成果物・正式終端・独立回収 proof が揃ってから行う。
capacity の artifact は本計時の標本へ混ぜず、本計時と capacity を取り違えないよう元 manifest・resource・receipt の結合を保持する。
予定 8 行・各 192 replicate、全 3072 MC/BAR task を保持し、記録済み失敗や区間未取得を除外しない。
欠損 artifact、kill、timeout は保存済み task failure に読み替えない。
全 task と summary が揃い、旧 driver の記録済み task failure 後の exit1 と整合する場合は `completed_with_recorded_task_failures` として保持する。

config の各 pin は `{ "path": "/absolute/path", "sha256": "accepted external hash" }` である。
現在読んだファイルから受理の根拠まで自己生成せず、独立回収時に受理した hash と照合して固定する。
`settings`、`reference`、`reference_audit`、`seed_census`、case 順の `selection_recoveries` 4 個を与える。
MC entry は `root`、`proof`、`verification`、`terminal`、`submission_output` を持つ。
BAR entry は `case`、`root`、`proof`、`verification`、`transfer`、`terminal` を持ち、case0〜3 の順に全件を与える。
`proof` は MC の `local_verification.json` または BAR の `independent_payload_verification.json`、`verification` は MC の `benchmark_verification.json` または BAR の `verification.json` を指す。
BAR の `transfer` は `transfer_verification.json` を指す。
元 root の全 files と accepted `verification.file_sha256` 表を結び、task marker を自己再hashしただけでは受理しない。

MC `local_verification.submission_sha256=56c9…` は保存 qsub stdout の bytes を指す。
由来は `data_tile_validation_2026-10-17/mc_timing_main_collect_v1.py` 142 行で、同 64 行では stdout JSON と実 ledger の一致を検証している。
保存 stdout の SHA256 は `56c9fb0cab8f52e55b8d117663e015e8619af072b592bb241e2ff5ce1adf9758`、実 ledger bytes は `6a7d9f948a15fe13d6a51aab1e62dcc57edf5ee0ab2aa383bce35189309b37b6` であり、JSON 内容は同じである。
adapter は stdout pin→JSON ledger と accepted inventory→ledger bytes の両経路を確認する。
collector の SHA256 は `153681620d886a1b205289851d89db4ec2bc02abbb29e6eac2d15f325f222f02` で、既存 proof は変更していない。

配置済み smoke config は field と既存 pin の実例だが、残り 3 root を置き換えず正式 config として流用しない。
`data_tile_validation_2026-10-17/timing_report_formal_config_template_v2.json` は未取得 field を null にした実行不能の template である。
残り 3 case の独立回収完了後、別の新しい request root に全 pin・実 root を埋めた config を保存する。
元 root の内容が回収時と同じ不変 snapshot であることを前提にし、controller がまだ書き込む root を固定済みとしない。

## metadata prepare と PBS 実行

以下は実行手順であり、本書の保存時点では正式 prepare・正式集計・qsub は未実施である。
まず v2 の Python と source を指定し、metadata-only の `inputs` で MC と全 4 BAR の state が `complete_candidate` であることを確認してから fresh plan を作る。
`complete_candidate` は全 artifact 監査の成功を意味せず、重い最終照合は compute node 上の `run` が行う。

```bash
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH=/home/user/workspace/mcmc4qec/20261018-tile-timing-report-v2/src:/home/user/workspace/mcmc4qec/20261018-tile-timing-report-v2/cluster_scripts
PY=/home/user/workspace/mcmc4qec/20261017-tile-production-v1/venv/bin/python
```

metadata gate は次の Python code とし、`CONFIG` と `PLAN` は新 request root 内の絶対 path を指定する。

```python
import json
from pathlib import Path
import tile_timing_evaluation_report as r
config = json.loads(Path(CONFIG).read_bytes())
proof = r.Evidence()
snapshots = r.inputs(config, proof)[3]
assert snapshots["mc"]["state"] == "complete_candidate"
assert all(row["state"] == "complete_candidate" for row in snapshots["bar"])
proof.finish()
r.prepare(CONFIG, PLAN)
```

正式 job は親指定の保守的 ceiling を 1 node・1 CPU・16 GiB・2 時間とするが、これは実測した完了時間の保証ではない。
追加 capacity 計測は行わない。
親担当が既存の共通 lock、controller 非競合、queued を含む最大 2 nodes を確認し、固定 script・plan hash・submit intent を保存して一度だけ `qsub` を使う。
qsub の応答が曖昧なら再投入せず、受理 job の照合へ戻る。
script は上記固定環境を設定し、PBS_JOBID の存在と新しい execution reservation を確認してから次を実行する。

```bash
"$PY" /home/user/workspace/mcmc4qec/20261018-tile-timing-report-v2/cluster_scripts/tile_timing_evaluation_report.py run --plan "$PLAN" --output-root "$NEW_OUTPUT_ROOT"
```

`NEW_OUTPUT_ROOT` は全入力 root と重ならず、既存 output がない排他的な新 directory とする。
成功 report 公開前に、全 accepted file の hash・解決先、全 task/file census、source closure 集合、runtime を再確認する。
途中の改変・追加 task・source 追加を検出した場合、成功 report を作らず `validation_failure.json` を保持する。
完了後は親担当が report job 自身の正式 PBS terminal、実 script/intent、report と日本語表の hash を回収し、input/source pin と照合する。
adapter の `report_pbs_job_id` だけでその job の正常終端を証明したとは扱わない。

`output/prepare_final_timing_report_v1.py` は上記 metadata gate と fresh request 作成をまとめた準備 helper であり、qsub を呼ばない。
Linux 上で `prepare --bundle <v2 bundle> --config <全pinを埋めたconfig> --root <新request root>` を実行すると、config/plan/ready、固定 `report.sh`、計算node用 `execution_driver.py`、親投入用 `preparation.json` を作る。
template_only が残る config と、4 case のいずれかが complete_candidate でない入力は拒否する。
親は `preparation.json` の command/resource/manifest/script hash をそのまま submit intent と receipt に保持し、`submission_intent.json` と job_id を追加した `submission.json` を保存する。
compute wrapper は実 PBS_JOBID、親 receipt、ready/driver/config/plan/script hash を照合し、排他的 execution intent と完了 record を保存する。
最適化された Python は明示拒否し、assert を無効化して gate を通過できないようにする。
project module を import する前に、固定 v2 acceptance manifest の hash、全 bundle input/source census、固定 plan の metadata/source hash・解決先を stdlib だけで検査する。
成功 completion 前にも ready/driver/config/plan/script/親 intent/ledger と全 bundle input を照合し、変更時は失敗 completion を残す。
この helper の正式 prepare と compute execute は本書保存時点では未実施であり、全 4 case 完了証跡が揃った後に別 request root で確認する。
最終 helper SHA256 は `ccc8ff5227b19ae982cc9ed8de403aed1d78239f2f45f9f0ce6b4478e39be0c9`、小 fixture は 7 passed / 4.93 秒で、独立静的レビューの blocking は解消した。
helper は `/home/user/workspace/mcmc4qec/20261018-tile-timing-report-tools-v1/prepare_final_timing_report_v1.py` に別配置し、科学 bundle v2 は変更していない。
その Linux stdlib/import smoke は 143 files の固定 bytes/target と実 adapter import/runtime を 0.694 秒で確認した。
証跡は `data_tile_validation_2026-10-17/timing_report_request_linux_smoke_v1.json`、独立レビューは同 `timing_report_request_static_review_v1_ja.md` にある。
これは既存 smoke plan の metadata/source 照合だけであり、正式 prepare・正式 compute・全 raw 走査・qsub を実施したものではない。

選択時の flagged=192 と独立 BAR の `not_collected` を混同せず、既存の有限 reference 全域 gate を変更しない。
MC の 4 within・2 above・2 reference_sensitive を固定規則のまま保持し、BAR の結果を見て閾値や seed を変えない。
low-noise 独立計時は別仕様・未完了の目標であり、この main report の完了で代替しない。
