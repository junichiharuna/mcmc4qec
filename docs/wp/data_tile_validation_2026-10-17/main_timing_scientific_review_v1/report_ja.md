# 主ノイズ独立計時：保存結果の科学的レビュー

正式回収済みreportの8条件を読み、保存値の抽出と判定・費用比の算術整合だけを確認した。
全8条件でMC/BARそれぞれ192/192点と区間を取得し、失敗・区間未取得は0だった。
MCは4 within・2 above・2 sensitiveで事前のMC集計と完全一致し、BARは6 within・1 above・1 sensitiveだった。
withinは有限99.9%reference区間全域で経験的相対RMSEが目標以下、aboveは全域で目標超過、sensitiveはreference内で判定が変わることを表す。
範囲は母RMSEの信頼区間ではなく、全192点の経験的誤差をreferenceの候補値に対して評価した範囲である。

## 主報告用の8条件表

|符号・noise|目標ε|MC相対RMSE範囲|MC判定|BAR相対RMSE範囲|BAR判定|mean MC / mean BAR：wall|同CPU|
|---|---:|---:|---|---:|---|---:|---:|
|tile72 bit-flip|20%|20.7686–21.0688%|above|11.9629–12.1141%|within|null|null|
|tile72 bit-flip|10%|9.1333–9.1863%|within|9.8470–9.9849%|within|0.045489|0.046970|
|tile288 bit-flip|20%|19.9303–20.2073%|sensitive|12.5380–12.8349%|within|null|null|
|tile288 bit-flip|10%|9.4453–9.4980%|within|9.9421–10.3387%|sensitive|null|null|
|tile72 depolarizing|20%|17.0494–17.2571%|within|13.3686–13.8137%|within|0.020834|0.020856|
|tile72 depolarizing|10%|9.6234–9.7225%|within|8.5976–8.7032%|within|0.034864|0.035642|
|tile288 depolarizing|20%|20.9573–21.3715%|above|18.7096–19.0191%|within|null|null|
|tile288 depolarizing|10%|9.9205–10.0048%|sensitive|10.0969–10.4235%|above|null|null|

比を表示できる3条件では全て1未満で、記録された環境でのMC平均task費用の方が小さかった。
他の5条件は少なくとも片方が固定精度gateを通らないためnullであり、失敗した行の削除や閾値変更で比を出さない。
tile288 bit-flipの10%ではBARがreference_sensitive、tile288 depolarizingの10%ではBARがaboveだった。
両方withinでも実達成精度が同一ではなく、閾値以下を満たす今回の固定候補間の記述的な費用比較である。

## 平均task時間

単位は秒で、wallとprocess CPUを別に示す。

|符号・noise|ε|MC wall|BAR wall|MC CPU|BAR CPU|
|---|---:|---:|---:|---:|---:|
|tile72 bit-flip|20%|0.287418|18.116091|0.279707|17.223333|
|tile72 bit-flip|10%|1.104759|24.286321|1.071236|22.806773|
|tile288 bit-flip|20%|1.628306|269.048755|1.584322|265.100633|
|tile288 bit-flip|10%|5.525721|423.405179|5.441126|416.420869|
|tile72 depolarizing|20%|0.646192|31.016038|0.628273|30.124379|
|tile72 depolarizing|10%|2.425824|69.579564|2.374337|66.615360|
|tile288 depolarizing|20%|20.290163|423.813137|20.060597|418.728616|
|tile288 depolarizing|10%|79.558932|1228.186655|78.891366|1214.702723|

task wall/CPUはartifact書込みを除き、BARは構築・独立anchor・初期化・sampling・compact再復号・選択解析の費用を含む。
MCは全8条件を一つの96worker pool、BARはcase別に2条件の96worker poolで実行しており、job/PBS wallを条件数やreplicate数で按分しない。
MCはnode011、BAR case0はnode012、case1/2/3はnode010で、host差を補正していない。
同じ受理済みnative profile・依存版でもCPU model・frequency・affinity・NUMA・当時の負荷はunknownであり、同等hardware性能を認定しない。
集計job265277のnode008・PBS7分41秒は後処理費用であり、MC/BAR task費用比に入れない。

## 区間被覆と診断

次表は各192区間について、独立MC reference点を含む数、99.9%reference区間全体を含む数、同区間と交差する数を分ける。

|符号・noise|ε|MC：点/全域/交差|BAR：点/全域/交差|
|---|---:|---|---|
|tile72 bit-flip|20%|180/180/180（分母192）|172/171/174（分母192）|
|tile72 bit-flip|10%|185/181/185（分母192）|158/155/162（分母192）|
|tile288 bit-flip|20%|176/176/184（分母192）|170/167/173（分母192）|
|tile288 bit-flip|10%|185/184/187（分母192）|172/167/172（分母192）|
|tile72 depolarizing|20%|188/188/188（分母192）|166/164/167（分母192）|
|tile72 depolarizing|10%|182/181/182（分母192）|168/163/172（分母192）|
|tile288 depolarizing|20%|182/178/182（分母192）|166/164/167（分母192）|
|tile288 depolarizing|10%|183/181/183（分母192）|171/169/174（分母192）|

BARのreference点に対する経験的被覆は158〜172/192で、相対RMSE条件の通過を名目95%被覆の確認とはしない。
全8選択候補の校正cohortには実測診断flag192/192があり、これを取り除いて候補を選び直してはいない。
独立BAR計時の混合診断はnot_collectedで、保存metricsのflagged/undefined=192は未取得placeholderである。
それを新しい実測R-hat/ESS警告や混合の良否として解釈しない。

## 解釈の限界と再現

選択用校正cohortと独立計時cohortを分け、MCはstage121、BARはstage140を用いた固定192 replicateである。
seed namespaceの分離と有限censusは乱数streamの数学的独立性の証明ではない。
同じ有限referenceを選択・MC予算・評価に共用し、99.9%区間を確実な真値範囲や全条件の同時保証とはしない。
今回の比を母時間比、最速設定、最小time-to-accuracy、低ノイズでの速度優位へ一般化しない。
主条件p*=.03/.05に限る結果で、低ノイズの独立計時は別scopeで未評価のままである。
全保存値・条件・host/source/hashは[review.json](review.json)、小数の全精度を保った8行表は[results.csv](results.csv)に保存した。
元report・回収証拠のhashを固定し、原task、JSONL、NPZ、科学数値helper、decoder、native probeは再読込・再実行していない。
