# 保存 MC 計時 summary の達成精度確認

固定 1536 行だけを既存の精度 helper で再集計し、raw payload の全再読込・MC 再実行・native probe は行っていない。
各条件の予定 192 replicate は全件成功し、区間欠損も 0 件だった。
予定 epsilon と実測相対 RMSE を区別し、閾値変更・seed 追加・cohort 削除は行わない。

|case|epsilon|実測相対 RMSE の reference 範囲|既存判定|
|---|---:|---:|---|
|0|0.2|0.207685753–0.210687755|empirical_above_target|
|0|0.1|0.091332817–0.091863465|empirical_within_target|
|1|0.2|0.199302615–0.202073332|reference_sensitive|
|1|0.1|0.094453174–0.094979728|empirical_within_target|
|2|0.2|0.170494158–0.172571286|empirical_within_target|
|2|0.1|0.096233593–0.097224748|empirical_within_target|
|3|0.2|0.209573160–0.213715290|empirical_above_target|
|3|0.1|0.099204667–0.100048078|reference_sensitive|

within は 4 条件、above は 2 条件、reference_sensitive は 2 条件である。
BAR main が未評価のため、現段階の全 8 条件の時間比は未取得である。
MC の gate を通らない 4 条件は、今後 BAR が通過しても固定規則上の同精度時間比を null とする。
20%・10%予算の計画式は、有限 reference 範囲を仮定した母 RMSE の式であり、この独立 192 標本の経験的 RMSE 通過を保証しない。
bias・RMSE・参考区間被覆・失敗分母と wall/CPU 費用の全 8 行は timing_mc_achieved_precision_v1.json に保存した。
MC は node011・96 workers、全 8 条件を一つの pool で実行し、phase wall は約 226.898 秒だった。
条件別 task wall/CPU の平均と、全 job の phase wall・PBS wall を混同せず、phase 時間を条件へ按分しない。
有限 reference の不確実性と有限 192 replicate の不確実性を残し、母精度・名目被覆・BAR の速度優位を保証しない。
元 summary、reference、audit、環境、数値 source と実行 script の hash を JSON に記録した。
