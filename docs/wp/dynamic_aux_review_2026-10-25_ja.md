# Dynamic auxiliary gate の独立レビュー

`output/dynamic_physical_aux_v1/gate.py` の初稿と、固定済み `physical_node_capacity_v1`・`low_parallel_dispatch_v2` を静的に読んだ。
このレビュー担当から source の変更、ローカルテスト、qsub、本番 controller の停止・起動は行っていない。

既知の science child は元 ledger・script・保存済みの実 R observation に結び付けられる。
現在観測との照合は job ID、owner、command、select、CPU・memory・nodect・walltime、run_count=1、stime、exec_vnode を含む。
Q、S、未観測 R、未知の unbound job、複数の全ノード級 child は投入可能と判定しない。
原 qstat を書き換えず、実際の child vnode を明示 binding として固定 capacity gate へ渡す。

固定 capacity gate は host alias を集約し、foreign assignment と既存 bound job の予約を含めて物理上限を確認する。
上限は同時2物理host、各hostで所有者96 CPU・340 GiBであり、単なる2 job制限ではない。
child の host と bound helper の host を分離するので、helper によって3つ目の物理hostへ広がる配置を拒否する。
共有lock内で2回の fresh censusを用い、qsub直前にintentを保存する。
qsub timeout・曖昧応答・確定前の障害は lock と証跡を保持し、同じstageへの自動再投入を拒否する。

この範囲で上限逸脱や重複 qsub を生む具体的経路は見つからなかった。
ただし、静的レビューは実 scheduler や全経路の受入成功を意味しない。

初稿の `raw(pin)` は無制限 `read_bytes()` なので、有限 tail の「小JSONだけを外側で読む」という契約に合わせた上限付き読込を作者へ提案した。
既存 `current_census()` の qstat 出力量も科学 result/selection の巨大JSONとは別の境界として扱う必要がある。
policy作成directoryとhelper投入stageは別にする必要があり、同一にすると既存証跡を守る fresh検査で拒否される。
dynamic gate自身のsource pinをouterの固定source closureへ含めることも統合担当へ依頼した。

ローカルの元 timing execution source では capacity は2 CPU・340 GiB、benchmark は内部 worker 数が変わっても PBS CPU は96固定で、memory は32–340 GiBの範囲に計画される。
したがって、この resource policy と dynamic gate の family whitelist は一致する。
census の1 CPU・2–4 GiBは対象外であり、census 実行中は軽い qstat で終端を待ち、その後に有限 observe を起動する場合に限って、この whitelist で足りる。
本番接続では、元 source の pin と実際の選択 resource の一致を引き続き検証する必要がある。

改訂稿では pin 読込を4 MiB+1の上限付き読込とし、既存 base validator にも検証済み同一bytesを渡すよう変更された。
census 取得も30秒timeoutの file-backed capture と上限付き読込・完全JSON検査・combined size検査になり、取得失敗や超過を待機として扱う。
これは controller RAM の境界であり、取得中の disk 出力量そのものを制限する保証ではない。
改訂稿を再読し、先の無制限read指摘の解消を確認した。
新 `derive_job.py` の変更は auxiliary source SHA、submission purpose、dynamic policy/resourceの一致検査という運用差分であり、既存 finite wrapper の ledger・PBS照合との静的なfield整合を確認した。
派生 wrapper の実 inputs と intent を dynamic policy fixtureで通す追加受入を推奨し、AST上の差分確認を元wrapper全受入の成功とは扱わないよう確認した。
