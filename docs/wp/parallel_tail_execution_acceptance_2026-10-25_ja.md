# 並列 merge 後段の接続受入

2026-10-25 に、8 CPU merge の実行証跡を census と最終 report が検証できる別版 tail を準備した。
元の driver、bridge、report、環境を上書きせず、`output/low_parallel_tail_v3` と新 report-only 環境を使用する。
parent 環境・basis・科学的な選択・24 行・校正・seed は変更していない。

旧 census driver の原本 pin 検査を維持した後、新 bridge / runner の実 pin を登録する。
report preparation の descriptor は二つの実行 helper pin だけを切り替える。
bridge は二箇所の PBS 検査を新 execution contract 経由にし、report は二つの許可 SHA だけを更新する。
新 report 環境の変更は source_sha256、resolved_sources、import_origins、import_prepend の四フィールドに限定して再導出し、完全一致を要求する。
新 runner / contract の元 worker evidence は従来の原本 pin のままで、新 validator と混同しない。

qsub 265611 は F / exit 0 / run_count 1、39 テストが 0.024 秒で成功した。
旧 tail の 17 テスト、bridge / report の 18 テスト、driver 接続の 4 テストを含む。
qsub 265614 は F / exit 0 / run_count 1、walltime 5 秒で成功した。
この受入では追加した source closure の 4 テストが 0.001 秒で成功した後、実 report_job.py の `-i --help` コンテキストで native bootstrap、script directory、全 import origin、完全 source 集合を検証した。
全ジョブは共有 physical-node gate を通した qsub で投入し、数値計算や本番 reader は起動していない。

先行する qsub 265612 と 265613 は、それぞれ F / exit 1 / walltime 5 秒であり、原本とログを保持する。
実 bootstrap は既存の source/runtime 検査を通過したが、その後に追加した受入側の source 集合比較が不完全だった。
265612 は report の集合だけ、265613 は report と wrapper 自身だけを比べていた。
実クラスタの固定 wrapper は、それらに加えて親の local_imports を再帰的にたどる実装であり、ローカルの旧 wrapper を比較の根拠に使った点が誤りだった。
265614 では実固定 wrapper の完全な手順を別 helper に再現し、推移依存・循環・未定義 origin・異なる origin を fixture で確認したうえで、完全一致を維持した。
期待集合から項目を除外したり、source 検査を弱めたりしていない。

新設定は `$HOME/workspace/mcmc4qec/20261025-low-parallel-tail-config-v8/tail-config.json` に保存した。
その SHA-256 は `e91b41145b18198161bf8f877af176b9512f943ec9ac52d56dcfc08cf553bb5f` である。
merge root は `20261025-low-parallel-front-v6/merge-parallel-v1`、flow / tail の journal は v8 の新しい保存先を使う。
設定生成時に native 受入原本、実 request、worker、terminal、旧 parent / basis を再照合し、後段はまだ起動していない状態で引き渡した。

これらは運用 source と環境の受入であり、実全12条件の merge 成功、独立計時、最終 report 完了を意味しない。
実データ量での最終 report 内 bridge 検証の所要時間は未測定で、既存の timeout は変更していない。
公開用の小さな証跡は同名の JSON に保存する。
記録した SHA-256 は識別子を置換する前のクラスタ原本を指し、公開 JSON 自身の hash ではない。
