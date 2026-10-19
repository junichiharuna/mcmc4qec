# 2026-10-19: C0T0の集約完了とBAR解析投入

公開候補を固定した後の計算進捗であり、候補915ファイルの内容は変更していない。
実状態と使用済み入口は[dispatch記録](data_tile_validation_2026-10-17/low_partition_dispatch_20261019_1144.json)に保存した。

## 完了した処理

tile72・bit-flipの低ノイズC0T0について、標本集約265323はF・Exit_status 0・run_count 1・wall 00:21:29で終了した。
complete_low_partition_collection_once.pyで実PBS・script・保存metadataと入力hashを照合し、完了を受理した。
この入口は使用済みで再実行しない。
これはmetadataの受理であり、全raw payloadの再hashや混合・被覆の検証完了を意味しない。

## BAR解析

prepare_low_partition_analysis_once.pyとsubmit_low_partition_analysis_once.pyのpartition 0のpreflight・executeは使用済みである。
prepared SHA256は87055745b2ac7d662e5fdd5766f777d2ec9c64be970d687aedc644c8f24aba92である。
qsubで265324.node-PRISMを取得し、R・run_count 1を確認した。
要求は1node・96CPU・96worker・226GiB・06:00:00であり、時間は要求上限であってETAではない。
同時に265319の標本生成もRで、待機中を含む要求node合計は2だった。
解析完了の受理は未実施であり、同じexecuteを繰り返さない。

## Trace監査の次の入口

prepare_low_partition_trace_once.pyとsubmit_low_partition_trace_once.pyのpreflightは使用済みで、いずれも受理された。
prepared SHA256はcb363176a60e0c70d66d14b3899802e253746bd96c33eb547e9799957488bf1cである。
対象はcase 0・target_index 0で、collector prepared SHA256は45c9015ab98bd1468a7305630106c4161602516737f705df2445e67470de4db6である。
trace capacityのexecuteは未使用であり、次の空き枠でsubmit_low_partition_trace_once.pyの同じ引数に--action executeを指定する。
実行前に実ownerのqstatを確認し、待機中を含む要求node数を合計2以内に保つ。
要求は1node・96CPU・8worker・340GiB・24:00:00で、初回の資源上限を表し予測所要時間ではない。
capacityの実測後にfull trace監査の資源を決める。

## 未完了の範囲

低ノイズ正式比較は引き続き3/12条件完了である。
C0T0のBAR・trace監査・最終比較・回収・算術レビューは未完了であり、今回の投入で科学的完了数を増やさない。
後続の入口と受入条件は[最終比較実行手順](low_partition_final_runbook_2026-10-19_ja.md)に従う。
公開候補のcommit・push・remote CIは依然未実施であり、今回の計算記録はその後の追加記録として区別する。
