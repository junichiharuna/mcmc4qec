# 初回4時間collectorからtrace監査への接続

対象は初回4時間collectorを明示したC1T1・C1T2・C3T0/T1/T2である。
既存のC1T0復旧authorityと別のpurpose・metadata keyを使用し、旧失敗jobや再試行履歴を作らない。
collectorの固定config、control、ledger、worker開始/完了、summary、封印済みterminal、元sampling証跡、全task indexを照合する。
実qstatでもjob ID、固定script、1 CPU・32 GB・4時間、F・exit 0・run_count 1を要求する。
sealed terminalだけで受理せず、失敗を含む全task/groupのmetadata検査を再実行する。
authority内の全inputはcanonical pathとhashへ結び、検査前後の変更を拒否する。

trace監査と資源計算は元の関数を別namespaceへ結び、明示したcollector evidenceを使用する。
各planとqsub ledgerにはplanned_collection_authorityを保持し、別collector・別source・変更されたauthorityの混在を拒否する。
capacityは既存の8 group、fullは全192 seed・768 groupを対象とし、scopeや判定を縮小しない。
監査の計算本体・group処理・資源推定の関数を変更しない。
監査jobの正常終端でも実行回数1を要求し、監査終了をBAR校正や名目被覆の保証とは扱わない。
別のworker/configと共有lockを通したqsub接続を検証してから実運用し、現行の稼働中処理と公開候補は変更しない。

## 実装・受入・配置

authority、監査/資源backend、qsub接続とworkerを隔離directoryへ実装した。
Windowsは統合51 passed・30.26秒と追加結合2 passed・3.76秒、Linuxは全53 passed・12.61秒だった。
初回にはWindows fixtureの相対path表記と、旧readerの拒否時exception種別を理由に各1件が失敗し、fixtureを実際のPOSIX契約と拒否動作へ合わせた。
本番のpath検査やscopeを緩める変更は行っていない。
失敗ログも保持する。

結合fixtureでは実collector completeと全task index readerからauthorityへ進み、封印後にtaskを欠落させて関連hashを再計算しても拒否することを確認した。
全失敗の768 sample group・192 anchorを保持したcapacity/full planを構成し、監査の計算本体とgroup処理、資源計算が元関数のままであることを確認した。
qsubとqstatはfixtureに置き換えており、本番のcollector完了やtrace監査成功を示す試験ではない。

別配置 `/home/user/workspace/mcmc4qec/20261020-planned-trace-execution-v1` にcontrolと5条件のconfigを固定した。
実元bundleのacceptance manifestと全input、初回collector config/control、元plan・runtime、未使用のcapacity/full出力先を照合した。
[native配置の実記録](data_tile_validation_2026-10-17/planned_trace_execution_native_v1/accepted.json)に実path・hashとPythonを保存した。
本番collectorの完了authority確認、監査plan・preflight・qsub・実行・completeは未実施である。
最終BAR readerへの初回collector authority接続も未完了であり、既存C1T0復旧readerを代用しない。
source・受入ログ・native配置・実config・実機観測を [47ファイルのmanifest](data_tile_validation_2026-10-17/planned_trace_execution_sources_v1/manifest.json) に保存し、SHA-256は `56b2646e229089fde456560a5da524c7d931800042a8ef60da662d08512c4122` である。
この保存で照合したPC回収済み範囲は224群であり、その後Labo batch1の24群も別途照合してhost側の回収は248群となった。
