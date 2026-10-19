# main 独立計時の達成精度と費用

全8条件・各192 replicateを保持する。
校正時の診断と独立BARの診断未取得を区別し、内部flagを実測R-hat/ESS失敗数にしない。
有限reference全域の経験的RMSEを両手法が満たす場合だけ平均task費用比を表示する。

|case|epsilon|MC状態/精度|BAR状態/精度|wall比|CPU比|
|---|---:|---|---|---:|---:|
|0|0.2|completed/empirical_above_target|completed/empirical_within_target|None|None|
|0|0.1|completed/empirical_within_target|completed/empirical_within_target|0.045488936762266764|0.04697008267696927|
|1|0.2|completed/reference_sensitive|completed/empirical_within_target|None|None|
|1|0.1|completed/empirical_within_target|completed/reference_sensitive|None|None|
|2|0.2|completed/empirical_within_target|completed/empirical_within_target|0.02083413548834582|0.02085594991246144|
|2|0.1|completed/empirical_within_target|completed/empirical_within_target|0.034864035360240395|0.03564248048214125|
|3|0.2|completed/empirical_above_target|completed/empirical_within_target|None|None|
|3|0.1|completed/reference_sensitive|completed/empirical_above_target|None|None|

費用比は記録環境での未補正の記述量であり、母精度・母時間比・最速設定・名目被覆を保証しない。
pool経過時間の条件別按分は行わず、task wall・process CPU・job/PBS wallを分ける。
低ノイズの独立計時は未評価であり、mainの結果で完了扱いしない。
