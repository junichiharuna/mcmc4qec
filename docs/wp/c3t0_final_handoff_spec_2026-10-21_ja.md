# C3T0最終設定・qsub・report回収への接続

## 小仕様

受入済み最終準備waiterを独立したnamespaceで読み込み、C3T0のaudit driverと固定hashを追加する。
元の全件転送・full監査・native referenceの照合と、1 thread環境による一度限りのprepareを変更しない。
元sourceと新しい接続sourceの両方を開始intentに固定する。
最終実行driverはC3T0を選択できるようにし、case=3・target_index=0をcollectorへ明示する。
既存qsub wrapperの共有lock・最大2要求ノード・曖昧な応答の保持・実PBS正常終端・13成果物回収を保持する。
稼働中C1T1・C1T2のdriverとsourceは変更しない。
全件回収・full監査・native referenceの前提がそろうまでは、新しい最終設定やqsubを実行しない。

## 受入条件

実C3T0のdistribution・audit開始intentとconfigを操作なしで照合する。
元の不一致拒否・順序・非zero終了後の再試行拒否の受入を維持する。
qsub実行境界とcollector引数をC3T0で検証し、別条件の最終設定を受理しない。
本番の最終設定・qsub・report回収が未実施の間は、その旨を記録する。

## 実施結果

最終準備waiterは元の操作を継承し、C3T0のaudit bindingだけを追加した。
Windowsで22件・1.58秒が成功し、実C3T0の開始intent・条件・元sourceのpinを確認した。
元のready・prepare・操作方法が同じ関数であることも確認した。
sourceと受入記録は [準備waiterのmanifest](data_tile_validation_2026-10-17/c3t0_final_handoff_acceptance_v1/manifest.json) に保存した。
manifest SHA-256は `716b24d1df92a76f6b795b513ec943b3246d592de5df0f4aae1a01ab2de157e7`、waiter SHA-256は `82df76f6ffd0fd6ca6b58d73acbabebaafcdc63ebbd5c46671b5c7b286d7e267` である。

最終実行の接続は元factoryの条件選択をC3T0に対応させ、case・target_indexと準備waiterの固定path/hashを追加した。
Windowsで追加7件と元回帰24件、計31件・0.82秒が成功した。
別条件設定の拒否、元のqsub境界と曖昧性の扱い、case=3・target_index=0による回収呼出を確認した。
sourceと受入記録は [最終実行のmanifest](data_tile_validation_2026-10-17/c3t0_final_execution_acceptance_v1/manifest.json) に保存した。
manifest SHA-256は `5fe34fa70351cddb82f4b590fa1ab44cacf43eb717e5163634d676859848a08d`、driver SHA-256は `838d5902f94a58bb0cb8be9e9f8c9f885e758ed2299fc81670f0b594df0ee609` である。

01:46 JSTに準備waiterのPID8696と最終実行driverのPID30128のlive sessionを確認した。
いずれも前段の完了待ちで、本番の最終設定・qsub・report回収は未実施である。
新しい親driverのLinux単独テストは未実施であり、接続先の元venv・wrapper・collectorのLinux受入と区別する。
