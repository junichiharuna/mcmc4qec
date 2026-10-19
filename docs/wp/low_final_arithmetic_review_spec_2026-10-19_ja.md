# 低ノイズ最終reportの独立算術レビュー

既存C2専用レビューを一般化し、tile72/288・bit-flip/depolarizingの12条件で同じ標準ライブラリだけの算術確認を使う。
本番のBAR・bootstrap・診断・WSS合成の関数は呼び出さない。
このレビューは保存済みrowの集計照合であり、decoder・raw trace・WSSラベルの独立再計算ではない。

## 入力とcohort

sealから取得した外部report SHAを要求し、reportのaudited_collection.evidence_sha256で固定したproduction planとrows.jsonlを読む。
planのcanonical digestをreportのmanifestと照合し、case・target・192 replicate・67,584 rowを確認する。
planのkernel・初期状態・chain数・burn-in・保存長・ladder・blockから352設定を独立に構成する。
各rowのgroup・noise・符号長・target・設定とreplicate番号を検証し、重複・欠損・未知設定を拒否する。
boolean flag・有限な確率・区間の順序・availableとの一致を検証する。
不成功rowや未定義診断は削除せず、全192 replicateで集計する。

## 算術

参照区間全体を含む区間数と参照区間に交わる区間数、その比率とWilson区間を再計算する。
全pointがある場合だけ、有限参照区間に対するbias・RMSEの最小最大を計算する。
相対RMSEの最小点はsum(x^2)/sum(x)を参照区間内に切り詰め、零または微小な値の二乗のunderflowを避ける。
参照下端0・参照未取得・point欠損・数値範囲外をそれぞれ区別する。
参照区間が広い場合にもmidpointを真値として報告しない。
precision分類・全診断flag・失敗分類・区間未取得数を保存reportと照合する。
浮動小数点の比較は相対許容差を用い、微小確率を固定絶対許容差で見逃さない。

## 出力と限界

全設定CSVとplanから選んだ最大chain・最大burn・最長trace・fine ladderの16行を保存する。
tile72 bit-flipの16chain・60,000保存と他条件の設定をplanから区別し、C2用の8chain・12,000保存を固定しない。
入力を前後で再hashし、新規出力先のreview.jsonに入力・source・CSVのhashと照合件数を保存する。
許容差内の一致は独立算術実装との整合性を示すが、混合・母集団RMSE・95%被覆・独立referenceの正しさは保証しない。

## 検証記録

2026-10-19にWindowsで17件・0.37秒、Linuxで17件・0.04秒の受入を実行した。
手計算可能なcohort、欠損pointと区間、診断未定義、参照下端0、参照未取得、全零推定値、1e-250程度の確率、重複replicate、flag型違反を確認した。
微小確率に対する2倍の誤差が固定絶対許容差で通らないことも確認した。
完了済みC2T2の実production plan・67,584 row・352設定を入力し、reportの11,968 scalar項目との一致を確認した。
最大絶対差は1.6940658945086007e-21であり、これは確率推定の誤差ではなく同じ保存rowの集計算術の差である。
実結果はdata_tile_validation_2026-10-17/low_final_case2_target2_arithmetic_general_v1に保存した。
review.jsonのSHA256は696f28c88ff0fdb14f98cebce660c9a319273c6ad142da1b9a1ca34790feb861である。
source2件はlow_final_arithmetic_sources_v1に保存し、manifest SHA256は115c93c373f643b3b9f5827b16b33de95eb9426effc66c1cc2a10eb6e47fe73bである。
Linux受入記録のSHA256は7eac80025ccff334a28a3813a07c68e63346e944267b07bc037dbb6c8cecab6bである。
残り9条件については本番reportとrowsの取得後に実行し、現時点でレビュー済みとは扱わない。
