# 有限後処理 controller の独立レビュー

初版 `output/finite_tail_outer_v1` の読取レビューから、固定 source の fixture と実設定の constructor 受入までの記録である。
時点ごとの指摘と結果を以下に残し、最新の受入範囲は末尾に記載する。
レビューではローカルテスト、本番ジョブ投入、controller 切替を行っていない。

## 確認した境界

六つの role の深い処理と final-report を有限 PBS operation とし、外側の polling は PBS 状態の小さい観測値に限る構造である。
F を観測した後も、その観測を科学的な受理とせず、元の observe を PBS 内で実行する。
元 driver の scheduler と科学関数を残し、collection のコピー・hash・manifest 作成を含む suffix 全体を PBS 内で実行する設計である。
独立比較の元 engine の 48 行、全 192 replicate の分割・保持、再投入を拒否する mutation state は変更対象ではない。
24 比較の選択や科学的な分母の実データ検証は、元の検証処理に残る。
mock fixture でこれらの数字を転送できることは、実データの不変量を独立に検証したことではない。
Deferred は元の深い submit 検証と lock・intent を保持し、親 PBS の F/0 後に実状態で再 gate してから子を qsub する。
既存の role namespace や不明な投入結果を自動再利用しない。

## 指摘と反映確認

最初の `scheduler.light_gate` は `capture_output` の後に長さを確認しており、事前のメモリ上限にはなっていなかった。
file-backed stdout と `MAX_SMALL + 1` read に変更されたことを確認した。
`final_report` の stat 後 `read_bytes` は、呼出経路によって read guard の外となり、途中で増大したファイルの上限がなかった。
前後の identity 確認と上限付き read を行う `contract.generated` への変更を確認した。
元 dispatch の default subprocess 経路にも同じ問題が残るため、元 dispatch source を変えず、bounded query・同値の final gate・bounded qsub runner を注入する修正を確認した。

初版の collection は、元 driver が固定した preparation receipt の hash を PBS 側で新しく計算し直していた。
これでは待ち時間中の変更検出が元より弱くなるため、元の `stable` closure が持つ pin map を payload に引き継ぐよう依頼した。
修正版の外側で元 closure を検査・複写し、PBS 側で元 source・environment・preparation receipt の exact pin 集合を要求する構造を確認した。
report collection の新しい呼出境界への結合と、待ち時間中に receipt を変更する negative fixture は最終受入時に改めて確認する。

## 残る結合確認

初版の `Coordinator.action` は既知の science child 全件が F になるまで待つ fallback である。
science child が一件 R のまま別ノードで次の helper を動かす dynamic 経路は、初版には含まれていない。
別担当の dynamic physical policy・alias binding を結合してから、その経路の実 qstat 原本、予定上の gate view、実 allocation を区別して確認する。
固定 policy 用の既存共通 job wrapper と dynamic policy の purpose・ledger 契約を暗黙に混ぜない。
effective environment・新 report collection・alias binding・dynamic gate の source freeze 後に再レビューし、全六 role と final-report の実 entry point context での受入を行う必要がある。
現時点では本番切替や全後処理完了を承認した記録ではない。

## 初期 snapshot の fixture 実行

上記修正を含む初期 source snapshot を別 stage に固定し、共有 physical gate と qsub を通した。
PBS は F/0・walltime 1 秒で、55 fixtures が 0.080 秒で成功した。
内訳は read 境界 8 件、scheduler 13 件、configuration 4 件、coordinator 24 件、元 stability pin 引継ぎ 6 件である。
元 preparation receipt が待ち時間中や worker 開始後に変更された場合を拒否する fixture を含む。
試験対象原本と terminal を ignored output の `finite_tail_outer_fixture_evidence_v1` に保存した。
動的 policy・実 alias binding・report collection 新版・全 role の実 entry point の受入は、この 55 件には含まれない。
作業中の local source が後に変更されても、固定済み snapshot の受入をそのまま新版に適用しない。

## Dynamic 結合後の joint fixture

次の固定 snapshot では、独立比較の一件 R を実観測として記録し、dynamic policy を経由して別の helper を準備する経路を追加した。
dynamic を指定しない場合の全 child F 待ち fallback は別の経路として残る。
元 qstat JSON を保存する first-running observation と、元 submit の予定上の gate view を混同しない構造である。
共有 lock と二回の fresh physical census を使う dynamic submitter と、対応する別版 job wrapper は別の受入証跡で固定する。
新しい joint PBS fixture は F/0・walltime 1 秒で、outer 68 件・alias binding 21 件・native constructor 用の純粋 fixture 6 件、合計 95 件が成功した。
試験時間は各 0.113 秒・0.052 秒・0.001 秒だった。
joint accepted 原本の SHA-256 は `5ce224502426470bbab29eaa2d71275cb6a67caaa9574334fe4c2402184c09b5`、source snapshot map 原本は `a2051810734f4b8caf9c80335e1f1558593a3033f0c382ab341e925f7efb97bf` である。
これらは識別子を除去する前の原本 hash であり、原本は ignored output の `finite-tail-outer-tests-v2-evidence` に保存した。
この 95 件も mock と純粋 fixture の受入であり、実設定の全 role constructor・科学 payload・本番 controller 切替を実施した証拠ではない。

## 実設定の assembly と全 role constructor

95 件の対象だった七つの outer core source と同一 bytes を、新しい実行領域へ固定した。
三つの plugin・dispatch・alias binding・二つの collection は、それぞれの受入 source から同一 bytes をコピーし、実際に使う新しい path の pin を設定に記録した。
report の IPC 環境、dynamic physical gate、対応する別版 job wrapper は各担当の受入原本に結合した。
assembly の PBS は F/0・walltime 1 秒で、新しい設定と preparation receipt を生成した。
既存の controller、旧設定、科学 worker の source を書き換えていない。

その実設定で別 PBS probe を実行し、F/0・walltime 4 秒を確認した。
実 `run.py --help` と、六 role それぞれの collection 変換なし・ありの 12 constructor、および final-report constructor の計 13 ケースが成功した。
実 entry point の import context、configured globals、元 helper の source origin、4 MiB read guard、operational payload を開かない監査を確認した。
final-report は constructor の確認のみで、最終報告を実際に生成したわけではない。
科学 payload、科学的な native bootstrap、本番 role の main、子の科学ジョブ投入はこの probe の対象外である。
したがって、この段階の成功を後処理全体の完走や数値の受理とは扱わない。

assembly 前の補助証跡追加で、別担当の effective fixture stage に terminal ファイルがないことを確認した。
元 accepted の job ID と一致する fresh qstat F/0 を新しい assembly stage に保存し、過去に保存済みだった原本ではない旨を注記した。
元 stage を修正せず、source の先行コピーも同一 bytes の再照合だけで引き継いだ。

constructor と assembly の小さい原本 109 ファイル・621,860 bytes を ignored output の `finite_tail_outer_native_evidence_v1` に回収した。
大きい合成 read-trap fixture 26 ファイルは回収していない。
正式な `{runner, config}` binding を同じ場所の `tail-binding.json` に保存し、flow 統合担当へ渡した。
識別子を省いた [受入 receipt](data/finite_tail_outer_native_20261025/receipt.json) の hash は、置換前の private 原本を指す。
本番 controller の停止・再起動・切替は、この担当から実行していない。
