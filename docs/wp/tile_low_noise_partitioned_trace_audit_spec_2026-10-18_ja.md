# 分割 sampling の trace audit 入口

既存の数値監査と資源式を維持し、複数 PBS job の生成証拠を明示して検査する新入口を追加する。
担当ファイルは `tile_low_noise_partitioned_trace_audit.py`、`tile_low_noise_partitioned_trace_audit_resources.py`、`submit_tile_low_noise_partitioned_trace_audit.py` と対応する受入テストである。
凍結済み既存ファイルは変更しない。

`completed_partition_evidence(root, sampling)` の `mode=partitioned_sampling`、全 task の分母、sample group record digest、anchor record digest、全 partition receipt・native・source・collection の hash を audit plan に保存する。
sampling snapshot は元 manifest/profile/fixture と、この reader が返す全 root-relative input hash を結合する。
collector 自身は `collector_pbs_job={phase:collect,job_id,exit_status:0}` として生成 partition と区別し、全元 job 検査に含める。
共通 reader が collector の ledger、実 execution/native、source、terminal receipt を検査したことを必須とする。
snapshot は入口と終端で再検査し、追加 reader/submitter/resource の全 source closure を別途結合する。
元 singleton reader、routing reservation の架空 PBS ID、動的 monkeypatch を使用しない。

`read_plan(root, source)` は旧形式と同じ `(audit_plan, sampling_plan)` を返す。
purpose、group、artifact、measurement、summary の形式は旧監査と同じで、plan に `mode=partitioned_sampling` を追加する。
capacity は production replicate 0/1 の全 rung・全 chain、full は全 192 replicate・768 group とする。
`run_group`、`verify_group_inputs`、数値 `audit_task` を既存実装から再利用する。
sampling failure を監査から除外せず、raw artifact 欠損や改変を監査 failure として保持する。
実行は PBS・固定 thread・新 root で行い、全監査前後の入力検査と native gate を維持する。
native gate 前に現在の PBS ID と submission ledger の実 job、script、source closure、package、Python executable、固定資源を照合する。
execution intent に submission、submission intent、script の hash を保存し、run 終端と terminal reader でも再検査する。

資源 reader は旧数値 `resource_plan` を用いるが、新 `read_plan` からのみ入力を取得する。
capacity の全 measurement・group artifact・入力 trace・submission・native と `terminal.json` の F/exit0 を検査する。
`terminal.json` は selected PBS fields を持つ `{Jobs:{job_id:{job_state,Exit_status,Submit_arguments}}}` とする。
script、submission intent、実 execution intent、native の job ID と digest を結合し、terminal だけで成功を宣言しない。
上限を超えた場合は明示停止し、条件や分母を縮小しない。

submitter は既存の共有 lock、controller gate、queued を含む 2 node 制限、qsub 一回・曖昧応答の intent/lock 保持を維持する。
長い検証の間に状態が変化し得るため、controller と node 制限は最初の検査に加え submission intent 直前にも再検査する。
全元 sampling job を検査し、記録された task failure の既知終端を含む全 expected exit status と scheduler の値を照合する。
capacity/full audit の新 script は新入口だけを実行する。
親 agent 以外は qsub しない。

受入は全 source closure、複数 receipt の混入・改変、snapshot の変更、singleton evidence 拒否、旧数値処理の同一性、全分母保持、capacity gate、resource 上限、2 node/lock/qsub ambiguity を小 fixture で調べる。
実数値 fixture と provenance fixture の範囲を分け、1 test file を 60 秒以内とする。
