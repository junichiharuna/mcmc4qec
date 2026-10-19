# 主4条件の正式計時報告の監視・回収

既存の科学source、request、閾値、原taskは変更せず、固定job 265277の保存結果だけを回収する。
新規所有fileは `output/collect_main_timing_report_v1.py` と `output/test_collect_main_timing_report_v1.py` と本仕様に限る。
固定accepted readiness 7fda7805…、親qsub stdout 4e3ffa41…、request、manifest、scriptと実receiptを照合する。
監視は約120秒間隔の軽量metadata読取で、qstatの許可fieldだけを保存し、Variable_List等は保存しない。
起動時に実script、1 node・1 CPU・16 GiB・2時間、run_count、親intent/receipt、execution-intent、準備6fileと固定source/runtime入力のhashを照合する。
監視と回収はremote read-onlyで、qsubやprepare、scheduler変更を呼ばない。

回収は実PBSのFを確認してから、6準備file、3投入file、execution-intent、completion、stdout/stderr、results全fileを新規local directoryへ保存する。
成功受理はF/exit0/run_count1、実要求資源・Submit_arguments・実job IDの一致を必須とする。
失敗終端では保存可能な証拠を残し、成功reportへ読み替えない。
sourceとplan input metadataのみ現在hashを照合し、report内の全raw hash表を現在原taskへ再走査しない。
全対象fileはregular非symlinkでrequest内に限定し、census・解決先・bytes hashを取得前後で固定する。
PBS安定fieldも取得前後に照合し、転送後にlocal全file hashを照合する。
completionのwrapper snapshotは、実driverがtrackするready/Python/driver/config/plan・plan入力・bundle manifest全入力・submission/intent/scriptのexact集合として再構築し、欠落・余分なentry・空mapを拒否する。
SSH各attemptはlocal排他directoryにintent・原stdout/stderr bytes・成功/例外receiptを保存し、timeoutや非0でもpartial bytesを捨てず自動再試行しない。
rawログbytesのhashを保持し、表示用sanitized logは別artifactとして保存する。
report hostnameやfresh native probeを保存されていない事実から補完しない。

成功reportはcase順0～3×epsilon 0.2/0.1の8行・各192予定分母、各methodの192観測・status件数・precision metrics分母を保持する。
保存済み有限reference RMSE rangeと分類の整合、両methodの精度gateと全clockのmeanが揃う場合だけ平均MC/BAR比が出る契約を検査する。
これは保存済み集計値の自己整合検査であり、原taskからRMSE・ACF・BAR・decoderを再計算した独立精度検証ではない。
failed/unavailable/区間無しを分母から除かず、selection診断と独立BAR診断未取得を区別する。
元計測の費用、report処理のCPU/wall、PBS経過時間を分離して記録し、低noise計時は未評価のまま保持する。

軽量受入は正常receipt/PBS、違うjob/script/resource/run_count、非F成功拒否、改変hash、unsafe member、分母欠落、有限reference分類不整合、precision非達成の非null比、clock不足、診断補完拒否を含む。
新collectorを小fixtureで受入後、独立reviewを経て実回収する。
