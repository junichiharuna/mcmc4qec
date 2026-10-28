# controller の切替・受理境界の独立レビュー

2026-10-25 に `output/low_parallel_flow_v7/` の source を読み、指摘後の `output/low_parallel_flow_v8/flow.py` の変更を再確認した。
このレビューは source の独立な読取確認であり、ローカルテスト・本番 controller の停止・新 controller の起動は行っていない。
v7 の flow source SHA-256 は `cf8918c04b7b2d96eb193acb1b986fdcdb29446a888202931498274dcbe21b5a`、v8 は `58ada8dedaf393d01f501a9615ee7e920146c6596989b20c1b0f67b47a21e138` である。

## 確認した契約

全 12 worker の新規投入経路は無条件に例外となり、ledger が欠けても再投入を行わない。
保持済み 11 worker の prepared・manifest・runner・環境・ジョブ ID は、それぞれの元の記録と照合する。
旧 controller の PID と start ticks が一致する live process は、新 controller の開始前と開始直前に拒否する。
新 controller 自身の初期化でも旧 process の生存を確認し、旧 journal を再利用しない。
shadow 初期化による例外は PBS 内の明示的な検証に限定され、native test は tick・worker・merge・tail を呼ばない。

既存 merge request と prepared は、全 12 worker envelope、policy、helper pin、資源、script の完全一致を確認して採用する。
元の merge root と出力先を維持し、既存の merge-result を controller の採用処理で開かない。
既存の投入について intent・ledger・qsub 応答を照合し、曖昧な状態から別ジョブを投入しない。
merge 成功後は PBS 受理 wrapper の prepare・submit・observe を通り、wrapper が accepted を返すまでは comparison 完了に進まない。
元 merge のジョブ ID と受理ジョブ ID を分離し、worker とも重複しないことを確認する。

## 指摘と対応

v7 の final-report stdout の JSON parse は無制限だったため、4 MiB の上限と `read(MAX+1)` を使う bounded read を求めた。
v8 の `read_generated` とその final-report 呼出で対応を確認した。
実 merge prepared の native preflight が手動の待機条件になっていた点は、別版の受理 wrapper v2 で同じ PBS ジョブ内の先行処理へ移した。
wrapper v2 は preflight 記録を保存してから claim と元の受理に進み、controller 側でも同じ prepared・source・環境・PBS ID の preflight を要求する。

## 適用範囲

以上の controller・merge・受理境界には、この読取レビューで未解決の blocker を見つけなかった。
worker 終端の既存 capture は values の hash を一度読むため、全経路が stat だけになったとは扱わない。
tail 全 6 role の新しい有限 PBS adapter は別途実装・受入中であり、このレビューは全経路の受入や本番切替の承認ではない。
本番の巨大 merge 結果に対する受理の完走、ピークメモリ、処理時間、科学的精度・被覆を保証するものではない。
