# 拡張seed全数監査の専用qsub

既存`tile_seed_audit.py`を変更せず、別のplan・submit・run wrapperを設ける。
planは新規run rootだけに作り、bundle内の保存manifest一式から全予定namespaceを再構成する。
production manifestのpackage hash・Python・依存versionと実runtimeを照合し、本校正のcore baselineを使用する。
入力manifest・native fixture/profile・全seed source・実行Python・bundle packageのhashを保存する。

plan時に1000件の実pilotを行い、経過時間・Linux peak RSS・SQLite file sizeを記録する。
時間は全件数への比例外挿の2倍と300秒の余裕が30分以内であることを要求する。
要求は1ノード・1 CPU・30分とし、memoryは測定RSSの1.5倍に1 GiBを加えた値を切り上げ、最低2 GiB、最大4 GiBとする。
SQLiteは逐次処理であるため全件をPythonメモリへ展開せず、diskはpilot file sizeの全件外挿の2倍に1 GiBを加え、最低4 GiBの空きを必要とする。
これらは測定に基づく初回上限であり、完了を保証しない。
時間またはmemoryが上限を超えるときは計画を拒否し、全数実行を自動開始しない。

qsubは既存low-noiseと共通の排他lockを使用し、controller不在とqueuedを含む追加後最大2ノードを確認する。
入力・sourceを再照合し、submission intent保存後に一度だけqsubする。
不明応答・timeout・非零終了後はintentとlockを保持する。
runはPBS・固定thread環境を要求し、execution intentを排他的に保存してから既存auditorの`--full --max-seconds 1800 --output NEW_PATH`を実行する。
既存output・intent・scratchがあれば再実行しない。
終了gateはfull結果の存在、予定件数とchecked件数の一致、complete=true、unexpected_collisions=0、全入力・source・予定namespaceの一致とする。
stage140/141は選択済み計時manifestが未取得なので未監査予約として残し、今回の完了を全goal namespaceの完了とは呼ばない。
受入は小fixtureとmock subprocessを用い、ローカル全数監査・remote配置・qsub実行を行わない。

immutableなproduction baseline bundleで`python cluster_scripts/submit_tile_seed_audit.py plan --bundle BUNDLE --root BUNDLE/runs/seed-audit`を実行する。
同じ引数で`submit`を実行するとdry-runとなり、`submit --execute`だけがqsubを呼ぶ。
`run`は生成PBS scriptからだけ呼ぶ運用とし、手動のローカル全数監査には用いない。
planでLinux RSSが取得できない環境は拒否し、Windows受入のRSS値は明示的fixtureとして扱う。
