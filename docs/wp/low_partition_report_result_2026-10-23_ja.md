# 分割集約から最終報告までの接続結果

最終報告に `kind=partition_merge` の証拠を追加し、従来の単一selector実行と区別して受理するようにした。
受入済みbridgeとrunnerのsource SHA256を固定し、実際のmerge job・qsub台帳・terminal・completion・選択結果を再検証する。
報告のselection pinを受理済みmergeと照合し、検証で追跡したhashと解決先を報告のEvidenceに引き継ぐ。
全24組合せ・MC/BARの48行・各192seedと既存の精度評価を維持し、未取得や失敗を成功した部分集合から除外しない。
この経路の検証成功を名目95%被覆の認定とは扱わない。

## 環境の修正と検証

最初のv1は報告用overlayと元merge環境を同じプロセスで検証するため、import元の検査が衝突することを追加レビューで見つけた。
準備PID42364と実行PID21176は、journalがintentと待機観測だけであることを確認して停止した。
停止前にremote準備やqsubは実行していない。
その記録は [stopped-waiters.json](data_tile_validation_2026-10-17/low_partition_report_acceptance_v1/stopped-waiters.json) に残した。

修正版は元merge環境のPython・PYTHONPATHを使う別プロセスでbridge検証を行い、返った証拠を親でも再照合する。
Linuxで報告環境を実際に読み込んだ後、子プロセスが元環境のmodule originとbootstrap検査を通ることを確認した。
既存のWSS生成側 `submission_intent.json` と監査側 `submission-intent.json` の区別は、配備済み報告コードから保持した。
配備版の科学処理に対する変更は、分割証拠の検証とその分岐に限定した。

修正版のWindows試験は証拠15件が5.15秒、既存報告61件が22.10秒、準備と待受22件が1.98秒、jobと待受21件が2.94秒で成功した。
Linux試験は証拠15件が10.31秒、準備17件が0.10秒で成功した。
変更していない報告job helperはLinux16件が0.54秒で成功した。
このhelperの最初のLinux試験はPYTHONPATH指定漏れにより4件失敗・12件成功となり、既存配備物をhash確認した上で記録済み環境による再試験を行った。
最初の失敗記録を残し、helperやjobを作り直す操作は行っていない。
試験には科学計算・PBS応答・子プロセス通信のfixtureを含み、本番merge sealを使った最終報告は未実施である。

## 配備と稼働

環境は `/home/user/workspace/mcmc4qec/20261023-low-partition-report-environment-v2/environment.json` に保存した。
SHA256は `d4baeedf102ed8b3a1ff1423b50f599ac124f6a103b28f6871819e2336fd7f0f` である。
sourceと検証記録は [accepted.json](data_tile_validation_2026-10-17/low_partition_report_acceptance_v2/accepted.json) に保存し、SHA256は `95ad59d367e6835a06b1e4d2a68e0f04818aa4e154999cfc8089647a8dbbcc54` である。

2026年10月23日06:24 JSTに準備PID30784と実行PID47980を起動し、06:25 JSTにcommand line付きで実稼働を確認した。
準備は独立計時の終了、実行は報告入力の完成を待っている。
通常経路が選ばれた場合は分割専用待受が投入せず終了する。
報告jobの投入には既存のqsub・共有lock・最大2要求nodeの制御を使う。
この記録時点では報告jobは未投入であり、実際の最終報告・回収物照合・内容レビューは残る。
samplingやPC解析、既存の通常経路のdriverは変更していない。
