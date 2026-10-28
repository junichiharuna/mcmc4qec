# 元worker受理経路のsource alias修正

本番merge265651は6秒でF/1となり、元worker verifierの `selector closure differs from environment` で停止した。
直前の[parent照合修正](parallel_merge_parent_alias_fix_2026-10-25_ja.md)はrequest準備を通したが、元 `accept_worker` 内にも同じ直接キー比較が残っていた。
前回の実native受入はterminal metadataとrequest準備までであり、元worker受理のこの箇所まで実行していなかった。
今回の全12workerは同じstaging sourceの宣言aliasとcanonical targetの表現差を持ち、既存の承認target・hashは一致している。
値の内容を読む前の失敗であり、科学値の不一致を検出したものではない。

## 変更範囲

`output/low_parallel_recovery_merge_v8/` の小仕様・受入・実装で、元verifierから派生するoperational validatorに1つの明示AST変換を追加した。
既存のproof factory・bulk hash・元verifier identityに加え、正確なclosure照合文1箇所だけを、v7と同じ承認済みresolved mapping照合へ置き換える。
四つのAST patternはそれぞれ一致数1を必須とし、元fileの外部hashと元workerのevidence pinを保持する。
直接キーのhash不一致をaliasで回避せず、直接キーがない場合だけ完全一致のtargetと対応する全hashを確認する。
元worker evidence・manifest・environment・valuesの原本を変更せず、元のsource/native hash検査とscript・intent・execution・terminal・values/input map検査を残す。
本番の変更はworker_validatorとintegrationの2pinだけで、v7 recovery contractとv6のmerger・builder・execution runner/contractは元path・bytesのままである。
新validatorの来歴には、元evidence pinと実行した新validator pinを分け、実際にimportされた旧bounded_hash sourceを記録する。

## PBS受入

| job番号 | 範囲 | 結果 |
|---|---|---|
| 265652 | 元統合受入・alias境界・AST過不足・実b24 verifierの固定bytes・全12alias fixtureのfullcombine | F/0、39 passed、32.34秒、wall 33秒 |
| 265653 | 実fullcombineと12件の受理処理の値読込直前まで、およびsource棚卸し | F/1、wall 18秒、probe棚卸しの文字コード名の誤記 |
| 265654 | probeだけを訂正した別stageで同じ全経路を再実施 | F/0、wall 18秒 |

fullcombine fixtureでは元の未修正verifierがaliasを拒否する例を再現し、新validatorで全12件の受理、24行の一致、元の結果sealまで通ることを確認した。
従来の入力pathごとのhash回数、登録順、barrier、実PBS allocation guardの受入も保持する。
実probeは元verifierの失敗を再現した後、実mergerの `combine` を呼び、最初のworker valuesを開く直前で専用例外により明示停止した。
さらに実12件それぞれの元descriptor・expected inputs・evidence pinで派生verifierを呼び、全員が自分のvaluesの読込直前へ到達することを確認した。
停止時に成功値やworker acceptanceを作らず、`worker_acceptance_returned=false`・`full_combine_returned=false` として保存した。
実values・raw配列は読まず、本番mergeの成功、科学的な深い受理、後段完走まで証明したとは扱わない。
265653の失敗はprobeの `utf8-sig` という文字コード名を `utf-8-sig` に直しただけであり、受入済み本番source2件は変更していない。
F/1の原本を残し、途中まで到達したことをprobe全体の受理に読み替えず、別stageの265654で全経路を再確認した。

## 後段sourceの監査

実engine・selector・planner・各evidence・merger・execution/acceptance helperなど71sourceの原本pinとASTを記録した。
実行文としての `source_sha256.get` は4箇所で、二つは保存した元evidenceの `accept_worker`、残りは分析bindingと過去final-reportのsource pin照合だった。
実workerの元evidence比較は今回の正確なAST変換を適用し、main evidenceに保存されている `accept_worker` は本mergeのworker受理には使わない。
残り二つは親環境のdeclared/resolved mappingを比較する処理ではなく、意味の違う原本source照合として保持した。
merger後段のengine確認・selector選択検証と、終端acceptanceの `verified_result`・`promote` は同じcanonical scientific source mapを照合する経路であり、親環境のalias keyへ読み替えない。
この棚卸しを全ての不具合がない証明とはせず、実行経路と保存した比較式の対応を確認する根拠として扱う。

## 証跡と再開境界

識別子を省いた[小receipt](data/parallel_merge_worker_alias_20261025/receipt.json)と[独立レビュー](parallel_worker_alias_review_2026-10-25_ja.md)を保存する。
private原本は `output/low_parallel_recovery_merge_v8/` 内の `worker-alias-merge-tests-v1-evidence`、`worker-alias-merge-native-v1-evidence`、`worker-alias-merge-native-v2-evidence` に元bytesのまま保存した。
hashは識別子を除去する前の原本を指す。
本番失敗merge・request・errorと全12workerの原本を保持し、再開には新しいmerge rootとrequest rootを使う。
本担当は本番controllerの開始・worker再実行を行っていない。
正式selection24行、独立計時48行・各192分母、最終報告・原本保存という完了要件は変更しない。
