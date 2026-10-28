# merge準備の親source alias照合修正

全12workerの正常終端後、controller設定v9はmerge request準備で `Parent scientific selector closure differs` として停止した。
selector manifestの53 sourceのうち1件はcanonical targetを記録し、親環境の93 sourceには同じ実体への宣言aliasが記録されていた。
親環境の `resolved_sources` に記録された承認targetとmanifestのpathは完全一致し、両者のSHA-256も一致する。
直接キーだけの包含比較がこの既存表現差を拒否したもので、worker値の数値不一致を発見したものではない。

## 最小変更と保存

`output/low_parallel_recovery_merge_v7/` に小仕様・受入fixture・実装を分けて作成した。
本番で置き換えるsourceはcontractとintegrationの2件だけで、実builder・merger・control・execution runnerは元v6のpathとbytesを保持する。
親sourceに直接キーがある場合はそのhash一致を必須とし、不一致を別aliasで回避しない。
直接キーがない場合だけ、親の承認済みresolved targetがmanifest pathと完全一致し、対応する全宣言hashが一致することを要求する。
同じhashだけの別path、欠落した対応、矛盾するaliasは拒否する。
既存 `proof.track` による宣言path・hash・承認targetの照合、全12worker各自のmanifest・source・jobの結合、科学selectorとengineの照合は維持する。
入力環境・worker出力・元失敗requestとerrorは変更せず、再開時は新しいrequest保存先を使う。

## qsubによる受入

| job番号 | 検証 | 結果 |
|---|---|---|
| 265647 | alias境界16件と既存統合9件 | F/0、25 passed、18.63秒、job wall 20秒 |
| 265648 | 実12件のterminal metadataと元失敗経路を用いたrequest準備・実CLI/native確認 | F/0、job wall 10秒 |

統合fixtureでは全24行のserial/parallel一致、元worker acceptance、入力pathごとのphase別hash回数、登録順・barrier、PBS allocation guardを再確認した。
実native確認では、元config・失敗request・errorを外部pinで固定し、実12件のterminal・ledger・completion・script・qsub responseを照合した。
続いて `builder.build`、修正版 `contract.inspect_request`、元 `control.prepare` と `preflight`、実execution runnerのCLI contextでの `initial`・native bootstrap・engine validateまで通過した。
試験用requestとmerge準備は独立したPBS stage内に生成し、本番merge rootは未作成のまま維持した。
worker values、配列payload、4MiBを超える非native入力の内容読込は禁止した。
科学的なworker深い受理、本番merge、controller再開をこの受入で実行したとは扱わない。
実CLI probeの標準エラーにある `SystemExit: 0` は `-i --help` で表示される終了通知であり、その後の検証結果1件と正常終了を別に確認した。
ローカルでのテスト・科学計算・worker再実行は行っていない。

## 証跡と限界

識別子を省いた[小receipt](data/parallel_merge_parent_alias_20261025/receipt.json)に、元sourceと受入原本のSHA-256を保存する。
private原本は `output/low_parallel_recovery_merge_v7/parent-alias-merge-tests-v1-evidence/` と `parent-alias-merge-native-v1-evidence/` に元bytesのまま保存した。
記載hashは識別子を除去する前の原本を指し、公開小receipt自体のhashとは区別する。
[独立レビュー](parallel_merge_parent_closure_review_2026-10-25_ja.md)も参照する。
この修正は元検証のpath対応を正すものであり、全12条件の正式selection、独立計時、最終報告が完成したという主張ではない。
