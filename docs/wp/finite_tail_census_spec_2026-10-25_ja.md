# Census の有限 PBS action 仕様

共通契約は `finite_tail_actions_spec_2026-10-25_ja.md` に従う。
本変更は新しい `output/finite_tail_census_v1` に閉じ、元 source、現行設定、科学条件を変更しない。

`execute(action, ctx, task=None, post_source='', *, sources, hooks=None)` は `sources={remote: pin}` で固定した元 census remote を使う。
対象 action は `no_op`、`gate`、`submit`、`observe`、`seal` であり、task と post_source は利用しない。
非 submit は hooks を受け付けず、元 bytes をそのまま実行する。
submit だけ元の `bridge.submit(root, execute=True)` の一箇所を置換し、親を明示的に除外する active_query と共通 Deferred runner を渡す。
元の bootstrap、science、config の検証、read_plan、proof.finish は順序も回数も維持する。
Deferred は plugin 内で捕捉せず、元 submit が作った lock と intent を保持したまま共通 worker へ伝える。
plugin は qsub を実行せず、成功 job ID、submission ledger、親退場後の投入許可を生成しない。
runner の qstat 委譲、親の真正性、実投入直前の再 gate、lock 引継ぎは共通 hooks / outer の責務である。

準備 role は `low_timing_partition_census_wait_v1` である。
共通 worker は上流の完了を確認してから、既存 v3 adapter の transform_driver / configure / run を PBS 内で実行する。
元 driver の payload、全入力検証、準備、回収、hash、accepted receipt の生成を同じ PBS に収める。
外側には accepted / skipped の小さい状態と生成 artifact の pin を返し、大きい bundle / config / plan を stdout に載せない。
上流待受と実 job の qstat 待受を外側に置き、元の深い検証は PBS 内に残す。

受入 fixture は実固定 remote の全 action と元 submit 本文を使い、科学依存を小さい fixture に置き換える。
非 submit の戻り値と呼出し列、submit の deep call、qstat 委譲、qsub 直前の Deferred、lock / intent 保持、成功 ledger 不在、source 改変拒否を確認する。
ローカル試験と本番投入は実施せず、共通担当が PBS で受入を実施する。
