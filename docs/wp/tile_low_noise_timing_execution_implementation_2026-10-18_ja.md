# 第3段階の独立計時 runner 実装記録

親承認済み仕様 `tile_low_noise_timing_execution_spec_2026-10-18_ja.md` の SHA256 は `b5fa77d2f8cdeca22fdf31096f0952391ae799c75ea02d0f8e1c48437b8a5ded` であり、承認時の仕様本文を変更していない。
本記録は実装後の状態を追記する文書であり、仕様末尾の「実装未実施」は承認時点の記録である。

新規実装は `cluster_scripts/tile_low_noise_timing_execution.py` と `cluster_scripts/submit_tile_low_noise_timing_execution.py` の二つである。
旧 runner、旧科学関数、stage2、selector、既存 cluster bundle は変更していない。
第2段階の task/seed/registry と、既存の問題構築・logical 初期化・sampling・compact・BAR・anchor 分散関数を直接再利用する。
旧 driver の manifest を差し替えて実行する方式は使っていない。

main は192反復、capacity は2反復・2 workersの full estimator であり、固定prior、fresh anchor、全 burn-in と trace、MC の巨大整数Nを短縮しない。
承認済みの資源式・係数・4例、全24行、192反復の分割和を実装した。
96 CPUへの競合外挿は未検証であり、capacity の実測が完了や精度を保証するものではない。
不可能と判定した main envelope は24行と未実施192反復を保持し、投入しない。

PBS非0終了のcapacityは、現入力・source・native・task provenanceに矛盾がない場合のみ、宣言したcapacity envelopeの失敗として保持する。
この場合の `execution_infeasible_capacity_envelope` は基本的な計算不可能性やtimeout/OOM原因の断定ではない。
実native結果自体が無い場合やprovenance不一致はvalidation failureとして停止する。
pool途中終了時も全予定taskを残し、有効な完了artifactからtask wall/CPUだけ回収して下限を保存する。
戻り値でしか得られないartifactを含むinclusive clockが無ければunknownを維持し、部分平均・速度比を作らない。
未観測taskをnot_startedと断定せず、interrupted・started=unknownとして保持する。

新bundleは新runnerとsubmitterだけを置き、stage2の既存配置先を明示PYTHONPATHで参照する設計である。
実import先の絶対source path/hash、PYTHONPATHの順序、coreの実path/runtime hash、実Python呼出path/hashをsnapshotへ固定する。
共有lock所有token、投入直前の最大2ノード再確認、qsub一回、意図・応答保存、不明応答時のlock保持、実PBS run_count=1・script・資源・hostnameを検査する。
終了時にはnative、現入力/source、全task artifact、scientific summaryと終端結果を再結合する。

正式censusは12descriptorの外部依存であり、本実装は全数censusを生成しない。
`formal_census` は旧completionや部分censusを受け取らず、stage2のnumeric gateに加えてnative・PBS・前後入力source hashを要求する。
selected=0のno-op receiptは正式censusへ変換せず、新timing jobを作らない。
全partitionの科学統合、同精度判定、時間比は第4段階の対象である。

受入は `tests/test_tile_low_noise_timing_execution.py` と `tests/test_tile_low_noise_timing_execution_gate.py` の53件で、Windows Python 3.11で全成功、skipなし、17.49秒だった。
小さい実tile72 bit-flip/depolarizing、固定prior、joint noise、fresh anchor、論理初期係数、cross-chain/block、直列/2 worker、巨大N不短縮、全分母、資源4例、formal gate、native/PBS/source改変、pool中断、二重投入・曖昧qsub・lock所有変更を含む。
PBSとnative execution envelopeはfixtureであり、ローカルでnativeを正式実測した結果とは扱わない。
正式selection、科学manifest、全数census、capacity/main qsub、Linux配置・本番計時は未実施である。
この版は独立レビューへ渡す初版であり、レビュー承認済みとは扱わない。

## 第2版のレビュー対応

初版の独立probeはfinal全0、syndrome範囲外、sector範囲外、weight負float、失敗回収の読取直後改変という5件の誤受理を検出した。
第2版では保存配列のdtype・shape・範囲、final状態のfailure supportとcompact最終値を検査し、回収も同一Evidenceで読取前pinと終了時照合を行う。
終了時のcore aggregate、実import source、PYTHONPATH、Python経路/hashを再検査する。

capacity runは、消費前pinと同じEvidenceから得たexact三重artifact集合を `summary.payload_verification` にmanifest・snapshot・task分母・scope付きで保存する。
成功capacity referenceにはmanifest・summary・submission receiptの外部SHAと正式terminalを必要とする。
`accepted_capacity(reference)` はこの保存された検証証拠をF0・run_count・script・native・現sourceと結合してmetadata-onlyで受理する。
これは現在のraw再監査ではなく、返り値の `payloads_rehashed_now=false` とscopeにその境界を明記する。
main prepare/read_plan/submitはこの入口からpure resource式へ接続し、payloadを読む `completed` を呼ばない。
main computeでは新task開始前にfull `completed` を呼び、実2payloadと保存map・summary・metadataが全て一致しなければ停止する。
prepare後にrawとmarkerの両方を再hashしても、このcompute gateは拒否する。
非0capacityは別途full readerが保存したfailure証拠の外部pinを受理し、unknown費用・未実施192件を残す。
新しい専用PBS job、追加科学capacity、seed、新moduleは追加しない。

capacityの保存対象は全物理trajectoryではなくcompact系列・初期終状態・係数である。
事前設定の最大非圧縮系列量はtile72 bitの2反復で約219.73 MiB、他caseは約21.97 MiBであり、NPZの実圧縮量は未測定である。
full readerはこれらを読み、初期状態を再構築・復号するため、metadata-only準備とcompute再確認を分離した。
第2版の66受入は全成功、skipなしであり、実行秒数・file hashは第2版freeze証拠に保存する。
独立差分レビューと正式配置・計時は引き続き未実施である。

第2版の独立受入は66件成功・17.81秒で、元の5変異probeは全て拒否へ転じた。
追加指摘により、submitterのintent保存後にもlock所有・現plan/source/script/intent・node/controllerを再確認してからqsubを呼ぶ。
intent保存直後のlock/plan/script/intent変更はqsub呼出0回で停止する受入を追加した。
この補強後の作者受入は70件成功で、最終freeze証拠に実行秒数とSHAを保存する。
