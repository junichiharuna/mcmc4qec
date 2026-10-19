# 低ノイズtrace監査の専用qsub

既存runnerの固定capacity 8groupまたはfull 768groupのmanifestを変更せず投入する。
capacityは8worker・1ノード・96 CPU・340 GiB・24時間という初回上限を使い、測定済みとは扱わない。
fullは独立したcapacity rootの完成済み実測証拠から資源を再構成し、保存済みfull planのworker数との完全一致を要求する。
不一致なら新規planが必要であり、submitterは既存manifestを書き換えない。

監査出力rootはbundleのruns配下とし、元sampling rootおよびcapacity rootとは祖先関係を持たない独立した場所に限定する。
manifest・source・package・Python・script・保存native証拠を検査し、出力へのsymlink逸脱を拒否する。
元samplingとanchorのexecution intentをplanに記録したhashと照合し、元jobをqstatで終端Fと確認する。
失敗samplingも監査対象なので、元jobの終了code 0は要求しない。

既存low-noiseと同じ親ディレクトリのsubmission lockを排他的に取得し、稼働coordinatorを拒否し、queuedを含め追加後最大2ノードを守る。
全入力・資源・source・Python・scriptをqsub直前に再照合し、submission intent保存後にqsubを一度だけ呼ぶ。
qsubのtimeout・非零終了・不明job ID・ledger保存失敗ではintentとlockを保持し、自動再投入しない。
intent前の拒否や状態照会失敗はlockだけを解放する。
既存audit・measurements・native preflight・execution intent・summary・submissionがあれば拒否する。

受入はmock qsubと小fixtureでcapacity/full両経路、worker一致、元job終端、共有lock、queued上限、曖昧応答、source変更、path逸脱を検証する。
remote操作と実qsubは受入では実施しない。

CLIは `python cluster_scripts/submit_tile_low_noise_trace_audit.py --bundle BUNDLE --root AUDIT_ROOT --source-root SAMPLING_ROOT` でcapacityのdry-runを作る。
fullでは追加で `--capacity-root CAPACITY_ROOT` を必須とする。
`--execute` を追加した場合だけguardと元jobの終端状態を再確認してqsubを呼ぶ。
submission記録のresource_basisはcapacityならinitial_ceiling、fullならmeasured_capacityとし、全資源証跡をresourceに保存する。
samplingとanchorが同じPBS jobなら、終端照会は1回にまとめる。
元jobがFでも終了codeは強制せず、既存のsampling/native証跡の検査を省略しない。

2026-10-18のWindows Python 3.11受入は33 passed、29.96秒だった。
境界の受入では実際の短いtrace監査と保存済みcapacity artifactを使い、prepare_fullからmeasured_capacity、submit dry-runまでを実経由で確認した。
native環境・PBS識別・時計は明示fixtureであり、本番の資源計測や実qsubではない。
capacity measurementのpayloadを変更するとdry-runが拒否することも確認した。
core環境は依存guardによって1 skipped、0.06秒だった。
Linux受入・remote配置・実qsubはこの時点では未実施である。
