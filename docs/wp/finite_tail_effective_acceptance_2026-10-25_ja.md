# 有限 PBS tail 用 report 環境の受入

既存の科学設定を保持したまま、report の巨大な検証結果を PBS 内の一時ファイル経由で受け渡す環境と、元の collection 処理を有限 PBS action に渡す実装を検証した。
本記録は bootstrap と設定の受入であり、全条件の科学解析や最終 report の完了を意味しない。

| 工程 | PBS job 番号 | 結果 |
|---|---:|---|
| effective 12件、collection 7件、native worker 7件 | 265635 | 26件成功、F / exit 0 / run 1 |
| 実 report CLI の bootstrap と source closure | 265636 | F / exit 0 / run 1、実行時間5秒 |
| v9 設定の作成と実 validator 照合 | 265638 | F / exit 0 / run 1、実行時間1秒 |

テストの実行時間は unittest の記録で0.210秒である。
ローカルでの Python 実行・テスト・科学計算は行っていない。
投入はすべて qsub で行い、共通の物理2ノード制限と投入ロックを用いた。
純試験は直前の共通 fixture と同じ policy v6、native と設定作成は指定された policy v4 を使用した。
両 policy の許可ノード・capacity helper・投入ロック・owner・配置は同一で、相違は preparation と runtime の参照先である。
初回の投入準備では login の既定 Python の機能不足で2回停止したが、いずれも qsub 前でありジョブは投入していない。
以後は既存環境の Python 絶対パスを明示し、失敗した準備ディレクトリは保存した。

新設定は `$HOME/workspace/mcmc4qec/20261025-low-parallel-tail-config-v9/tail-config.json` に保存した。
設定の SHA-256 は `eed3366d1be6737a2ab283d2bd5db3370c10c3c8c164f8010dc48734e466119c` である。
既存 v8 の設定 pin は `e91b41145b18198161bf8f877af176b9512f943ec9ac52d56dcfc08cf553bb5f` のまま保持した。
parent environment、basis、merge root、科学 source、元 adapter source、科学的な選択規則を変更していない。
新 report 環境では report module の source・resolved source・import origin・import prepend の4フィールドだけを更新した。
実際の report CLI による bootstrap と、実 wrapper の再帰的な report/parent source closure の検証を通過した。
collection は元の stable closure を渡し、元の upstream accepted.json の pin を PBS 開始時の値で取り直さない。

ローカルの非追跡証跡は `output/finite_tail_effective_evidence_v1/` に回収した。
純試験の accepted.json 原本 SHA-256 は `c5f99b28d9be9249e881d117b387f0d4284c80298a41217d7f18e60abe877771` である。
native acceptance 原本 SHA-256 は `5137c717ef422569ab206e8653b4bcf62e190af2e9d6342c6d78cdb5e8a3236d` である。
新 report environment 原本 SHA-256 は `c35afbf82e7a4dc0c1dc3f992141e10a350be46b147d27a1b410dc496d6bc2b1` である。
設定作成 receipt 原本 SHA-256 は `c05197b1976c56f4bd34f62a0b67f99ec2777780e09bd8ec30d5eff4cb634f52` である。
これらの SHA-256 は識別子を置換していない非公開原本を指す。
