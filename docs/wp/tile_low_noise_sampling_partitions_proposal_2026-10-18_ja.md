# 低ノイズ sampling 分割の仕様案と受入要件

本書は実装前の案であり、既存 source、bundle、manifest、計算条件を変更せず、qsub も行わない。
対象は既定の 4 case × 3 target と各 192 replicate であり、新条件や seed を追加しない。
科学的な数値処理と task artifact の形式を維持し、実行単位と複数 PBS job の証拠を追加する。

## 1. 分割が必要になった根拠

capacity-0-0 の job 265235.node-PRISM は F / exit 0 で、sampling 80 task と anchor 2 task が全て成功した。
記録は [回収・照合結果](data_tile_validation_2026-10-17/low_sampling_capacity_0_0_terminal_v1.json) と同名 `_files/` にある。
sampling phase は 35.81106254 秒、最長 worker は 34.17394052 秒、最大 RSS は 122.7266 MiB だった。
anchor phase は 8.33526555 秒、最長 worker は 6.77535623 秒、最大 RSS は 90.7891 MiB だった。
既存 `submit_tile_low_noise.measured_capacity` は `resource_plan` で上限超過として拒否した。
その拒否は native/payload 検証より先に発生するため、拒否例外を捕まえただけでは検証済 capacity として使用できない。
同じ固定式の補助算術では sampling 55005.7920599 秒、anchor 800.1854926 秒、要求 113400 秒（31時間30分）・32 GiB となり、超えたのは時間上限である。
これらは拒否した関数の返り値ではなく、回収値から再現した補助算術である。
既存の短い capacity は将来の完了時間、混合、収束、精度を保証しない。

## 2. 不変条件と分割単位

新規 production root の `manifest.json` は凍結済 `tile_low_noise_study.make_plan(case,target,capacity=False)` と完全一致させ、source/runtime/native digest を変えない。
新 bundle は旧 core と sampling driver を byte 単位で継承し、追加 module だけを別の hash 集合で固定する。
stage は sampling 151、anchor 152、analysis 153 のままで、capacity の 150/154/155 を production に混ぜない。
task は `(case,target,kernel,initialization,replicate,rung,chain)` の元 7 座標を維持する。
partition index、job ID、worker 数、実行順を seed、初期 logical basis、logical combination、decoder prior に入れない。
burn、trace 長、chain 数、ladder、bootstrap、誤差法、保存 checkpoint、失敗定義を変えない。

sampling の最小分割単位は replicate 一つとし、その replicate の全 kernel × initialization × rung × chain を一つの partition に含める。
これにより各 BAR group の trace を複数 partition に分けず、全 768 group を維持する。
各 partition の replicate 集合を事前固定の連続区間とし、全 0..191 を重複なく一度ずつ覆う。
anchor は各 replicate につき元の 1 task だけを生成し、kernel/init/ladder/誤差設定を通じて同じ artifact を参照する。
anchor phase は sampling と別に分割し、1 job で収まれば全 192 task を一つの anchor partition に入れる。
anchor phase 自体が上限を超える場合も replicate 区間でのみ分割し、anchor の再生成・再平均・partition ごとの複製を行わない。
sampling と anchor は独立に実行できるが、後処理の開始は両方の全 task collection 完了後に限る。

## 3. 資源計画

新 capacity 証拠 validator は、元 capacity plan、全予定 task、各実 artifact/marker/hash、実 RNG・prior・configuration、summary、native、intent、submission script、PBS F/exit0 を検証する。
既存 `measured_capacity` の上限拒否を検証成功として流用せず、その検証節を忠実に移した独立 reader を小さい受入で照合する。
検証と allocation は分離し、上限超過しても検証済 measurement は失われない API とする。
別 case、target、source、runtime、seed stage の capacity を流用しない。

phase ごとに最大 RSS から 1..96 workers の最大安全候補を選び、要求 memory を `max(32,ceil(1.5*workers*peak_MiB/1024+8))` GiB とする。
workers=1 でも 340 GiB を超える場合は計画不能として停止する。
capacity は 96 workers で測定されているため、workers を減らす場合は時間外挿に `96/workers` を掛け、低並列で速くなると仮定しない。
phase 内の `k=1..192` の順に、`[floor(i*192/k),floor((i+1)*192/k))` を partition `i` の区間とする候補を調べる。
各 partition の予測は、元式の phase elapsed による task 数比の外挿、各 kernel/init/rung の最長 task を割り当て数だけ足して workers で割った値、割当内最長 task の最大値を用いる。
anchor は元の 1 task/replicate と対応する phase measurement を用いる。
要求時間は元と同じ `1800*ceil((2*predicted_seconds+600)/1800)` 秒とし、全 partition が 24 時間以下となる最小 k を採用する。
1 replicate 単位でも収まらない場合は自動で chain/trace/replicate を減らさず、実行不能を記録する。
96 CPU を要求し、worker 数、memory、walltime、partition の task 集合 digest を計画に固定する。
queued を含め最大 2 nodes と共有 submission lock を維持する。

0-0 の補助値にこの規則を適用すると、sampling は 96 replicate × 2 partition の候補で各 61440 task・384 BAR group、各 15時間30分・32 GiB となる。
anchor は 192 task の 1 partition、1時間・32 GiB の候補となる。
これは仕様案の補助算術であり、新 validator/resource planner の受入・実装・実測済み allocation ではない。
追加の job 起動・I/O 競合・ファイル数の影響を含む完了保証はない。

## 4. Artifact と実行証拠

canonical artifact は新 production root の元パス `traces/<task>.{json,npz,done.json}` と `anchors/<task>.{json,npz,done.json}` に保存する。
identity は元の `manifest digest + task` のままとし、低層 worker は `sample_task` / `anchor_task` を変更せず呼ぶ。
wrapper は呼ぶ前に自分の全予定 task のファイル不存在を確認し、元 worker の cache-return が新しい資源計測や再実行にならないようにする。
partition manifest と `sampling-partitions/<phase>/<index>/` に各 job の intent、native、summary、task marker map、time/RSS を保存する。
submission evidence は別の `sampling-submissions/<phase>/<index>/` に置き、実行先の存在 guard と衝突させない。
重複 partition の並行実行を exclusive intent で止め、全 partition 間の task 集合が disjoint であることを事前・終端で検証する。
元単一 phase runner との衝突防止には各 phase の既存パス `{phase}-execution-intent.json` へ `mode=partitioned` の routing reservation を排他作成し、そこに PBS job ID を捏造しない。
reservation は partition manifest digest と phase を持ち、実 job の intent は `sampling-partitions/<phase>/<index>/execution-intent.json` のみへ置く。
旧単一 phase reader がこの reservation を拒否し、旧 `run_phase` も同 intent の排他作成で停止して native/artifact を生成しないことを受入で確認する。

各 job は現在の source/runtime/native を検査し、自身の実 PBS job ID・hostname・固定資源・script とその partition を結ぶ。
partition ごとの wall/CPU/RSS、全 partition の task CPU 合計、最初の開始から最後の終了までの全体経過時間を区別し、並列 job の wall の和を実経過時間や速度改善として報告しない。
各 task の実際の結果 `ok/failed` を保存し、recorded failure であっても全 task の artifact と summary を出す。
全 task が記録され、失敗 task がある場合は、成功 job と区別した既知の非 zero 終端を wrapper が記録する。
collect は単に F/exit0 だけで task を選別せず、既知の recorded-task-failure 終端は全分母に残す。
欠損 artifact、kill、worker pool crash、hash mismatch、出力欠損、未終端 job を recorded sampling failure に変換しない。
それらは collection 不完了として停止し、予定・観測・欠損 task 数と全既存 outcome を残す。
同 root の自動再実行、seed 交換、失敗 partition の除外はしない。

## 5. 複数 job 証拠と後続互換の境界

`tile_low_noise_analysis.completed_phase_evidence` は単一の phase intent と native の PBS ID を要求する。
`tile_low_noise_trace_audit_run.sampling_snapshot`、同 `prepare/read_plan/run`、trace audit submitter の `checked_plan` もこの単一 job 契約へ依存する。
`tile_low_noise_analysis_partitions.create_plan/read_plan/run_partition/collect/read_collection` と `tile_low_noise_audited_collection.read_audited_collection`、既存 summary/reference CLI も間接的に同じ契約へ依存する。
したがって sampling を分割しただけでは、これらの旧 CLI をそのまま本番入口として使えない。
collector の job を sampling 全件の生成 job に見せたり、最初の partition の native を全件の native とみなしたり、PBS ID を空で埋めたりしない。
旧 module の monkeypatch、plan/source hash の差し替え、native gate の回避は行わない。

追加する明示 reader は `mode=partitioned_sampling` と各 phase の全 partition manifest・実 PBS receipt・native digest・task所有権を持つ collection を検証する。
返す completed evidence は各 phase の全 `tasks/failed` と、元 worker が要求する sample の `group_record_digests`、anchor の `record_digests` を含める。
sample の group digest は元 `analyze_group` と同じく、各 raw record の `task/status/wall_seconds/cpu_seconds/peak_rss_mb` の 5 項目に縮約し、`(rung,chain)` 順に並べた list から再生成する。
anchor の digest は対応する raw record 全体から再生成し、いずれも失敗や未定義を除外しない。
collection の mode、partition receipt、追加 reader source hash も analysis context に含め、旧単一 job の context とは異なる digest にする。
新 reader/wrapper の全 source closure と全 partition receipt digest は BAR context だけでなく trace audit plan と最終 collection evidence にも結び、途中で provenance 検査実装が変わった結果を混ぜない。
全 task payload/hash の完了確認を含む collect は qsub で実行し、prepare の login metadata 検査に押し込めない。

|後続処理|そのまま再利用する処理|必要な新入口|
|---|---|---|
|BAR|`analysis_context/validate_context`、`load_group/validate_record`、`analyze_group/analyze_arrays`、stage153 bootstrap|複数job completed evidence を検査する analysis plan/run wrapper|
|BAR partition集計|`validate_partitions/validate_rows/read_group/partition_evidence/validated_groups`、全分母counter|旧 `read_plan` に戻らない新 create/read/run/collect/read_collection|
|trace audit|`make_plan/groups/run_group/verify_group_inputs`、`audit_task`、実native検査|新 sampling snapshot と全元job集合を検査する prepare/read/run/submit入口|
|trace audit資源|既存 `resource_plan` の数式|新 snapshot を検査する measured reader、上限超過時の明示停止|
|最終 audited collection|`Evidence` と `verify_group`、既存 anchor/marker/full-cohort検査|新 BAR collection/new audit read_plan を使い、全sampling job証拠を再照合する最終reader|
|低ノイズsummary/WSS比較|`summarize_rows`、`compare_rows`、既存 bounded reference監査|新最終readerから受け取る read-only rows と evidence を結合する入口|

上表の再利用関数は新 wrapper が検証した値を引数で渡して呼び、旧 provenance 入口を動的に差し替えない。
実装時に再利用関数が旧 reader を内部で呼ぶことが分かった場合、その入口は再利用せず、新 wrapper で同じ検査を明示して受入する。
full trace audit の capacity は production の replicate 0/1 の全 rung・全 chain を用い、one-chain sampling capacity で代用しない。
sampling capacity を科学的入力や full BAR group の代用品にしない。
BAR 資源は既存の全次元 synthetic analysis profile、trace audit 資源は既存の全次元 production audit capacity と別々に検証する。
後続の資源上限が再び超過した場合も sampling 分割だけで解決したとせず、その phase を停止して別計画を作る。

## 6. 小さい受入要件

1. 全 12 条件について task enumeration の union が元 `tasks(plan,phase)` と完全一致し、重複・欠損・余分な task がない。
2. 全 production task の seed 入力座標、初期化 index、stage、rung p、固定 decoder prior が partition 前後で一致する。
実際の seed 値と初期状態は四 case・三 target・各 kernel/init/境界 rep/chain を含む事前固定の有界 witness で確認し、重い全 seed RNG 生成を軽量受入に押し込めない。
3. 0-0 の回収済 measurement と元式の単一job補助値を再現し、新規候補 2 sampling + 1 anchor、各上限と task 数を再現する。
4. capacity の raw/native/source/PBS/seed/config の各改変、別target混入、成功数不足、RSS/時間未定義を allocation 前に拒否する。
5. 上限ぎりぎり・端数区間・memory減workers・1repでも超過を列挙可能 fixture で検査し、予算超過を暗黙の条件縮小で回避しない。
6. 軽い実 code/noise fixture の同taskを別rootの直列・分割・異なるworker順で実行し、非決定的な時刻/RSSを除いた seed、初期状態、全compact/checkpoint、失敗判定が一致する。
7. anchor は各rep一回で、4 kernel/init group と全 window/ladder が同じ anchor marker/hash を参照する。
8. 初回実行・重複投入・部分artifact・cache-return・同root再実行・曖昧qsub応答・既存lock・controller稼働・queued込み2node上限を mocked scheduler で検査する。
9. 正常task、記録されたsampling/anchor failure、zero-failure anchor、missing artifact、worker crashを分け、全192分母と未完了状態を保つ。
10. 各partition PBS/native/intent/script/source/marker とtask所有権を照合し、別partition receipt、native取り違え、先に完了した入力の終端改変を拒否する。
11. 旧単一job completed reader が partition routing reservation を拒否し、新readerが架空の単一PBS証拠を拒否する。
12. 新completed evidence→元 `analyze_group`→新BAR collect→新full trace audit→新audited collection を短い fixture で接続し、全768 group の小さなcontractfixtureと実四caseの短traceの役割を分ける。
13. 旧単一phase fixture と新分割fixtureで数値 helper の出力が一致し、provenance/context digestだけが分割証拠に応じて変わることを検査する。
14. source・receipt・途中output変化と診断未定義・区間未取得を保存し、終了済みsubsetだけで完了・精度・coverageを宣言しない。
15. 新summary/WSS入口は既存の純粋関数へ全予定rowsを渡し、partial WSS をfull point referenceとして使わない。

1 test file は 60 秒以内で、重い full sampling や sweep を受入に含めない。
実装順は capacity証拠readerとpartition planner、sampling runner/submitter、collection/provenance reader、後続の各明示入口、統合受入とする。
後続の明示入口と統合受入が完成する前に sampling production を投入しない。
本案の独立レビュー後に、小仕様を固定して受入テスト・実装へ進む。
