# 有限 PBS 後処理の fixture と起動境界の受入

## 範囲

元の科学検証を PBS 内へ移すための census・独立比較・report・子ジョブ投入・census 回収・共通 PBS envelope を対象とした。
試験は共有 physical-node gate と `qsub` を通し、2 CPU・4 GiB・10 分の予算で実行した。
ローカルでのテスト・科学計算、本番 controller の切替、本番 worker の再投入は行っていない。
合成 fixture の成功と、実データを用いた後処理全経路の受入は区別する。

## 結果と失敗記録

| qsub job番号 | 対象 | PBS結果 |
|---|---|---|
| 265630 | 初回の全96件 | F/1、指定元moduleの誤りを記録 |
| 265631 | 修正した独立比較16件 | F/0 |
| 265632 | 共通envelopeの実CLIと外側の採用 | F/0 |
| 265633 | 正しいsource bindingでの全96件 | F/0 |

初回の全体ジョブは F/1・walltime 2 秒だった。
census 8 件、report 19 件、dispatch 26 件、census collection 7 件、共通 job 20 件は成功したが、独立比較 16 件中 12 件が fixture の元関数抽出で失敗した。
原因は request が `submit_tile_low_noise_timing_execution` ではなく別の `submit` module を指定したことであり、この時点では統合受入は成立していない。
元環境の source pin に結合した正しい module へ request を修正し、adapter・科学処理・test source は変更しなかった。
元の失敗 stage を保持して別 stage で独立比較 16 件を再実行し、F/0・walltime 1 秒、16 件成功を確認した。
続いて正しい source binding の下で全 96 件を別 stage で再実行し、F/0・walltime 2 秒、全件成功を確認した。
初回の成功 80 件を全体ジョブ F/0 と読み替えてはいない。

## 共通 envelope の独立レビューと実 CLI

レビュー対象 `finite_tail_job_v1/job.py` の SHA-256 は `380fe15d273da4c960e38e3b973ce3011f01045e8d75223449782e6f84cb8c07` である。
4 MiB を上限とする read、実 PBS allocation・hostname・job ID の照合後の operation import、intent・ledger・qsub response の結合を確認した。
F/0 と completion の一致後だけ結果を採用し、応答不明や部分実行を自動再試行しない構造を確認した。
大きい artifact の内容 hash は PBS 内で行い、外側は保存済み stat と照合する。
stat 照合は独立した内容 hash の保証ではなく、その制限は維持する。
本人と子プロセスの最大 RSS を分けて保存し、加算値と称さない。
この静的レビューでは blocking 指摘はなかった。

元の共通 wrapper bytes と受入済み physical gate を使い、小さな専用 operation で prepare・qsub・実 `job.py` CLI・実 PBS guard・F/0・外側 observe による採用まで確認した。
この実 CLI probe は F/0 で、科学 payload・科学環境 bootstrap・子ジョブ投入を実行していない。
そのため、実科学データの後処理や派生 report 環境の受入とは扱わない。
本番の operation・payload・環境の組立と下流全経路の受入は別工程として残る。

## 証跡

失敗・修正後の個別再試験・統合再試験・実 CLI probe の原本 111 ファイルを ignored output の `finite_tail_fixture_acceptance_evidence_v1` に保存した。
原本にはクラスタの識別子が含まれるため、追跡文書へ複写しない。
公開用の小 receipt には識別子を含めず、記載 SHA-256 は置換前の原本を指す。
