# 保存済み混合診断の計時とクラスタ実行

既存の `tile_mixing_inventory.py` と科学計画を変更せず、追加runnerで容量計測と全件一覧を実行する。
各caseの固定先頭group `(case,0,0,0)` を容量計測に用い、成功した最終再集計のaudited report、元のpath、archive verification、manifest/context、sourceを保持する。
準備では保存済み最終再集計の成功summary、submission、intent、audited phaseのmeasurement/output、PBSのF/exit0とSubmit_argumentsを結合する。
全raw payloadの走査は準備時に行わない。
容量計測は元の予定768 groupの集合を確認した上で先頭1 groupだけJSON/markerを読み、既存inventory_group、_addとJSONL書込みを実行し、入力hashを終端で再照合する。
容量出力は部分計測であり、192 replicateの科学要約を作らない。
容量jobは1 node、1 CPU、4 GB、30分という未測定の上限とする。
full資源は同caseで成功した容量jobの実測wall秒を768倍し、安全係数2と600秒を加えて30分単位に切り上げ、最小30分とする。
記憶量は容量計測RSSの2倍に1 GBを加えてGB単位に切り上げ、最小4 GBとする。
24時間または340 GBを超える予測は拒否し、完了保証とは扱わない。
容量測定には計画とsource/inputの検証時間も含めるため、単純外挿は保守的であり、共有filesystemの競合やcache効果は未同定である。
fullは既存inventory.runを呼び、全768 groupと全192 replicateの分母を維持する。
wrapperの実測は別summaryに記録し、既存inventoryの歴史的な未測定警告を書き換えない。
新規rootを排他作成し、submission/execution intent、script、manifest、入力/source hash、CPU/wall/RSS、PBS job IDと終端照合を保存する。
失敗時は失敗summaryを保存し、上書き・自動再投入をしない。
qsub直前に共有lock、coordinator不在、queuedを含む全体2 node上限を確認する。
PBS応答不明時はintentとlockを保持する。
既存v10 bundleは変更せず、追加bundleに同一byteの依存sourceと新runnerを配置する。
受入は小fixtureで固定先頭identity、artifact/hash不一致、部分分母、full delegation、非有限/負資源、上限、source/input終端変化、PBS binding、排他と2 node制限を確認する。
本仕様は新たな混合や被覆の科学的保証を追加しない。
