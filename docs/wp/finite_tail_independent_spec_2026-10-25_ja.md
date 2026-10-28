# 独立計時 tail の有限 PBS action

対象は元 `low_partition_independent_execution_v1/remote.py` の setup / gate / submit / observe / finish である。
新しい family plugin は `output/finite_tail_independent_v1/plugin.py` とし、元ファイル、元環境、科学計画、seed、結果は変更しない。
共通契約は [finite_tail_actions_spec_2026-10-25_ja.md](finite_tail_actions_spec_2026-10-25_ja.md) に従う。

## source と API

`execute(action, ctx, task=None, post_source='', *, sources, hooks=None)` の `sources` は `remote` という一つの pin を持つ。
元 remote の SHA-256 は `e57a0f3795567254ba1e7050f56054c2555681527c686a8aec09c53c8bd42fff` とする。
実行前後で元ファイルの bytes と pin を照合し、外部 pin の変更と同じ内容への path 差替えを受理しない。
`describe` は元 source pin と実行する派生 bytes の hash を別々に返す。
派生 code のファイル名は元 source の所在を維持するが、派生 bytes を元 hash として表示しない。
PBS allocation、request、plugin と hooks の source pin、および receipt の真正性は共通 worker が検証する。
この plugin 自体は本物の qsub を直接実行しない。

## 許可する二つの submit 差分

非 submit action は元 source の bytes をそのまま実行し、hooks を受け付けない。
submit だけ、元 `submitter.submit` 呼出しへ既存引数 `active_query` と `runner` を注入する。
active query は元 `own_active_jobs()` の観測を hooks へ渡し、検証済み親 PBS の退場後という別 view を取得する。
実観測の保存、除外対象の実 PBS identity 検証、親退場後の実 gate は共通 hooks / dispatcher の責任である。
通常 gate action にはこの除外を適用しない。
元 submit の bootstrap、checked、read_plan、bundle_binding、upstream、lock、intent、qsub 直前検査は保持する。
runner は qstat などの読取を hooks に委譲し、qsub は専用 Deferred 例外で停止する。
qsub hook が値を返した場合は拒否し、偽 job ID から response や submission ledger を生成しない。

二つ目の差分は元 run の operate 呼出しを try/finally で囲み、元 `proof.finish()` を finally 内で必ず実施することである。
Deferred の unwind でも source / native proof の最後の照合を省略しない。
finish が失敗した場合は Deferred 成功として扱わず、共通 worker は accepted receipt を生成しない。
元 submit が uncertain を設定して保持した lock / intent はそのまま残し、成功 ledger と混同しない。
共通 finalizer が親 F0 の確認後に元 lock を継承して実 qsub と元形式の ledger 保存を行う。

## 準備 role と返却境界

independent-preparation は上流 completed の小 pin と error 不在を outer が確認した後だけ、元 v3 adapter の role 全体を PBS 内で実行する。
元 driver の待受ループを PBS に残して先行起動しない。
no-op 分岐も bundle の parse / catalog 検査があるので PBS 内に置く。
元 preparation の `execution.inputs`、48 method row の catalog、eligible capacity ごとの prepare / read_plan / bundle_binding と二回の proof.finish を保持する。
prepared inventory は plan 本体を内包しない manifest pin と resource の一覧だが、outer はそれでも共通上限付き JSON として読む。
setup / gate / observe の元返値は小さいが、finish の capacity 結果は main partition の一覧を含み得るため、共通 worker が PBS artifact に保存し、outer はその pin と bounded receipt だけを受け取る。
元返値の切捨て、科学 row の省略、plan の軽量版への置換は行わない。
深い検証のメモリ使用量や時間は未測定であり、この adapter の fixture を実大規模データの完走証拠としない。

## 受入

実元 remote の hash と非 submit の bytes 同一性、submit の厳密二差分を確認する。
元 submit 関数を固定 source から抽出し、fixture 内の明示的な科学 dependency stub と組み合わせて検査の呼出し順・回数と lock / intent の永続化を確認する。
stub は科学計算の独立検証を意味しない。
Deferred 時の最終 proof、finish 異常、偽 qsub return、元 source 変更、通常 gate の実観測維持を含める。
setup / observe / benchmark finish は元 remote の実分岐を実行して返値と証跡を比較する。
capacity finish も固定した元 post helper を実行し、非零終端と成功後の 192 replicate 分割が元経路へ渡ることを確認する。
実 source bytes の作用中の変更と source pin 辞書の差替えも拒否する。
テストと native bootstrap は qsub で実施し、ローカルでは実行しない。
作成時点では受入未実施である。
