# case2 target0 コピーの一回投入 wrapper

対象は元 `low-noise-v2/runs/production-2-0`、PBS `265259.node-PRISM` に固定する。
新 root は `staging-control-v2/runs/copy-2-0-v1`、宛先は `low-analysis-v11/runs/staged-production-2-0-v1` とし、他 case/target は受け付けない。
`output/submit_low_noise_staging_copy_2_0_once.py` は既存 deployment・Linux acceptance・元 sampling preparation/親 receipt・controller finished 証拠を外部の固定 SHA から読み取る。
import 前に accepted source/package/Python/native binary を検証し、元 source と v11/v1/control-v2 は変更しない。
初回コピー資源は 1 node・1 CPU・8 GiB・24 時間の未計測 ceiling とし、完了予測や厳密上界とは扱わない。

`--prepare` は元 PBS の終端・run_count・実 resource/元 script/host・全 task summary/native evidence を metadata だけで確認した後に限り、既存 staging helper で新規 plan を作る。
元 PBS が R、summary が欠損、意図しない再実行、未完了の場合は root 作成前に拒否する。
全 task を保存した既定の recorded failure は消さずにコピー対象として保持する。
accepted-inputs.json と stage.sh、copy-readiness.json を排他的に作り、準備済みであることを投入済みとは扱わない。
worker は PBS 内だけで実 resource を確認し、既存 `s.run` に全 raw hash・コピー・終端 hash・seal 作成を委譲する。

親は prepare の readiness bytes を保存し、その SHA を `--readiness-sha256` で明示して `--preflight` または `--execute` を呼ぶ。
preflight は既存 plan/script/inputs、元 sampling metadata、source/runtime/native、controller fixed finished 証拠と実プロセス不在を再照合し、raw は読まない。
execute は workspace 直下の共有 `tile-low-noise-submission.lock` を排他的に取得し、同じ gate と queued を含む現在の全自分ジョブの要求 node 合計を再確認する。
新規 1 node を加えて最大 2 nodes を超える場合は投入しない。
remote submission-intent を fsync してから、固定 command `qsub <control-root>/stage.sh` を一回だけ実行する。
qsub 直前にも source/script/metadata、controller、queue を確認する。
成功 receipt は既存 staging helper と一致する `submission.json = submission-intent + job_id` とし、stdout/stderr/returncode は別の submission-receipt.json に保存する。
非0・不明な stdout・timeout・送信後の例外は曖昧とみなし、intent と共有 lock を残して自動再試行しない。
lock を除く際は取得時 hash と現在の所有を確認し、他者の lock は削除しない。
local でも各 mode の排他的 intent を SSH 前に保存し、remote script/stdout/stderr と wrapper/readiness SHA を保存する。

受入は小さい filesystem/mock PBS に限定し、一回成功、二回目拒否、曖昧応答、queue race、controller 生存、lock 所有変化、source/plan/script 改変、import 前拒否、PBS 未終端で prepare しないことを確認する。
この開発中は実 prepare・コピー・qsub を行わない。

## 正式終端後の手順

1. 既存 watcher で元 PBS 終端と全 sample 61,440 件・anchor 192 件を確認する。
2. 親が wrapper の `--prepare` を明示実行し、元 receipt の JSON 内容と独立 preparation の manifest/script SHA を照合した準備結果を保存する。
3. 保存した readiness ファイルの SHA を固定して `--preflight` を実行し、空き 1 node と controller 不在を確認する。
4. 同じ readiness SHA で親が `--execute` を一回実行し、実 job ID と正式 receipt を保存する。
5. copy 自身の F0 と seal/receipt/hash を別途確認してから、実測コピー時間による I/O 予算を後段に加える。

必要 pins は accepted deployments/acceptance/source map、元 preparation と親 sampling receipt、controller finished/exhaustion、prepare が保存した plan/script/accepted-inputs/readiness、および実投入後の親 receipt である。

親用 command は以下の順とし、`<readiness_sha256>` は prepare stdout の保存 bytes から算出する。
この stdout は remote `copy-readiness.json` と同じ canonical JSON bytes を保存する。

```text
<Python311> output/submit_low_noise_staging_copy_2_0_once.py --prepare
<Python311> output/submit_low_noise_staging_copy_2_0_once.py --preflight --readiness docs/wp/data_tile_validation_2026-10-17/low_noise_staging_copy_2_0_prepare_v1_stdout.txt --readiness-sha256 <readiness_sha256>
<Python311> output/submit_low_noise_staging_copy_2_0_once.py --execute --readiness docs/wp/data_tile_validation_2026-10-17/low_noise_staging_copy_2_0_prepare_v1_stdout.txt --readiness-sha256 <readiness_sha256>
```

現在は全 command 未実施であり、元ジョブの R 状態で `--prepare` を試すことも行わない。
