# 分割BAR解析のPBS集約

## 目的と範囲

完了した全BAR partitionを、凍結済みのtile_low_noise_partitioned_analysis.collectで集約する。
科学計算の定義・seed・分母・既定値は変更しない。
正式なWSS比較では既存final v3のpartitioned readerとsource relocation検証を使用する。
集約だけでtrace全体の再監査や名目95%被覆の保証が済んだとは扱わない。

## 入力の受入条件

元のanalysis requestと外部prepared SHA、計画順の全partitionの外部completion SHA・受理内容を入力とする。
analysis prepared・sampling collector・同条件capacity・source/nativeの結合を既存analysis_bindingで確認する。
各completionのscope、partition番号、prepared SHA、全metadata hash、summary hash、groupとrow件数を確認する。
実PBSがF・exit0・run_count1であり、脚本と資源が準備時に一致することを確認する。
既存partition_evidenceを用いて実台帳・終端・native・summaryを照合する。
全partitionのgroup集合が計画と一致し、重複なしで768 group・67584行を持つことを要求する。
入力・source・上流PBSを読み取り前後で照合し、変更があれば受理しない。

## 準備と実行

新しいanalysis-collection-submissionにworker・control・PBS脚本・preparedを排他的に保存する。
資源はserialの1 CPU・1 worker・32 GiB・24時間を初期上限とし、所要時間予測とは扱わない。
集約はgroupごとに読み込むため全groupを同時に保持せず、実測時間と最大RSSを保存する。
prepareはqsubを呼ばない。
prepareは既存analysis completionの全入力と、凍結bundleのacceptance manifest・全source・native binary・Pythonをcontrolへ固定する。
workerは既知SHAの実装だけを新しい出力先へ書き込み、controlと脚本を生成後にbash -nを通す。
実submissionに使うprepared.jsonと、元のrequest・上流証拠・生成物hashを持つparent-prepared.jsonを区別して保存する。
生成前後で全入力・source・PBS終端を確認し、途中変更があれば成功したparent-preparedを残さない。
executeは共有lock、旧controller停止、待機中を含む最大2ノードを確認してqsubを一度だけ呼ぶ。
qsub入口は外部parent-prepared SHAで元request・scope・生成物を照合し、同じcontrolから再構成した脚本との一致を要求する。
共有lockの所有者はroot・phase=bar_collection・pidで固定し、他処理のlockを消さない。
submission intentとguard intentを保存する前後で入力・source/native・旧controller・node予算を再確認する。
qsub呼出し後に応答が失われた場合やjob IDが不明な場合は、lockと曖昧な応答記録を保持する。
preflightはqsubを呼ばず、空き枠の有無だけを返す。
曖昧な応答・途中変更・既存出力は記録を保持し自動再試行しない。
workerは入力hashと実submissionのPBS_JOBID・脚本を確認してから科学moduleをimportする。
既存collectで全group payloadを検証し、集約後にも固定入力を照合する。
親側完了受理は実PBS終端・台帳・summary・worker完了を結合する。
完了受理では実PBSのF・exit0・run_count1・脚本・資源・実hostを照合し、worker intentが固定controlの全入力と実submissionを参照していることを確認する。
summaryの全partition hash・768 group・67584行と、区間未取得・診断未定義・flag・sampling失敗の件数を保持する。
大きなrows.jsonlは親側で再走査せず、workerのhash証拠とファイルの存在・stat前後一致を記録し、親によるpayload再hashではないと明示する。
rowsとraw group・trace・anchorの内容照合は後続final v3のPBS readerで実施する。
最終比較用producer_completionには既存partition-collection/summary.jsonを使用し、独自worker計測は別証拠とする。

## 受入テスト

合成fixtureで正常系、partition欠落・重複・順序違い、scope不一致、件数不一致、hash差異、稼働中・失敗・再実行PBS、入力途中変更を検証する。
workerは実job不一致・source差異・既存出力・途中変更を拒否し、元のcollectorの結果と計測を保存することを検証する。
合成テストの成功を実科学データの集約成功とは扱わない。
