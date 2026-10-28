# 全hash検査を維持する8 CPU合流

wall-only merge v5と既存workerの原本を保持し、別のmerge v6としてbounded bulk hashだけを並列化する。
科学的row・selector・全12条件の実manifest・prepared・runner・元worker evidence pin・失敗判定・分母は変更しない。
v5から許すsource変換を明示し、科学処理を含む残りのbytesが変わっていないことを検証する。

PBSは1ノード・8 CPU・32 GiB・24時間、coordinatorは1 process、hashは8 threads、未完了taskは最大16件とする。
24時間は実行予測ではなく資源上限であり、32 GiBの十分性も保証しない。
実qstatで現在のjob ID・run_count・要求select・walltime・実hostを確認してからpoolを生成する。
元のmerge runnerによるprepared・script・start evidence照合を迂回しない。

Proof.readは逐次のままにし、元のsnapshotのstat・resolve・hash・再stat・再resolveを保持する。
worker入力、worker finish、合流へのacceptance登録、fragment登録、最終finishを元の順序とbarrierで実行する。
辞書登録はcoordinatorが元の順に行い、成功時の元入力pathごとの検査回数を削減しない。
workerごとの入力参照数の和をS、合流後の一意入力数をUとした元入力集合について4*S+Uと各phaseの実測回数を旧版と比較する。
追加helperのsource hash検査は別の運用証拠として数え、元入力検査が減っていないことと区別する。

各workerはそのworkerの元evidence pinで検証し、並列validator自身のpinを元workerの実行sourceに見せかけない。
追加provenanceはselectionの科学的rowsとは分離したresultのtop-level fieldへ保存し、通常のresult sealで結び付ける。
成功時の全24 rows・calibration binding・worker acceptance、元入力path×phaseのhash回数、登録順、phase完了、guard前にpoolを開始しないことを受入で比較する。
受入は実8 CPUのqsubと既存physical-node gateを使い、PC上ではテストを実行しない。
本番flowへの適用は受入後に行い、稼働中のconfigや既存結果を上書きしない。

## 受入結果

qsub job 265608は正常終了し、9件の統合受入が17.64秒で成功した。
実8 CPU・32 GiBのallocation guardを確認してから、人工保存値を使った旧版・新版の比較を行った。
全24 rows・calibration binding・12 worker acceptanceは一致し、12条件で共有する入力を含む13個のraw fixture pathについてphase別回数が一致した。
このfixtureのSは24、Uは13であり、実測合計は4*S+U=109だった。
49 phaseの順序・完了barrier・登録順と、7種類の不正allocationでpoolを作らないことを確認した。
追加sourceのhash検査は上のraw入力回数に含めていない。

qsub job 265609は正常終了し、本番配置したexecution runnerの実CLI・sys.path・import origin・native bootstrap・現行manifest・8 CPU実行変換を確認した。
allocation guard後に行った並列処理は2件のmetadataを使う入力検査とfinishだけであり、本番worker値やraw traceを読み込む合流ではない。
CLI子プロセスのtimeoutは180秒である。
要求walltime 24時間はguard契約を満たすための上限であり、実際の計算所要時間の予測ではない。

合格時と同一bytesのmerge helperと、受入済みadapterによる8 CPU execution contract・runnerを新しい名前空間へ配置した。
最初のdeployment記録を変更せず、native受入のpinを付けた別のproduction-ready記録を作成した。
受入証跡は[統合受入](data_tile_validation_2026-10-17/parallel_hash_merge_acceptance_20261025_v1/receipt.json)と[実CLI native受入](data_tile_validation_2026-10-17/parallel_merge_cli_native_20261025_v1/receipt.json)に保存した。
本番合流と全12worker終端後のunbound merge jobのadmissionは未実施である。
下流reportが旧merge runnerのpinを固定している点は別の運用互換修正を要し、この合流受入だけで最終reportまでの完了を主張しない。
