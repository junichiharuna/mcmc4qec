# 移設後の投入・終了照合の小仕様

既存 `tile_low_noise_staging.py` の Linux 配置済み freeze と v11 は変更しない。
新しい `tile_low_noise_staging_control.py` は、移設済み単一 PBS 計算の analysis 全 partition と trace audit の実投入・終了証拠を接続する。
科学条件・worker 数・元の資源計画は変更せず、既存 `budget_resources` による追加 I/O 見積もりだけを実 PBS 要求へ反映する。
qsub は親のみが共有 lock・controller 不在・queued を含め最大 2 nodes・一回投入契約の下で行い、この module 自体は qsub を呼ばない。

| 対象 | 証拠と担当 gate | 失敗の扱い |
|---|---|---|
| 元 sampling と copy | 既存 `read_staged_provenance` / `read_staged` による元絶対 path、全分母、copy 自身の receipt/script/PBS F0、source/native、seal | 完了済み recorded sampling failure を保持し、元 root は不変 |
| 投入直前 | 新 `pre_submit` が親の prepared SHA pin、実 script/argv、追加予算を含む resource、固定 scientific metadata、source/runtime と現在の staging metadata を再照合 | intent/receipt/compute marker 既存時は自動再投入不可 |
| analysis 各 partition | 新 `compute` が現在の実 PBS resource/host/run_count と receipt を確認し、旧 runner を full reader の前後 gate 内で実行 | 既存 rows の未取得区間・診断未定義・sampling failure は分母に保持し、途中例外は完了としない |
| trace audit capacity/full | 新 `compute` が同じ PBS gate と full reader、旧 audit runner の全 records、native/summary を結合 | 全予定 groups と tasks を記録した audit failure は `complete_recorded_failure` として保持し、成功監査とは区別 |
| 外部の終端確認 | 新 `read_completion` が親保存 receipt SHA と prepared SHA、実 PBS F/exit/run_count/Resource_List/Submit_arguments/host、compute 完了 marker を照合 | compute 内 marker だけで PBS 終了とは認定せず、未完了・非正常中断・事後 hash 不一致は拒否 |
| 最終 collection | 全 partition と full audit の外部終端 gate を通した上で、compute 内で旧 full audited collection を実行し前後の seal/PBS metadata を再照合 | recorded audit failure の記録は返せるが successful audited collection は拒否し、失敗条件を黙って除外しない |

prepared record と script は新規専用 root の既存互換 filename `partition.sh` / `trace-audit.sh` に排他的に生成する。
実 argv はこの新 module の `compute --plan <control-plan>` を指し、旧 runner を直接投入したかのような receipt を作らない。
親は prepared SHA と実 `submission.json` の SHA を別の保存証拠として保持し、終端 reader に明示的に渡す。
receipt は prepared record に実 job ID だけを追加し、submission-intent は prepared record と一致させる。
source/runtime/native/Python は prepare・投入前・compute 前後・終端で照合し、読み取った JSON の digest は実際に消費した bytes から計算して終端で再照合する。
実 resource は 1 node、96 CPU、指定 GiB と walltime の等価表記を厳格に確認し、run_count は 1 を要求する。
compute は前後 full reader を各 1 回だけ呼び、合計 4 raw hash passes として既存資源見積もりに一致させる。
旧 runner が例外を出しても後段 full gate を試み、全 records が揃った既定の audit failure だけを完了済み失敗として保存する。
前後 gate の失敗は診断として残せるが完了 marker は作らない。
login の投入前・終端 reader は固定 metadata のみを読み、全 raw 走査は PBS compute でのみ行う。
旧 full audit の `measured_capacity` は元 raw を再走査するため login の確認経路では呼ばない。
full audit の計画と資源は、親が固定した capacity prepared/receipt SHA、capacity control 完了 marker、実 PBS F0、全 group/task を含む保存 summary に結合して、既存の純関数 `resource_plan` で再構成する。
capacity compute は元 runner の全入力検査と前後 full gate を終えた場合だけ marker を保存し、現在の原本 raw は後段 compute の full gate で検証する。
`prepare_audit_full` はこの metadata 経路で worker 数を選んでから新規 plan を作り、既存 plan を書き換えない。
受入は小さな metadata fixture と実 script/argv/PBS resource 照合、元 reader 境界、全 partition census、欠落・変更・異常終了・失敗分母、compute 前後 gate の呼出数を確認する。
本番 qsub・原本 raw 走査・本番 copy はこの実装検証では行わない。
