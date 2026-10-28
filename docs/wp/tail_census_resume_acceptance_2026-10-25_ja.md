# census後続再開の構成・接続受入

元12 worker・merge・acceptance・全12条件比較を保持し、失敗したcensus準備以降だけを新しい出力先で再開するための構成を用意した。
本稿の受入は制御処理と実構成の接続に限り、全件seed census・独立計時・最終報告の完了を意味しない。

## 固定した変更範囲

科学bundle・selection・registry・seed生成・全域衝突判定・stream hashは元の値を保持する。
census専用environmentとbasisを正規の新sourceへ結合し、元の資源式の候補と運用上の1 CPU・96 GiB・4時間の割当を分けて記録する。
全予定4,208,002件と、新規割当244,440件を区別する。
元census準備の失敗rootは再利用しない。
outerの7ファイルは新しい実pathへ置き、operationだけにcensus収集時の専用environment照合を加え、他6ファイルのbytesを維持する。
実行先の変更は別の限定authorityでpolicy・dispatch・bindingへ結合し、同時利用の上限は2物理ノードのままにする。
旧source pinを別内容へ流用せず、旧source closureを保持した上で新しいsourceを追加する。
元controllerのdispatch policyは元job照合用に保持し、新しい実投入の配置はouter側のpolicyで決める。

## 実行した受入

| 対象 | qsub job | 結果 | 範囲 |
|---|---:|---|---|
| tail専用controller | 265689 | F/0、run_count=1 | 27 fixture、元比較・failure・fresh root・同一bytesのrunner移動 |
| recovery loaderとnative境界 | 265692 | F/0、run_count=1 | 27 fixture、operation/node移行の限定差分と読取り・書込み境界 |
| 実recovery構成 | 265698 | F/0、run_count=1、1秒 | 既存の環境・operation・node authorityを結合し、実outer contractで構成を受理 |
| 実tail constructor | 265699 | F/0、run_count=1、15秒 | 6 roleをcollection変換あり・なしで各1回、final-reportはconstructorだけ、合計13 case |

13 caseでは実outer entrypointのimport基点、実loader、実driver sourceとgeneric helperのoriginを照合した。
censusの2 roleだけ新environment、census準備だけ新basisとなり、独立計時とreportのenvironmentが元のままであることを確認した。
constructorの実行中はsubprocess・qsub・大きなpayloadの読取りと、検証用ディレクトリ外への書込みを拒否した。
元入力pinを前後で照合し、production出力先が未作成であることを確認した。
この試験ではcensusの実prepare/run、独立計時、report生成を実行していない。
既存observerのhost authorityを保持するため、controller自体の実constructorとlaunch previewはcluster loginの小metadata確認として別に扱い、PBS constructor試験へ混同しない。

## 再開用成果物

クラスタworkspace `$HOME/workspace/mcmc4qec` からの相対パスを示す。
以下のSHA-256はprivate原本bytesを指す。
原本には運用上の識別子が含まれるため、本文では原本の内容を転記しない。

| 原本 | 相対パス | SHA-256 |
|---|---|---|
| recovery構成 | `20261025-finite-tail-census-recovery-v13/config.json` | `a2c7b83d36b9c91b40af50214c78ad65afafb0506fa02da736741e3926da1a34` |
| recovery authority | `20261025-finite-tail-census-recovery-v13/authority.json` | `85e8cb9235e71a8868db19e6f3701f903059453f0b716c0236523b487835d2c8` |
| recovery組立receipt | `20261025-finite-tail-census-recovery-v13/prepared-receipt.json` | `8af4d1a1303894b13cbc5230a693d69c9f5764f3acead6e6edc9f83efacabf3c` |
| 実constructor受入 | `20261024-c3t2-index-relocation-v1/pipeline-submissions/finite-tail-census-native-v1/results/accepted.json` | `9583f9bf07de49fd8bef6c1dac949a4b99c7752d77c481e1b1a14ccde9dbbf49` |
| tail専用controller構成 | `20261025-low-parallel-controller-v13/flow-config.json` | `e68ac4d738c21c6d79ddf71a22f0dd8aa35456c4325507fccf48ca2cf547c0fa` |

controller構成の小metadata組立はcluster loginで行い、元14 jobを再実行していない。
元controllerの停止識別情報、比較・handoff、12 workerの終端、失敗265675、実constructor受入を構成へ結合した。
新controllerの実sourceとlauncherは265689で試験した実pathをそのまま使う。
本稿の保存時点で本番起動の実行担当はrootであり、起動結果は状態文書と別のlogin readiness・launch証拠で確認する。

小原本36ファイル・479,460 bytesを `output/finite_tail_census_recovery_v1/accepted-evidence/` に保存した。
取得対象はrequest・script・submission intent/response・PBS終端・組立receipt・13 caseの受入であり、科学的なraw traceや巨大bundleは取得していない。
staging原本は `output/finite_tail_census_recovery_v1/stage_build.py`・`stage_native.py`、小controller構成の組立は `output/finite_tail_resume_controller_v1/assemble_config.py` にある。
native staging初回は小receiptのauthority参照位置の誤りで投入前に停止し、正しい `transition.authority` へ修正した。
当該stderrは保持し、この停止によるPBS jobの二重投入はない。

資源割当の4時間は運用上の上限であり、完了時刻の予測ではない。
独立referenceのない領域について、ここでの接続試験や設定間整合性から精度・95%被覆を保証しない。
